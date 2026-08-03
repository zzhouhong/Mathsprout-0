"""
build_golden.py — Interactive helper to create golden test cases for vision_eval.

Takes an operation sheet image, runs the recognition pipeline, then prompts
the user to confirm/correct each field. Saves the result as:
    tests/images/golden/<name>/image.png
    tests/images/golden/<name>/expected.json

Usage:
    cd backend
    .\\venv\\Scripts\\python.exe build_golden.py --image path/to/worksheet.jpg --name "counting-basic"
    .\\venv\\Scripts\\python.exe build_golden.py --image path/to/ws.png  # auto-name from filename
"""

import asyncio
import json
import sys
import shutil
import argparse
from pathlib import Path

# Ensure backend is on path
sys.path.insert(0, str(Path(__file__).parent))

GOLDEN_DIR = Path(__file__).parent / "tests" / "images" / "golden"


async def run_recognition(image_path: Path, age_group: str, quality: str) -> dict:
    """Run the full recognition pipeline and return the result."""
    from app.services.image_processor import ImageProcessor, resolve_image_size
    from app.services.worksheet_recognizer import WorksheetRecognizer

    print(f"\n[1/3] 预处理图片: {image_path.name}")
    image_data = image_path.read_bytes()
    processor = ImageProcessor(target_size_px=resolve_image_size(quality))
    processed, out_name = await processor.process(image_data, image_path.name)
    print(f"      输出: {out_name} ({len(processed)} bytes)")

    print(f"[2/3] 运行 3-pass 识别 (age={age_group})...")
    recognizer = WorksheetRecognizer()
    result = await recognizer.analyze(processed, age_group=age_group, use_cache=False)

    meta = result.get("_meta", {})
    problems = result.get("problems", [])
    print(f"      识别完成: {len(problems)} 道题目, "
          f"模型={meta.get('model', '?')}, "
          f"tokens={meta.get('usage', {}).get('total_tokens', '?')}")

    return result


def interactive_confirm(result: dict, age_group: str) -> dict:
    """Let the user review and modify the recognition result."""
    problems = result.get("problems", [])
    obs = result.get("observations", {})

    print("\n[3/3] 交互确认（直接回车保留原值）\n")
    print(f"  操作单标题: {obs.get('title', '未标注')}")
    print(f"  学习目标: {obs.get('learning_objective', '未标注')}")
    print(f"  类型: {result.get('worksheet_type', '?')}")
    print()

    # Show each problem
    for i, p in enumerate(problems):
        print(f"  题目 {p.get('id', f'P{i+1}')}:")
        print(f"    类型: {p.get('type', '?')}")
        print(f"    幼儿答案: {p.get('child_answer', '?')}")
        print(f"    正确答案: {p.get('correct_answer', '?')}")
        print(f"    对错: {'✓' if p.get('is_correct') else '✗' if p.get('is_correct') is False else '?'}")
        print(f"    置信度: {p.get('confidence', 0):.2f}")
        print()

    # Interactive corrections
    expected_problems = []
    for i, p in enumerate(problems):
        pid = p.get("id", f"P{i+1}")
        print(f"\n--- 确认题目 {pid} ---")

        child_ans = input(f"  幼儿答案 [{p.get('child_answer', '')}]: ").strip()
        if not child_ans:
            child_ans = p.get("child_answer", "")

        correct_ans = input(f"  正确答案 [{p.get('correct_answer', '')}]: ").strip()
        if not correct_ans:
            correct_ans = p.get("correct_answer", "")

        expected_problems.append({
            "id": pid,
            "type": p.get("type", ""),
            "child_answer_match": child_ans,
            "correct_answer_match": correct_ans,
        })

    # Determine dimensions covered
    dim_map = {
        "counting": "counting", "compare": "counting",
        "add_10": "addition_subtraction", "sub_10": "addition_subtraction",
        "number_composition": "addition_subtraction",
        "shape_id": "shapes_space", "shape_counting": "shapes_space",
        "spatial_position": "shapes_space",
        "pattern_next": "patterns", "sort": "patterns", "classify": "patterns",
    }
    dims_covered = sorted(set(
        dim_map.get(p.get("type", ""), "")
        for p in problems
        if dim_map.get(p.get("type", ""), "")
    ))

    # Build expected.json
    expected = {
        "age_group": age_group,
        "child_name": "测试幼儿",
        "expected": {
            "worksheet_type": result.get("worksheet_type", "mixed"),
            "problem_count": {
                "min": max(1, len(problems) - 2),
                "max": len(problems) + 2,
            },
            "dimensions_covered": dims_covered,
            "at_least_one_correct": any(p.get("is_correct") for p in problems),
            "problems": expected_problems,
        },
        "tolerance": {
            "min_dimensions_scored": max(1, len(dims_covered) - 1),
            "max_unrecognized_ratio": 0.5,
        },
    }
    return expected


