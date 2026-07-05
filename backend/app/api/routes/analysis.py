from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import AgeGroupEnum
from app.core.database import get_db
from app.models import AnalysisResult, Worksheet, Child
from app.core.prompts.pck_reference import (
    MILESTONES,
    ERROR_PATTERNS,
    SUB_SKILLS,
    SUB_DIMENSION_TO_DIMENSION,
    INDICATOR_EXPLANATIONS,
    AgeGroup,
    Dimension,
    SubDimension,
    DevLevel,
    PCKStage,
    CountingStage,
    COUNTING_STAGE_INFO,
    OperationStage,
    OPERATION_STAGE_INFO,
    PatternStage,
    PATTERN_STAGE_INFO,
    COUNTING_PRINCIPLES,
    TEACHING_PRINCIPLES,
    NUMBER_USE_TYPES,
    SUBTITIZING_INFO,
    get_dimension_display_name,
    get_sub_dimension_display_name,
    get_indicator_explanation,
    get_age_display_name,
    get_level_description,
    find_error_patterns,
    get_teaching_recommendation,
    PROBLEM_TYPE_TO_SUB_DIMENSION,
)

router = APIRouter()


@router.get("/demo-assessment")
async def get_demo_assessment(
    age_group: AgeGroupEnum = Query(default=AgeGroupEnum.MIDDLE),
    child_name: str = Query(default="示例幼儿"),
):
    """
    Return a dynamically generated demo assessment for frontend development.
    This does NOT call the Claude API — returns sample data anchored to the
    selected age group.

    The demo data respects:
    - Age-appropriate milestones
    - Realistic error patterns
    - Varying development levels across dimensions
    """
    age = age_group.value
    age_display = get_age_display_name(age)

    # Build demo data with grain that matches the selected age group
    demo = _build_demo(age, child_name, age_display)

    return JSONResponse(content=demo)


