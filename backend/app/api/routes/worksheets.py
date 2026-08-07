from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from pathlib import Path
import uuid
import os
import json
import asyncio
import logging
from typing import Optional

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas import (
    WorksheetUploadResponse,
    AnalyzeRequest,
    AgeGroupEnum,
    UploadMethodEnum,
    WorksheetStatusEnum,
    CompletionContextEnum,
    ProgressEvent,
    ConfirmAnswersRequest,
)
from app.services.image_processor import ImageProcessor, resolve_image_size
from app.services.worksheet_recognizer import WorksheetRecognizer
from app.services.assessment_engine import assess
from app.services.report_generator import generate_teacher_report, generate_parent_report
from app.services.persistence_service import persist_analysis

settings = get_settings()
router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize services
_resolved_target_size = resolve_image_size(
    settings.VISION_IMAGE_SIZE,
    fallback=settings.IMAGE_TARGET_SIZE_PX,
)
image_processor = ImageProcessor(
    target_size_px=_resolved_target_size,
    max_size_px=settings.IMAGE_MAX_SIZE_PX,
    quality=settings.IMAGE_QUALITY,
)
worksheet_recognizer = WorksheetRecognizer()


# ─── SSE Progress Helper ─────────────────────────────────────────────

async def _stream_progress(steps: list):
    """
    Generator that yields SSE progress events.
    Each step is an async callable that returns (step_name, status, message, progress_pct, data).
    """
    for i, step in enumerate(steps):
        try:
            result = await step["fn"]()
            event = ProgressEvent(
                step=step["name"],
                status="completed",
                message=step["complete_msg"],
                progress_pct=step["pct"],
                data=result if isinstance(result, dict) else None,
            )
        except Exception as e:
            event = ProgressEvent(
                step=step["name"],
                status="error",
                message=f"{step['name']}失败: {str(e)}",
                progress_pct=step["pct"],
                data={"error": str(e)},
            )
        yield f"data: {event.model_dump_json()}\n\n"

    # Final completion event
    final = ProgressEvent(
        step="complete",
        status="completed",
        message="分析完成",
        progress_pct=100.0,
    )
    yield f"data: {final.model_dump_json()}\n\n"


# ─── Upload Endpoint ─────────────────────────────────────────────────

@router.post("/upload", response_model=WorksheetUploadResponse)
async def upload_worksheet(
    file: UploadFile = File(...),
    child_id: int = Form(...),
    age_group: AgeGroupEnum = Form(...),
    upload_method: UploadMethodEnum = Form(default=UploadMethodEnum.FILE),
    completion_context: CompletionContextEnum = Form(default=None),
    teacher_notes: str = Form(default=None),
):
    """
    Upload a worksheet image.

    Accepts: JPG, PNG, WEBP, PDF (first page rendered as image)
    Max file size: 20MB
    """
    # Validate file type
    allowed_types = [
        "image/jpeg", "image/png", "image/webp", "application/pdf",
    ]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=(
                f"不支持的文件格式。支持：JPG, PNG, WEBP, PDF "
                f"(当前: {file.content_type})"
            ),
        )

    # Read file
    contents = await file.read()
    if len(contents) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(status_code=400, detail="文件大小不能超过20MB")

    # Generate unique filename
    ext = Path(file.filename).suffix if file.filename else ".jpg"
    unique_name = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, unique_name)

    # Save file
    with open(file_path, "wb") as f:
        f.write(contents)

    return {
        "id": hash(unique_name) % 1000000,
        "child_id": child_id,
        "file_path": file_path,
        "original_filename": file.filename,
        "status": WorksheetStatusEnum.UPLOADED,
        "upload_method": upload_method,
        "created_at": None,
    }


# ─── Analyze Endpoint (full pipeline) ────────────────────────────────

