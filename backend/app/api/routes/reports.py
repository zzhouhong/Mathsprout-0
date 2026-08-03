from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse, Response
from typing import Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas import ReportTypeEnum, AgeGroupEnum
from app.services.report_generator import generate_teacher_report, generate_parent_report
from app.services.pdf_exporter import generate_teacher_pdf, generate_parent_pdf
from app.services.assessment_engine import assess
from app.core.prompts.pck_reference import (
    AgeGroup,
    get_age_display_name,
    get_dimension_display_name,
)
from app.core.security import get_current_teacher, get_current_user
from app.models import Report, ReportAnnotation

router = APIRouter()


async def _save_report_to_db(
    db: AsyncSession,
    report_type: str,
    content: dict,
    child_id: int,
    worksheet_id: Optional[int] = None,
) -> int:
    """Persist a generated report to DB and return its ID."""
    report = Report(
        child_id=child_id,
        worksheet_id=worksheet_id,
        report_type=ReportTypeEnum(report_type),
        content_json=content,
    )
    db.add(report)
    await db.flush()
    await db.refresh(report)
    return report.id


async def _get_report_from_db(
    db: AsyncSession, report_id: int, expected_type: Optional[str] = None
) -> Report:
    """Fetch a report by ID, optionally checking type. Raises 404 if not found."""
    report = await db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"未找到报告 (ID: {report_id})")
    if expected_type and report.report_type.value != expected_type:
        raise HTTPException(status_code=404, detail=f"未找到{expected_type}报告 (ID: {report_id})")
    return report


# ─── Dynamic Report Generation ───────────────────────────────────────