def _build_demo(age: str, child_name: str, age_display: str) -> dict:
    """Build a realistic demo assessment for the given age group."""

    # Age-specific scoring variations
    age_expectations = {
        AgeGroup.SMALL: {
            "counting": {"score": 65, "level": "L2", "correct": 4, "total": 6},
            "addition": {"score": 40, "level": "L1", "correct": 1, "total": 3},
            "shapes": {"score": 72, "level": "L3", "correct": 5, "total": 7},
            "patterns": {"score": 52, "level": "L2", "correct": 3, "total": 5},
        },
        AgeGroup.MIDDLE: {
            "counting": {"score": 78, "level": "L3", "correct": 8, "total": 10},
            "addition": {"score": 55, "level": "L2", "correct": 3, "total": 5},
            "shapes": {"score": 90, "level": "L3", "correct": 8, "total": 9},
            "patterns": {"score": 45, "level": "L2", "correct": 3, "total": 6},
        },
        AgeGroup.LARGE: {
            "counting": {"score": 85, "level": "L3", "correct": 12, "total": 14},
            "addition": {"score": 72, "level": "L3", "correct": 7, "total": 10},
            "shapes": {"score": 92, "level": "L4", "correct": 10, "total": 11},
            "patterns": {"score": 68, "level": "L2", "correct": 6, "total": 9},
        },
    }

    exp = age_expectations.get(age, age_expectations[AgeGroup.MIDDLE])
    milestones = MILESTONES.get(age, MILESTONES[AgeGroup.MIDDLE])

    def _milestone_text(dim: str) -> str:
        items = milestones.get(dim, [])
        return "；".join(items[:3]) if items else "暂无该年龄段数据"

    def _benchmark(score: float) -> str:
        if score >= 91:
            return f"超越{age_display}期望，核心经验已熟练掌握"
        elif score >= 71:
            return f"符合{age_display}发展期望，核心经验基本建立"
        elif score >= 41:
            return f"部分达到{age_display}期望，核心经验正在形成中"
        else:
            return f"尚未达到{age_display}期望，需加强具体实物操作经验"

    def _level_info(level: str):
        return {
            "L1": {"name": "萌芽期", "emoji": "🌱", "pck": "前运算阶段初期：依赖动作感知"},
            "L2": {"name": "发展期", "emoji": "🌿", "pck": "前运算阶段中期：半具象表征过渡"},
            "L3": {"name": "熟练期", "emoji": "🌳", "pck": "前运算阶段后期：趋于符号表征"},
            "L4": {"name": "进阶期", "emoji": "⭐", "pck": "具体运算阶段前期：符号运算萌芽"},
        }.get(level, {"name": "未知", "emoji": "❓", "pck": ""})

    def _recommendations(dim: str, level: str) -> str:
        stage_recs = {
            "L1": "建议从具体实物操作开始，通过游戏化方式帮助幼儿建立基础感知。",
            "L2": "建议在巩固实物操作基础上，逐步引入半具象材料（点卡、手指计数）。",
            "L3": "建议增加多样化变式练习，引导幼儿用语言描述思考过程。",
            "L4": "建议提供高阶挑战活动，保护数学兴趣和自信心。",
        }
        dim_recs = {
            "counting": "推荐活动：'数筷子'、'排队比一比'、'数字寻宝'。",
            "addition_sub": "推荐活动：'分水果'、'买东西'角色扮演。",
            "shapes_space": "推荐活动：'形状寻宝'、'身体方向游戏'、'积木搭建'。",
            "patterns": "推荐活动：'穿珠子'、'排队游戏'、'分类收纳'。",
        }
        return f"{stage_recs.get(level, '')} {dim_recs.get(dim, '')}"

    def _sub_skills(dim: str, base_score: float) -> list:
        skills_map = {
            "counting": ["点数准确性", "按数取物", "数量比较", "序数理解", "数的组成", "数量守恒"],
            "addition_sub": ["实物操作正确率", "符号运算正确率", "策略水平", "应用题理解", "运算思维灵活性"],
            "shapes_space": ["平面图形识别", "立体图形识别", "图形特征描述", "空间方位", "图形组合与分解"],
            "patterns": ["分类能力", "模式识别", "模式扩展", "模式创造", "排序能力", "规律语言描述"],
        }
        import hashlib
        results = []
        for name in skills_map.get(dim, []):
            seed = int(hashlib.md5(name.encode()).hexdigest()[:4], 16)
            variance = (seed % 21) - 10  # -10 to +10
            s = max(0, min(100, base_score + variance))
            results.append({"name": name, "score": round(s, 1), "max_score": 100.0})
        return results

    def _demo_dimension_problems() -> dict:
        """Fabricate per-dimension problem details so the demo experience
        matches a real upload (expandable problem list + dimension analysis).
        Correct/total counts are consistent with the age-specific expectations.
        """
        # Realistic problem templates per dimension
        templates = {
            "counting": {
                "type": "counting",
                "type_name": "点数",
                "items": [("🍎🍎🍎🍎", "4"), ("🍌🍌🍌", "3"), ("⚽⚽⚽⚽⚽", "5"), ("🍓🍓", "2"), ("🍇🍇🍇🍇", "4"), ("🥕🥕🥕🥕🥕🥕", "6")],
            },
            "addition_sub": {
                "type": "add_10",
                "type_name": "加法",
                "items": [("2 + 1", "3"), ("1 + 3", "4"), ("2 + 2", "4"), ("3 + 2", "5"), ("1 + 4", "5")],
            },
            "shapes_space": {
                "type": "shape_id",
                "type_name": "图形识别",
                "items": [("⚪圆形", "圆形"), ("🟦正方形", "正方形"), ("🔺三角形", "三角形"), ("⭐星形", "星形"), ("🟩长方形", "长方形"), ("⬟六边形", "六边形"), ("🔷菱形", "菱形")],
            },
            "patterns": {
                "type": "pattern_next",
                "type_name": "找规律",
                "items": [("🔴🔵🔴🔵🔴 ?", "🔵"), ("🔺⭐🔺⭐🔺 ?", "⭐"), ("🍎🍎🍐🍎🍎🍐🍎 ?", "🍎"), ("1 2 1 2 1 ?", "2"), ("⬆️⬇️⬆️⬇️⬆️ ?", "⬇️"), ("🌕🌑🌕🌑 ?", "🌕")],
            },
        }
        dim_order = ["counting", "addition", "shapes", "patterns"]
        dim_key_map = {"counting": "counting", "addition": "addition_sub", "shapes": "shapes_space", "patterns": "patterns"}
        dim_name_map = {"counting": "数概念与运算", "addition_sub": "数运算能力", "shapes_space": "图形与空间", "patterns": "集合与模式"}
        dim_analysis_map = {
            "counting": "点数准确性是数概念基础；该幼儿在实物点数方面表现稳定，建议通过'按数取物'游戏巩固基数意义理解。",
            "addition_sub": "实物操作阶段是加减运算的关键过渡；建议继续借助实物/手指等半具象材料，逐步过渡到符号运算。",
            "shapes_space": "图形识别能力发展良好；可增加图形拼搭与空间方位描述活动，促进空间想象力发展。",
            "patterns": "模式识别处于AB水平；建议通过分类、排序活动强化属性辨识，引导幼儿用语言描述规律。",
        }

        result = {}
        for dim_short in dim_order:
            exp_data = exp[dim_short]
            dim_key = dim_key_map[dim_short]
            tmpl = templates[dim_key]
            total = exp_data["total"]
            correct = exp_data["correct"]
            items = tmpl["items"][:total] if len(tmpl["items"]) >= total else tmpl["items"]
            # Pad if not enough items
            while len(items) < total:
                items.append(tmpl["items"][len(items) % len(tmpl["items"])])
            problems = []
            for i, (prompt, answer) in enumerate(items):
                is_correct = i < correct
                # Wrong answers: a plausible distractor
                wrong = str(int(answer) + 1) if answer.isdigit() else (answer + "？")
                problems.append({
                    "id": f"{dim_short[0].upper()}{i+1}",
                    "type": tmpl["type"],
                    "type_name": tmpl["type_name"],
                    "child_answer": answer if is_correct else wrong,
                    "correct_answer": answer,
                    "is_correct": is_correct,
                    "handwriting_quality": "clear",
                    "strategy": "counting_objects" if dim_key == "addition_sub" else "",
                })
            result[dim_key] = {
                "display_name": dim_name_map[dim_key],
                "score": float(exp_data["score"]),
                "level": exp_data["level"],
                "level_name": _level_info(exp_data["level"])["name"],
                "correct_count": correct,
                "total_count": total,
                "problems": problems,
                "dimension_analysis": dim_analysis_map[dim_key],
            }
        return result

    return {
        "child_name": child_name,
        "age_group": age,
        "age_display": age_display,
        "assessment": [
            {
                "dimension": "counting",
                "display_name": "数概念与运算",
                "score": float(exp["counting"]["score"]),
                "level": exp["counting"]["level"],
                "level_name": _level_info(exp["counting"]["level"])["name"],
                "level_emoji": _level_info(exp["counting"]["level"])["emoji"],
                "pck_stage": _level_info(exp["counting"]["level"])["pck"],
                "sub_skills": _sub_skills("counting", exp["counting"]["score"]),
                "error_patterns": [],
                "age_benchmark_comparison": _benchmark(exp["counting"]["score"]),
                "age_milestones": _milestone_text("counting"),
                "recommendations": _recommendations("counting", exp["counting"]["level"]),
                "score_details": {
                    "correct": exp["counting"]["correct"],
                    "total": exp["counting"]["total"],
                    "strategy_level": "semi_concrete",
                },
            },
            {
                "dimension": "addition_sub",
                "display_name": "数运算能力",
                "score": float(exp["addition"]["score"]),
                "level": exp["addition"]["level"],
                "level_name": _level_info(exp["addition"]["level"])["name"],
                "level_emoji": _level_info(exp["addition"]["level"])["emoji"],
                "pck_stage": _level_info(exp["addition"]["level"])["pck"],
                "sub_skills": _sub_skills("addition_sub", exp["addition"]["score"]),
                "error_patterns": (
                    ["实物依赖：不用实物就不会算"]
                    if exp["addition"]["level"] in ["L1", "L2"]
                    else []
                ),
                "age_benchmark_comparison": _benchmark(exp["addition"]["score"]),
                "age_milestones": _milestone_text("addition_sub"),
                "recommendations": _recommendations("addition_sub", exp["addition"]["level"]),
                "score_details": {
                    "correct": exp["addition"]["correct"],
                    "total": exp["addition"]["total"],
                    "strategy_level": "concrete_objects",
                },
            },
            {
                "dimension": "shapes_space",
                "display_name": "图形与空间",
                "score": float(exp["shapes"]["score"]),
                "level": exp["shapes"]["level"],
                "level_name": _level_info(exp["shapes"]["level"])["name"],
                "level_emoji": _level_info(exp["shapes"]["level"])["emoji"],
                "pck_stage": _level_info(exp["shapes"]["level"])["pck"],
                "sub_skills": _sub_skills("shapes_space", exp["shapes"]["score"]),
                "error_patterns": [],
                "age_benchmark_comparison": _benchmark(exp["shapes"]["score"]),
                "age_milestones": _milestone_text("shapes_space"),
                "recommendations": _recommendations("shapes_space", exp["shapes"]["level"]),
                "score_details": {
                    "correct": exp["shapes"]["correct"],
                    "total": exp["shapes"]["total"],
                    "strategy_level": "symbolic",
                },
            },
            {
                "dimension": "patterns",
                "display_name": "集合与模式",
                "score": float(exp["patterns"]["score"]),
                "level": exp["patterns"]["level"],
                "level_name": _level_info(exp["patterns"]["level"])["name"],
                "level_emoji": _level_info(exp["patterns"]["level"])["emoji"],
                "pck_stage": _level_info(exp["patterns"]["level"])["pck"],
                "sub_skills": _sub_skills("patterns", exp["patterns"]["score"]),
                "error_patterns": (
                    ["模式理解表面化", "分类标准漂移"]
                    if exp["patterns"]["level"] in ["L1", "L2"]
                    else []
                ),
                "age_benchmark_comparison": _benchmark(exp["patterns"]["score"]),
                "age_milestones": _milestone_text("patterns"),
                "recommendations": _recommendations("patterns", exp["patterns"]["level"]),
                "score_details": {
                    "correct": exp["patterns"]["correct"],
                    "total": exp["patterns"]["total"],
                    "strategy_level": "AB_copy",
                },
            },
        ],
        "observations": {
            "number_formation_issues": (
                ["mirror_3"] if age in [AgeGroup.SMALL, AgeGroup.MIDDLE] else []
            ),
            "attention_indicators": "careful",
            "task_completion_context": "independent",
            "overall_pck_notes": (
                f"该{age_display}幼儿在点数和图形识别方面表现良好，"
                f"符合{age_display}典型发展特征。"
                f"这是基于演示数据的PCK分析。"
            ),
        },
        "overall_summary": (
            f"这是一份关于{child_name}（{age_display}）数学操作单的观察分析。"
            f"在各维度均处于自然发展阶段。"
            f"每个孩子都有自己独特的发展节奏，"
            f"建议结合日常观察全面了解幼儿的发展。"
        ),
    }


