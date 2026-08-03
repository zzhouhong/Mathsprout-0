r"""
萌芽数学 Mathsprout — 视觉识别独立评估工具 (Phase 2.1)

只跑 AI 视觉识别管线（3-pass），不跑评估引擎。用于：
- 对比不同 AI 提供商（Qwen-VL vs Claude）对同一张图的识别效果
- 迭代提示词和 OpenCV 参数
- 检查裁剪后的答案区域图片质量

用法:
  .\venv\Scripts\python.exe vision_eval.py --image tests/images/worksheet_01.jpg
  .\venv\Scripts\python.exe vision_eval.py --image tests/images/worksheet_01.jpg --provider claude
  .\venv\Scripts\python.exe vision_eval.py --image tests/images/worksheet_01.jpg --save-crops --age-group large
  .\venv\Scripts\python.exe vision_eval.py --image tests/images/worksheet_01.jpg --format markdown

提供商切换:
  --provider qwen    → 阿里云百炼 Qwen-VL (默认，当前 .env 配置)
  --provider claude  → Anthropic Claude Vision (需在 .env 中配置 ANTHROPIC_API_KEY)
"""

import json
import sys
import io
import time
import base64
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import Optional

# Force UTF-8 output on Windows
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
if sys.stderr.encoding != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

sys.path.insert(0, str(Path(__file__).parent))

from app.services.image_processor import ImageProcessor, resolve_image_size
from app.services.worksheet_recognizer import WorksheetRecognizer

# ═══════════════════════════════════════════════════════════════════════════════
# Provider configuration presets
# ═══════════════════════════════════════════════════════════════════════════════

PROVIDER_PRESETS = {
    "qwen": {
        "VISION_MODEL": "qwen3-vl-plus",
        "VISION_BASE_URL": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        # API key unchanged (from .env)
    },
    "claude": {
        "VISION_MODEL": "claude-sonnet-4-20250514",
        "VISION_BASE_URL": "https://api.anthropic.com",
        # API key must be set separately as ANTHROPIC_API_KEY in .env
    },
    "offline": {
        "VISION_MODEL": "offline",
        "VISION_BASE_URL": "local",
        # 离线模式：从 OFFLINE_RESULTS_DIR 按图片哈希读取预存识别结果，零 API 依赖
    },
}


def switch_provider(provider: str):
    """Override environment variables for the chosen provider."""
    import os
    preset = PROVIDER_PRESETS.get(provider)
    if not preset:
        print(f"未知提供商: {provider}，可选: {list(PROVIDER_PRESETS.keys())}")
        sys.exit(1)

    os.environ["VISION_MODEL"] = preset["VISION_MODEL"]
    os.environ["VISION_BASE_URL"] = preset["VISION_BASE_URL"]

    # offline provider 走离线分支：显式设置 VISION_PROVIDER 让 recognizer 检测到
    if provider == "offline":
        os.environ["VISION_PROVIDER"] = "offline"
    else:
        os.environ.pop("VISION_PROVIDER", None)

    # For Claude, use ANTHROPIC_API_KEY if VISION_API_KEY isn't already anthropic
    if provider == "claude":
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if anthropic_key:
            os.environ["VISION_API_KEY"] = anthropic_key

    # Clear settings cache so new env vars take effect
    try:
        from app.core.config import get_settings
        get_settings.cache_clear()
    except Exception:
        pass

    print(f"🔀 已切换到: {provider} ({preset['VISION_MODEL']} @ {preset['VISION_BASE_URL']})")
    return preset


# ═══════════════════════════════════════════════════════════════════════════════
# Output formatting
# ═══════════════════════════════════════════════════════════════════════════════

