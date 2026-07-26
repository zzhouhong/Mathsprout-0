"""
OCR key chapters from the preschool math textbook PDF using Qwen-VL.
Focuses on sections 1 & 2 of chapters relevant to the 4 assessment dimensions.

Based on the TOC (from web search), the printed page numbers are:
- Chapter 3 (模式): p59-88 → Section 1: p59-65, Section 2: p66-68
- Chapter 4 (计数): p91-125 → Section 1: p91-102, Section 2: p103-106
- Chapter 5 (数符号): p129-163 → Section 1: p129-134, Section 2: p135-139
- Chapter 6 (数运算): p168-199 → Section 1: p168-176, Section 2: p177-180
- Chapter 9 (图形): p273-323 → Section 1: p273-286, Section 2: p287-291
- Chapter 10 (空间方位): p327-362 → Section 1: p327-331, Section 2: p332-334
"""
import os
import sys
import base64
import time
import json
from pathlib import Path

import fitz
from openai import OpenAI

# ─── Config ──────────────────────────────────────────────────────
PDF_PATH = r"C:\Users\Zred\Desktop\（已压缩）学前儿童数学学习与发展核心经验.pdf"
OUTPUT_MD = Path(r"C:\Users\Zred\Desktop\first CC\backend\app\core\prompts\pck_textbook_extracted.md")

# ⚠️ 安全：API Key 必须从环境变量读取，切勿硬编码。
#    此前硬编码的真实 key 已从代码中移除，请确保在阿里云控制台吊销旧 key。
import os
API_KEY = os.environ.get("DASHSCOPE_API_KEY") or os.environ.get("VISION_API_KEY", "")
if not API_KEY:
    raise SystemExit("请在环境变量中设置 DASHSCOPE_API_KEY 或 VISION_API_KEY 后再运行此脚本。")
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL = "qwen-vl-max"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ─── Chapter definitions (printed page numbers) ──────────────────
# We need to find the PDF-page-to-printed-page offset
# Each chapter: name, printed_start, printed_end, dimension_key
CHAPTERS = {
    "counting": {
        "name": "数数与数量对应 (Counting & Cardinality)",
        "sub_chapters": [
            {"title": "第四章 计数", "sections": [(91, 102), (103, 106), (107, 110)]},   # Section 1, 2, 3 (partial)
            {"title": "第五章 数符号", "sections": [(129, 134), (135, 139)]},  # Section 1, 2
        ]
    },
    "addition_sub": {
        "name": "简单加减运算 (Addition & Subtraction)",
        "sub_chapters": [
            {"title": "第六章 数运算", "sections": [(168, 176), (177, 180), (181, 184)]},  # Section 1, 2, 3 (partial)
        ]
    },
    "shapes_space": {
        "name": "图形与空间 (Shapes & Space)",
        "sub_chapters": [
            {"title": "第九章 图形", "sections": [(273, 286), (287, 291), (292, 295)]},  # Section 1, 2, 3 (partial)
            {"title": "第十章 空间方位", "sections": [(327, 331), (332, 334)]},  # Section 1, 2
        ]
    },
    "patterns": {
        "name": "模式与规律 (Patterns & Regularity)",
        "sub_chapters": [
            {"title": "第三章 模式", "sections": [(59, 65), (66, 68), (69, 72)]},  # Section 1, 2, 3 (partial)
        ]
    }
}

# ─── Helpers ─────────────────────────────────────────────────────

def render_page_as_b64(doc, page_idx, zoom=2.0):
    """Render a PDF page to base64-encoded PNG."""
    page = doc[page_idx]
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    return base64.b64encode(pix.tobytes("png")).decode("utf-8")


def ocr_page(doc, page_idx, custom_prompt=None, zoom=2.0):
    """OCR a single page using Qwen-VL."""
    if custom_prompt is None:
        custom_prompt = """请将这张书页中的所有文字完整地OCR识别出来。保持原文结构（标题层级、段落）。
这是一本学前儿童数学教育的专业书籍。请准确识别所有文字，包括小标题、正文、表格等。
直接输出识别到的所有文字，不要添加任何解释或前言。"""

    img_b64 = render_page_as_b64(doc, page_idx, zoom)

    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                    {"type": "text", "text": custom_prompt}
                ]
            }],
            max_tokens=4096,
            temperature=0.1,
        )
        return resp.choices[0].message.content
    except Exception as e:
        print(f"    API Error on page {page_idx+1}: {e}")
        time.sleep(3)
        return None


def find_pdf_offset(doc):
    """Find the offset between PDF page index and printed page number."""
    print("=== Finding PDF-to-printed-page offset ===\n")
    # Printed page 1 should be around PDF page 20-30 (after cover, front matter)
    # Let's check a range of PDF pages and look for page numbers
    for pdf_idx in [20, 25, 30, 35, 40, 45]:
        prompt = """这张书页的最底部或顶部有一个页码数字。请只输出这个页码数字，不要输出其他任何内容。
如果页脚有页码如"19"或"019"，只输出数字。如果没有找到页码，输出"NONE"。"""
        result = ocr_page(doc, pdf_idx, prompt, zoom=1.5)
        print(f"  PDF page {pdf_idx+1} -> printed page: {result}")
        time.sleep(0.5)

    # Also try to figure from chapter start pages
    # Chapter 2 starts at printed page 19
    # Let's scan around PDF page 20-35 for "集合与分类" or "第二章"
    for pdf_idx in range(15, 40, 2):
        prompt = "只输出这一页右上角或左上角的页码数字。如果没有，输出NONE。"
        result = ocr_page(doc, pdf_idx, prompt, zoom=1.5)
        if result and result.strip() != "NONE":
            print(f"  PDF page {pdf_idx+1}: printed page number = {result.strip()}")
        time.sleep(0.3)