@router.post("/generate/{report_type}")
async def generate_report(
    report_type: ReportTypeEnum,
    assessment_data: dict,
    child_name: str = "幼儿",
    age_group: AgeGroupEnum = AgeGroupEnum.MIDDLE,
    child_id: Optional[int] = Query(default=None, description="幼儿ID，提供则持久化到DB"),
    worksheet_id: Optional[int] = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate a report from assessment data.

    - report_type: "teacher" or "parent"
    - assessment_data: Full assessment result dict
    - child_id: If provided, persist report to DB linked to the child
    """
    if report_type == ReportTypeEnum.TEACHER:
        report = await generate_teacher_report(
            assessment_result=assessment_data,
            child_name=child_name,
            age_group=age_group.value,
            worksheet_observations=assessment_data.get("observations"),
        )
    else:
        report = await generate_parent_report(
            assessment_result=assessment_data,
            child_name=child_name,
            age_group=age_group.value,
        )

    # Persist if child_id provided
    report_id = None
    if child_id is not None:
        report_id = await _save_report_to_db(
            db, report_type.value, report, child_id, worksheet_id,
        )

    response = dict(report)
    response["report_id"] = report_id
    response["persisted"] = child_id is not None

    return JSONResponse(content=response)


# ─── Get Report by ID (from DB) ──────────────────────────────────────

@router.get("/teacher/{report_id}")
async def get_teacher_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Get teacher version of a report. Requires authentication."""
    report = await _get_report_from_db(db, report_id, "teacher")
    return JSONResponse(content={
        "report_id": report.id,
        "child_id": report.child_id,
        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
        **report.content_json,
    })


@router.get("/parent/{report_id}")
async def get_parent_report(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get parent version of a report. Public access."""
    report = await _get_report_from_db(db, report_id, "parent")
    return JSONResponse(content={
        "report_id": report.id,
        "child_id": report.child_id,
        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
        **report.content_json,
    })


@router.get("/history/{child_id}")
async def get_report_history(
    child_id: int,
    report_type: Optional[ReportTypeEnum] = Query(default=None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_teacher),
):
    """List all saved reports for a child. Requires teacher authentication."""
    stmt = select(Report).where(Report.child_id == child_id)
    if report_type:
        stmt = stmt.where(Report.report_type == report_type)
    stmt = stmt.order_by(Report.generated_at.desc())

    result = await db.execute(stmt)
    reports = result.scalars().all()

    results = []
    for r in reports:
        content = r.content_json or {}
        results.append({
            "report_id": r.id,
            "type": r.report_type.value if r.report_type else "unknown",
            "child_id": r.child_id,
            "generated_at": r.generated_at.isoformat() if r.generated_at else None,
            "summary": content.get("overall_summary", "")[:120],
        })

    return JSONResponse(content={
        "child_id": child_id,
        "count": len(results),
        "reports": results,
    })


# ─── PDF Export (from DB) ────────────────────────────────────────────

@router.get("/{report_id}/pdf/teacher")
async def export_teacher_pdf(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Export a teacher report as PDF. Requires authentication."""
    report = await _get_report_from_db(db, report_id, "teacher")
    pdf_bytes = generate_teacher_pdf(report.content_json)
    filename = f"report_{report_id}_teacher_{_format_filename_date(report.generated_at)}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


@router.get("/{report_id}/pdf/parent")
async def export_parent_pdf(
    report_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Export a parent report as PDF. Public access."""
    report = await _get_report_from_db(db, report_id, "parent")
    pdf_bytes = generate_parent_pdf(report.content_json)
    filename = f"report_{report_id}_parent_{_format_filename_date(report.generated_at)}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
        },
    )


def _format_filename_date(dt_val) -> str:
    """Format datetime to compact filename-safe string."""
    if dt_val is None:
        return "unknown"
    if isinstance(dt_val, str):
        try:
            dt_val = datetime.fromisoformat(dt_val)
        except (ValueError, TypeError):
            return "unknown"
    return dt_val.strftime("%Y%m%d")


# ─── Annotations (in-memory, per-report) ────────────────────────────

@router.post("/{report_id}/annotations")
async def add_annotation(
    report_id: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_teacher),
):
    """Add a teaching annotation to a report. Shared among teachers.

    存储到 report_annotations 表（DB），重启后端不会丢失。
    """
    # Verify report exists in DB
    await _get_report_from_db(db, report_id)

    text = (body.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="批注内容不能为空")
    if len(text) > 500:
        raise HTTPException(status_code=400, detail="批注内容不超过500字")

    annotation = ReportAnnotation(
        report_id=report_id,
        author_email=current_user.get("email"),
        author_name=current_user.get("name") or current_user.get("email", "教师"),
        text=text,
        dimension=body.get("dimension"),
    )
    db.add(annotation)
    await db.commit()
    await db.refresh(annotation)

    return JSONResponse(
        content={
            "id": annotation.id,
            "report_id": annotation.report_id,
            "author": annotation.author_name,
            "text": annotation.text,
            "dimension": annotation.dimension,
            "created_at": annotation.created_at.isoformat() if annotation.created_at else None,
        },
        status_code=201,
    )


@router.get("/{report_id}/annotations")
async def list_annotations(
    report_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List all annotations for a report. Requires authentication."""
    await _get_report_from_db(db, report_id)

    result = await db.execute(
        select(ReportAnnotation)
        .where(ReportAnnotation.report_id == report_id)
        .order_by(ReportAnnotation.created_at.desc())
    )
    annotations = result.scalars().all()
    return JSONResponse(
        content={
            "report_id": report_id,
            "count": len(annotations),
            "annotations": [
                {
                    "id": a.id,
                    "report_id": a.report_id,
                    "author": a.author_name,
                    "text": a.text,
                    "dimension": a.dimension,
                    "created_at": a.created_at.isoformat() if a.created_at else None,
                }
                for a in annotations
            ],
        }
    )


@router.delete("/{report_id}/annotations/{annotation_id}")
async def delete_annotation(
    report_id: int,
    annotation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete an annotation. Only authenticated users can delete."""
    result = await db.execute(
        select(ReportAnnotation).where(
            ReportAnnotation.id == annotation_id,
            ReportAnnotation.report_id == report_id,
        )
    )
    annotation = result.scalar_one_or_none()
    if not annotation:
        raise HTTPException(status_code=404, detail="批注不存在")
    await db.delete(annotation)
    await db.commit()
    return JSONResponse(content={"deleted": True})


# ─── Demo Reports ────────────────────────────────────────────────────

@router.get("/demo/teacher")
async def get_demo_teacher_report(
    age_group: AgeGroupEnum = Query(default=AgeGroupEnum.MIDDLE),
    child_name: str = Query(default="小明"),
):
    """Generate a demo teacher report with sample assessment data."""
    age = age_group.value
    demo_assessment = _build_demo_assessment(child_name, age)
    report = await generate_teacher_report(
        assessment_result=demo_assessment,
        child_name=child_name,
        age_group=age,
        worksheet_observations=demo_assessment.get("observations"),
    )
    return JSONResponse(content=report)


@router.get("/demo/parent")
async def get_demo_parent_report(
    age_group: AgeGroupEnum = Query(default=AgeGroupEnum.MIDDLE),
    child_name: str = Query(default="小明"),
):
    """Generate a demo parent report with sample assessment data."""
    age = age_group.value
    demo_assessment = _build_demo_assessment(child_name, age)
    report = await generate_parent_report(
        assessment_result=demo_assessment,
        child_name=child_name,
        age_group=age,
    )
    return JSONResponse(content=report)


# ─── Demo Data Builder ───────────────────────────────────────────────

def _build_demo_assessment(child_name: str, age_group: str) -> dict:
    """Build sample assessment data for demo reports."""
    age_display = get_age_display_name(age_group)
    return {
        "child_name": child_name,
        "age_group": age_group,
        "age_display": age_display,
        "assessment": [
            {
                "dimension": "counting",
                "display_name": "数概念与运算",
                "score": 78.0,
                "level": "L3",
                "level_name": "熟练期",
                "level_emoji": "🌳",
                "pck_stage": "前运算阶段后期：趋于符号表征",
                "sub_skills": [
                    {"name": "点数准确性", "score": 85.0, "max_score": 100.0},
                    {"name": "按数取物", "score": 80.0, "max_score": 100.0},
                    {"name": "数量比较", "score": 75.0, "max_score": 100.0},
                    {"name": "序数理解", "score": 70.0, "max_score": 100.0},
                    {"name": "数的组成", "score": 80.0, "max_score": 100.0},
                    {"name": "数量守恒", "score": 78.0, "max_score": 100.0},
                ],
                "error_patterns": [],
                "age_benchmark_comparison": f"符合{age_display}发展期望，核心经验基本建立",
                "age_milestones": "能手口一致地点数10以内物体，说出总数；理解序数",
                "recommendations": "建议增加序数练习和数的组成活动。推荐活动：'数筷子'游戏。",
                "score_details": {"correct": 8, "total": 10, "strategy_level": "semi_concrete"},
            },
            {
                "dimension": "addition_sub",
                "display_name": "数运算能力",
                "score": 55.0,
                "level": "L2",
                "level_name": "发展期",
                "level_emoji": "🌿",
                "pck_stage": "前运算阶段中期：半具象表征过渡",
                "sub_skills": [
                    {"name": "实物操作正确率", "score": 80.0, "max_score": 100.0},
                    {"name": "符号运算正确率", "score": 30.0, "max_score": 100.0},
                    {"name": "策略水平", "score": 50.0, "max_score": 100.0},
                    {"name": "应用题理解", "score": 60.0, "max_score": 100.0},
                    {"name": "运算思维灵活性", "score": 55.0, "max_score": 100.0},
                ],
                "error_patterns": ["实物依赖：不用实物就不会算"],
                "age_benchmark_comparison": f"部分达到{age_display}期望，核心经验正在形成中",
                "age_milestones": "借助实物操作进行10以内的加减；开始用点卡、手指等半具象策略",
                "recommendations": "建议逐步引入半具象材料（点卡、手指计数）。推荐活动：'分水果'角色扮演游戏。",
                "score_details": {"correct": 3, "total": 5, "strategy_level": "concrete_objects"},
            },
            {
                "dimension": "shapes_space",
                "display_name": "图形与空间",
                "score": 90.0,
                "level": "L3",
                "level_name": "熟练期",
                "level_emoji": "🌳",
                "pck_stage": "前运算阶段后期：趋于符号表征",
                "sub_skills": [
                    {"name": "平面图形识别", "score": 95.0, "max_score": 100.0},
                    {"name": "立体图形识别", "score": 85.0, "max_score": 100.0},
                    {"name": "图形特征描述", "score": 90.0, "max_score": 100.0},
                    {"name": "空间方位", "score": 90.0, "max_score": 100.0},
                    {"name": "图形组合与分解", "score": 90.0, "max_score": 100.0},
                ],
                "error_patterns": [],
                "age_benchmark_comparison": f"符合{age_display}发展期望，核心经验基本建立",
                "age_milestones": "能识别长方形、半圆形、椭圆形、梯形；以自身为中心区分左右",
                "recommendations": "建议增加图形组合创作活动。推荐活动：'形状寻宝'游戏。",
                "score_details": {"correct": 8, "total": 9, "strategy_level": "symbolic"},
            },
            {
                "dimension": "patterns",
                "display_name": "集合与模式",
                "score": 45.0,
                "level": "L2",
                "level_name": "发展期",
                "level_emoji": "🌿",
                "pck_stage": "前运算阶段中期：半具象表征过渡",
                "sub_skills": [
                    {"name": "分类能力", "score": 60.0, "max_score": 100.0},
                    {"name": "模式识别", "score": 50.0, "max_score": 100.0},
                    {"name": "模式扩展", "score": 40.0, "max_score": 100.0},
                    {"name": "模式创造", "score": 30.0, "max_score": 100.0},
                    {"name": "排序能力", "score": 45.0, "max_score": 100.0},
                    {"name": "规律语言描述", "score": 45.0, "max_score": 100.0},
                ],
                "error_patterns": [
                    "模式理解表面化：只能复制AB模式，无法扩展",
                    "分类标准漂移：分类中途切换标准",
                ],
                "age_benchmark_comparison": f"部分达到{age_display}期望，核心经验正在形成中",
                "age_milestones": "能识别、复制、扩展ABC/AABB模式；按规律排序",
                "recommendations": "建议通过穿珠子、排队游戏加强模式理解。推荐活动：'穿珠子'模式游戏。",
                "score_details": {"correct": 3, "total": 6, "strategy_level": "AB_copy"},
            },
        ],
        "observations": {
            "number_formation_issues": ["mirror_3"],
            "attention_indicators": "careful",
            "task_completion_context": "independent",
            "overall_pck_notes": (
                "该幼儿在点数和图形识别方面表现良好，"
                "加减运算仍依赖实物操作，模式理解处于AB复制阶段——"
                f"符合{age_display}上学期典型发展特征。"
            ),
        },
        "overall_summary": (
            f"这是一份关于{child_name}（{age_display}）数学操作单的观察分析。"
            f"在数概念与运算、图形与空间方面表现出良好的发展态势。"
            f"在数运算能力、集合与模式方面，正处于自然的学习成长过程中，"
            f"这是{age_display}小朋友的正常发展阶段。"
        ),
    }