# ─── PCK Framework API ────────────────────────────────────────────────

@router.get("/pck-framework")
async def get_pck_framework():
    """
    Return the full PCK (Pedagogical Content Knowledge) framework data
    for frontend visualization. All data sourced from the textbook:
    《学前儿童数学学习与发展核心经验》(黄瑾、田方, 2015)

    Returns:
    - dimensions: 4 main dimensions with sub-dimensions
    - development_stages: counting/operation/pattern stage models
    - teaching_principles: cross-dimensional teaching principles
    - indicator_explanations: per sub-dim × age group details
    - error_patterns: full catalog
    - counting_principles: Gelman & Gallistel's 5 principles
    """
    # Build dimension + sub-dimension tree
    dims = []
    for dim in Dimension:
        sub_dims = [
            {
                "key": sd.value,
                "name": get_sub_dimension_display_name(sd),
            }
            for sd in SubDimension
            if SUB_DIMENSION_TO_DIMENSION.get(sd) == dim
        ]
        dims.append({
            "key": dim.value,
            "name": get_dimension_display_name(dim),
            "sub_dimensions": sub_dims,
            "sub_skills": SUB_SKILLS.get(dim, []),
            "milestones_by_age": {
                age: MILESTONES.get(age, {}).get(dim, [])
                for age in [AgeGroup.SMALL, AgeGroup.MIDDLE, AgeGroup.LARGE]
            },
        })

    # Build indicator explanations (simplified for frontend)
    indicator_data = {}
    for sd in SubDimension:
        sd_key = sd.value
        indicator_data[sd_key] = {
            "name": get_sub_dimension_display_name(sd),
            "by_age": {},
        }
        for age in [AgeGroup.SMALL, AgeGroup.MIDDLE, AgeGroup.LARGE]:
            exp = get_indicator_explanation(sd, age)
            if exp:
                indicator_data[sd_key]["by_age"][age] = exp

    return {
        "dimensions": dims,
        "indicator_explanations": indicator_data,
        "development_stages": {
            "counting": {
                "stages": [
                    {"key": s.value, "name": COUNTING_STAGE_INFO[s]["name"],
                     "age": COUNTING_STAGE_INFO[s]["age"],
                     "description": COUNTING_STAGE_INFO[s]["description"]}
                    for s in CountingStage
                ],
            },
            "operation": {
                "stages": [
                    {"key": s.value, "name": OPERATION_STAGE_INFO[s]["name"],
                     "age": OPERATION_STAGE_INFO[s]["age"],
                     "description": OPERATION_STAGE_INFO[s]["description"]}
                    for s in OperationStage
                ],
            },
            "pattern": {
                "stages": [
                    {"key": s.value, "name": PATTERN_STAGE_INFO[s]["name"],
                     "age_anchor": PATTERN_STAGE_INFO[s]["age_anchor"],
                     "description": PATTERN_STAGE_INFO[s]["description"]}
                    for s in PatternStage
                ],
            },
        },
        "teaching_principles": TEACHING_PRINCIPLES,
        "error_patterns": [
            {
                "id": ep["id"],
                "name": ep["name"],
                "description": ep["description"],
                "dimension": ep["dimension"],
                "age_groups": ep["age_groups"],
                "teaching_implication": ep["teaching_implication"],
            }
            for ep in ERROR_PATTERNS
        ],
        "counting_principles": COUNTING_PRINCIPLES,
        "number_use_types": NUMBER_USE_TYPES,
        "subitizing_info": SUBTITIZING_INFO,
        "age_groups": [
            {"key": AgeGroup.SMALL, "name": get_age_display_name(AgeGroup.SMALL)},
            {"key": AgeGroup.MIDDLE, "name": get_age_display_name(AgeGroup.MIDDLE)},
            {"key": AgeGroup.LARGE, "name": get_age_display_name(AgeGroup.LARGE)},
        ],
    }


