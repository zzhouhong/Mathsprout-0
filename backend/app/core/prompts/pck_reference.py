"""
PCK (Pedagogical Content Knowledge) Reference Data
Based on《学前儿童数学学习与发展核心经验》(黄瑾、田方, 南京师范大学出版社, 2015)

This module encodes age-specific developmental milestones for each math dimension.
Data is cross-validated between the printed textbook and pck_textbook_extracted.md.

Used by: system prompt builder, assessment engine, report generator.

v2.0 — enriched with full textbook data:
  - Detailed assessment indicators per sub-skill × age group
  - Development stages per dimension (e.g., counting 4-stage model)
  - Comprehensive error pattern catalog (20+ patterns)
  - Cross-dimensional teaching principles
  - PCK stage (concrete → semi-concrete → symbolic) determination
"""

from enum import Enum
from typing import Dict, List, Optional
import re


class AgeGroup(str, Enum):
    SMALL = "small"    # 小班 3-4岁
    MIDDLE = "middle"  # 中班 4-5岁
    LARGE = "large"    # 大班 5-6岁


class Dimension(str, Enum):
    COUNTING = "counting"                  # 数数与数量对应
    ADDITION_SUBTRACTION = "addition_sub"  # 简单加减运算
    SHAPES_SPACE = "shapes_space"          # 图形与空间
    PATTERNS = "patterns"                  # 模式与规律


class PCKStage(str, Enum):
    CONCRETE = "concrete"              # 动作水平（实物操作）
    SEMI_CONCRETE = "semi_concrete"    # 半具象水平（图片/手指/点卡）
    SYMBOLIC = "symbolic"              # 符号水平（数字/算式）


class SubDimension(str, Enum):
    """子维度 — 13个细分能力领域，每个归属一个主维度"""
    # 数概念与运算
    COUNTING_ACCURACY = "counting_accuracy"        # 点数能力
    QUANTITY_COMPARISON = "quantity_comparison"    # 数量比较
    NUMBER_COMPOSITION = "number_composition"      # 数的组成
    CONCRETE_OPERATION = "concrete_operation"      # 实物运算
    SYMBOLIC_OPERATION = "symbolic_operation"      # 符号运算
    # 图形与空间
    SHAPE_RECOGNITION = "shape_recognition"        # 图形识别
    SHAPE_COMPOSITION = "shape_composition"        # 图形组合
    SPATIAL_AWARENESS = "spatial_awareness"        # 空间方位
    SOLID_RECOGNITION = "solid_recognition"        # 立体认知
    # 模式与逻辑
    CLASSIFICATION = "classification"              # 分类能力
    PATTERN_RECOGNITION = "pattern_recognition"    # 模式识别
    PATTERN_EXTENSION = "pattern_extension"        # 模式扩展
    SORTING = "sorting"                            # 排序能力


# 子维度 → 主维度归属
SUB_DIMENSION_TO_DIMENSION: Dict[str, str] = {
    SubDimension.COUNTING_ACCURACY: Dimension.COUNTING,
    SubDimension.QUANTITY_COMPARISON: Dimension.COUNTING,
    SubDimension.NUMBER_COMPOSITION: Dimension.COUNTING,
    SubDimension.CONCRETE_OPERATION: Dimension.ADDITION_SUBTRACTION,
    SubDimension.SYMBOLIC_OPERATION: Dimension.ADDITION_SUBTRACTION,
    SubDimension.SHAPE_RECOGNITION: Dimension.SHAPES_SPACE,
    SubDimension.SHAPE_COMPOSITION: Dimension.SHAPES_SPACE,
    SubDimension.SPATIAL_AWARENESS: Dimension.SHAPES_SPACE,
    SubDimension.SOLID_RECOGNITION: Dimension.SHAPES_SPACE,
    SubDimension.CLASSIFICATION: Dimension.PATTERNS,
    SubDimension.PATTERN_RECOGNITION: Dimension.PATTERNS,
    SubDimension.PATTERN_EXTENSION: Dimension.PATTERNS,
    SubDimension.SORTING: Dimension.PATTERNS,
}


class DevLevel(str, Enum):
    L1_SPROUT = "L1"       # 萌芽期 0-40%
    L2_GROWING = "L2"      # 发展期 41-70%
    L3_PROFICIENT = "L3"   # 熟练期 71-90%
    L4_ADVANCED = "L4"     # 进阶期 91-100%


# ═══════════════════════════════════════════════════════════════════════
# Age-specific developmental milestones
# ═══════════════════════════════════════════════════════════════════════

MILESTONES: Dict[str, Dict[str, List[str]]] = {
    AgeGroup.SMALL: {
        Dimension.COUNTING: [
            "能手口一致地点数5以内物体，说出总数",
            "能按数（5以内）取物",
            "能比较两组物体的'多''少''一样多'",
            "感知'1'和'许多'的概念",
            "能唱数到10（机械记忆，常有跳数/重复）",
            "只能从1开始数，不会从中间任意数起",
        ],
        Dimension.ADDITION_SUBTRACTION: [
            "借助实物操作，感知5以内数量的'增加'与'减少'",
            "能通过一一对应比较'变多了'还是'变少了'",
            "以实物操作为主，处于动作水平",
            "基本不会正式的加减运算",
            "有时能在生活情境中用数数解决小数量问题",
        ],
        Dimension.SHAPES_SPACE: [
            "能识别并命名：圆形、正方形、三角形",
            "能区分平面图形的明显特征（圆圆的、方方的）",
            "理解上下、前后、里外等空间方位",
            "能进行简单的图形匹配（一样的放一起）",
            "对图形感知是整体、笼统和模糊的（圆形叫'太阳'、正方形叫'电视机'）",
            "不能从形状本质特征来认识图形（如'为什么是圆形？'答：'因为它圆圆的'）",
        ],
        Dimension.PATTERNS: [
            "能根据单一明显外部特征分类（颜色、大小、形状）",
            "能识别并复制简单AB模式（如红蓝红蓝）",
            "能将相同物品匹配（配对）",
            "理解'一样'和'不一样'",
            "处于模式识别和复制阶段",
        ],
    },
    AgeGroup.MIDDLE: {
        Dimension.COUNTING: [
            "能手口一致地点数10以内物体，说出总数",
            "能按数（10以内）取物",
            "理解序数（第1、第2…第10）",
            "能比较10以内数量的多少、一样多",
            "理解数的守恒（排列方式变化不影响数量）",
            "末期能通过操作理解数与数关系（'5比4多1'，'2和3合在一起是5'）",
            "此阶段是形成数概念的关键期",
        ],
        Dimension.ADDITION_SUBTRACTION: [
            "借助实物操作进行10以内的加减",
            "能口编简单的应用题",
            "开始用点卡、手指等半具象策略",
            "理解'添上'（加）和'拿走'（减）的实际意义",
            "能进行5以内数的分解与组合",
            "运算方法是逐一计数（点数全部或接着数）",
        ],
        Dimension.SHAPES_SPACE: [
            "能识别并命名：长方形、半圆形、椭圆形、梯形",
            "理解图形的基本特征（边、角数量）",
            "能以自身为中心区分左右",
            "能判断远近、高低、前后等相对空间关系",
            "能用图形拼搭组合图案",
            "4岁是图形知觉的敏感期",
            "开始关注图形组成部分——认识边、角等个别特征",
            "图形守恒：辨认不受颜色、大小及摆放位置的影响",
        ],
        Dimension.PATTERNS: [
            "能按两个维度分类（如红色大的、蓝色小的）",
            "能识别、复制、扩展ABC/AABB模式",
            "能按规律排序（从大到小、从长到短）",
            "理解'类包含'关系（苹果是水果的一种）",
            "处于模式复制和扩展阶段",
        ],
    },
    AgeGroup.LARGE: {
        Dimension.COUNTING: [
            "理解10以内数的组成与分解（如5可以分成2和3）",
            "能进行20以内的点数与唱数，能计数到100甚至以上",
            "理解群数（2个2个数、5个5个数）",
            "理解相邻数关系（n比n-1多1）",
            "能用简单图表记录数量",
            "5岁左右是数概念发展的质的飞跃阶段",
            "能脱离实物进行计数，具有较高水平数抽象能力",
        ],
        Dimension.ADDITION_SUBTRACTION: [
            "能进行10以内的加减运算（符号水平）",
            "理解加减互逆关系（如3+2=5→5-2=3）",
            "能自编和解答简单应用题",
            "开始使用数字符号书写算式",
            "理解'0'在加减中的意义",
            "逐步达到按数群运算的水平",
        ],
        Dimension.SHAPES_SPACE: [
            "认识常见立体图形：球体、圆柱体、正方体、长方体",
            "理解平面图形与立体图形的关系（面在体上）",
            "能以客体为中心区分左右",
            "理解空间方位相对性",
            "能进行图形二等分、四等分",
            "能在网格/坐标中定位（简单地图）",
            "头脑中形成图形的'标准样式'，能识别各种变式",
            "能在一定抽象水平概括图形关系（如将正方形、长方形、梯形概括为'四边形'）",
        ],
        Dimension.PATTERNS: [
            "能按事物内在属性（功能、用途）分类",
            "能识别、复制、扩展、创造复杂模式（AAB、ABB、ABBA）",
            "能发现生活中的规律并用语言描述",
            "理解交集与包含关系（两个集合的交叉）",
            "能按多标准交替排序",
            "能将一种形式的模式转换为另一种形式（如视觉→动作/声音）",
        ],
    },
}


# ═══════════════════════════════════════════════════════════════════════
# Sub-skills per dimension
# ═══════════════════════════════════════════════════════════════════════

SUB_SKILLS: Dict[str, List[str]] = {
    Dimension.COUNTING: [
        "点数准确性", "按数取物", "数量比较", "序数理解",
        "数的组成", "数量守恒", "唱数与群数",
    ],
    Dimension.ADDITION_SUBTRACTION: [
        "实物操作正确率", "符号运算正确率", "策略水平",
        "应用题理解", "运算思维灵活性",
    ],
    Dimension.SHAPES_SPACE: [
        "平面图形识别", "立体图形识别", "图形特征描述",
        "空间方位", "图形组合与分解",
    ],
    Dimension.PATTERNS: [
        "分类能力", "模式识别", "模式扩展", "模式创造",
        "排序能力", "规律语言描述",
    ],
}


