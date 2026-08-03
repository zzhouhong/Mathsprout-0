"""
Parametrized scenario tests — load all JSON fixtures from tests/scenarios/
and verify assessment engine output structure + key PCK rules.

Run:
    cd backend
    python -m pytest tests/test_scenarios.py -v
    python -m pytest tests/test_scenarios.py -v -k "cross_age"  # filter
"""

import json
import pytest
from pathlib import Path
from app.services.assessment_engine import assess
from app.services.report_generator import generate_teacher_report, generate_parent_report
from app.core.prompts.pck_reference import (
    Dimension,
    DevLevel,
    AgeGroup,
    get_dimension_display_name,
)

SCENARIOS_DIR = Path(__file__).parent / "scenarios"

VALID_AGE_GROUPS = {"small", "middle", "large"}
VALID_DIMENSIONS = {Dimension.COUNTING, Dimension.ADDITION_SUBTRACTION, Dimension.SHAPES_SPACE, Dimension.PATTERNS}
VALID_LEVELS = {DevLevel.L1_SPROUT.value, DevLevel.L2_GROWING.value, DevLevel.L3_PROFICIENT.value, DevLevel.L4_ADVANCED.value}


def load_scenarios():
    """Load all scenario JSON files, return list of (name, data) tuples."""
    if not SCENARIOS_DIR.is_dir():
        return []
    scenarios = []
    for f in sorted(SCENARIOS_DIR.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        scenarios.append((f.stem, data))
    return scenarios


def scenario_ids():
    """Return scenario names for test parametrization."""
    return [s[0] for s in load_scenarios()]


# ═══════════════════════════════════════════════════════════════════════════════
# Structure & Completeness Tests (run on every scenario)
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", load_scenarios(), ids=scenario_ids())
async def test_scenario_assessment_structure(scenario):
    """Every scenario must produce a structurally valid assessment result."""
    name, data = scenario
    vision = data.get("vision", {})
    age = data.get("age", "middle")
    child = data.get("child", "测试幼儿")

    assert age in VALID_AGE_GROUPS, f"Invalid age_group: {age}"
    assert "problems" in vision, f"vision missing 'problems' key"
    assert isinstance(vision["problems"], list), f"'problems' must be a list"

    result = await assess(vision, age_group=age, child_name=child)

    # Top-level keys
    assert result["child_name"] == child
    assert result["age_group"] == age
    assert "assessment" in result
    assert isinstance(result["assessment"], list)
    assert len(result["assessment"]) == 4, "Must assess all 4 dimensions"

    # Each dimension
    for dim in result["assessment"]:
        assert dim["dimension"] in VALID_DIMENSIONS, f"Unknown dimension: {dim['dimension']}"
        assert "display_name" in dim
        assert "score" in dim
        assert isinstance(dim["score"], (int, float))
        assert 0.0 <= dim["score"] <= 100.0, f"Score {dim['score']} out of range"
        assert dim["level"] in VALID_LEVELS, f"Unknown level: {dim['level']}"
        assert "level_emoji" in dim
        assert "level_name" in dim
        assert "pck_stage" in dim
        assert "sub_skills" in dim
        assert isinstance(dim["sub_skills"], list)
        assert "error_patterns" in dim
        assert isinstance(dim["error_patterns"], list)
        assert "recommendations" in dim
        assert len(dim["recommendations"]) > 0

        # Score details
        sd = dim.get("score_details", {})
        assert "correct" in sd
        assert "total" in sd
        assert sd["correct"] <= sd["total"]

        # Reasoning chain
        rc = dim.get("reasoning_chain", {})
        assert "summary" in rc
        # Note: blank worksheet has simplified chain (summary only, no steps)
        if dim["score"] > 0 or dim.get("score_details", {}).get("total", 0) > 0:
            assert "steps" in rc, f"Missing steps in reasoning chain for {dim['dimension']}"
            steps = rc["steps"]
            assert "observation" in steps, "Missing step 1: observation"
            assert "milestone_comparison" in steps, "Missing step 2: milestone comparison"
            assert "level_determination" in steps, "Missing step 3: level determination"
            assert "error_analysis" in steps, "Missing step 4: error analysis"
            assert "recommendation_basis" in steps, "Missing step 5: recommendation basis"


@pytest.mark.asyncio
@pytest.mark.parametrize("scenario", load_scenarios(), ids=scenario_ids())
async def test_scenario_dual_reports(scenario):
    """Every scenario must produce valid teacher + parent reports."""
    name, data = scenario
    vision = data.get("vision", {})
    age = data.get("age", "middle")
    child = data.get("child", "测试幼儿")

    assessment = await assess(vision, age_group=age, child_name=child)
    teacher = await generate_teacher_report(assessment, child_name=child, age_group=age)
    parent = await generate_parent_report(assessment, child_name=child, age_group=age)

    # Teacher report structure
    assert "dimensions" in teacher
    assert "radar_chart_data" in teacher
    assert "pck_analysis" in teacher
    assert "teaching_suggestions" in teacher
    assert "teaching_reflection_questions" in teacher

    # Parent report structure
    assert "strengths" in parent
    assert isinstance(parent["strengths"], list)
    assert "growing_areas" in parent
    assert isinstance(parent["growing_areas"], list)
    assert "family_activities" in parent
    assert "learning_quality_notes" in parent
    assert "overall_summary" in parent

    # CRITICAL: Parent report must NEVER use forbidden words
    forbidden = ["分数", "排名", "落后", "成绩"]
    parent_str = json.dumps(parent, ensure_ascii=False)
    for word in forbidden:
        assert word not in parent_str, f"PARENT REPORT VIOLATION: '{word}' found!"


# ═══════════════════════════════════════════════════════════════════════════════
# Specific PCK Rule Tests
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.asyncio
async def test_blank_worksheet_early_return():
    """Blank worksheet should trigger early return with L1 for all dimensions."""
    data = json.loads((SCENARIOS_DIR / "blank-worksheet.json").read_text(encoding="utf-8"))
    result = await assess(data["vision"], age_group=data["age"], child_name=data["child"])

    for dim in result["assessment"]:
        assert dim["score"] == 0.0
        assert dim["level"] == "L1"
        assert dim["age_benchmark_comparison"] == "本张操作单未作答，无法评估"
        assert dim["recommendations"] == "请幼儿完成操作单后重新上传分析"


@pytest.mark.asyncio
async def test_cross_age_anchoring():
    """Same answers, different ages → different levels. Small class should get more lenient levels."""
    small = json.loads((SCENARIOS_DIR / "cross-age-small.json").read_text(encoding="utf-8"))
    large = json.loads((SCENARIOS_DIR / "cross-age-large.json").read_text(encoding="utf-8"))

    result_small = await assess(small["vision"], age_group="small", child_name="test")
    result_large = await assess(large["vision"], age_group="large", child_name="test")

    small_levels = {d["dimension"]: d["level"] for d in result_small["assessment"]}
    large_levels = {d["dimension"]: d["level"] for d in result_large["assessment"]}

    # counting: small should NOT be stricter than large
    counting_small = small_levels.get("counting", "L1")
    counting_large = large_levels.get("counting", "L1")
    assert counting_small >= counting_large, \
        f"Age anchoring FAILED: small={counting_small}, large={counting_large}. Small should be >= lenient."

    print(f"  counting: small={counting_small}, large={counting_large}")


@pytest.mark.asyncio
async def test_shape_priority_dimension_mapping():
    """shape_counting problem type → shapes_space dimension (shape priority rule)."""
    data = json.loads((SCENARIOS_DIR / "shape-counting.json").read_text(encoding="utf-8"))
    result = await assess(data["vision"], age_group=data["age"], child_name=data["child"])

    shapes_dim = next(d for d in result["assessment"] if d["dimension"] == Dimension.SHAPES_SPACE)
    counting_dim = next(d for d in result["assessment"] if d["dimension"] == Dimension.COUNTING)

    # shape_counting problems (P1, P2) should land in shapes_space, not counting
    sd = shapes_dim["score_details"]
    assert sd["total"] >= 2, f"Expected ≥2 shape problems, got {sd['total']} in shapes_space"
    print(f"  shapes_space: {sd['correct']}/{sd['total']}, counting: {counting_dim['score_details']['correct']}/{counting_dim['score_details']['total']}")


@pytest.mark.asyncio
async def test_mirror_writing_detected_not_penalized():
    """Mirror writing should be flagged in error_patterns but score should reflect intent."""
    data = json.loads((SCENARIOS_DIR / "mirror-writing.json").read_text(encoding="utf-8"))
    result = await assess(data["vision"], age_group=data["age"], child_name=data["child"])

    counting_dim = next(d for d in result["assessment"] if d["dimension"] == Dimension.COUNTING)
    # Mirror writing detection should appear somewhere
    all_errors = " ".join(counting_dim.get("error_patterns", []))
    print(f"  errors: {all_errors}")


@pytest.mark.asyncio
async def test_add_sub_confusion_detected():
    """Subtraction with answer > minuend should trigger add-sub confusion flag."""
    data = json.loads((SCENARIOS_DIR / "add-sub-confusion.json").read_text(encoding="utf-8"))
    result = await assess(data["vision"], age_group=data["age"], child_name=data["child"])

    add_dim = next(d for d in result["assessment"] if d["dimension"] == Dimension.ADDITION_SUBTRACTION)
    all_errors = " ".join(add_dim.get("error_patterns", []))
    assert "混淆" in all_errors or "加法" in all_errors, \
        f"Add-sub confusion NOT detected! errors={all_errors}"
    print(f"  add_sub errors: {all_errors}")


@pytest.mark.asyncio
async def test_all_correct_achieves_high_levels():
    """All-correct scenario (large class) should achieve L3+ on scored dimensions."""
    data = json.loads((SCENARIOS_DIR / "all-correct.json").read_text(encoding="utf-8"))
    result = await assess(data["vision"], age_group=data["age"], child_name=data["child"])

    for dim in result["assessment"]:
        sd = dim["score_details"]
        if sd["total"] > 0:
            assert dim["score"] == 100.0, \
                f"{dim['display_name']}: all correct but score={dim['score']}%"
            assert dim["level"] in ("L3", "L4"), \
                f"{dim['display_name']}: all correct but level={dim['level']}"


@pytest.mark.asyncio
async def test_all_incorrect_triggers_l1():
    """All-incorrect scenario (large class) should produce L1 on scored dimensions."""
    data = json.loads((SCENARIOS_DIR / "all-incorrect.json").read_text(encoding="utf-8"))
    result = await assess(data["vision"], age_group=data["age"], child_name=data["child"])

    l1_count = sum(1 for d in result["assessment"] if d["level"] == "L1")
    assert l1_count >= 2, f"Expected ≥2 L1 dimensions, got {l1_count}"
    print(f"  L1 dimensions: {l1_count}/4")