@router.post("/{worksheet_id}/analyze")
async def analyze_worksheet(
    worksheet_id: int,
    request: AnalyzeRequest,
):
    """
    Trigger full analysis pipeline for a worksheet:
    1. Load worksheet from storage
    2. Preprocess image
    3. Call Claude Vision API for recognition
    4. Run 4-dimension assessment
    5. Generate teacher + parent reports
    """
    # Build the file path from worksheet_id (MVP: hash-based)
    # In production, load from database
    # For now, accept file_path from the request context
    file_path = getattr(request, 'file_path', None)

    if file_path and os.path.exists(file_path):
        # Read the uploaded file
        with open(file_path, "rb") as f:
            image_bytes = f.read()
    else:
        # Try to find in uploads directory (fallback)
        candidates = list(Path(settings.UPLOAD_DIR).glob(f"*"))
        if not candidates:
            return JSONResponse(
                content={
                    "status": "error",
                    "message": (
                        "找不到操作单文件。请先通过 POST /worksheets/upload 上传，"
                        "或使用 POST /worksheets/demo 进行演示分析。"
                    ),
                },
                status_code=404,
            )
        # Use most recently uploaded file
        latest = max(candidates, key=lambda p: p.stat().st_mtime)
        with open(latest, "rb") as f:
            image_bytes = f.read()

    # Step 1: Preprocess image
    processed_image, processed_filename = await image_processor.process(
        image_bytes, Path(file_path).name if file_path else "worksheet.jpg"
    )

    # Step 2: Vision recognition
    vision_result = await worksheet_recognizer.analyze(
        processed_image, age_group=request.age_group.value
    )

    # Step 3: Assessment
    assessment = await assess(
        vision_result=vision_result,
        age_group=request.age_group.value,
        child_name=getattr(request, 'child_name', '幼儿'),
    )

    # Step 4: Generate reports
    teacher_report = await generate_teacher_report(
        assessment_result=assessment,
        child_name=getattr(request, 'child_name', '幼儿'),
        age_group=request.age_group.value,
        worksheet_observations=vision_result.get("observations"),
    )

    parent_report = await generate_parent_report(
        assessment_result=assessment,
        child_name=getattr(request, 'child_name', '幼儿'),
        age_group=request.age_group.value,
    )

    return JSONResponse(
        content={
            "vision": vision_result,
            "assessment": assessment,
            "reports": {
                "teacher": teacher_report,
                "parent": parent_report,
            },
            "meta": vision_result.get("_meta", {}),
        }
    )


# ─── SSE Streaming Analyze Endpoint ──────────────────────────────────