def format_markdown(result: dict, meta: dict, image_path: str):
    """Format recognition results as readable Markdown."""
    lines = []
    lines.append(f"# 🔍 视觉识别结果")
    lines.append(f"")
    lines.append(f"**图片**: `{image_path}`")
    lines.append(f"**模型**: `{meta.get('model', '?')}` | **提供商**: `{meta.get('provider', '?')}`")
    lines.append(f"**Token**: 输入 {meta.get('usage', {}).get('input_tokens', '?')} / 输出 {meta.get('usage', {}).get('output_tokens', '?')}")
    lines.append(f"**耗时**: {meta.get('timing_ms', '?')}ms | **Pass**: {meta.get('pass_count', '?')}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # Worksheet metadata
    lines.append(f"## 📋 操作单信息")
    lines.append(f"")
    lines.append(f"| 字段 | 值 |")
    lines.append(f"|------|-----|")
    lines.append(f"| 类型 | {result.get('worksheet_type', '?')} |")
    lines.append(f"| PCK 备注 | {result.get('observations', {}).get('overall_pck_notes', '—')} |")
    lines.append(f"")

    # Problems table
    problems = result.get("problems", [])
    if problems:
        lines.append(f"## 📝 题目识别 ({len(problems)} 题)")
        lines.append(f"")
        lines.append(f"| ID | 题型 | 幼儿答案 | 标准答案 | ✓/✗ | 置信度 | 书写质量 | 策略 |")
        lines.append(f"|----|------|----------|----------|-----|--------|----------|------|")
        for p in problems:
            correct = "✓" if p.get("is_correct") else "✗"
            lines.append(f"| {p.get('id', '?')} | {p.get('type', '?')} | **{p.get('child_answer', '?')}** | {p.get('correct_answer', '?')} | {correct} | {p.get('confidence', '?')} | {p.get('handwriting_quality', '?')} | {p.get('strategy_indicators', '—') or '—'} |")
        lines.append(f"")

    # Dimension scores preliminary
    dim_scores = result.get("dimension_scores_preliminary", {})
    if dim_scores:
        lines.append(f"## 📊 初步维度评分")
        lines.append(f"")
        for dim, info in dim_scores.items():
            lines.append(f"- **{dim}**: {info.get('correct', '?')}/{info.get('total', '?')} ({info.get('score', '?')}%)")
        lines.append(f"")

    # Observations
    obs = result.get("observations", {})
    obs_items = {k: v for k, v in obs.items() if k != "overall_pck_notes"}
    if obs_items:
        lines.append(f"## 👀 观察标记")
        lines.append(f"")
        for k, v in obs_items.items():
            lines.append(f"- **{k}**: {v}")
        lines.append(f"")

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# Core logic
# ═══════════════════════════════════════════════════════════════════════════════

async def run_vision_eval(
    image_path: str,
    age_group: str = "middle",
    quality: str = "balanced",
    use_cache: bool = True,
    save_crops: bool = False,
    output_format: str = "json",
):
    """Run vision recognition on a single image and print results."""
    img_path = Path(image_path)
    if not img_path.is_file():
        print(f"错误: 图片不存在 — {image_path}", file=sys.stderr)
        sys.exit(1)

    # Read image
    file_bytes = img_path.read_bytes()
    ext = img_path.suffix.lower()
    content_type_map = {
        ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
        ".png": "image/png", ".webp": "image/webp",
    }
    content_type = content_type_map.get(ext, "image/png")

    print(f"📷 读取图片: {img_path.name} ({len(file_bytes) / 1024:.1f} KB)")
    print(f"👶 年龄段: {age_group} | 🎯 质量: {quality}")
    print()

    # Preprocess
    t0 = time.time()
    processor = ImageProcessor(
        target_size_px=resolve_image_size(quality),
        max_size_px=2576,
        quality=85,
    )
    processed_bytes, out_filename = await processor.process(
        file_bytes, img_path.name, content_type
    )
    t_preprocess = time.time() - t0
    print(f"⚙️  预处理完成: {len(processed_bytes) / 1024:.1f} KB → {out_filename} ({t_preprocess * 1000:.0f}ms)")

    # Save processed image for inspection
    if save_crops:
        processed_dir = Path("tests/output")
        processed_dir.mkdir(parents=True, exist_ok=True)
        processed_path = processed_dir / f"processed_{img_path.stem}.png"
        processed_path.write_bytes(processed_bytes)
        print(f"💾 预处理图片已保存: {processed_path}")

    # Vision recognition
    recognizer = WorksheetRecognizer()
    print(f"🤖 模型: {recognizer.model} | 提供商: {recognizer._provider}")
    print()

    t1 = time.time()
    try:
        vision_result = await recognizer.analyze(
            processed_bytes,
            age_group=age_group,
            use_cache=use_cache,
            use_multi_pass=True,
        )
    except Exception as e:
        print(f"\n❌ 识别失败: {type(e).__name__}: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
    t_vision = time.time() - t1

    meta = vision_result.get("_meta", {})
    meta["timing_ms"] = round(t_vision * 1000, 1)
    meta["preprocess_ms"] = round(t_preprocess * 1000, 1)
    meta["pass_count"] = 3 if meta.get("multi_pass") else 1
    meta["cache_hit"] = meta.get("cache_hit", False)

    print(f"⏱️  识别耗时: {meta['timing_ms']}ms" + (" (缓存命中)" if meta.get("cache_hit") else ""))
    print(f"📊 Token: 输入 {meta.get('usage', {}).get('input_tokens', '?')} / 输出 {meta.get('usage', {}).get('output_tokens', '?')}")
    print()

    # Output
    if output_format == "markdown":
        print(format_markdown(vision_result, meta, image_path))
    else:
        # JSON output — strip _meta for cleanliness, print summary first
        summary = {
            "image": str(img_path.name),
            "model": meta.get("model", "?"),
            "provider": meta.get("provider", "?"),
            "timing_ms": meta.get("timing_ms"),
            "cache_hit": meta.get("cache_hit"),
            "token_usage": meta.get("usage", {}),
            "worksheet_type": vision_result.get("worksheet_type"),
            "problem_count": len(vision_result.get("problems", [])),
        }
        result_out = {k: v for k, v in vision_result.items() if k != "_meta"}
        output = {
            "meta": summary,
            "recognition": result_out,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2, default=str))

    return vision_result


# ═══════════════════════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    parser = argparse.ArgumentParser(
        description="萌芽数学 Mathsprout — 视觉识别独立评估工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --image tests/images/worksheet_01.jpg
  %(prog)s --image tests/images/worksheet_01.jpg --provider claude
  %(prog)s --image tests/images/worksheet_01.jpg --save-crops --format markdown
  %(prog)s --image tests/images/worksheet_01.jpg --age-group large --quality precise
        """.strip(),
    )
    parser.add_argument("--image", "-i", type=str, required=True, help="操作单图片路径")
    parser.add_argument("--age-group", "-a", type=str, default="middle",
                        choices=["small", "middle", "large"], help="年龄段（默认: middle）")
    parser.add_argument("--quality", "-q", type=str, default="balanced",
                        choices=["fast", "balanced", "precise"], help="预处理质量（默认: balanced）")
    parser.add_argument("--provider", "-p", type=str, default="qwen",
                        choices=["qwen", "claude", "offline"], help="AI 提供商（默认: qwen；offline 走离线预存结果）")
    parser.add_argument("--no-cache", action="store_true", help="禁用缓存（强制重新识别）")
    parser.add_argument("--save-crops", action="store_true", help="保存预处理图片到 tests/output/")
    parser.add_argument("--format", "-f", type=str, choices=["json", "markdown"], default="json",
                        help="输出格式（默认: json）")

    args = parser.parse_args()

    # Switch provider BEFORE creating recognizer
    switch_provider(args.provider)

    print("=" * 60)
    print("  萌芽数学 Mathsprout — 视觉识别评估")
    print("=" * 60)
    print()

    await run_vision_eval(
        image_path=args.image,
        age_group=args.age_group,
        quality=args.quality,
        use_cache=not args.no_cache,
        save_crops=args.save_crops,
        output_format=args.format,
    )


if __name__ == "__main__":
    asyncio.run(main())
