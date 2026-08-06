"""
Report Generator — Dual-report system (Teacher + Parent versions).

Aligned with:
- 《幼儿园保育教育质量评估指南》: Teacher version focuses on teaching improvement,
  parent version focuses on home-kindergarten collaboration.
- 《学前儿童数学学习与发展核心经验》: Reports reference PCK stages and milestones.

CRITICAL RULES for parent reports:
- NO "分数", "排名", "落后", "成绩" vocabulary
- Use encouraging, growth-focused language
- Frame challenges as "正在学习" (learning in progress)
"""

from typing import Dict, List, Optional
from datetime import datetime
from app.core.prompts.pck_reference import (
    MILESTONES,
    AGE_LEVEL_THRESHOLDS,
    AgeGroup,
    Dimension,
    DevLevel,
    get_level_description,
    get_dimension_display_name,
    get_age_display_name,
)
from app.services.memory_service import build_memory_card, build_comparison_for_dimension


async def generate_teacher_report(
    assessment_result: Dict,
    child_name: str,
    age_group: str,
    worksheet_observations: Optional[Dict] = None,
    child_memory: Optional[Dict] = None,
) -> Dict:
    """
    Generate detailed teacher report focused on teaching reflection and improvement.

    child_memory: optional prior-memory dict (from memory_service). When present,
    the report surfaces a "🧠 我记得这个孩子" card (B6) and per-dimension
    "↻ 对比上次" comparison lines (B8).
    """
    dimensions = assessment_result.get("assessment", [])
    overall = assessment_result.get("overall_summary", "")
    age_display = get_age_display_name(age_group)

    # Build radar chart data
    radar_data = {
        "labels": [get_dimension_display_name(d["dimension"]) for d in dimensions],
        "datasets": [{
            "label": child_name,
            "data": [d["score"] for d in dimensions],
            "fill": True,
            "backgroundColor": "rgba(99, 102, 241, 0.2)",
            "borderColor": "rgba(99, 102, 241, 1)",
            "pointBackgroundColor": [
                "#ef4444" if d["level"] in [DevLevel.L1_SPROUT.value] else
                "#f59e0b" if d["level"] in [DevLevel.L2_GROWING.value] else
                "#10b981" if d["level"] in [DevLevel.L3_PROFICIENT.value] else
                "#6366f1"
                for d in dimensions
            ],
            "pointRadius": 6,
        }],
        "age_expectation": {
            "label": f"{age_display}期望基准",
            # L3 (熟练期) threshold anchored to age group: small=60, middle=70, large=80.
            # Younger kids have a lower bar — the baseline ring moves with age.
            "data": [
                AGE_LEVEL_THRESHOLDS.get(age_group, {}).get("L3", 70)
            ] * len(dimensions),
            "borderColor": "rgba(148, 163, 184, 0.5)",
            "borderDash": [5, 5],
            "pointRadius": 0,
        },
    }

    # PCK analysis
    pck_analysis = _build_pck_analysis(dimensions, age_group)

    # Typical errors diagnosis
    error_diagnosis = _build_error_diagnosis(dimensions)

    # Teaching suggestions organized by PCK chapter
    teaching_suggestions = {}
    for d in dimensions:
        dim_name = get_dimension_display_name(d["dimension"])
        comparison = build_comparison_for_dimension(child_memory, d["dimension"], d)
        # B8: adjust next-stage goal wording if we know prior trajectory
        next_goal = _get_next_stage_goal(d["dimension"], d["level"])
        if comparison and child_memory and child_memory.get("has_memory"):
            prior = child_memory.get("dimensions", {}).get(d["dimension"])
            if prior:
                delta = d.get("score", 0) - prior.get("latest_score", 0)
                if delta > 5 or (set(prior.get("error_patterns", [])) - set(d.get("error_patterns", []))):
                    next_goal = f"已进步，可向下一阶段进阶：{next_goal}"
                elif set(prior.get("error_patterns", [])) & set(d.get("error_patterns", [])):
                    next_goal = f"仍需巩固：{next_goal}"
        teaching_suggestions[dim_name] = {
            "current_stage": d.get("pck_stage", ""),
            "level": f"{d.get('level_emoji', '')} {d.get('level_name', '')}",
            "recommendations": d.get("recommendations", ""),
            "next_stage_goal": next_goal,
            "classroom_activities": _get_classroom_activities(d["dimension"], d["level"]),
            "materials_suggestion": _get_materials_suggestion(d["dimension"]),
            "comparison_to_last": comparison,
        }

    # Core-experience targeting conclusion + support (drives the new top-of-report
    # sections): declares which core experience(s) this worksheet points at and
    # organizes teacher follow-up support around them.
    core_experiences = assessment_result.get("core_experiences") or {}
    core_experience_analysis = _build_core_experience_analysis(core_experiences)
    core_experience_support = _build_core_experience_support(core_experiences)

    # Teaching reflection questions (aligned with 《评估指南》 B8)
    reflection_questions = _generate_reflection_questions(dimensions, age_group)

    # B6: "🧠 我记得这个孩子" card (None on first assessment → frontend hides it)
    child_memory_card = build_memory_card(child_memory, assessment_result)

    return {
        "child_name": child_name,
        "age_group": age_display,
        "generated_at": datetime.now().isoformat(),
        "dimensions": dimensions,
        "dimension_problems": assessment_result.get("dimension_problems", {}),
        "radar_chart_data": radar_data,
        "pck_analysis": pck_analysis,
        "typical_errors_diagnosis": error_diagnosis,
        "teaching_suggestions": teaching_suggestions,
        "core_experience_analysis": core_experience_analysis,
        "core_experience_support": core_experience_support,
        "teaching_reflection_questions": reflection_questions,
        "child_memory_card": child_memory_card,
        "overall_summary": overall,
        "report_type": "teacher",
    }


