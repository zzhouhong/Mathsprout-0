"""
Question templates for counting games.

Generates: count_objects, compare_quantity, ordinal_position,
           number_composition, skip_counting questions.
"""

import random
from typing import Dict, List, Any
from ..progressions import NUMBER_RANGES, DifficultyLevel


def _num_range(level: int) -> Dict[str, int]:
    return NUMBER_RANGES.get(level, NUMBER_RANGES[1])


# ─── Count Objects ────────────────────────────────────────────────────

_COUNT_OBJECTS: Dict[str, List[str]] = {
    1: ["🍎", "🌟", "🌈", "🐱", "🐶", "🌸", "🎈", "🍪", "🐰", "🐟"][:5],
    2: ["🍎", "🌟", "🌈", "🐱", "🐶", "🌸", "🎈", "🍪", "🐰", "🐟"],
    3: ["🍎", "🌟", "🌈", "🐱", "🐶", "🌸", "🎈", "🍪", "🐰", "🐟", "🦋", "🐢", "🎵", "🍕", "🚗"],
    4: ["🍎", "🌟", "🌈", "🐱", "🐶", "🌸", "🎈", "🍪", "🐰", "🐟", "🦋", "🐢", "🎵", "🍕", "🚗", "🐘", "🌻", "⚽", "📚", "🖍️"],
    5: ["🍎", "🌟", "🌈", "🐱", "🐶", "🌸", "🎈", "🍪", "🐰", "🐟", "🦋", "🐢", "🎵", "🍕", "🚗", "🐘", "🌻", "⚽", "📚", "🖍️", "🏀", "🐧", "🎸", "🍩", "✈️"],
}

EMOJI_NAMES: Dict[str, str] = {
    "🍎": "苹果", "🌟": "星星", "🌈": "彩虹", "🐱": "小猫", "🐶": "小狗",
    "🌸": "花朵", "🎈": "气球", "🍪": "饼干", "🐰": "兔子", "🐟": "小鱼",
    "🦋": "蝴蝶", "🐢": "乌龟", "🎵": "音符", "🍕": "披萨", "🚗": "汽车",
    "🐘": "大象", "🌻": "向日葵", "⚽": "足球", "📚": "书本", "🖍️": "蜡笔",
    "🏀": "篮球", "🐧": "企鹅", "🎸": "吉他", "🍩": "甜甜圈", "✈️": "飞机",
}


def generate_count_objects(level: int) -> Dict[str, Any]:
    """Generate a 'count the objects' question."""
    r = _num_range(level)
    count = random.randint(r["min"], r["objects_max"])
    pool = _COUNT_OBJECTS.get(level, _COUNT_OBJECTS[1])
    items = random.choices(pool, k=count)

    # Generate 3 wrong answers
    wrong_answers = set()
    for _ in range(3):
        offset = random.choice([-2, -1, 1, 2])
        wrong = count + offset
        if wrong > 0 and wrong != count:
            wrong_answers.add(wrong)
    wrong_answers = list(wrong_answers)[:3]
    while len(wrong_answers) < 3:
        w = random.randint(max(1, count - 3), count + 3)
        if w != count and w not in wrong_answers:
            wrong_answers.append(w)

    options = [count] + wrong_answers
    random.shuffle(options)

    return {
        "type": "count_objects",
        "prompt": f"数一数，一共有几个{EMOJI_NAMES.get(items[0], '物品')}？",
        "items": items,
        "item_name": EMOJI_NAMES.get(items[0], "物品"),
        "correct_answer": count,
        "options": options,
        "interaction": "tap_count",
        "scaffold": "一一对应点数" if level <= 2 else "目测或点数",
    }


# ─── Compare Quantity ─────────────────────────────────────────────────

