"""
Longitudinal tracking and class analysis service.

Features:
- Multi-worksheet progress tracking per child
- Growth trajectory computation
- Current-vs-previous comparison
- Class-level distribution analysis
- Common weakness identification
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from app.core.prompts.pck_reference import (
    Dimension,
    DevLevel,
    AgeGroup,
    get_dimension_display_name,
    get_age_display_name,
)


# ─── Individual Longitudinal Tracking ───────────────────────────────

async def compute_growth_trajectory(
    assessments: List[Dict],
    child_name: str,
    age_group: str,
) -> Dict:
    """
    Compute growth trajectory from a list of historical assessments.

    Args:
        assessments: List of assessment results sorted by date (oldest first)
        child_name: Child's display name
        age_group: Current age group

    Returns:
        Growth trajectory with trends, deltas, and visualizations
    """
    if not assessments:
        return {
            "child_name": child_name,
            "has_data": False,
            "message": "暂无历史评估数据，完成首次分析后可查看成长轨迹。",
        }

    dimensions = [
        Dimension.COUNTING,
        Dimension.ADDITION_SUBTRACTION,
        Dimension.SHAPES_SPACE,
        Dimension.PATTERNS,
    ]

    trajectories = []
    for dim in dimensions:
        dim_name = get_dimension_display_name(dim)
        scores = []
        levels = []
        dates = []

        for a in assessments:
            for d in a.get("assessment", []):
                if d.get("dimension") == dim:
                    scores.append(d.get("score", 0))
                    levels.append(d.get("level", "L1"))
                    dates.append(a.get("assessed_at") or a.get("generated_at", ""))

        if not scores:
            trajectories.append({
                "dimension": dim,
                "display_name": dim_name,
                "has_data": False,
            })
            continue

        # Compute trend
        first_score = scores[0]
        latest_score = scores[-1]
        delta = latest_score - first_score

        if delta >= 10:
            trend = "accelerating"
            trend_emoji = "🚀"
            trend_text = "显著进步"
        elif delta >= 3:
            trend = "improving"
            trend_emoji = "📈"
            trend_text = "稳步提升"
        elif delta >= -3:
            trend = "stable"
            trend_emoji = "➡️"
            trend_text = "保持稳定"
        elif delta >= -10:
            trend = "fluctuating"
            trend_emoji = "🔄"
            trend_text = "略有波动"
        else:
            trend = "declining"
            trend_emoji = "⚠️"
            trend_text = "需要关注"

        # Level progression
        level_sequence = " → ".join(levels)

        # Chart data (for frontend)
        chart_points = [
            {"x": str(dates[i]) if dates[i] else f"第{i+1}次",
             "y": scores[i],
             "level": levels[i]}
            for i in range(len(scores))
        ]

        trajectories.append({
            "dimension": dim,
            "display_name": dim_name,
            "has_data": True,
            "first_score": first_score,
            "latest_score": latest_score,
            "delta": round(delta, 1),
            "trend": trend,
            "trend_emoji": trend_emoji,
            "trend_text": trend_text,
            "level_sequence": level_sequence,
            "chart_points": chart_points,
            "assessment_count": len(scores),
        })

    # Generate overall growth summary
    overall = _generate_growth_summary(trajectories, child_name, age_group)

    return {
        "child_name": child_name,
        "age_group": get_age_display_name(age_group),
        "has_data": True,
        "assessment_count": len(assessments),
        "date_range": {
            "first": dates[0].split("T")[0] if assessments and dates else "",
            "latest": dates[-1].split("T")[0] if assessments and dates else "",
        },
        "trajectories": trajectories,
        "overall_growth_summary": overall,
    }


def _generate_growth_summary(
    trajectories: List[Dict],
    child_name: str,
    age_group: str,
) -> str:
    """Generate an encouraging growth summary."""
    age_display = get_age_display_name(age_group)

    accelerating = [t for t in trajectories if t.get("trend") == "accelerating"]
    improving = [t for t in trajectories if t.get("trend") == "improving"]
    stable = [t for t in trajectories if t.get("trend") == "stable"]
    needs_attention = [t for t in trajectories if t.get("trend") in ("declining", "fluctuating")]

    parts = [f"这是{child_name}（{age_display}）的数学发展成长轨迹。"]

    if accelerating:
        areas = "、".join([t["display_name"] for t in accelerating])
        parts.append(f"{child_name}在{areas}方面取得了显著进步，核心经验正在快速建立。")

    if improving:
        areas = "、".join([t["display_name"] for t in improving])
        parts.append(f"在{areas}方面，{child_name}正在稳步提升，持续积累数学经验。")

    if needs_attention:
        areas = "、".join([t["display_name"] for t in needs_attention])
        parts.append(
            f"在{areas}方面，近期表现有所波动。"
            f"这在幼儿发展中是常见现象，建议增加游戏化互动，观察日常情境中的自然表现。"
        )

    if not accelerating and not improving and not needs_attention:
        parts.append("各维度均保持稳定发展，建议持续丰富数学游戏活动。")

    parts.append(
        "每个孩子都有自己独特的发展节奏。"
        "成长轨迹反映的是特定时刻的表现，请结合日常观察全面看待孩子的发展。"
    )

    return "".join(parts)


# ─── Current vs Previous Comparison ─────────────────────────────────

async def compare_assessments(
    current: Dict,
    previous: Optional[Dict],
    child_name: str,
) -> Dict:
    """
    Compare current assessment with the previous one.

    Returns per-dimension deltas and summarized changes.
    """
    if previous is None:
        return {
            "is_first_assessment": True,
            "message": "这是首次评估，完成更多次分析后可查看对比。",
        }

    dimensions = [
        Dimension.COUNTING,
        Dimension.ADDITION_SUBTRACTION,
        Dimension.SHAPES_SPACE,
        Dimension.PATTERNS,
    ]

    comparisons = []
    for dim in dimensions:
        current_dim = _find_dimension(current.get("assessment", []), dim)
        prev_dim = _find_dimension(previous.get("assessment", []), dim)

        if not current_dim or not prev_dim:
            continue

        score_delta = current_dim["score"] - prev_dim["score"]
        level_changed = current_dim["level"] != prev_dim["level"]
        level_up = (
            int(current_dim["level"][1]) > int(prev_dim["level"][1])
            if level_changed else False
        )

        comparisons.append({
            "dimension": dim,
            "display_name": get_dimension_display_name(dim),
            "previous_score": prev_dim["score"],
            "current_score": current_dim["score"],
            "score_delta": round(score_delta, 1),
            "previous_level": prev_dim["level"],
            "current_level": current_dim["level"],
            "level_changed": level_changed,
            "level_up": level_up,
            "delta_emoji": (
                "⬆️" if score_delta > 5 else
                "↗️" if score_delta > 0 else
                "➡️" if score_delta >= -5 else
                "↘️"
            ),
        })

    # Summarize
    improvements = [c for c in comparisons if c["score_delta"] > 5]
    declines = [c for c in comparisons if c["score_delta"] < -5]

    summary_parts = []
    if improvements:
        areas = "、".join([c["display_name"] for c in improvements])
        summary_parts.append(f"进步明显的方面：{areas}")
    if declines:
        areas = "、".join([c["display_name"] for c in declines])
        summary_parts.append(
            f"需要关注的变化：{areas}（这在发展中是正常的，建议观察日常情境中的自然表现）"
        )
    if not improvements and not declines:
        summary_parts.append("各维度较上次变化平稳，正在持续积累中。")

    return {
        "is_first_assessment": False,
        "comparisons": comparisons,
        "summary": " ".join(summary_parts),
        "previous_date": previous.get("assessed_at") or previous.get("generated_at", ""),
        "current_date": current.get("assessed_at") or current.get("generated_at", ""),
    }


def _find_dimension(assessment_list: List[Dict], dimension: str) -> Optional[Dict]:
    """Find a dimension in an assessment list."""
    for d in assessment_list:
        if d.get("dimension") == dimension:
            return d
    return None


# ─── Class-Level Analysis ───────────────────────────────────────────

async def analyze_class(
    children_assessments: List[Dict],
    class_name: str = "本班",
) -> Dict:
    """
    Aggregate analysis across all children in a class.

    Args:
        children_assessments: List of per-child assessment summaries:
            [{"child_name": "...", "age_group": "...", "assessment": [...]}, ...]

    Returns:
        Class distribution, common patterns, teaching recommendations
    """
    if not children_assessments:
        return {
            "class_name": class_name,
            "has_data": False,
            "message": "暂无班级数据",
        }

    dimensions = [
        Dimension.COUNTING,
        Dimension.ADDITION_SUBTRACTION,
        Dimension.SHAPES_SPACE,
        Dimension.PATTERNS,
    ]

    # Per-dimension aggregation
    class_dimensions = []
    for dim in dimensions:
        scores = []
        levels = defaultdict(int)
        for child in children_assessments:
            dim_data = _find_dimension(child.get("assessment", []), dim)
            if dim_data:
                scores.append(dim_data["score"])
                levels[dim_data["level"]] += 1

        if not scores:
            continue

        avg_score = sum(scores) / len(scores)
        min_score = min(scores)
        max_score = max(scores)

        # Distribution buckets
        distribution = {
            "L1_萌芽期": levels.get("L1", 0),
            "L2_发展期": levels.get("L2", 0),
            "L3_熟练期": levels.get("L3", 0),
            "L4_进阶期": levels.get("L4", 0),
        }

        # Determine if this is a class-wide strength or weakness
        l1_l2_count = levels.get("L1", 0) + levels.get("L2", 0)
        l3_l4_count = levels.get("L3", 0) + levels.get("L4", 0)
        total = l1_l2_count + l3_l4_count

        if total == 0:
            focus = "no_data"
        elif l1_l2_count > total * 0.6:
            focus = "needs_attention"  # > 60% in L1/L2
        elif l3_l4_count > total * 0.7:
            focus = "class_strength"   # > 70% in L3/L4
        else:
            focus = "mixed"

        class_dimensions.append({
            "dimension": dim,
            "display_name": get_dimension_display_name(dim),
            "avg_score": round(avg_score, 1),
            "min_score": round(min_score, 1),
            "max_score": round(max_score, 1),
            "score_spread": round(max_score - min_score, 1),
            "distribution": distribution,
            "focus": focus,
            "child_count": total,
        })

    # Identify common error patterns
    common_errors = _find_common_errors(children_assessments)

    # Build error heatmap data (dimension × error pattern matrix)
    error_heatmap = _build_error_heatmap(children_assessments)

    # Generate class-level recommendations
    recommendations = _generate_class_recommendations(class_dimensions)

    return {
        "class_name": class_name,
        "has_data": True,
        "child_count": len(children_assessments),
        "dimensions": class_dimensions,
        "common_error_patterns": common_errors,
        "error_heatmap": error_heatmap,
        "class_recommendations": recommendations,
    }


def _find_common_errors(children_assessments: List[Dict]) -> List[Dict]:
    """Find error patterns that appear across multiple children."""
    error_counts = defaultdict(lambda: {"count": 0, "children": [], "dimension": ""})

    for child in children_assessments:
        for dim in child.get("assessment", []):
            for err in dim.get("error_patterns", []):
                key = err[:50]  # Use first 50 chars as key
                error_counts[key]["count"] += 1
                error_counts[key]["children"].append(child.get("child_name", "?"))
                error_counts[key]["dimension"] = dim.get("display_name", "")

    # Filter to errors that appear in >= 2 children
    common = [
        {
            "pattern": key,
            "count": data["count"],
            "dimension": data["dimension"],
            "affected_children": data["children"][:5],  # Limit to 5 names
        }
        for key, data in error_counts.items()
        if data["count"] >= 2
    ]

    # Sort by frequency
    common.sort(key=lambda x: x["count"], reverse=True)
    return common[:10]  # Top 10


def _build_error_heatmap(children_assessments: List[Dict]) -> Dict:
    """
    Build an error-heatmap matrix: dimension × error pattern → child count.

    Returns a structure suitable for rendering a CSS-based heatmap on the frontend.
    """
    dimensions_order = [
        Dimension.COUNTING,
        Dimension.ADDITION_SUBTRACTION,
        Dimension.SHAPES_SPACE,
        Dimension.PATTERNS,
    ]

    dim_labels = [get_dimension_display_name(d) for d in dimensions_order]

    # Collect all unique error patterns per dimension
    from collections import defaultdict, Counter
    dim_errors: Dict[str, Counter] = {d: Counter() for d in dimensions_order}

    for child in children_assessments:
        for dim_data in child.get("assessment", []):
            dim = dim_data.get("dimension", "")
            if dim not in dim_errors:
                continue
            for err in dim_data.get("error_patterns", []):
                # Normalize: use first 40 chars as key, full text as label
                key = err.strip()[:60]
                dim_errors[dim][key] += 1

    # Build rows: one per dimension
    rows = []
    all_cells = []
    for dim in dimensions_order:
        errors_in_dim = dim_errors.get(dim, Counter())
        if not errors_in_dim:
            rows.append({
                "dimension": dim,
                "display_name": get_dimension_display_name(dim),
                "cells": [],
            })
            continue

        cells = []
        for pattern, count in errors_in_dim.most_common(8):  # Top 8 per dimension
            cells.append({
                "pattern": pattern,
                "count": count,
                "child_count": len(children_assessments),
            })
            all_cells.append(count)
        rows.append({
            "dimension": dim,
            "display_name": get_dimension_display_name(dim),
            "cells": cells,
        })

    max_count = max(all_cells) if all_cells else 1

    return {
        "dimensions": dim_labels,
        "rows": rows,
        "max_count": max_count,
        "total_children": len(children_assessments),
    }


def _generate_class_recommendations(class_dimensions: List[Dict]) -> List[str]:
    """Generate class-level teaching recommendations."""
    recs = []

    needs_attention = [d for d in class_dimensions if d.get("focus") == "needs_attention"]
    strengths = [d for d in class_dimensions if d.get("focus") == "class_strength"]

    if needs_attention:
        areas = "、".join([d["display_name"] for d in needs_attention])
        recs.append(
            f"🔴 重点关注领域：{areas}。"
            f"建议在区角活动中增加相关材料投放，设计更多游戏化集体活动。"
        )

    if strengths:
        areas = "、".join([d["display_name"] for d in strengths])
        recs.append(
            f"🟢 班级优势领域：{areas}。"
            f"建议在此基础上拓展更丰富的变式活动，鼓励幼儿同伴互助。"
        )

    # Check for high variance (large gap between min and max)
    high_variance = [d for d in class_dimensions if d.get("score_spread", 0) > 50]
    if high_variance:
        areas = "、".join([d["display_name"] for d in high_variance])
        recs.append(
            f"🟡 个体差异较大：{areas}。"
            f"建议采用分层活动设计，为不同发展水平的幼儿提供适宜的材料和挑战。"
        )

    if not recs:
        recs.append(
            "班级各维度发展较为均衡。建议持续通过游戏化活动丰富数学经验，"
            "关注个体差异，为每个幼儿提供适宜的发展支持。"
        )

    return recs
