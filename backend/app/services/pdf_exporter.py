"""
PDF Report Exporter — Teacher & Parent versions using ReportLab.

Uses ReportLab's built-in CJK CID fonts (STSong-Light) for Chinese text —
no external font files required.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

from app.core.prompts.pck_reference import get_dimension_display_name

# ─── Register CJK font ──────────────────────────────────────────────

try:
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    CJK_FONT = "STSong-Light"
except Exception:
    # Fallback — will show tofu characters, but won't crash
    CJK_FONT = "Helvetica"

PAGE_W, PAGE_H = A4  # 210 x 297 mm

# ─── Color Palette ──────────────────────────────────────────────────

BRAND_PRIMARY = colors.HexColor("#6366F1")     # Indigo
BRAND_LIGHT = colors.HexColor("#EEF2FF")
DARK_TEXT = colors.HexColor("#1E293B")
MED_TEXT = colors.HexColor("#475569")
LIGHT_BORDER = colors.HexColor("#E2E8F0")
WHITE = colors.white

LEVEL_COLORS = {
    "L1": colors.HexColor("#EF4444"),  # Red — sprout
    "L2": colors.HexColor("#F59E0B"),  # Amber — growing
    "L3": colors.HexColor("#10B981"),  # Green — proficient
    "L4": colors.HexColor("#6366F1"),  # Indigo — advanced
}
LEVEL_LABELS = {
    "L1": "萌芽期", "L2": "发展期", "L3": "熟练期", "L4": "进阶期",
}
LEVEL_EMOJI = {
    "L1": "🌱", "L2": "🌿", "L3": "🌳", "L4": "⭐",
}


# ─── Custom Flowables ────────────────────────────────────────────────

class ProgressBar(Flowable):
    """Horizontal progress bar with label."""

    def __init__(self, label: str, score: float, level: str, width: float = 120 * mm):
        super().__init__()
        self.label = label
        self.score = max(0, min(100, score))
        self.level = level
        self._width = width
        self._height = 10 * mm

    def wrap(self, availWidth, availHeight):
        return (min(self._width, availWidth), self._height)

    def draw(self):
        c = self.canv
        bar_h = 5 * mm
        bar_y = 2 * mm

        # Label
        c.setFont(CJK_FONT, 9)
        c.setFillColor(DARK_TEXT)
        c.drawString(0, bar_y + 7, self.label)

        # Score text
        score_text = f"{self.score:.0f}%"
        c.setFillColor(MED_TEXT)
        c.drawRightString(self._width, bar_y + 7, score_text)

        # Background bar
        c.setFillColor(LIGHT_BORDER)
        c.roundRect(0, bar_y, self._width, bar_h, 1.5 * mm, fill=1, stroke=0)

        # Filled bar
        fill_w = self._width * (self.score / 100.0)
        # 先无条件初始化 color（避免低分时 fill_w<=0 导致下面 setFillColor(color) UnboundLocalError）
        color = LEVEL_COLORS.get(self.level, BRAND_PRIMARY)
        if fill_w > 1 * mm:
            c.setFillColor(color)
            c.roundRect(0, bar_y, fill_w, bar_h, 1.5 * mm, fill=1, stroke=0)

        # Level badge
        badge_text = f"{LEVEL_EMOJI.get(self.level, '')} {LEVEL_LABELS.get(self.level, '?')}"
        c.setFont(CJK_FONT, 7)
        c.setFillColor(color)
        c.drawString(fill_w + 3, bar_y + 7, badge_text)


class SectionHeader(Flowable):
    """Styled section title with left accent bar."""

    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self._height = 12 * mm

    def wrap(self, availWidth, availHeight):
        return (availWidth, self._height)

    def draw(self):
        c = self.canv
        # Accent bar
        c.setFillColor(BRAND_PRIMARY)
        c.rect(0, 2 * mm, 3 * mm, 8 * mm, fill=1, stroke=0)
        # Title
        c.setFont(CJK_FONT, 14)
        c.setFillColor(DARK_TEXT)
        c.drawString(6 * mm, 3 * mm, self.title)


# ─── Styles ──────────────────────────────────────────────────────────

def _build_styles() -> dict:
    """Build CJK-compatible paragraph styles."""
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "CN-Title", fontName=CJK_FONT, fontSize=20, leading=28,
            textColor=DARK_TEXT, alignment=TA_CENTER, spaceAfter=4 * mm,
        ),
        "subtitle": ParagraphStyle(
            "CN-Subtitle", fontName=CJK_FONT, fontSize=10, leading=14,
            textColor=MED_TEXT, alignment=TA_CENTER, spaceAfter=6 * mm,
        ),
        "h2": ParagraphStyle(
            "CN-H2", fontName=CJK_FONT, fontSize=14, leading=20,
            textColor=DARK_TEXT, spaceBefore=6 * mm, spaceAfter=3 * mm,
        ),
        "h3": ParagraphStyle(
            "CN-H3", fontName=CJK_FONT, fontSize=12, leading=17,
            textColor=DARK_TEXT, spaceBefore=4 * mm, spaceAfter=2 * mm,
        ),
        "body": ParagraphStyle(
            "CN-Body", fontName=CJK_FONT, fontSize=10, leading=16,
            textColor=DARK_TEXT, alignment=TA_JUSTIFY, spaceAfter=3 * mm,
        ),
        "body_small": ParagraphStyle(
            "CN-Body-Small", fontName=CJK_FONT, fontSize=9, leading=14,
            textColor=MED_TEXT, spaceAfter=2 * mm,
        ),
        "label": ParagraphStyle(
            "CN-Label", fontName=CJK_FONT, fontSize=9, leading=13,
            textColor=MED_TEXT, spaceAfter=1 * mm,
        ),
        "footer": ParagraphStyle(
            "CN-Footer", fontName=CJK_FONT, fontSize=8, leading=11,
            textColor=colors.HexColor("#94A3B8"), alignment=TA_CENTER,
        ),
    }


# ─── PDF Builders ────────────────────────────────────────────────────

def generate_teacher_pdf(report: Dict) -> bytes:
    """Generate teacher-report PDF and return raw bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"{report.get('child_name', '幼儿')} 教师版报告",
        author="萌芽数学 Mathsprout",
    )
    styles = _build_styles()
    story = _build_teacher_story(report, styles)
    doc.build(story)
    return buf.getvalue()