@router.post("/{worksheet_id}/analyze-stream")
async def analyze_worksheet_stream(
    worksheet_id: int,
    file: UploadFile = File(...),
    age_group: AgeGroupEnum = Form(default=AgeGroupEnum.MIDDLE),
    child_name: str = Form(default="幼儿"),
):
    """
    Full analysis pipeline with SSE progress streaming.
    Use this for the frontend to show real-time progress.

    Events:
    - preprocessing: 图片预处理
    - recognizing: AI 识别操作单
    - assessing: 4维度评估
    - generating_report: 生成报告
    - complete: 完成
    """
    # Read file once at the start
    raw_bytes = await file.read()
    file_name = file.filename or "worksheet.jpg"

    # Build processing steps
    state = {}

    async def step_preprocess():
        processed, name = await image_processor.process(raw_bytes, file_name)
        state["processed_image"] = processed
        state["processed_filename"] = name
        return {"filename": name}

    async def step_recognize():
        processed = state.get("processed_image", raw_bytes)
        result = await worksheet_recognizer.analyze(
            processed, age_group=age_group.value
        )
        state["vision_result"] = result
        return {
            "worksheet_type": result.get("worksheet_type", "unknown"),
            "problem_count": len(result.get("problems", [])),
            "token_usage": result.get("_meta", {}).get("usage", {}),
        }

    async def step_assess():
        vision = state["vision_result"]
        result = await assess(
            vision_result=vision,
            age_group=age_group.value,
            child_name=child_name,
        )
        state["assessment"] = result
        # Return summarized assessment
        return {
            "dimensions": [
                {
                    "name": d["display_name"],
                    "score": d["score"],
                    "level": f"{d.get('level_emoji', '')} {d.get('level_name', '')}",
                }
                for d in result.get("assessment", [])
            ],
        }

    async def step_reports():
        assessment = state["assessment"]
        vision = state.get("vision_result", {})

        teacher = await generate_teacher_report(
            assessment_result=assessment,
            child_name=child_name,
            age_group=age_group.value,
            worksheet_observations=vision.get("observations"),
        )
        parent = await generate_parent_report(
            assessment_result=assessment,
            child_name=child_name,
            age_group=age_group.value,
        )
        state["teacher_report"] = teacher
        state["parent_report"] = parent
        return {"report_types": ["teacher", "parent"]}

    steps = [
        {
            "name": "preprocessing",
            "fn": step_preprocess,
            "complete_msg": "图片预处理完成",
            "pct": 15.0,
        },
        {
            "name": "recognizing",
            "fn": step_recognize,
            "complete_msg": "AI 识别完成",
            "pct": 50.0,
        },
        {
            "name": "assessing",
            "fn": step_assess,
            "complete_msg": "4维度评估完成",
            "pct": 75.0,
        },
        {
            "name": "generating_report",
            "fn": step_reports,
            "complete_msg": "双版报告生成完成",
            "pct": 95.0,
        },
    ]

    return StreamingResponse(
        _stream_progress(steps),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── Batch Analyze SSE Endpoint ──────────────────────────────────────

@router.post("/batch/analyze-stream")
async def batch_analyze_stream(
    files: list[UploadFile] = File(...),
    age_group: AgeGroupEnum = Form(default=AgeGroupEnum.MIDDLE),
    child_name: str = Form(default="幼儿"),
):
    """
    Batch analysis pipeline with SSE progress streaming.
    Accepts up to 10 worksheet images, processes each sequentially.

    SSE event types:
    - batch_start:     {type, total}
    - file_start:      {type, index, total, filename}
    - file_progress:   {type, index, step, message}
    - file_complete:   {type, index, filename, result: {assessment, reports}}
    - file_error:      {type, index, filename, error}
    - batch_complete:  {type, total, succeeded, failed}
    """
    MAX_BATCH = 10
    if len(files) > MAX_BATCH:
        raise HTTPException(
            status_code=400,
            detail=f"批量上传最多支持 {MAX_BATCH} 张图片，当前: {len(files)} 张",
        )

    async def _batch_stream():
        total = len(files)
        results = []
        succeeded = 0
        failed = 0

        # Batch start
        yield _sse({"type": "batch_start", "total": total})

        for idx, f in enumerate(files):
            filename = f.filename or f"worksheet_{idx + 1}.jpg"
            file_idx = idx + 1  # 1-based for display

            try:
                # File start
                yield _sse({
                    "type": "file_start",
                    "index": file_idx,
                    "total": total,
                    "filename": filename,
                })

                # Step 1: Read + Preprocess
                yield _sse({
                    "type": "file_progress",
                    "index": file_idx,
                    "step": "preprocessing",
                    "message": f"正在预处理 ({file_idx}/{total}): {filename}",
                })
                raw_bytes = await f.read()
                processed, _ = await image_processor.process(raw_bytes, filename)

                # Step 2: Vision recognition
                yield _sse({
                    "type": "file_progress",
                    "index": file_idx,
                    "step": "recognizing",
                    "message": f"AI 正在识别 ({file_idx}/{total}): {filename}",
                })
                vision_result = await worksheet_recognizer.analyze(
                    processed, age_group=age_group.value
                )

                # Step 3: Assessment
                yield _sse({
                    "type": "file_progress",
                    "index": file_idx,
                    "step": "assessing",
                    "message": f"正在评估 ({file_idx}/{total}): {filename}",
                })
                assessment = await assess(
                    vision_result=vision_result,
                    age_group=age_group.value,
                    child_name=child_name,
                )

                # Step 4: Reports
                yield _sse({
                    "type": "file_progress",
                    "index": file_idx,
                    "step": "generating_report",
                    "message": f"正在生成报告 ({file_idx}/{total}): {filename}",
                })
                teacher = await generate_teacher_report(
                    assessment_result=assessment,
                    child_name=child_name,
                    age_group=age_group.value,
                    worksheet_observations=vision_result.get("observations"),
                )
                parent = await generate_parent_report(
                    assessment_result=assessment,
                    child_name=child_name,
                    age_group=age_group.value,
                )

                file_result = {
                    "filename": filename,
                    "assessment": assessment,
                    "reports": {"teacher": teacher, "parent": parent},
                }
                results.append(file_result)
                succeeded += 1

                yield _sse({
                    "type": "file_complete",
                    "index": file_idx,
                    "total": total,
                    "filename": filename,
                    "result": file_result,
                })

            except Exception as exc:
                failed += 1
                results.append({"filename": filename, "error": str(exc)})
                yield _sse({
                    "type": "file_error",
                    "index": file_idx,
                    "total": total,
                    "filename": filename,
                    "error": str(exc),
                })

        # Batch complete
        yield _sse({
            "type": "batch_complete",
            "total": total,
            "succeeded": succeeded,
            "failed": failed,
            "results": results,
        })

    return StreamingResponse(
        _batch_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def _sse(data: dict) -> str:
    """Serialize a dict as an SSE data line."""
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


# ─── Demo Endpoint ───────────────────────────────────────────────────

async def _run_analysis_pipeline(
    image_bytes: bytes,
    filename: str,
    age_group: AgeGroupEnum,
    child_name: str,
    child_id: Optional[int],
    db,
) -> dict:
    """完整分析流水线：预处理 → 识别 → 评估 → 报告 → 持久化。

    供 /demo（multipart 直传）与 /cloud-analyze（云存储 fileID）共用。
    """
    # Step 1: Read and preprocess
    processed_image, processed_filename = await image_processor.process(
        image_bytes, filename
    )

    # Step 2: Vision recognition
    vision_result = await worksheet_recognizer.analyze(
        processed_image, age_group=age_group.value
    )

    # Step 3: Assessment
    assessment = await assess(
        vision_result=vision_result,
        age_group=age_group.value,
        child_name=child_name,
    )

    # B6/B8: build child memory BEFORE persisting (so it reflects prior state)
    from app.services.memory_service import build_child_memory
    child_memory = None
    if child_id is not None:
        child_memory = await build_child_memory(db, child_id)

    # Step 4: Generate reports
    teacher_report = await generate_teacher_report(
        assessment_result=assessment,
        child_name=child_name,
        age_group=age_group.value,
        worksheet_observations=vision_result.get("observations"),
        child_memory=child_memory,
    )

    parent_report = await generate_parent_report(
        assessment_result=assessment,
        child_name=child_name,
        age_group=age_group.value,
        child_memory=child_memory,
    )

    # Step 5: Generate evaluation trace (per-problem PCK indicator mapping)
    from app.services.assessment_engine import generate_evaluation_trace
    evaluation_trace = generate_evaluation_trace(vision_result, age_group.value, child_name)

    response_data = {
        "vision": vision_result,
        "assessment": assessment,
        "reports": {
            "teacher": teacher_report,
            "parent": parent_report,
        },
        "evaluation_trace": evaluation_trace,
        "meta": vision_result.get("_meta", {}),
    }

    # Step 6: Persist to DB if child_id is provided
    if child_id is not None:
        try:
            persisted = await persist_analysis(
                db=db,
                child_id=child_id,
                original_filename=filename,
                image_bytes=processed_image,
                vision_result=vision_result,
                assessment_result=assessment,
                teacher_report=teacher_report,
                parent_report=parent_report,
                age_group=age_group.value,
            )
            response_data["persisted"] = persisted
        except Exception as e:
            response_data["persist_error"] = str(e)

    return response_data


@router.post("/demo")
async def demo_analysis(
    file: UploadFile = File(...),
    age_group: AgeGroupEnum = Form(default=AgeGroupEnum.SMALL),
    child_name: str = Form(default="小明"),
    child_id: Optional[int] = Form(default=None, description="幼儿ID，提供则持久化到数据库"),
    db = Depends(get_db),
):
    """
    Demo endpoint: Full analysis pipeline on a single image.
    This is the MVP core endpoint — upload + preprocess + recognize + assess + report.

    If child_id is provided, results are persisted to the database and linked to the child.
    """
    image_bytes = await file.read()
    try:
        result = await _run_analysis_pipeline(
            image_bytes,
            file.filename or "worksheet.jpg",
            age_group,
            child_name,
            child_id,
            db,
        )
        return JSONResponse(content=result)
    except RuntimeError as e:
        err_msg = str(e)
        # MiniMax 配额不足 → 503 服务暂不可用（前端可提示）
        if "1008" in err_msg or "insufficient balance" in err_msg.lower() or "配额" in err_msg:
            return JSONResponse(
                status_code=503,
                content={
                    "error": True,
                    "detail": "AI 识别服务暂不可用：MiniMax 周配额已用尽，请稍后重试。",
                    "error_type": "QuotaExhausted",
                },
            )
        return JSONResponse(
            status_code=500,
            content={"error": True, "detail": err_msg or "分析失败", "error_type": "RuntimeError"},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": True, "detail": f"分析失败：{e}", "error_type": type(e).__name__},
        )


class CloudAnalyzeRequest(BaseModel):
    """教师拍照 → 云存储 fileID → 后端读取分析（云托管通道）。"""
    file_id: str = ""
    file_url: Optional[str] = None
    age_group: AgeGroupEnum = AgeGroupEnum.MIDDLE
    child_name: str = "小朋友"
    child_id: Optional[int] = None


@router.post("/cloud-analyze")
async def cloud_analyze(
    payload: CloudAnalyzeRequest,
    db = Depends(get_db),
):
    """云托管通道的照片分析：按 fileURL/fileID 读图，复用完整分析流水线。"""
    from app.services.cloud_storage import download_file, download_url

    try:
        if payload.file_url:
            image_bytes = await download_url(payload.file_url)
        else:
            image_bytes = await download_file(payload.file_id)
    except Exception as e:
        logger.warning(f"cloud-analyze: 读取对象存储失败 {e}")
        return JSONResponse(
            status_code=400,
            content={
                "error": True,
                "detail": f"读取图片失败：{e}",
            },
        )

    try:
        result = await _run_analysis_pipeline(
            image_bytes,
            "cloud-worksheet.jpg",
            payload.age_group,
            payload.child_name,
            payload.child_id,
            db,
        )
        return JSONResponse(content=result)
    except RuntimeError as e:
        err_msg = str(e)
        # MiniMax 配额不足 → 503 服务暂不可用（前端可提示）
        if "1008" in err_msg or "insufficient balance" in err_msg.lower() or "配额" in err_msg:
            return JSONResponse(
                status_code=503,
                content={
                    "error": True,
                    "detail": "AI 识别服务暂不可用：MiniMax 周配额已用尽，请稍后重试。",
                    "error_type": "QuotaExhausted",
                },
            )
        return JSONResponse(
            status_code=500,
            content={"error": True, "detail": err_msg or "分析失败", "error_type": "RuntimeError"},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": True, "detail": f"分析失败：{e}", "error_type": type(e).__name__},
        )


# ─── Teacher Confirmation Endpoints ────────────────────────────────────

@router.post("/recognize")
async def recognize_worksheet(
    file: UploadFile = File(...),
    age_group: AgeGroupEnum = Form(default=AgeGroupEnum.SMALL),
    child_name: str = Form(default="幼儿"),
):
    """
    Recognize-only endpoint: preprocess + 3-pass vision recognition.
    Stops before assessment so the teacher can review/correct answers.

    Returns the full vision_result for display in the TeacherReviewPanel.
    """
    # Step 1: Read and preprocess
    image_bytes = await file.read()
    processed_image, processed_filename = await image_processor.process(
        image_bytes, file.filename or "worksheet.jpg"
    )

    # Step 2: 3-pass vision recognition
    vision_result = await worksheet_recognizer.analyze(
        processed_image, age_group=age_group.value
    )

    return JSONResponse(content={
        "vision": vision_result,
        "meta": vision_result.get("_meta", {}),
    })


@router.post("/confirm")
async def confirm_answers(
    request: ConfirmAnswersRequest,
    db = Depends(get_db),
):
    """
    Accept teacher-confirmed/corrected answers, re-run assessment engine
    and report generation. No AI calls — pure computation.

    Returns updated assessment, teacher report, and parent report.
    """
    # Build a vision_result-like dict from confirmed problems
    problems_dicts = [
        {
            "id": p.id,
            "type": p.type.value if hasattr(p.type, 'value') else p.type,
            "child_answer": p.child_answer,
            "correct_answer": p.correct_answer,
            "is_correct": p.is_correct,
            "confidence": p.confidence,
            "handwriting_quality": p.handwriting_quality.value if hasattr(p.handwriting_quality, 'value') else p.handwriting_quality,
            "has_erasure": p.has_erasure,
            "erasure_pattern": p.erasure_pattern.value if hasattr(p.erasure_pattern, 'value') else p.erasure_pattern,
            "strategy_indicators": p.strategy_indicators or "",
        }
        for p in request.problems
    ]

    vision_result = {
        "worksheet_type": "mixed",
        "age_group_hint": request.age_group.value,
        "problems": problems_dicts,
        "observations": request.observations or {},
        "dimension_scores_preliminary": {},
    }

    # Step 1: Re-run assessment with corrected answers (no AI)
    assessment = await assess(
        vision_result=vision_result,
        age_group=request.age_group.value,
        child_name=request.child_name,
    )

    # B6/B8: build child memory to surface "我记得这个孩子" + "对比上次"
    from app.services.memory_service import build_child_memory
    child_memory = None
    if request.child_id is not None:
        child_memory = await build_child_memory(db, request.child_id)

    # Step 2: Re-generate reports (no AI)
    teacher_report = await generate_teacher_report(
        assessment_result=assessment,
        child_name=request.child_name,
        age_group=request.age_group.value,
        worksheet_observations=request.observations,
        child_memory=child_memory,
    )

    parent_report = await generate_parent_report(
        assessment_result=assessment,
        child_name=request.child_name,
        age_group=request.age_group.value,
        child_memory=child_memory,
    )

    # Step 3: Regenerate evaluation trace (per-problem PCK indicator mapping)
    # so the teacher-review → confirm flow also surfaces the 13-sub-dimension
    # breakdown in the UI (previously dropped entirely on confirm).
    from app.services.assessment_engine import generate_evaluation_trace
    evaluation_trace = generate_evaluation_trace(
        vision_result, request.age_group.value, request.child_name
    )

    return JSONResponse(content={
        "assessment": assessment,
        "reports": {
            "teacher": teacher_report,
            "parent": parent_report,
        },
        "evaluation_trace": evaluation_trace,
    })


# ─── Adaptive Difficulty Recommendation (B5) ──────────────────────────

@router.get("/recommend-difficulty")
async def recommend_difficulty_endpoint(
    child_id: int = Query(...),
    db = Depends(get_db),
):
    """
    Recommend a worksheet difficulty level for a child based on their
    assessment history. Drives the 'auto-pick' badge on the generator page.
    """
    from app.services.memory_service import build_child_memory, recommend_difficulty

    memory = await build_child_memory(db, child_id)
    if memory is None:
        raise HTTPException(status_code=404, detail="幼儿不存在")

    rec = recommend_difficulty(memory)
    weak_dims = [
        {"dimension": w["dimension"], "display_name": w["display_name"], "score": w["latest_score"]}
        for w in memory.get("weak_dimensions", [])
    ]
    return {
        "child_id": child_id,
        "child_name": memory.get("child_name"),
        "has_memory": memory.get("has_memory", False),
        "last_accuracy": memory.get("last_accuracy"),
        "session_count": memory.get("session_count", 0),
        "level": rec["level"],
        "reason": rec["reason"],
        "weak_dimensions": weak_dims,
    }


# ─── Worksheet Generation Endpoint ────────────────────────────────────

def _render_worksheet(worksheet, format: str):
    """按 format 渲染操作单（html/pdf/pdf_base64/markdown/json），供 GET/POST 共用。"""
    from app.services.worksheet_generator import (
        worksheet_to_html,
        worksheet_to_markdown,
        worksheet_to_pdf,
    )
    from fastapi.responses import HTMLResponse, JSONResponse, Response
    from urllib.parse import quote
    import base64

    if format == "html":
        return HTMLResponse(content=worksheet_to_html(worksheet))
    if format == "pdf":
        pdf_bytes = worksheet_to_pdf(worksheet)
        filename = "worksheet_" + worksheet.child_name + ".pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition":
                    'attachment; filename="worksheet.pdf"; filename*=UTF-8\'\''
                    + quote(filename),
            },
        )
    if format == "pdf_base64":
        pdf_bytes = worksheet_to_pdf(worksheet)
        return JSONResponse(content={
            "filename": "worksheet_" + worksheet.child_name + ".pdf",
            "content_base64": base64.b64encode(pdf_bytes).decode("ascii"),
        })
    if format == "markdown":
        return JSONResponse(content={"markdown": worksheet_to_markdown(worksheet)})
    # json 兜底
    return JSONResponse(content={
        "title": worksheet.title,
        "child_name": worksheet.child_name,
        "difficulty_level": worksheet.difficulty_level,
        "problems": [
            {
                "number": p.number,
                "type": p.type,
                "dimension": p.dimension,
                "prompt": p.prompt,
                "operation": p.operation,
            }
            for p in worksheet.problems
        ],
        "answer_key": worksheet.answer_key,
    })


