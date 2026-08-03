"""
Dashboard API routes — trend charts, class overviews, semester comparisons, Excel export.
"""

import hashlib
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_teacher
from app.services.dashboard_service import (
    get_child_trajectory,
    get_class_overview,
    get_semester_comparison,
)
from app.services.excel_exporter import export_class_roster, export_child_report

router = APIRouter()


# ─── Child Trajectory ────────────────────────────────────────────────

@router.get("/child/{child_id}/trajectory")
async def child_trajectory(
    child_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_teacher),
):
    """Get a child's growth trajectory across all dimensions over time."""
    data = await get_child_trajectory(db, child_id)
    if data is None:
        raise HTTPException(status_code=404, detail=f"未找到幼儿 (ID: {child_id})")
    return JSONResponse(content=data)


# ─── Class Overview ──────────────────────────────────────────────────

@router.get("/class/{class_name}/overview")
async def class_overview(
    class_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_teacher),
):
    """Get aggregated overview for a class (averages, level distribution, strengths/needs)."""
    data = await get_class_overview(db, class_name)
    return JSONResponse(content=data)


@router.get("/class/{class_name}/semester-compare")
async def semester_compare(
    class_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_teacher),
):
    """Compare current vs previous semester for a class."""
    data = await get_semester_comparison(db, class_name)
    return JSONResponse(content=data)


# ─── Excel Export ─────────────────────────────────────────────────────

@router.get("/export/class/{class_name}")
async def export_class_excel(
    class_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_teacher),
):
    """Export class roster as Excel (.xlsx)."""
    try:
        data = await export_class_roster(db, class_name)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Use hash of class_name to ensure ASCII-only filename (avoids UnicodeEncodeError)
    safe_name = hashlib.md5(class_name.encode()).hexdigest()[:8]
    filename = f"{safe_name}_class_roster.xlsx"
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(data)),
        },
    )


@router.get("/export/child/{child_id}")
async def export_child_excel(
    child_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_teacher),
):
    """Export a single child's assessment history as Excel (.xlsx)."""
    try:
        data = await export_child_report(db, child_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="child_{child_id}_report.xlsx"',
            "Content-Length": str(len(data)),
        },
    )
