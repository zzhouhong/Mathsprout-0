"""
Question templates for patterns games.

Generates: classify, pattern_what_next, pattern_extend,
           sort_by_attribute, pattern_create questions.
"""

import random
from typing import Dict, List, Any, Tuple


# ─── Classification ───────────────────────────────────────────────────

CLASSIFY_ATTRIBUTES = {
    1: ["color"],              # 单一维度：颜色
    2: ["color", "shape"],     # 单一维度
    3: ["color", "shape", "size"],  # 两维度开始引入
    4: ["color", "shape", "size", "function"],
    5: ["color", "shape", "size", "function", "material"],
}

COLORS = [
    {"name": "红色", "emoji": "🔴"},
    {"name": "蓝色", "emoji": "🔵"},
    {"name": "黄色", "emoji": "🟡"},
    {"name": "绿色", "emoji": "🟢"},
]

ITEMS_FOR_CLASSIFY = {
    "color": [
        [{"name": "红苹果", "emoji": "🍎", "attr": "红色"},
         {"name": "蓝气球", "emoji": "🎈", "attr": "蓝色"},
         {"name": "黄星星", "emoji": "🌟", "attr": "黄色"},
         {"name": "红草莓", "emoji": "🍓", "attr": "红色"},
         {"name": "蓝鲸鱼", "emoji": "🐳", "attr": "蓝色"},
         {"name": "黄太阳", "emoji": "☀️", "attr": "黄色"}],
    ],
    "shape": [
        [{"name": "圆形饼干", "emoji": "🍪", "attr": "圆形"},
         {"name": "方形盒子", "emoji": "📦", "attr": "方形"},
         {"name": "三角尺", "emoji": "📐", "attr": "三角形"},
         {"name": "圆形钟", "emoji": "🕐", "attr": "圆形"},
         {"name": "方形书", "emoji": "📖", "attr": "方形"}],
    ],
    "size": [
        [{"name": "大象", "emoji": "🐘", "attr": "大"},
         {"name": "老鼠", "emoji": "🐭", "attr": "小"},
         {"name": "鲸鱼", "emoji": "🐳", "attr": "大"},
         {"name": "蚂蚁", "emoji": "🐜", "attr": "小"}],
    ],
    "function": [
        [{"name": "铅笔", "emoji": "✏️", "attr": "写字"},
         {"name": "橡皮", "emoji": "🧹", "attr": "写字"},
         {"name": "足球", "emoji": "⚽", "attr": "运动"},
         {"name": "跳绳", "emoji": "🪢", "attr": "运动"},
         {"name": "碗", "emoji": "🥣", "attr": "吃饭"}],
    ],
}


def generate_classify(level: int) -> Dict[str, Any]:
    """Generate a classification question."""
    attrs_available = CLASSIFY_ATTRIBUTES.get(level, CLASSIFY_ATTRIBUTES[1])
    attr = random.choice(attrs_available)

    items_pool = ITEMS_FOR_CLASSIFY.get(attr, ITEMS_FOR_CLASSIFY["color"])[0]

    if attr == "color":
        # Pick items with 2 different colors
        red_items = [i for i in items_pool if i["attr"] == "红色"]
        blue_items = [i for i in items_pool if i["attr"] == "蓝色"]
        yellow_items = [i for i in items_pool if i["attr"] == "黄色"]

        group_a = random.sample(red_items, min(2, len(red_items)))
        group_b = random.sample(blue_items, min(2, len(blue_items)))
        odd_one = random.choice(yellow_items)

        all_items = group_a + group_b + [odd_one]
        random.shuffle(all_items)

        return {
            "type": "classify",
            "prompt": f"哪一个和其他的不是同一类？",
            "items": all_items,
            "attribute": "颜色",
            "correct_class": "红色和蓝色",
            "odd_one": odd_one,
            "correct_answer": odd_one["name"],
            "options": [item["name"] for item in all_items],
            "interaction": "tap_select",
            "scaffold": f"观察每个东西的{attr}" if level <= 2 else "想想分类的标准是什么",
        }

    # Generic classification
    return {
        "type": "classify",
        "prompt": f"哪些东西是一类的？（按{attr}分类）",
        "items": random.sample(items_pool, min(len(items_pool), 6)),
        "attribute": attr,
        "interaction": "drag_sort",
        "scaffold": f"想一想：它们有什么共同点？",
    }


