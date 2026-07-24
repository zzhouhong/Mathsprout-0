"""
Tests for the worksheet generator service.

Covers: default generation, per-age-group, per-dimension, child-memory note
surfacing, markdown/HTML rendering, and answer-key correctness.
"""

import pytest
from app.services.worksheet_generator import (
    WorksheetConfig,
    WorksheetProblem,
    GeneratedWorksheet,
    generate_worksheet,
    worksheet_to_markdown,
    worksheet_to_html,
    _build_memory_note,
)


# ─── generate_worksheet: defaults & structure ────────────────────────

class TestGenerateWorksheetDefaults:
    def test_default_config_produces_valid_worksheet(self):
        ws = generate_worksheet()
        assert isinstance(ws, GeneratedWorksheet)
        assert ws.problems  # at least one problem
        assert ws.child_name == "小朋友"
        assert ws.age_group == "middle"
        assert ws.date  # non-empty

    def test_none_config_uses_defaults(self):
        ws = generate_worksheet(None)
        assert ws.config.age_group == "middle"
        assert ws.config.dimensions == ["counting", "shapes_space"]

    def test_problems_have_required_fields(self):
        ws = generate_worksheet(WorksheetConfig(dimensions=["counting"]))
        for p in ws.problems:
            assert isinstance(p, WorksheetProblem)
            assert p.number >= 1
            assert p.type
            assert p.dimension
            assert p.prompt

    def test_answer_key_matches_problems(self):
        ws = generate_worksheet()
        for p in ws.problems:
            assert p.number in ws.answer_key
            assert ws.answer_key[p.number] == p.correct_answer

    def test_total_possible_equals_problem_count(self):
        ws = generate_worksheet()
        assert ws.total_possible == len(ws.problems)


# ─── Per-age-group generation ────────────────────────────────────────

class TestAgeGroups:
    @pytest.mark.parametrize("age_group", ["small", "middle", "large"])
    def test_each_age_group_generates(self, age_group):
        ws = generate_worksheet(WorksheetConfig(age_group=age_group, dimensions=["counting"]))
        assert ws.age_group == age_group
        assert ws.problems

    def test_learning_objective_populated_when_blank(self):
        ws = generate_worksheet(WorksheetConfig(learning_objective=""))
        assert ws.learning_objective  # auto-generated, non-empty

    def test_explicit_learning_objective_preserved(self):
        ws = generate_worksheet(WorksheetConfig(learning_objective="感知三角形的多种变式"))
        assert ws.learning_objective == "感知三角形的多种变式"


# ─── Per-dimension generation ────────────────────────────────────────

class TestDimensions:
    @pytest.mark.parametrize("dim", ["counting", "shapes_space", "patterns", "addition_sub"])
    def test_each_dimension_generates(self, dim):
        ws = generate_worksheet(WorksheetConfig(dimensions=[dim]))
        assert any(p.dimension == dim for p in ws.problems)

    def test_multiple_dimensions_distribute_problems(self):
        ws = generate_worksheet(
            WorksheetConfig(dimensions=["counting", "shapes_space"], problem_count=4)
        )
        dims = {p.dimension for p in ws.problems}
        assert "counting" in dims
        assert "shapes_space" in dims


# ─── Child memory note (B6 feature) ──────────────────────────────────

class TestChildMemoryNote:
    def test_no_memory_yields_empty_note(self):
        assert _build_memory_note(None, ["counting"]) == ""
        assert _build_memory_note({}, ["counting"]) == ""
        assert _build_memory_note({"has_memory": False}, ["counting"]) == ""

    def test_memory_without_weak_dims_yields_empty(self):
        note = _build_memory_note({"has_memory": True, "weak_dimensions": []}, ["counting"])
        assert note == ""

    def test_weak_dim_targeted_surfaces_in_note(self):
        memory = {
            "has_memory": True,
            "weak_dimensions": [
                {"dimension": "counting", "latest_score": 45.0},
            ],
        }
        note = _build_memory_note(memory, ["counting"])
        assert "📌" in note
        assert "counting" in note.lower() or "数" in note

    def test_memory_note_in_generated_worksheet(self):
        memory = {
            "has_memory": True,
            "weak_dimensions": [{"dimension": "counting", "latest_score": 40.0}],
        }
        ws = generate_worksheet(WorksheetConfig(dimensions=["counting"]), child_memory=memory)
        assert ws.memory_note  # non-empty
        assert "📌" in ws.memory_note


# ─── Rendering: markdown & HTML ──────────────────────────────────────

class TestRendering:
    def test_worksheet_to_markdown_returns_string(self):
        ws = generate_worksheet()
        md = worksheet_to_markdown(ws)
        assert isinstance(md, str)
        assert ws.child_name in md

    def test_worksheet_to_html_returns_string(self):
        ws = generate_worksheet()
        html = worksheet_to_html(ws)
        assert isinstance(html, str)
        assert "<" in html  # contains HTML tags

    def test_markdown_contains_child_name_and_problems(self):
        ws = generate_worksheet(WorksheetConfig(child_name="小明"))
        md = worksheet_to_markdown(ws)
        assert "小明" in md


# ─── Edge cases ──────────────────────────────────────────────────────

class TestEdgeCases:
    def test_custom_child_name_used(self):
        ws = generate_worksheet(WorksheetConfig(child_name="小红"))
        assert ws.child_name == "小红"
        assert "小红" in ws.title

    def test_difficulty_level_reflected(self):
        ws = generate_worksheet(WorksheetConfig(difficulty_level=5))
        assert ws.difficulty_level == 5