@router.get("/evaluation-trace")
async def get_evaluation_trace(
    worksheet_type: str = "counting",
    age_group: str = "middle",
    child_name: str = "示例幼儿",
):
    """
    Generate an evaluation trace demo showing how the AI maps each problem
    to specific PCK indicators. Uses demo data for frontend development.

    In production, this would be called with a real analysis result ID.
    """
    from app.services.assessment_engine import generate_evaluation_trace

    # Build demo vision result based on worksheet_type
    demo_problems = {
        "counting": [
            {"id": "P1", "type": "counting", "child_answer": "5", "correct_answer": "5",
             "is_correct": True, "confidence": 0.95, "handwriting_quality": "clear",
             "has_erasure": False, "strategy_indicators": "counting_fingers"},
            {"id": "P2", "type": "counting", "child_answer": "3", "correct_answer": "3",
             "is_correct": True, "confidence": 0.9, "handwriting_quality": "clear",
             "has_erasure": False, "strategy_indicators": "mental"},
            {"id": "P3", "type": "compare", "child_answer": "左边多", "correct_answer": "左边多",
             "is_correct": True, "confidence": 0.85, "handwriting_quality": "clear",
             "has_erasure": False, "strategy_indicators": "counting_objects"},
            {"id": "P4", "type": "counting", "child_answer": "4", "correct_answer": "6",
             "is_correct": False, "confidence": 0.8, "handwriting_quality": "messy",
             "has_erasure": True, "erasure_pattern": "persistent_error",
             "strategy_indicators": "counting_fingers"},
        ],
        "shapes": [
            {"id": "P1", "type": "shape_id", "child_answer": "圆形", "correct_answer": "圆形",
             "is_correct": True, "confidence": 0.95, "handwriting_quality": "clear",
             "has_erasure": False, "strategy_indicators": "mental"},
            {"id": "P2", "type": "shape_id", "child_answer": "正方形", "correct_answer": "正方形",
             "is_correct": True, "confidence": 0.9, "handwriting_quality": "clear",
             "has_erasure": False, "strategy_indicators": "mental"},
            {"id": "P3", "type": "shape_id", "child_answer": "长方形", "correct_answer": "三角形",
             "is_correct": False, "confidence": 0.7, "handwriting_quality": "clear",
             "has_erasure": False, "strategy_indicators": ""},
            {"id": "P4", "type": "spatial", "child_answer": "上面", "correct_answer": "上面",
             "is_correct": True, "confidence": 0.85, "handwriting_quality": "clear",
             "has_erasure": False, "strategy_indicators": "mental"},
        ],
        "patterns": [
            {"id": "P1", "type": "classify", "child_answer": "按颜色分", "correct_answer": "按颜色分",
             "is_correct": True, "confidence": 0.9, "handwriting_quality": "clear",
             "has_erasure": False, "strategy_indicators": "mental"},
            {"id": "P2", "type": "pattern_next", "child_answer": "红色", "correct_answer": "红色",
             "is_correct": True, "confidence": 0.85, "handwriting_quality": "clear",
             "has_erasure": False, "strategy_indicators": "AB_copy"},
            {"id": "P3", "type": "sort", "child_answer": "小中大", "correct_answer": "小中大",
             "is_correct": True, "confidence": 0.8, "handwriting_quality": "clear",
             "has_erasure": False, "strategy_indicators": "mental"},
        ],
    }

    problems = demo_problems.get(worksheet_type, demo_problems["counting"])

    demo_vision_result = {
        "problems": problems,
        "worksheet_type": worksheet_type,
        "observations": {
            "number_formation_issues": [],
            "attention_indicators": "careful",
            "task_completion_context": "independent",
            "overall_pck_notes": "演示数据 — 幼儿在大多数题目上表现良好。",
        },
        "dimension_scores_preliminary": {},
    }

    trace = generate_evaluation_trace(demo_vision_result, age_group, child_name)
    return trace


