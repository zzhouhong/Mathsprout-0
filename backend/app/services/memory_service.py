"""
Child memory service — aggregates a child's assessment history into a
"memory" object that downstream generators (worksheet / report) can consume
to personalize output.

This is the backbone of the agent's long-term memory for the
「第二次见同一个孩子」demo narrative:
  - /generate uses last_accuracy to auto-pick difficulty (B5)
  - report_generator uses weak_dimensions / improving / error_history to
    render the "🧠 我记得这个孩子" card and "↻ 对比上次" lines (B6/B8)
  - dashboard_service uses error_history for the evolution timeline (B7)

No schema migration: everything is derived on the fly from AbilityAssessment
rows (which already store score / level / error_patterns / assessed_at).
"""

from typing import Optional, Dict, List, Any
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Child, AbilityAssessment
from app.core.prompts.pck_reference import get_dimension_display_name
from app.services.interactive_content.progressions import get_age_anchor_level


def aggregate_error_history(assessments: List[AbilityAssessment]) -> List[Dict[str, Any]]:
    """
    Aggregate error-pattern strings across a child's assessments into a
    time series with status labels (resolved / recurring / new).

    Shared by build_child_memory (memory card) and dashboard_service
    (growth trajectory error-evolution timeline, B7).
    """
    if not assessments:
        return []
    latest_dt = max((a.assessed_at for a in assessments if a.assessed_at), default=None)
    latest_date_str = latest_dt.strftime("%Y-%m-%d") if latest_dt else None

    error_map: Dict[str, Dict[str, Any]] = {}
    for a in assessments:
        date_str = a.assessed_at.strftime("%Y-%m-%d") if a.assessed_at else "unknown"
        for e in (a.error_patterns or []):
            if not e:
                continue
            key = str(e)
            if key not in error_map:
                error_map[key] = {
                    "error": key,
                    "first_seen": date_str,
                    "last_seen": date_str,
                    "count": 0,
                    "dates": [],
                }
            rec = error_map[key]
            rec["count"] += 1
            if date_str not in rec["dates"]:
                rec["dates"].append(date_str)
            if date_str < rec["first_seen"]:
                rec["first_seen"] = date_str
            if date_str > rec["last_seen"]:
                rec["last_seen"] = date_str

    history: List[Dict[str, Any]] = []
    for rec in error_map.values():
        in_latest = rec["last_seen"] == latest_date_str
        if in_latest and rec["count"] >= 2:
            status = "recurring"
        elif in_latest:
            status = "new"
        else:
            status = "resolved"
        history.append({
            "error": rec["error"],
            "first_seen": rec["first_seen"],
            "last_seen": rec["last_seen"],
            "count": rec["count"],
            "dates": sorted(rec["dates"]),
            "status": status,
        })
    history.sort(key=lambda x: (-x["count"], x["error"]))
    return history


