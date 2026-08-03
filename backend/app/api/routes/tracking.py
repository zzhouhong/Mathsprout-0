"""
Longitudinal tracking and class analysis API routes.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Optional, List

from app.schemas import AgeGroupEnum
from app.core.security import get_current_teacher
from app.services.tracking_service import (
    compute_growth_trajectory,
    compare_assessments,
    analyze_class,
)
from app.core.prompts.pck_reference import (
    get_age_display_name,
    get_dimension_display_name,
    Dimension,
    AgeGroup,
    DevLevel,
)

router = APIRouter()


# ─── Individual Growth Trajectory ───────────────────────────────────

@router.post("/trajectory/{child_name}")
async def get_growth_trajectory(
    child_name: str,
    assessments: List[dict],
    age_group: AgeGroupEnum = Query(default=AgeGroupEnum.MIDDLE),
):
    """
    Compute growth trajectory from historical assessments.

    Request body: list of assessment results (sorted oldest first)
    """
    result = await compute_growth_trajectory(
        assessments=assessments,
        child_name=child_name,
        age_group=age_group.value,
    )
    return JSONResponse(content=result)


@router.post("/compare/{child_name}")
async def compare_child_assessments(
    child_name: str,
    current: dict,
    previous: Optional[dict] = None,
):
    """
    Compare current vs previous assessment for a child.
    """
    result = await compare_assessments(
        current=current,
        previous=previous,
        child_name=child_name,
    )
    return JSONResponse(content=result)


# ─── Class Analysis ─────────────────────────────────────────────────

@router.post("/class-analysis")
async def get_class_analysis(
    children_data: List[dict],
    class_name: str = "本班",
    current_user: dict = Depends(get_current_teacher),
):
    """
    Generate class-level analysis from all children's assessment data.

    Requires teacher authentication.
    """
    result = await analyze_class(
        children_assessments=children_data,
        class_name=class_name,
    )
    return JSONResponse(content=result)


# ─── Demo Trajectory ────────────────────────────────────────────────

@router.get("/demo/trajectory")
async def get_demo_trajectory(
    age_group: AgeGroupEnum = Query(default=AgeGroupEnum.MIDDLE),
    child_name: str = Query(default="小明"),
):
    """
    Generate demo growth trajectory data for frontend development.
    """
    age = age_group.value
    age_display = get_age_display_name(age)

    # Build 3 simulated assessments over time
    demo_assessments = _build_demo_history(child_name, age)

    result = await compute_growth_trajectory(
        assessments=demo_assessments,
        child_name=child_name,
        age_group=age,
    )

    return JSONResponse(content=result)


def _build_demo_history(child_name: str, age: str) -> List[dict]:
    """Build simulated historical assessments."""
    import hashlib

    def _make_assessment(month_offset: int, score_offsets: dict) -> dict:
        """Create one assessment with dimension scores adjusted by offsets."""
        dims = []
        base_scores = {
            "counting": 55 + month_offset * 8 + score_offsets.get("counting", 0),
            "addition_sub": 35 + month_offset * 7 + score_offsets.get("addition_sub", 0),
            "shapes_space": 60 + month_offset * 10 + score_offsets.get("shapes_space", 0),
            "patterns": 30 + month_offset * 5 + score_offsets.get("patterns", 0),
        }

        for dim_key, dim_name, skills in [
            ("counting", "数概念与运算",
             ["点数准确性", "按数取物", "数量比较", "序数理解", "数的组成", "数量守恒"]),
            ("addition_sub", "数运算能力",
             ["实物操作正确率", "符号运算正确率", "策略水平", "应用题理解", "运算思维灵活性"]),
            ("shapes_space", "图形与空间",
             ["平面图形识别", "立体图形识别", "图形特征描述", "空间方位", "图形组合与分解"]),
            ("patterns", "集合与模式",
             ["分类能力", "模式识别", "模式扩展", "模式创造", "排序能力", "规律语言描述"]),
        ]:
            score = min(100, max(0, base_scores[dim_key]))
            if score >= 91:
                level = "L4"
            elif score >= 71:
                level = "L3"
            elif score >= 41:
                level = "L2"
            else:
                level = "L1"

            sub_skills = []
            for sk_name in skills:
                seed = int(hashlib.md5(sk_name.encode()).hexdigest()[:4], 16)
                variance = (seed % 15) - 7
                sk_score = min(100, max(0, score + variance))
                sub_skills.append({
                    "name": sk_name,
                    "score": round(sk_score, 1),
                    "max_score": 100.0,
                })

            dims.append({
                "dimension": dim_key,
                "display_name": dim_name,
                "score": round(score, 1),
                "level": level,
                "level_name": {"L1": "萌芽期", "L2": "发展期", "L3": "熟练期", "L4": "进阶期"}[level],
                "level_emoji": {"L1": "🌱", "L2": "🌿", "L3": "🌳", "L4": "⭐"}[level],
                "sub_skills": sub_skills,
                "error_patterns": [],
                "age_benchmark_comparison": "",
                "recommendations": "",
                "score_details": {"correct": int(score / 10), "total": 10, "strategy_level": None},
            })

        return {
            "child_name": child_name,
            "age_group": age,
            "age_display": get_age_display_name(age),
            "assessment": dims,
            "observations": {},
            "overall_summary": "",
            "assessed_at": f"2025-{9 + month_offset:02d}-15T10:00:00",
        }

    return [
        _make_assessment(0, {}),
        _make_assessment(2, {"counting": 3, "shapes_space": 5}),
        _make_assessment(4, {"counting": 8, "addition_sub": 5, "shapes_space": 10, "patterns": 3}),
    ]
