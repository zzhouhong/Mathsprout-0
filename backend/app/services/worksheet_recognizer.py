"""
LLM Vision API worksheet recognition service.
Supports both Anthropic native API (Claude Vision) and OpenAI-compatible providers.

v2.0 — Multi-pass recognition pipeline:
  Pass 1: Read printed text (title, learning objective, problem instructions)
  Pass 2: Determine correct answers + classify problem types + map dimensions
  Pass 3: Read child's handwritten/circled answers (CROPPED image for accuracy)
"""

import json
import asyncio
import base64
import hashlib
import io
import cv2
import numpy as np
from typing import Optional, Dict, Any, Union, List, Tuple
from pathlib import Path
from openai import (
    AsyncOpenAI,
    APIStatusError as OpenAIStatusError,
    APITimeoutError as OpenAITimeoutError,
    APIConnectionError as OpenAIConnectionError,
    RateLimitError as OpenAIRateLimitError,
    InternalServerError as OpenAIInternalServerError,
)
import anthropic
from PIL import Image
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

OPENAI_RETRYABLE = (
    OpenAITimeoutError, OpenAIConnectionError, OpenAIRateLimitError, OpenAIInternalServerError
)
ANTHROPIC_RETRYABLE = (
    anthropic.APITimeoutError,
    anthropic.APIConnectionError,
    anthropic.RateLimitError,
    anthropic.InternalServerError,
)

# ─── Provider detection ──────────────────────────────────────────────

def _detect_provider() -> str:
    """Detect the vision provider.

    Priority:
      1. Explicit VISION_PROVIDER setting (e.g. "offline")
      2. Auto-detect from VISION_BASE_URL ("anthropic.com"/"claude" → anthropic)
      3. Fallback to OpenAI-compatible
    """
    explicit = (settings.VISION_PROVIDER or "").strip().lower()
    if explicit:
        return explicit
    base = (settings.VISION_BASE_URL or "").lower()
    if "anthropic.com" in base or "claude" in base:
        return "anthropic"
    return "openai_compatible"


def _is_anthropic_provider() -> bool:
    """Backward-compatible shim. Prefer _detect_provider()."""
    return _detect_provider() == "anthropic"


# ─── Prompt cache ─────────────────────────────────────────────────────
_prompt_cache: Dict[str, str] = {}


# ═══════════════════════════════════════════════════════════════════════
# Pass 1: Read printed worksheet text
# ═══════════════════════════════════════════════════════════════════════

PASS1_SYSTEM_PROMPT = """你是一位幼儿园数学教育分析师。你的唯一任务是：仔细阅读幼儿数学操作单上的所有印刷文字。

## 输出
严格按以下JSON输出（纯JSON，不含```json标记）：

{
  "title": "操作单标题（如'感官游乐园——明亮的眼睛'）",
  "learning_objective": "操作单上印刷的学习目标（如'感知三角形的多种变式，在拼搭中体会图形的翻转和位置变化'）",
  "instructions": "操作单上的操作说明",
  "problem_text": ["题目1的完整文字描述", "题目2的完整文字描述"],
  "note": "如果某字段在操作单上找不到，填'无'"
}"""


# ═══════════════════════════════════════════════════════════════════════
# Pass 2: Analyze problems (no child answers yet)
# ═══════════════════════════════════════════════════════════════════════

def _build_pass2_prompt(age_group: Optional[str], pass1_result: dict, opencv_hint: Optional[dict] = None) -> str:
    """Build prompt for pass 2: classify problems and determine correct answers.

    Args:
        age_group: Child's age group
        pass1_result: Pass 1 text extraction result
        opencv_hint: Optional OpenCV shape count result {"shape_type": "triangle", "count": 7, "keyword": "三角"}
    """
    age_context = ""
    if age_group and age_group in MILESTONES:
        milestones = MILESTONES[age_group]
        age_display = get_age_display_name(age_group)
        age_context = f"\n当前幼儿年龄段：{age_display}\n该年龄段在各维度的期望表现：\n"
        for dim, items in milestones.items():
            dim_name = get_dimension_display_name(dim)
            age_context += f"【{dim_name}】\n"
            for item in items:
                age_context += f"  - {item}\n"

    filtered_patterns = ERROR_PATTERNS
    if age_group:
        filtered_patterns = [ep for ep in ERROR_PATTERNS if age_group in ep.get("age_groups", [])]

    error_ref = "\n幼儿常见错误模式：\n"
    for ep in filtered_patterns:
        error_ref += f"- {ep['name']}（{ep['description']}）：{ep['teaching_implication']}\n"

    prompt = f"""你是一位幼儿园数学教育PCK分析师。

## 任务
基于操作单图片和已提取的题目文字，分析每道题的：
1. 题型归类（从以下类型中选择）
2. 标准答案（正确的数学答案）
3. PCK维度映射

## 题型类型（必须从以下中选择，不要发明新类型）
- counting: 点数、数物体个数
- compare: 比较多少/大小
- number_composition: 数的组成与分解
- add_10: 10以内加法
- sub_10: 10以内减法
- shape_id: 图形识别与命名
- spatial: 空间方位判断
- pattern_next: 模式规律接龙
- classify: 分类
- sort: 排序

## 维度映射规则
- counting/compare/number_composition → 数概念与运算(counting)
- add_10/sub_10 → 数运算能力(addition_sub)
- shape_id/spatial → 图形与空间(shapes_space)
- pattern_next/classify/sort → 集合与模式(patterns)

## 重要
- **shape_id 题型**：任务是识别图形、感知图形变式（翻转/旋转/大小变化），属于图形与空间维度。即使需要数图形个数（如"有几个三角形"），核心是图形感知，类型仍为 shape_id
- **counting 题型**：任务是手口一致点数、说出总数，属于数概念与运算维度

{age_context}
{error_ref}

{_build_opencv_hint_section(opencv_hint)}

## 已提取的题目文字
{json.dumps(pass1_result.get('problem_text', []), ensure_ascii=False)}

## 输出
严格按以下JSON输出（纯JSON）：

{{"problems":[{{"id":"P1","type":"题型（见上方枚举）","dimension":"counting|addition_sub|shapes_space|patterns","correct_answer":"标准答案","prompt_description":"题目简述"}}],"worksheet_type":"counting|addition|shapes|patterns|mixed","age_group_hint":"small|middle|large","overall_analysis":"基于操作单目标的整体教学分析（2-3句话）"}}"""

    return prompt