def generate_parent_pdf(report: Dict) -> bytes:
    """Generate parent-report PDF and return raw bytes."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=16 * mm,
        title=f"{report.get('child_name', '幼儿')} 成长观察记录",
        author="萌芽数学 Mathsprout",
    )
    styles = _build_styles()
    story = _build_parent_story(report, styles)
    doc.build(story)
    return buf.getvalue()


# ─── Teacher Report Layout ───────────────────────────────────────────

def _build_teacher_story(report: Dict, s: dict) -> list:
    story = []

    # ── Header ──
    child = report.get("child_name", "幼儿")
    age = report.get("age_group", "")
    date_str = _format_date(report.get("generated_at", ""))

    # Title block with background
    header_table = Table([
        [Paragraph(f"数学学习发展观察报告", s["title"])],
        [Paragraph(f"{child}  ·  {age}  ·  {date_str}", s["subtitle"])],
    ], colWidths=[PAGE_W - 36 * mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_LIGHT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [3 * mm, 3 * mm, 3 * mm, 3 * mm]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8 * mm))
    story.append(Paragraph("教师版 · 教学反思与专业发展", s["label"]))
    story.append(Spacer(1, 6 * mm))

    # ── PCK Analysis ──
    story.append(SectionHeader("PCK 核心经验分析"))
    story.append(Spacer(1, 4 * mm))
    dimensions = report.get("dimensions", [])
    for d in dimensions:
        dim_name = get_dimension_display_name(d.get("dimension", ""))
        score = d.get("score", 0)
        level = d.get("level", "L1")
        story.append(ProgressBar(dim_name, score, level))
        story.append(Spacer(1, 2 * mm))
        story.append(Paragraph(
            f"PCK阶段：{d.get('pck_stage', '')}　|　"
            f"基准对比：{d.get('age_benchmark_comparison', '')}",
            s["body_small"],
        ))
        story.append(Spacer(1, 2 * mm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_BORDER))
    story.append(Spacer(1, 4 * mm))

    # ── Dimension Details (granular sub-skills) ──
    story.append(SectionHeader("各维度粒化技能详情"))
    story.append(Spacer(1, 4 * mm))
    for d in dimensions:
        dim_name = get_dimension_display_name(d.get("dimension", ""))
        story.append(Paragraph(
            f"{d.get('level_emoji', '')} {dim_name} — {d.get('level_name', '')}（{d.get('score', 0):.0f}%）",
            s["h3"],
        ))
        sub_skills = d.get("sub_skills", [])
        if sub_skills:
            skill_data = [[
                Paragraph(sk["name"], s["body_small"]),
                Paragraph(f"{sk['score']:.0f}", s["body_small"]),
            ] for sk in sub_skills]
            skill_table = Table(
                skill_data,
                colWidths=[100 * mm, 40 * mm],
                hAlign="LEFT",
            )
            skill_table.setStyle(TableStyle([
                ("TEXTCOLOR", (0, 0), (-1, -1), DARK_TEXT),
                ("LINEBELOW", (0, 0), (-1, -2), 0.3, LIGHT_BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            ]))
            story.append(skill_table)
        story.append(Spacer(1, 3 * mm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_BORDER))
    story.append(Spacer(1, 4 * mm))

    # ── Error Diagnosis ──
    story.append(SectionHeader("典型错误诊断"))
    story.append(Spacer(1, 3 * mm))
    errors = report.get("typical_errors_diagnosis", [])
    if isinstance(errors, list) and errors:
        for i, err in enumerate(errors, 1):
            story.append(Paragraph(f"{i}. {err}", s["body"]))
    else:
        story.append(Paragraph(str(errors) if errors else "未发现明显错误模式", s["body"]))
    story.append(Spacer(1, 4 * mm))

    # ── Teaching Suggestions ──
    suggestions = report.get("teaching_suggestions", {})
    if suggestions:
        story.append(SectionHeader("教学建议与活动推荐"))
        story.append(Spacer(1, 3 * mm))
        for dim_name, sug in suggestions.items():
            story.append(Paragraph(f"<b>{dim_name}</b> — 当前：{sug.get('level', '')}", s["h3"]))
            story.append(Paragraph(f"课堂建议：{sug.get('recommendations', '')}", s["body"]))
            activities = sug.get("classroom_activities", [])
            if activities:
                for act in activities:
                    story.append(Paragraph(f"  · {act}", s["body_small"]))
            story.append(Paragraph(
                f"推荐材料：{sug.get('materials_suggestion', '')}",
                s["body_small"],
            ))
            story.append(Spacer(1, 2 * mm))
        story.append(Spacer(1, 4 * mm))

    # ── Reflection Questions ──
    reflections = report.get("teaching_reflection_questions", [])
    if reflections:
        story.append(SectionHeader("教学反思问题"))
        story.append(Spacer(1, 3 * mm))
        for i, q in enumerate(reflections, 1):
            story.append(Paragraph(f"{i}. {q}", s["body"]))
        story.append(Spacer(1, 4 * mm))

    # ── Overall Summary ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=LIGHT_BORDER))
    story.append(Spacer(1, 4 * mm))
    story.append(SectionHeader("综合评述"))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(report.get("overall_summary", ""), s["body"]))

    # ── Footer ──
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(_footer_text(), s["footer"]))

    return story


# ─── Parent Report Layout ────────────────────────────────────────────

def _build_parent_story(report: Dict, s: dict) -> list:
    story = []

    child = report.get("child_name", "幼儿")
    age = report.get("age_group", "")
    date_str = _format_date(report.get("generated_at", ""))

    # ── Header ──
    header_table = Table([
        [Paragraph(f"{child} 的数学成长记录", s["title"])],
        [Paragraph(f"{age}  ·  {date_str}", s["subtitle"])],
    ], colWidths=[PAGE_W - 36 * mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRAND_LIGHT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [3 * mm, 3 * mm, 3 * mm, 3 * mm]),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph(
        '这不是一份"成绩单"，而是一份观察记录。每个孩子都在以自己的节奏成长。',
        s["body_small"],
    ))
    story.append(Spacer(1, 6 * mm))

    # ── Overall Summary ──
    story.append(SectionHeader("整体观察"))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(report.get("overall_summary", "").replace("\n", "<br/>"), s["body"]))
    story.append(Spacer(1, 5 * mm))

    # ── Strengths ──
    strengths = report.get("strengths", [])
    if strengths:
        story.append(SectionHeader("宝宝的闪光时刻 ✨"))
        story.append(Spacer(1, 3 * mm))
        for item in strengths:
            story.append(Paragraph(
                f"<b>{item.get('emoji', '🌟')} {item.get('area', '')}</b>",
                s["h3"],
            ))
            story.append(Paragraph(item.get("description", ""), s["body"]))
            story.append(Paragraph(
                f"💡 在家可以观察：{item.get('parent_observation_tip', '')}",
                s["body_small"],
            ))
            story.append(Spacer(1, 3 * mm))
        story.append(Spacer(1, 3 * mm))

    # ── Growing Areas ──
    growing = report.get("growing_areas", [])
    if growing:
        story.append(SectionHeader("正在努力成长中 🌱"))
        story.append(Spacer(1, 3 * mm))
        for item in growing:
            story.append(Paragraph(
                f"<b>{item.get('emoji', '🌱')} {item.get('area', '')}</b>",
                s["h3"],
            ))
            story.append(Paragraph(item.get("description", ""), s["body"]))
            story.append(Paragraph(
                f"💡 在家可以观察：{item.get('parent_observation_tip', '')}",
                s["body_small"],
            ))
            story.append(Spacer(1, 3 * mm))
        story.append(Spacer(1, 3 * mm))

    # ── Family Activities ──
    activities = report.get("family_activities", [])
    if activities:
        story.append(SectionHeader("在家就能玩的数学小游戏 🎮"))
        story.append(Spacer(1, 3 * mm))
        for act in activities:
            story.append(Paragraph(f"<b>{act.get('title', '')}</b>", s["h3"]))
            story.append(Paragraph(f"材料：{act.get('materials', '')}", s["body_small"]))
            story.append(Paragraph(f"玩法：{act.get('steps', '')}", s["body"]))
            story.append(Paragraph(f"为什么好：{act.get('why', '')}", s["body_small"]))
            story.append(Spacer(1, 3 * mm))
        story.append(Spacer(1, 3 * mm))

    # ── Learning Quality ──
    quality = report.get("learning_quality_notes", "")
    if quality:
        story.append(SectionHeader("比'做对多少'更重要的事"))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(quality.replace("\n", "<br/>"), s["body"]))
        story.append(Spacer(1, 4 * mm))

    # ── Parent Tips ──
    tips = report.get("parent_tips", "")
    if tips:
        story.append(SectionHeader("给家长的温馨提醒 💝"))
        story.append(Spacer(1, 3 * mm))
        story.append(Paragraph(tips.replace("\n", "<br/>"), s["body"]))

    # ── Footer ──
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(_footer_text(), s["footer"]))

    return story


# ─── Helpers ─────────────────────────────────────────────────────────

def _format_date(iso_str: str) -> str:
    """Format ISO datetime string to Chinese date."""
    if not iso_str:
        return datetime.now().strftime("%Y年%m月%d日")
    try:
        dt = datetime.fromisoformat(iso_str)
        return dt.strftime("%Y年%m月%d日")
    except (ValueError, TypeError):
        return iso_str[:10] if len(iso_str) >= 10 else iso_str


def _footer_text() -> str:
    return (
        "本报告由萌芽数学 Mathsprout 自动生成 · "
        "基于《学前儿童数学学习与发展核心经验》PCK框架 · "
        "仅供教育参考"
    )