async def generate_parent_report(
    assessment_result: Dict,
    child_name: str,
    age_group: str,
    child_memory: Optional[Dict] = None,
) -> Dict:
    """
    Generate warm, encouraging parent report.

    CRITICAL: Must use ONLY encouraging, growth-focused language.
    Absolutely NO ranking, scoring, or deficit-based language.
    """
    dimensions = assessment_result.get("assessment", [])
    age_display = get_age_display_name(age_group)

    # B6: parent-friendly memory card (encouraging framing, no scores)
    parent_memory_card = None
    if child_memory and child_memory.get("has_memory"):
        session_count = child_memory.get("session_count", child_memory.get("assessment_count", 0))
        improving_names = [i["display_name"] for i in child_memory.get("improving", [])]
        prior_weak = [w["display_name"] for w in child_memory.get("weak_dimensions", [])]
        # dims that were weak before but improved now → "进步了"
        current_dims = {d["dimension"]: d for d in dimensions}
        progressed = []
        for w in child_memory.get("weak_dimensions", []):
            cur = current_dims.get(w["dimension"])
            if cur and cur.get("score_details", {}).get("total", 0) > 0:
                if cur.get("score", 0) > w.get("latest_score", 0) + 5:
                    progressed.append(w["display_name"])
        summary = f"这是宝宝第 {session_count} 次和萌芽助手见面啦！"
        if progressed:
            summary += f"上次还在努力的「{'、'.join(progressed)}」，这次有明显进步，为宝宝点赞！🌟"
        elif improving_names:
            summary += f"宝宝一直在进步的方面：{'、'.join(improving_names[:2])}。"
        else:
            summary += "宝宝正在稳步发展，继续保持陪伴就好。"
        parent_memory_card = {
            "remembered": True,
            "session_count": session_count,
            "summary": summary,
            "progressed_areas": progressed,
        }

    # Extract strengths (L3/L4) and growing areas (L1/L2)
    strengths = []
    growing_areas = []

    for d in dimensions:
        dim_name = get_dimension_display_name(d["dimension"])
        milestones = MILESTONES.get(age_group, {}).get(d["dimension"], [])

        if d["level"] in [DevLevel.L3_PROFICIENT.value, DevLevel.L4_ADVANCED.value]:
            # Format strengths with concrete examples from milestones
            achieved = milestones[:2] if milestones else ["正在稳定发展"]
            strengths.append({
                "area": dim_name,
                "emoji": d.get("level_emoji", "🌟"),
                "description": f"宝宝已经能{', '.join(achieved)}",
                "parent_observation_tip": _get_parent_observation_tip(d["dimension"], "strength"),
            })
        else:
            # Format growing areas positively — "正在学习" framing
            next_steps = milestones[:2] if milestones else ["持续发展中"]
            growing_areas.append({
                "area": dim_name,
                "emoji": "🌱",
                "description": f"宝宝正在学习{', '.join(next_steps)}，这是{age_display}小朋友的自然成长过程",
                "parent_observation_tip": _get_parent_observation_tip(d["dimension"], "growing"),
            })

    # Generate family activities using common household items
    family_activities = _generate_family_activities(dimensions)

    # Build overall summary (warm, encouraging)
    strengths_text = ""
    if strengths:
        areas = "、".join([s["area"] for s in strengths])
        strengths_text = f"{child_name}在{areas}方面表现出了浓厚的兴趣和良好的发展。"
    else:
        strengths_text = f"{child_name}正在各个数学领域快乐地探索和成长。"

    growing_text = ""
    if growing_areas:
        areas = "、".join([g["area"] for g in growing_areas])
        growing_text = (
            f"在{areas}方面，{child_name}正处于自然的学习过程中。"
            f"对于{age_display}的小朋友来说，这些都是正在发展的能力。"
        )

    overall_summary = (
        f"亲爱的家长，这是一份关于{child_name}（{age_display}）数学学习与发展的观察记录。"
        f"它不是'考试'或'测评'，而是帮助我们发现孩子独特成长轨迹的参考。\n\n"
        f"{strengths_text}\n\n"
        f"{growing_text}\n\n"
        f"每个孩子都有自己独特的成长节奏。数学学习应该像玩游戏一样自然而有趣。"
        f"您可以参考下面的家庭小游戏，用日常生活中的物品和{child_name}一起快乐地探索数学的奥秘。"
    )

    # Learning quality notes (focus on non-cognitive aspects)
    learning_quality_notes = (
        "除了具体的数学能力，我们更关注孩子的学习品质：\n"
        "• 专注力 — 孩子是否能投入地完成活动？\n"
        "• 好奇心 — 孩子是否对数学现象感兴趣？\n"
        "• 坚持性 — 遇到困难时是否愿意再试试？\n"
        "• 自信心 — 孩子是否愿意主动尝试？\n\n"
        "建议您在家中多观察这些品质，它们比'做对多少题'重要得多。"
        "当孩子感受到数学的乐趣而非压力时，学习会自然发生。"
    )

    parent_tips = (
        "💡 给家长的温馨提醒：\n"
        "1. 数学就在生活中 — 购物、做饭、整理玩具时都可以自然地聊数学\n"
        "2. 多问'你是怎么知道的' — 关注思考过程而非答案对错\n"
        "3. 允许犯错 — 错误是孩子理解世界的重要方式\n"
        "4. 玩中学 — 游戏是最好的学习方式，不用刻意'教'\n"
        "5. 保持耐心 — 每个孩子发展节奏不同，无需与其他孩子比较"
    )

    return {
        "child_name": child_name,
        "age_group": age_display,
        "generated_at": datetime.now().isoformat(),
        "overall_summary": overall_summary,
        "strengths": strengths,
        "growing_areas": growing_areas,
        "family_activities": family_activities,
        "learning_quality_notes": learning_quality_notes,
        "parent_tips": parent_tips,
        "parent_memory_card": parent_memory_card,
        "report_type": "parent",
    }


