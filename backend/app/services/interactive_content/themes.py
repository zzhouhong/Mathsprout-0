"""学前数学能力主题体系（基于 PCK 核心经验，黄瑾框架）。

9 个可生成主题，每个主题 3 个难度阶梯（1基础/2进阶/3挑战）。
教师选题后 AI 按主题严格生成；操作单自动记录留存，供历史查看与难度推进。
（注：幼儿园不涉及加减运算，故不含加减主题。）
"""

from typing import Dict, List

# 主题 key → 元信息
MATH_THEMES: Dict[str, dict] = {
    "count": {
        "label": "数的点数",
        "desc": "手口一致地点数，说出总数",
        "dims": ["counting"],
        "difficulties": {
            1: "3以内点数，对应真实物品",
            2: "5以内点数，说出总数",
            3: "10以内点数，按物取数",
        },
    },
    "sort": {
        "label": "数的排序",
        "desc": "按数量、大小把物品排排队",
        "dims": ["counting", "patterns"],
        "difficulties": {
            1: "3个物品按数量从少到多排序",
            2: "5个物品按数量/大小排序",
            3: "10个物品排序，含两两比较",
        },
    },
    "compare": {
        "label": "数的比较",
        "desc": "比较多和少、一样多",
        "dims": ["counting"],
        "difficulties": {
            1: "两组3以内物品，比较多和少",
            2: "两组5以内物品比较，一样多",
            3: "三组比较，最多/最少",
        },
    },
    "composition": {
        "label": "数的组成与分解",
        "desc": "把数分成几和几，合起来是几",
        "dims": ["counting", "addition_sub"],
        "difficulties": {
            1: "3的组成（1和2）",
            2: "5的组成",
            3: "10以内的分解组合",
        },
    },
    "classify": {
        "label": "分类",
        "desc": "按颜色、形状、大小把物品分一分",
        "dims": ["patterns"],
        "difficulties": {
            1: "按单一特征分类（颜色）",
            2: "按两个特征分类（颜色+大小）",
            3: "按用途/多特征分类",
        },
    },
    "pattern": {
        "label": "规律模式",
        "desc": "发现规律、接着排（红蓝红蓝…）",
        "dims": ["patterns"],
        "difficulties": {
            1: "复制简单AB模式",
            2: "扩展AB/ABB模式",
            3: "ABC模式与自创模式",
        },
    },
    "measure": {
        "label": "测量比较",
        "desc": "比长短、高矮、粗细",
        "dims": ["patterns", "shapes_space"],
        "difficulties": {
            1: "比长短（两根比）",
            2: "比高矮、长短（多根排序）",
            3: "自然测量（用纸条/脚步量）",
        },
    },
    "shape": {
        "label": "图形认知",
        "desc": "认识圆形、三角形、正方形…",
        "dims": ["shapes_space"],
        "difficulties": {
            1: "认识圆形/三角形/正方形",
            2: "认识长方形/梯形/椭圆形",
            3: "图形拼搭与变式",
        },
    },
    "space": {
        "label": "空间方位",
        "desc": "上下、前后、里外、左右",
        "dims": ["shapes_space"],
        "difficulties": {
            1: "上下、里外",
            2: "前后、远近",
            3: "以自身为中心的左右",
        },
    },
}

THEME_KEYS: List[str] = list(MATH_THEMES.keys())

# 操作类型 → 允许的图形 kind（视觉一致性校验用）
# 点数→dots；圈画→dots/shapes；涂色→shapes；描线→path；配对→groups；
# 找一找→shapes；按规律续→pattern
OPERATION_KINDS: Dict[str, tuple] = {
    "点数": ("dots",),
    "圈画": ("dots", "shapes"),
    "涂色": ("shapes",),
    "描线": ("path",),
    "配对": ("groups",),
    "找一找": ("shapes", "dots"),
    "按规律续": ("pattern",),
}

# 当 visual 缺失/不匹配时，按操作类型生成默认图形骨架
DEFAULT_VISUAL_BY_OPERATION: Dict[str, dict] = {
    "点数": {"kind": "dots", "count": 5},
    "圈画": {"kind": "dots", "count": 5},
    "涂色": {"kind": "shapes", "items": ["circle", "triangle", "square", "circle"], "color": "红"},
    "描线": {"kind": "path"},
    "配对": {"kind": "groups", "left": ["apple", "apple", "apple"], "right": ["apple", "apple"]},
    "找一找": {"kind": "shapes", "items": ["circle", "triangle", "square", "circle", "triangle"], "color": "红"},
    "按规律续": {"kind": "pattern", "colors": ["红", "蓝", "红", "蓝", "", ""], "labels": ["", "", "", "", "？", "？"]},
}
