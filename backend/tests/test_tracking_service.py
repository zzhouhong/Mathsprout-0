"""
Tests for the tracking service.
"""

import pytest
from app.services.tracking_service import (
    compute_growth_trajectory,
    compare_assessments,
    analyze_class,
)
from app.core.prompts.pck_reference import AgeGroup, Dimension, DevLevel


@pytest.fixture
def three_assessments():
    """Three synthetic assessments showing growth."""
    return [
        {
            "child_name": "小明",
            "age_group": AgeGroup.MIDDLE,
            "assessment": [
                {"dimension": "counting", "display_name": "数数", "score": 55, "level": "L2"},
                {"dimension": "addition_sub", "display_name": "加减", "score": 40, "level": "L1"},
                {"dimension": "shapes_space", "display_name": "图形", "score": 60, "level": "L2"},
                {"dimension": "patterns", "display_name": "模式", "score": 35, "level": "L1"},
            ],
            "assessed_at": "2025-09-15T10:00:00",
        },
        {
            "child_name": "小明",
            "age_group": AgeGroup.MIDDLE,
            "assessment": [
                {"dimension": "counting", "display_name": "数数", "score": 65, "level": "L2"},
                {"dimension": "addition_sub", "display_name": "加减", "score": 50, "level": "L2"},
                {"dimension": "shapes_space", "display_name": "图形", "score": 72, "level": "L3"},
                {"dimension": "patterns", "display_name": "模式", "score": 42, "level": "L2"},
            ],
            "assessed_at": "2025-11-15T10:00:00",
        },
        {
            "child_name": "小明",
            "age_group": AgeGroup.MIDDLE,
            "assessment": [
                {"dimension": "counting", "display_name": "数数", "score": 78, "level": "L3"},
                {"dimension": "addition_sub", "display_name": "加减", "score": 58, "level": "L2"},
                {"dimension": "shapes_space", "display_name": "图形", "score": 85, "level": "L3"},
                {"dimension": "patterns", "display_name": "模式", "score": 50, "level": "L2"},
            ],
            "assessed_at": "2026-01-15T10:00:00",
        },
    ]


# ─── Growth Trajectory Tests ───────────────────────────────────────

class TestGrowthTrajectory:
    @pytest.mark.asyncio
    async def test_computes_trajectory(self, three_assessments):
        result = await compute_growth_trajectory(
            three_assessments, "小明", AgeGroup.MIDDLE
        )
        assert result["has_data"] is True
        assert result["assessment_count"] == 3
        assert len(result["trajectories"]) == 4

    @pytest.mark.asyncio
    async def test_detects_accelerating_dimension(self, three_assessments):
        result = await compute_growth_trajectory(
            three_assessments, "小明", AgeGroup.MIDDLE
        )
        # Counting goes from 55 to 78 (+23) — should be accelerating
        counting = [t for t in result["trajectories"] if t["dimension"] == "counting"]
        assert len(counting) == 1
        assert counting[0]["trend"] == "accelerating"
        assert counting[0]["delta"] > 10

    @pytest.mark.asyncio
    async def test_trajectory_includes_chart_points(self, three_assessments):
        result = await compute_growth_trajectory(
            three_assessments, "小明", AgeGroup.MIDDLE
        )
        for traj in result["trajectories"]:
            if traj["has_data"]:
                assert len(traj["chart_points"]) == 3

    @pytest.mark.asyncio
    async def test_empty_assessments(self):
        result = await compute_growth_trajectory([], "小明", AgeGroup.MIDDLE)
        assert result["has_data"] is False
        assert "message" in result

    @pytest.mark.asyncio
    async def test_single_assessment(self, three_assessments):
        result = await compute_growth_trajectory(
            three_assessments[:1], "小明", AgeGroup.MIDDLE
        )
        assert result["has_data"] is True
        assert result["assessment_count"] == 1

    @pytest.mark.asyncio
    async def test_growth_summary_no_forbidden_words(self, three_assessments):
        result = await compute_growth_trajectory(
            three_assessments, "小明", AgeGroup.MIDDLE
        )
        summary = result["overall_growth_summary"]
        for word in ["落后", "排名", "成绩", "分数"]:
            assert word not in summary


# ─── Compare Assessments Tests ─────────────────────────────────────