async def build_child_memory(db: AsyncSession, child_id: int) -> Optional[Dict[str, Any]]:
    """
    Build an in-memory child profile from assessment history.

    Returns None if the child doesn't exist. Returns a "cold-start" memory
    (has_memory=False) if the child exists but has no assessments yet.
    """
    child = await db.get(Child, child_id)
    if not child:
        return None

    age_group = child.age_group.value if hasattr(child.age_group, "value") else str(child.age_group)

    result = await db.execute(
        select(AbilityAssessment)
        .where(AbilityAssessment.child_id == child_id)
        .order_by(AbilityAssessment.assessed_at)
    )
    assessments = result.scalars().all()

    cold_start = {
        "child_id": child_id,
        "child_name": child.name,
        "age_group": age_group,
        "has_memory": False,
        "assessment_count": 0,
        "session_count": 0,
        "last_assessed_at": None,
        "days_since_last": None,
        "last_accuracy": None,
        "baseline_level": get_age_anchor_level(age_group),
        "dimensions": {},
        "weak_dimensions": [],
        "improving": [],
        "error_history": [],
    }
    if not assessments:
        return cold_start

    # Group by dimension → chronological list of assessments
    by_dim: Dict[str, List[AbilityAssessment]] = {}
    for a in assessments:
        by_dim.setdefault(a.dimension, []).append(a)

    latest_dt = max(a.assessed_at for a in assessments if a.assessed_at)

    # Per-dimension latest snapshot + full history
    dim_latest: Dict[str, Dict[str, Any]] = {}
    for dim, lst in by_dim.items():
        last = lst[-1]
        dim_latest[dim] = {
            "dimension": dim,
            "display_name": get_dimension_display_name(dim),
            "latest_score": last.score,
            "level": last.level.value if hasattr(last.level, "value") else str(last.level),
            "error_patterns": list(last.error_patterns or []),
            "assessed_at": last.assessed_at.isoformat() if last.assessed_at else None,
            "history": [
                {
                    "score": x.score,
                    "assessed_at": x.assessed_at.isoformat() if x.assessed_at else None,
                }
                for x in lst
            ],
        }

    # Weak dimensions: lowest latest_score (up to 2)
    weak = sorted(dim_latest.values(), key=lambda d: d["latest_score"])[:2]

    # Overall accuracy proxy: mean of latest per-dimension scores / 100
    last_accuracy = sum(d["latest_score"] for d in dim_latest.values()) / (100.0 * len(dim_latest))

    # Improving dimensions: ≥2 assessments, latest - first > 5
    improving: List[Dict[str, Any]] = []
    for dim, lst in by_dim.items():
        if len(lst) >= 2:
            delta = lst[-1].score - lst[0].score
            if delta > 5:
                improving.append({
                    "dimension": dim,
                    "display_name": get_dimension_display_name(dim),
                    "from_score": lst[0].score,
                    "to_score": lst[-1].score,
                    "delta": round(delta, 1),
                })

    # Error history: aggregate error strings across all assessments
    error_history = aggregate_error_history(assessments)

    days_since = (datetime.now() - latest_dt).days if latest_dt else None
    session_count = len({a.assessed_at.strftime("%Y-%m-%d") for a in assessments if a.assessed_at})

    return {
        "child_id": child_id,
        "child_name": child.name,
        "age_group": age_group,
        "has_memory": True,
        "assessment_count": len(assessments),
        "session_count": session_count,
        "last_assessed_at": latest_dt.isoformat() if latest_dt else None,
        "days_since_last": days_since,
        "last_accuracy": round(last_accuracy, 3),
        "baseline_level": get_age_anchor_level(age_group),
        "dimensions": dim_latest,
        "weak_dimensions": weak,
        "improving": improving,
        "error_history": error_history,
    }


