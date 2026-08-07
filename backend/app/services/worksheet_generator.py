"""
Dynamic Worksheet Generator — Creates printable math worksheets tailored to child's level.

Generates A4-format math worksheets with:
- Age/difficulty-appropriate problems
- Visual elements (emojis for young children)
- Header with child name and date
- Teacher notes section
"""

import random
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .interactive_content.templates import TEMPLATE_REGISTRY
from .interactive_content.scenarios import (
    pick_scenario,
    OPERATION_BY_TYPE,
    SUPPORTED_OPERATIONS,
)
from .interactive_content.progressions import (
    NUMBER_RANGES,
    QUESTIONS_PER_SESSION,
    get_age_anchor_level,
)
from app.core.prompts.pck_reference import (
    SUB_DIMENSION_TO_DIMENSION,
    get_sub_dimension_display_name,
    get_dimension_display_name,
)


@dataclass
class WorksheetConfig:
    """Configuration for worksheet generation."""
    child_name: str = "小朋友"
    age_group: str = "middle"           # small / middle / large
    difficulty_level: int = 2           # 1-5
    dimensions: List[str] = field(default_factory=lambda: ["counting", "shapes_space"])
    problem_count: int = 1              # Single cartoon card per generation
    include_instructions: bool = True
    include_answer_key: bool = True
    large_font: bool = True             # For young children
    show_example: bool = True
    learning_objective: str = ""        # Printed on worksheet, e.g. "感知三角形的多种变式"
    activity_theme: str = ""            # 教师输入的活动情境（如"春游时小兔分萝卜"）；非空走 AI 情境化生成


@dataclass
class WorksheetProblem:
    """A single problem on the worksheet."""
    number: int
    type: str
    dimension: str
    prompt: str
    data: Dict[str, Any]
    correct_answer: Any
    workspace_lines: int = 2            # Number of blank lines for writing
    operation: str = ""                 # 操作类型：涂色/圈画/描线/配对/找一找/按规律续/点数
    scenario: str = ""                  # 本题情境（整单故事线下）


@dataclass
class GeneratedWorksheet:
    """A complete generated worksheet."""
    title: str
    child_name: str
    date: str
    age_group: str
    difficulty_level: int
    problems: List[WorksheetProblem]
    instructions: str
    answer_key: Dict[int, Any]
    config: WorksheetConfig
    total_possible: int
    learning_objective: str = ""
    memory_note: str = ""           # B6: "📌 针对上次薄弱的…" line when child_memory present
    story_title: str = ""           # 整单故事标题（如"小兔的萝卜园"）
    scene_intro: str = ""           # 情境引言（开场白）
    mascot_name: str = ""           # 整单固定卡通角色
    generation_note: str = ""       # 降级/提示说明
    generation_mode: str = "template"  # ai / template / fallback


# ─── Worksheet Generator ──────────────────────────────────────────────

def generate_worksheet(config: Optional[WorksheetConfig] = None, child_memory: Optional[Dict[str, Any]] = None) -> GeneratedWorksheet:
    """
    Generate a complete printable worksheet.

    Args:
        config: Worksheet generation settings (uses defaults if None)
        child_memory: Optional child memory dict (from memory_service) — when
            present, the worksheet surfaces a "📌 针对上次薄弱" note so the
            generated sheet visibly targets the child's weak dimensions.

    Returns:
        GeneratedWorksheet with problems, metadata, and answer key
    """
    if config is None:
        config = WorksheetConfig()

    level = config.difficulty_level if config.difficulty_level else get_age_anchor_level(config.age_group)

    # 整单情境化：抽一个主情境 + 固定角色，所有题共享同一故事线
    scen = pick_scenario(random)
    problems = _generate_worksheet_problems(config, level, scen["mascot_name"])

    # Generate instructions
    instructions = _generate_instructions(config.age_group)

    # Build answer key
    answer_key = {p.number: p.correct_answer for p in problems}

    # Build title
    dim_names = {
        "counting": "数数练习", "addition_sub": "加减练习",
        "shapes_space": "图形练习", "patterns": "规律练习",
    }
    title_parts = [dim_names.get(d, d) for d in config.dimensions]
    title = f"{'、'.join(title_parts)} — {config.child_name}"

    # Auto-generate learning objective if not provided
    learning_obj = config.learning_objective or _auto_learning_objective(
        config.dimensions, config.age_group, config.difficulty_level
    )

    # B6: build the "针对上次薄弱" note from child memory
    memory_note = _build_memory_note(child_memory, config.dimensions)

    return GeneratedWorksheet(
        title=title,
        child_name=config.child_name,
        date="____年____月____日",
        age_group=config.age_group,
        difficulty_level=level,
        problems=problems,
        instructions=instructions,
        answer_key=answer_key,
        config=config,
        total_possible=len(problems),
        learning_objective=learning_obj,
        memory_note=memory_note,
        story_title=scen["title"],
        scene_intro=scen["intro"],
        mascot_name=scen["mascot_name"],
        generation_mode="template",
    )


def _build_memory_note(child_memory: Optional[Dict[str, Any]], selected_dims: List[str]) -> str:
    """Build the '📌 针对上次薄弱' line shown on the assessment-target card."""
    if not child_memory or not child_memory.get("has_memory"):
        return ""
    weak = child_memory.get("weak_dimensions") or []
    if not weak:
        return ""
    # Only mention weak dims actually targeted by this worksheet
    targeted = [w for w in weak if w.get("dimension") in selected_dims]
    if not targeted:
        targeted = weak[:1]
    parts = []
    for w in targeted[:2]:
        name = get_dimension_display_name(w.get("dimension", ""))
        score = w.get("latest_score")
        score_str = f"（上次 {score:.0f}%）" if score is not None else ""
        parts.append(f"「{name}」{score_str}")
    return "📌 本单针对上次薄弱：" + "、".join(parts)