# ═══════════════════════════════════════════════════════════════════════
# Problem type → Sub-dimension mapping
# Maps AI-recognized problem types to the 13 sub-dimensions
# ═══════════════════════════════════════════════════════════════════════

PROBLEM_TYPE_TO_SUB_DIMENSION: Dict[str, str] = {
    "counting": SubDimension.COUNTING_ACCURACY,
    "compare": SubDimension.QUANTITY_COMPARISON,
    "number_composition": SubDimension.NUMBER_COMPOSITION,
    "add_10": SubDimension.CONCRETE_OPERATION,
    "sub_10": SubDimension.CONCRETE_OPERATION,
    "symbol_add": SubDimension.SYMBOLIC_OPERATION,
    "symbol_sub": SubDimension.SYMBOLIC_OPERATION,
    "shape_id": SubDimension.SHAPE_RECOGNITION,
    "spatial": SubDimension.SPATIAL_AWARENESS,
    "classify": SubDimension.CLASSIFICATION,
    "pattern_next": SubDimension.PATTERN_RECOGNITION,
    "sort": SubDimension.SORTING,
    "shape_composition": SubDimension.SHAPE_COMPOSITION,
    "solid_shape": SubDimension.SOLID_RECOGNITION,
    "pattern_extend": SubDimension.PATTERN_EXTENSION,
    "word_problem": SubDimension.SYMBOLIC_OPERATION,
}


# ═══════════════════════════════════════════════════════════════════════
# Indicator explanations — "why this matters" for teachers
# Each sub-dimension × age group has: indicator, why_this_matters,
# evidence_examples, and teaching_tips
# ═══════════════════════════════════════════════════════════════════════