async def _generate_worksheet_payload(config, child_memory=None):
    """生成操作单：有 activity_theme 走 AI 情境化（失败降级模板），否则走模板。"""
    import logging
    from app.services.worksheet_generator import generate_worksheet
    from app.services.worksheet_ai_generator import (
        generate_worksheet_with_ai,
        WorksheetAIGenerationError,
        MAX_ACTIVITY_THEME_LENGTH,
    )

    logger = logging.getLogger(__name__)
    if config.activity_theme:
        theme = config.activity_theme
        if len(theme) > MAX_ACTIVITY_THEME_LENGTH:
            from fastapi import HTTPException
            raise HTTPException(
                status_code=422,
                detail=f"活动情境请控制在 {MAX_ACTIVITY_THEME_LENGTH} 字以内",
            )
        try:
            return await generate_worksheet_with_ai(config, theme)
        except WorksheetAIGenerationError as exc:
            # AI 不可用（配额/鉴权/超时/校验失败）→ 降级模板，标注提示
            logger.warning("AI worksheet generation failed, fallback to template: %s", exc)
            worksheet = generate_worksheet(config, child_memory=child_memory)
            worksheet.generation_mode = "fallback"
            worksheet.generation_note = "AI 情境化暂时不可用，已为你生成标准情境操作单，可稍后重试。"
            return worksheet
    return generate_worksheet(config, child_memory=child_memory)


