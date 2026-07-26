"""
Children CRUD API routes.
Manage classroom children records — create, list, get, update, delete.
Uses SQLAlchemy async database for persistent storage.
"""

import secrets
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.core.database import get_db
from app.core.security import get_current_teacher
from app.schemas import AgeGroupEnum, ChildCreate, ChildResponse
from app.models import Child
from app.services.csv_importer import import_children_from_csv

router = APIRouter()


# ─── Routes ───────────────────────────────────────────────────────────

@router.get("")
async def list_children(
    age_group: Optional[AgeGroupEnum] = Query(default=None, description="按年龄段筛选"),
    class_name: Optional[str] = Query(default=None, description="按班级筛选"),
    search: Optional[str] = Query(default=None, description="按姓名搜索"),
    db: AsyncSession = Depends(get_db),
    _current_user: dict = Depends(get_current_teacher),
):
    """
    List all children in the classroom.
    Supports optional filtering by age_group, class_name, and name search.
    Requires teacher authentication.
    """
    stmt = select(Child).order_by(Child.created_at.desc())

    if age_group:
        stmt = stmt.where(Child.age_group == age_group.value)

    if class_name:
        stmt = stmt.where(Child.class_name == class_name)

    if search:
        stmt = stmt.where(Child.name.ilike(f"%{search}%"))

    result = await db.execute(stmt)
    children = result.scalars().all()

    return {
        "count": len(children),
        "children": [ChildResponse.model_validate(c).model_dump(mode="json") for c in children],
    }


@router.post("")
async def create_child(
    request: ChildCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_teacher),
):
    """
    Create a new child record.
    Requires teacher authentication.
    """
    # Generate a unique parent access code
    access_code = secrets.token_hex(4).upper()  # 8-char random code

    child = Child(
        name=request.name,
        age_group=request.age_group.value if hasattr(request.age_group, 'value') else request.age_group,
        class_name=request.class_name,
        birth_date=request.birth_date,
        parent_access_code=access_code,
        notes=request.notes,
    )

    db.add(child)
    await db.flush()
    await db.refresh(child)

    return JSONResponse(
        status_code=201,
        content=ChildResponse.model_validate(child).model_dump(mode="json"),
    )


@router.get("/class-summary")
async def get_class_summary(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_teacher),
):
    """
    Get per-class child counts and age distribution.
    Requires teacher authentication.
    """
    result = await db.execute(select(Child).order_by(Child.class_name, Child.age_group))
    children = result.scalars().all()

    classes: dict = {}
    for c in children:
        cn = c.class_name or "未分班"
        if cn not in classes:
            classes[cn] = {"class_name": cn, "total": 0, "age_groups": {"small": 0, "middle": 0, "large": 0}}
        classes[cn]["total"] += 1
        ag = c.age_group.value if hasattr(c.age_group, 'value') else str(c.age_group)
        if ag in classes[cn]["age_groups"]:
            classes[cn]["age_groups"][ag] += 1

    return {
        "total_classes": len(classes),
        "total_children": len(children),
        "classes": sorted(classes.values(), key=lambda x: x["class_name"]),
    }


@router.get("/{child_id}")
async def get_child(
    child_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_teacher),
):
    """
    Get a single child's details.
    Requires teacher authentication.
    """
    child = await db.get(Child, child_id)
    if not child:
        raise HTTPException(status_code=404, detail=f"未找到幼儿 (ID: {child_id})")

    return ChildResponse.model_validate(child).model_dump(mode="json")


@router.put("/{child_id}")
async def update_child(
    child_id: int,
    request: ChildCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_teacher),
):
    """
    Update a child's information.
    Requires teacher authentication.
    """
    child = await db.get(Child, child_id)
    if not child:
        raise HTTPException(status_code=404, detail=f"未找到幼儿 (ID: {child_id})")

    age_val = request.age_group.value if hasattr(request.age_group, 'value') else request.age_group

    child.name = request.name
    child.age_group = age_val
    child.class_name = request.class_name
    child.birth_date = request.birth_date
    child.notes = request.notes

    await db.flush()
    await db.refresh(child)

    return ChildResponse.model_validate(child).model_dump(mode="json")


