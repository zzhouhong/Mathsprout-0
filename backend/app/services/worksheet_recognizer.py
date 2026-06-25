"""
LLM Vision API worksheet recognition service.
Supports both Anthropic native API (Claude Vision) and OpenAI-compatible providers.

Core responsibilities:
- Build system prompt with PCK framework from reference data
- Call Vision API with structured JSON output
- Parse and validate vision recognition response
- Track token usage and cost
- Retry with exponential backoff on transient failures
"""

import json
import asyncio
import base64
import hashlib
from typing import Optional, Dict, Any, Union
from openai import (
    AsyncOpenAI,
    APIStatusError as OpenAIStatusError,
    APITimeoutError as OpenAITimeoutError,
    APIConnectionError as OpenAIConnectionError,
    RateLimitError as OpenAIRateLimitError,
    InternalServerError as OpenAIInternalServerError,
)
import anthropic
from app.core.config import get_settings
from app.core.prompts.pck_reference import (
    MILESTONES,
    ERROR_PATTERNS,
    AgeGroup,
    Dimension,
    get_age_display_name,
    get_dimension_display_name,
)
from app.services.cache_service import LRUDict

settings = get_settings()

# ─── Retry configuration ─────────────────────────────────────────────

MAX_RETRIES = 3
BASE_DELAY_SECONDS = 2.0
MAX_DELAY_SECONDS = 30.0

# Transient errors worth retrying (OpenAI SDK)
OPENAI_RETRYABLE = (
    OpenAITimeoutError, OpenAIConnectionError, OpenAIRateLimitError, OpenAIInternalServerError
)

# Transient errors worth retrying (Anthropic SDK)
ANTHROPIC_RETRYABLE = (
    anthropic.APITimeoutError,
    anthropic.APIConnectionError,
    anthropic.RateLimitError,
    anthropic.InternalServerError,
)

# ─── Provider detection ──────────────────────────────────────────────

def _is_anthropic_provider() -> bool:
    """Detect if the configured provider is Anthropic (not OpenAI-compatible)."""
    base = (settings.VISION_BASE_URL or "").lower()
    return "anthropic.com" in base or "claude" in base


# ─── Prompt cache (module-level, keyed by age_group) ──────────────────
_prompt_cache: Dict[str, str] = {}


