"""
Tests for the report generator.
"""

import pytest
from app.services.report_generator import (
    generate_teacher_report,
    generate_parent_report,
    _build_pck_analysis,
)
from app.core.prompts.pck_reference import AgeGroup, Dimension, DevLevel


@pytest.fixture
def sample_assessment():
    """Sample assessment result for report generation tests."""
    return {
        "child_name": "小明",
        "age_group": AgeGroup.MIDDLE,
        "age_display": "中班（4-5岁）",
        "assessment": [
            {
                "dimension": "counting",
                "display_name": "数概念与运算",
                "score": 78.0,
                "level": "L3",
                "level_name": "熟练期",
                "level_emoji": "🌳",
                "pck_stage": "前运算阶段后期：趋于符号表征",
                "sub_skills": [
                    {"name": "点数准确性", "score": 85.0, "max_score": 100.0},
                ],
                "error_patterns": [],
                "age_benchmark_comparison": "符合中班发展期望",
                "age_milestones": "能手口一致点数10以内物体",
                "recommendations": "建议增加序数练习。推荐活动：'数筷子'游戏。",
                "score_details": {"correct": 8, "total": 10, "strategy_level": "semi_concrete"},
            },
            {
                "dimension": "addition_sub",
                "display_name": "数运算能力",
                "score": 45.0,
                "level": "L2",
                "level_name": "发展期",
                "level_emoji": "🌿",
                "pck_stage": "前运算阶段中期：半具象表征过渡",
                "sub_skills": [
                    {"name": "实物操作正确率", "score": 60.0, "max_score": 100.0},
                ],
                "error_patterns": ["实物依赖：不用实物就不会算"],
                "age_benchmark_comparison": "部分达到中班期望",
                "age_milestones": "借助实物进行10以内加减",
                "recommendations": "建议逐步引入半具象材料。推荐活动：'分水果'游戏。",
                "score_details": {"correct": 3, "total": 5, "strategy_level": "concrete_objects"},
            },
            {
                "dimension": "shapes_space",
                "display_name": "图形与空间",
                "score": 85.0,
                "level": "L3",
                "level_name": "熟练期",
                "level_emoji": "🌳",
                "pck_stage": "前运算阶段后期：趋于符号表征",
                "sub_skills": [
                    {"name": "平面图形识别", "score": 90.0, "max_score": 100.0},
                ],
                "error_patterns": [],
                "age_benchmark_comparison": "符合中班发展期望",
                "age_milestones": "能识别多种平面图形",
                "recommendations": "建议增加立体图形认识。推荐活动：'形状寻宝'游戏。",
                "score_details": {"correct": 8, "total": 9, "strategy_level": "symbolic"},
            },
            {
                "dimension": "patterns",
                "display_name": "集合与模式",
                "score": 50.0,
                "level": "L2",
                "level_name": "发展期",
                "level_emoji": "🌿",
                "pck_stage": "前运算阶段中期：半具象表征过渡",
                "sub_skills": [
                    {"name": "分类能力", "score": 55.0, "max_score": 100.0},
                ],
                "error_patterns": ["模式理解表面化"],
                "age_benchmark_comparison": "部分达到中班期望",
                "age_milestones": "能识别复制ABC模式",
                "recommendations": "建议多进行模式游戏。推荐活动：'穿珠子'游戏。",
                "score_details": {"correct": 3, "total": 6, "strategy_level": "AB_copy"},
            },
        ],
        "observations": {
            "attention_indicators": "careful",
            "overall_pck_notes": "测试用PCK观察",
        },
        "overall_summary": "测试用整体总结。",
    }


# ─── Teacher Report Tests ──────────────────────────────────────────