def _generate_worksheet_problems(
    config: WorksheetConfig, level: int, mascot_name: str = ""
) -> List[WorksheetProblem]:
    """Generate the problem list for a worksheet."""
    problems = []
    dimensions = config.dimensions
    count = config.problem_count

    # Distribute problems across dimensions
    per_dim = max(1, count // len(dimensions))
    remainder = count - per_dim * len(dimensions)

    problem_number = 1
    for i, dim in enumerate(dimensions):
        num_for_dim = per_dim + (1 if i < remainder else 0)
        dim_problems = _generate_for_dimension(dim, level, num_for_dim, problem_number, mascot_name)
        problems.extend(dim_problems)
        problem_number += num_for_dim

    return problems


def _generate_for_dimension(
    dimension: str,
    level: int,
    count: int,
    start_number: int,
    mascot_name: str = "",
) -> List[WorksheetProblem]:
    """Generate problems for a single dimension."""
    problems = []
    generators = TEMPLATE_REGISTRY.get(dimension)
    if not generators:
        return problems

    q_types = list(generators.keys())
    # Filter appropriate types for difficulty
    if dimension == "counting":
        if level <= 2:
            q_types = [t for t in q_types if t in ("count_objects", "compare_quantity")]
        elif level <= 3:
            q_types = [t for t in q_types if t not in ("skip_counting",)]
    elif dimension == "addition_sub":
        if level <= 2:
            q_types = ["object_add", "object_sub"]
        elif level <= 3:
            q_types = ["object_add", "object_sub", "symbol_add"]

    for i in range(count):
        q_type = random.choice(q_types)
        generator = generators[q_type]
        try:
            data = generator(level)
        except Exception:
            continue

        workspace = 2
        if q_type in ("word_problem", "pattern_create"):
            workspace = 3
        elif q_type in ("number_composition", "symbol_add", "symbol_sub"):
            workspace = 2

        # 从题型候选操作中选一个（随机），并包上整单故事线的情境
        op_candidates = OPERATION_BY_TYPE.get(q_type, ("圈画", "点数"))
        operation = random.choice(op_candidates)
        scenario = ""
        if mascot_name:
            scenario = f"{mascot_name}请你帮忙完成这个小任务！"
        problem = WorksheetProblem(
            number=start_number + i,
            type=q_type,
            dimension=dimension,
            prompt=data.get("prompt", "请作答"),
            data=data,
            correct_answer=data.get("correct_answer", "（开放题）"),
            workspace_lines=workspace,
            operation=operation,
            scenario=scenario,
        )
        problems.append(problem)

    return problems


def _auto_learning_objective(dimensions: List[str], age_group: str, difficulty: int) -> str:
    """Auto-generate a learning objective based on dimension, age, and difficulty."""
    age_map = {"small": "小班（3-4岁）", "middle": "中班（4-5岁）", "large": "大班（5-6岁）"}
    age_label = age_map.get(age_group, age_group)

    objectives = {
        "counting": {
            1: f"能手口一致地点数3以内的物体",
            2: f"能手口一致地点数5以内的物体，并说出总数",
            3: f"能按数（5以内）取物，比较两组物体的多少",
            4: f"能手口一致地点数10以内的物体",
            5: f"理解10以内序数，感知数的守恒",
        },
        "addition_sub": {
            1: f"借助实物感知3以内数量的增加与减少",
            2: f"借助实物操作进行5以内的加减",
            3: f"借助实物操作进行10以内的加减",
            4: f"能口编简单的加减应用题",
            5: f"能进行10以内加减运算，理解加减互逆关系",
        },
        "shapes_space": {
            1: f"能识别并命名圆形、正方形、三角形",
            2: f"感知图形的多种变式，在拼搭中体会图形的翻转和位置变化",
            3: f"能识别长方形、椭圆形、梯形等图形，关注边角特征",
            4: f"能以自身为中心区分左右，判断远近高低",
            5: f"认识常见立体图形，理解平面与立体的关系",
        },
        "patterns": {
            1: f"能按单一明显特征（颜色、大小）分类",
            2: f"能识别并复制简单AB模式（如红蓝红蓝）",
            3: f"能识别、复制、扩展ABC/AABB模式",
            4: f"能按两个维度分类，按规律排序",
            5: f"能识别和创造复杂模式，实现跨形式转换",
        },
    }

    parts = []
    for dim in dimensions:
        dim_obj = objectives.get(dim, {}).get(difficulty, "")
        if dim_obj:
            parts.append(dim_obj)

    if not parts:
        return f"通过操作练习发展{age_label}幼儿数学核心经验"

    return "；".join(parts)


def _generate_instructions(age_group: str) -> str:
    """Generate age-appropriate instructions for the worksheet."""
    if age_group == "small":
        return (
            "🌟 小朋友，请仔细看每一道题目。\n"
            "数一数、圈一圈、连一连，慢慢做，不着急哦！"
        )
    elif age_group == "middle":
        return (
            "📝 请认真完成每一道题目。\n"
            "先看清题目再作答，做完后检查一遍。加油！"
        )
    else:
        return (
            "📝 请独立完成以下题目。\n"
            "注意书写工整，完成后再仔细检查一遍。\n"
            "如有不会的题目，做好标记，结束后问老师。"
        )


# ─── Printable format helpers ─────────────────────────────────────────

def worksheet_to_markdown(worksheet: GeneratedWorksheet) -> str:
    """Convert a generated worksheet to markdown format for printing."""
    lines = [
        f"# 🧮 {worksheet.title}",
        f"",
        f"**姓名：** {worksheet.child_name}　　　**日期：** {worksheet.date}",
        f"**难度等级：** {'⭐' * worksheet.difficulty_level}",
        f"",
        f"---",
        f"",
    ]
    if worksheet.story_title and worksheet.mascot_name:
        lines += [
            f"### 📖 {worksheet.story_title}",
            f"{worksheet.scene_intro or ''}",
            f"",
            f"---",
            f"",
        ]
    lines += [
        f"### 🎯 考察目标",
        f"{worksheet.learning_objective}",
        f"{worksheet.memory_note}" if worksheet.memory_note else f"",
        f"",
        f"---",
        f"",
        f"### 📋 做题说明",
        f"{worksheet.instructions}",
        f"",
        f"---",
        f"",
    ]

    for p in worksheet.problems:
        op_badge = f" ✏️操作：{p.operation}" if p.operation else ""
        scen_line = f"📍情境：{p.scenario}" if p.scenario else ""
        lines.append(f"### {p.number}. {p.prompt}{op_badge}")
        if scen_line:
            lines.append(f"")
            lines.append(f"{scen_line}")
        lines.append(f"")
        # Add visual elements if available
        data = p.data
        if "items" in data and isinstance(data["items"], list):
            display_items = data["items"][:15]  # Limit for display
            lines.append(f"> {'  '.join(display_items)}")
        elif "group_a" in data and "group_b" in data:
            ga = data["group_a"]
            gb = data["group_b"]
            lines.append(f"> {ga['label']}：{'  '.join([ga['emoji']] * ga['count'])}")
            lines.append(f"> {gb['label']}：{'  '.join([gb['emoji']] * gb['count'])}")
        elif "sequence" in data and isinstance(data["sequence"], list):
            seq_str = "  ".join([str(s) if s else "❓" for s in data["sequence"]])
            lines.append(f"> {seq_str}")
        elif "expression" in data:
            lines.append(f"> {data['expression']}")

        # Workspace lines
        for _ in range(p.workspace_lines):
            lines.append(f"")
        lines.append(f"")

    # 降级/提示说明
    if worksheet.generation_note:
        lines += [f"", f"---", f"", f"> ℹ️ {worksheet.generation_note}", f""]

    # Answer key (separate page)
    if worksheet.config.include_answer_key:
        lines.append(f"---")
        lines.append(f"")
        lines.append(f"## 📝 答案（教师用）")
        lines.append(f"")
        for num, answer in worksheet.answer_key.items():
            lines.append(f"- **第{num}题：** {answer}")

    return "\n".join(lines)


# ─── SVG Cartoon Illustration System ───────────────────────────────────

# Cartoon color palette
_SVG_COLORS = {
    "apple": "#FF6B6B", "banana": "#FFD93D", "orange": "#FF8C42",
    "grape": "#9B59B6", "leaf": "#6BCB77", "blue": "#4D96FF",
    "pink": "#FF85A2", "sky": "#A8D8EA", "brown": "#C49B6C",
}

_SVG_ANIMAL_FACES = {
    0: {"body": "#FF6B6B", "ears": "pointy", "face": "🐱"},
    1: {"body": "#C49B6C", "ears": "floppy", "face": "🐶"},
    2: {"body": "#FFD93D", "ears": "round", "face": "🐰"},
    3: {"body": "#6BCB77", "ears": "small", "face": "🐸"},
    4: {"body": "#FF85A2", "ears": "pointy", "face": "🐭"},
}

_FRUIT_EMOJIS = {"🍎": "apple", "🍊": "orange", "🍌": "banana", "🍇": "grape", "🍓": "strawberry", "🍐": "pear"}

def _cartoon_animal_svg(index: int, size: int = 60) -> str:
    """Single cartoon animal with face."""
    face = _SVG_ANIMAL_FACES.get(index % 5, _SVG_ANIMAL_FACES[0])
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 60 60" xmlns="http://www.w3.org/2000/svg">
      <circle cx="30" cy="32" r="24" fill="{face["body"]}" stroke="#333" stroke-width="1.5"/>
      <circle cx="30" cy="32" r="20" fill="{face["body"]}" opacity="0.3"/>
      <circle cx="20" cy="28" r="3" fill="#333"/><circle cx="40" cy="28" r="3" fill="#333"/>
      <ellipse cx="30" cy="38" rx="5" ry="3" fill="#333"/>
      <text x="30" y="52" text-anchor="middle" font-size="14" fill="#333">😊</text>
    </svg>'''

def _cartoon_fruit_svg(fruit_type: str, size: int = 50) -> str:
    """Single cartoon fruit."""
    color = _SVG_COLORS.get(fruit_type, "#FF6B6B")
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 50 50" xmlns="http://www.w3.org/2000/svg">
      <circle cx="25" cy="28" r="18" fill="{color}" stroke="#333" stroke-width="1.5"/>
      <ellipse cx="25" cy="28" rx="14" ry="16" fill="{color}" opacity="0.3"/>
      <line x1="25" y1="10" x2="25" y2="16" stroke="#6BCB77" stroke-width="3" stroke-linecap="round"/>
      <ellipse cx="21" cy="6" rx="6" ry="4" fill="#6BCB77" transform="rotate(-20 21 6)"/>
      <circle cx="20" cy="26" r="2" fill="rgba(255,255,255,0.4)"/>
    </svg>'''

def _cartoon_shape_svg(shape_name: str, size: int = 80) -> str:
    """Cartoon geometric shape with face and color."""
    shapes_map = {
        "圆形": '<circle cx="40" cy="40" r="30" fill="#4D96FF" stroke="#333" stroke-width="2"/>',
        "正方形": '<rect x="10" y="10" width="60" height="60" rx="6" fill="#FF8C42" stroke="#333" stroke-width="2"/>',
        "三角形": '<polygon points="40,5 75,70 5,70" fill="#6BCB77" stroke="#333" stroke-width="2"/>',
        "长方形": '<rect x="5" y="18" width="70" height="44" rx="6" fill="#9B59B6" stroke="#333" stroke-width="2"/>',
        "椭圆形": '<ellipse cx="40" cy="40" rx="32" ry="22" fill="#FF85A2" stroke="#333" stroke-width="2"/>',
        "梯形": '<polygon points="15,25 65,25 75,55 5,55" fill="#FFD93D" stroke="#333" stroke-width="2"/>',
        "半圆形": '<path d="M10,65 A30,25 0 0,1 70,65 Z" fill="#A8D8EA" stroke="#333" stroke-width="2"/>',
        "星形": '<polygon points="40,5 48,30 75,30 53,45 61,70 40,55 19,70 27,45 5,30 32,30" fill="#FFD93D" stroke="#333" stroke-width="2"/>',
    }
    shape_svg = shapes_map.get(shape_name, shapes_map["圆形"])
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 80 80" xmlns="http://www.w3.org/2000/svg">
      {shape_svg}
      <circle cx="32" cy="36" r="4" fill="#333"/><circle cx="48" cy="36" r="4" fill="#333"/>
      <path d="M32,52 Q40,60 48,52" fill="none" stroke="#333" stroke-width="2.5" stroke-linecap="round"/>
    </svg>'''

def _cartoon_bead_svg(color: str, size: int = 44) -> str:
    """Single cartoon bead for pattern sequences."""
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 44 44" xmlns="http://www.w3.org/2000/svg">
      <circle cx="22" cy="22" r="18" fill="{color}" stroke="#333" stroke-width="2"/>
      <circle cx="17" cy="17" r="5" fill="rgba(255,255,255,0.35)"/>
      <circle cx="22" cy="6" r="3" fill="rgba(255,255,255,0.5)"/>
    </svg>'''

def _problem_cartoon_svg(problem, age_group: str) -> str:
    """Generate a cartoon SVG illustration for a single problem.

    Returns an HTML-safe SVG string or empty string if no illustration fits.
    """
    ptype = problem.type
    data = problem.data
    size_scale = {"small": 1.3, "middle": 1.0, "large": 0.8}.get(age_group, 1.0)

    # ── Counting: row of cartoon animals ──
    if ptype == "count_objects" and "items" in data:
        items = data["items"][:12]
        count = len(items)
        animal_size = int(50 * size_scale)
        svg_w = count * animal_size + 20
        animals = ""
        for i in range(count):
            x = 10 + i * animal_size
            animals += f'<g transform="translate({x},5)">{_cartoon_animal_svg(i, animal_size)}</g>'
        return f'<svg width="{svg_w}" height="{animal_size + 10}" viewBox="0 0 {svg_w} {animal_size + 10}" xmlns="http://www.w3.org/2000/svg">{animals}</svg>'

    # ── Compare: two groups of cartoon fruits ──
    if ptype == "compare_quantity" and "group_a" in data:
        ga, gb = data["group_a"], data["group_b"]
        fruit_size = int(44 * size_scale)
        max_count = max(ga["count"], gb["count"])
        svg_w = max_count * fruit_size + 80
        svg_h = fruit_size * 2 + 40

        parts = f'<text x="10" y="22" font-size="16" font-weight="bold" fill="#64748b">{ga["label"]}</text>'
        for i in range(min(ga["count"], 10)):
            parts += f'<g transform="translate({10 + i * fruit_size}, 30)">{_cartoon_fruit_svg("apple", fruit_size)}</g>'

        y2 = fruit_size + 50
        parts += f'<text x="10" y="{y2 + 16}" font-size="16" font-weight="bold" fill="#64748b">{gb["label"]}</text>'
        for i in range(min(gb["count"], 10)):
            parts += f'<g transform="translate({10 + i * fruit_size}, {y2 + 24})">{_cartoon_fruit_svg("orange", fruit_size)}</g>'

        return f'<svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">{parts}</svg>'

    # ── Add/Sub: expression with visual items ──
    if ptype in ("object_add", "object_sub") and "expression" in data:
        expr = data.get("expression", "")
        fruit_size = int(40 * size_scale)
        svg_h = fruit_size + 30
        svg_w = 400
        parts = ""
        # Decorative fruits
        for i in range(3):
            parts += f'<g transform="translate({20 + i * (fruit_size + 10)}, 10)">{_cartoon_fruit_svg("apple", fruit_size)}</g>'
        parts += f'<text x="200" y="{fruit_size // 2 + 10}" text-anchor="middle" font-size="22" font-weight="900" fill="#4D96FF">{expr}</text>'
        for i in range(2):
            parts += f'<g transform="translate({240 + i * (fruit_size + 10)}, 10)">{_cartoon_fruit_svg("banana", fruit_size)}</g>'
        return f'<svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">{parts}</svg>'

    # ── Shape ID: cartoon shape ──
    if ptype == "shape_id":
        shape_name = data.get("shape_name", "圆形")
        shape_size = int(100 * size_scale)
        return _cartoon_shape_svg(shape_name, shape_size)

    # ── Pattern next: bead/block sequence ──
    if ptype == "pattern_next" and "sequence" in data:
        seq = data["sequence"][:10]
        bead_size = int(44 * size_scale)
        color_map = {"红": "#FF6B6B", "蓝": "#4D96FF", "黄": "#FFD93D", "绿": "#6BCB77", "紫": "#9B59B6", "橙": "#FF8C42", "粉": "#FF85A2"}
        svg_w = len(seq) * bead_size + 20
        svg_h = bead_size + 10
        parts = ""
        for i, item in enumerate(seq):
            if item is None:
                parts += f'<g transform="translate({10 + i * bead_size}, 5)"><rect x="0" y="0" width="{bead_size - 4}" height="{bead_size - 4}" rx="10" fill="none" stroke="#FF6B6B" stroke-width="3" stroke-dasharray="6,4"/><text x="{(bead_size - 4) / 2}" y="{(bead_size - 4) / 2 + 5}" text-anchor="middle" font-size="18" fill="#FF6B6B">?</text></g>'
            else:
                color = color_map.get(str(item)[:1], "#FF6B6B")
                parts += f'<g transform="translate({10 + i * bead_size}, 5)">{_cartoon_bead_svg(color, bead_size)}</g>'
        return f'<svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">{parts}</svg>'

    # ── Classify: colored groups ──
    if ptype == "classify":
        group_colors = ["#FF6B6B", "#4D96FF", "#6BCB77", "#FFD93D"]
        bead_s = int(36 * size_scale)
        svg_w = 4 * bead_s + 60
        svg_h = bead_s * 2 + 30
        parts = ""
        for gi, color in enumerate(group_colors):
            for ri in range(3):
                x = 20 + gi * (bead_s + 10)
                y = 10 + ri * (bead_s // 2)
                parts += f'<circle cx="{x + bead_s // 2}" cy="{y + bead_s // 2}" r="{bead_s // 2 - 2}" fill="{color}" stroke="#333" stroke-width="1.5"/>'
        return f'<svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">{parts}</svg>'

    # ── Sort: ordered items ──
    if ptype == "sort":
        sizes = [30, 38, 46, 54, 62]
        svg_w = 5 * 70 + 20
        svg_h = 80
        parts = '<text x="10" y="16" font-size="14" fill="#64748b">从小到大 →</text>'
        for i, s in enumerate(sizes):
            x = 20 + i * 70
            y = 70 - s
            color = ["#FF6B6B", "#FF8C42", "#FFD93D", "#6BCB77", "#4D96FF"][i]
            parts += f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="8" fill="{color}" stroke="#333" stroke-width="2"/>'
        return f'<svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">{parts}</svg>'

    # ── Number composition: visual number split ──
    if ptype == "number_composition" and "expression" in data:
        expr = data.get("expression", "")
        svg_w, svg_h = 220, 100
        parts = ""
        for i in range(3):
            parts += f'<g transform="translate({20 + i * 50}, 50)">{_cartoon_fruit_svg("apple", 36)}</g>'
        parts += f'<text x="110" y="30" text-anchor="middle" font-size="18" font-weight="900" fill="#4D96FF">{expr}</text>'
        for i in range(2):
            parts += f'<g transform="translate({20 + i * 50}, 50)">{_cartoon_fruit_svg("banana", 36)}</g>'
        return f'<svg width="{svg_w}" height="{svg_h}" viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">{parts}</svg>'

    return ""


# ─── Core-experience tagging & mascot (for prominent 考察目标 card) ─────

# Map the generator's problem-type names to PCK sub-dimensions (核心经验).
# These keys are the actual "type" strings emitted by the interactive_content
# templates (count_objects/shape_recognition/pattern_what_next/...), which
# differ from the recognizer's PROBLEM_TYPE_TO_SUB_DIMENSION keys.
_GENERATOR_TYPE_TO_SUB_DIM: Dict[str, str] = {
    # counting
    "count_objects": "counting_accuracy",
    "compare_quantity": "quantity_comparison",
    "ordinal_position": "counting_accuracy",   # 序数：13子维度无专属，归入点数能力
    "number_composition": "number_composition",
    "skip_counting": "counting_accuracy",
    # addition_sub
    "object_add": "concrete_operation",
    "object_sub": "concrete_operation",
    "symbol_add": "symbolic_operation",
    "symbol_sub": "symbolic_operation",
    "word_problem": "symbolic_operation",
    # shapes_space
    "shape_recognition": "shape_recognition",
    "spatial_position": "spatial_awareness",
    "shape_composition": "shape_composition",
    "solid_shape": "solid_recognition",
    # symmetry: 13 子维度无对应项，略去不标
    # patterns
    "classify": "classification",
    "pattern_what_next": "pattern_recognition",
    "pattern_extend": "pattern_extension",
    "pattern_create": "pattern_extension",
    "sort_by_attribute": "sorting",
}


def _core_experience_tags(problems: List[WorksheetProblem]) -> List[Dict[str, str]]:
    """Return unique core-experience tags for the problems on this worksheet.

    Each tag: {dimension, dimension_name, sub_dimension, name} — e.g.
    {dimension: 'shapes_space', dimension_name: '图形与空间',
     sub_dimension: 'shape_recognition', name: '图形识别'}.
    Ordered by first appearance.
    """
    tags: List[Dict[str, str]] = []
    seen = set()
    for p in problems:
        sd = _GENERATOR_TYPE_TO_SUB_DIM.get(p.type)
        if not sd or sd in seen:
            continue
        seen.add(sd)
        dim = SUB_DIMENSION_TO_DIMENSION.get(sd, p.dimension)
        tags.append({
            "dimension": dim,
            "dimension_name": get_dimension_display_name(dim) if dim else "",
            "sub_dimension": sd,
            "name": get_sub_dimension_display_name(sd),
        })
    return tags


def _mascot_svg(size: int = 64) -> str:
    """Cute sprout mascot (萌芽) — a smiling seedling with two leaves."""
    return f'''<svg width="{size}" height="{size}" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
      <circle cx="32" cy="42" r="19" fill="#FFD93D" stroke="#3a3a3a" stroke-width="2"/>
      <circle cx="32" cy="42" r="13" fill="#FFE54C" opacity="0.45"/>
      <circle cx="26" cy="38" r="3.2" fill="#3a3a3a"/><circle cx="38" cy="38" r="3.2" fill="#3a3a3a"/>
      <circle cx="27" cy="37" r="1" fill="white"/><circle cx="39" cy="37" r="1" fill="white"/>
      <path d="M26,47 Q32,53 38,47" fill="none" stroke="#3a3a3a" stroke-width="2.5" stroke-linecap="round"/>
      <circle cx="22" cy="45" r="2.5" fill="#FF85A2" opacity="0.6"/>
      <circle cx="42" cy="45" r="2.5" fill="#FF85A2" opacity="0.6"/>
      <path d="M32,24 Q22,16 14,22 Q20,28 32,24 Z" fill="#6BCB77" stroke="#3a3a3a" stroke-width="1.5"/>
      <path d="M32,24 Q42,16 50,22 Q44,28 32,24 Z" fill="#6BCB77" stroke="#3a3a3a" stroke-width="1.5"/>
      <line x1="32" y1="24" x2="32" y2="30" stroke="#6BCB77" stroke-width="2.2"/>
    </svg>'''


def worksheet_to_html(worksheet: GeneratedWorksheet) -> str:
    """Convert a generated worksheet to cartoon-style printable HTML.

    Age-specific styling:
    - small (3-4): extra large fonts, large emoji, ≤4 problems per "page", dashed borders
    - middle (4-5): large fonts, emoji+text mix, rounded cards
    - large (5-6): standard fonts, cartoony accents, grade-school prep
    """
    age = worksheet.config.age_group
    is_small = age == "small"
    is_middle = age == "middle"
    is_large = age == "large"

    # Age-specific sizes
    if is_small:
        body_font = "20px"
        emoji_size = "48px"
        title_size = "32px"
        prompt_size = "22px"
        card_radius = "var(--kid-radius-xl)"
        bg_color = "#FFF8E7"
    elif is_middle:
        body_font = "18px"
        emoji_size = "36px"
        title_size = "28px"
        prompt_size = "20px"
        card_radius = "var(--kid-radius-lg)"
        bg_color = "#FFF9E6"
    else:
        body_font = "16px"
        emoji_size = "28px"
        title_size = "24px"
        prompt_size = "17px"
        card_radius = "var(--kid-radius-md)"
        bg_color = "#F8FAFC"

    problems_html = ""
    # Core-experience badges for the prominent 考察目标 card
    core_tags = _core_experience_tags(worksheet.problems)
    if core_tags:
        ce_badges_html = "".join(
            f'<span class="ce-badge"><span class="ce-badge-dim">{t["dimension_name"]}</span>'
            f'<span class="ce-badge-sep">·</span>'
            f'<span class="ce-badge-sub">{t["name"]}</span></span>'
            for t in core_tags
        )
        ce_summary = "本单考察核心经验：" + "、".join(
            f'{t["dimension_name"]}·{t["name"]}' for t in core_tags
        )
    else:
        ce_badges_html = ""
        ce_summary = ""

    for p in worksheet.problems:
        data = p.data
        visual_html = ""

        # Generate cartoon SVG illustration (primary visual)
        cartoon_svg = _problem_cartoon_svg(p, age)
        if cartoon_svg:
            visual_html = f'<div class="cartoon-illustration">{cartoon_svg}</div>'

        # Fallback: emoji display if no SVG available
        if not cartoon_svg:
            if "items" in data and isinstance(data["items"], list):
                items = "".join(
                    f'<span class="item-emoji">{item}</span>'
                    for item in data["items"][:12]
                )
                visual_html = f'<div class="visual-items">{items}</div>'
            elif "group_a" in data and "group_b" in data:
                ga = data["group_a"]
                gb = data["group_b"]
                a_emojis = "".join(f'<span class="item-emoji">{ga["emoji"]}</span>' for _ in range(ga["count"]))
                b_emojis = "".join(f'<span class="item-emoji">{gb["emoji"]}</span>' for _ in range(gb["count"]))
                visual_html = (
                    f'<div class="compare-group"><div class="group-label">{ga["label"]}</div>'
                    f'<div class="visual-items">{a_emojis}</div></div>'
                    f'<div class="compare-group"><div class="group-label">{gb["label"]}</div>'
                    f'<div class="visual-items">{b_emojis}</div></div>'
                )
            elif "sequence" in data and isinstance(data["sequence"], list):
                seq = "".join(
                    f'<span class="seq-item">{s if s else "❓"}</span>'
                    for s in data["sequence"][:10]
                )
                visual_html = f'<div class="pattern-sequence">{seq}</div>'
            elif "expression" in data:
                visual_html = f'<div class="expression">{data["expression"]}</div>'

        lines_html = "<br>" * (p.workspace_lines * (2 if is_small else 1))

        # Colorful number badge
        num_colors = ["#FF6B6B", "#4D96FF", "#6BCB77", "#FF8C42", "#9B59B6", "#4ECDC4"]
        num_color = num_colors[(p.number - 1) % len(num_colors)]

        # Single-card mode: larger card with extra padding
        is_single = worksheet.config.problem_count == 1
        card_class = "problem single-card" if is_single else "problem"

        op_badge_html = f'<span class="op-badge">{p.operation}</span>' if p.operation else ""
        scen_html = f'<div class="prob-scenario">{p.scenario}</div>' if p.scenario else ""
        problems_html += f"""
        <div class="{card_class}">
            <div class="problem-header">
                <span class="problem-number" style="background:{num_color}">{p.number}</span>
                <span class="problem-prompt">{p.prompt}</span>
                {op_badge_html}
            </div>
            {scen_html}
            {visual_html}
            <div class="workspace">{lines_html}</div>
        </div>
        """

    answer_html = ""
    if worksheet.config.include_answer_key:
        answer_rows = "".join(
            f"<tr><td>{num}</td><td>{answer}</td></tr>"
            for num, answer in worksheet.answer_key.items()
        )
        answer_html = f"""
        <div class="answer-key page-break">
            <div class="answer-badge">👩‍🏫</div>
            <h2>📝 答案（教师用）</h2>
            <table><thead><tr><th>题号</th><th>答案</th></tr></thead><tbody>{answer_rows}</tbody></table>
            <div class="mascot-footer">🌱 萌芽助手 · 为成长助力</div>
        </div>
        """

    # Age-specific instructions
    small_extra = ""
    if is_small:
        small_extra = '<div class="small-hint">💡 小班小朋友可以用手指点着数哦～</div>'

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>{worksheet.title}</title>
<style>
  :root {{
    --kid-orange: #FF8C42; --kid-blue: #4D96FF; --kid-green: #6BCB77;
    --kid-purple: #9B59B6; --kid-pink: #FF85A2; --kid-yellow: #FFD93D;
    --kid-cream: #FFF8E7; --kid-radius-sm: 12px; --kid-radius-md: 20px;
    --kid-radius-lg: 28px; --kid-radius-xl: 36px;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
    max-width: 800px; margin: 0 auto; padding: 24px 20px;
    font-size: {body_font}; background: {bg_color};
    background-image: radial-gradient(circle at 90% 10%, #FFD93D15 0%, transparent 40%),
                      radial-gradient(circle at 10% 90%, #4D96FF10 0%, transparent 40%);
  }}
  h1 {{
    text-align: center; font-size: {title_size}; color: #FF8C42;
    margin-bottom: 4px; font-weight: 900;
  }}
  .subtitle {{ text-align: center; font-size: 14px; color: #94a3b8; margin-bottom: 16px; }}
  .meta {{
    display: flex; justify-content: center; gap: 20px; margin: 12px 0 20px;
    font-size: 15px; flex-wrap: wrap;
  }}
  .meta span {{
    background: white; padding: 6px 16px; border-radius: 999px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.04); font-weight: 600;
  }}
  .story-intro {{
    background: linear-gradient(135deg, #E3F2FD 0%, #FFF8E7 100%);
    border: 2.5px dashed #4D96FF; border-radius: 20px;
    padding: 14px 20px; margin-bottom: 16px; text-align: center;
  }}
  .story-title {{ font-size: 20px; font-weight: 900; color: #1E3A8A; margin-bottom: 4px; }}
  .story-text {{ font-size: 15px; color: #64748b; }}
  .gen-note {{
    background: #FFF3CD; border: 1.5px dashed #E0A800; border-radius: 12px;
    padding: 8px 14px; margin-bottom: 14px; font-size: 14px; color: #8a6d1a;
  }}
  .op-badge {{
    flex-shrink: 0; align-self: center;
    background: #EEF2FF; color: #4F46E5; font-weight: 700; font-size: 13px;
    border-radius: 999px; padding: 3px 12px; margin-left: 8px;
  }}
  .prob-scenario {{ font-size: 14px; color: #8a6d1a; font-style: italic; margin-bottom: 6px; }}
  .instructions {{
    background: white; border-radius: {card_radius}; padding: 16px 20px;
    margin-bottom: 20px; border: 2px dashed #FFD93D;
    font-size: 16px; color: #64748b; text-align: center;
  }}
  .assessment-target {{
    display: flex; align-items: center; gap: 16px;
    background: linear-gradient(135deg, #FFF8E7 0%, #E8F5E9 100%);
    border: 3px dashed #6BCB77; border-radius: {card_radius};
    padding: 18px 22px; margin-bottom: 18px;
    box-shadow: 0 4px 14px rgba(107,203,119,0.12);
  }}
  .at-mascot {{ flex-shrink: 0; }}
  .at-content {{ flex: 1; min-width: 0; }}
  .at-title {{
    font-size: 20px; font-weight: 900; color: #1B5E20;
    margin-bottom: 8px;
  }}
  .at-badges {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 10px; }}
  .ce-badge {{
    display: inline-flex; align-items: center; gap: 4px;
    background: white; border: 2px solid #6BCB77;
    border-radius: 999px; padding: 4px 14px;
    font-size: 15px; box-shadow: 0 2px 6px rgba(0,0,0,0.05);
  }}
  .ce-badge-dim {{ color: #4D96FF; font-weight: 800; }}
  .ce-badge-sep {{ color: #94a3b8; }}
  .ce-badge-sub {{ color: #2E7D32; font-weight: 700; }}
  .at-objective {{
    font-size: 17px; color: #334155; font-weight: 600;
    line-height: 1.6; margin-bottom: 6px;
  }}
  .at-memory {{
    font-size: 14px; color: #C62828; font-weight: 700;
    background: #FFEBEE; border: 2px solid #EF9A9A;
    border-radius: 10px; padding: 6px 12px; margin: 8px 0;
    display: inline-block;
  }}
  .at-summary {{ font-size: 13px; color: #64748b; }}
  .reward-row {{
    display: flex; align-items: center; justify-content: center; gap: 14px;
    background: #FFF3CD; border: 2.5px dashed #FFD93D;
    border-radius: 999px; padding: 14px 24px; margin: 24px auto 8px;
    max-width: 560px; flex-wrap: wrap; text-align: center;
  }}
  .reward-label {{ font-size: 20px; font-weight: 900; color: #B8860B; }}
  .reward-stars {{ font-size: 30px; color: #FFD93D; letter-spacing: 8px; }}
  .reward-hint {{ font-size: 13px; color: #94a3b8; }}
  .small-hint {{
    background: #FF85A210; border-radius: 20px; padding: 10px 20px;
    margin-bottom: 16px; text-align: center; font-size: 18px; color: #FF85A2;
    border: 2px dashed #FF85A230;
  }}
  .problem {{
    margin: 18px 0; padding: 20px 24px;
    background: white; border-radius: {card_radius};
    border: 2.5px solid #e2e8f0;
    box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    transition: transform 0.2s;
  }}
  .problem:hover {{ transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.06); }}
  .single-card {{
    max-width: 650px; margin: 20px auto; padding: 32px 28px;
    border-width: 3px; border-color: #FFD93D;
    background: linear-gradient(135deg, #FFFDF5 0%, #FFF8E7 100%);
  }}
  .single-card .problem-prompt {{ font-size: {'26px' if is_small else '24px' if is_middle else '20px'}; }}
  .single-card .workspace {{ min-height: {'120px' if is_small else '90px'}; }}
  .problem-header {{ display: flex; align-items: flex-start; gap: 12px; margin-bottom: 14px; }}
  .problem-number {{
    display: inline-flex; align-items: center; justify-content: center;
    width: 36px; height: 36px; min-width: 36px;
    border-radius: 50%; color: white; font-weight: 900;
    font-size: 18px; box-shadow: 0 3px 8px rgba(0,0,0,0.12);
  }}
  .problem-prompt {{ font-size: {prompt_size}; color: #334155; font-weight: 700; padding-top: 6px; }}
  .visual-items {{ font-size: {emoji_size}; line-height: 1.6; margin: 8px 0; display: flex; flex-wrap: wrap; gap: 6px; }}
  .item-emoji {{ display: inline-block; transition: transform 0.2s; }}
  .item-emoji:hover {{ transform: scale(1.2); }}
  .compare-group {{ margin: 6px 0; }}
  .group-label {{ font-size: 16px; font-weight: 700; color: #64748b; margin-bottom: 4px; }}
  .pattern-sequence {{ font-size: {emoji_size}; display: flex; flex-wrap: wrap; gap: 6px; }}
  .seq-item {{
    padding: 6px 14px; border: 2px dashed #cbd5e1; border-radius: 12px;
    background: #f8fafc; font-weight: 700;
  }}
  .expression {{
    font-size: 28px; text-align: center; margin: 12px 0;
    color: #4D96FF; font-weight: 900;
    background: #4D96FF08; border-radius: 16px; padding: 12px;
  }}
  .workspace {{ min-height: {'80px' if is_small else '50px'}; }}
  .cartoon-illustration {{
    display: flex; justify-content: center; align-items: center;
    margin: 16px 0; padding: 12px;
    background: #FFFAF0; border-radius: 20px;
    border: 2px dashed #FFD93D;
    overflow-x: auto;
  }}
  .cartoon-illustration svg {{ max-width: 100%; height: auto; }}
  .page-break {{ page-break-before: always; margin-top: 40px; }}
  .answer-key h2 {{ text-align: center; color: #6BCB77; font-size: 22px; margin-bottom: 16px; }}
  .answer-key table {{ width: 100%; border-collapse: collapse; border-radius: 16px; overflow: hidden; }}
  .answer-key td, .answer-key th {{
    border: 1px solid #e2e8f0; padding: 10px 16px; text-align: center; font-size: 16px;
  }}
  .answer-key th {{ background: #6BCB77; color: white; font-weight: 700; }}
  .answer-key td {{ background: white; }}
  .answer-badge {{ text-align: center; font-size: 48px; margin-bottom: 8px; }}
  .mascot-footer {{ text-align: center; font-size: 13px; color: #94a3b8; margin-top: 24px; padding-top: 16px; border-top: 1px solid #e2e8f0; }}
  .difficulty-stars {{ color: #FFD93D; font-size: 18px; }}
  @media print {{
    body {{ background: white; padding: 10px; font-size: {'18px' if is_small else '15px'}; }}
    .problem {{ break-inside: avoid; box-shadow: none; border-color: #ddd; }}
    .problem-number {{ box-shadow: none; }}
  }}
</style>
</head>
<body>
  <h1>🧮 {worksheet.title}</h1>
  <div class="subtitle">🌱 萌芽助手 · 幼儿数学练习操作单</div>
  <div class="meta">
    <span>👶 {worksheet.child_name}</span>
    <span>📅 {worksheet.date}</span>
    <span class="difficulty-stars">{'⭐' * worksheet.difficulty_level}</span>
    <span>{
      '🌱 小班' if is_small else '🌿 中班' if is_middle else '🌳 大班'
    }</span>
  </div>
  {f'''
  <div class="story-intro">
    <div class="story-title">📖 {worksheet.story_title}</div>
    <div class="story-text">{worksheet.scene_intro}</div>
  </div>
  ''' if worksheet.story_title else ''}
  {f'<div class="gen-note">ℹ️ {worksheet.generation_note}</div>' if worksheet.generation_note else ''}
  <div class="assessment-target">
    <div class="at-mascot">{_mascot_svg(72)}</div>
    <div class="at-content">
      <div class="at-title">🎯 考察目标</div>
      {ce_badges_html and f'<div class="at-badges">{ce_badges_html}</div>'}
      <div class="at-objective">{worksheet.learning_objective}</div>
      {worksheet.memory_note and f'<div class="at-memory">{worksheet.memory_note}</div>'}
      {ce_summary and f'<div class="at-summary">{ce_summary}</div>'}
    </div>
  </div>
  <div class="instructions">{worksheet.instructions.replace(chr(10), '<br>')}</div>
  {small_extra}
  {problems_html}
  {answer_html}
  <div class="reward-row">
    <span class="reward-label">🏅 完成奖励</span>
    <span class="reward-stars">☆ ☆ ☆</span>
    <span class="reward-hint">（做完请老师/家长涂色奖励星星）</span>
  </div>
  <div class="mascot-footer">🌱 萌芽助手 Mathsprout · 陪伴每一次成长</div>
</body>
</html>"""


# ─── PDF Export ──────────────────────────────────────────────────────

def _pdf_clean_text(text: str) -> str:
    """PDF 文本清洗：只保留子集字体有字形的字符（ASCII / CJK / 常用标点 / 白名单符号），
    剥离 emoji 与生僻符号（否则渲染成缺字方块）。"""
    if not text:
        return ""
    keep = set("★☆○●◆◇□■▲△→←↑↓①②③④⑤⑥⑦⑧⑨⑩")
    out = []
    for c in text:
        o = ord(c)
        if o < 0x2000:                      # ASCII 区（含 ×÷ — … 等）
            out.append(c)
        elif c in keep:
            out.append(c)
        elif 0x4E00 <= o <= 0x9FFF:         # CJK 汉字
            out.append(c)
        elif 0x3000 <= o <= 0x303F:         # CJK 标点（，。！？；：、（））
            out.append(c)
        elif 0xFF00 <= o <= 0xFFEF:         # 全角形式（数字/字母）
            out.append(c)
        elif 0x2010 <= o <= 0x2027 or 0x2030 <= o <= 0x205E:
            out.append(c)                   # 通用标点（… 等）
        # 其余（emoji/装饰符号/生僻字）丢弃
    return "".join(out)


def _pdf_font_name():
    """注册并返回 PDF 正文字体名：优先嵌入「霞鹜文楷」子集 TTF（backend/fonts/），
    文件缺失时回退 ReportLab 内置 CID 字体 STSong-Light（不嵌入字形，仅应急）。"""
    import os
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    font_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "fonts",
    )
    font_file = os.path.join(font_dir, "LXGWWenKai-Regular.subset.ttf")
    if os.path.isfile(font_file):
        try:
            pdfmetrics.registerFont(TTFont("LXGWKai", font_file))
            return "LXGWKai"
        except Exception:
            pass  # 注册失败则回退
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    except Exception:
        pass
    return "STSong-Light"



def worksheet_to_pdf(worksheet: "GeneratedWorksheet") -> bytes:
    """Render a generated worksheet to A4 PDF bytes (ReportLab).

    与 worksheet_to_html 同源：标题 / 操作说明 / 每题（题目文本 + 答案）/
    答案区 / 完成奖励区。中文字体优先嵌入「霞鹜文楷」子集 TTF（backend/fonts/，
    已子集化 ~1.8MB，任何设备都能正确显示）；字体文件缺失时回退内置
    STSong-Light（CID 字体不嵌入字形，部分设备可能显示乱码）。
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        Preformatted, KeepTogether,
    )
    import io

    FONT = _pdf_font_name()

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=16 * mm, rightMargin=16 * mm,
        topMargin=14 * mm, bottomMargin=14 * mm,
        title=worksheet.child_name + " 数学操作单",
        author="萌芽助手 Mathsprout",
    )

    s_title = ParagraphStyle("t", fontName=FONT, fontSize=22, leading=28,
                             alignment=1, spaceAfter=6)
    s_sub = ParagraphStyle("s", fontName=FONT, fontSize=11, leading=16,
                           alignment=1, textColor=colors.HexColor("#666666"),
                           spaceAfter=10)
    s_inst = ParagraphStyle("i", fontName=FONT, fontSize=12, leading=18,
                            spaceAfter=14)
    s_problem = ParagraphStyle("p", fontName=FONT, fontSize=13, leading=20,
                               spaceAfter=10)
    s_answer = ParagraphStyle("a", fontName=FONT, fontSize=11, leading=16,
                              textColor=colors.HexColor("#1a6b3c"))
    s_note = ParagraphStyle("n", fontName=FONT, fontSize=11, leading=16,
                            textColor=colors.HexColor("#8a6d1a"))

    story = []
    story.append(Paragraph(_pdf_clean_text(worksheet.title), s_title))
    stars = "★" * worksheet.difficulty_level + "☆" * (5 - worksheet.difficulty_level)
    story.append(Paragraph(
        _pdf_clean_text("幼儿：" + worksheet.child_name + " ｜ 日期：" + worksheet.date +
        " ｜ 难度：" + stars),
        s_sub,
    ))

    # 整单故事线（情境引言）
    if worksheet.story_title and worksheet.mascot_name:
        story.append(Paragraph(
            _pdf_clean_text("📖 " + worksheet.story_title + "：" + (worksheet.scene_intro or "")),
            s_note,
        ))
        story.append(Spacer(1, 4))

    if worksheet.learning_objective:
        story.append(Paragraph(_pdf_clean_text("学习目标：" + worksheet.learning_objective), s_note))
    if worksheet.memory_note:
        story.append(Paragraph(_pdf_clean_text(worksheet.memory_note), s_note))

    story.append(Spacer(1, 4))
    story.append(Paragraph(_pdf_clean_text(worksheet.instructions).replace("\n", "<br/>"), s_inst))
    story.append(Spacer(1, 6))

    # 题目区（每 4 题一组，便于换页）
    group = []
    for i, prob in enumerate(worksheet.problems):
        answer = worksheet.answer_key.get(prob.number, "")
        ans_txt = ""
        if worksheet.config.include_answer_key and answer not in (None, ""):
            ans_txt = "（答案：" + str(answer) + "）"
        emoji = getattr(prob, "emoji", "") or ""
        op_tag = ("[操作：" + prob.operation + "] ") if prob.operation else ""
        scen_tag = ("📌 " + prob.scenario + " ") if prob.scenario else ""
        group.append(Paragraph(
            _pdf_clean_text(str(prob.number) + ". " + op_tag + scen_tag + str(emoji) + " " + str(prob.prompt) + " " + ans_txt),
            s_problem,
        ))
        if len(group) >= 4 or i == len(worksheet.problems) - 1:
            story.append(KeepTogether(group))
            story.append(Spacer(1, 8))
            group = []

    # 降级/提示说明
    if worksheet.generation_note:
        story.append(Spacer(1, 6))
        story.append(Paragraph(_pdf_clean_text("ℹ️ " + worksheet.generation_note), s_note))

    # 答案区
    if worksheet.config.include_answer_key and worksheet.answer_key:
        story.append(Spacer(1, 6))
        story.append(Paragraph(_pdf_clean_text("参考答案"), s_answer))
        # 每条答案一行（Paragraph 自动换行，避免长答案截断）
        for num in sorted(worksheet.answer_key.keys()):
            story.append(Paragraph(
                _pdf_clean_text(str(num) + ". " + str(worksheet.answer_key[num])),
                s_answer,
            ))

    # 完成奖励
    story.append(Spacer(1, 10))
    story.append(Paragraph(_pdf_clean_text("完成奖励：☆ ☆ ☆（做完请老师/家长涂色）"), s_note))

    doc.build(story)
    return buf.getvalue()