def recommend_difficulty(memory: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recommend a worksheet difficulty level from the child's memory.

    Used by /generate (B5). Falls back to the age-anchored baseline on
    cold start. We do NOT require streak_max (which we don't persist) —
    accuracy + presence of errors drives the shift, so the demo's
    "auto-pick" works without ProblemResult streak lookup.
    """
    age_group = memory.get("age_group", "middle")
    base = memory.get("baseline_level") or get_age_anchor_level(age_group)

    if not memory.get("has_memory"):
        return {"level": base, "reason": "首次评估，按年龄段基准定档"}

    acc = memory.get("last_accuracy")
    has_errors = any(d.get("error_patterns") for d in memory.get("dimensions", {}).values())

    if acc is None:
        return {"level": base, "reason": "首次评估，按年龄段基准定档"}
    if acc >= 0.75 and not has_errors:
        lvl = min(5, base + 1)
        return {"level": lvl, "reason": f"上次正确率{acc:.0%}且无典型错误，升档至 Lv.{lvl}"}
    if acc < 0.40:
        lvl = max(1, base - 1)
        return {"level": lvl, "reason": f"上次正确率{acc:.0%}偏低，降档至 Lv.{lvl}巩固基础"}
    return {"level": base, "reason": f"上次正确率{acc:.0%}，维持 Lv.{base}"}


def build_memory_card(memory: Optional[Dict[str, Any]], current_assessment: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Build the "🧠 我记得这个孩子" card payload for the teacher report.

    Compares the memory (state BEFORE this assessment) against the current
    assessment's per-dimension results to produce human-readable contrast
    lines. Returns None when there's no prior memory (first assessment).
    """
    if not memory or not memory.get("has_memory"):
        return None

    days = memory.get("days_since_last")
    last_seen = f"{days} 天前" if days is not None else "上次"

    current_dims = {d["dimension"]: d for d in current_assessment.get("assessment", [])}
    prior_dims = memory.get("dimensions", {})

    weak_then = [
        {"dimension": d["dimension"], "display_name": d["display_name"], "score": d["latest_score"]}
        for d in memory.get("weak_dimensions", [])
    ]
    weak_now = [
        {"dimension": d["dimension"], "display_name": d.get("display_name", d["dimension"]),
         "score": d.get("score", 0), "level": d.get("level_name", "")}
        for d in current_dims.values()
        if d.get("score_details", {}).get("total", 0) > 0 and d.get("score", 100) < 70
    ]

    improving = []
    still_struggling = []
    for dim, prior in prior_dims.items():
        cur = current_dims.get(dim)
        if not cur or cur.get("score_details", {}).get("total", 0) == 0:
            continue
        prior_score = prior.get("latest_score")
        cur_score = cur.get("score")
        if prior_score is None or cur_score is None:
            continue
        delta = cur_score - prior_score
        prior_errs = set(prior.get("error_patterns", []))
        cur_errs = set(cur.get("error_patterns", []))
        resolved_errs = list(prior_errs - cur_errs)
        persisted_errs = list(prior_errs & cur_errs)
        entry = {
            "dimension": dim,
            "display_name": prior.get("display_name", dim),
            "prior_score": prior_score,
            "current_score": cur_score,
            "delta": round(delta, 1),
            "resolved_errors": resolved_errs,
            "persisted_errors": persisted_errs,
        }
        if delta > 5 or resolved_errs:
            improving.append(entry)
        if persisted_errs or delta < 0:
            still_struggling.append(entry)

    summary_parts = [f"这是第 {memory.get('session_count', memory.get('assessment_count', 0))} 次评估，距上次 {last_seen}。"]
    if weak_then:
        names = "、".join(w["display_name"] for w in weak_then)
        summary_parts.append(f"上次薄弱维度：{names}。")
    if improving:
        names = "、".join(i["display_name"] for i in improving)
        summary_parts.append(f"本次进步：{names}。")
    if still_struggling:
        names = "、".join(s["display_name"] for s in still_struggling)
        summary_parts.append(f"仍需关注：{names}。")

    return {
        "remembered": True,
        "last_seen": last_seen,
        "session_count": memory.get("session_count", memory.get("assessment_count", 0)),
        "summary": " ".join(summary_parts),
        "weak_then": weak_then,
        "weak_now": weak_now,
        "improving": improving,
        "still_struggling": still_struggling,
    }


def build_comparison_for_dimension(memory: Optional[Dict[str, Any]], dimension: str, current_dim: Dict[str, Any]) -> Optional[str]:
    """
    Build the "↻ 对比上次：…" line for a single dimension in teaching_suggestions (B8).
    Returns None if no prior data for this dimension.
    """
    if not memory or not memory.get("has_memory"):
        return None
    prior = memory.get("dimensions", {}).get(dimension)
    if not prior:
        return None
    prior_score = prior.get("latest_score")
    cur_score = current_dim.get("score")
    if prior_score is None or cur_score is None:
        return None

    parts = [f"上次 {prior_score:.0f}% → 本次 {cur_score:.0f}%"]
    delta = cur_score - prior_score
    if delta > 5:
        parts.append(f"提升 {delta:.0f} 分 📈")
    elif delta < -5:
        parts.append(f"下降 {abs(delta):.0f} 分 ⚠️")
    else:
        parts.append("基本持平")

    prior_errs = set(prior.get("error_patterns", []))
    cur_errs = set(current_dim.get("error_patterns", []))
    resolved = list(prior_errs - cur_errs)
    persisted = list(prior_errs & cur_errs)
    if resolved:
        parts.append(f"已克服：{'、'.join(resolved[:2])}")
    if persisted:
        parts.append(f"仍出现：{'、'.join(persisted[:2])}，建议重点干预")
    if not resolved and not persisted and prior_errs:
        parts.append("错误模式有变化")

    return "↻ 对比上次：" + "，".join(parts)