# ─── Real Evaluation Trace (from persisted analysis) ──────────────────

@router.get("/{analysis_id}/evaluation-trace")
async def get_real_evaluation_trace(
    analysis_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve the evaluation trace for a previously analyzed worksheet.

    Queries the persisted AnalysisResult to get the raw vision recognition data,
    then runs the same generate_evaluation_trace() logic used by the demo endpoint,
    producing a per-problem trace with PCK indicator matching and evidence.

    This is the production version — no demo data.
    """
    from app.services.assessment_engine import generate_evaluation_trace

    # Query AnalysisResult
    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.id == analysis_id)
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail=f"分析结果未找到 (ID: {analysis_id})")

    # Get vision result from raw_response
    raw_response = analysis.raw_response
    if not raw_response or "problems" not in raw_response:
        raise HTTPException(
            status_code=422, detail="该分析结果不包含有效的操作单识别数据"
        )

    age_group = analysis.age_group_anchor or "middle"

    # Look up child name via worksheet → child
    child_name = "幼儿"
    if analysis.worksheet_id:
        ws_result = await db.execute(
            select(Worksheet).where(Worksheet.id == analysis.worksheet_id)
        )
        worksheet = ws_result.scalar_one_or_none()
        if worksheet and worksheet.child_id:
            child_result = await db.execute(
                select(Child).where(Child.id == worksheet.child_id)
            )
            child = child_result.scalar_one_or_none()
            if child:
                child_name = child.name

    trace = generate_evaluation_trace(raw_response, age_group, child_name)
    trace["analysis_id"] = analysis_id
    trace["from_real_data"] = True
    return trace
