"""
Question templates for shapes & space games.

Generates: shape_recognition, spatial_position, shape_composition,
           solid_shape, symmetry questions.
"""

import random
from typing import Dict, List, Any, Optional
from ..progressions import NUMBER_RANGES


# ─── Shape Data ───────────────────────────────────────────────────────

PLANE_SHAPES = {
    "circle": {"name": "圆形", "emoji": "⭕", "sides": 0, "properties": "圆圆的，没有角"},
    "square": {"name": "正方形", "emoji": "🟦", "sides": 4, "properties": "四条边一样长，四个角都是方方的"},
    "triangle": {"name": "三角形", "emoji": "🔺", "sides": 3, "properties": "三条边，三个角"},
    "rectangle": {"name": "长方形", "emoji": "📄", "sides": 4, "properties": "对边一样长，四个角都是方方的"},
    "oval": {"name": "椭圆形", "emoji": "🥚", "sides": 0, "properties": "像压扁的圆形"},
    "trapezoid": {"name": "梯形", "emoji": "🪜", "sides": 4, "properties": "有一组对边平行"},
    "semicircle": {"name": "半圆形", "emoji": "🌓", "sides": 0, "properties": "圆形的一半"},
}

SOLID_SHAPES = {
    "sphere": {"name": "球体", "emoji": "⚽", "properties": "圆圆的，可以滚"},
    "cube": {"name": "正方体", "emoji": "🎲", "properties": "六个面都是正方形"},
    "cylinder": {"name": "圆柱体", "emoji": "🥫", "properties": "上下两个圆形面"},
    "cuboid": {"name": "长方体", "emoji": "📦", "properties": "六个面都是长方形"},
}

SPATIAL_TERMS = {
    "above": {"name": "上面", "opposite": "下面"},
    "below": {"name": "下面", "opposite": "上面"},
    "left": {"name": "左边", "opposite": "右边"},
    "right": {"name": "右边", "opposite": "左边"},
    "front": {"name": "前面", "opposite": "后面"},
    "behind": {"name": "后面", "opposite": "前面"},
    "inside": {"name": "里面", "opposite": "外面"},
    "outside": {"name": "外面", "opposite": "里面"},
}

SPATIAL_LEVELS = {
    1: ["above", "below", "inside", "outside"],
    2: ["above", "below", "front", "behind", "inside", "outside"],
    3: ["above", "below", "left", "right", "front", "behind", "inside", "outside"],
    4: ["above", "below", "left", "right", "front", "behind", "inside", "outside"],
    5: ["above", "below", "left", "right", "front", "behind", "inside", "outside"],
}

SHAPE_LEVELS = {
    1: ["circle", "square", "triangle"],
    2: ["circle", "square", "triangle", "rectangle", "oval"],
    3: ["circle", "square", "triangle", "rectangle", "oval", "semicircle", "trapezoid"],
    4: ["circle", "square", "triangle", "rectangle", "oval", "semicircle", "trapezoid"],
    5: ["circle", "square", "triangle", "rectangle", "oval", "semicircle", "trapezoid"],
}


def generate_shape_recognition(level: int) -> Dict[str, Any]:
    """Generate a shape recognition question."""
    available = SHAPE_LEVELS.get(level, SHAPE_LEVELS[1])
    correct_key = random.choice(available)
    correct = PLANE_SHAPES[correct_key]

    # Pick 3 wrong shapes
    wrong_keys = [k for k in available if k != correct_key]
    random.shuffle(wrong_keys)
    wrong_keys = wrong_keys[:3]

    options = [
        {"key": correct_key, "name": correct["name"], "emoji": correct["emoji"]}
    ] + [
        {"key": wk, "name": PLANE_SHAPES[wk]["name"], "emoji": PLANE_SHAPES[wk]["emoji"]}
        for wk in wrong_keys
    ]
    random.shuffle(options)

    question_type = random.choice(["name_to_shape", "shape_to_name", "properties"])
    if question_type == "name_to_shape":
        prompt = f"哪个是{correct['name']}？"
    elif question_type == "shape_to_name":
        prompt = f"这个图形叫什么名字？{correct['emoji']}"
    else:
        prompt = f"哪个图形{correct['properties']}？"

    return {
        "type": "shape_recognition",
        "prompt": prompt,
        "question_subtype": question_type,
        "correct_shape_key": correct_key,
        "correct_shape_name": correct["name"],
        "correct_answer": correct["name"] if question_type != "name_to_shape" else correct["name"],
        "options": options,
        "interaction": "tap_select",
        "scaffold": "观察形状特征" if level <= 2 else "",
    }


