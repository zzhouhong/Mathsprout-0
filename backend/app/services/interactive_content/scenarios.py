"""整单级情境池 + 题型→操作类型映射。

参考「完整儿童在线」公众号真实操作单设计语言：
- 每张操作单先抽一个整单主情境 + 固定角色（如"小兔的萝卜园"），
  所有题目共享同一条故事线（样例：去郊游/种萝卜/对对碰/送小兔回家）。
- 每题绑定一个孩子能动手的操作类型（涂色/圈画/描线/配对/找一找/按规律续/点数）。
"""

from typing import Dict, List, Tuple

# ─── 操作类型（与渲染层版式能力一一对应，禁止引入无版式的操作） ──────────
SUPPORTED_OPERATIONS = ("涂色", "圈画", "描线", "配对", "找一找", "按规律续", "点数")

# 题型 → 候选操作类型（模板层为每题从候选中随机选一个）
OPERATION_BY_TYPE: Dict[str, Tuple[str, ...]] = {
    # counting
    "count_objects": ("点数", "圈画", "涂色"),
    "compare_quantity": ("圈画", "找一找", "点数"),
    "ordinal_position": ("圈画", "描线", "找一找"),
    "number_composition": ("点数", "涂色", "圈画"),
    "skip_counting": ("描线", "按规律续", "点数"),
    # addition_sub
    "object_add": ("点数", "涂色", "圈画"),
    "object_sub": ("点数", "圈画", "涂色"),
    "symbol_add": ("点数", "涂色"),
    "symbol_sub": ("点数", "圈画"),
    "word_problem": ("找一找", "圈画", "点数"),
    # shapes_space
    "shape_recognition": ("涂色", "找一找", "圈画"),
    "spatial_position": ("描线", "圈画", "找一找"),
    "shape_composition": ("配对", "圈画", "涂色"),
    "solid_shape": ("找一找", "涂色", "配对"),
    "symmetry": ("配对", "描线", "涂色"),
    # patterns
    "classify": ("配对", "圈画", "找一找"),
    "pattern_what_next": ("按规律续", "配对", "找一找"),
    "pattern_extend": ("按规律续", "涂色"),
    "sort_by_attribute": ("描线", "圈画", "配对"),
    "pattern_create": ("涂色", "按规律续"),
}

# ─── 整单主情境池（借鉴真实活动名 + 幼儿园常见主题） ────────────────────
# 每个情境: title（故事标题）/ intro（引言）/ mascot_candidates（可选角色）
WORKSHEET_SCENARIOS: List[Dict[str, object]] = [
    {
        "title": "小兔的萝卜园",
        "intro": "秋天到了，小兔跳跳在萝卜园里收萝卜，要请你来帮忙！",
        "mascot_candidates": ["小兔跳跳", "小兔白白", "萝卜兔"],
    },
    {
        "title": "去郊游",
        "intro": "小动物们一起去郊游，野餐垫上摆满了好吃的，数一数、比一比！",
        "mascot_candidates": ["小熊笨笨", "小猴皮皮", "小鹿朵朵"],
    },
    {
        "title": "对对碰",
        "intro": "生活里很多东西都是好朋友，帮它们找一找配对！",
        "mascot_candidates": ["小猫花花", "小狗旺旺", "小鸭嘎嘎"],
    },
    {
        "title": "送小兔回家",
        "intro": "天快黑了，小兔要沿着小路回家，路上还有很多小任务等着你！",
        "mascot_candidates": ["小兔跳跳", "小兔点点"],
    },
    {
        "title": "种萝卜",
        "intro": "春天是种萝卜的季节，帮小动物们把种子种进土里吧！",
        "mascot_candidates": ["小兔跳跳", "小猪哼哼", "小熊笨笨"],
    },
    {
        "title": "超市购物",
        "intro": "小动物们去超市买东西，货架上的物品可真多，帮忙数一数、分一分！",
        "mascot_candidates": ["小熊笨笨", "小猫花花", "小猴皮皮"],
    },
    {
        "title": "小动物派对",
        "intro": "森林里要开派对啦，小动物们准备了气球、点心和礼物！",
        "mascot_candidates": ["小猴皮皮", "小兔跳跳", "小刺猬果果"],
    },
    {
        "title": "搭积木城堡",
        "intro": "小动物们要用积木搭一座大城堡，各种形状的积木等着你来认一认！",
        "mascot_candidates": ["小熊笨笨", "小猪哼哼"],
    },
    {
        "title": "水果店开张",
        "intro": "水果店开张啦，苹果、香蕉、橘子摆满了货架，来当小小店员吧！",
        "mascot_candidates": ["小猴皮皮", "小猫花花"],
    },
    {
        "title": "图形乐园",
        "intro": "图形乐园里住着圆形、三角形、正方形，它们都等着和你做游戏！",
        "mascot_candidates": ["图形宝宝", "圆滚滚", "方方正"],
    },
]

# 操作 → 一句给孩子的动作描述（渲染/文案用）
OPERATION_VERB: Dict[str, str] = {
    "涂色": "把××涂上颜色",
    "圈画": "用笔圈出××",
    "描线": "沿着虚线描一描",
    "配对": "把××和××连一连",
    "找一找": "找出所有的××",
    "按规律续": "照着规律继续画",
    "点数": "数一数一共有几个",
}


def pick_scenario(random_module) -> Dict[str, object]:
    """整单级抽一个主情境（含角色）。传入 random 模块以便复用/测试。"""
    scen = random_module.choice(WORKSHEET_SCENARIOS)
    mascot = random_module.choice(scen["mascot_candidates"])
    return {"title": scen["title"], "intro": scen["intro"], "mascot_name": mascot}