INDICATOR_EXPLANATIONS: Dict[str, Dict[str, Dict]] = {
    # ── 点数能力 ──
    SubDimension.COUNTING_ACCURACY: {
        AgeGroup.SMALL: {
            "indicator": "能手口一致地点数5以内的物体，并说出总数",
            "why_this_matters": "这是基数原则建立的关键期。幼儿需要理解'最后一个数代表总数'，而非仅会唱数。手口一致是数概念形成的生理基础。",
            "evidence_examples": [
                "点数时手指与嘴巴同步，不跳数不漏数",
                "点数结束后能准确报出总数（如'一共5个'）",
                "有自我纠正行为（数错后重新数）",
            ],
            "teaching_tips": "提供一一对应的实物操作机会（分发餐具、数玩具），每次点数后追问'一共几个'强化总数概念。",
        },
        AgeGroup.MIDDLE: {
            "indicator": "能手口一致地点数10以内的物体，并说出总数",
            "why_this_matters": "10以内点数稳定是进入运算的基础。此阶段要求从'会数'到'数对'的质的提升，开始建立数序概念。",
            "evidence_examples": [
                "点数10以内物体准确率≥90%",
                "能按数（10以内）取物",
                "开始出现接着数策略（不是每次都从1开始）",
            ],
            "teaching_tips": "在生活情境中渗透计数（数楼梯、数排队人数），鼓励从任意数开始接着数。",
        },
        AgeGroup.LARGE: {
            "indicator": "能目测计数20以内，能唱数到100以上",
            "why_this_matters": "目测计数标志着数感的成熟——不再依赖一一对应点数，能快速感知小数量。群数能力为十进制理解奠基。",
            "evidence_examples": [
                "看到7个物品能直接报出'7个'（不点数）",
                "能2个2个、5个5个地数到100",
                "能从任意数开始接着数",
            ],
            "teaching_tips": "引入群数游戏（2个一组、5个一组），用百数表帮助发现数字规律，为小学做准备。",
        },
    },
    # ── 数量比较 ──
    SubDimension.QUANTITY_COMPARISON: {
        AgeGroup.SMALL: {
            "indicator": "能比较两组物体的'多''少''一样多'",
            "why_this_matters": "数量比较是数感的核心成分——在不需要精确计数的情况下感知量的差异。一一对应是比较的策略基础。",
            "evidence_examples": [
                "两组物体并排时能指出'这排多'",
                "能用一一对应方式验证（每个苹果配一个小朋友）",
                "理解'一样多'的含义",
            ],
            "teaching_tips": "在日常生活中创造比较情境（'谁的饼干多？'），引导一一对应而不是凭感觉判断。",
        },
        AgeGroup.MIDDLE: {
            "indicator": "能比较10以内数量的多少、一样多，开始出现守恒意识",
            "why_this_matters": "数量守恒是皮亚杰理论的里程碑——判断数量不受排列方式影响，标志逻辑思维的萌芽。",
            "evidence_examples": [
                "两组数量相同但排列不同时，仍能判断'一样多'",
                "能用'多几个''少几个'描述比较结果",
                "能按数量排序（从少到多）",
            ],
            "teaching_tips": "用不同排列展示相同数量的物体（排成一排 vs 排成圆圈），引导讨论'为什么还是一样多'。",
        },
        AgeGroup.LARGE: {
            "indicator": "理解相邻数关系（n比n-1多1），完全建立数量守恒",
            "why_this_matters": "相邻数关系的理解标志着数字系统的结构性理解——每个数不是孤立的，而是有前后关系的数序系统。",
            "evidence_examples": [
                "能准确说出'6比5多1''5比6少1'",
                "任何排列变化下都能坚定判断数量不变",
                "能解释为什么数量不变（'没拿走也没加进来'）",
            ],
            "teaching_tips": "用数字线游戏帮助可视化相邻数关系，讨论'变多'和'变少'的生活情境。",
        },
    },
    # ── 数的组成 ──
    SubDimension.NUMBER_COMPOSITION: {
        AgeGroup.SMALL: {
            "indicator": "感知'1'和'许多'的概念",
            "why_this_matters": "这是数组成的萌芽——理解一个整体可以由许多个'1'组成。为后续数的分解组合奠定基础。",
            "evidence_examples": [
                "能分辨'1个'和'许多个'",
                "理解把一个分成很多个（分饼干）",
            ],
            "teaching_tips": "多玩'分与合'的游戏（如把一堆积木分成几份），在生活中体验整体与部分的关系。",
        },
        AgeGroup.MIDDLE: {
            "indicator": "能进行5以内数的分解与组合",
            "why_this_matters": "数的组成是加减运算的逆向思维基础——理解整体可以分成部分，部分合起来就是整体。这是运算理解的真正起点。",
            "evidence_examples": [
                "知道5可以分成2和3、1和4等",
                "能用实物操作演示数的分解与组合",
                "理解'2和3合在一起是5'",
            ],
            "teaching_tips": "利用分合操作板（如有5颗珠子分成两堆有几种分法），鼓励幼儿发现规律。",
        },
        AgeGroup.LARGE: {
            "indicator": "理解10以内数的组成与分解，为进位加法做准备",
            "why_this_matters": "10的组成是十进制系统的核心——理解10是1个十，是小学进位加法和退位减法的关键基础。",
            "evidence_examples": [
                "熟练掌握10的各种组成（1和9、2和8……）",
                "能不借助实物说出数的分解方式",
                "理解'凑十'策略",
            ],
            "teaching_tips": "用十格阵、双色计数器等教具系统学习10的组成，多玩'找朋友凑10'游戏。",
        },
    },
    # ── 实物运算 ──
    SubDimension.CONCRETE_OPERATION: {
        AgeGroup.SMALL: {
            "indicator": "借助实物操作，感知5以内数量的'增加'与'减少'",
            "why_this_matters": "这是运算概念的前身——幼儿不需要知道'+''-'符号，但通过实物操作理解'添上'和'拿走'改变了数量。",
            "evidence_examples": [
                "看到别人加了一个苹果，知道'变多了'",
                "能通过一一对应比较'变多了'还是'变少了'",
                "在游戏情境中正确操作实物加减",
            ],
            "teaching_tips": "在游戏和生活中创设加减情境（'再给你一个'、'吃掉了一个'），强调数量变化而非符号运算。",
        },
        AgeGroup.MIDDLE: {
            "indicator": "借助实物操作进行10以内的加减，用点数全部或接着数策略",
            "why_this_matters": "实物运算是从具体到抽象的桥梁——幼儿需要在大量实物操作中内化'加'和'减'的实际意义。策略从'全部点数'发展到'接着数'是重要的认知进步。",
            "evidence_examples": [
                "能用实物算出3+2=5（摆出3个再摆2个，点数得出5）",
                "开始使用接着数策略（'4个再加2个——5、6'）",
                "能口编简单应用题",
            ],
            "teaching_tips": "遵循'实物→口述→算式'的顺序，不急于引入抽象符号。关注幼儿用的策略而非只看答案对错。",
        },
        AgeGroup.LARGE: {
            "indicator": "脱离实物进行10以内加减，逐步达到按数群运算",
            "why_this_matters": "脱离实物操作标志着运算进入抽象水平。'按群运算'（如知道3+2=5不需要从1数起）意味着建立了稳定的心理数线。",
            "evidence_examples": [
                "不用实物能准确计算10以内加减",
                "使用接着数/倒接数策略（非全部点数）",
                "能自编和解答应用题",
            ],
            "teaching_tips": "逐步撤走实物支持，鼓励心算。引导学生反思策略：'你是怎么算出来的？有没有更快的办法？'",
        },
    },
    # ── 符号运算 ──
    SubDimension.SYMBOLIC_OPERATION: {
        AgeGroup.SMALL: {
            "indicator": "—（此年龄段不适用）",
            "why_this_matters": "小班幼儿处于动作水平，不应引入'+''-''='等抽象符号。过早的符号训练会破坏数感发展。",
            "evidence_examples": [],
            "teaching_tips": "避免任何形式的符号运算练习，专注于实物操作和数量感知。",
        },
        AgeGroup.MIDDLE: {
            "indicator": "—（此年龄段不适用，少数发展超前的幼儿可能开始接触）",
            "why_this_matters": "中班末期部分幼儿可能对数字符号产生兴趣，这是自然的认知发展，但不应作为统一要求。",
            "evidence_examples": [
                "认识'+'和'-'符号",
                "能读出简单算式（如'3加2等于5'）",
            ],
            "teaching_tips": "以实物操作和口述应用题为重心，符号接触以游戏形式自然引入，不强求。",
        },
        AgeGroup.LARGE: {
            "indicator": "理解'+''-''='符号含义，能书写简单算式，理解加减互逆关系",
            "why_this_matters": "符号运算是数学抽象思维的正式起点——幼儿从实物操作过渡到用符号表达数学关系，这是进入小学数学的必要准备。",
            "evidence_examples": [
                "看到'3+2=?'能直接心算得出5",
                "理解'3+2=5'意味着'5-2=3'（互逆关系）",
                "能自编应用题并写出对应算式",
            ],
            "teaching_tips": "利用应用题作为桥梁（先口述→再写算式），强调符号代表的是真实的数量关系。互逆关系通过分合操作理解。",
        },
    },
    # ── 图形识别 ──
    SubDimension.SHAPE_RECOGNITION: {
        AgeGroup.SMALL: {
            "indicator": "能识别并命名圆形、正方形、三角形",
            "why_this_matters": "小班幼儿对图形的感知是整体和笼统的——他们通过'像什么'来认识图形（圆形像太阳），而非通过特征定义。这是正常的认知发展起点。",
            "evidence_examples": [
                "能指认和说出三种基本图形的名称",
                "能将相同形状配对",
                "理解'圆圆的''方方的'等整体描述",
            ],
            "teaching_tips": "提供丰富多样的图形实物（不同大小、颜色的圆/方/三角），让幼儿触摸、拼搭、描画。不要求定义，重在感知。",
        },
        AgeGroup.MIDDLE: {
            "indicator": "扩展识别长方形、椭圆形、梯形、半圆形，开始关注边角特征",
            "why_this_matters": "4岁是图形知觉的敏感期——幼儿从整体感知过渡到关注图形组成部分（边、角），开始从形状本质特征来认识图形。",
            "evidence_examples": [
                "能说出长方形有几条边几个角",
                "能区分椭圆和圆（'椭圆是扁扁的'）",
                "图形守恒：辨认不受颜色、大小、摆放位置影响",
            ],
            "teaching_tips": "引导关注图形特征（'这个图形有几条边？'），提供变式（不同角度的三角形、不同比例的长方形），避免刻板印象。",
        },
        AgeGroup.LARGE: {
            "indicator": "能在抽象水平概括图形关系（如将正方形、长方形、梯形概括为'四边形'），识别各种图形变式",
            "why_this_matters": "图形概括是数学抽象思维的重要表现——幼儿能从多个具体图形中抽象出共同特征，形成类别概念。",
            "evidence_examples": [
                "能将正方形、长方形、梯形、菱形归为'四边形'",
                "识别旋转/翻转后的图形（不被方向迷惑）",
                "能描述'为什么这个是三角形'（三条边三个角）",
            ],
            "teaching_tips": "引导分类讨论：'这些图形有什么共同点？'提供非典型变式（钝角三角形、细长长方形），促进特征本质理解。",
        },
    },
    # ── 图形组合 ──
    SubDimension.SHAPE_COMPOSITION: {
        AgeGroup.SMALL: {
            "indicator": "能进行简单图形拼图填充",
            "why_this_matters": "图形组合是空间想象力的起点——通过拼搭操作感知图形之间的关系，为几何思维打下基础。",
            "evidence_examples": [
                "能把三角形放入对应凹槽",
                "能用两个半圆形拼成一个圆形",
                "简单积木搭建",
            ],
            "teaching_tips": "提供形状嵌板、简单拼图，让幼儿在操作中感知'部分与整体'的关系。",
        },
        AgeGroup.MIDDLE: {
            "indicator": "能通过移动、翻转、旋转构造图形",
            "why_this_matters": "心理旋转能力是空间认知的核心——幼儿能在头脑中想象图形的移动和变化，这是空间推理的基础。",
            "evidence_examples": [
                "用七巧板拼出指定图形",
                "能判断翻转后的图形是否和原来一样",
                "用积木搭建有结构的作品",
            ],
            "teaching_tips": "提供七巧板、积木、折纸等活动，鼓励'试试转一下会怎样'。",
        },
        AgeGroup.LARGE: {
            "indicator": "能进行图形二等分、四等分，在网格中定位",
            "why_this_matters": "等分概念连接图形与分数——幼儿初步理解'一半''四分之一'的直观含义。网格定位建立了坐标思维的雏形。",
            "evidence_examples": [
                "能将正方形纸对折两次分成四等份",
                "能在简单网格中定位（'第2排第3个'）",
                "能进行图形拼搭创造新图形",
            ],
            "teaching_tips": "折纸、剪纸活动自然引入等分概念。棋盘游戏、坐标寻宝建立空间定位能力。",
        },
    },
    # ── 空间方位 ──
    SubDimension.SPATIAL_AWARENESS: {
        AgeGroup.SMALL: {
            "indicator": "理解上下、前后、里外等空间方位",
            "why_this_matters": "空间方位概念是幼儿认识世界的基础——理解物体与自身的位置关系，是运动发展和空间认知的前提。",
            "evidence_examples": [
                "能按指令把东西放在'桌子上面''盒子里面'",
                "理解'向前走''往后退'",
                "知道自己的身体前面和后面",
            ],
            "teaching_tips": "在日常活动中自然渗透方位语言（'把鞋子放在椅子下面'）。以自身为参照是第一步。",
        },
        AgeGroup.MIDDLE: {
            "indicator": "以自身为中心区分左右，判断远近、高低等相对关系",
            "why_this_matters": "左右区分是空间认知的难点——需要一个稳定的身体参照系。中班幼儿开始建立以自身为中心的左右概念。",
            "evidence_examples": [
                "能指出'我的右手''我的左边'",
                "能判断'桌子比椅子高''门比窗户远'",
                "理解'在……旁边''在……中间'",
            ],
            "teaching_tips": "配合儿歌、游戏练习左右（'举起你的右手'），利用排队、体操等日常活动强化方位意识。",
        },
        AgeGroup.LARGE: {
            "indicator": "以客体为中心区分左右，理解空间方位相对性",
            "why_this_matters": "这是皮亚杰'三山实验'揭示的能力——从他人视角理解空间关系，标志着去自我中心化的认知发展。",
            "evidence_examples": [
                "面对老师时能说出'老师的左边是谁'",
                "理解'我站在树的左边'和'树在我的右边'是同一关系",
                "能看懂简单地图并找到对应位置",
            ],
            "teaching_tips": "多角色扮演游戏（医生和病人面对面），引导从不同角度描述空间关系。寻宝地图活动建立方向感。",
        },
    },
    # ── 立体认知 ──
    SubDimension.SOLID_RECOGNITION: {
        AgeGroup.SMALL: {
            "indicator": "—（此年龄段不适用，以平面图形感知为主）",
            "why_this_matters": "小班幼儿的图形认知以平面为主，立体图形感知尚在发展。常见的'球体→圆形'混淆是正常发展现象。",
            "evidence_examples": [
                "能区分'球'和'圆片'（实物层面，非概念层面）",
                "玩积木时感知不同形状",
            ],
            "teaching_tips": "提供球、积木等立体玩具自由操作，不要求命名，重在触觉和操作体验。",
        },
        AgeGroup.MIDDLE: {
            "indicator": "—（此年龄段以平面图形为主，个别幼儿开始区分平面和立体）",
            "why_this_matters": "中班是平面→立体的过渡期，部分幼儿开始关注'这个积木摸起来不一样'。不应强制要求立体图形命名。",
            "evidence_examples": [
                "能把球和圆形卡片区分开（'这个是球，可以滚'）",
                "对立体积木的不同面感兴趣",
            ],
            "teaching_tips": "提供各种立体实物（球、盒子、罐子）让幼儿自由探索，引导触摸和滚动体验。",
        },
        AgeGroup.LARGE: {
            "indicator": "认识球体、圆柱体、正方体、长方体，理解'面在体上'",
            "why_this_matters": "'面在体上'是平面与立体关系的核心理解——立体图形的表面由平面图形构成。这是从二维到三维的认知飞跃。",
            "evidence_examples": [
                "能说出球体、正方体等的名称",
                "知道正方体有6个正方形的面",
                "不再将球体称为'圆形'",
            ],
            "teaching_tips": "用实物触摸感知立体图形的面（如拆开纸盒看有几个面），讨论平面图形和立体图形的关系。",
        },
    },
    # ── 分类能力 ──
    SubDimension.CLASSIFICATION: {
        AgeGroup.SMALL: {
            "indicator": "能按单一明显外部特征分类（颜色、大小、形状）",
            "why_this_matters": "分类是逻辑思维的基础——幼儿通过'找相同'和'找不同'建立最初的集合概念。单一标准分类是分类能力的起点。",
            "evidence_examples": [
                "能把红色积木放一起、蓝色积木放一起",
                "能区分'大的'和'小的'",
                "完成'把一样的放一起'的指令",
            ],
            "teaching_tips": "在日常收玩具时渗透分类（'先把红色的收起来'），从单一标准逐步过渡到关注多个属性。",
        },
        AgeGroup.MIDDLE: {
            "indicator": "能按两个维度分类，理解'类包含'关系",
            "why_this_matters": "双维度分类要求同时关注两个属性（如'红色且大的'），涉及逻辑交集的初步理解。类包含关系（苹果是水果的一种）标志层级分类能力的出现。",
            "evidence_examples": [
                "能找出'红色大的积木'（同时满足两个条件）",
                "理解'苹果、香蕉都是水果'",
                "分类时能保持标准一致（不中途换标准）",
            ],
            "teaching_tips": "用嵌套分类游戏（如动物→哺乳动物→猫），引导讨论'是不是所有的猫都是动物'帮助建立层级关系。",
        },
        AgeGroup.LARGE: {
            "indicator": "能按事物内在属性（功能、用途）分类，理解交集与包含关系",
            "why_this_matters": "按内在属性分类要求抽象思维——从'看起来像'到'用起来是'，标志着从感知分类到概念分类的转变。",
            "evidence_examples": [
                "能把'吃饭用的''写字用的''穿的'分类",
                "理解两个集合的交叉（如'既是女生又穿红衣服'）",
                "能解释分类理由（'因为它们都是交通工具'）",
            ],
            "teaching_tips": "用维恩图入门（两个交叉圆圈），讨论'有没有东西属于两个组'。鼓励幼儿定义自己的分类标准。",
        },
    },
    # ── 模式识别 ──
    SubDimension.PATTERN_RECOGNITION: {
        AgeGroup.SMALL: {
            "indicator": "能识别并复制简单AB模式（如红蓝红蓝）",
            "why_this_matters": "模式识别是代数思维的萌芽——发现规律、预测下一个，是数学推理的核心能力。AB模式是最简单的重复模式，是小班幼儿的认知起点。",
            "evidence_examples": [
                "看到红蓝红蓝的珠子，能指出'接下来是红色'",
                "能照着红蓝红蓝的模式自己摆出来",
                "发现儿歌中的重复节奏",
            ],
            "teaching_tips": "在生活中发现模式（起床→吃饭→游戏→睡觉是日常模式），用积木、串珠提供模式复制体验。",
        },
        AgeGroup.MIDDLE: {
            "indicator": "能识别、复制、扩展ABC/AABB模式",
            "why_this_matters": "从AB到AABB/ABC，模式复杂度提升——幼儿需要识别更长的核心单元（从2元素到3元素），认知负荷显著增加。",
            "evidence_examples": [
                "看到红红蓝红红蓝，能继续排下去",
                "能从模式序列中识别出'核心单元'（如'红蓝黄'）",
                "能指出模式中哪一部分在重复",
            ],
            "teaching_tips": "引导讨论'什么在重复'——这是从表层感知到核心单元抽象的关键提问。用动作模式辅助理解（拍手拍腿→红蓝）。",
        },
        AgeGroup.LARGE: {
            "indicator": "能识别、创造复杂模式（AAB/ABB/ABBA），实现跨形式转换",
            "why_this_matters": "跨形式转换（如颜色模式→声音模式）标志真正的模式抽象——幼儿理解'规律'本身，而非具体元素的排列。",
            "evidence_examples": [
                "识别ABBA等复杂模式",
                "将红蓝红的颜色模式转换成拍手跺脚拍手的声音模式",
                "能自创模式并解释规律",
            ],
            "teaching_tips": "鼓励跨形式转换（颜色→动作→声音→图形），提供开放式模式创造任务（'用这些材料创造你自己的规律'）。",
        },
    },
    # ── 模式扩展 ──
    SubDimension.PATTERN_EXTENSION: {
        AgeGroup.SMALL: {
            "indicator": "—（此年龄段以模式识别和复制为主）",
            "why_this_matters": "小班幼儿的模式能力停留在识别和复制阶段，模式扩展需要更强的预测和推理能力。",
            "evidence_examples": [],
            "teaching_tips": "先确保AB模式识别和复制稳定后，再尝试简单的'红蓝红蓝__？'填空。",
        },
        AgeGroup.MIDDLE: {
            "indicator": "能扩展简单模式，填补中间缺失元素",
            "why_this_matters": "模式填充（序列中间缺一个）比扩展（序列末尾接一个）更难——需要同时关注前后关系。这测试对模式核心单元的真正理解。",
            "evidence_examples": [
                "看到ABAB__能填出下一个",
                "能从序列中间补全缺失元素",
                "能判断一个序列'有没有规律'",
            ],
            "teaching_tips": "从模式末尾扩展到中间填空——后者需要更强的模式理解。使用模式卡片，遮盖中间或末尾元素让幼儿补充。",
        },
        AgeGroup.LARGE: {
            "indicator": "能扩展和填充复杂模式，创造自己的模式并遵循稳定规律",
            "why_this_matters": "模式创造是最高层次的模式能力——幼儿不仅理解已有模式，还能主动构建新模式。这标志模式思维的成熟。",
            "evidence_examples": [
                "能创造AAB、ABB等复杂模式",
                "创造的'模式'有稳定的核心单元（不是随机的）",
                "能解释自己的模式规律",
            ],
            "teaching_tips": "提供开放式材料（多种颜色/形状的积木），鼓励创造和命名自己的模式。引导验证：'检查一下你的规律是不是一直在重复'。",
        },
    },
    # ── 排序能力 ──
    SubDimension.SORTING: {
        AgeGroup.SMALL: {
            "indicator": "能进行简单配对和匹配（一样的放一起）",
            "why_this_matters": "配对是排序的前身——在能够'从大到小排列'之前，幼儿需要先能识别'一样'和'不一样'，建立比较的基础。",
            "evidence_examples": [
                "能把相同的袜子配对",
                "能找出'最大的'和'最小的'",
                "理解'比……大''比……小'",
            ],
            "teaching_tips": "配对游戏（找相同）、比较游戏（找最大/最小），用具体实物操作建立比较概念。",
        },
        AgeGroup.MIDDLE: {
            "indicator": "能按规律排序（从大到小、从长到短），最多5个物品",
            "why_this_matters": "排序涉及序列化思维——同时比较多个物品并按某一维度排列，需要逻辑推理和系统比较策略。",
            "evidence_examples": [
                "能将5根不同长度的吸管从短到长排列",
                "排序时使用系统策略（先找最小的，再找下一个最小的）",
                "能按大小或长短以外的一个维度排序",
            ],
            "teaching_tips": "从3个物品开始（减少认知负荷），逐步增加到5个。引导讨论排序策略：'你是怎么知道这个应该放这里的？'",
        },
        AgeGroup.LARGE: {
            "indicator": "能按多标准交替排序，理解可逆性",
            "why_this_matters": "多标准排序和可逆性（正着排和倒着排）标志排序思维的成熟——幼儿理解序列是一个可双向操作的系统。",
            "evidence_examples": [
                "先按颜色再按大小排序",
                "能从大到小排，也能从小到大排",
                "能将新物品正确插入已排好的序列中",
            ],
            "teaching_tips": "引入多标准排序（先分颜色组，每组内按大小排），建立二维矩阵思维。用数字线游戏强化序列可逆性理解。",
        },
    },
}