# ─── Pattern What's Next ──────────────────────────────────────────────

PATTERN_TYPES = {
    "AB": {"name": "AB模式", "example": ["🔴", "🔵", "🔴", "🔵"], "next": "🔴"},
    "AAB": {"name": "AAB模式", "example": ["🔴", "🔴", "🔵", "🔴", "🔴", "🔵"], "next": "🔴"},
    "ABB": {"name": "ABB模式", "example": ["🔴", "🔵", "🔵", "🔴", "🔵", "🔵"], "next": "🔴"},
    "ABC": {"name": "ABC模式", "example": ["🔴", "🔵", "🟡", "🔴", "🔵", "🟡"], "next": "🔴"},
    "AABB": {"name": "AABB模式", "example": ["🔴", "🔴", "🔵", "🔵", "🔴", "🔴"], "next": "🔵"},
    "ABBA": {"name": "ABBA模式", "example": ["🔴", "🔵", "🔵", "🔴", "🔴", "🔵"], "next": "🔵"},
}

PATTERN_LEVELS = {
    1: ["AB"],
    2: ["AB", "AAB"],
    3: ["AB", "AAB", "ABB", "ABC"],
    4: ["AB", "AAB", "ABB", "ABC", "AABB"],
    5: ["AB", "AAB", "ABB", "ABC", "AABB", "ABBA"],
}


def generate_pattern_what_next(level: int) -> Dict[str, Any]:
    """Generate a 'what comes next in the pattern' question."""
    available = PATTERN_LEVELS.get(level, PATTERN_LEVELS[1])
    ptype_key = random.choice(available)
    ptype = PATTERN_TYPES[ptype_key]

    # Pick emojis for the pattern
    emoji_options = ["🔴", "🔵", "🟡", "🟢", "🟣", "🟠"]
    emojis_used = random.sample(emoji_options, 3)
    emoji_map = {"A": emojis_used[0], "B": emojis_used[1], "C": emojis_used[2]}

    # Generate the actual sequence
    sequence = []
    unit_repeat = 2 if level <= 3 else 3
    for _ in range(unit_repeat):
        for ch in ptype_key:
            sequence.append(emoji_map.get(ch, "?"))

    correct = sequence[0]  # next item = first of the pattern unit
    # Actually, let's compute the correct next item based on the pattern
    unit = list(ptype_key)
    seq_len = len(sequence)
    correct = emoji_map[unit[seq_len % len(unit)]]

    # Show most of the sequence, hiding the last one
    display_seq = sequence[:-1] if len(sequence) > 3 else sequence

    return {
        "type": "pattern_what_next",
        "prompt": f"接下来应该是哪个？",
        "sequence": display_seq,
        "pattern_type": ptype["name"],
        "pattern_key": ptype_key,
        "correct_answer": correct,
        "options": emojis_used[:3] + [random.choice(emoji_options) for _ in range(3 - len(emojis_used))],
        "interaction": "tap_select",
        "scaffold": f"找规律：{'→'.join(display_seq)}→？" if level <= 2 else "观察重复的单元",
    }


# ─── Pattern Extend ───────────────────────────────────────────────────