# ─── Helper Functions ────────────────────────────────────────────────

def _build_core_experience_analysis(core_experiences: Dict) -> Dict:
    """
    Build the "核心经验定位" conclusion block for the teacher report.

    Passes through the assessment_engine core_experiences block (learning
    objective + targeted sub-dimensions with level/indicator/why), and adds
    a one-line summary the UI can render as the conclusion sentence.
    """
    targets = core_experiences.get("targets", []) if core_experiences else []
    learning_objective = (core_experiences or {}).get("learning_objective", "")

    if targets:
        # Group target names by dimension for a readable summary
        assessed = [t for t in targets if t.get("source") == "assessed"]
        pointed = [t for t in targets if t.get("source") == "pointed"]
        parts = []
        for t in assessed:
            parts.append(f"{t['dimension_name']}·{t['name']}")
        summary = "本操作单指向核心经验：" + "、".join(parts) if parts else ""
        if pointed:
            pt_names = "、".join(f"{t['name']}" for t in pointed)
            summary += f"（学习目标另指向：{pt_names}，本单未直接测查）"
    else:
        summary = "未能从操作单识别明确的核心经验指向，请教师结合学习目标人工判断。"

    return {
        "learning_objective": learning_objective,
        "targets": targets,
        "summary": summary,
    }