# ═══════════════════════════════════════════════════════════════════════
# Detailed assessment indicators — per sub-skill × age group
# Derived from textbook Chapters 3-6, 9-10
# ═══════════════════════════════════════════════════════════════════════

ASSESSMENT_INDICATORS: Dict[str, Dict[str, Dict[str, str]]] = {
    # ── Counting ──
    "点数准确性": {
        AgeGroup.SMALL: "能手口一致地点数5以内物体",
        AgeGroup.MIDDLE: "能手口一致地点数10以内物体",
        AgeGroup.LARGE: "能目测计数20以内",
    },
    "按数取物": {
        AgeGroup.SMALL: "能按数（5以内）取物",
        AgeGroup.MIDDLE: "能按数（10以内）取物",
        AgeGroup.LARGE: "能熟练按数取物",
    },
    "数量比较": {
        AgeGroup.SMALL: "能比较两组物体的'多''少''一样多'",
        AgeGroup.MIDDLE: "能比较10以内数量的多少",
        AgeGroup.LARGE: "理解相邻数关系（n比n-1多1）",
    },
    "序数理解": {
        AgeGroup.SMALL: "—",
        AgeGroup.MIDDLE: "理解序数（第1—第10）",
        AgeGroup.LARGE: "熟练掌握序数",
    },
    "数的组成": {
        AgeGroup.SMALL: "—",
        AgeGroup.MIDDLE: "感知5以内数的组成",
        AgeGroup.LARGE: "理解10以内数的组成与分解",
    },
    "数量守恒": {
        AgeGroup.SMALL: "—",
        AgeGroup.MIDDLE: "开始出现守恒意识",
        AgeGroup.LARGE: "完全建立数量守恒",
    },
    "唱数与群数": {
        AgeGroup.SMALL: "能唱数到10",
        AgeGroup.MIDDLE: "能唱数到20+",
        AgeGroup.LARGE: "能群数（2个2个、5个5个）",
    },
    # ── Addition/Subtraction ──
    "实物操作正确率": {
        AgeGroup.SMALL: "感知5以内数量的增加与减少",
        AgeGroup.MIDDLE: "借助实物进行10以内加减",
        AgeGroup.LARGE: "脱离实物进行10以内加减",
    },
    "符号运算正确率": {
        AgeGroup.SMALL: "—",
        AgeGroup.MIDDLE: "—",
        AgeGroup.LARGE: "理解'+''-''='符号含义",
    },
    "策略水平": {
        AgeGroup.SMALL: "实物点数全部",
        AgeGroup.MIDDLE: "点数全部或接着数",
        AgeGroup.LARGE: "接着数/倒接数/按群加减",
    },
    "应用题理解": {
        AgeGroup.SMALL: "—",
        AgeGroup.MIDDLE: "能理解简单口述应用题",
        AgeGroup.LARGE: "能自编和解答简单应用题",
    },
    "运算思维灵活性": {
        AgeGroup.SMALL: "—",
        AgeGroup.MIDDLE: "—",
        AgeGroup.LARGE: "理解加减互逆关系",
    },
    # ── Shapes & Space ──
    "平面图形识别": {
        AgeGroup.SMALL: "圆形、正方形、三角形",
        AgeGroup.MIDDLE: "+长方形、椭圆形、梯形、半圆形",
        AgeGroup.LARGE: "概括'四边形'等类别",
    },
    "立体图形识别": {
        AgeGroup.SMALL: "—",
        AgeGroup.MIDDLE: "—",
        AgeGroup.LARGE: "球体、圆柱体、正方体、长方体",
    },
    "图形特征描述": {
        AgeGroup.SMALL: "'圆圆的''方方的'",
        AgeGroup.MIDDLE: "认识边、角等特征",
        AgeGroup.LARGE: "能按属性定义图形",
    },
    "空间方位": {
        AgeGroup.SMALL: "上/下、前/后、里/外",
        AgeGroup.MIDDLE: "+以自身为中心分左右",
        AgeGroup.LARGE: "+以客体为中心分左右",
    },
    "图形组合与分解": {
        AgeGroup.SMALL: "简单拼图填充",
        AgeGroup.MIDDLE: "移动/翻转/旋转构造图形",
        AgeGroup.LARGE: "七巧板拼搭、二等分/四等分",
    },
    # ── Patterns ──
    "分类能力": {
        AgeGroup.SMALL: "按单一明显特征分类",
        AgeGroup.MIDDLE: "按两个维度分类",
        AgeGroup.LARGE: "按事物内在属性分类",
    },
    "模式识别": {
        AgeGroup.SMALL: "识别简单AB模式",
        AgeGroup.MIDDLE: "识别ABC/AABB模式",
        AgeGroup.LARGE: "识别复杂模式（AAB/ABB/ABBA）",
    },
    "模式扩展": {
        AgeGroup.SMALL: "—",
        AgeGroup.MIDDLE: "扩展简单模式",
        AgeGroup.LARGE: "扩展和填充复杂模式",
    },
    "模式创造": {
        AgeGroup.SMALL: "—",
        AgeGroup.MIDDLE: "创造简单模式",
        AgeGroup.LARGE: "创造复杂模式，跨形式转换",
    },
    "排序能力": {
        AgeGroup.SMALL: "简单配对和匹配",
        AgeGroup.MIDDLE: "按规律排序（大小/长短）",
        AgeGroup.LARGE: "按多标准交替排序",
    },
    "规律语言描述": {
        AgeGroup.SMALL: "用'一样''不一样'描述",
        AgeGroup.MIDDLE: "能说出简单规律",
        AgeGroup.LARGE: "描述复杂规律及解释核心单元",
    },
}


