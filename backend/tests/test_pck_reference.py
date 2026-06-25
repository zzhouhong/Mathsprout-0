"""
Tests for PCK reference data module.
"""

import pytest
from app.core.prompts.pck_reference import (
    MILESTONES,
    ERROR_PATTERNS,
    SUB_SKILLS,
    AgeGroup,
    Dimension,
    DevLevel,
    determine_level,
    get_level_description,
    get_dimension_display_name,
    get_age_display_name,
)


class TestAgeGroups:
    def test_all_age_groups_present(self):
        """All three age groups should have milestone data."""
        assert AgeGroup.SMALL in MILESTONES
        assert AgeGroup.MIDDLE in MILESTONES
        assert AgeGroup.LARGE in MILESTONES

    def test_small_class_has_4_dimensions(self):
        """Each age group should have data for all 4 dimensions."""
        assert len(MILESTONES[AgeGroup.SMALL]) == 4
        assert Dimension.COUNTING in MILESTONES[AgeGroup.SMALL]
        assert Dimension.ADDITION_SUBTRACTION in MILESTONES[AgeGroup.SMALL]
        assert Dimension.SHAPES_SPACE in MILESTONES[AgeGroup.SMALL]
        assert Dimension.PATTERNS in MILESTONES[AgeGroup.SMALL]

    def test_milestones_not_empty(self):
        """Each dimension should have at least 2 milestones."""
        for age_group in AgeGroup:
            for dim in Dimension:
                milestones = MILESTONES[age_group].get(dim, [])
                assert len(milestones) >= 2, f"{age_group}/{dim} has too few milestones"


class TestErrorPatterns:
    def test_all_patterns_have_required_fields(self):
        """Each error pattern should have id, name, description, is_developmental."""
        for ep in ERROR_PATTERNS:
            assert "id" in ep
            assert "name" in ep
            assert "description" in ep
            assert "is_developmental" in ep
            assert ep["is_developmental"] is True

    def test_all_pattern_ids_are_unique(self):
        """Error pattern ids must be unique."""
        ids = [ep["id"] for ep in ERROR_PATTERNS]
        assert len(ids) == len(set(ids)), f"Duplicate ids found: {ids}"

    def test_mirror_writing_is_developmental(self):
        """Mirror writing must be marked as developmental."""
        mirror = [ep for ep in ERROR_PATTERNS if ep["id"] == "mirror_writing"]
        assert len(mirror) == 1
        assert mirror[0]["is_developmental"] is True
        assert AgeGroup.SMALL in mirror[0]["age_groups"]


class TestSubSkills:
    def test_all_dimensions_have_sub_skills(self):
        """Each dimension should have sub-skills."""
        for dim in Dimension:
            assert dim in SUB_SKILLS

    def test_sub_skills_not_empty(self):
        """Each dimension should have at least 3 sub-skills."""
        for dim in Dimension:
            assert len(SUB_SKILLS[dim]) >= 3


class TestDetermineLevel:
    def test_l4_advanced(self):
        assert determine_level(95, AgeGroup.MIDDLE, Dimension.COUNTING) == DevLevel.L4_ADVANCED
        assert determine_level(91, AgeGroup.MIDDLE, Dimension.COUNTING) == DevLevel.L4_ADVANCED

    def test_l3_proficient(self):
        assert determine_level(71, AgeGroup.MIDDLE, Dimension.COUNTING) == DevLevel.L3_PROFICIENT
        assert determine_level(90, AgeGroup.MIDDLE, Dimension.COUNTING) == DevLevel.L3_PROFICIENT

    def test_l2_growing(self):
        assert determine_level(41, AgeGroup.MIDDLE, Dimension.COUNTING) == DevLevel.L2_GROWING
        assert determine_level(70, AgeGroup.MIDDLE, Dimension.COUNTING) == DevLevel.L2_GROWING

    def test_l1_sprout(self):
        assert determine_level(0, AgeGroup.MIDDLE, Dimension.COUNTING) == DevLevel.L1_SPROUT
        assert determine_level(40, AgeGroup.MIDDLE, Dimension.COUNTING) == DevLevel.L1_SPROUT

    def test_boundary_precision(self):
        """Test exact boundary values."""
        assert determine_level(70.5, AgeGroup.MIDDLE, Dimension.COUNTING) == DevLevel.L2_GROWING
        assert determine_level(71.0, AgeGroup.MIDDLE, Dimension.COUNTING) == DevLevel.L3_PROFICIENT


class TestGetLevelDescription:
    def test_all_levels_have_descriptions(self):
        for level in DevLevel:
            desc = get_level_description(level)
            assert "name" in desc
            assert "emoji" in desc
            assert "meaning" in desc
            assert "pck_stage" in desc

    def test_l1_sprout_emoji(self):
        desc = get_level_description(DevLevel.L1_SPROUT)
        assert desc["emoji"] == "🌱"

    def test_l4_advanced_emoji(self):
        desc = get_level_description(DevLevel.L4_ADVANCED)
        assert desc["emoji"] == "⭐"


class TestDisplayNames:
    def test_dimension_names(self):
        assert get_dimension_display_name(Dimension.COUNTING) == "数概念与运算"
        assert get_dimension_display_name(Dimension.ADDITION_SUBTRACTION) == "数运算能力"
        assert get_dimension_display_name(Dimension.SHAPES_SPACE) == "图形与空间"
        assert get_dimension_display_name(Dimension.PATTERNS) == "集合与模式"

    def test_age_display_names(self):
        assert "小班" in get_age_display_name(AgeGroup.SMALL)
        assert "中班" in get_age_display_name(AgeGroup.MIDDLE)
        assert "大班" in get_age_display_name(AgeGroup.LARGE)

    def test_unknown_dimension_returns_input(self):
        assert get_dimension_display_name("nonexistent") == "nonexistent"

    def test_unknown_age_returns_input(self):
        assert get_age_display_name("nonexistent") == "nonexistent"
