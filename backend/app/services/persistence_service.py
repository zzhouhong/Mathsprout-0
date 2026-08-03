"""
Persistence service — bridges the analysis pipeline to the database.

Before this module, the entire analysis pipeline was compute-only:
results were returned as JSON and discarded. This module saves:
  Worksheet → AnalysisResult → ProblemResult[] → AbilityAssessment[]
  → Report (teacher) → Report (parent) → AIRequestLog
"""

import time
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Child,
    Worksheet,
    AnalysisResult,
    ProblemResult,
    AbilityAssessment,
    Report,
    AIRequestLog,
)
from app.models.enums import (
    WorksheetStatusEnum,
    UploadMethodEnum,
    LevelEnum,
    ReportTypeEnum,
)


# Problem type → dimension mapping (mirrors assessment_engine.py)
PROBLEM_TYPE_TO_DIMENSION: Dict[str, str] = {
    "counting": "counting",
    "add_10": "addition_sub",
    "sub_10": "addition_sub",
    "number_composition": "counting",
    "shape_id": "shapes_space",
    "spatial": "shapes_space",
    "pattern_next": "patterns",
    "classify": "patterns",
    "compare": "counting",
    "sort": "patterns",
}


async def persist_analysis(
    db: AsyncSession,
    child_id: int,
    original_filename: str,
    image_bytes: bytes,
    vision_result: dict,
    assessment_result: dict,
    teacher_report: dict,
    parent_report: dict,
    age_group: str = "middle",
    upload_method: str = "file",
) -> dict:
    """
    Persist the full analysis pipeline result to the database.

    Creates: Worksheet, AnalysisResult, ProblemResult[], AbilityAssessment[],
             Report (teacher), Report (parent), AIRequestLog

    Returns dict with created record IDs.
    """
    meta = vision_result.get("_meta", {})
    usage = meta.get("usage", {})
    now_ms = int(time.time() * 1000)

    # 1. Worksheet
    worksheet = Worksheet(
        child_id=child_id,
        file_path=f"uploads/{original_filename}",
        original_filename=original_filename,
        status=WorksheetStatusEnum.ANALYZED,
        upload_method=UploadMethodEnum.FILE,
    )
    db.add(worksheet)
    await db.flush()

    # 2. AnalysisResult
    analysis = AnalysisResult(
        worksheet_id=worksheet.id,
        raw_response=vision_result,
        model_used=meta.get("model", "unknown"),
        token_usage=usage,
        age_group_anchor=age_group,
    )
    db.add(analysis)
    await db.flush()

    # 3. ProblemResult[] — one per recognized problem
    problems = vision_result.get("problems", [])
    for p in problems:
        p_type = p.get("type", "unknown")
        dimension = PROBLEM_TYPE_TO_DIMENSION.get(p_type, "counting")
        pr = ProblemResult(
            analysis_id=analysis.id,
            problem_id=p.get("id", "?"),
            problem_type=p_type,
            child_answer=str(p.get("child_answer", "")),
            correct_answer=str(p.get("correct_answer", "")),
            is_correct=bool(p.get("is_correct", False)),
            confidence=float(p.get("confidence", 0.5)),
            strategy_indicators=p.get("strategy_indicators"),
            erasure_pattern=p.get("erasure_pattern"),
            dimension=dimension,
        )
        db.add(pr)

    # 4. AbilityAssessment[] — one per dimension
    assessment_list = assessment_result.get("assessment", [])
    for dim in assessment_list:
        level_str = dim.get("level", "L1")
        try:
            level_enum = LevelEnum(level_str)
        except ValueError:
            level_enum = LevelEnum.L1

        aa = AbilityAssessment(
            child_id=child_id,
            dimension=dim.get("dimension", "unknown"),
            score=float(dim.get("score", 0)),
            level=level_enum,
            pck_stage=dim.get("pck_stage"),
            error_patterns=dim.get("error_patterns", []),
            age_benchmark_comparison=dim.get("age_benchmark_comparison"),
            recommendations=dim.get("recommendations"),
        )
        db.add(aa)

    # 5. Reports (teacher + parent)
    report_teacher = Report(
        child_id=child_id,
        worksheet_id=worksheet.id,
        report_type=ReportTypeEnum.TEACHER,
        content_json=teacher_report,
    )
    db.add(report_teacher)

    report_parent = Report(
        child_id=child_id,
        worksheet_id=worksheet.id,
        report_type=ReportTypeEnum.PARENT,
        content_json=parent_report,
    )
    db.add(report_parent)
    await db.flush()

    # 6. AIRequestLog
    req_log = AIRequestLog(
        worksheet_id=worksheet.id,
        model_used=meta.get("model", "unknown"),
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        caching_hit=meta.get("cache_hit", False),
    )
    db.add(req_log)

    await db.commit()

    return {
        "worksheet_id": worksheet.id,
        "analysis_id": analysis.id,
        "report_teacher_id": report_teacher.id,
        "report_parent_id": report_parent.id,
        "problem_count": len(problems),
        "dimension_count": len(assessment_list),
    }