# ═══════════════════════════════════════════════════════════════════════
# Development stage models per dimension
# ═══════════════════════════════════════════════════════════════════════

class CountingStage(str, Enum):
    """计数的四个发展阶段 (Textbook Ch4)"""
    STAGE1_CHANTING = "chanting"                    # 口头数数（唱数）— 2-3岁
    STAGE2_POINT_COUNT = "point_count"              # 按物点数 — 3-4岁
    STAGE3_CARDINAL = "cardinal"                     # 说出总数 — 4岁+
    STAGE4_GROUP_COUNT = "group_count"               # 按群计数 — 5-6岁


COUNTING_STAGE_INFO: Dict[str, Dict] = {
    CountingStage.STAGE1_CHANTING: {
        "name": "口头数数（唱数）",
        "age": "2-3岁",
        "description": "按顺序背诵数词，手口不一致，不理解实际意义",
        "indicator": "能从1背到10，但不会点数",
        "teaching_focus": "建立数词顺序，在生活中大量接触数字",
    },
    CountingStage.STAGE2_POINT_COUNT: {
        "name": "按物点数",
        "age": "3-4岁",
        "description": "手逐一指点物体并说数词，但点数后说不出总数",
        "indicator": "能用手点着物体一个一个数，但最后不知道有几个",
        "teaching_focus": "强化手口一致，一一对应练习",
    },
    CountingStage.STAGE3_CARDINAL: {
        "name": "说出总数",
        "age": "4岁+",
        "description": "点数后用最后一个数词表示总数，标志数概念形成",
        "indicator": "数完后能正确说出'一共X个'",
        "teaching_focus": "反复强化'总数代表集合量'，这是关键发展节点",
    },
    CountingStage.STAGE4_GROUP_COUNT: {
        "name": "按群计数",
        "age": "5-6岁",
        "description": "以数群为单位计数（2个2个、5个5个），更高抽象水平",
        "indicator": "能2个2个、5个5个、10个10个数到100",
        "teaching_focus": "从逐一计数过渡到按群计数，建立十进制基础",
    },
}


class OperationStage(str, Enum):
    """运算能力发展三阶段 (Textbook Ch6)"""
    CONCRETE_OP = "concrete_op"        # 动作水平（具体实物）
    REPRESENTATIONAL = "representational"  # 表象水平
    ABSTRACT_OP = "abstract_op"         # 概念水平（抽象符号）


OPERATION_STAGE_INFO: Dict[str, Dict] = {
    OperationStage.CONCRETE_OP: {
        "name": "动作水平（具体实物操作）",
        "age": "小班—中班",
        "description": "以实物或图片为工具，借助合并、分开等动作进行运算",
        "example": "提供4个苹果和1个苹果实物，通过点数得出5个",
        "strategy": "实物点数全部",
    },
    OperationStage.REPRESENTATIONAL: {
        "name": "表象水平（半具象）",
        "age": "中班—大班",
        "description": "不借助实物，依靠头脑中对形象化物体的再现进行运算",
        "example": "口述'给你4个苹果，再给1个，一共几个？'凭借表象回答",
        "strategy": "点数全部或接着数",
    },
    OperationStage.ABSTRACT_OP: {
        "name": "概念水平（抽象符号）",
        "age": "大班",
        "description": "无需实物或表象依托，直接运用抽象数概念进行运算",
        "example": "听到'4+1=?'即能说出答案",
        "strategy": "接着数/倒接数/按群加减",
    },
}


class PatternStage(str, Enum):
    """模式能力发展的五阶段 (Textbook Ch3)"""
    RECOGNIZE = "recognize"         # 模式识别
    COPY = "copy"                    # 模式复制
    EXTEND = "extend"                # 模式扩展与填充
    CREATE = "create"                # 模式创造
    TRANSFORM = "transform"          # 模式比较与转换


PATTERN_STAGE_INFO: Dict[str, Dict] = {
    PatternStage.RECOGNIZE: {
        "name": "模式识别",
        "description": "能发现并指出序列中的规律",
        "age_anchor": "小班",
        "example": "看到红蓝红蓝的珠子，能指出'红色后面是蓝色'",
    },
    PatternStage.COPY: {
        "name": "模式复制",
        "description": "能按照已有模式照样子排出来",
        "age_anchor": "小班—中班",
        "example": "照着红蓝红蓝的模式，自己摆出一样的序列",
    },
    PatternStage.EXTEND: {
        "name": "模式扩展与填充",
        "description": "能接续未完的模式，或填补中间缺失的元素",
        "age_anchor": "中班",
        "example": "看到红蓝红蓝__，能填出下一个是'红'",
    },
    PatternStage.CREATE: {
        "name": "模式创造",
        "description": "能自己创造出一种稳定的模式",
        "age_anchor": "中班—大班",
        "example": "自己创造出'红红黄红红黄'的AAB模式",
    },
    PatternStage.TRANSFORM: {
        "name": "模式比较与转换",
        "description": "能将一种形式的模式转换为另一种形式（如视觉颜色→拍手动作）",
        "age_anchor": "大班",
        "example": "看到颜色模式后，能用拍手/跺脚动作表现同样的规律",
    },
}


# ═══════════════════════════════════════════════════════════════════════
# Comprehensive error pattern catalog (20+ from textbook)
# ═══════════════════════════════════════════════════════════════════════

ERROR_PATTERNS: List[Dict] = [
    # ── Counting errors ──
    {
        "id": "mirror_writing",
        "name": "镜像书写",
        "description": "3→ε、5→ϱ、7→⅃",
        "dimension": Dimension.COUNTING,
        "age_groups": [AgeGroup.SMALL, AgeGroup.MIDDLE],
        "is_developmental": True,
        "teaching_implication": "正常视觉-运动发展过程，不反映数学能力，无需刻意纠正",
    },
    {
        "id": "unordered_counting",
        "name": "手口不一",
        "description": "手点得快口说得慢，或反之；重复数或漏数",
        "dimension": Dimension.COUNTING,
        "age_groups": [AgeGroup.SMALL],
        "is_developmental": True,
        "teaching_implication": "手口一致协调尚未建立，需大量一一对应练习",
    },
    {
        "id": "missing_cardinal_principle",
        "name": "基数原则未掌握",
        "description": "点数正确但说不出'一共几个'",
        "dimension": Dimension.COUNTING,
        "age_groups": [AgeGroup.SMALL, AgeGroup.MIDDLE],
        "is_developmental": True,
        "teaching_implication": "理解'总数代表集合量'是关键发展节点，需反复强化",
    },
    {
        "id": "quantity_retrieval_deviation",
        "name": "按数取物偏差",
        "description": "要求拿5个拿了4个/6个",
        "dimension": Dimension.COUNTING,
        "age_groups": [AgeGroup.SMALL, AgeGroup.MIDDLE],
        "is_developmental": True,
        "teaching_implication": "数量表征不精确，需多感官参与的数量操作练习",
    },
    {
        "id": "skip_counting",
        "name": "跳数/漏数",
        "description": "1,2,4,6,5…数字顺序混乱",
        "dimension": Dimension.COUNTING,
        "age_groups": [AgeGroup.SMALL],
        "is_developmental": True,
        "teaching_implication": "数字顺序尚未牢固建立，需大量唱数和点数练习",
    },
    {
        "id": "conservation_not_established",
        "name": "数的守恒未建立",
        "description": "同样数量换排列说不一样多",
        "dimension": Dimension.COUNTING,
        "age_groups": [AgeGroup.MIDDLE],
        "is_developmental": True,
        "teaching_implication": "仍受视觉排列影响，需多变式练习建立守恒概念",
    },
    # ── Operation errors ──
    {
        "id": "concrete_dependency",
        "name": "实物依赖",
        "description": "不用实物就不会算",
        "dimension": Dimension.ADDITION_SUBTRACTION,
        "age_groups": [AgeGroup.MIDDLE, AgeGroup.LARGE],
        "is_developmental": True,
        "teaching_implication": "需支持半具象到符号的过渡，如点卡、手指替代",
    },
    {
        "id": "operation_confusion",
        "name": "加减混淆",
        "description": "所有题都做加法（或减法）",
        "dimension": Dimension.ADDITION_SUBTRACTION,
        "age_groups": [AgeGroup.MIDDLE],
        "is_developmental": True,
        "teaching_implication": "运算符号意义未建立，需在真实情境中区分加减",
    },
    {
        "id": "count_all_strategy",
        "name": "全部点数（不会接着数）",
        "description": "算3+2时从1数到5，不会从3接着数",
        "dimension": Dimension.ADDITION_SUBTRACTION,
        "age_groups": [AgeGroup.MIDDLE],
        "is_developmental": True,
        "teaching_implication": "引导'接着数'策略，从实物过渡到符号表征",
    },
    {
        "id": "no_inverse_understanding",
        "name": "不理解互逆关系",
        "description": "不知道3+2=5意味着5-2=3",
        "dimension": Dimension.ADDITION_SUBTRACTION,
        "age_groups": [AgeGroup.LARGE],
        "is_developmental": True,
        "teaching_implication": "在分合操作中建立互逆理解，从实物分合过渡到算式",
    },
    # ── Shapes & Space errors ──
    {
        "id": "shape_stereotype",
        "name": "图形刻板印象",
        "description": "只认识顶点在上的等边三角形",
        "dimension": Dimension.SHAPES_SPACE,
        "age_groups": [AgeGroup.SMALL, AgeGroup.MIDDLE, AgeGroup.LARGE],
        "is_developmental": True,
        "teaching_implication": "提供多样化变式（钝角三角形、顶点在下的三角形等）",
    },
    {
        "id": "2d3d_confusion",
        "name": "二维三维混淆",
        "description": "将球体叫'圆形'，将正方体叫'正方形'",
        "dimension": Dimension.SHAPES_SPACE,
        "age_groups": [AgeGroup.SMALL, AgeGroup.MIDDLE],
        "is_developmental": True,
        "teaching_implication": "触摸比较平面与立体，建立'面在体上'概念",
    },
    {
        "id": "left_right_confusion",
        "name": "空间左右混淆",
        "description": "以自身为中心都无法区分左右",
        "dimension": Dimension.SHAPES_SPACE,
        "age_groups": [AgeGroup.MIDDLE, AgeGroup.LARGE],
        "is_developmental": True,
        "teaching_implication": "需通过身体运动感知空间方位，配合儿歌、游戏",
    },
    {
        "id": "relativity_not_understood",
        "name": "方位相对性不理解",
        "description": "面对面时认为对方的左也是自己的左",
        "dimension": Dimension.SHAPES_SPACE,
        "age_groups": [AgeGroup.LARGE],
        "is_developmental": True,
        "teaching_implication": "多情境体验方位相对性",
    },
    # ── Pattern errors ──
    {
        "id": "surface_pattern_understanding",
        "name": "模式理解表面化",
        "description": "只能复制不能扩展/创造；能哼唱模式但不能说出核心单元",
        "dimension": Dimension.PATTERNS,
        "age_groups": [AgeGroup.MIDDLE, AgeGroup.LARGE],
        "is_developmental": True,
        "teaching_implication": "模式核心单元概念未建立，需引导讨论'什么在重复'",
    },
    {
        "id": "classification_standard_drift",
        "name": "分类标准漂移",
        "description": "分类中途切换标准（先按颜色又改按大小）",
        "dimension": Dimension.PATTERNS,
        "age_groups": [AgeGroup.SMALL, AgeGroup.MIDDLE],
        "is_developmental": True,
        "teaching_implication": "分类一致性尚未稳定，可引导幼儿说出分类标准",
    },
    {
        "id": "unstable_creation",
        "name": "模式创造不稳定",
        "description": "创造的'模式'无稳定规律",
        "dimension": Dimension.PATTERNS,
        "age_groups": [AgeGroup.MIDDLE, AgeGroup.LARGE],
        "is_developmental": True,
        "teaching_implication": "检查'你创造的规律是什么'，引导反思和验证",
    },
    {
        "id": "extend_from_mid_unit",
        "name": "模式扩展断点困难",
        "description": "序列结束于重复单元中间时无法正确扩展（如AAB·AA__）",
        "dimension": Dimension.PATTERNS,
        "age_groups": [AgeGroup.MIDDLE, AgeGroup.LARGE],
        "is_developmental": True,
        "teaching_implication": "核心单元概念是关键——引导识别'AB'是什么，而不仅是记忆序列",
    },
]