def _build_core_experience_support(core_experiences: Dict) -> Dict:
    """
    Build the "教师后续支持（按核心经验组织）" block.

    For each targeted core experience (assessed + pointed), assemble:
      - strategy: teaching_tips for this sub-dimension × age (from PCK)
      - observation_points: evidence_examples (what to look for)
      - materials: classroom materials for the parent dimension
    """
    targets = core_experiences.get("targets", []) if core_experiences else []
    support = {}
    for t in targets:
        dim = t.get("dimension", "")
        entry = {
            "dimension_name": t.get("dimension_name", ""),
            "source": t.get("source", ""),
            "strategy": t.get("teaching_tips", "") or "参照该核心经验的年龄段教学建议开展活动。",
            "observation_points": t.get("evidence_examples", []) or [],
            "materials": _get_materials_suggestion(dim),
        }
        # Carry level info for assessed targets so the support card can show it
        if t.get("source") == "assessed":
            entry["level"] = t.get("level", "")
            entry["level_name"] = t.get("level_name", "")
            entry["level_emoji"] = t.get("level_emoji", "")
            entry["score"] = t.get("score", 0.0)
        support[t["sub_dimension"]] = entry
    return support


def _build_pck_analysis(dimensions: List[Dict], age_group: str) -> str:
    """Build PCK-stage analysis for each dimension."""
    parts = []
    for d in dimensions:
        dim_name = get_dimension_display_name(d["dimension"])
        milestones = MILESTONES.get(age_group, {}).get(d["dimension"], [])
        expected = milestones[0] if milestones else "持续发展"

        parts.append(
            f"【{dim_name}】得分{d['score']:.0f}%，等级：{d.get('level_emoji', '')}{d.get('level_name', '')}。"
            f"PCK阶段：{d.get('pck_stage', '')}。"
            f"该年龄段核心期望：{expected}。"
            f"{d.get('age_benchmark_comparison', '')}。"
        )

    return "\n\n".join(parts)


def _build_error_diagnosis(dimensions: List[Dict]) -> List[str]:
    """Build list of error diagnoses from assessment."""
    diagnoses = []
    for d in dimensions:
        errors = d.get("error_patterns", [])
        if errors:
            dim_name = get_dimension_display_name(d["dimension"])
            for err in errors:
                diagnoses.append(f"【{dim_name}】{err}")
    return diagnoses or ["未发现明显错误模式"]


def _get_next_stage_goal(dimension: str, current_level: str) -> str:
    """Get next-stage goal based on current PCK level."""
    level_order = {
        DevLevel.L1_SPROUT.value: "建立基础感知和一一对应能力",
        DevLevel.L2_GROWING.value: "从实物操作向半具象符号过渡",
        DevLevel.L3_PROFICIENT.value: "巩固符号表征，向更复杂问题延伸",
        DevLevel.L4_ADVANCED.value: "拓展应用，担任同伴导师",
    }
    return level_order.get(current_level, "持续发展")