def find_printed_page_offset(doc):
    """Find offset by looking for chapter 3 start (printed p59)."""
    # Chapter 3 (模式) starts at printed p59
    # Scan around PDF page 55-70
    print("Scanning for Chapter 3 start (printed p59)...")
    results = []
    for pdf_idx in range(55, 75):
        prompt = "只输出这个页面底部或顶部的页码数字。只输出数字，不要其他内容。如找不到输出NONE。"
        result = ocr_page(doc, pdf_idx, prompt, zoom=1.5)
        page_num = result.strip() if result else "NONE"
        print(f"  PDF page {pdf_idx+1}: result={page_num}")
        results.append((pdf_idx, page_num))
        time.sleep(0.3)
    return results


def printed_to_pdf(page_ranges, offset):
    """Convert printed page number ranges to PDF page indices."""
    result = []
    for start, end in page_ranges:
        result.append((start + offset, end + offset))
    return result


def main():
    print("=" * 60)
    print("OCR Textbook Chapters with Qwen-VL")
    print("=" * 60)

    doc = fitz.open(PDF_PATH)
    total_pages = doc.page_count

    # Build the markdown output
    md = []
    md.append("# 学前儿童数学学习与发展核心经验 — PCK提取笔记\n")
    md.append("> 来源: 黄瑾、田方 主编，南京师范大学出版社，2015\n")
    md.append(f"> PDF总页数: {total_pages} | OCR方式: Qwen-VL (qwen-vl-max)\n")
    md.append("\n---\n\n")

    # First, let's find the PDF-to-printed-page offset by checking specific pages
    # We know printed page 59 = start of Chapter 3
    # Let's find which PDF page corresponds to printed page 59

    print("\nStep 1: Finding offset between PDF pages and printed pages...")
    print("Checking PDF pages around the expected Chapter 3 start...\n")

    # Chapter 3 starts at printed p59. Front matter is usually ~10-15 pages.
    # PDF p1 = cover. So printed p59 ≈ PDF p59+15 = PDF p74. Let's search.
    offset_candidates = []
    for pdf_idx in range(65, 85):
        prompt = "请只输出这个页面底部或顶部的页码数字。只输出纯粹的数字。如找不到页码，输出NONE。"
        result = ocr_page(doc, pdf_idx, prompt, zoom=1.8)
        page_str = result.strip() if result else "NONE"
        print(f"  PDF p{pdf_idx+1}: detected page num = {page_str}")
        try:
            detected = int(page_str)
            offset = pdf_idx - detected
            offset_candidates.append((pdf_idx, detected, offset))
            print(f"    => offset = PDF_idx({pdf_idx}) - printed({detected}) = {offset}")
        except:
            pass
        time.sleep(0.3)

    if offset_candidates:
        # Use the most common offset
        offsets = [o[2] for o in offset_candidates]
        # Most common offset
        from collections import Counter
        offset = Counter(offsets).most_common(1)[0][0]
        print(f"\n[Deduced offset: {offset}] (PDF_page_idx = printed_page + {offset})")
    else:
        print("\n[Could not determine offset. Using default offset of 12.]")
        offset = 12

    md.append(f"## 技术说明\n\n")
    md.append(f"- PDF页号 = 印刷页号 + {offset}\n")
    md.append("\n---\n\n")

    # Now OCR the key chapters
    md.append("## 四维度核心经验提取\n\n")
    md.append("> 以下内容对应AI评估系统的4个评估维度，提取自原书各章节\n\n")

    total_ocr_pages = 0
    for dim_key, dim_info in CHAPTERS.items():
        md.append(f"### {dim_info['name']}\n\n")

        for sub in dim_info["sub_chapters"]:
            md.append(f"#### {sub['title']}\n\n")

            for section_start, section_end in sub["sections"]:
                pdf_start = section_start + offset
                pdf_end = min(section_end + offset, total_pages - 1)

                if pdf_start >= total_pages:
                    md.append(f"*(印刷页{section_start}-{section_end}超出PDF范围)*\n\n")
                    continue

                # Cap the range to avoid excessive API calls
                actual_end = min(pdf_end, pdf_start + 15)  # Max 15 pages per section

                md.append(f"**印刷页 {section_start}-{section_end} (PDF页 {pdf_start+1}-{actual_end+1})**\n\n")

                for pg in range(pdf_start, actual_end + 1):
                    print(f"\n  OCR: {sub['title']} - printed p{section_start + (pg - pdf_start)} (PDF p{pg+1})")
                    text = ocr_page(doc, pg)
                    if text:
                        md.append(f"*[p{section_start + (pg - pdf_start)}]*\n\n{text}\n\n---\n\n")
                    else:
                        md.append(f"*[p{section_start + (pg - pdf_start)}]* OCR失败\n\n---\n\n")
                    total_ocr_pages += 1
                    time.sleep(0.5)

                # Save intermediate after each section
                with open(OUTPUT_MD, "w", encoding="utf-8") as f:
                    f.write("\n".join(md))
                print(f"  [Saved after {total_ocr_pages} pages OCR'd]")

        md.append("\n")

    # Final save
    with open(OUTPUT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    doc.close()
    print(f"\n{'='*60}")
    print(f"DONE! Total pages OCR'd: {total_ocr_pages}")
    print(f"Output: {OUTPUT_MD}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