def generate_spatial_position(level: int) -> Dict[str, Any]:
    """Generate a spatial position question."""
    available = SPATIAL_LEVELS.get(level, SPATIAL_LEVELS[1])
    position_key = random.choice(available)
    position = SPATIAL_TERMS[position_key]

    objects = ["🌟", "🐱", "🍎", "🎈", "🌸", "📦", "⚽", "🐶"]
    target = random.choice(objects)
    reference = random.choice([o for o in objects if o != target])

    return {
        "type": "spatial_position",
        "prompt": f"{target} 在 {reference} 的哪里？",
        "target_emoji": target,
        "reference_emoji": reference,
        "position": position_key,
        "correct_answer": position["name"],
        "options": _spatial_options(position_key, available),
        "interaction": "drag_position",
        "scaffold": f"以{reference}为参照物判断",
    }


def generate_shape_composition(level: int) -> Dict[str, Any]:
    """Generate a shape composition / tangram-style question."""
    target_shapes = {
        "house": {"name": "房子", "pieces": ["square", "triangle"], "count": 2},
        "tree": {"name": "树", "pieces": ["rectangle", "circle", "triangle"], "count": 3},
        "boat": {"name": "小船", "pieces": ["trapezoid", "triangle"], "count": 2},
        "rocket": {"name": "火箭", "pieces": ["rectangle", "triangle", "triangle"], "count": 3},
    }

    target_key = random.choice(list(target_shapes.keys()))
    target = target_shapes[target_key]

    # For level 1-3, ask how many shapes; for 4-5, ask which shapes
    if level <= 3:
        return {
            "type": "shape_composition",
            "prompt": f"这个{target['name']}由几个图形拼成？",
            "target_name": target["name"],
            "pieces": target["pieces"],
            "correct_answer": target["count"],
            "options": [target["count"] + d for d in [-1, 0, 1, 2] if target["count"] + d > 0][:4],
            "interaction": "tap_select",
            "scaffold": "一个一个数图形",
        }
    else:
        available = SHAPE_LEVELS[level]
        correct_piece = random.choice(target["pieces"])
        wrong_shapes = [s for s in available if s != correct_piece][:3]

        return {
            "type": "shape_composition",
            "prompt": f"拼{target['name']}需要用到哪个图形？",
            "target_name": target["name"],
            "pieces": target["pieces"],
            "correct_answer": PLANE_SHAPES[correct_piece]["name"],
            "options": [PLANE_SHAPES[s]["name"] for s in [correct_piece] + wrong_shapes],
            "interaction": "tap_select",
            "scaffold": "",
        }


def generate_solid_shape(level: int) -> Dict[str, Any]:
    """Generate a 3D shape recognition question."""
    solid_keys = list(SOLID_SHAPES.keys())
    correct_key = random.choice(solid_keys)
    correct = SOLID_SHAPES[correct_key]

    wrong_keys = [k for k in solid_keys if k != correct_key]
    options = [{"key": k, "name": SOLID_SHAPES[k]["name"], "emoji": SOLID_SHAPES[k]["emoji"]}
               for k in [correct_key] + random.sample(wrong_keys, min(3, len(wrong_keys)))]
    random.shuffle(options)

    return {
        "type": "solid_shape",
        "prompt": f"以下哪个是{correct['name']}？{correct['properties']}",
        "correct_shape_key": correct_key,
        "correct_answer": correct["name"],
        "options": options,
        "interaction": "tap_select",
        "scaffold": "联系生活中的物品",
    }


def generate_symmetry(level: int) -> Dict[str, Any]:
    """Generate a symmetry question."""
    patterns = ["🌟", "🌸", "🦋", "😊", "🏠", "❤️"]
    pattern = random.choice(patterns)

    return {
        "type": "symmetry",
        "prompt": f"下面哪半和左半拼起来是完整的{pattern}？",
        "emoji": pattern,
        "interaction": "drag_rotate",
        "scaffold": "对折想象",
    }


# ─── Helpers ──────────────────────────────────────────────────────────

def _spatial_options(correct_key: str, available_keys: List[str]) -> List[str]:
    correct_name = SPATIAL_TERMS[correct_key]["name"]
    others = [SPATIAL_TERMS[k]["name"] for k in available_keys if k != correct_key]
    random.shuffle(others)
    options = [correct_name] + others[:3]
    random.shuffle(options)
    return options


# ─── Generator registry ───────────────────────────────────────────────

GENERATORS = {
    "shape_recognition": generate_shape_recognition,
    "spatial_position": generate_spatial_position,
    "shape_composition": generate_shape_composition,
    "solid_shape": generate_solid_shape,
    "symmetry": generate_symmetry,
}