def _build_opencv_hint_section(opencv_hint: Optional[dict]) -> str:
    """Build a hint section for Pass 2 based on OpenCV shape counting results."""
    if not opencv_hint:
        return ""
    shape_names = {"triangle": "三角形", "rectangle": "长方形", "circle": "圆形"}
    shape_cn = shape_names.get(opencv_hint["shape_type"], opencv_hint["shape_type"])
    return (
        f"## 计算机视觉辅助计数\n"
        f"OpenCV 在该图片中检测到 **{opencv_hint['count']} 个{shape_cn}**。"
        f"请以此为参考确定题目的正确答案。"
        f"（如果操作单题目要求数{shape_cn}个数，正确答案应为 {opencv_hint['count']}。）\n"
    )


# ═══════════════════════════════════════════════════════════════════════
# Pass 3: Read child's actual answers
# ═══════════════════════════════════════════════════════════════════════

PASS3_SYSTEM_PROMPT = """你是一位幼儿园教师助理。你的唯一任务是：仔细看这张幼儿数学操作单图片，读取幼儿实际写下的答案。

## 关键原则
1. **只看幼儿的笔迹**：观察幼儿圈了什么数字、写了什么文字。不要受题目正确答案影响
2. **区分印刷和手写**：操作单上印刷的数字和文字不是幼儿的答案
3. **幼儿可能写错**：幼儿可能圈了错误的数字，这很正常
4. **逐题确认**：每一道题都要实际看一下幼儿作答区域
5. **如果某道题幼儿确实没有作答痕迹**，child_answer 填 "未作答"，不要编造答案

## 输出
严格按以下JSON输出（纯JSON）：

{
  "child_answers": [
    {
      "problem_id": "P1",
      "child_answer": "幼儿实际圈的数字或写的答案（只看幼儿笔迹！）",
      "handwriting_quality": "clear|messy|illegible|mirrored",
      "has_erasure": false,
      "erasure_pattern": "none|self_correct|persistent_error",
      "confidence": 0.0-1.0
    }
  ],
  "observations": {
    "number_formation_issues": ["mirror_3"],
    "attention_indicators": "completed_all|skipped|rushed|careful",
    "task_completion_context": "independent|with_prompts|teacher_assisted",
    "is_blank": false
  }
}"""


# ═══════════════════════════════════════════════════════════════════════
# Helper: detect + crop child answer region from image
# ═══════════════════════════════════════════════════════════════════════

def _detect_answer_row_bounds(image_data: bytes) -> Optional[Tuple[int, int]]:
    """
    Detect the answer row (printed numbers for circling) near the bottom of the image.
    Returns (top_row, bottom_row) relative to the full image, or None.
    """
    try:
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        h, w = img.shape

        # Only look at bottom 25% of the image
        bottom_region = img[int(h * 0.75):h, :]
        bh = bottom_region.shape[0]

        # Threshold to find dark printed content
        _, thresh = cv2.threshold(bottom_region, 100, 255, cv2.THRESH_BINARY_INV)
        row_dark = np.sum(thresh == 255, axis=1)

        # Find bands with dense dark pixels (text/numbers) — at least 25% of width
        threshold = w * 0.25
        bands = []
        in_band = False
        band_start = 0
        for r in range(bh):
            if row_dark[r] > threshold:
                if not in_band:
                    band_start = r
                    in_band = True
            else:
                if in_band and (r - band_start) >= 4:
                    bands.append((band_start, r))
                in_band = False
        if in_band:
            bands.append((band_start, bh - 1))

        if not bands:
            return None

        # The answer row is the bottommost band (closest to image bottom)
        last_band = bands[-1]
        top = int(h * 0.75) + last_band[0]
        bottom = int(h * 0.75) + last_band[1]

        # Safety: if the band is too tall (>15% of image), use only the bottom 10%
        if (bottom - top) > h * 0.15:
            top = int(h * 0.90)
            bottom = h

        # Add small padding
        top = max(0, top - 5)
        bottom = min(h, bottom + 5)

        return (top, bottom)
    except Exception:
        return None