def generate_pattern_extend(level: int) -> Dict[str, Any]:
    """Generate a pattern extension question (fill in the blanks)."""
    available = PATTERN_LEVELS.get(level, PATTERN_LEVELS[1])
    ptype_key = random.choice([p for p in available if len(p) >= 2])
    ptype = PATTERN_TYPES[ptype_key]

    emoji_options = ["🔴", "🔵", "🟡", "🟢", "🟣", "🟠"]
    emojis_used = random.sample(emoji_options, 3)
    emoji_map = {"A": emojis_used[0], "B": emojis_used[1], "C": emojis_used[2]}

    # Build a longer visible sequence with one missing
    unit = list(ptype_key)
    sequence = []
    for _ in range(3):
        for ch in unit:
            sequence.append(emoji_map[ch])

    # Hide one position (not first, not last)
    hide_idx = random.randint(len(unit), len(sequence) - 2)
    correct_emoji = sequence[hide_idx]
    display_seq = [e if i != hide_idx else "❓" for i, e in enumerate(sequence)]

    return {
        "type": "pattern_extend",
        "prompt": f"❓ 处应该是什么？",
        "sequence": display_seq,
        "missing_index": hide_idx,
        "correct_answer": correct_emoji,
        "options": emojis_used[:3],
        "interaction": "drag_extend",
        "scaffold": "观察重复出现的规律" if level <= 2 else "找出模式的核心单元",
    }


# ─── Sort By Attribute ────────────────────────────────────────────────

def generate_sort_by_attribute(level: int) -> Dict[str, Any]:
    """Generate a sorting question (order by size/length/etc)."""
    sort_type = random.choice(["size", "length", "quantity"])

    if sort_type == "size":
        items = [
            {"name": "小老鼠", "emoji": "🐭", "rank": 1},
            {"name": "小猫", "emoji": "🐱", "rank": 3},
            {"name": "小兔", "emoji": "🐰", "rank": 2},
            {"name": "小狗", "emoji": "🐶", "rank": 4},
            {"name": "大象", "emoji": "🐘", "rank": 5},
        ]
        prompt = "请把这些动物从小到大排列"
    elif sort_type == "length":
        items = [
            {"name": "短蜡笔", "emoji": "🖍️", "rank": 1},
            {"name": "铅笔", "emoji": "✏️", "rank": 2},
            {"name": "长尺子", "emoji": "📏", "rank": 3},
            {"name": "鱼竿", "emoji": "🎣", "rank": 4},
        ]
        prompt = "请把这些从短到长排列"
    else:
        items = [
            {"name": "1个苹果", "emoji": "🍎", "rank": 1},
            {"name": "2个橙子", "emoji": "🍊🍊", "rank": 2},
            {"name": "3个梨", "emoji": "🍐🍐🍐", "rank": 3},
            {"name": "4个草莓", "emoji": "🍓🍓🍓🍓", "rank": 4},
        ]
        prompt = "请把水果从少到多排列"

    selected = random.sample(items, min(len(items), level + 2))
    random.shuffle(selected)

    return {
        "type": "sort_by_attribute",
        "prompt": prompt,
        "items": selected,
        "sort_type": sort_type,
        "correct_order": sorted(selected, key=lambda x: x["rank"]),
        "correct_answer": [s["name"] for s in sorted(selected, key=lambda x: x["rank"])],
        "interaction": "drag_sort",
        "scaffold": "两两比较" if level <= 2 else "先找最小（最短），再找下一个",
    }


# ─── Pattern Create ───────────────────────────────────────────────────

def generate_pattern_create(level: int) -> Dict[str, Any]:
    """Generate a pattern creation challenge."""
    emoji_options = ["🔴", "🔵", "🟡", "🟢", "🟣"]
    pattern_type = random.choice(["AB", "ABC", "AAB", "ABB"]) if level <= 4 else random.choice(["AB", "ABC", "AAB", "ABB", "AABB", "ABBA"])

    return {
        "type": "pattern_create",
        "prompt": f"用这些颜色创建一个{'简单' if level <= 2 else '有趣'}的规律图案",
        "available_emojis": emoji_options[:2 + (level // 2)],
        "pattern_hint": pattern_type,
        "interaction": "drag_extend",
        "scaffold": "先选两个颜色交替摆" if level <= 2 else "设计自己的模式",
    }


# ─── Generator registry ───────────────────────────────────────────────

GENERATORS = {
    "classify": generate_classify,
    "pattern_what_next": generate_pattern_what_next,
    "pattern_extend": generate_pattern_extend,
    "sort_by_attribute": generate_sort_by_attribute,
    "pattern_create": generate_pattern_create,
}
