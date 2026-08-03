"""
Parent-facing API for WeChat mini-program access.

Parents authenticate via child's parent_access_code (no WeChat login required for MVP).
Once bound, they can view their child's reports and growth trends.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.models import Child, Report, AbilityAssessment

router = APIRouter()


@router.post("/bind")
async def parent_bind(
    body: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    Bind a parent to a child using the parent_access_code.
    Returns child info and a simple session token.

    Request: {"access_code": "XIAOMING01"}
    """
    code = (body.get("access_code") or "").strip().upper()
    if not code or len(code) < 6:
        raise HTTPException(status_code=400, detail="请输入有效的家长访问码（6-8位）")

    result = await db.execute(
        select(Child).where(Child.parent_access_code == code)
    )
    child = result.scalars().first()
    if not child:
        raise HTTPException(status_code=404, detail="访问码无效，请检查后重试")

    return {
        "child_id": child.id,
        "child_name": child.name,
        "age_group": child.age_group.value if hasattr(child.age_group, 'value') else child.age_group,
        "class_name": child.class_name,
        "token": f"parent_{child.id}_{child.parent_access_code}",
    }


@router.get("/child-profile")
async def child_profile(
    child_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Get bound child's basic info."""
    child = await db.get(Child, child_id)
    if not child:
        raise HTTPException(status_code=404, detail="幼儿不存在")

    return {
        "child_id": child.id,
        "name": child.name,
        "age_group": child.age_group.value if hasattr(child.age_group, 'value') else child.age_group,
        "class_name": child.class_name,
        "notes": child.notes,
    }


@router.get("/latest-report")
async def latest_report(
    child_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Get the most recent parent report for the bound child."""
    result = await db.execute(
        select(Report)
        .where(Report.child_id == child_id, Report.report_type == "parent")
        .order_by(desc(Report.generated_at))
        .limit(1)
    )
    report = result.scalars().first()
    if not report:
        return JSONResponse(content={"has_report": False, "message": "暂无分析报告"})

    content = report.content_json or {}
    return {
        "has_report": True,
        "report_id": report.id,
        "generated_at": report.generated_at.isoformat() if report.generated_at else None,
        "overall_summary": content.get("overall_summary", ""),
        "strengths": content.get("strengths", []),
        "growing_areas": content.get("growing_areas", []),
        "family_activities": content.get("family_activities", [])[:3],
        "learning_quality_notes": content.get("learning_quality_notes", ""),
        "parent_tips": content.get("parent_tips", ""),
    }


@router.get("/report-history")
async def report_history(
    child_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """List all reports for the bound child (parent-friendly summaries)."""
    result = await db.execute(
        select(Report)
        .where(Report.child_id == child_id)
        .order_by(desc(Report.generated_at))
    )
    reports = result.scalars().all()

    items = []
    for r in reports:
        content = r.content_json or {}
        items.append({
            "report_id": r.id,
            "type": r.report_type.value if r.report_type else "unknown",
            "generated_at": r.generated_at.isoformat() if r.generated_at else None,
            "summary": (content.get("overall_summary") or "")[:150],
            "strengths_count": len(content.get("strengths", [])),
        })

    return {"child_id": child_id, "count": len(items), "reports": items}


@router.get("/growth-trend")
async def growth_trend(
    child_id: int = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Get simplified per-dimension growth over time (for mini-program display)."""
    result = await db.execute(
        select(AbilityAssessment)
        .where(AbilityAssessment.child_id == child_id)
        .order_by(AbilityAssessment.assessed_at)
    )
    assessments = result.scalars().all()

    # Group by dimension
    dims: dict = {}
    for a in assessments:
        if a.dimension not in dims:
            dims[a.dimension] = []
        dims[a.dimension].append({
            "date": a.assessed_at.strftime("%Y-%m-%d") if a.assessed_at else "",
            "score": a.score,
            "level": a.level.value if hasattr(a.level, 'value') else str(a.level),
        })

    # Determine trend
    trends = {}
    for dim, points in dims.items():
        if len(points) >= 2:
            diff = points[-1]["score"] - points[0]["score"]
            trends[dim] = "up" if diff > 5 else "down" if diff < -5 else "stable"
        else:
            trends[dim] = "first_assessment"

    dim_names = {
        "counting": "数数", "addition_sub": "加减", "shapes_space": "图形", "patterns": "模式"
    }

    return {
        "child_id": child_id,
        "dimensions": {
            dim_names.get(d, d): {"points": pts, "trend": trends.get(d, "")}
            for d, pts in dims.items()
        },
    }
