"""
Difficulty progression rules for interactive math games.

Each game type has 5 difficulty levels (1→5), mapping to:
- Age-group expectations from PCK framework
- Question complexity and scaffolding
- Number ranges and operation types
"""

from enum import IntEnum
from typing import Dict, List, Optional, Tuple


class DifficultyLevel(IntEnum):
    LEVEL_1 = 1  # 入门 — 实物操作，小数量
    LEVEL_2 = 2  # 基础 — 半具象，中等数量
    LEVEL_3 = 3  # 进阶 — 符号表征，标准数量
    LEVEL_4 = 4  # 挑战 — 抽象思维，大数量
    LEVEL_5 = 5  # 大师 — 灵活应用，综合


# ─── Number ranges per difficulty ────────────────────────────────────

NUMBER_RANGES: Dict[int, Dict[str, Tuple[int, int]]] = {
    1: {"min": 1, "max": 5,   "add_result_max": 5,  "objects_max": 5},
    2: {"min": 1, "max": 10,  "add_result_max": 10, "objects_max": 10},
    3: {"min": 1, "max": 15,  "add_result_max": 10, "objects_max": 15},
    4: {"min": 1, "max": 20,  "add_result_max": 15, "objects_max": 20},
    5: {"min": 1, "max": 30,  "add_result_max": 20, "objects_max": 25},
}

# ─── Per-game-type progression definitions ────────────────────────────

COUNTING_PROGRESSION: Dict[int, List[str]] = {
    1: ["count_objects"],                          # 点数 ≤5 个物体
    2: ["count_objects", "compare_quantity"],      # 点数 ≤10 + 多少比较
    3: ["count_objects", "compare_quantity", "ordinal_position"],  # + 序数
    4: ["count_objects", "number_composition", "ordinal_position", "compare_quantity"],
    5: ["skip_counting", "number_composition", "ordinal_position", "compare_quantity"],
}

ADDITION_SUB_PROGRESSION: Dict[int, List[str]] = {
    1: ["object_add"],                             # 实物加法 ≤5
    2: ["object_add", "object_sub"],               # 实物加减 ≤10
    3: ["object_add", "object_sub", "symbol_add"], # + 符号加法
    4: ["symbol_add", "symbol_sub", "word_problem"],  # 符号加减 + 应用题
    5: ["symbol_add", "symbol_sub", "word_problem"],  # 全部 ≤20
}

SHAPES_SPACE_PROGRESSION: Dict[int, List[str]] = {
    1: ["shape_recognition"],                      # 圆形/正方形/三角形
    2: ["shape_recognition", "spatial_position"],  # + 上下前后
    3: ["shape_recognition", "spatial_position", "shape_composition"],  # + 左右/组合
    4: ["shape_composition", "solid_shape", "spatial_position"],  # 立体/相对方位
    5: ["shape_composition", "solid_shape", "symmetry", "spatial_position"],  # 对称/坐标
}

PATTERNS_PROGRESSION: Dict[int, List[str]] = {
    1: ["classify"],                               # 单一维度分类
    2: ["classify", "pattern_what_next"],          # + AB 模式
    3: ["pattern_what_next", "pattern_extend", "sort_by_attribute"],  # ABC/AABB
    4: ["pattern_extend", "sort_by_attribute", "pattern_create"],  # 复杂模式
    5: ["pattern_create", "pattern_extend", "sort_by_attribute"],  # 多标准
}

# ─── Score threshold to advance difficulty ────────────────────────────

ADVANCE_THRESHOLD: float = 0.75   # 正确率 ≥75% 才升难度
DEMOTE_THRESHOLD: float = 0.40    # 正确率 <40% 降难度

# ─── Question count per session per difficulty ────────────────────────

QUESTIONS_PER_SESSION: Dict[int, int] = {
    1: 5,   # 入门：5题
    2: 6,   # 基础：6题
    3: 8,   # 进阶：8题
    4: 8,   # 挑战：8题
    5: 10,  # 大师：10题
}

# ─── Time limits per question (seconds) ───────────────────────────────

TIME_LIMITS: Dict[int, int] = {
    1: 30,  # 入门：30秒/题
    2: 25,
    3: 20,
    4: 15,
    5: 12,  # 大师：12秒/题
}

# ─── Scoring weights ──────────────────────────────────────────────────

SCORING = {
    "base_correct": 10,          # 基础正确得分
    "speed_bonus_threshold": 3,  # 3秒内答对加速度分
    "speed_bonus": 3,            # 速度加分
    "streak_bonus_threshold": 3, # 连续3题正确开始加分
    "streak_bonus_per": 2,       # 每连续一题额外加2分
    "perfect_bonus": 20,         # 全部正确额外加分
}

# ─── Adaptive difficulty calculation ──────────────────────────────────

def calculate_next_difficulty(
    current_level: int,
    accuracy: float,
    avg_time_seconds: float,
    streak_max: int,
) -> Tuple[int, str]:
    """
    Determine next difficulty level based on performance.

    Returns: (new_level, reason)
    """
    reasons: List[str] = []

    if accuracy >= ADVANCE_THRESHOLD and streak_max >= 3:
        if current_level < 5:
            current_level += 1
            reasons.append(f"正确率{accuracy:.0%}达标")
        else:
            reasons.append("已达最高难度")
    elif accuracy < DEMOTE_THRESHOLD:
        if current_level > 1:
            current_level -= 1
            reasons.append(f"正确率{accuracy:.0%}偏低，降低难度")
        else:
            reasons.append("已是最低难度")

    if avg_time_seconds < 5 and accuracy >= 0.7:
        reasons.append("答题速度优秀")

    return current_level, "；".join(reasons) if reasons else "难度不变"


def get_age_anchor_level(age_group: str) -> int:
    """Map age group to suggested starting difficulty."""
    mapping = {"small": 1, "middle": 2, "large": 3}
    return mapping.get(age_group, 1)