# ═══════════════════════════════════════════════════════════════════════
# Mapping: Counting 5 Principles (Gelman & Gallistel, from Ch4)
# ═══════════════════════════════════════════════════════════════════════

COUNTING_PRINCIPLES: List[Dict] = [
    {
        "principle": "一一对应原则",
        "description": "每个元素只能对应一个数词，必须且只能点数一次",
        "common_violation": "手口不匹配、重复数（双标记）、漏数",
    },
    {
        "principle": "固定顺序原则",
        "description": "数字顺序固定不变（1,2,3,4...），每个数比前一个多1",
        "common_violation": "数字顺序混乱、跳数",
    },
    {
        "principle": "顺序无关原则",
        "description": "总数与点数顺序无关，无论从哪开始数结果相同",
        "common_violation": "以为不同方向数结果不同",
    },
    {
        "principle": "基数原则",
        "description": "最后一个数词代表集合的总数",
        "common_violation": "点数正确但说不出'一共几个'",
    },
    {
        "principle": "抽象原则",
        "description": "任何可数实体（包括声音、动作、想法）都可计数",
        "common_violation": "只认为实物可数",
    },
]


# ═══════════════════════════════════════════════════════════════════════
# Cross-dimensional teaching principles (from all textbook chapters)
# ═══════════════════════════════════════════════════════════════════════

TEACHING_PRINCIPLES: List[Dict] = [
    {
        "id": "concrete_to_abstract",
        "name": "具体→半具体→抽象的渐进路径",
        "description": "所有数学概念的学习都应从实物操作开始，逐步过渡到图片/符号表征，最后达到抽象概念水平",
        "guidance": {
            AgeGroup.SMALL: "动作水平：借助实物、教具进行数学活动",
            AgeGroup.MIDDLE: "表象水平：借助图片、点卡、手指等进行数学活动",
            AgeGroup.LARGE: "符号水平：运用数字符号、算式进行数学活动",
        },
    },
    {
        "id": "real_life_context",
        "name": "植根于真实生活情境",
        "description": "在日常生活和游戏中自然渗透数学经验，避免脱离情境的机械训练",
        "guidance": "关注幼儿对数学问题的'理解过程'，而非仅仅关注'正确答案'",
    },
    {
        "id": "multi_representation",
        "name": "多元表征促进深层理解",
        "description": "提供视觉、听觉、动作、语言等多种表征方式，鼓励幼儿在不同表征形式之间转换",
        "guidance": "多样化材料投放（低结构+高结构均衡）",
    },
    {
        "id": "development_sequence",
        "name": "遵循发展顺序，尊重个体差异",
        "description": "了解每个年龄段的典型发展特点和个体差异，不拔高要求",
        "guidance": "利用关键发展期：4岁图形敏感期、5岁数概念飞跃期",
    },
    {
        "id": "encourage_discussion",
        "name": "鼓励数学交流与讨论",
        "description": "引导幼儿讨论、解释数学过程，关注'如何发现'和'为什么'",
        "guidance": "如引导讨论'什么在重复'帮助幼儿从表层感知上升到对核心单元的抽象认识",
    },
]


# ═══════════════════════════════════════════════════════════════════════
# Number uses taxonomy (from Ch5)
# ═══════════════════════════════════════════════════════════════════════

NUMBER_USE_TYPES: List[Dict] = [
    {"type": "命名数", "english": "Nominal", "description": "给集合命名，表示数量属性",
     "example": "'3个苹果'——忽略颜色、形状等"},
    {"type": "参照数", "english": "Reference", "description": "作为事物的参照号码/标示",
     "example": "电话号码、公交车号、学号"},
    {"type": "基数", "english": "Cardinal", "description": "表示集合中物体的个数（多少）",
     "example": "'6颗糖果''4个女孩'"},
    {"type": "序数", "english": "Ordinal", "description": "表示物体的排列顺序或位置",
     "example": "'第3名''第2排'"},
]


# ═══════════════════════════════════════════════════════════════════════
# Subitizing info (from Ch4)
# ═══════════════════════════════════════════════════════════════════════

SUBTITIZING_INFO: Dict[str, Dict] = {
    "perceptual": {
        "name": "感知估算",
        "range": "≤3",
        "description": "幼儿天生能快速感知3以内的小数量",
    },
    "conceptual": {
        "name": "概念估算",
        "range": "4-6",
        "description": "借助模式识别（如骰子上的两个3组成6），建立在感数基础上",
    },
}


# ═══════════════════════════════════════════════════════════════════════
# Level determination & display helpers
# ═══════════════════════════════════════════════════════════════════════

# Age-group-anchored score→level thresholds.
# Younger children have lower bars (lenient), older children have higher bars (strict).
# Rationale: a small-class child getting 6/10 correct is doing well (L3),
#            a large-class child getting 6/10 needs more support (L2).
AGE_LEVEL_THRESHOLDS: Dict[str, Dict[str, int]] = {
    AgeGroup.SMALL:  {"L4": 85, "L3": 60, "L2": 30},   # lenient — younger kids, lower bar
    AgeGroup.MIDDLE: {"L4": 90, "L3": 70, "L2": 40},   # standard
    AgeGroup.LARGE:  {"L4": 95, "L3": 80, "L2": 50},   # strict — older kids, higher bar
}


def determine_level(score: float, age_group: str = None, dimension: str = None) -> DevLevel:
    """
    Determine development level based on score percentage, with age-group-anchored thresholds.

    The same score yields different levels for different age groups:
      - A small-class child scoring 50% → L2 (adequate for age)
      - A large-class child scoring 50% → L1 (below age expectation)

    When age_group is None, falls back to legacy uniform thresholds (91/71/41).

    Args:
        score: percentage score 0-100
        age_group: optional age group ("small"|"middle"|"large") for anchored scoring
        dimension: optional dimension for future per-dimension fine-tuning
    """
    if age_group and age_group in AGE_LEVEL_THRESHOLDS:
        thresholds = AGE_LEVEL_THRESHOLDS[age_group]
        if score >= thresholds["L4"]:
            return DevLevel.L4_ADVANCED
        elif score >= thresholds["L3"]:
            return DevLevel.L3_PROFICIENT
        elif score >= thresholds["L2"]:
            return DevLevel.L2_GROWING
        else:
            return DevLevel.L1_SPROUT

    # Legacy fallback — uniform thresholds (backward compatible)
    if score >= 91:
        return DevLevel.L4_ADVANCED
    elif score >= 71:
        return DevLevel.L3_PROFICIENT
    elif score >= 41:
        return DevLevel.L2_GROWING
    else:
        return DevLevel.L1_SPROUT