def save_case(name: str, image_path: Path, expected: dict, processed_data: bytes = None):
    """Save the golden case to disk."""
    case_dir = GOLDEN_DIR / name
    case_dir.mkdir(parents=True, exist_ok=True)

    # Copy image
    ext = image_path.suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp"}:
        ext = ".png"
    dest_image = case_dir / f"image{ext}"
    if processed_data:
        dest_image.write_bytes(processed_data)
    else:
        shutil.copy2(image_path, dest_image)
    print(f"\n保存图片: {dest_image}")

    # Save expected.json
    dest_json = case_dir / "expected.json"
    dest_json.write_text(json.dumps(expected, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"保存期望: {dest_json}")

    print(f"\n✅ Golden case '{name}' 已创建！")
    print(f"   运行测试: python -m pytest tests/test_vision_golden.py -v")


async def main():
    parser = argparse.ArgumentParser(description="Build a golden test case for vision recognition")
    parser.add_argument("--image", "-i", required=True, help="Path to worksheet image")
    parser.add_argument("--name", "-n", help="Case name (default: auto from filename)")
    parser.add_argument("--age-group", "-a", default="middle", choices=["small", "middle", "large"])
    parser.add_argument("--quality", "-q", default="balanced", choices=["fast", "balanced", "precise"])
    parser.add_argument("--skip-interactive", action="store_true", help="Skip interactive confirmation")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"❌ 图片不存在: {image_path}")
        sys.exit(1)

    name = args.name or image_path.stem.lower().replace(" ", "-")

    # Run recognition
    result = await run_recognition(image_path, args.age_group, args.quality)

    if args.skip_interactive:
        # Auto-generate expected from result
        problems = result.get("problems", [])
        dim_map = {
            "counting": "counting", "compare": "counting",
            "add_10": "addition_subtraction", "sub_10": "addition_subtraction",
            "shape_id": "shapes_space", "shape_counting": "shapes_space",
            "pattern_next": "patterns", "sort": "patterns",
        }
        dims = sorted(set(dim_map.get(p.get("type", ""), "") for p in problems))
        expected = {
            "age_group": args.age_group,
            "child_name": "测试幼儿",
            "expected": {
                "worksheet_type": result.get("worksheet_type", "mixed"),
                "problem_count": {"min": max(1, len(problems) - 2), "max": len(problems) + 2},
                "dimensions_covered": dims,
                "at_least_one_correct": False,  # conservative
                "problems": [
                    {"id": p.get("id", ""), "type": p.get("type", ""),
                     "child_answer_match": p.get("child_answer", ""),
                     "correct_answer_match": p.get("correct_answer", "")}
                    for p in problems
                ],
            },
            "tolerance": {"min_dimensions_scored": 1, "max_unrecognized_ratio": 0.5},
        }
    else:
        expected = interactive_confirm(result, args.age_group)

    save_case(name, image_path, expected)


if __name__ == "__main__":
    asyncio.run(main())
