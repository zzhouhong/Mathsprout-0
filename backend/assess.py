r"""
萌芽数学 Mathsprout — 独立评估核心 CLI

纯 Python 脚本，零外部依赖（无 AI API、无数据库、无 Web）。
接受 JSON 场景文件，跑通 PCK 评估引擎 → 双报告全流程。

用法:
  .\venv\Scripts\python.exe assess.py --input tests/scenarios/typical.json
  .\venv\Scripts\python.exe assess.py --input tests/scenarios/advanced.json --format markdown
  .\venv\Scripts\python.exe assess.py --input tests/scenarios/  (跑整个目录)
  .\venv\Scripts\python.exe assess.py --demo  (跑内置 3 个 demo 场景)
"""

import json
import sys
import io

# Force UTF-8 output on Windows (PowerShell GBK chokes on emoji)
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).parent))

from app.services.assessment_engine import assess
from app.services.report_generator import generate_teacher_report, generate_parent_report

# ═══════════════════════════════════════════════════════════════════════════════
# 内置场景（来自 competition.py 的 DEMO_SCENARIOS）
# ═══════════════════════════════════════════════════════════════════════════════

DEMO_SCENARIOS = {
    "advanced": {
        "child": "小明", "age": "large",
        "vision": {
            "worksheet_type": "mixed", "problems": [
                {"id": "P1", "type": "shape_id", "child_answer": "三角形", "correct_answer": "三角形", "is_correct": True, "confidence": 0.95, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": ""},
                {"id": "P2", "type": "shape_id", "child_answer": "正方形", "correct_answer": "正方形", "is_correct": True, "confidence": 0.9, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": ""},
                {"id": "P3", "type": "spatial", "child_answer": "上面", "correct_answer": "上面", "is_correct": True, "confidence": 0.85, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": ""},
                {"id": "P4", "type": "add_10", "child_answer": "8", "correct_answer": "8", "is_correct": True, "confidence": 0.92, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": "mental"},
                {"id": "P5", "type": "counting", "child_answer": "10", "correct_answer": "10", "is_correct": True, "confidence": 0.9, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": "mental"},
                {"id": "P6", "type": "sub_10", "child_answer": "4", "correct_answer": "4", "is_correct": True, "confidence": 0.88, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": "mental"},
            ],
            "observations": {"overall_pck_notes": "幼儿表现出较强的图形感知和空间方位能力，运算思维已进入符号水平"},
        }
    },
    "typical": {
        "child": "小华", "age": "middle",
        "vision": {
            "worksheet_type": "mixed", "problems": [
                {"id": "P1", "type": "counting", "child_answer": "5", "correct_answer": "5", "is_correct": True, "confidence": 0.95, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": "counting_objects"},
                {"id": "P2", "type": "counting", "child_answer": "3", "correct_answer": "4", "is_correct": False, "confidence": 0.8, "handwriting_quality": "clear", "has_erasure": True, "erasure_pattern": "self_correct", "strategy_indicators": ""},
                {"id": "P3", "type": "add_10", "child_answer": "7", "correct_answer": "7", "is_correct": True, "confidence": 0.9, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": "finger_counting"},
                {"id": "P4", "type": "sub_10", "child_answer": "5", "correct_answer": "3", "is_correct": False, "confidence": 0.85, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": "counting_objects"},
                {"id": "P5", "type": "shape_id", "child_answer": "圆形", "correct_answer": "圆形", "is_correct": True, "confidence": 0.9, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": ""},
                {"id": "P6", "type": "pattern_next", "child_answer": "△", "correct_answer": "△", "is_correct": True, "confidence": 0.85, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": ""},
            ],
            "observations": {"overall_pck_notes": "幼儿处于中班典型发展水平，各维度表现基本符合年龄期望"},
        }
    },
    "developing": {
        "child": "小花", "age": "small",
        "vision": {
            "worksheet_type": "mixed", "problems": [
                {"id": "P1", "type": "counting", "child_answer": "3", "correct_answer": "5", "is_correct": False, "confidence": 0.8, "handwriting_quality": "clear", "has_erasure": True, "erasure_pattern": "persistent_error", "strategy_indicators": "counting_objects"},
                {"id": "P2", "type": "counting", "child_answer": "2", "correct_answer": "3", "is_correct": False, "confidence": 0.75, "handwriting_quality": "mirrored", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": "counting_objects"},
                {"id": "P3", "type": "classify", "child_answer": "红色", "correct_answer": "红色", "is_correct": True, "confidence": 0.9, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": ""},
                {"id": "P4", "type": "compare", "child_answer": "左边多", "correct_answer": "左边多", "is_correct": True, "confidence": 0.85, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": ""},
            ],
            "observations": {"overall_pck_notes": "幼儿处于点数能力发展初期，手口一致点数尚不稳定，但分类与比较能力开始萌芽"},
        }
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# 输出格式化
# ═══════════════════════════════════════════════════════════════════════════════

def format_as_markdown(scenario_name, child, age, assessment, teacher_report, parent_report, timing_ms):
    """将评估结果格式化为可读 Markdown."""
    lines = []
    lines.append(f"# 萌芽数学评估报告")
    lines.append(f"")
    lines.append(f"**场景**: `{scenario_name}` | **幼儿**: {child} | **年龄段**: {age} | **耗时**: {timing_ms:.0f}ms")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 📊 四维度评估")
    lines.append(f"")
    lines.append(f"| 维度 | 得分 | 等级 | PCK 阶段 | 对/总 |")
    lines.append(f"|------|------|------|----------|-------|")
    for d in assessment.get("assessment", []):
        sd = d.get("score_details", {})
        lines.append(f"| {d['display_name']} | **{d['score']}%** | {d['level_emoji']} {d['level_name']} | {d.get('pck_stage', '—')} | {sd.get('correct','?')}/{sd.get('total','?')} |")
    lines.append(f"")
    lines.append(f"### 各维度错误模式")
    for d in assessment.get("assessment", []):
        if d.get("error_patterns"):
            for ep in d["error_patterns"]:
                lines.append(f"- **{d['display_name']}**: {ep}")
    lines.append(f"")
    lines.append(f"### 总评")
    lines.append(f"{assessment.get('overall_summary', '—')}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 👩‍🏫 教师报告要点")
    lines.append(f"")
    lines.append(f"### PCK 分析")
    lines.append(f"{teacher_report.get('pck_analysis', '—')}")
    lines.append(f"")
    lines.append(f"### 教学建议")
    for dim_name, suggestion in teacher_report.get("teaching_suggestions", {}).items():
        lines.append(f"- **{dim_name}** [{suggestion.get('current_stage', '')}] → {suggestion.get('next_stage_goal', '')}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"## 👨‍👩‍👧 家长报告要点")
    lines.append(f"")
    lines.append(f"### 优势领域")
    for s in parent_report.get("strengths", []):
        lines.append(f"- {s.get('emoji', '')} **{s.get('dimension', '')}**: {s.get('description', '')}")
    lines.append(f"")
    lines.append(f"### 成长中的领域")
    for g in parent_report.get("growing_areas", []):
        lines.append(f"- 🌱 **{g.get('dimension', '')}**: {g.get('description', '')}")
    lines.append(f"")
    lines.append(f"### 家庭活动推荐")
    for act in parent_report.get("family_activities", []):
        lines.append(f"- **{act.get('title', '')}** — {act.get('why', '')}")
    lines.append(f"")
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 核心逻辑
# ═══════════════════════════════════════════════════════════════════════════════

async def run_scenario(scenario_data: dict, scenario_name: str = "unknown", output_format: str = "json"):
    """Run a single scenario through the full assessment pipeline."""
    child = scenario_data.get("child", "幼儿")
    age = scenario_data.get("age", "middle")
    vision = scenario_data.get("vision", {})

    t0 = datetime.now()

    # Step 1: Assessment
    assessment_result = await assess(vision, age_group=age, child_name=child)

    # Step 2: Dual reports
    teacher_report = await generate_teacher_report(assessment_result, child_name=child, age_group=age)
    parent_report = await generate_parent_report(assessment_result, child_name=child, age_group=age)

    t1 = datetime.now()
    timing_ms = (t1 - t0).total_seconds() * 1000

    # Output
    result = {
        "success": True,
        "scenario": scenario_name,
        "child": child,
        "age_group": age,
        "timing_ms": round(timing_ms, 1),
        "assessment": assessment_result,
        "teacher_report": teacher_report,
        "parent_report": parent_report,
    }

    if output_format == "markdown":
        print(format_as_markdown(scenario_name, child, age, assessment_result, teacher_report, parent_report, timing_ms))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))

    return result


async def run_all_scenarios(scenarios_dir: str, output_format: str = "json"):
    """Run all JSON scenario files in a directory."""
    dir_path = Path(scenarios_dir)
    if not dir_path.is_dir():
        print(f"错误: 目录不存在 — {scenarios_dir}", file=sys.stderr)
        sys.exit(1)

    json_files = sorted(dir_path.glob("*.json"))
    if not json_files:
        print(f"警告: {scenarios_dir} 下无 .json 文件", file=sys.stderr)
        return

    print(f"发现 {len(json_files)} 个场景文件\n")

    for i, json_file in enumerate(json_files, 1):
        print(f"{'─' * 60}")
        print(f"[{i}/{len(json_files)}] {json_file.name}")
        print(f"{'─' * 60}")
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            await run_scenario(data, scenario_name=json_file.stem, output_format=output_format)
        except Exception as e:
            print(f"  ❌ 失败: {e}", file=sys.stderr)
        print()


async def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="萌芽数学 Mathsprout — 独立评估核心 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --input tests/scenarios/typical.json
  %(prog)s --input tests/scenarios/typical.json --format markdown
  %(prog)s --input tests/scenarios/    (跑整个目录)
  %(prog)s --demo                       (跑内置 3 个 demo 场景)
        """.strip(),
    )
    parser.add_argument("--input", "-i", type=str, help="JSON 场景文件路径（或目录路径）")
    parser.add_argument("--demo", action="store_true", help="跑内置 3 个 demo 场景")
    parser.add_argument("--format", "-f", type=str, choices=["json", "markdown"], default="json",
                        help="输出格式（默认: json）")

    args = parser.parse_args()

    if args.demo:
        print("=" * 60)
        print("  萌芽数学 Mathsprout — 内置 Demo 场景")
        print("=" * 60)
        print()
        for name, data in DEMO_SCENARIOS.items():
            print(f"{'─' * 60}")
            print(f"  场景: {name}")
            print(f"{'─' * 60}")
            await run_scenario(data, scenario_name=name, output_format=args.format)
            print()
        return

    if not args.input:
        parser.print_help()
        sys.exit(1)

    input_path = Path(args.input)
    if input_path.is_dir():
        await run_all_scenarios(str(input_path), args.format)
    elif input_path.is_file():
        data = json.loads(input_path.read_text(encoding="utf-8"))
        await run_scenario(data, scenario_name=input_path.stem, output_format=args.format)
    else:
        print(f"错误: 路径不存在 — {args.input}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