def _get_classroom_activities(dimension: str, level: str) -> List[str]:
    """Get classroom activity suggestions."""
    activities = {
        Dimension.COUNTING: [
            "晨间圈数人：每天数一数来了几个小朋友",
            "区角材料点数：请幼儿在收纳玩具时数一数",
            "排队游戏：按人数分组，比比哪组多",
        ],
        Dimension.ADDITION_SUBTRACTION: [
            "故事数学：用绘本中的故事情境编加减题",
            "分餐小帮手：分餐具时自然引入加减",
            "角色扮演超市：用代币进行买卖游戏",
        ],
        Dimension.SHAPES_SPACE: [
            "形状寻宝：在教室中找特定形状的物品",
            "身体方向舞：听指令做动作（举左手、向右转）",
            "积木建筑师：用图形拼搭创作并描述",
        ],
        Dimension.PATTERNS: [
            "串珠模式：提供各色珠子请幼儿创造模式",
            "排队规律：按身高/性别/衣服颜色规律排队",
            "分类收纳官：请幼儿将玩具按不同标准分类",
        ],
    }
    return activities.get(dimension, ["游戏化探索活动"])


def _get_materials_suggestion(dimension: str) -> str:
    """Suggest classroom materials for the dimension."""
    materials = {
        Dimension.COUNTING: "计数棒、数字卡片、点卡、实物计数盒、数字拼图",
        Dimension.ADDITION_SUBTRACTION: "操作板、计数小熊、算珠架、数字天平、应用题图片卡",
        Dimension.SHAPES_SPACE: "几何积木、七巧板、图形拼图、立体积木、沙盘描画",
        Dimension.PATTERNS: "串珠套装、分类盒、排序棒、模式卡片、属性块",
    }
    return materials.get(dimension, "多样化操作材料")


def _generate_reflection_questions(
    dimensions: List[Dict], age_group: str
) -> List[str]:
    """Generate teaching reflection questions aligned with 《评估指南》 B8."""
    base_questions = [
        "本次操作单反映了幼儿怎样的思维过程？是否有预料之外的答案值得深入探究？",
        "幼儿在完成操作单时的状态（独立/伴同/辅助）说明了什么？",
        "本班在哪些数学核心经验上需要更多的区角材料支持？",
    ]

    # Add dimension-specific reflection questions
    for d in dimensions:
        if d["level"] in [DevLevel.L1_SPROUT.value, DevLevel.L2_GROWING.value]:
            dim_name = get_dimension_display_name(d["dimension"])
            base_questions.append(
                f"在'{dim_name}'方面，是否可以设计更多游戏化活动代替纸面操作单？"
            )

    # Add age-specific reflection
    age_reflections = {
        AgeGroup.SMALL: "小班数学学习以感知和操作为主，本次操作单的形式是否适合3-4岁幼儿？",
        AgeGroup.MIDDLE: "中班幼儿正在从动作水平向表象水平过渡，我们的材料是否支持了这个过渡？",
        AgeGroup.LARGE: "大班幼儿即将进入小学，我们的数学活动是否在保护兴趣的同时做好了学习品质的准备？",
    }
    if age_group in age_reflections:
        base_questions.append(age_reflections[age_group])

    return base_questions


def _get_parent_observation_tip(dimension: str, category: str) -> str:
    """Get tips for parents on what to observe at home."""
    tips = {
        Dimension.COUNTING: {
            "strength": "您可以请宝宝当'小小点数员'，在吃饭前数一数筷子，在公园里数一数小花。",
            "growing": "您可以在日常生活中创造点数机会——上下楼梯时数台阶、吃水果时数葡萄，让宝宝在自然情境中感受数量。",
        },
        Dimension.ADDITION_SUBTRACTION: {
            "strength": "您可以和宝宝玩'分糖果'游戏——'你有3颗糖，吃了1颗，还剩几颗？'",
            "growing": "您可以在吃零食时用实物操作——'你有2块饼干，再给你2块，现在一共有几块？'不要让宝宝用符号算，要用实物。",
        },
        Dimension.SHAPES_SPACE: {
            "strength": "您可以和宝宝玩'我是侦察兵'——在家/户外寻找特定的形状，并说出它们的空间位置。",
            "growing": "您可以通过身体游戏帮助宝宝感知空间方位——'举左手''向右转''把玩具放在桌子上面'。",
        },
        Dimension.PATTERNS: {
            "strength": "您可以请宝宝帮忙分类收纳——'帮妈妈把袜子按颜色分开''把玩具按大小排排队'。",
            "growing": "您可以和宝宝玩'穿珠子'或'排排队'游戏，按照红-蓝-红-蓝的规律，或者从大到小的顺序排列。",
        },
    }
    return tips.get(dimension, {}).get(category, "多在生活中观察宝宝的数学行为")


