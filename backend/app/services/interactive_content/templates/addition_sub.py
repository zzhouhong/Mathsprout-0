"""
Question templates for addition & subtraction games.

Generates: object_add, object_sub, symbol_add, symbol_sub, word_problem questions.
"""

import random
from typing import Dict, List, Any, Tuple
from ..progressions import NUMBER_RANGES


def _num_range(level: int) -> Dict[str, int]:
    return NUMBER_RANGES.get(level, NUMBER_RANGES[1])


# ─── Object Addition ──────────────────────────────────────────────────

def _random_pair(level: int, max_result: int) -> Tuple[int, int]:
    """Generate two numbers whose sum ≤ max_result."""
    r = _num_range(level)
    a = random.randint(1, max_result - 1)
    b = random.randint(1, max_result - a)
    return a, b


OBJECTS = ["🍎", "🌟", "🐱", "🌸", "🎈", "🍪", "🐰", "🌈", "🐶", "🦋",
           "⚽", "🚗", "🐟", "🎵", "🍕"]


def generate_object_add(level: int) -> Dict[str, Any]:
    """Generate a concrete object addition question."""
    r = _num_range(level)
    a, b = _random_pair(level, r["add_result_max"])

    emoji = random.choice(OBJECTS)
    return {
        "type": "object_add",
        "prompt": f"数一数，一共有多少个{emoji}？",
        "group_a": {"emoji": emoji, "count": a, "label": f"左边有{a}个"},
        "group_b": {"emoji": emoji, "count": b, "label": f"右边有{b}个"},
        "expression": f"{a} + {b}",
        "correct_answer": a + b,
        "options": _gen_opts(a + b, max(1, a + b - 3), a + b + 3),
        "interaction": "drag_count" if level <= 2 else "tap_select",
        "scaffold": "先数左边，再数右边，合起来数" if level <= 2 else "直接心算",
    }


def generate_object_sub(level: int) -> Dict[str, Any]:
    """Generate a concrete object subtraction question."""
    r = _num_range(level)
    total = random.randint(max(3, r["min"] + 2), r["add_result_max"])
    take = random.randint(1, total - 1)

    emoji = random.choice(OBJECTS)
    return {
        "type": "object_sub",
        "prompt": f"原来有{total}个{emoji}，拿走了{take}个，还剩几个？",
        "total": total,
        "take_away": take,
        "expression": f"{total} - {take}",
        "emoji": emoji,
        "correct_answer": total - take,
        "options": _gen_opts(total - take, max(0, total - take - 2), total),
        "interaction": "drag_count" if level <= 2 else "tap_select",
        "scaffold": "用实物演示'拿走'" if level <= 2 else "直接心算",
    }


def generate_symbol_add(level: int) -> Dict[str, Any]:
    """Generate a symbolic addition problem."""
    r = _num_range(level)
    a = random.randint(r["min"], r["add_result_max"] - 1)
    b = random.randint(1, r["add_result_max"] - a)

    return {
        "type": "symbol_add",
        "prompt": f"{a} + {b} = ？",
        "expression": f"{a} + {b}",
        "a": a, "b": b,
        "correct_answer": a + b,
        "options": _gen_opts(a + b, max(0, a + b - 4), a + b + 4),
        "interaction": "number_pad" if level >= 3 else "tap_select",
        "scaffold": "可用手指辅助" if level <= 3 else "心算",
    }


def generate_symbol_sub(level: int) -> Dict[str, Any]:
    """Generate a symbolic subtraction problem."""
    r = _num_range(level)
    a = random.randint(max(3, r["min"] + 2), r["add_result_max"])
    b = random.randint(1, a - 1)

    return {
        "type": "symbol_sub",
        "prompt": f"{a} - {b} = ？",
        "expression": f"{a} - {b}",
        "a": a, "b": b,
        "correct_answer": a - b,
        "options": _gen_opts(a - b, max(0, a - b - 3), a),
        "interaction": "number_pad" if level >= 3 else "tap_select",
        "scaffold": "可用手指辅助" if level <= 3 else "心算",
    }


def generate_word_problem(level: int) -> Dict[str, Any]:
    """Generate a simple word problem."""
    r = _num_range(level)
    is_addition = random.random() > 0.5

    contexts_add = [
        ("树上原来有{a}只小鸟，又飞来了{b}只", "现在树上有几只小鸟？"),
        ("小明有{a}块糖，妈妈又给了他{b}块", "小明现在有几块糖？"),
        ("桌上有{a}本书，老师又放了{b}本", "桌上一共有几本书？"),
        ("花园里有{a}朵花，又开了{b}朵", "花园里一共有几朵花？"),
    ]
    contexts_sub = [
        ("鱼缸里有{a}条鱼，捞走了{b}条", "鱼缸里还剩几条鱼？"),
        ("小红有{a}支蜡笔，用完了{b}支", "小红还剩几支蜡笔？"),
        ("篮子里有{a}个鸡蛋，打破了{b}个", "篮子里还有几个好鸡蛋？"),
        ("操场上有{a}个小朋友，{b}个回家了", "操场上还剩几个小朋友？"),
    ]

    if is_addition:
        a = random.randint(1, r["add_result_max"] - 1)
        b = random.randint(1, r["add_result_max"] - a)
        context, question = random.choice(contexts_add)
        answer = a + b
    else:
        a = random.randint(max(3, r["min"] + 2), r["add_result_max"])
        b = random.randint(1, a - 1)
        context, question = random.choice(contexts_sub)
        answer = a - b

    return {
        "type": "word_problem",
        "prompt": question,
        "context": context.format(a=a, b=b),
        "expression": f"{a} + {b}" if is_addition else f"{a} - {b}",
        "correct_answer": answer,
        "options": _gen_opts(answer, answer - 3, answer + 3),
        "interaction": "number_pad" if level >= 3 else "tap_select",
        "scaffold": "用实物或画图辅助理解" if level <= 3 else "直接列算式",
    }


# ─── Helpers ──────────────────────────────────────────────────────────

def _gen_opts(correct: int, min_val: int, max_val: int) -> List[int]:
    options = {correct}
    for offset in [-2, -1, 1, 2]:
        w = correct + offset
        if w >= 0 and w != correct:
            options.add(w)
    while len(options) < 4:
        w = random.randint(max(0, min_val), max_val)
        if w != correct:
            options.add(w)
    result = list(options)[:4]
    random.shuffle(result)
    return result


# ─── Generator registry ───────────────────────────────────────────────

GENERATORS = {
    "object_add": generate_object_add,
    "object_sub": generate_object_sub,
    "symbol_add": generate_symbol_add,
    "symbol_sub": generate_symbol_sub,
    "word_problem": generate_word_problem,
}