def _crop_answer_region(image_data: bytes) -> bytes:
    """
    Crop the answer row from the bottom of the worksheet with auto-detection.
    Applies CLAHE contrast enhancement and 2x enlargement for better LLM reading.
    Falls back to bottom 12% if detection fails.
    """
    try:
        bounds = _detect_answer_row_bounds(image_data)

        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return image_data

        h, w = img.shape[:2]

        if bounds:
            crop_top, crop_bottom = bounds
        else:
            # Fallback: bottom 8% (very tight — just the number row)
            crop_top = int(h * 0.92)

        cropped = img[crop_top:h, 0:w]
        ch, cw = cropped.shape[:2]

        # Convert to grayscale and enhance contrast (CLAHE)
        gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Enlarge 3x for maximum clarity of small printed numbers
        new_w = int(cw * 3.0)
        new_h = int(ch * 3.0)
        enlarged = cv2.resize(enhanced, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

        # Convert back to PNG bytes
        _, buf = cv2.imencode('.png', enlarged)
        return buf.tobytes()
    except Exception:
        return image_data  # Fallback: return original


def _detect_circled_number(image_data: bytes) -> Optional[dict]:
    """
    Use OpenCV to detect which printed number the child circled in the answer row.
    Looks for circular/elliptical hand-drawn contours around printed numbers.

    Returns {"circled_number": "7", "confidence": 0.85, "method": "opencv"} or None.
    """
    try:
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return None

        h, w = img.shape[:2]

        # Focus on bottom 15%
        bottom = img[int(h * 0.85):h, 0:w]
        gray = cv2.cvtColor(bottom, cv2.COLOR_BGR2GRAY)

        # CLAHE enhancement
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Find all contours
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Look for hand-drawn circles: medium-sized, good circularity, surrounding a character
        candidates = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Hand-drawn circle: roughly 500-8000 sq px in a 1280-wide image
            if area < 400 or area > 12000:
                continue

            peri = cv2.arcLength(cnt, True)
            if peri == 0:
                continue

            circularity = 4 * np.pi * area / (peri * peri)
            # Hand-drawn circles: circularity 0.4-0.85 (less perfect than printed circles)
            if circularity < 0.35 or circularity > 0.92:
                continue

            x, y, bw, bh = cv2.boundingRect(cnt)
            aspect = bw / bh if bh > 0 else 0
            # Should be roughly square (circle bounding box)
            if aspect < 0.4 or aspect > 2.5:
                continue

            cx = x + bw // 2
            cy = y + bh // 2
            candidates.append({
                "cx": cx, "cy": cy,
                "area": area,
                "circularity": circularity,
                "bbox": (x, y, bw, bh),
            })

        if not candidates:
            return None

        # The best candidate is the one with the most "hand-drawn" characteristics:
        # - Good but not perfect circularity (0.5-0.85)
        # - Reasonable size
        # Score: prefer circularity closer to 0.7 and larger area
        best = max(candidates, key=lambda c: c["area"] * (1.0 - abs(c["circularity"] - 0.65)))

        return {
            "circled_bbox": best["bbox"],
            "center": (best["cx"], best["cy"]),
            "confidence": round(min(best["circularity"] * 1.3, 0.9), 2),
            "method": "opencv_circle_detect",
            "candidates_found": len(candidates),
        }
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════
# Pass3 OpenCV Fallback — when LLM fails, use circle position to infer answer
# ═══════════════════════════════════════════════════════════════════════

def _opencv_circle_fallback(
    image_data: bytes,
    pass2_problems: list,
    circled_result: Optional[dict],
) -> list:
    """
    When Pass3 LLM fails to read the child's handwriting, use the OpenCV
    circle detection result as a fallback.

    Lightweight strategy:
    1. If a circle was detected, detect printed number positions in the answer row
    2. Match the circle's x-position to the nearest number → that's the child's answer
    3. Map that number's position index to the corresponding problem

    Returns a list of partial child_answer dicts to substitute for "未识别" entries.
    """
    if not circled_result or not pass2_problems:
        return []

    circle_conf = circled_result.get("confidence", 0)
    if circle_conf < 0.3:
        return []

    try:
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return []

        h, w = img.shape[:2]
        # Focus on bottom 15% (same region as _detect_circled_number)
        top_y = int(h * 0.85)
        bottom_region = img[top_y:h, 0:w]
        gray = cv2.cvtColor(bottom_region, cv2.COLOR_BGR2GRAY)

        # CLAHE + Otsu threshold
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        _, thresh = cv2.threshold(enhanced, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        # Find contours in the answer row
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter for number-sized contours (not too small, not too large)
        rh, rw = bottom_region.shape[:2]
        min_area = max(100, rw * rh * 0.001)  # at least 0.1% of region
        max_area = min(8000, rw * rh * 0.15)  # at most 15% of region

        number_contours = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area <= area <= max_area:
                x, y, bw, bh = cv2.boundingRect(cnt)
                if bh > 0:
                    aspect = bw / bh
                    # Numbers are typically taller than wide (aspect 0.3-1.5)
                    if 0.2 <= aspect <= 2.0:
                        cx = x + bw // 2  # center x in bottom_region coords
                        number_contours.append({
                            "cx": cx,
                            "x": x,
                            "w": bw,
                            "area": area,
                        })

        if not number_contours:
            return []

        # Sort by x-position (left to right = option order)
        number_contours.sort(key=lambda n: n["cx"])

        # Find the circle's x-position in the same coordinate space
        circle_bbox = circled_result.get("circled_bbox")
        circle_center = circled_result.get("center")
        if circle_bbox:
            # circle_bbox is in bottom_region coords (from _detect_circled_number)
            circle_cx = circle_bbox[0] + circle_bbox[2] // 2
        elif circle_center:
            circle_cx = circle_center[0]
        else:
            return []

        # Find the closest number contour to the circle center
        closest = min(number_contours, key=lambda n: abs(n["cx"] - circle_cx))

        # The index of the closest number = which option was circled
        circled_idx = number_contours.index(closest)
        proximity = abs(closest["cx"] - circle_cx)

        # Sanity: if the circle is too far from any number (> 50% of region width), skip
        if proximity > rw * 0.5:
            return []

        # Map circled option index to problems
        # Strategy: if number of detected numbers matches number of problems,
        # direct 1:1 mapping. Otherwise, we can't reliably determine which problem.
        n_numbers = len(number_contours)
        n_problems = len(pass2_problems)

        fallback_answers = []
        conf = min(0.5, circle_conf * 0.8)

        if n_numbers == n_problems and n_problems > 0:
            # Direct mapping: circled_idx → problem at same index
            prob = pass2_problems[circled_idx]
            # The "correct answer" of this problem is the printed number
            # The child circled it, so child_answer = that number
            child_answer = prob.get("correct_answer", str(circled_idx + 1))
            fallback_answers.append({
                "problem_id": prob.get("id", ""),
                "child_answer": child_answer,
                "confidence": round(conf, 2),
                "strategy_indicators": "opencv_fallback",
                "handwriting_quality": "illegible",
                "has_erasure": False,
                "erasure_pattern": "none",
                "_fallback_note": f"OpenCV: circle matched option {circled_idx + 1}/{n_numbers} at x={closest['cx']}",
            })
        elif n_numbers > 0:
            # Fallback: can't map exactly, but mark that a circle was detected
            # Apply to the first problem as a "best guess" with very low confidence
            prob = pass2_problems[0]
            fallback_answers.append({
                "problem_id": prob.get("id", ""),
                "child_answer": f"[圈选@{circled_idx + 1}/{n_numbers}]",
                "confidence": round(conf * 0.5, 2),
                "strategy_indicators": "opencv_fallback_uncertain",
                "handwriting_quality": "illegible",
                "has_erasure": False,
                "erasure_pattern": "none",
                "_fallback_note": f"OpenCV detected circle near option {circled_idx + 1} of {n_numbers}, but count mismatch ({n_numbers} numbers vs {n_problems} problems)",
            })

        return fallback_answers

    except Exception as e:
        print(f"[Pass 3] OpenCV fallback error: {type(e).__name__}: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════
# OpenCV Shape Detection — replaces LLM-based shape counting
# ═══════════════════════════════════════════════════════════════════════

def count_shapes_in_image(
    image_data: bytes,
    shape_type: str = "triangle",
    min_area: int = 200,
    max_area_ratio: float = 0.4,
) -> dict:
    """
    Count geometric shapes in a worksheet image using OpenCV contour analysis.

    Args:
        image_data: PNG/JPEG image bytes
        shape_type: "triangle", "rectangle", "circle", or "any"
        min_area: minimum contour area (filters noise)
        max_area_ratio: max contour area as fraction of total image

    Returns:
        {"count": N, "contours_found": M, "shape_type": "...", "method": "opencv"}
    """
    try:
        # Decode image
        nparr = np.frombuffer(image_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            return {"count": -1, "error": "无法解码图片", "method": "opencv"}

        h, w = img.shape[:2]
        total_area = h * w
        max_area = int(total_area * max_area_ratio)

        # Convert to grayscale and threshold
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Adaptive threshold — works well for printed shapes on paper
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV, 11, 2
        )

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Filter and classify contours
        matched = 0
        all_filtered = 0
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area or area > max_area:
                continue
            if area > total_area * 0.8:
                continue  # Skip full-image border

            all_filtered += 1
            peri = cv2.arcLength(cnt, True)
            approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
            vertices = len(approx)

            # Shape classification
            if shape_type == "triangle" and vertices == 3:
                # Extra check: aspect ratio to filter thin slivers
                x, y, bw, bh = cv2.boundingRect(cnt)
                aspect = bw / bh if bh > 0 else 0
                if 0.2 < aspect < 5.0:
                    matched += 1
            elif shape_type == "rectangle" and vertices == 4:
                x, y, bw, bh = cv2.boundingRect(cnt)
                aspect = bw / bh if bh > 0 else 0
                if 0.5 < aspect < 2.0:
                    matched += 1
            elif shape_type == "circle":
                # Circularity check
                if peri > 0:
                    circularity = 4 * np.pi * area / (peri * peri)
                    if circularity > 0.7:
                        matched += 1
            elif shape_type == "any":
                matched += 1

        print(f"[OpenCV] shape={shape_type} | raw_contours={len(contours)} | "
              f"filtered={all_filtered} | matched={matched}")

        return {
            "count": max(matched, 0),
            "raw_contours": len(contours),
            "filtered_contours": all_filtered,
            "shape_type": shape_type,
            "method": "opencv",
        }

    except Exception as e:
        print(f"[OpenCV] Error: {e}")
        return {"count": -1, "error": str(e), "method": "opencv"}


# ═══════════════════════════════════════════════════════════════════════
# Response parsing helpers
# ═══════════════════════════════════════════════════════════════════════

def _compute_image_hash(image_data: bytes) -> str:
    return hashlib.sha256(image_data).hexdigest()


def _parse_response(text: Optional[str]) -> dict:
    if text is None:
        raise ValueError("AI 响应为空。请检查 API Key 是否有效、账户是否有额度。")
    if not text.strip():
        raise ValueError("AI 返回了空响应内容。")

    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    brace_start = cleaned.find("{")
    brace_end = cleaned.rfind("}")
    if brace_start >= 0 and brace_end > brace_start:
        try:
            return json.loads(cleaned[brace_start:brace_end + 1])
        except json.JSONDecodeError:
            pass

    try:
        import re
        fixed = re.sub(r"'([^']*)':", r'"\1":', cleaned)
        fixed = re.sub(r":\s*'([^']*)'", r': "\1"', fixed)
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    raise ValueError(f"无法解析 AI 响应为 JSON。原始响应前200字符: {text[:200]}")


# ═══════════════════════════════════════════════════════════════════════
# Anthropic response helpers
# ═══════════════════════════════════════════════════════════════════════

def _extract_anthropic_text(response) -> Optional[str]:
    if not response or not response.content:
        return None
    texts = []
    for block in response.content:
        if block.type == "text":
            texts.append(block.text)
    return "\n".join(texts) if texts else None


def _extract_anthropic_usage(response) -> dict:
    if response and response.usage:
        return {
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
        }
    return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}


# ═══════════════════════════════════════════════════════════════════════
# WorksheetRecognizer — Multi-pass pipeline
# ═══════════════════════════════════════════════════════════════════════

class WorksheetRecognizer:
    """Multi-pass worksheet recognition service.

    Pass 1: Read printed text (cheap, structural)
    Pass 2: Classify problems + correct answers + dimension mapping
    Pass 3: Read child's handwritten answers (on cropped image)
    """

    def __init__(self):
        self.model = settings.VISION_MODEL
        self._result_cache = LRUDict(max_size=64)
        self._pass1_cache = LRUDict(max_size=64)

        provider = _detect_provider()
        if provider == "offline":
            # 离线模式：无需任何 HTTP client，识别结果从本地预存 JSON 读取
            self._provider = "offline"
            self.client = None
        elif provider == "anthropic":
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
        use_multi_pass: bool = True,
    ) -> dict:
        """
        Analyze a worksheet image.

        Args:
            image_data: Processed PNG image bytes
            age_group: Optional age group hint (small/middle/large)
            use_cache: Whether to use in-memory cache
            use_multi_pass: Use 3-pass pipeline (default) or single-pass legacy

        Returns:
            Structured recognition result dict
        """
        image_hash = _compute_image_hash(image_data)
        if use_cache and image_hash in self._result_cache:
            cached = self._result_cache[image_hash]
            result = dict(cached)
            result["_meta"] = dict(result.get("_meta", {}))
            result["_meta"]["cache_hit"] = True
            return result

        # ── Offline provider: read pre-stored recognition result by image hash ──
        if self._provider == "offline":
            result = self._offline_lookup(image_hash, age_group)
            result["_meta"] = {
                "model": self.model,
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                "provider": "offline",
                "multi_pass": False,
            }
            result.setdefault("problems", [])
            result.setdefault("observations", {})
            result.setdefault("dimension_scores_preliminary", {})
            result.setdefault("worksheet_type", "unknown")
            if use_cache:
                self._result_cache[image_hash] = result
            return result

        base64_image = base64.b64encode(image_data).decode("utf-8")

        total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

        if use_multi_pass:
            result, total_usage = await self._multi_pass_analyze(
                image_data, base64_image, age_group, total_usage
            )
        else:
            result, total_usage = await self._single_pass_analyze(
                base64_image, age_group, total_usage
            )

        # Attach metadata
        result["_meta"] = {
            "model": self.model,
            "usage": total_usage,
            "provider": self._provider,
            "multi_pass": use_multi_pass,
        }

        # Ensure required fields
        result.setdefault("problems", [])
        result.setdefault("observations", {})
        result.setdefault("dimension_scores_preliminary", {})
        result.setdefault("worksheet_type", "unknown")

        if use_cache:
            self._result_cache[image_hash] = result

        return result

    async def _multi_pass_analyze(
        self,
        image_data: bytes,
        base64_image: str,
        age_group: Optional[str],
        total_usage: dict,
    ) -> Tuple[dict, dict]:
        """3-pass pipeline: read text → classify → read child answers."""

        # ── Pass 1: Read printed text ──────────────────────────────
        pass1_result = await self._call_pass("pass1", PASS1_SYSTEM_PROMPT, base64_image,
            "读取操作单上所有印刷文字（标题、学习目标、操作说明、题目文字）。", total_usage)
        print(f"[Pass 1] Title: {pass1_result.get('title', '?')}")
        print(f"[Pass 1] Objective: {pass1_result.get('learning_objective', '?')}")

        # ── Pre-Pass-2: OpenCV shape counting (improves consistency) ──
        opencv_shape_hint = None
        pass1_text = " ".join(pass1_result.get("problem_text", []))
        pass1_text += " " + pass1_result.get("learning_objective", "")
        pass1_text += " " + pass1_result.get("title", "")
        for kw, shape_type in [("三角", "triangle"), ("正方形", "rectangle"),
                               ("正方", "rectangle"), ("圆形", "circle"),
                               ("圆", "circle"), ("长方形", "rectangle")]:
            if kw in pass1_text:
                cv_result = count_shapes_in_image(image_data, shape_type=shape_type)
                cv_count = cv_result.get("count", -1)
                if 1 <= cv_count <= 30:
                    opencv_shape_hint = {
                        "shape_type": shape_type,
                        "count": cv_count,
                        "keyword": kw,
                    }
                    print(f"[OpenCV Pre-Pass2] Detected {cv_count} {shape_type}(s) from keyword '{kw}'")
                break  # Only match first shape keyword

        # ── Pass 2: Classify problems + correct answers ─────────────
        pass2_prompt = _build_pass2_prompt(age_group, pass1_result, opencv_shape_hint)
        pass2_result = await self._call_pass("pass2", pass2_prompt, base64_image,
            "分析题目类型、标准答案和PCK维度映射。", total_usage)
        print(f"[Pass 2] Problems: {len(pass2_result.get('problems', []))}")

        # ── Pass 3: Read child answers ─────────────────────────────
        # Pre-check: OpenCV circle detection as a hint for the AI
        opencv_circle = _detect_circled_number(image_data)
        pass3_hint = ""
        if opencv_circle and opencv_circle.get("confidence", 0) >= 0.5:
            cx, cy = opencv_circle.get("center", (0, 0))
            conf = opencv_circle["confidence"]
            print(f"[Pass 3] OpenCV detected possible circle at ({cx}, {cy}), conf={conf:.2f}")
            pass3_hint = (
                f"（辅助提示：OpenCV在答案行预扫描检测到可能的手画标记，"
                f"位于图像底部区域中心偏右位置x≈{cx}。"
                f"请特别留意该位置附近的数字上是否有圈或标记。）"
            )
        else:
            if opencv_circle:
                cv_conf = opencv_circle.get("confidence", 0)
                print(f"[Pass 3] OpenCV circle detection: low confidence ({cv_conf:.2f})")
            else:
                print("[Pass 3] OpenCV circle detection: no circle found")

        pass3_user_prompt = (
            "看这张幼儿操作单图片。在底部有一排数字选项。"
            "仔细观察每个数字，哪个数字上有幼儿画的圈或标记？"
            "只报告你实际看到的标记，不要猜测。"
            "如果没有看到任何标记，说'未作答'。"
        )
        if pass3_hint:
            pass3_user_prompt = pass3_hint + pass3_user_prompt

        # Try dual-image (full + cropped answer row) for better detail on circled numbers.
        # Fall back to single-image if cropping or dual call fails.
        pass3_result = None
        try:
            cropped_bytes = _crop_answer_region(image_data)
            if cropped_bytes and cropped_bytes != image_data:
                cropped_b64 = base64.b64encode(cropped_bytes).decode("utf-8")
                pass3_result = await self._call_pass_dual_image(
                    "pass3", PASS3_SYSTEM_PROMPT,
                    base64_image, cropped_b64,
                    pass3_user_prompt, total_usage)
                print(f"[Pass 3] Dual-image call succeeded")
        except Exception as e:
            print(f"[Pass 3] Dual-image call failed ({type(e).__name__}: {e}), falling back to single-image")

        if pass3_result is None:
            # Fallback: single full-image call
            pass3_result = await self._call_pass("pass3", PASS3_SYSTEM_PROMPT, base64_image,
                pass3_user_prompt,
                total_usage)

        child_answers = pass3_result.get("child_answers", [])
        pass3_obs = pass3_result.get("observations", {})

        # Log the raw Pass 3 result for debugging
        ans_raw = child_answers[0].get("child_answer", "?") if child_answers else "?"
        print(f"[Pass 3] child_answer = {ans_raw}")

        # Check if blank — only truly blank when Pass 2 also found no problems.
        # Pass 3 failure to read handwriting is common (Qwen-VL bottleneck);
        # we preserve Pass 1 (printed text) + Pass 2 (problem classification)
        # results and mark child answers as "未识别".
        is_explicitly_blank = pass3_obs.get("is_blank", False)
        has_no_answers = not child_answers or all(
            a.get("child_answer", "") in ("", "未作答", "无", "?", "未识别")
            for a in child_answers
        )
        # Use OR: either condition alone is enough to treat Pass 3 as failed
        pass3_failed = is_explicitly_blank or has_no_answers

        pass2_problems = pass2_result.get("problems", [])
        if not pass2_problems:
            # Pass 2 found no problems — genuinely empty/incomplete worksheet
            return {
                "worksheet_type": "incomplete",
                "problems": [],
                "observations": {
                    "learning_objective": pass1_result.get("learning_objective", "未标注"),
                    "title": pass1_result.get("title", ""),
                    "instructions": pass1_result.get("instructions", ""),
                    "number_formation_issues": [],
                    "attention_indicators": "unknown",
                    "task_completion_context": "unknown",
                    "overall_pck_notes": "操作单未完成——AI 未能识别到印刷题目。",
                },
                "dimension_scores_preliminary": {},
                "_pass1": pass1_result,
            }, total_usage

        if pass3_failed:
            # Try OpenCV circle fallback before giving up entirely
            fallback_answers = _opencv_circle_fallback(image_data, pass2_problems, opencv_circle)
            if fallback_answers:
                n_fallback = len(fallback_answers)
                print(f"[Pass 3] ⚠️ LLM 未读取到作答，但 OpenCV 圆形回退成功推断出 {n_fallback} 个答案")
                # Build "未识别" for problems not covered by fallback
                fallback_ids = {fb["problem_id"] for fb in fallback_answers}
                child_answers = fallback_answers + [
                    {"problem_id": p2.get("id", ""), "child_answer": "未识别",
                     "handwriting_quality": "illegible", "has_erasure": False,
                     "erasure_pattern": "none", "confidence": 0.0}
                    for p2 in pass2_problems if p2.get("id", "") not in fallback_ids
                ]
            else:
                print(f"[Pass 3] ⚠️ 未读取到幼儿作答痕迹（is_blank={is_explicitly_blank}, no_answers={has_no_answers}），保留 Pass 1+2 识别结果（题型+标准答案），child_answer 标记为'未识别'")
                # Replace child_answers with "未识别" entries for each Pass 2 problem
                child_answers = [
                    {"problem_id": p2.get("id", ""), "child_answer": "未识别",
                     "handwriting_quality": "illegible", "has_erasure": False,
                     "erasure_pattern": "none", "confidence": 0.0}
                    for p2 in pass2_problems
                ]

        # ── OpenCV shape counting override (ONLY for counting problems) ──
        pass2_problems = pass2_result.get("problems", [])
        for prob in pass2_problems:
            # Only override for counting-type problems (literal "count the objects")
            # Do NOT override shape_id — those are perception tasks (triangles in a fox picture, etc.)
            if prob.get("type") == "counting":
                desc = prob.get("prompt_description", "")
                shape_to_count = None
                for kw, shape in [("三角", "triangle"), ("正方形", "rectangle"), ("正方", "rectangle"),
                                   ("圆形", "circle"), ("圆", "circle"), ("长方形", "rectangle")]:
                    if kw in desc:
                        shape_to_count = shape
                        break

                if shape_to_count:
                    cv_result = count_shapes_in_image(image_data, shape_type=shape_to_count)
                    cv_count = cv_result.get("count", -1)
                    if 1 <= cv_count <= 30:  # Sanity check
                        print(f"[OpenCV] counting override: {prob.get('correct_answer')} → {cv_count} ({shape_to_count})")
                        prob["correct_answer"] = str(cv_count)
                        prob["_opencv_override"] = True

        # ── Merge pass2 + pass3 ────────────────────────────────────
        merged_problems = []
        for p2 in pass2_problems:
            pid = p2.get("id", "")
            # Find matching child answer
            p3 = next((a for a in child_answers if a.get("problem_id") == pid), None)
            if p3 is None and child_answers:
                p3 = child_answers[0]  # Single problem worksheet fallback

            child_answer = p3.get("child_answer", "未识别") if p3 else "未识别"
            # "未识别" means AI couldn't read the answer — treat as unknown (None), not incorrect (False)
            if child_answer in ("未识别", "未作答"):
                is_correct = None  # Unknown — assessment engine will handle
            else:
                is_correct = str(child_answer).strip() == str(p2.get("correct_answer", "")).strip()
            merged_problems.append({
                "id": pid,
                "type": p2.get("type", ""),
                "child_answer": child_answer,
                "correct_answer": p2.get("correct_answer", "?"),
                "is_correct": is_correct,
                "confidence": p3.get("confidence", 0.7) if p3 else 0.5,
                "handwriting_quality": p3.get("handwriting_quality", "clear") if p3 else "unknown",
                "has_erasure": p3.get("has_erasure", False) if p3 else False,
                "erasure_pattern": p3.get("erasure_pattern", "none") if p3 else "none",
                "strategy_indicators": "",
            })

        # Build dimension_scores_preliminary
        dim_scores = {}
        for p in merged_problems:
            dim = p2.get("dimension", "") if isinstance(p2 := next((pp for pp in pass2_problems if pp.get("id") == p["id"]), {}), dict) else ""
            if not dim:
                # Infer from type
                type_dim_map = {
                    "counting": "counting", "compare": "counting", "number_composition": "counting",
                    "add_10": "addition_sub", "sub_10": "addition_sub",
                    "shape_id": "shapes_space", "spatial": "shapes_space",
                    "pattern_next": "patterns", "classify": "patterns", "sort": "patterns",
                }
                dim = type_dim_map.get(p["type"], "counting")
            if dim not in dim_scores:
                dim_scores[dim] = {"correct": 0, "total": 0}
            dim_scores[dim]["total"] += 1
            if p["is_correct"]:
                dim_scores[dim]["correct"] += 1

        result = {
            "worksheet_type": pass2_result.get("worksheet_type", "mixed"),
            "age_group_hint": pass2_result.get("age_group_hint", age_group or "middle"),
            "problems": merged_problems,
            "observations": {
                "learning_objective": pass1_result.get("learning_objective", "未标注"),
                "number_formation_issues": pass3_obs.get("number_formation_issues", []),
                "attention_indicators": pass3_obs.get("attention_indicators", "unknown"),
                "task_completion_context": pass3_obs.get("task_completion_context", "unknown"),
                "overall_pck_notes": pass2_result.get("overall_analysis", ""),
            },
            "dimension_scores_preliminary": dim_scores,
            "_pass1": pass1_result,
            "_pass3_raw": pass3_result,
        }
        return result, total_usage

    async def _single_pass_analyze(
        self, base64_image: str, age_group: Optional[str], total_usage: dict
    ) -> Tuple[dict, dict]:
        """Legacy single-pass analysis (fallback)."""
        system_prompt = _build_system_prompt(age_group)
        result = await self._call_pass("single", system_prompt, base64_image,
            "请分析这张幼儿数学操作单图片，严格按JSON格式输出所有分析结果。", total_usage)
        return result, total_usage

    async def _call_pass(
        self, pass_name: str, system_prompt: str, base64_image: str,
        user_text: str, total_usage: dict,
    ) -> dict:
        """Execute one API call with retry logic."""
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await self._call_llm(system_prompt, base64_image, user_text)

                if self._provider == "anthropic":
                    text_content = _extract_anthropic_text(response)
                    usage = _extract_anthropic_usage(response)
                else:
                    text_content = response.choices[0].message.content
                    usage = {
                        "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "output_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0,
                    }

                total_usage["input_tokens"] += usage["input_tokens"]
                total_usage["output_tokens"] += usage["output_tokens"]
                total_usage["total_tokens"] += usage["total_tokens"]

                if not text_content:
                    raise ValueError(f"[{pass_name}] AI API 返回了空的文本内容。")

                result = _parse_response(text_content)
                result["_pass"] = pass_name
                result["_attempt"] = attempt
                return result

            except tuple(OPENAI_RETRYABLE + ANTHROPIC_RETRYABLE) as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    delay = min(BASE_DELAY_SECONDS * (2 ** attempt), MAX_DELAY_SECONDS)
                    print(f"[{pass_name}] 重试 {attempt + 1}/{MAX_RETRIES}，等待 {delay:.1f}s: {type(e).__name__}")
                    await asyncio.sleep(delay)
                else:
                    raise RuntimeError(
                        f"[{pass_name}] AI API 调用失败，已重试 {MAX_RETRIES} 次。"
                        f"最后错误: {type(last_error).__name__}: {str(last_error)}"
                    ) from last_error

            except (json.JSONDecodeError, ValueError) as e:
                if attempt < MAX_RETRIES:
                    delay = BASE_DELAY_SECONDS * (2 ** attempt)
                    await asyncio.sleep(delay)
                    last_error = e
                else:
                    return {"error": str(e), "_pass": pass_name, "_parse_failed": True}

            except (OpenAIStatusError, anthropic.APIStatusError) as e:
                status = getattr(e, 'status_code', 0)
                if status in (400, 401, 413, 429):
                    raise RuntimeError(f"[{pass_name}] API 错误 (HTTP {status}): {str(e)}") from e
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(BASE_DELAY_SECONDS * (2 ** attempt))
                    last_error = e
                else:
                    raise RuntimeError(f"[{pass_name}] API 错误: {str(e)}") from e

        raise RuntimeError(f"[{pass_name}] 未知错误: {str(last_error)}")

    async def _call_pass_dual_image(
        self, pass_name: str, system_prompt: str,
        full_image_b64: str, cropped_image_b64: str,
        user_text: str, total_usage: dict,
    ) -> dict:
        """Execute one API call with TWO images (full + cropped) and retry logic."""
        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = await self._call_llm_dual_image(
                    system_prompt, full_image_b64, cropped_image_b64, user_text
                )

                if self._provider == "anthropic":
                    text_content = _extract_anthropic_text(response)
                    usage = _extract_anthropic_usage(response)
                else:
                    text_content = response.choices[0].message.content
                    usage = {
                        "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                        "output_tokens": response.usage.completion_tokens if response.usage else 0,
                        "total_tokens": response.usage.total_tokens if response.usage else 0,
                    }

                total_usage["input_tokens"] += usage["input_tokens"]
                total_usage["output_tokens"] += usage["output_tokens"]
                total_usage["total_tokens"] += usage["total_tokens"]

                if not text_content:
                    raise ValueError(f"[{pass_name}] AI API 返回了空的文本内容。")

                result = _parse_response(text_content)
                result["_pass"] = pass_name
                result["_attempt"] = attempt
                return result

            except tuple(OPENAI_RETRYABLE + ANTHROPIC_RETRYABLE) as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    delay = min(BASE_DELAY_SECONDS * (2 ** attempt), MAX_DELAY_SECONDS)
                    print(f"[{pass_name}] 重试 {attempt + 1}/{MAX_RETRIES}，等待 {delay:.1f}s: {type(e).__name__}")
                    await asyncio.sleep(delay)
                else:
                    raise RuntimeError(
                        f"[{pass_name}] AI API 调用失败，已重试 {MAX_RETRIES} 次。"
                        f"最后错误: {type(last_error).__name__}: {str(last_error)}"
                    ) from last_error

            except (json.JSONDecodeError, ValueError) as e:
                if attempt < MAX_RETRIES:
                    delay = BASE_DELAY_SECONDS * (2 ** attempt)
                    await asyncio.sleep(delay)
                    last_error = e
                else:
                    return {"error": str(e), "_pass": pass_name, "_parse_failed": True}

            except (OpenAIStatusError, anthropic.APIStatusError) as e:
                status = getattr(e, 'status_code', 0)
                if status in (400, 401, 413, 429):
                    raise RuntimeError(f"[{pass_name}] API 错误 (HTTP {status}): {str(e)}") from e
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(BASE_DELAY_SECONDS * (2 ** attempt))
                    last_error = e
                else:
                    raise RuntimeError(f"[{pass_name}] API 错误: {str(e)}") from e

        raise RuntimeError(f"[{pass_name}] 未知错误: {str(last_error)}")

    async def _call_llm(
        self, system_prompt: str, base64_image: str, user_text: str
    ) -> Any:
        """Dispatch to provider-specific implementation."""
        if self._provider == "anthropic":
            return await self._call_anthropic(system_prompt, base64_image, user_text)
        else:
            return await self._call_openai_compatible(system_prompt, base64_image, user_text)

    async def _call_llm_dual_image(
        self, system_prompt: str, full_image_b64: str, cropped_image_b64: str, user_text: str
    ) -> Any:
        """Dispatch dual-image call to provider-specific implementation."""
        if self._provider == "anthropic":
            return await self._call_anthropic_dual(system_prompt, full_image_b64, cropped_image_b64, user_text)
        else:
            return await self._call_openai_compatible_dual(system_prompt, full_image_b64, cropped_image_b64, user_text)

    async def _call_anthropic(
        self, system_prompt: str, base64_image: str, user_text: str
    ) -> Any:
        return await self.client.messages.create(
            model=self.model,
            max_tokens=settings.VISION_MAX_TOKENS,
            timeout=settings.VISION_TIMEOUT_SECONDS,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": base64_image}},
                    {"type": "text", "text": user_text},
                ],
            }],
        )

    async def _call_openai_compatible(
        self, system_prompt: str, base64_image: str, user_text: str
    ) -> Any:
        data_url = f"data:image/png;base64,{base64_image}"
        return await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": data_url}},
                    {"type": "text", "text": user_text},
                ]},
            ],
            max_tokens=settings.VISION_MAX_TOKENS,
            timeout=settings.VISION_TIMEOUT_SECONDS,
        )

    async def _call_anthropic_dual(
        self, system_prompt: str, full_b64: str, cropped_b64: str, user_text: str
    ) -> Any:
        """Anthropic API call with two images (full + cropped answer area)."""
        return await self.client.messages.create(
            model=self.model,
            max_tokens=settings.VISION_MAX_TOKENS,
            timeout=settings.VISION_TIMEOUT_SECONDS,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": full_b64}},
                    {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": cropped_b64}},
                    {"type": "text", "text": user_text},
                ],
            }],
        )

    async def _call_openai_compatible_dual(
        self, system_prompt: str, full_b64: str, cropped_b64: str, user_text: str
    ) -> Any:
        """OpenAI-compatible API call with two images (full + cropped answer area)."""
        full_url = f"data:image/png;base64,{full_b64}"
        cropped_url = f"data:image/png;base64,{cropped_b64}"
        return await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {"url": full_url}},
                    {"type": "image_url", "image_url": {"url": cropped_url}},
                    {"type": "text", "text": user_text},
                ]},
            ],
            max_tokens=settings.VISION_MAX_TOKENS,
            timeout=settings.VISION_TIMEOUT_SECONDS,
        )

    # ── Offline provider ────────────────────────────────────────────────

    def _offline_lookup(self, image_hash: str, age_group: Optional[str] = None) -> dict:
        """Read a pre-stored recognition result from the offline results dir.

        The offline directory (settings.OFFLINE_RESULTS_DIR) holds one subdirectory
        per worksheet image. Each subdirectory contains:
          - ``image_hash.txt``  : the SHA-256 hash of the source image (first line)
          - ``recognition_result.json`` : the recognition result dict

        Matching is by image hash so the same image always yields the same result.
        """
        results_dir = Path(settings.OFFLINE_RESULTS_DIR)
        if not results_dir.is_dir():
            raise RuntimeError(
                f"离线模式：结果目录不存在 ({results_dir})。"
                f"请在 .env 中正确设置 OFFLINE_RESULTS_DIR，"
                f"或切换 VISION_PROVIDER 到 qwen/claude。"
            )

        for case_dir in results_dir.iterdir():
            if not case_dir.is_dir():
                continue
            hash_file = case_dir / "image_hash.txt"
            result_file = case_dir / "recognition_result.json"
            if not (hash_file.exists() and result_file.exists()):
                continue
            try:
                stored_hash = hash_file.read_text(encoding="utf-8").strip().splitlines()[0].strip()
            except (OSError, IndexError):
                continue
            if stored_hash == image_hash:
                with open(result_file, "r", encoding="utf-8") as f:
                    return json.load(f)

        # 未匹配到预存结果：返回友好的空结果（而非抛异常），让前端能正常展示"暂无分析"
        # 同时在 observations 里附说明，提示该图未被预识别
        return {
            "worksheet_type": "unknown",
            "age_group_hint": age_group or "middle",
            "problems": [],
            "observations": {
                "learning_objective": "离线模式：该图片未预存识别结果",
                "number_formation_issues": [],
                "attention_indicators": "skipped",
                "task_completion_context": "independent",
                "overall_pck_notes": (
                    f"离线模式仅能识别预存的测试图片。当前图片（hash={image_hash[:12]}…）"
                    f"未在离线库中。要识别任意图片，请在 .env 配置 VISION_PROVIDER=qwen 或 claude，"
                    f"并填入对应 API key。"
                ),
            },
            "dimension_scores_preliminary": {},
            "_offline_unmatched": True,
        }

    def clear_cache(self) -> int:
        count = len(self._result_cache) + len(self._pass1_cache)
        self._result_cache.clear()
        self._pass1_cache.clear()
        return count