def get_level_description(level: DevLevel) -> Dict[str, str]:
    """Get human-readable level description with PCK stage context."""
    descriptions = {
        DevLevel.L1_SPROUT: {
            "name": "萌芽期",
            "emoji": "🌱",
            "meaning": "该维度核心经验尚未建立，需大量具体实物操作和教师引导",
            "pck_stage": "动作水平：依赖实物感知和操作",
            "teaching_emphasis": "大量实物操作、一一对应练习、多感官参与",
        },
        DevLevel.L2_GROWING: {
            "name": "发展期",
            "emoji": "🌿",
            "meaning": "该维度核心经验正在形成中，需持续巩固和多样化练习",
            "pck_stage": "动作→表象过渡：开始使用半具象策略",
            "teaching_emphasis": "支持半具象过渡（点卡、手指）、多变式练习",
        },
        DevLevel.L3_PROFICIENT: {
            "name": "熟练期",
            "emoji": "🌳",
            "meaning": "该维度核心经验已基本建立，能稳定表现，可向更高阶过渡",
            "pck_stage": "表象→符号过渡：趋于抽象表征",
            "teaching_emphasis": "鼓励符号表征、应用题理解、策略多样化",
        },
        DevLevel.L4_ADVANCED: {
            "name": "进阶期",
            "emoji": "⭐",
            "meaning": "该维度超越本年龄段期望，可能具备更高年龄段的数学思维",
            "pck_stage": "符号运算萌芽：稳定的抽象概念水平",
            "teaching_emphasis": "提供高阶挑战、跨维度综合活动",
        },
    }
    return descriptions.get(level, {})


def get_dimension_display_name(dimension: str) -> str:
    """Get Chinese display name for dimension (aligned with textbook chapters)."""
    names = {
        Dimension.COUNTING: "数概念与运算",
        Dimension.ADDITION_SUBTRACTION: "数运算能力",
        Dimension.SHAPES_SPACE: "图形与空间",
        Dimension.PATTERNS: "集合与模式",
    }
    return names.get(dimension, dimension)


def get_sub_dimension_display_name(sub_dim: str) -> str:
    """Get Chinese display name for a sub-dimension."""
    names = {
        SubDimension.COUNTING_ACCURACY: "点数能力",
        SubDimension.QUANTITY_COMPARISON: "数量比较",
        SubDimension.NUMBER_COMPOSITION: "数的组成",
        SubDimension.CONCRETE_OPERATION: "实物运算",
        SubDimension.SYMBOLIC_OPERATION: "符号运算",
        SubDimension.SHAPE_RECOGNITION: "图形识别",
        SubDimension.SHAPE_COMPOSITION: "图形组合",
        SubDimension.SPATIAL_AWARENESS: "空间方位",
        SubDimension.SOLID_RECOGNITION: "立体认知",
        SubDimension.CLASSIFICATION: "分类能力",
        SubDimension.PATTERN_RECOGNITION: "模式识别",
        SubDimension.PATTERN_EXTENSION: "模式扩展",
        SubDimension.SORTING: "排序能力",
    }
    return names.get(sub_dim, sub_dim)


def get_indicator_explanation(sub_dim: str, age_group: str) -> Optional[Dict]:
    """Get the detailed indicator explanation for a sub-dimension × age group.

    Returns dict with: indicator, why_this_matters, evidence_examples, teaching_tips
    """
    try:
        return INDICATOR_EXPLANATIONS.get(sub_dim, {}).get(age_group)
    except Exception:
        return None


def get_age_display_name(age_group: str) -> str:
    """Get Chinese display name for age group."""
    names = {
        AgeGroup.SMALL: "小班（3-4岁）",
        AgeGroup.MIDDLE: "中班（4-5岁）",
        AgeGroup.LARGE: "大班（5-6岁）",
    }
    return names.get(age_group, age_group)


# ═══════════════════════════════════════════════════════════════════════
# Core-experience targeting — map a worksheet's printed learning objective
# (recognized by vision) to the 13 sub-dimensions (= the 13 "核心经验").
# Used by assessment_engine to build the "本操作单指向核心经验" conclusion.
# ═══════════════════════════════════════════════════════════════════════

# Each keyword maps to one sub-dimension. Keywords are matched as substrings
# against the learning_objective text. Keep keywords specific enough to
# avoid cross-noise (e.g. "拼搭/拼成" → shape_composition, not number_composition).
LEARNING_OBJECTIVE_KEYWORDS: Dict[str, str] = {
    # ── 数概念与运算 ──
    "点数": SubDimension.COUNTING_ACCURACY,
    "数数": SubDimension.COUNTING_ACCURACY,
    "计数": SubDimension.COUNTING_ACCURACY,
    "唱数": SubDimension.COUNTING_ACCURACY,
    "点一点": SubDimension.COUNTING_ACCURACY,
    "数一数": SubDimension.COUNTING_ACCURACY,
    "说出总数": SubDimension.COUNTING_ACCURACY,
    "手口一致": SubDimension.COUNTING_ACCURACY,
    "多少": SubDimension.QUANTITY_COMPARISON,
    "一样多": SubDimension.QUANTITY_COMPARISON,
    "比较数量": SubDimension.QUANTITY_COMPARISON,
    "多几个": SubDimension.QUANTITY_COMPARISON,
    "少几个": SubDimension.QUANTITY_COMPARISON,
    "比一比": SubDimension.QUANTITY_COMPARISON,
    "守恒": SubDimension.QUANTITY_COMPARISON,
    "分解": SubDimension.NUMBER_COMPOSITION,
    "组成": SubDimension.NUMBER_COMPOSITION,
    "分合": SubDimension.NUMBER_COMPOSITION,
    "分成": SubDimension.NUMBER_COMPOSITION,
    "合起来": SubDimension.NUMBER_COMPOSITION,
    "凑十": SubDimension.NUMBER_COMPOSITION,
    "凑10": SubDimension.NUMBER_COMPOSITION,
    "添上": SubDimension.CONCRETE_OPERATION,
    "拿走": SubDimension.CONCRETE_OPERATION,
    "增加": SubDimension.CONCRETE_OPERATION,
    "减少": SubDimension.CONCRETE_OPERATION,
    "变多": SubDimension.CONCRETE_OPERATION,
    "变少": SubDimension.CONCRETE_OPERATION,
    "实物加减": SubDimension.CONCRETE_OPERATION,
    "加法": SubDimension.CONCRETE_OPERATION,
    "减法": SubDimension.CONCRETE_OPERATION,
    "加减": SubDimension.CONCRETE_OPERATION,
    "算式": SubDimension.SYMBOLIC_OPERATION,
    "列式": SubDimension.SYMBOLIC_OPERATION,
    "加号": SubDimension.SYMBOLIC_OPERATION,
    "减号": SubDimension.SYMBOLIC_OPERATION,
    "等号": SubDimension.SYMBOLIC_OPERATION,
    "符号运算": SubDimension.SYMBOLIC_OPERATION,
    "互逆": SubDimension.SYMBOLIC_OPERATION,
    # ── 图形与空间 ──
    "三角形": SubDimension.SHAPE_RECOGNITION,
    "圆形": SubDimension.SHAPE_RECOGNITION,
    "正方形": SubDimension.SHAPE_RECOGNITION,
    "长方形": SubDimension.SHAPE_RECOGNITION,
    "梯形": SubDimension.SHAPE_RECOGNITION,
    "椭圆": SubDimension.SHAPE_RECOGNITION,
    "半圆": SubDimension.SHAPE_RECOGNITION,
    "图形识别": SubDimension.SHAPE_RECOGNITION,
    "认识图形": SubDimension.SHAPE_RECOGNITION,
    "命名": SubDimension.SHAPE_RECOGNITION,
    "变式": SubDimension.SHAPE_RECOGNITION,
    "图形特征": SubDimension.SHAPE_RECOGNITION,
    "拼搭": SubDimension.SHAPE_COMPOSITION,
    "拼图": SubDimension.SHAPE_COMPOSITION,
    "拼成": SubDimension.SHAPE_COMPOSITION,
    "拼一拼": SubDimension.SHAPE_COMPOSITION,
    "七巧板": SubDimension.SHAPE_COMPOSITION,
    "嵌板": SubDimension.SHAPE_COMPOSITION,
    "图形组合": SubDimension.SHAPE_COMPOSITION,
    "等分": SubDimension.SHAPE_COMPOSITION,
    "上下": SubDimension.SPATIAL_AWARENESS,
    "前后": SubDimension.SPATIAL_AWARENESS,
    "里外": SubDimension.SPATIAL_AWARENESS,
    "左右": SubDimension.SPATIAL_AWARENESS,
    "方位": SubDimension.SPATIAL_AWARENESS,
    "位置": SubDimension.SPATIAL_AWARENESS,
    "空间": SubDimension.SPATIAL_AWARENESS,
    "方向": SubDimension.SPATIAL_AWARENESS,
    "远近": SubDimension.SPATIAL_AWARENESS,
    "高低": SubDimension.SPATIAL_AWARENESS,
    "立体": SubDimension.SOLID_RECOGNITION,
    "球体": SubDimension.SOLID_RECOGNITION,
    "圆柱": SubDimension.SOLID_RECOGNITION,
    "正方体": SubDimension.SOLID_RECOGNITION,
    "长方体": SubDimension.SOLID_RECOGNITION,
    "面在体上": SubDimension.SOLID_RECOGNITION,
    # ── 集合与模式 ──
    "分类": SubDimension.CLASSIFICATION,
    "归类": SubDimension.CLASSIFICATION,
    "找相同": SubDimension.CLASSIFICATION,
    "集合": SubDimension.CLASSIFICATION,
    "类包含": SubDimension.CLASSIFICATION,
    "模式": SubDimension.PATTERN_RECOGNITION,
    "规律": SubDimension.PATTERN_RECOGNITION,
    "重复": SubDimension.PATTERN_RECOGNITION,
    "排列": SubDimension.PATTERN_RECOGNITION,
    "找规律": SubDimension.PATTERN_RECOGNITION,
    "扩展": SubDimension.PATTERN_EXTENSION,
    "接着": SubDimension.PATTERN_EXTENSION,
    "下一个": SubDimension.PATTERN_EXTENSION,
    "补全": SubDimension.PATTERN_EXTENSION,
    "填空": SubDimension.PATTERN_EXTENSION,
    "排序": SubDimension.SORTING,
    "从大到小": SubDimension.SORTING,
    "从小到大": SubDimension.SORTING,
    "从长到短": SubDimension.SORTING,
    "从短到长": SubDimension.SORTING,
    "排排队": SubDimension.SORTING,
    "长短": SubDimension.SORTING,
    "大小顺序": SubDimension.SORTING,
}