class WorksheetGenerateRequest(BaseModel):
    child_name: str = "小朋友"
    age_group: AgeGroupEnum = AgeGroupEnum.MIDDLE
    difficulty: int = 2
    dimensions: str = "counting,shapes_space"
    problem_count: int = 8
    include_answer: bool = True
    format: str = "markdown"
    activity_theme: Optional[str] = None
    child_id: Optional[int] = None


@router.post("/generate")
async def generate_worksheet_post(body: WorksheetGenerateRequest, db = Depends(get_db)):
    """POST 版生成（长活动情境走 body，避免 URL 长度/编码问题）。"""
    from app.services.worksheet_generator import WorksheetConfig
    from app.services.memory_service import build_child_memory

    dim_list = [d.strip() for d in body.dimensions.split(",") if d.strip()]
    child_memory = None
    if body.child_id is not None:
        child_memory = await build_child_memory(db, body.child_id)
    config = WorksheetConfig(
        child_name=body.child_name,
        age_group=body.age_group.value,
        difficulty_level=body.difficulty,
        dimensions=dim_list,
        problem_count=body.problem_count,
        include_answer_key=body.include_answer,
        activity_theme=(body.activity_theme or "").strip() or None,
    )
    worksheet = await _generate_worksheet_payload(config, child_memory)
    return _render_worksheet(worksheet, body.format)


