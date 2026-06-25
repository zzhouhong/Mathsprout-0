"""
Dashboard data service — aggregates analysis data for trend charts and class overviews.

Provides:
- Child growth trajectory (per-dimension scores over time)
- Class overview (average scores, level distribution, common strengths/needs)
- Semester comparison (current vs previous)
"""

from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Child, AbilityAssessment, Report, Worksheet


async def get_child_trajectory(
    db: AsyncSession,
    child_id: int,
) -> Dict[str, Any]:
    """
    Get a child's growth trajectory across all dimensions over time.

    Returns per-dimension score history sorted by assessment date.
    """
    child = await db.get(Child, child_id)
    if not child:
        return None

    result = await db.execute(
        select(AbilityAssessment)
        .where(AbilityAssessment.child_id == child_id)
        .order_by(AbilityAssessment.assessed_at)
    )
    assessments = result.scalars().all()

    # Group by dimension → list of {date, score, level}
    dimensions: Dict[str, List[Dict]] = {}
    for a in assessments:
        dim = a.dimension
        if dim not in dimensions:
            dimensions[dim] = []
        dimensions[dim].append({
            "date": a.assessed_at.isoformat() if a.assessed_at else None,
            "score": a.score,
            "level": a.level.value if hasattr(a.level, 'value') else str(a.level),
            "pck_stage": a.pck_stage,
        })

    # Build trajectory points (one per assessment session, identified by date)
    dates = sorted(set(
        a.assessed_at.strftime("%Y-%m-%d") if a.assessed_at else "unknown"
        for a in assessments
    ))

    chart_data = []
    for date_str in dates:
        point = {"date": date_str}
        date_assessments = [
            a for a in assessments
            if a.assessed_at and a.assessed_at.strftime("%Y-%m-%d") == date_str
        ]
        for a in date_assessments:
            point[a.dimension] = a.score
        chart_data.append(point)

    # Latest scores summary
    latest = {}
    for dim, scores in dimensions.items():
        if scores:
            latest[dim] = scores[-1]

    # Compute trend direction (first → latest)
    trends = {}
    for dim, scores in dimensions.items():
        if len(scores) >= 2:
            diff = scores[-1]["score"] - scores[0]["score"]
            if diff > 5:
                trends[dim] = "up"
            elif diff < -5:
                trends[dim] = "down"
            else:
                trends[dim] = "stable"
        else:
            trends[dim] = "insufficient_data"

    return {
        "child_id": child_id,
        "child_name": child.name,
        "age_group": child.age_group.value if hasattr(child.age_group, 'value') else child.age_group,
        "class_name": child.class_name,
        "dimensions": {dim: scores for dim, scores in dimensions.items()},
        "chart_data": chart_data,
        "latest_scores": latest,
        "trends": trends,
        "assessment_count": len(assessments),
    }


async def get_class_overview(
    db: AsyncSession,
    class_name: str,
) -> Dict[str, Any]:
    """
    Get aggregated overview for all children in a class.

    Returns average scores per dimension, level distribution, top strengths, common needs.
    """
    # Get all children in class
    children_result = await db.execute(
        select(Child).where(Child.class_name == class_name)
    )
    children = children_result.scalars().all()
    child_ids = [c.id for c in children]

    if not child_ids:
        return {"class_name": class_name, "total_children": 0, "error": "班级无幼儿"}

    # Get latest assessment per dimension per child
    all_assessments = []
    for cid in child_ids:
        result = await db.execute(
            select(AbilityAssessment)
            .where(AbilityAssessment.child_id == cid)
            .order_by(desc(AbilityAssessment.assessed_at))
        )
        all_assessments.extend(result.scalars().all())

    # Group by dimension
    dim_scores: Dict[str, List[float]] = {}
    dim_levels: Dict[str, List[str]] = {}
    for a in all_assessments:
        dim = a.dimension
        if dim not in dim_scores:
            dim_scores[dim] = []
            dim_levels[dim] = []
        dim_scores[dim].append(a.score)
        dim_levels[dim].append(a.level.value if hasattr(a.level, 'value') else str(a.level))

    dimensions = []
    for dim, scores in dim_scores.items():
        if scores:
            avg = sum(scores) / len(scores)
            level_counts = {}
            for lv in dim_levels.get(dim, []):
                level_counts[lv] = level_counts.get(lv, 0) + 1
            dimensions.append({
                "dimension": dim,
                "average_score": round(avg, 1),
                "max_score": max(scores),
                "min_score": min(scores),
                "level_distribution": level_counts,
                "sample_count": len(scores),
            })

    # Top strengths (highest avg) and common needs (lowest avg)
    sorted_dims = sorted(dimensions, key=lambda d: d["average_score"], reverse=True)
    strengths = [d["dimension"] for d in sorted_dims[:2]] if sorted_dims else []
    needs = [d["dimension"] for d in sorted_dims[-2:]] if len(sorted_dims) >= 2 else []

    return {
        "class_name": class_name,
        "total_children": len(children),
        "assessed_children": len([cid for cid in child_ids if any(
            a.child_id == cid for a in all_assessments
        )]),
        "dimensions": dimensions,
        "top_strengths": strengths,
        "common_needs": needs,
        "generated_at": datetime.now().isoformat(),
    }


async def get_semester_comparison(
    db: AsyncSession,
    class_name: str,
) -> Dict[str, Any]:
    """
    Compare current vs previous semester for a class.
    Splits assessments at 6 months ago as the semester boundary.
    """
    six_months_ago = datetime.now() - timedelta(days=180)

    children_result = await db.execute(
        select(Child).where(Child.class_name == class_name)
    )
    children = children_result.scalars().all()
    child_ids = [c.id for c in children]

    all_assessments = []
    for cid in child_ids:
        result = await db.execute(
            select(AbilityAssessment)
            .where(AbilityAssessment.child_id == cid)
            .order_by(AbilityAssessment.assessed_at)
        )
        all_assessments.extend(result.scalars().all())

    # Split into current and previous
    current = [a for a in all_assessments if a.assessed_at and a.assessed_at > six_months_ago]
    previous = [a for a in all_assessments if a.assessed_at and a.assessed_at <= six_months_ago]

    def avg_by_dim(assessments):
        dims = {}
        for a in assessments:
            if a.dimension not in dims:
                dims[a.dimension] = []
            dims[a.dimension].append(a.score)
        return {d: round(sum(s) / len(s), 1) for d, s in dims.items() if s}

    current_avg = avg_by_dim(current)
    previous_avg = avg_by_dim(previous)

    comparison = []
    all_dims = set(list(current_avg.keys()) + list(previous_avg.keys()))
    for dim in all_dims:
        cur = current_avg.get(dim)
        prev = previous_avg.get(dim)
        delta = round(cur - prev, 1) if cur is not None and prev is not None else None
        comparison.append({
            "dimension": dim,
            "current_semester": cur,
            "previous_semester": prev,
            "delta": delta,
            "trend": "up" if delta and delta > 0 else "down" if delta and delta < 0 else "stable",
        })

    return {
        "class_name": class_name,
        "semester_boundary": six_months_ago.strftime("%Y-%m-%d"),
        "comparison": comparison,
        "current_assessment_count": len(current),
        "previous_assessment_count": len(previous),
    }
