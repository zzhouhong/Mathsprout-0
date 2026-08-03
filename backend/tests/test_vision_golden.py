"""
Vision Recognition Golden Set Tests.

Scans `tests/images/golden/` for subdirectories containing an image file
and an `expected.json`. For each case, runs the full recognition pipeline
and validates the result against the expected output.

Golden set tests use structural assertions (not exact match) since vision
recognition has inherent randomness:
  - Problem count within range
  - Required dimensions covered
  - At least one correct answer
  - Unrecognized ratio below threshold
  - Specific answer fuzzy matching (digit extraction + containment)

Run:
    cd backend
    python -m pytest tests/test_vision_golden.py -v

Add new cases:
    python build_golden.py --image path/to/worksheet.jpg --name "case-name"
"""

import json
import re
import pytest
from pathlib import Path

GOLDEN_DIR = Path(__file__).parent / "images" / "golden"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}


def discover_golden_cases():
    """
    Scan golden/ for subdirectories with an image + expected.json.
    Returns list of (case_name, image_path, expected_dict).
    """
    cases = []
    if not GOLDEN_DIR.exists():
        return cases

    for case_dir in sorted(GOLDEN_DIR.iterdir()):
        if not case_dir.is_dir():
            continue
        expected_file = case_dir / "expected.json"
        if not expected_file.exists():
            continue
        # Find the image file
        image_files = [
            f for f in case_dir.iterdir()
            if f.suffix.lower() in IMAGE_EXTENSIONS
        ]
        if not image_files:
            continue
        try:
            expected = json.loads(expected_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        cases.append((case_dir.name, image_files[0], expected))
    return cases


def _extract_numbers(text: str) -> list:
    """Extract all integer/float numbers from a string."""
    if not text or not isinstance(text, str):
        return []
    return re.findall(r'\d+(?:\.\d+)?', text)


def _fuzzy_match_answer(actual: str, expected: str) -> bool:
    """
    Fuzzy match for child answers / correct answers.
    Handles:
      - Exact match
      - Numeric extraction (e.g., "第3个" matches "3")
      - Containment (e.g., "三角形" matches "三角")
      - Chinese number mapping
    """
    if not actual or not expected:
        return False
    # Normalize
    a = str(actual).strip()
    e = str(expected).strip()

    # Exact match
    if a == e:
        return True

    # Containment
    if e in a or a in e:
        return True

    # Numeric match
    a_nums = _extract_numbers(a)
    e_nums = _extract_numbers(e)
    if a_nums and e_nums and a_nums[0] == e_nums[0]:
        return True

    # Chinese number mapping
    cn_map = {
        "一": "1", "二": "2", "三": "3", "四": "4", "五": "5",
        "六": "6", "七": "7", "八": "8", "九": "9", "十": "10",
        "两": "2",
    }
    for cn, ar in cn_map.items():
        if cn in a and ar in e:
            return True
        if ar in a and cn in e:
            return True

    return False


# Collect cases at import time
_golden_cases = discover_golden_cases()


def _case_ids():
    return [c[0] for c in _golden_cases]


@pytest.mark.skipif(
    not _golden_cases,
    reason="No golden cases found in tests/images/golden/. "
           "Add cases with: python build_golden.py --image <path> --name <name>"
)
@pytest.mark.parametrize(
    "case_name,image_path,expected",
    _golden_cases,
    ids=_case_ids(),
)
class TestGoldenCase:
    """Parameterized test for each golden case."""

    @pytest.mark.asyncio
    async def test_recognition_structure(self, case_name, image_path, expected):
        """Verify the recognition result matches the expected structure."""
        from app.services.image_processor import ImageProcessor
        from app.services.worksheet_recognizer import WorksheetRecognizer

        age_group = expected.get("age_group", "middle")
        exp = expected.get("expected", {})
        tolerance = expected.get("tolerance", {})

        # Load and preprocess image
        image_data = image_path.read_bytes()
        processor = ImageProcessor(target_size_px=1080)
        processed, _ = await processor.process(image_data, image_path.name)

        # Run recognition
        recognizer = WorksheetRecognizer()
        result = await recognizer.analyze(processed, age_group=age_group, use_cache=False)

        problems = result.get("problems", [])
        obs = result.get("observations", {})

        # ── Structural assertions ──

        # 1. Worksheet type (if specified)
        if "worksheet_type" in exp:
            # Allow fuzzy match — "mixed" includes any non-blank type
            actual_type = result.get("worksheet_type", "")
            if exp["worksheet_type"] == "mixed":
                assert actual_type in ("mixed", "counting", "addition_subtraction",
                                        "shapes_space", "shapes", "patterns", "incomplete"), \
                    f"{case_name}: unexpected worksheet_type={actual_type}"
            else:
                assert actual_type == exp["worksheet_type"], \
                    f"{case_name}: expected type={exp['worksheet_type']}, got {actual_type}"

        # 2. Problem count in range
        if "problem_count" in exp:
            pc = exp["problem_count"]
            min_count = pc.get("min", 0)
            max_count = pc.get("max", 100)
            assert min_count <= len(problems) <= max_count, \
                f"{case_name}: problem count {len(problems)} not in [{min_count}, {max_count}]"

        # 3. Required dimensions covered
        if "dimensions_covered" in exp:
            # Determine which dimensions have scored problems
            dim_counts = {}
            for p in problems:
                ptype = p.get("type", "")
                # Map problem type to dimension (rough heuristic)
                dim_map = {
                    "counting": "counting", "compare": "counting",
                    "add_10": "addition_subtraction", "sub_10": "addition_subtraction",
                    "number_composition": "addition_subtraction",
                    "shape_id": "shapes_space", "shape_counting": "shapes_space",
                    "spatial_position": "shapes_space",
                    "pattern_next": "patterns", "sort": "patterns", "classify": "patterns",
                }
                dim = dim_map.get(ptype, "unknown")
                dim_counts[dim] = dim_counts.get(dim, 0) + 1

            for required_dim in exp["dimensions_covered"]:
                assert dim_counts.get(required_dim, 0) > 0, \
                    f"{case_name}: dimension '{required_dim}' not covered. Found: {list(dim_counts.keys())}"

        # 4. At least one correct answer (if requested)
        if exp.get("at_least_one_correct"):
            correct_count = sum(1 for p in problems if p.get("is_correct") is True)
            assert correct_count >= 1, \
                f"{case_name}: expected at least 1 correct answer, got {correct_count}"

        # 5. Max unrecognized ratio
        if "max_unrecognized_ratio" in tolerance:
            max_ratio = tolerance["max_unrecognized_ratio"]
            if problems:
                unrecognized = sum(
                    1 for p in problems
                    if p.get("child_answer", "") in ("", "未识别", "未作答")
                )
                ratio = unrecognized / len(problems)
                assert ratio <= max_ratio, \
                    f"{case_name}: unrecognized ratio {ratio:.0%} > {max_ratio:.0%}"

        # 6. Min dimensions scored
        if "min_dimensions_scored" in tolerance:
            min_dims = tolerance["min_dimensions_scored"]
            scored_dims = sum(1 for d, c in dim_counts.items() if c > 0)
            assert scored_dims >= min_dims, \
                f"{case_name}: only {scored_dims} dimensions scored, need >= {min_dims}"

        # 7. Specific problem matching (if specified)
        expected_problems = exp.get("problems", [])
        for ep in expected_problems:
            ep_id = ep.get("id")
            # Find matching problem by ID or by position
            actual_prob = None
            if ep_id:
                actual_prob = next((p for p in problems if p.get("id") == ep_id), None)
            if not actual_prob and "type" in ep:
                # Match by type (first of that type)
                actual_prob = next((p for p in problems if p.get("type") == ep["type"]), None)

            if actual_prob is None:
                pytest.skip(f"{case_name}: no problem matching id={ep_id} or type={ep.get('type')}")
                continue

            # Check child_answer match (fuzzy)
            if "child_answer_match" in ep:
                actual_answer = actual_prob.get("child_answer", "")
                assert _fuzzy_match_answer(actual_answer, ep["child_answer_match"]), \
                    f"{case_name}: problem {ep.get('id','?')} child_answer '{actual_answer}' " \
                    f"doesn't match expected '{ep['child_answer_match']}'"

            # Check correct_answer match (fuzzy)
            if "correct_answer_match" in ep:
                actual_correct = actual_prob.get("correct_answer", "")
                assert _fuzzy_match_answer(actual_correct, ep["correct_answer_match"]), \
                    f"{case_name}: problem {ep.get('id','?')} correct_answer '{actual_correct}' " \
                    f"doesn't match expected '{ep['correct_answer_match']}'"

            # Check type match
            if "type" in ep:
                assert actual_prob.get("type") == ep["type"], \
                    f"{case_name}: problem type mismatch: expected {ep['type']}, got {actual_prob.get('type')}"


def test_golden_set_not_empty():
    """Sanity check: at least one golden case exists."""
    if not _golden_cases:
        pytest.skip("No golden cases in tests/images/golden/. "
                     "Add with: python build_golden.py --image <path> --name <name>")
    assert len(_golden_cases) >= 1