def _build_system_prompt(age_group: Optional[str] = None) -> str:
    """
    Build the system prompt embedding PCK framework knowledge.

    Optimizations (P0.2-P0.4):
    - Age-filtered error patterns (~40% token reduction)
    - Deduplicated mirror writing instructions
    - Compressed JSON format (single-language field names)
    - Few-shot examples for output anchoring
    - Chain-of-thought reasoning steps
    - Module-level prompt cache by age_group
    """
    cache_key = age_group or "__no_age__"
    if cache_key in _prompt_cache:
        return _prompt_cache[cache_key]

    # ── Age-specific milestone context ──
    age_context = ""
    if age_group and age_group in MILESTONES:
        milestones = MILESTONES[age_group]
        age_display = get_age_display_name(age_group)
        age_context = f"\n当前幼儿年龄段：{age_display}\n"
        age_context += "该年龄段在各维度的期望表现：\n"
        for dim, items in milestones.items():
            dim_name = get_dimension_display_name(dim)
            age_context += f"【{dim_name}】\n"
            for item in items:
                age_context += f"  - {item}\n"

    # ── Age-filtered error patterns ──
    filtered_patterns = ERROR_PATTERNS
    if age_group:
        filtered_patterns = [
            ep for ep in ERROR_PATTERNS
            if age_group in ep.get("age_groups", [])
        ]
    error_ref = "\n幼儿常见错误模式及其发展性含义：\n"
    for ep in filtered_patterns:
        error_ref += (
            f"- {ep['name']}（{ep['description']}）："
            f"{ep['teaching_implication']}\n"
        )

    prompt = f"""你是一位幼儿园数学教育PCK（学科教学知识）分析师。你精通《学前儿童数学学习与发展核心经验》框架，理解各年龄段幼儿数学发展里程碑和典型错误模式。

## 任务
分析幼儿数学操作单（照片/扫描件），识别每道题目的类型、幼儿答案、正确性，并基于PCK框架提供观察分析。

## 重要原则（基于《幼儿园保育教育质量评估指南》）
1. 操作单是幼儿**自然学习活动的产出**，不是标准化测试
2. 关注**解题过程痕迹**（擦除、策略痕迹），而非仅看对错
3. 镜像书写（3→ε、5→ϱ、7→⅃）是正常视觉运动发展现象，不视为数学错误——若答案意图正确但书写镜像，is_correct应为true，在number_formation_issues中记录
4. 区分中文数字"一二三"和阿拉伯数字"123"
5. 使用鼓励性、成长性语言
6. **⚠️ 如果操作单上没有任何幼儿书写痕迹或答案（空白/未作答），必须在overall_pck_notes中明确说明"操作单未完成"**，problems数组为空，worksheet_type为"incomplete"，所有dimension_scores_preliminary为空

## 思考步骤（请按此顺序逐步分析）
步骤0 — **读取操作单印刷文字**：仔细阅读操作单上印刷的标题、学习目标、操作说明。这些文字直接告诉你题目的教学意图。例如：
  - 标题"感知三角形的多种变式"→ shapes_space（图形感知，非数数）
  - 标题"数一数有几个"→ counting（点数）
  - 目标"在拼搭中体会图形的翻转和位置变化"→ shapes_space（空间感知）
  - 目标"能手口一致地点数5以内物体"→ counting（点数）
步骤1 — 整体观察：识别操作单类型、布局、题目数量和幼儿完成度
步骤2 — 逐题分析：读取每道题幼儿的手写答案，与标准答案对比
步骤3 — 书写质量：检查镜像书写、擦除痕迹、数字书写规范性
步骤4 — 策略识别：观察解题策略痕迹（数手指、画标记、心算、实物操作）
步骤5 — **维度映射（核心要求）**：将每道题精确映射到PCK四维度之一，并标注映射依据
  - **题型→维度映射规则**：
    - 点数/按数取物/数量比较/序数 → 数概念与运算(counting)
    - 加法/减法 → 数运算能力(addition_sub)
    - 图形识别/空间方位 → 图形与空间(shapes_space)
    - 分类/模式规律/排序 → 集合与模式(patterns)
  - **只输出实际有题目的维度**，空维度不出现
  - 若某题同时涉及两个维度（如既有分类又有排序），选择**最主要的PCK维度**归类

## 常见维度归类错误（避免以下错误）
- ❌ 将"比较多少"归为"加减"——比较题属于counting而非addition_sub
- ❌ 将"按颜色形状分类"归为"图形"——按颜色分属于patterns而非shapes_space
- ❌ 将"排序"归为"数数"——排序题属于patterns而非counting
- ❌ 将"找规律/模式接龙"归为"加减"——模式扩展属于patterns而非addition_sub

## PCK知识库
{age_context}
{error_ref}

## 示例（Few-Shot 参考，覆盖四维度）

示例1 — 数数操作单（小班）：
题型：点数（counting）| 幼儿答案: "4" | 标准答案: "4" | 正确
维度映射依据：点数题→一一对应点数→数概念与运算维度
输出：{{"worksheet_type":"counting","problems":[{{"id":"P1","type":"counting","child_answer":"4","correct_answer":"4","is_correct":true,"confidence":0.95,"handwriting_quality":"clear","has_erasure":false,"strategy_indicators":"counting_fingers"}}],"observations":{{"number_formation_issues":[],"attention_indicators":"careful","task_completion_context":"independent","overall_pck_notes":"幼儿能手口一致地点数5以内物体并准确说出总数，符合小班数数期望。维度映射：点数→counting。"}},"dimension_scores_preliminary":{{"counting":{{"correct":1,"total":1,"error_patterns":[]}}}}}}

示例2 — 图形操作单（中班）：
题型：图形识别（shapes_space）| 幼儿答案: "正方形" | 标准答案: "正方形" | 正确
维度映射依据：图形识别→形状命名→图形与空间维度
输出：{{"worksheet_type":"shapes","problems":[{{"id":"P1","type":"shape_id","child_answer":"正方形","correct_answer":"正方形","is_correct":true,"confidence":0.9,"handwriting_quality":"clear","has_erasure":false,"strategy_indicators":"mental"}}],"observations":{{"number_formation_issues":[],"attention_indicators":"completed_all","task_completion_context":"independent","overall_pck_notes":"幼儿能准确识别并命名常见平面图形，符合中班图形认知期望。维度映射：图形命名→shapes_space。"}},"dimension_scores_preliminary":{{"shapes_space":{{"correct":1,"total":1,"spatial_errors":[]}}}}}}

示例3 — 加减操作单（大班）：
题型：实物加法（addition_sub）| 幼儿答案: "5" | 标准答案: "3+2=5" | 正确
维度映射依据：实物操作→加减运算→数运算能力维度
输出：{{"worksheet_type":"addition","problems":[{{"id":"P1","type":"add_10","child_answer":"5","correct_answer":"3+2=5","is_correct":true,"confidence":0.85,"handwriting_quality":"clear","has_erasure":false,"strategy_indicators":"counting_objects"}}],"observations":{{"number_formation_issues":[],"attention_indicators":"completed_all","task_completion_context":"independent","overall_pck_notes":"幼儿借助实物操作进行10以内加减，符合大班实物运算期望。维度映射：加法→addition_sub。"}},"dimension_scores_preliminary":{{"addition_subtraction":{{"correct":1,"total":1,"strategy_level":"concrete_objects"}}}}}}

示例4 — 模式操作单（中班）：
题型：模式规律（patterns）| 幼儿答案: "红色" | 标准答案: "红色" | 正确
维度映射依据：模式识别→规律扩展→集合与模式维度
输出：{{"worksheet_type":"patterns","problems":[{{"id":"P1","type":"pattern_next","child_answer":"红色","correct_answer":"红色","is_correct":true,"confidence":0.8,"handwriting_quality":"clear","has_erasure":false,"strategy_indicators":"AB_copy"}}],"observations":{{"number_formation_issues":[],"attention_indicators":"completed_all","task_completion_context":"independent","overall_pck_notes":"幼儿能识别并复制简单AB模式，符合中班模式识别期望。维度映射：模式识别→patterns。"}},"dimension_scores_preliminary":{{"patterns":{{"correct":1,"total":1,"pattern_level":"AB_copy_only"}}}}}}

## 输出格式
严格按以下JSON结构输出（纯JSON，不含```json标记）。**务必只包含实际有题目的维度，空维度不出现在dimension_scores_preliminary中**：

{{"worksheet_type":"counting|addition|subtraction|shapes|patterns|mixed","age_group_hint":"small|middle|large","problems":[{{"id":"P1","type":"题目类型（见上方映射规则）","child_answer":"幼儿实际写的答案","correct_answer":"标准答案","is_correct":true,"confidence":0.0-1.0,"handwriting_quality":"clear|messy|illegible|mirrored","has_erasure":true,"erasure_pattern":"none|self_correct|persistent_error","strategy_indicators":"counting_fingers|drawing_marks|mental|counting_objects"}}],"observations":{{"learning_objective":"从操作单印刷文字提取的学习目标（如'感知三角形的多种变式'），若无则填'未标注'","number_formation_issues":["mirror_3"],"attention_indicators":"completed_all|skipped|rushed|careful","task_completion_context":"independent|with_prompts|teacher_assisted","overall_pck_notes":"基于PCK框架的整体观察分析（2-3句话），必须包含维度映射依据"}},"dimension_scores_preliminary":{{"counting":{{"correct":0,"total":0,"error_patterns":[]}},"addition_subtraction":{{"correct":0,"total":0,"strategy_level":"concrete_objects|semi_concrete|symbolic"}},"shapes_space":{{"correct":0,"total":0,"spatial_errors":[]}},"patterns":{{"correct":0,"total":0,"pattern_level":"AB_copy_only|AB_extend|ABC_create"}}}}}}

请基于图片内容，按思考步骤逐步分析后输出JSON。"""


    _prompt_cache[cache_key] = prompt
    return prompt


