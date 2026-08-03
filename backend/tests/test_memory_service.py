"""
Tests for memory_service.py — the backbone of the agent's long-term memory.

Covers:
  - aggregate_error_history (pure, sync)
  - recommend_difficulty (pure, sync)
  - build_memory_card (pure, sync)
  - build_comparison_for_dimension (pure, sync)
  - build_child_memory (async, needs DB)

Run:
    cd backend
    python -m pytest tests/test_memory_service.py -v
"""

import pytest
from types import SimpleNamespace
from datetime import datetime, timedelta

from app.services.memory_service import (
    aggregate_error_history,
    build_child_memory,
    recommend_difficulty,
    build_memory_card,
    build_comparison_for_dimension,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_assessment(
    dimension: str = "counting",
    score: float = 60.0,
    level: str = "L2",
    error_patterns: list = None,
    assessed_at=None,
    _use_default_time=True,
):
    """Build a SimpleNamespace that quacks like AbilityAssessment."""
    if assessed_at is None and _use_default_time:
        assessed_at = datetime.now()
    return SimpleNamespace(
        id=1,
        child_id=1,
        dimension=dimension,
        score=score,
        level=SimpleNamespace(value=level),
        error_patterns=error_patterns or [],
        assessed_at=assessed_at,
    )


def _make_memory(
    has_memory=True,
    age_group="middle",
    last_accuracy=None,
    baseline_level=2,
    dimensions=None,
    weak_dimensions=None,
    session_count=1,
    days_since_last=1,
    error_history=None,
):
    """Build a memory dict with sensible defaults."""
    return {
        "child_id": 1,
        "child_name": "小明",
        "age_group": age_group,
        "has_memory": has_memory,
        "assessment_count": 4,
        "session_count": session_count,
        "last_assessed_at": "2026-06-30T10:00:00",
        "days_since_last": days_since_last,
        "last_accuracy": last_accuracy,
        "baseline_level": baseline_level,
        "dimensions": dimensions or {},
        "weak_dimensions": weak_dimensions or [],
        "improving": [],
        "error_history": error_history or [],
    }


def _current_assessment(dims=None):
    """Build a minimal current assessment dict (output of assess())."""
    if dims is None:
        dims = [
            {
                "dimension": "counting",
                "display_name": "数运算能力",
                "score": 75.0,
                "level": "L3",
                "level_name": "熟练期",
                "error_patterns": [],
                "score_details": {"correct": 3, "total": 4},
            },
            {
                "dimension": "addition_subtraction",
                "display_name": "加减运算",
                "score": 50.0,
                "level": "L2",
                "level_name": "发展期",
                "error_patterns": ["进位错误"],
                "score_details": {"correct": 1, "total": 2},
            },
        ]
    return {"assessment": dims}


# ===========================================================================
# aggregate_error_history
# ===========================================================================

class TestAggregateErrorHistory:

    def test_empty_returns_empty(self):
        assert aggregate_error_history([]) == []

    def test_single_assessment_single_error_is_new(self):
        a = _mock_assessment(error_patterns=["镜像书写"], assessed_at=datetime(2026, 6, 30))
        result = aggregate_error_history([a])
        assert len(result) == 1
        assert result[0]["error"] == "镜像书写"
        assert result[0]["status"] == "new"
        assert result[0]["count"] == 1

    def test_single_assessment_multiple_errors(self):
        a = _mock_assessment(error_patterns=["镜像书写", "进位错误"], assessed_at=datetime(2026, 6, 30))
        result = aggregate_error_history([a])
        assert len(result) == 2
        assert all(r["status"] == "new" for r in result)

    def test_same_error_two_assessments_is_recurring(self):
        a1 = _mock_assessment(error_patterns=["镜像书写"], assessed_at=datetime(2026, 6, 28))
        a2 = _mock_assessment(error_patterns=["镜像书写"], assessed_at=datetime(2026, 6, 30))
        result = aggregate_error_history([a1, a2])
        assert len(result) == 1
        assert result[0]["error"] == "镜像书写"
        assert result[0]["status"] == "recurring"
        assert result[0]["count"] == 2

    def test_error_gone_in_latest_is_resolved(self):
        a1 = _mock_assessment(error_patterns=["镜像书写"], assessed_at=datetime(2026, 6, 28))
        a2 = _mock_assessment(error_patterns=[], assessed_at=datetime(2026, 6, 30))
        result = aggregate_error_history([a1, a2])
        assert len(result) == 1
        assert result[0]["error"] == "镜像书写"
        assert result[0]["status"] == "resolved"

    def test_mixed_errors_correct_statuses(self):
        a1 = _mock_assessment(error_patterns=["镜像书写", "进位错误"], assessed_at=datetime(2026, 6, 28))
        a2 = _mock_assessment(error_patterns=["镜像书写", "加法混淆"], assessed_at=datetime(2026, 6, 30))
        result = aggregate_error_history([a1, a2])
        by_error = {r["error"]: r for r in result}
        assert by_error["镜像书写"]["status"] == "recurring"
        assert by_error["进位错误"]["status"] == "resolved"
        assert by_error["加法混淆"]["status"] == "new"

    def test_sorted_by_count_desc(self):
        a1 = _mock_assessment(
            error_patterns=["常见错误", "常见错误"],  # same error listed twice in one assessment
            assessed_at=datetime(2026, 6, 28),
        )
        a2 = _mock_assessment(
            error_patterns=["常见错误", "罕见错误"],
            assessed_at=datetime(2026, 6, 30),
        )
        result = aggregate_error_history([a1, a2])
        # "常见错误" count=3 (appears 3 times across 2 assessments), "罕见错误" count=1
        assert result[0]["count"] >= result[-1]["count"]

    def test_empty_error_strings_skipped(self):
        a = _mock_assessment(error_patterns=["", None, "镜像书写"], assessed_at=datetime(2026, 6, 30))
        result = aggregate_error_history([a])
        assert len(result) == 1
        assert result[0]["error"] == "镜像书写"

    def test_none_error_patterns_handled(self):
        a = _mock_assessment(error_patterns=None, assessed_at=datetime(2026, 6, 30))
        result = aggregate_error_history([a])
        assert result == []

    def test_none_assessed_at_uses_unknown(self):
        a = _mock_assessment(error_patterns=["镜像书写"], assessed_at=None, _use_default_time=False)
        result = aggregate_error_history([a])
        assert len(result) == 1
        # When latest_dt is None, latest_date_str is None, so "unknown" != None
        # → in_latest is False → status is "resolved"
        assert result[0]["first_seen"] == "unknown"
        assert result[0]["status"] == "resolved"


# ===========================================================================
# recommend_difficulty
# ===========================================================================

class TestRecommendDifficulty:

    def test_no_memory_returns_baseline(self):
        mem = _make_memory(has_memory=False, baseline_level=2)
        result = recommend_difficulty(mem)
        assert result["level"] == 2
        assert "首次" in result["reason"]

    def test_none_accuracy_returns_baseline(self):
        mem = _make_memory(last_accuracy=None, baseline_level=3)
        result = recommend_difficulty(mem)
        assert result["level"] == 3

    def test_high_accuracy_no_errors_promotes(self):
        mem = _make_memory(
            last_accuracy=0.80,
            baseline_level=2,
            dimensions={"counting": {"error_patterns": []}},
        )
        result = recommend_difficulty(mem)
        assert result["level"] == 3
        assert "升档" in result["reason"]

    def test_low_accuracy_demotes(self):
        mem = _make_memory(
            last_accuracy=0.30,
            baseline_level=3,
            dimensions={"counting": {"error_patterns": ["进位错误"]}},
        )
        result = recommend_difficulty(mem)
        assert result["level"] == 2
        assert "降档" in result["reason"]

    def test_mid_accuracy_maintains(self):
        mem = _make_memory(
            last_accuracy=0.55,
            baseline_level=2,
            dimensions={"counting": {"error_patterns": ["进位错误"]}},
        )
        result = recommend_difficulty(mem)
        assert result["level"] == 2
        assert "维持" in result["reason"]

    def test_high_accuracy_with_errors_maintains(self):
        """75% accuracy but has errors → should NOT promote."""
        mem = _make_memory(
            last_accuracy=0.75,
            baseline_level=2,
            dimensions={"counting": {"error_patterns": ["进位错误"]}},
        )
        result = recommend_difficulty(mem)
        assert result["level"] == 2

    def test_promote_capped_at_5(self):
        mem = _make_memory(
            last_accuracy=0.90,
            baseline_level=5,  # already at max
            dimensions={"counting": {"error_patterns": []}},
        )
        result = recommend_difficulty(mem)
        assert result["level"] == 5

    def test_demote_floored_at_1(self):
        mem = _make_memory(
            last_accuracy=0.10,
            baseline_level=1,  # already at min
            dimensions={"counting": {"error_patterns": []}},
        )
        result = recommend_difficulty(mem)
        assert result["level"] == 1

    def test_small_age_group_baseline(self):
        mem = _make_memory(age_group="small", has_memory=False, baseline_level=1)
        result = recommend_difficulty(mem)
        assert result["level"] == 1

    def test_large_age_group_baseline(self):
        mem = _make_memory(age_group="large", has_memory=False, baseline_level=3)
        result = recommend_difficulty(mem)
        assert result["level"] == 3


# ===========================================================================
# build_memory_card
# ===========================================================================

class TestBuildMemoryCard:

    def test_none_memory_returns_none(self):
        assert build_memory_card(None, _current_assessment()) is None

    def test_no_memory_flag_returns_none(self):
        mem = _make_memory(has_memory=False)
        assert build_memory_card(mem, _current_assessment()) is None

    def test_improving_dimension_detected(self):
        mem = _make_memory(
            dimensions={
                "counting": {
                    "dimension": "counting",
                    "display_name": "数运算能力",
                    "latest_score": 50.0,
                    "error_patterns": ["镜像书写"],
                },
            },
            weak_dimensions=[
                {"dimension": "counting", "display_name": "数运算能力", "latest_score": 50.0},
            ],
        )
        current = _current_assessment([
            {
                "dimension": "counting",
                "display_name": "数运算能力",
                "score": 80.0,
                "level": "L3",
                "level_name": "熟练期",
                "error_patterns": [],
                "score_details": {"correct": 4, "total": 5},
            },
        ])
        card = build_memory_card(mem, current)
        assert card is not None
        assert card["remembered"] is True
        assert len(card["improving"]) == 1
        assert card["improving"][0]["dimension"] == "counting"
        assert card["improving"][0]["delta"] == 30.0

    def test_still_struggling_detected(self):
        mem = _make_memory(
            dimensions={
                "counting": {
                    "dimension": "counting",
                    "display_name": "数运算能力",
                    "latest_score": 60.0,
                    "error_patterns": ["进位错误"],
                },
            },
        )
        current = _current_assessment([
            {
                "dimension": "counting",
                "display_name": "数运算能力",
                "score": 55.0,
                "level": "L2",
                "level_name": "发展期",
                "error_patterns": ["进位错误"],
                "score_details": {"correct": 2, "total": 4},
            },
        ])
        card = build_memory_card(mem, current)
        assert len(card["still_struggling"]) == 1
        assert "进位错误" in card["still_struggling"][0]["persisted_errors"]

    def test_weak_now_empty_when_all_high(self):
        mem = _make_memory(
            dimensions={"counting": {"dimension": "counting", "latest_score": 80.0, "error_patterns": []}},
        )
        current = _current_assessment([
            {
                "dimension": "counting",
                "display_name": "数运算能力",
                "score": 85.0,
                "level": "L3",
                "level_name": "熟练期",
                "error_patterns": [],
                "score_details": {"correct": 4, "total": 5},
            },
        ])
        card = build_memory_card(mem, current)
        assert card["weak_now"] == []

    def test_summary_includes_session_count(self):
        mem = _make_memory(session_count=3, days_since_last=5)
        current = _current_assessment([])
        card = build_memory_card(mem, current)
        assert "第 3 次" in card["summary"]
        assert "5 天前" in card["last_seen"]

    def test_days_none_shows_last_time(self):
        mem = _make_memory(days_since_last=None)
        current = _current_assessment([])
        card = build_memory_card(mem, current)
        assert card["last_seen"] == "上次"

    def test_resolved_errors_appear_in_improving(self):
        """Delta < 5 but errors resolved → still counts as improving."""
        mem = _make_memory(
            dimensions={
                "counting": {
                    "dimension": "counting",
                    "display_name": "数运算能力",
                    "latest_score": 70.0,
                    "error_patterns": ["镜像书写"],
                },
            },
        )
        current = _current_assessment([
            {
                "dimension": "counting",
                "display_name": "数运算能力",
                "score": 72.0,  # delta=2, < 5
                "level": "L3",
                "level_name": "熟练期",
                "error_patterns": [],  # error resolved
                "score_details": {"correct": 4, "total": 5},
            },
        ])
        card = build_memory_card(mem, current)
        assert len(card["improving"]) == 1
        assert "镜像书写" in card["improving"][0]["resolved_errors"]


# ===========================================================================
# build_comparison_for_dimension
# ===========================================================================

class TestBuildComparisonForDimension:

    def test_none_memory_returns_none(self):
        assert build_comparison_for_dimension(None, "counting", {"score": 70}) is None

    def test_no_memory_flag_returns_none(self):
        mem = _make_memory(has_memory=False)
        assert build_comparison_for_dimension(mem, "counting", {"score": 70}) is None

    def test_no_prior_data_returns_none(self):
        mem = _make_memory(dimensions={})
        assert build_comparison_for_dimension(mem, "counting", {"score": 70}) is None

    def test_improvement_shows_arrow(self):
        mem = _make_memory(
            dimensions={
                "counting": {"latest_score": 60.0, "error_patterns": []},
            },
        )
        result = build_comparison_for_dimension(mem, "counting", {"score": 80.0, "error_patterns": []})
        assert "📈" in result
        assert "提升 20 分" in result

    def test_decline_shows_warning(self):
        mem = _make_memory(
            dimensions={
                "counting": {"latest_score": 80.0, "error_patterns": []},
            },
        )
        result = build_comparison_for_dimension(mem, "counting", {"score": 60.0, "error_patterns": []})
        assert "⚠️" in result
        assert "下降 20 分" in result

    def test_stable_shows_neutral(self):
        mem = _make_memory(
            dimensions={
                "counting": {"latest_score": 70.0, "error_patterns": []},
            },
        )
        result = build_comparison_for_dimension(mem, "counting", {"score": 72.0, "error_patterns": []})
        assert "基本持平" in result

    def test_resolved_errors_shown(self):
        mem = _make_memory(
            dimensions={
                "counting": {"latest_score": 60.0, "error_patterns": ["镜像书写", "进位错误"]},
            },
        )
        result = build_comparison_for_dimension(
            mem, "counting",
            {"score": 80.0, "error_patterns": ["进位错误"]},
        )
        assert "已克服" in result
        assert "镜像书写" in result

    def test_persisted_errors_shown(self):
        mem = _make_memory(
            dimensions={
                "counting": {"latest_score": 60.0, "error_patterns": ["镜像书写"]},
            },
        )
        result = build_comparison_for_dimension(
            mem, "counting",
            {"score": 80.0, "error_patterns": ["镜像书写"]},
        )
        assert "仍出现" in result
        assert "重点干预" in result

    def test_error_pattern_change_no_resolution(self):
        """Prior has errors, current has different errors, score stable.
        Both resolved and persisted are shown."""
        mem = _make_memory(
            dimensions={
                "counting": {"latest_score": 70.0, "error_patterns": ["镜像书写"]},
            },
        )
        result = build_comparison_for_dimension(
            mem, "counting",
            {"score": 72.0, "error_patterns": ["加法混淆"]},
        )
        # delta=2, so "基本持平"
        assert "基本持平" in result
        # prior has 镜像书写, current has 加法混淆 → resolved={镜像书写}
        assert "已克服" in result
        assert "镜像书写" in result


# ===========================================================================
# build_child_memory (async, needs DB)
# ===========================================================================

class TestBuildChildMemory:

    @pytest.mark.asyncio
    async def test_nonexistent_child_returns_none(self, db_session):
        result = await build_child_memory(db_session, 999)
        assert result is None

    @pytest.mark.asyncio
    async def test_child_no_assessments_returns_cold_start(self, db_session):
        from app.models import Child
        from app.models.enums import AgeGroupEnum

        child = Child(name="小红", age_group=AgeGroupEnum.MIDDLE, parent_access_code="ABC123")
        db_session.add(child)
        await db_session.commit()

        result = await build_child_memory(db_session, child.id)
        assert result is not None
        assert result["has_memory"] is False
        assert result["assessment_count"] == 0
        assert result["child_name"] == "小红"
        assert result["age_group"] == "middle"

    @pytest.mark.asyncio
    async def test_child_with_assessments_returns_full_memory(self, db_session):
        from app.models import Child, AbilityAssessment
        from app.models.enums import AgeGroupEnum, LevelEnum

        child = Child(name="小刚", age_group=AgeGroupEnum.LARGE, parent_access_code="DEF456")
        db_session.add(child)
        await db_session.commit()

        now = datetime.now()
        # Session 1: 4 dimensions
        for dim, score, level in [
            ("counting", 60.0, LevelEnum.L2),
            ("addition_subtraction", 50.0, LevelEnum.L2),
            ("shapes_space", 70.0, LevelEnum.L3),
            ("patterns", 40.0, LevelEnum.L1),
        ]:
            db_session.add(AbilityAssessment(
                child_id=child.id, dimension=dim, score=score, level=level,
                error_patterns=["测试错误"] if score < 60 else [],
                assessed_at=now - timedelta(days=7),
            ))
        # Session 2: 4 dimensions (some improved)
        for dim, score, level in [
            ("counting", 75.0, LevelEnum.L3),
            ("addition_subtraction", 65.0, LevelEnum.L2),
            ("shapes_space", 80.0, LevelEnum.L3),
            ("patterns", 55.0, LevelEnum.L2),
        ]:
            db_session.add(AbilityAssessment(
                child_id=child.id, dimension=dim, score=score, level=level,
                error_patterns=[] if score >= 70 else ["测试错误"],
                assessed_at=now,
            ))
        await db_session.commit()

        result = await build_child_memory(db_session, child.id)
        assert result is not None
        assert result["has_memory"] is True
        assert result["assessment_count"] == 8
        assert result["session_count"] == 2
        assert result["age_group"] == "large"
        assert result["child_name"] == "小刚"

        # last_accuracy = mean(75, 65, 80, 55) / 100 = 0.6875
        assert abs(result["last_accuracy"] - 0.6875) < 0.01

        # weak_dimensions: patterns(55) and addition_subtraction(65)
        weak_names = {d["dimension"] for d in result["weak_dimensions"]}
        assert "patterns" in weak_names

        # improving: all 4 dimensions improved (delta > 5 for each)
        improving_dims = {i["dimension"] for i in result["improving"]}
        assert "counting" in improving_dims  # 60→75

        # error_history: "测试错误" appears in session 1 (all dims) and session 2 (some)
        assert len(result["error_history"]) >= 1
        err = result["error_history"][0]
        assert err["error"] == "测试错误"
        # In session 2, some dims still have it → recurring
        assert err["status"] in ("recurring", "resolved")