# Compiled once: alternation of all keywords sorted by length descending so
# the regex engine prefers the longest keyword at each position (longest-match
# disambiguation, e.g. '圆柱' wins over '圆' inside '圆柱体').
_LO_KEYWORD_SORTED = sorted(LEARNING_OBJECTIVE_KEYWORDS.keys(), key=len, reverse=True)
_LO_PATTERN = re.compile("|".join(re.escape(k) for k in _LO_KEYWORD_SORTED))


def _classify_by_keywords(text: str) -> List[str]:
    """Return de-duplicated sub-dimensions matched in `text` (ordered by enum).

    Uses a regex alternation of all keywords sorted by length descending so
    that longer keywords win at a given position (e.g. '圆柱体' matches
    '圆柱'→立体认知, not the bare '圆'→图形识别). Non-overlapping left-to-right.
    """
    if not text:
        return []
    matched = set()
    for m in _LO_PATTERN.finditer(text):
        matched.add(LEARNING_OBJECTIVE_KEYWORDS[m.group()])
    # Preserve canonical enum order for stable output
    return [sd for sd in SubDimension if sd in matched]


def classify_core_experiences(
    worksheet_text: str,
    problems: List[dict],
) -> List[Dict]:
    """
    Determine which core experiences (sub-dimensions) a worksheet targets.

    Two signals, unioned:
      - assessed: sub-dimensions actually present via problem types
        (PROBLEM_TYPE_TO_SUB_DIMENSION) — the worksheet directly tests these.
      - pointed: sub-dimensions inferred from the worksheet's printed text
        (learning objective + title + instructions) via
        LEARNING_OBJECTIVE_KEYWORDS — the worksheet intends these, even if
        no problem of that type was recognized.

    `worksheet_text` should be a combined string of the worksheet's printed
    learning_objective / title / instructions (caller assembles it); the
    longest-match regex disambiguates overlapping keywords.

    Returns a list (ordered: assessed first in enum order, then pointed-only)
    of dicts:
      {sub_dimension, dimension, source: "assessed"|"pointed"}
    """
    assessed_set = set()
    for p in problems or []:
        sd = PROBLEM_TYPE_TO_SUB_DIMENSION.get(p.get("type", ""))
        if sd:
            assessed_set.add(sd)

    pointed = _classify_by_keywords(worksheet_text)

    # Union, assessed-first, canonical enum order within each group
    targets = []
    for sd in SubDimension:
        if sd in assessed_set:
            targets.append({
                "sub_dimension": sd,
                "dimension": SUB_DIMENSION_TO_DIMENSION.get(sd, ""),
                "source": "assessed",
            })
    assessed_only = set(t["sub_dimension"] for t in targets)
    for sd in pointed:
        if sd not in assessed_only:
            targets.append({
                "sub_dimension": sd,
                "dimension": SUB_DIMENSION_TO_DIMENSION.get(sd, ""),
                "source": "pointed",
            })
    return targets


# ═══════════════════════════════════════════════════════════════════════
# New v2.0 helper functions
# ═══════════════════════════════════════════════════════════════════════

def get_sub_skill_indicator(sub_skill: str, age_group: str) -> str:
    """Get the age-anchored assessment indicator for a sub-skill."""
    try:
        return ASSESSMENT_INDICATORS.get(sub_skill, {}).get(age_group, "—")
    except Exception:
        return "—"


def get_expected_pck_stage(age_group: str, dimension: str) -> PCKStage:
    """Get the expected PCK stage for an age group × dimension combination."""
    mapping = {
        AgeGroup.SMALL: PCKStage.CONCRETE,
        AgeGroup.MIDDLE: {Dimension.COUNTING: PCKStage.SEMI_CONCRETE,
                          Dimension.ADDITION_SUBTRACTION: PCKStage.CONCRETE,
                          Dimension.SHAPES_SPACE: PCKStage.SEMI_CONCRETE,
                          Dimension.PATTERNS: PCKStage.SEMI_CONCRETE},
        AgeGroup.LARGE: {Dimension.ADDITION_SUBTRACTION: PCKStage.SEMI_CONCRETE},
    }
    if age_group == AgeGroup.SMALL:
        return PCKStage.CONCRETE
    if age_group == AgeGroup.LARGE:
        if dimension == Dimension.ADDITION_SUBTRACTION:
            return PCKStage.SEMI_CONCRETE
        return PCKStage.SYMBOLIC
    # Middle: per-dimension
    stage = mapping.get(age_group, {}).get(dimension)
    if isinstance(stage, PCKStage):
        return stage
    return PCKStage.SEMI_CONCRETE


def find_error_patterns(
    age_group: str,
    dimension: Optional[str] = None,
) -> List[Dict]:
    """Find relevant error patterns for an age group and optional dimension."""
    results = []
    for ep in ERROR_PATTERNS:
        if age_group not in ep.get("age_groups", []):
            continue
        if dimension and ep.get("dimension") != dimension:
            continue
        results.append(ep)
    return results


def get_teaching_recommendation(dimension: str, level: DevLevel) -> List[str]:
    """Get dimension-specific teaching recommendations based on development level."""
    base_recs = {
        Dimension.COUNTING: [
            "在日常活动中渗入计数练习（数筷子、水果、楼梯等）",
            "运用实物或具体教具，将数字与物体、动作相联系",
            "从小数字开始（3或5以内），逐步扩展到10、20",
            "鼓励计数中的数学交流——引导幼儿讨论、解释计数过程",
        ],
        Dimension.ADDITION_SUBTRACTION: [
            "通过实物操作和创设情境，引导幼儿用数运算解决问题",
            "遵循教学顺序：实物加减→口述应用题→列式运算",
            "借助数的组成和口述应用题，促进抽象数运算能力发展",
            "在生活和游戏中渗透数概念，体验'加'和'减'的真实意义",
        ],
        Dimension.SHAPES_SPACE: [
            "提供多样化的图形示例（旋转角度、翻转、各种变式）",
            "引导幼儿进行更加精确的图形表述——尽可能'正确'地定义图形",
            "在真实生活情境中感受空间方位（寻宝游戏、方位指令等）",
            "鼓励观察、预测、思考、描述等探索行为",
        ],
        Dimension.PATTERNS: [
            "根据年龄发展阶段开展适宜的模式活动",
            "利用多样化形式渗透模式经验（节奏、音乐、美术、体育）",
            "引导讨论'什么在重复'——从表层感知上升到核心单元抽象",
            "提供视觉、听觉、动作等多种模式的识别与转换体验",
        ],
    }

    recs = base_recs.get(dimension, ["多参与数学游戏，保持练习"])

    # Augment with level-specific guidance
    if level == DevLevel.L1_SPROUT:
        recs.insert(0, "🔑 当前处于萌芽期：以实物操作和感知体验为主，不急于符号学习")
    elif level == DevLevel.L4_ADVANCED:
        recs.append("🌟 当前处于进阶期：可提供跨年龄段的高阶挑战，如综合数学项目")

    return recs


def get_age_development_summary(age_group: str, dimension: str) -> str:
    """Get a concise development summary for a given age × dimension."""
    summaries = {
        (AgeGroup.SMALL, Dimension.COUNTING):
            "多数能唱数到10（机械记忆）；能手口一致点数5以内物体但说出总数困难；"
            "只能从1开始数，不会从中间任意数起。此阶段的核心任务是建立一一对应关系。",
        (AgeGroup.MIDDLE, Dimension.COUNTING):
            "手口一致点数10以内并说出总数——标志最初数概念形成；"
            "末期开始出现数的守恒。4-5岁是形成数概念的关键期。",
        (AgeGroup.LARGE, Dimension.COUNTING):
            "能计数到100+，发展按群计数能力；熟练说出总数；"
            "掌握相邻数关系及自然数列等差关系。5岁左右是数概念发展的质的飞跃。",
        (AgeGroup.SMALL, Dimension.ADDITION_SUBTRACTION):
            "基本不会正式加减运算；通过一一对应比较感知'变多了'还是'变少了'；"
            "以实物操作感知为主，处于动作水平。",
        (AgeGroup.MIDDLE, Dimension.ADDITION_SUBTRACTION):
            "借助实物进行10以内加减；运用点数全部或接着数策略；"
            "能进行5以内数的分解组合。实物依赖是该阶段典型特征。",
        (AgeGroup.LARGE, Dimension.ADDITION_SUBTRACTION):
            "利用表象进行10以内加减运算；出现逐一加减（顺接数和倒接数）；"
            "逐步达到按数群运算水平；理解加减互逆关系。",
        (AgeGroup.SMALL, Dimension.SHAPES_SPACE):
            "图形感知整体、笼统、模糊——将图形与熟悉物体对照（圆形叫'太阳'）；"
            "能配对和指认圆形、正方形、三角形；理解上下、前后、里外等方位。",
        (AgeGroup.MIDDLE, Dimension.SHAPES_SPACE):
            "图形范围扩大到长方形、椭圆形、梯形等；开始关注边、角特征；"
            "4岁是图形知觉敏感期；能以自身为中心区分左右。",
        (AgeGroup.LARGE, Dimension.SHAPES_SPACE):
            "头脑中形成图形'标准样式'；能在抽象水平概括图形关系（如'四边形'）；"
            "开始认识立体图形，理解'面在体上'；以客体为中心区分左右。",
        (AgeGroup.SMALL, Dimension.PATTERNS):
            "处于模式识别和复制阶段；能识别并复制简单AB模式；"
            "按单一明显外部特征分类；将相同物品配对。",
        (AgeGroup.MIDDLE, Dimension.PATTERNS):
            "处于模式复制和扩展阶段；识别ABC/AABB模式；"
            "按两个维度分类；按规律排序；理解'类包含'关系。",
        (AgeGroup.LARGE, Dimension.PATTERNS):
            "处于模式创造和转换阶段；识别/创造复杂模式（AAB/ABB/ABBA）；"
            "按事物内在属性分类；理解交集与包含关系；能跨形式转换模式。",
    }
    return summaries.get((age_group, dimension), "暂无该年龄×维度的详细发展总结")