def _compute_image_hash(image_data: bytes) -> str:
    """Compute a SHA-256 hash of image data for deduplication."""
    return hashlib.sha256(image_data).hexdigest()


def _parse_response(text: Optional[str]) -> dict:
    """Parse the LLM's JSON response, handling common formatting issues."""
    if text is None:
        raise ValueError("AI 响应为空。请检查 API Key 是否有效、账户是否有额度。")
    if not text.strip():
        raise ValueError("AI 返回了空响应内容。")

    # Strip markdown code block wrappers
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    # Try direct parse
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    brace_start = cleaned.find("{")
    brace_end = cleaned.rfind("}")
    if brace_start >= 0 and brace_end > brace_start:
        try:
            return json.loads(cleaned[brace_start:brace_end + 1])
        except json.JSONDecodeError:
            pass

    # Last resort: try to fix common issues
    try:
        import re
        fixed = re.sub(r"'([^']*)':", r'"\1":', cleaned)
        fixed = re.sub(r":\s*'([^']*)'", r': "\1"', fixed)
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    raise ValueError(f"无法解析 AI 响应为 JSON。原始响应前200字符: {text[:200]}")


class WorksheetRecognizer:
    """Service for recognizing and analyzing worksheets using Vision LLM API.

    Supports two provider modes:
    - Anthropic native: uses anthropic SDK (Claude Vision models)
    - OpenAI-compatible: uses openai SDK (any provider with compatible API)
    """

    def __init__(self):
        self.model = settings.VISION_MODEL
        self._result_cache = LRUDict(max_size=64)  # LRU cache for recognition results

        # Detect provider and create appropriate client
        if _is_anthropic_provider():
            self._provider = "anthropic"
            self.client = anthropic.AsyncAnthropic(
                api_key=settings.VISION_API_KEY,
                base_url=settings.VISION_BASE_URL or None,
            )
        else:
            self._provider = "openai_compatible"
            self.client = AsyncOpenAI(
                api_key=settings.VISION_API_KEY,
                base_url=settings.VISION_BASE_URL,
            )

    async def analyze(
        self,
        image_data: bytes,
        age_group: Optional[str] = None,
        use_cache: bool = True,
    ) -> dict:
        """
        Analyze a worksheet image using Vision LLM API.

        Args:
            image_data: Processed PNG image bytes
            age_group: Optional age group hint (small/middle/large)
            use_cache: Whether to use in-memory cache for identical images

        Returns:
            Structured recognition result dict

        Raises:
            RuntimeError: After all retries are exhausted
        """
        # Check cache
        image_hash = _compute_image_hash(image_data)
        if use_cache and image_hash in self._result_cache:
            cached = self._result_cache[image_hash]
            result = dict(cached)  # shallow copy
            result["_meta"] = dict(result.get("_meta", {}))
            result["_meta"]["cache_hit"] = True
            return result

        # Build system prompt
        system_prompt = _build_system_prompt(age_group)

        # Encode image
        base64_image = base64.b64encode(image_data).decode("utf-8")

        # Pick the right retryable errors for the provider
        if self._provider == "anthropic":
            retryable = ANTHROPIC_RETRYABLE
            status_error_cls = anthropic.APIStatusError
        else:
            retryable = OPENAI_RETRYABLE
            status_error_cls = OpenAIStatusError

        # Call with retry logic
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await self._call_llm(system_prompt, base64_image)

                # Extract the text response and usage metadata
                if self._provider == "anthropic":
                    # Anthropic response: content is a list of blocks
                    text_content = _extract_anthropic_text(response)
                    usage = _extract_anthropic_usage(response)
                    model_name = response.model
                else:
                    # OpenAI-compatible response
                    text_content = response.choices[0].message.content
                    usage = {
                        "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "output_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0,
                    }
                    model_name = response.model

                if not text_content:
                    raise ValueError("AI API 返回了空的文本内容。")
                result = _parse_response(text_content)

                # Attach usage metadata
                result["_meta"] = {
                    "model": model_name,
                    "retry_attempt": attempt,
                    "usage": usage,
                    "provider": self._provider,
                }

                # Ensure required fields exist
                result.setdefault("problems", [])
                result.setdefault("observations", {})
                result.setdefault("dimension_scores_preliminary", {})
                result.setdefault("worksheet_type", "unknown")

                # Cache the result
                if use_cache:
                    self._result_cache[image_hash] = result

                return result

            except retryable as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    delay = min(
                        BASE_DELAY_SECONDS * (2 ** attempt),
                        MAX_DELAY_SECONDS,
                    )
                    print(
                        f"[WorksheetRecognizer] 重试 {attempt + 1}/{MAX_RETRIES}，"
                        f"等待 {delay:.1f}s，原因: {type(e).__name__}"
                    )
                    await asyncio.sleep(delay)
                else:
                    raise RuntimeError(
                        f"AI API 调用失败，已重试 {MAX_RETRIES} 次。"
                        f"最后错误: {type(last_error).__name__}: {str(last_error)}"
                    ) from last_error

            except (json.JSONDecodeError, ValueError) as e:
                # JSON parse errors — retry
                if attempt < MAX_RETRIES:
                    delay = BASE_DELAY_SECONDS * (2 ** attempt)
                    await asyncio.sleep(delay)
                    last_error = e
                else:
                    # Return partial result on final attempt
                    return {
                        "worksheet_type": "unknown",
                        "problems": [],
                        "observations": {
                            "number_formation_issues": [],
                            "attention_indicators": "unknown",
                            "task_completion_context": "unknown",
                            "overall_pck_notes": (
                                f"AI 响应解析失败（已重试{MAX_RETRIES}次）: {str(e)}"
                            ),
                        },
                        "dimension_scores_preliminary": {},
                        "_meta": {
                            "model": self.model,
                            "error": str(e),
                            "parse_failed": True,
                            "provider": self._provider,
                        },
                    }

            except status_error_cls as e:
                # Non-retryable API errors
                if e.status_code == 400:
                    raise RuntimeError(
                        f"AI API 请求无效 (400): {str(e)}。请检查图片格式和大小。"
                    ) from e
                elif e.status_code == 401:
                    raise RuntimeError(
                        "AI API 密钥无效 (401)。请检查 ANTHROPIC_API_KEY 配置。"
                    ) from e
                elif e.status_code == 413:
                    raise RuntimeError(
                        "图片过大 (413)。请使用较小的图片或降低分辨率。"
                    ) from e
                elif e.status_code == 429:
                    raise RuntimeError(
                        f"AI API 速率限制 (429): {str(e)}。请稍后重试。"
                    ) from e
                else:
                    raise RuntimeError(
                        f"AI API 错误 (HTTP {e.status_code}): {str(e)}"
                    ) from e

        # Should not reach here
        raise RuntimeError(f"未知错误: {str(last_error)}")

    async def _call_llm(
        self, system_prompt: str, base64_image: str
    ) -> Any:
        """Dispatch to the right API implementation based on provider."""
        if self._provider == "anthropic":
            return await self._call_anthropic(system_prompt, base64_image)
        else:
            return await self._call_openai_compatible(system_prompt, base64_image)

    async def _call_anthropic(
        self, system_prompt: str, base64_image: str
    ) -> Any:
        """Call Anthropic Vision API using the native anthropic SDK."""
        return await self.client.messages.create(
            model=self.model,
            max_tokens=settings.VISION_MAX_TOKENS,
            timeout=settings.VISION_TIMEOUT_SECONDS,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": "请分析这张幼儿数学操作单图片，严格按JSON格式输出所有分析结果。",
                        },
                    ],
                }
            ],
        )

    async def _call_openai_compatible(
        self, system_prompt: str, base64_image: str
    ) -> Any:
        """Call an OpenAI-compatible Vision API (GPT-4o, Qwen-VL, etc.)."""
        data_url = f"data:image/png;base64,{base64_image}"

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": data_url},
                    },
                    {
                        "type": "text",
                        "text": "请分析这张幼儿数学操作单图片，严格按JSON格式输出所有分析结果。",
                    },
                ],
            },
        ]

        return await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=settings.VISION_MAX_TOKENS,
            timeout=settings.VISION_TIMEOUT_SECONDS,
        )

    def clear_cache(self) -> int:
        """Clear the in-memory result cache. Returns number of entries cleared."""
        count = len(self._result_cache)
        self._result_cache.clear()
        return count


# ─── Anthropic response helpers ────────────────────────────────────────

def _extract_anthropic_text(response) -> Optional[str]:
    """Extract text content from an Anthropic Messages API response."""
    if not response or not response.content:
        return None
    texts = []
    for block in response.content:
        if block.type == "text":
            texts.append(block.text)
    return "\n".join(texts) if texts else None


def _extract_anthropic_usage(response) -> dict:
    """Extract token usage from an Anthropic Messages API response."""
    if response and response.usage:
        return {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }
    return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