def generate_compare_quantity(level: int) -> Dict[str, Any]:
    """Generate a 'which has more/less' question."""
    r = _num_range(level)
    a_count = random.randint(r["min"], r["objects_max"])
    diff = random.randint(1, max(2, r["objects_max"] // 3))
    b_count = a_count + diff if random.random() > 0.5 else max(1, a_count - diff)
    if b_count == a_count:
        b_count = a_count + 1

    compare_type = random.choice(["more", "less"])
    question_map = {"more": "多", "less": "少"}
    correct = "A" if (
        (compare_type == "more" and a_count > b_count) or
        (compare_type == "less" and a_count < b_count)
    ) else "B"

    emoji_a = random.choice(["🌟", "🍎", "🌸", "🐱", "🎈"])
    emoji_b = random.choice(["🌈", "🍪", "🐶", "🦋", "⚽"])
    while emoji_b == emoji_a:
        emoji_b = random.choice(["🌈", "🍪", "🐶", "🦋", "⚽"])

    return {
        "type": "compare_quantity",
        "prompt": f"哪一组更{question_map[compare_type]}？",
        "group_a": {"emoji": emoji_a, "count": a_count, "label": "A组"},
        "group_b": {"emoji": emoji_b, "count": b_count, "label": "B组"},
        "compare_type": compare_type,
        "correct_answer": correct,
        "options": ["A", "B"],
        "interaction": "tap_select",
        "scaffold": "一一对应比较" if level <= 2 else "目测比较或数数比较",
    }


# ─── Ordinal Position ─────────────────────────────────────────────────

ORDINAL_LABELS = {1: "第1个", 2: "第2个", 3: "第3个", 4: "第4个", 5: "第5个",
                  6: "第6个", 7: "第7个", 8: "第8个", 9: "第9个", 10: "第10个"}


def generate_ordinal_position(level: int) -> Dict[str, Any]:
    """Generate a 'which position' ordinal question."""
    r = _num_range(level)
    count = random.randint(max(3, r["min"] + 2), r["objects_max"])
    target_pos = random.randint(1, count)

    emojis = _COUNT_OBJECTS.get(level, _COUNT_OBJECTS[1])
    items = random.sample(emojis, min(count, len(emojis)))
    if len(items) < count:
        items += random.choices(emojis, k=count - len(items))

    target_emoji = items[target_pos - 1]
    # ensure target is unique
    other_indices = [i for i, e in enumerate(items) if e == target_emoji and i != target_pos - 1]
    if other_indices:
        # replace duplicates
        for idx in other_indices:
            alt = random.choice([e for e in emojis if e != target_emoji])
            items[idx] = alt

    return {
        "type": "ordinal_position",
        "prompt": f"从左边数起，{EMOJI_NAMES.get(target_emoji, '它')}排在第几个？",
        "items": items,
        "target_position": target_pos,
        "correct_answer": target_pos,
        "options": _gen_options(target_pos, 1, count),
        "interaction": "tap_select",
        "scaffold": "从左到右逐一点数" if level <= 3 else "直接判断",
    }


# ─── Number Composition ───────────────────────────────────────────────

def generate_number_composition(level: int) -> Dict[str, Any]:
    """Generate a number decomposition/composition question."""
    r = _num_range(level)
    # Pick a target number to decompose
    total = random.randint(max(3, r["min"] + 1), r["objects_max"])
    part1 = random.randint(1, total - 1)
    part2 = total - part1

    if random.random() > 0.5:
        # Missing part: "5 can be 2 and ?"
        return {
            "type": "number_composition",
            "prompt": f"{total} 可以分成 {part1} 和几？",
            "total": total,
            "given_part": part1,
            "missing_part": part2,
            "correct_answer": part2,
            "options": _gen_options(part2, 1, total),
            "interaction": "number_pad" if level >= 3 else "tap_select",
            "scaffold": "用手指或实物分解" if level <= 3 else "心算",
        }
    else:
        # Missing whole: "2 and 3 make ?"
        return {
            "type": "number_composition",
            "prompt": f"{part1} 和 {part2} 合起来是几？",
            "total": total,
            "given_parts": [part1, part2],
            "missing_whole": total,
            "correct_answer": total,
            "options": _gen_options(total, max(1, total - 2), total + 2),
            "interaction": "number_pad" if level >= 3 else "tap_select",
            "scaffold": "用手指或实物组合" if level <= 3 else "心算",
        }


# ─── Skip Counting ────────────────────────────────────────────────────

SKIP_PATTERNS = {2: "2个2个数", 5: "5个5个数", 10: "10个10个数"}


def generate_skip_counting(level: int) -> Dict[str, Any]:
    """Generate a skip counting pattern question."""
    skip = random.choice([2, 5]) if level < 5 else random.choice([2, 5, 10])
    start = skip * random.randint(0, 3)  # 0, 2, 4, 6 or 0, 5, 10, 15
    length = random.randint(3, 5)
    sequence = [start + i * skip for i in range(length)]
    missing_idx = random.randint(1, length - 2)  # Don't hide first or last

    return {
        "type": "skip_counting",
        "prompt": f"按规律填数（{SKIP_PATTERNS.get(skip, f'{skip}个{skip}个数')}）：",
        "sequence": [n if i != missing_idx else None for i, n in enumerate(sequence)],
        "missing_index": missing_idx,
        "correct_answer": sequence[missing_idx],
        "options": _gen_options(sequence[missing_idx], max(0, sequence[0] - skip), sequence[-1] + skip),
        "interaction": "number_pad",
        "scaffold": SKIP_PATTERNS.get(skip, ""),
    }


# ─── Helpers ──────────────────────────────────────────────────────────

def _gen_options(correct: int, min_val: int, max_val: int) -> List[int]:
    """Generate 4 options including the correct one."""
    options = {correct}
    for _ in range(10):  # try to get 3 distinct wrong answers
        wrong = correct + random.choice([-2, -1, 1, 2])
        if min_val <= wrong <= max_val and wrong != correct:
            options.add(wrong)
        if len(options) >= 4:
            break
    while len(options) < 4:
        w = random.randint(min_val, max_val)
        if w != correct:
            options.add(w)
    result = list(options)[:4]
    random.shuffle(result)
    return result


# ─── Generator registry ───────────────────────────────────────────────

GENERATORS = {
    "count_objects": generate_count_objects,
    "compare_quantity": generate_compare_quantity,
    "ordinal_position": generate_ordinal_position,
    "number_composition": generate_number_composition,
    "skip_counting": generate_skip_counting,
}


def get_question_types_for_level(game_type: str, level: int) -> List[str]:
    """Get available question types for a given game type and difficulty."""
    from .progressions import (
        COUNTING_PROGRESSION, ADDITION_SUB_PROGRESSION,
        SHAPES_SPACE_PROGRESSION, PATTERNS_PROGRESSION,
    )
    mapping = {
        "counting": COUNTING_PROGRESSION,
        "addition_sub": ADDITION_SUB_PROGRESSION,
        "shapes_space": SHAPES_SPACE_PROGRESSION,
        "patterns": PATTERNS_PROGRESSION,
    }
    progression = mapping.get(game_type, {})
    return progression.get(level, progression.get(1, ["count_objects"]))