def _generate_family_activities(dimensions: List[Dict]) -> List[Dict]:
    """Generate family-friendly activities using common household items."""
    all_activities = {
        Dimension.COUNTING: [
            {
                "title": "🍽️ 数筷子游戏",
                "materials": "一家人吃饭用的筷子",
                "steps": "吃饭前，请宝宝给每个人发筷子——'爸爸一双、妈妈一双、宝宝一双，一共需要几双？'数一数一共多少人，需要多少根。",
                "why": "在真实的生活情境中，宝宝能更好地理解'数'的实际意义。",
            },
            {
                "title": "🧦 袜子配对",
                "materials": "洗好的袜子",
                "steps": "请宝宝帮忙把袜子一双一双配对，边配边数：'1双、2双、3双……一共几双？'",
                "why": "配对是一一对应的重要练习，也是分类的基础。",
            },
        ],
        Dimension.ADDITION_SUBTRACTION: [
            {
                "title": "🍎 水果加减法",
                "materials": "家里的水果或零食",
                "steps": "洗水果时和宝宝互动：'篮子里有3个苹果，我又放进2个，现在有几个？'吃水果时：'你有5颗葡萄，吃了1颗，还剩几颗？'",
                "why": "用真实的物品操作，而不是抽象的数字符号，这是幼儿学习加减的自然方式。",
            },
        ],
        Dimension.SHAPES_SPACE: [
            {
                "title": "🔍 形状寻宝大冒险",
                "materials": "家中的各种物品",
                "steps": "和宝宝一起在家寻找形状——'找找看，哪些东西是圆圆的？（钟表、盘子、硬币……）哪些是方方的？'然后画下来。",
                "why": "将形状学习与真实物品联系起来，帮助宝宝理解数学在生活中的应用。",
            },
            {
                "title": "🕺 身体方向舞",
                "materials": "音乐",
                "steps": "播放音乐，和宝宝一起做动作：'举起左手！''向右转！''把小手放在头上！'轮流当指令官。",
                "why": "通过身体运动感知空间方位，比纸上练习更有效。",
            },
        ],
        Dimension.PATTERNS: [
            {
                "title": "📿 创意串珠",
                "materials": "绳子+彩珠（或用彩色吸管剪段+鞋带替代）",
                "steps": "和宝宝一起按规律串珠：'红-蓝-红-蓝''大-小-大-小'。然后请宝宝自己创造一种规律。",
                "why": "发现和创造模式是重要的数学思维能力，也是未来代数思维的基础。",
            },
            {
                "title": "🧸 玩具分类收纳",
                "materials": "宝宝的玩具",
                "steps": "请宝宝帮忙把玩具分类收纳：'把所有的小汽车放在这个盒子，积木放在那个盒子。'鼓励宝宝说为什么这样分。",
                "why": "分类是幼儿理解'集合'概念的重要方式，也是逻辑思维的基础。",
            },
        ],
    }

    # Collect relevant activities based on child's growing areas
    selected = []
    for d in dimensions:
        activities = all_activities.get(d["dimension"], [])
        # Include if L1/L2 (growing area) or L3/L4 (strength - still fun)
        selected.extend(activities[:1])  # Pick one per dimension

    # Deduplicate by title
    seen = set()
    unique = []
    for act in selected:
        if act["title"] not in seen:
            seen.add(act["title"])
            unique.append(act)

    return unique[:5]  # Max 5 activities