class TestCompareAssessments:
    @pytest.mark.asyncio
    async def test_first_assessment(self):
        current = {"assessment": []}
        result = await compare_assessments(
            current, None, "小明"
        )
        assert result["is_first_assessment"] is True

    @pytest.mark.asyncio
    async def test_detects_improvement(self, three_assessments):
        result = await compare_assessments(
            current=three_assessments[2],
            previous=three_assessments[0],
            child_name="小明",
        )
        assert result["is_first_assessment"] is False
        assert len(result["comparisons"]) == 4

        # Counting improved from 55 to 78
        counting = [c for c in result["comparisons"] if c["dimension"] == "counting"]
        assert len(counting) == 1
        assert counting[0]["score_delta"] > 0
        assert counting[0]["delta_emoji"] in ["⬆️", "↗️"]


# ─── Class Analysis Tests ──────────────────────────────────────────

class TestClassAnalysis:
    @pytest.fixture
    def class_data(self):
        return [
            {
                "child_name": "小明",
                "age_group": AgeGroup.MIDDLE,
                "assessment": [
                    {"dimension": "counting", "display_name": "数数", "score": 78, "level": "L3", "error_patterns": ["镜像书写3"]},
                    {"dimension": "addition_sub", "display_name": "加减", "score": 55, "level": "L2", "error_patterns": ["实物依赖"]},
                    {"dimension": "shapes_space", "display_name": "图形", "score": 90, "level": "L3", "error_patterns": []},
                    {"dimension": "patterns", "display_name": "模式", "score": 45, "level": "L2", "error_patterns": ["模式理解表面化"]},
                ],
            },
            {
                "child_name": "小红",
                "age_group": AgeGroup.MIDDLE,
                "assessment": [
                    {"dimension": "counting", "display_name": "数数", "score": 85, "level": "L3", "error_patterns": []},
                    {"dimension": "addition_sub", "display_name": "加减", "score": 48, "level": "L2", "error_patterns": ["实物依赖"]},
                    {"dimension": "shapes_space", "display_name": "图形", "score": 75, "level": "L3", "error_patterns": []},
                    {"dimension": "patterns", "display_name": "模式", "score": 60, "level": "L2", "error_patterns": ["分类标准漂移"]},
                ],
            },
            {
                "child_name": "小刚",
                "age_group": AgeGroup.MIDDLE,
                "assessment": [
                    {"dimension": "counting", "display_name": "数数", "score": 40, "level": "L1", "error_patterns": ["未掌握基数原则"]},
                    {"dimension": "addition_sub", "display_name": "加减", "score": 30, "level": "L1", "error_patterns": ["实物依赖", "加减混淆"]},
                    {"dimension": "shapes_space", "display_name": "图形", "score": 55, "level": "L2", "error_patterns": []},
                    {"dimension": "patterns", "display_name": "模式", "score": 35, "level": "L1", "error_patterns": ["模式理解表面化"]},
                ],
            },
        ]

    @pytest.mark.asyncio
    async def test_class_analysis_basic(self, class_data):
        result = await analyze_class(class_data, "中一班")
        assert result["has_data"] is True
        assert result["child_count"] == 3
        assert result["class_name"] == "中一班"

    @pytest.mark.asyncio
    async def test_class_dimension_stats(self, class_data):
        result = await analyze_class(class_data, "中一班")
        assert len(result["dimensions"]) == 4

        for dim in result["dimensions"]:
            assert "avg_score" in dim
            assert "min_score" in dim
            assert "max_score" in dim
            assert "distribution" in dim
            assert "focus" in dim

    @pytest.mark.asyncio
    async def test_finds_common_errors(self, class_data):
        result = await analyze_class(class_data, "中一班")
        # "实物依赖" appears in 2+ children
        errors = result["common_error_patterns"]
        shiwu = [e for e in errors if "实物依赖" in e["pattern"]]
        assert len(shiwu) >= 1

    @pytest.mark.asyncio
    async def test_generates_class_recommendations(self, class_data):
        result = await analyze_class(class_data, "中一班")
        assert len(result["class_recommendations"]) >= 1

    @pytest.mark.asyncio
    async def test_empty_class(self):
        result = await analyze_class([], "空班")
        assert result["has_data"] is False

    @pytest.mark.asyncio
    async def test_identifies_high_variance(self):
        """When score spread > 50, should flag high variance."""
        data = [
            {
                "child_name": "A",
                "assessment": [
                    {"dimension": "counting", "display_name": "数数", "score": 95, "level": "L4", "error_patterns": []},
                ],
            },
            {
                "child_name": "B",
                "assessment": [
                    {"dimension": "counting", "display_name": "数数", "score": 25, "level": "L1", "error_patterns": []},
                ],
            },
        ]
        result = await analyze_class(data)
        counting = [d for d in result["dimensions"] if d["dimension"] == "counting"]
        assert len(counting) == 1
        assert counting[0]["score_spread"] > 50