# ═══════════════════════════════════════════════════════════════════════
# Legacy single-pass prompt (fallback)
# ═══════════════════════════════════════════════════════════════════════

def _build_system_prompt(age_group: Optional[str] = None) -> str:
    """Legacy single-pass prompt — used when use_multi_pass=False."""
    cache_key = f"legacy_{age_group or 'no_age'}"
    if cache_key in _prompt_cache:
        return _prompt_cache[cache_key]

    age_context = ""
    if age_group and age_group in MILESTONES:
        milestones = MILESTONES[age_group]
        age_display = get_age_display_name(age_group)
        age_context = f"\n当前幼儿年龄段：{age_display}\n该年龄段在各维度的期望表现：\n"
        for dim, items in milestones.items():
            dim_name = get_dimension_display_name(dim)
            age_context += f"【{dim_name}】\n"
            for item in items:
                age_context += f"  - {item}\n"

    prompt = f"""你是一位幼儿园数学教育PCK分析师。分析幼儿数学操作单，识别题目类型、幼儿答案、正确性。

## 重要原则
1. 操作单是幼儿自然学习活动的产出，不是标准化测试
2. 关注解题过程痕迹（擦除、策略），而非仅看对错
3. 镜像书写（3→ε、5→ϱ、7→⅃）是正常发展现象，不视为数学错误
4. 区分中文数字"一二三"和阿拉伯数字"123"

## 题型类型（必须从以下选择，不要发明新类型）
counting / compare / number_composition / add_10 / sub_10 / shape_id / spatial / pattern_next / classify / sort

## 维度映射
- counting/compare/number_composition → counting
- add_10/sub_10 → addition_sub
- shape_id/spatial → shapes_space
- pattern_next/classify/sort → patterns

## 重要区分
- shape_id: 感知图形变式（翻转/旋转），核心是图形感知 → shapes_space
- counting: 手口一致点数、说出总数 → counting

## 输出格式
{{"worksheet_type":"...","problems":[{{"id":"P1","type":"...","child_answer":"...","correct_answer":"...","is_correct":true/false,"confidence":0.0-1.0,"handwriting_quality":"...","has_erasure":false,"erasure_pattern":"none","strategy_indicators":""}}],"observations":{{"learning_objective":"...","number_formation_issues":[],"attention_indicators":"...","task_completion_context":"...","overall_pck_notes":"..."}},"dimension_scores_preliminary":{{}}}}

{age_context}

请基于图片内容分析后输出JSON。"""

    _prompt_cache[cache_key] = prompt
    return prompt