@router.get("/generate")
async def generate_worksheet_endpoint(
    child_name: str = Query(default="小朋友"),
    age_group: AgeGroupEnum = Query(default=AgeGroupEnum.MIDDLE),
    difficulty: int = Query(default=2, ge=1, le=5),
    dimensions: str = Query(default="counting,shapes_space"),
    problem_count: int = Query(default=8, ge=4, le=20),
    include_answer: bool = Query(default=True),
    format: str = Query(default="html"),
    child_id: Optional[int] = Query(default=None),
    auto_difficulty: bool = Query(default=False),
    db = Depends(get_db),
):
    """
    Generate a printable worksheet dynamically.
    Returns HTML (for preview/print) or JSON.

    When child_id + auto_difficulty are provided, the difficulty is derived
    from the child's assessment history (B5) and weak dimensions are injected
    into dimension selection (B6).
    """
    from app.services.worksheet_generator import (
        generate_worksheet,
        worksheet_to_html,
        worksheet_to_markdown,
        worksheet_to_pdf,
        WorksheetConfig,
    )
    from app.services.memory_service import build_child_memory, recommend_difficulty
    from fastapi.responses import HTMLResponse

    dim_list = [d.strip() for d in dimensions.split(",") if d.strip()]

    # B5/B6: pull child memory to drive difficulty + weak-dimension targeting
    child_memory = None
    resolved_difficulty = difficulty
    difficulty_reason = None
    if child_id is not None:
        child_memory = await build_child_memory(db, child_id)
        if child_memory and child_memory.get("has_memory") and auto_difficulty:
            rec = recommend_difficulty(child_memory)
            resolved_difficulty = rec["level"]
            difficulty_reason = rec["reason"]
            # B6: if caller used default dimensions, target prior weak dims
            if not dimensions or dimensions == "counting,shapes_space":
                weak_dims = [w["dimension"] for w in child_memory.get("weak_dimensions", [])]
                if weak_dims:
                    dim_list = weak_dims[:2]

    config = WorksheetConfig(
        child_name=child_name,
        age_group=age_group.value,
        difficulty_level=resolved_difficulty,
        dimensions=dim_list,
        problem_count=problem_count,
        include_answer_key=include_answer,
        activity_theme=(activity_theme or "").strip() or None,
    )

    worksheet = await _generate_worksheet_payload(config, child_memory)

    return _render_worksheet(worksheet, format)