class TestTeacherReport:
    @pytest.mark.asyncio
    async def test_generates_report(self, sample_assessment):
        report = await generate_teacher_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        assert report["report_type"] == "teacher"
        assert report["child_name"] == "小明"

    @pytest.mark.asyncio
    async def test_includes_radar_chart_data(self, sample_assessment):
        report = await generate_teacher_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        assert "radar_chart_data" in report
        chart = report["radar_chart_data"]
        assert "labels" in chart
        assert len(chart["labels"]) == 4
        assert "datasets" in chart

    @pytest.mark.asyncio
    async def test_includes_pck_analysis(self, sample_assessment):
        report = await generate_teacher_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        assert "pck_analysis" in report
        assert len(report["pck_analysis"]) > 0

    @pytest.mark.asyncio
    async def test_includes_error_diagnosis(self, sample_assessment):
        report = await generate_teacher_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        assert "typical_errors_diagnosis" in report
        # Should have at least one error from the patterns dimension
        assert len(report["typical_errors_diagnosis"]) > 0

    @pytest.mark.asyncio
    async def test_teaching_suggestions_per_dimension(self, sample_assessment):
        report = await generate_teacher_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        suggestions = report["teaching_suggestions"]
        assert len(suggestions) == 4
        for dim_name in ["数概念与运算", "数运算能力", "图形与空间", "集合与模式"]:
            assert dim_name in suggestions
            assert "current_stage" in suggestions[dim_name]
            assert "recommendations" in suggestions[dim_name]

    @pytest.mark.asyncio
    async def test_reflection_questions(self, sample_assessment):
        report = await generate_teacher_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        questions = report["teaching_reflection_questions"]
        assert len(questions) >= 2

    @pytest.mark.asyncio
    async def test_no_forbidden_terminology_teacher(self, sample_assessment):
        report = await generate_teacher_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        # Teacher report CAN mention levels but should NOT say "落后" or "排名"
        assert "落后" not in str(report)
        assert "排名" not in str(report)


# ─── Parent Report Tests ───────────────────────────────────────────

class TestParentReport:
    @pytest.mark.asyncio
    async def test_generates_report(self, sample_assessment):
        report = await generate_parent_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        assert report["report_type"] == "parent"
        assert report["child_name"] == "小明"

    @pytest.mark.asyncio
    async def test_includes_strengths_and_growing_areas(self, sample_assessment):
        report = await generate_parent_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        # L3 dimensions should be in strengths
        assert len(report["strengths"]) >= 1
        # L2 dimensions should be in growing_areas
        assert len(report["growing_areas"]) >= 1

    @pytest.mark.asyncio
    async def test_strength_has_required_fields(self, sample_assessment):
        report = await generate_parent_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        for s in report["strengths"]:
            assert "area" in s
            assert "emoji" in s
            assert "description" in s
            assert "parent_observation_tip" in s

    @pytest.mark.asyncio
    async def test_growing_area_uses_learning_language(self, sample_assessment):
        report = await generate_parent_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        for g in report["growing_areas"]:
            # Should use "正在学习" framing, not "deficit" language
            assert "正在学习" in g.get("description", "") or "自然" in g.get("description", "")

    @pytest.mark.asyncio
    async def test_includes_family_activities(self, sample_assessment):
        report = await generate_parent_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        assert len(report["family_activities"]) >= 1
        for act in report["family_activities"]:
            assert "title" in act
            assert "materials" in act
            assert "steps" in act
            assert "why" in act

    @pytest.mark.asyncio
    async def test_absolutely_no_scores_in_parent_report(self, sample_assessment):
        report = await generate_parent_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        # Convert to JSON-safe string for searching
        import json
        text = json.dumps(report, ensure_ascii=False)
        # Parent report must NOT contain numerical scores
        forbidden = ["分数", "排名", "落后", "成绩", "得分"]
        for word in forbidden:
            assert word not in text, f"Parent report contains forbidden word: {word}"

    @pytest.mark.asyncio
    async def test_includes_parent_tips(self, sample_assessment):
        report = await generate_parent_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        assert "parent_tips" in report
        assert len(report["parent_tips"]) > 0

    @pytest.mark.asyncio
    async def test_includes_learning_quality_notes(self, sample_assessment):
        report = await generate_parent_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        assert "learning_quality_notes" in report
        assert "专注力" in report["learning_quality_notes"]

    @pytest.mark.asyncio
    async def test_overall_summary_is_encouraging(self, sample_assessment):
        report = await generate_parent_report(
            sample_assessment, "小明", AgeGroup.MIDDLE
        )
        summary = report["overall_summary"]
        assert "不是" in summary or "游戏" in summary or "自然" in summary
        # Should address parents warmly
        assert "家长" in summary or "宝宝" in summary or "孩子" in summary