@router.delete("/{child_id}")
async def delete_child(
    child_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_teacher),
):
    """
    Delete a child record.
    Requires teacher authentication (admin only in production).
    """
    child = await db.get(Child, child_id)
    if not child:
        raise HTTPException(status_code=404, detail=f"未找到幼儿 (ID: {child_id})")

    await db.delete(child)
    await db.flush()

    return JSONResponse(
        content={"status": "deleted", "child_id": child_id, "message": "幼儿记录已删除"},
    )


@router.get("/{child_id}/stats")
async def get_child_stats(
    child_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_teacher),
):
    """
    Get summary statistics for a child.
    Includes worksheet count, last assessment date, dimension summaries.
    """
    child = await db.get(Child, child_id)
    if not child:
        raise HTTPException(status_code=404, detail=f"未找到幼儿 (ID: {child_id})")

    # Count worksheets for this child
    from app.models import Worksheet
    ws_result = await db.execute(
        select(func.count(Worksheet.id)).where(Worksheet.child_id == child_id)
    )
    worksheet_count = ws_result.scalar() or 0

    # Get latest assessment
    from app.models import AbilityAssessment
    latest_result = await db.execute(
        select(AbilityAssessment.assessed_at)
        .where(AbilityAssessment.child_id == child_id)
        .order_by(AbilityAssessment.assessed_at.desc())
        .limit(1)
    )
    last_assessment = latest_result.scalar()

    return {
        "child_id": child_id,
        "name": child.name,
        "worksheet_count": worksheet_count,
        "last_assessment": last_assessment.isoformat() if last_assessment else None,
        "dimension_summary": {},
        "growth_trend": "stable",
    }


@router.get("/{child_id}/reports")
async def get_child_reports(
    child_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_teacher),
):
    """
    Get all reports for a child, with recent assessment summaries.
    Requires teacher authentication.
    """
    child = await db.get(Child, child_id)
    if not child:
        raise HTTPException(status_code=404, detail=f"未找到幼儿 (ID: {child_id})")

    # Fetch reports
    from app.models import Report, AbilityAssessment
    from sqlalchemy import desc

    report_result = await db.execute(
        select(Report)
        .where(Report.child_id == child_id)
        .order_by(desc(Report.generated_at))
    )
    reports = report_result.scalars().all()

    # Fetch recent assessments
    assess_result = await db.execute(
        select(AbilityAssessment)
        .where(AbilityAssessment.child_id == child_id)
        .order_by(desc(AbilityAssessment.assessed_at))
        .limit(20)
    )
    assessments = assess_result.scalars().all()

    report_list = []
    for r in reports:
        content = r.content_json or {}
        report_list.append({
            "report_id": r.id,
            "type": r.report_type.value if r.report_type else "unknown",
            "generated_at": r.generated_at.isoformat() if r.generated_at else None,
            "summary": content.get("overall_summary", "")[:200],
            "dimensions": [
                {"name": d.get("display_name", ""), "score": d.get("score", 0), "level": d.get("level_name", "")}
                for d in content.get("dimensions", content.get("assessment", []))
            ][:4],
        })

    return {
        "child": {
            "id": child.id,
            "name": child.name,
            "age_group": child.age_group.value if hasattr(child.age_group, 'value') else child.age_group,
            "class_name": child.class_name,
        },
        "reports": report_list,
        "recent_assessments": [
            {
                "dimension": a.dimension,
                "score": a.score,
                "level": a.level.value if hasattr(a.level, 'value') else str(a.level),
                "assessed_at": a.assessed_at.isoformat() if a.assessed_at else None,
            }
            for a in assessments
        ],
        "worksheet_count": len(reports),
    }


# ─── Batch Import ─────────────────────────────────────────────────────

@router.post("/import")
async def import_children(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_teacher),
):
    """
    Batch import children from a CSV or Excel file.

    Expected columns: name (required), age_group (required: small/middle/large),
                      class_name (optional), birth_date (optional), notes (optional).

    Supports CSV (UTF-8/GBK) and Excel (.xlsx) formats.
    Max file size: 5MB.
    """
    # Validate file type
    filename = file.filename or "import.csv"
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in ("csv", "xlsx", "xls"):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件格式 ({ext})。请上传 CSV 或 Excel (.xlsx) 文件。",
        )

    # Read file
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过 5MB")

    # Import
    result = await import_children_from_csv(db, contents, filename)

    status_code = 200 if result["imported"] > 0 else 400
    return JSONResponse(content={
        "status": "success" if result["imported"] > 0 else "error",
        **result,
    }, status_code=status_code)


# ─── Class Summary ────────────────────────────────────────────────────
