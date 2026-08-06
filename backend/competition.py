"""
萌芽助手 Mathsprout — 教育智能体（比赛版）

单文件 Web 应用：FastAPI + 内嵌 HTML/CSS/JS。
零新依赖，纯 Python 运行。

启动: .\\venv\\Scripts\\python.exe app.py
访问: http://localhost:8000
"""

import json
import sys
import time
import base64
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, File, UploadFile, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

from app.services.image_processor import ImageProcessor, resolve_image_size
from app.services.worksheet_recognizer import WorksheetRecognizer
from app.services.assessment_engine import assess
from app.services.report_generator import generate_teacher_report, generate_parent_report
from app.core.prompts.pck_reference import (
    MILESTONES,
    SUB_SKILLS,
    ERROR_PATTERNS,
    AgeGroup,
    Dimension,
    DevLevel,
    get_age_display_name,
    get_dimension_display_name,
    get_level_description,
    COUNTING_PRINCIPLES,
    TEACHING_PRINCIPLES,
)


# ═══════════════════════════════════════════════════════════════════════════
# FastAPI App
# ═══════════════════════════════════════════════════════════════════════════

app = FastAPI(title="萌芽助手 Mathsprout", version="2.0-competition")

# Reusable recognizer instance (keeps cache warm)
_recognizer = None


def get_recognizer():
    global _recognizer
    if _recognizer is None:
        _recognizer = WorksheetRecognizer()
    return _recognizer


# ═══════════════════════════════════════════════════════════════════════════
# API: Analyze
# ═══════════════════════════════════════════════════════════════════════════

@app.post("/api/analyze")
async def analyze_worksheet(
    file: UploadFile = File(...),
    age_group: str = Form("middle"),
    child_name: str = Form("幼儿"),
    quality: str = Form("balanced"),
):
    """Full analysis pipeline: preprocess → recognize → assess → report."""
    try:
        # Read uploaded file
        file_bytes = await file.read()

        # Step 1: Preprocess
        t0 = time.time()
        processor = ImageProcessor(
            target_size_px=resolve_image_size(quality),
            max_size_px=2576,
            quality=85,
        )
        processed_bytes, out_filename = await processor.process(
            file_bytes, file.filename or "upload.jpg", file.content_type
        )
        t1 = time.time()

        # Step 2: Vision recognition
        recognizer = get_recognizer()
        vision_result = await recognizer.analyze(processed_bytes, age_group=age_group)
        t2 = time.time()

        meta = vision_result.get("_meta", {})
        problem_count = len(vision_result.get("problems", []))

        # Step 3: Assessment
        assessment_result = await assess(vision_result, age_group=age_group, child_name=child_name)
        t3 = time.time()

        # Step 4: Reports
        teacher_report = await generate_teacher_report(
            assessment_result, child_name=child_name, age_group=age_group
        )
        parent_report = await generate_parent_report(
            assessment_result, child_name=child_name, age_group=age_group
        )
        t4 = time.time()

        return JSONResponse({
            "success": True,
            "timing": {
                "preprocess": round(t1 - t0, 2),
                "vision": round(t2 - t1, 2),
                "assessment": round(t3 - t2, 2),
                "report": round(t4 - t3, 2),
                "total": round(t4 - t0, 2),
            },
            "meta": {
                "model": meta.get("model", "?"),
                "provider": meta.get("provider", "?"),
                "cache_hit": meta.get("cache_hit", False),
                "usage": meta.get("usage", {}),
                "problem_count": problem_count,
            },
            "assessment": assessment_result,
            "teacher_report": teacher_report,
            "parent_report": parent_report,
        })

    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


# ═══════════════════════════════════════════════════════════════════════════
# API: Demo Report (no AI call, uses preset data)
# ═══════════════════════════════════════════════════════════════════════════

DEMO_SCENARIOS = {
    "advanced": {
        "child": "小明", "age": "large",
        "vision": {
            "worksheet_type": "mixed", "problems": [
                {"id": "P1", "type": "shape_id", "child_answer": "三角形", "correct_answer": "三角形", "is_correct": True, "confidence": 0.95, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": ""},
                {"id": "P2", "type": "shape_id", "child_answer": "正方形", "correct_answer": "正方形", "is_correct": True, "confidence": 0.9, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": ""},
                {"id": "P3", "type": "spatial", "child_answer": "上面", "correct_answer": "上面", "is_correct": True, "confidence": 0.85, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": ""},
                {"id": "P4", "type": "add_10", "child_answer": "8", "correct_answer": "8", "is_correct": True, "confidence": 0.92, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": "mental"},
                {"id": "P5", "type": "counting", "child_answer": "10", "correct_answer": "10", "is_correct": True, "confidence": 0.9, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": "mental"},
                {"id": "P6", "type": "sub_10", "child_answer": "4", "correct_answer": "4", "is_correct": True, "confidence": 0.88, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": "mental"},
            ],
            "observations": {"overall_pck_notes": "幼儿表现出较强的图形感知和空间方位能力，运算思维已进入符号水平"},
        }
    },
    "typical": {
        "child": "小华", "age": "middle",
        "vision": {
            "worksheet_type": "mixed", "problems": [
                {"id": "P1", "type": "counting", "child_answer": "5", "correct_answer": "5", "is_correct": True, "confidence": 0.95, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": "counting_objects"},
                {"id": "P2", "type": "counting", "child_answer": "3", "correct_answer": "4", "is_correct": False, "confidence": 0.8, "handwriting_quality": "clear", "has_erasure": True, "erasure_pattern": "self_correct", "strategy_indicators": ""},
                {"id": "P3", "type": "add_10", "child_answer": "7", "correct_answer": "7", "is_correct": True, "confidence": 0.9, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": "finger_counting"},
                {"id": "P4", "type": "sub_10", "child_answer": "5", "correct_answer": "3", "is_correct": False, "confidence": 0.85, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": "counting_objects"},
                {"id": "P5", "type": "shape_id", "child_answer": "圆形", "correct_answer": "圆形", "is_correct": True, "confidence": 0.9, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": ""},
                {"id": "P6", "type": "pattern_next", "child_answer": "△", "correct_answer": "△", "is_correct": True, "confidence": 0.85, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": ""},
            ],
            "observations": {"overall_pck_notes": "幼儿处于中班典型发展水平，各维度表现基本符合年龄期望"},
        }
    },
    "developing": {
        "child": "小花", "age": "small",
        "vision": {
            "worksheet_type": "mixed", "problems": [
                {"id": "P1", "type": "counting", "child_answer": "3", "correct_answer": "5", "is_correct": False, "confidence": 0.8, "handwriting_quality": "clear", "has_erasure": True, "erasure_pattern": "persistent_error", "strategy_indicators": "counting_objects"},
                {"id": "P2", "type": "counting", "child_answer": "2", "correct_answer": "3", "is_correct": False, "confidence": 0.75, "handwriting_quality": "mirrored", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": "counting_objects"},
                {"id": "P3", "type": "classify", "child_answer": "红色", "correct_answer": "红色", "is_correct": True, "confidence": 0.9, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": ""},
                {"id": "P4", "type": "compare", "child_answer": "左边多", "correct_answer": "左边多", "is_correct": True, "confidence": 0.85, "handwriting_quality": "clear", "has_erasure": False, "erasure_pattern": "none", "strategy_indicators": ""},
            ],
            "observations": {"overall_pck_notes": "幼儿处于点数能力发展初期，手口一致点数尚不稳定，但分类与比较能力开始萌芽"},
        }
    },
}


@app.post("/api/demo/{scenario}")
async def get_demo_report(scenario: str):
    """Generate a demo report from preset scenario data (no AI call)."""
    if scenario not in DEMO_SCENARIOS:
        return JSONResponse({"success": False, "error": f"未知场景: {scenario}"}, status_code=404)

    demo = DEMO_SCENARIOS[scenario]
    assessment_result = await assess(demo["vision"], age_group=demo["age"], child_name=demo["child"])
    teacher_report = await generate_teacher_report(assessment_result, child_name=demo["child"], age_group=demo["age"])
    parent_report = await generate_parent_report(assessment_result, child_name=demo["child"], age_group=demo["age"])

    return JSONResponse({
        "success": True,
        "scenario": scenario,
        "child_name": demo["child"],
        "age_group": demo["age"],
        "age_display": get_age_display_name(demo["age"]),
        "assessment": assessment_result,
        "teacher_report": teacher_report,
        "parent_report": parent_report,
    })


# ═══════════════════════════════════════════════════════════════════════════
# API: PCK Knowledge Data
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/api/pck")
async def get_pck_data():
    """Return PCK knowledge base data for the frontend."""
    # Build error patterns by dimension
    error_by_dim = {}
    for ep in ERROR_PATTERNS:
        dims = ep.get("dimensions", [])
        for d in dims:
            if d not in error_by_dim:
                error_by_dim[d] = []
            error_by_dim[d].append({
                "name": ep.get("name", ""),
                "description": ep.get("description", ""),
                "age_groups": [get_age_display_name(ag) for ag in ep.get("age_groups", [])],
                "teaching_implication": ep.get("teaching_implication", ""),
            })

    return JSONResponse({
        "milestones": {
            age_key: {
                get_dimension_display_name(dim): items
                for dim, items in age_data.items()
            }
            for age_key, age_data in MILESTONES.items()
        },
        "sub_skills": {
            dim: items for dim, items in SUB_SKILLS.items()
        },
        "error_patterns": error_by_dim,
        "levels": {
            level.value: get_level_description(level)
            for level in [DevLevel.L1_SPROUT, DevLevel.L2_GROWING, DevLevel.L3_PROFICIENT, DevLevel.L4_ADVANCED]
        },
        "counting_principles": COUNTING_PRINCIPLES,
        "teaching_principles": TEACHING_PRINCIPLES,
    })


# ═══════════════════════════════════════════════════════════════════════════
# Main HTML Page
# ═══════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML_PAGE


HTML_PAGE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>萌芽助手 Mathsprout — 幼儿数学教育智能体</title>
<style>
  :root { --bg:#f8fafc; --card:#fff; --text:#1e293b; --sub:#64748b; --border:#e2e8f0;
    --pri:#6366f1; --pri2:#818cf8; --suc:#10b981; --war:#f59e0b; --err:#ef4444; --pin:#ec4899;
    --rad:12px; --sh:0 1px 3px rgba(0,0,0,.08),0 1px 2px rgba(0,0,0,.06); }
  * { box-sizing:border-box; margin:0; padding:0 }
  body { font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"PingFang SC","Microsoft YaHei",sans-serif;
    background:var(--bg); color:var(--text) }
  .app { max-width:1100px; margin:0 auto; padding:16px 20px }
  header { text-align:center; padding:28px 0 20px }
  header h1 { font-size:2rem; background:linear-gradient(135deg,var(--pri),var(--pin)); -webkit-background-clip:text;
    -webkit-text-fill-color:transparent; background-clip:text }
  header p { color:var(--sub); font-size:.95rem; margin-top:4px }

  /* Tabs */
  .tabs { display:flex; gap:4px; margin:16px 0; background:var(--card); border-radius:var(--rad);
    box-shadow:var(--sh); padding:4px; overflow-x:auto }
  .tab-btn { flex:1; min-width:100px; padding:10px 16px; border:none; background:transparent;
    border-radius:calc(var(--rad) - 4px); cursor:pointer; font-size:.92rem; color:var(--sub);
    transition:all .2s; white-space:nowrap }
  .tab-btn.active { background:var(--pri); color:#fff; font-weight:600 }
  .tab-btn:hover:not(.active) { background:#f1f5f9 }

  /* Panels */
  .panel { display:none }
  .panel.active { display:block }

  .card { background:var(--card); border-radius:var(--rad); box-shadow:var(--sh); padding:24px; margin-bottom:16px }
  .card h3 { font-size:1.1rem; margin-bottom:12px; color:var(--text) }
  .card h4 { font-size:.95rem; margin:12px 0 6px }

  /* Upload */
  .upload-zone { border:2px dashed var(--border); border-radius:var(--rad); padding:48px 24px;
    text-align:center; cursor:pointer; transition:all .2s }
  .upload-zone:hover { border-color:var(--pri2); background:#eef2ff }
  .upload-zone.has-file { border-color:var(--suc); background:#ecfdf5 }
  .upload-zone input { display:none }
  .upload-zone .icon { font-size:3rem; margin-bottom:8px }
  .upload-zone .hint { color:var(--sub); font-size:.85rem }
  .upload-zone .filename { color:var(--suc); font-weight:600; margin-top:8px }

  .form-row { display:flex; gap:12px; flex-wrap:wrap; margin-top:16px }
  .form-group { flex:1; min-width:150px }
  .form-group label { display:block; font-size:.85rem; font-weight:600; margin-bottom:4px; color:var(--sub) }
  .form-group select, .form-group input { width:100%; padding:10px 12px; border:1px solid var(--border);
    border-radius:var(--rad); font-size:.9rem; background:var(--card); color:var(--text) }

  /* Buttons */
  .btn { display:inline-flex; align-items:center; gap:6px; padding:10px 24px; border:none;
    border-radius:var(--rad); font-size:.9rem; font-weight:600; cursor:pointer; transition:all .2s }
  .btn-pri { background:var(--pri); color:#fff }
  .btn-pri:hover { background:var(--pri2); transform:translateY(-1px) }
  .btn-pri:disabled { background:#cbd5e1; cursor:not-allowed; transform:none }
  .btn-block { display:flex; width:100%; justify-content:center; margin-top:12px }

  /* Progress */
  .progress-wrap { margin:16px 0 }
  .progress-bar { height:8px; background:var(--border); border-radius:4px; overflow:hidden }
  .progress-fill { height:100%; background:linear-gradient(90deg,var(--pri),var(--pri2));
    border-radius:4px; transition:width .3s; width:0% }
  .progress-text { font-size:.85rem; color:var(--sub); margin-top:4px }

  /* Metrics */
  .metrics { display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:12px; margin:16px 0 }
  .metric { background:var(--card); border-radius:var(--rad); box-shadow:var(--sh); padding:16px;
    text-align:center; border-top:3px solid var(--pri) }
  .metric .score { font-size:2rem; font-weight:700 }
  .metric .label { font-size:.8rem; color:var(--sub); margin-top:2px }
  .metric .level { font-size:.85rem; margin-top:4px }

  /* Tags */
  .tag { display:inline-block; padding:2px 8px; border-radius:6px; font-size:.78rem; font-weight:600 }
  .tag-l1 { background:#fef2f2; color:var(--err) }
  .tag-l2 { background:#fffbeb; color:var(--war) }
  .tag-l3 { background:#ecfdf5; color:var(--suc) }
  .tag-l4 { background:#eef2ff; color:var(--pri) }

  /* Report sections */
  .report-section { margin:16px 0 }
  .report-section h4 { margin-bottom:8px }
  .strength-item, .growing-item { padding:8px 12px; border-radius:8px; margin:4px 0 }
  .strength-item { background:#ecfdf5; border-left:3px solid var(--suc) }
  .growing-item { background:#fff7ed; border-left:3px solid var(--war) }

  /* Accordion */
  .accordion { border:1px solid var(--border); border-radius:var(--rad); margin:8px 0; overflow:hidden }
  .accordion-header { padding:12px 16px; background:#f8fafc; cursor:pointer; font-weight:600;
    display:flex; justify-content:space-between; align-items:center; user-select:none }
  .accordion-header:hover { background:#f1f5f9 }
  .accordion-body { padding:12px 16px; display:none; border-top:1px solid var(--border) }
  .accordion.open .accordion-body { display:block }
  .accordion.open .accordion-header { background:#eef2ff }

  /* Knowledge cards */
  .k-card { border:1px solid var(--border); border-radius:var(--rad); padding:16px; margin:8px 0 }
  .k-card h4 { font-size:.95rem; margin-bottom:6px }
  .k-card ul { padding-left:20px; color:var(--sub); font-size:.9rem }
  .k-card li { margin:3px 0 }

  /* Timing */
  .timing { display:flex; gap:12px; flex-wrap:wrap; font-size:.8rem; color:var(--sub); margin:8px 0 }
  .timing span { background:#f1f5f9; padding:2px 8px; border-radius:4px }

  /* Toast */
  .toast { position:fixed; top:16px; right:16px; padding:12px 20px; border-radius:var(--rad); color:#fff;
    font-weight:600; z-index:100; display:none; animation:slideIn .3s }
  .toast.show { display:block }
  .toast-err { background:var(--err) }
  .toast-suc { background:var(--suc) }
  @keyframes slideIn { from{transform:translateX(100%);opacity:0} to{transform:translateX(0);opacity:1} }

  /* Responsive */
  @media (max-width:640px) {
    .app { padding:8px }
    .metrics { grid-template-columns:repeat(2,1fr) }
    header h1 { font-size:1.5rem }
  }

  /* Knowledge tab grid */
  .k-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:16px; margin:16px 0 }
  .k-grid .k-card { margin:0 }

  .dim-badge { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:4px }
  .dim-counting { background:var(--pri) }
  .dim-addsub { background:var(--war) }
  .dim-shapes { background:var(--suc) }
  .dim-patterns { background:var(--pin) }
</style>
</head>
<body>
<div class="app">
  <header>
    <h1>🌱 萌芽助手 Mathsprout</h1>
    <p>幼儿数学操作单 AI 识别 · PCK 四维度评估 · 双版发展报告</p>
  </header>

  <div class="tabs">
    <button class="tab-btn active" data-tab="upload">📷 上传分析</button>
    <button class="tab-btn" data-tab="demo">📊 演示报告</button>
    <button class="tab-btn" data-tab="pck">📚 PCK 知识库</button>
  </div>

  <!-- ═══════════════════ TAB: Upload ═══════════════════ -->
  <div id="panel-upload" class="panel active">
    <div class="card">
      <h3>📤 上传幼儿数学操作单</h3>
      <div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileInput').click()">
        <div class="icon">📸</div>
        <p>点击上传或拖拽图片到此处</p>
        <p class="hint">支持 JPG / PNG / WEBP / PDF，建议清晰拍照</p>
        <input type="file" id="fileInput" accept="image/jpeg,image/png,image/webp,application/pdf"
               onchange="onFileSelected(event)">
        <p class="filename" id="fileName"></p>
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>幼儿年龄段</label>
          <select id="ageGroup">
            <option value="small">小班（3-4岁）</option>
            <option value="middle" selected>中班（4-5岁）</option>
            <option value="large">大班（5-6岁）</option>
          </select>
        </div>
        <div class="form-group">
          <label>幼儿姓名（选填）</label>
          <input type="text" id="childName" value="幼儿" placeholder="幼儿">
        </div>
        <div class="form-group">
          <label>图片质量</label>
          <select id="quality">
            <option value="balanced" selected>🎯 均衡 (1080px)</option>
            <option value="fast">⚡ 快速 (720px)</option>
            <option value="accurate">🔬 精确 (1440px)</option>
          </select>
        </div>
      </div>
      <button class="btn btn-pri btn-block" id="analyzeBtn" disabled onclick="startAnalysis()">
        🔍 开始 AI 分析
      </button>
      <div class="progress-wrap" id="progressWrap" style="display:none">
        <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
        <p class="progress-text" id="progressText">准备中…</p>
        <div class="timing" id="timing"></div>
      </div>
    </div>

    <!-- Results area (populated dynamically) -->
    <div id="results"></div>
  </div>

  <!-- ═══════════════════ TAB: Demo ═══════════════════ -->
  <div id="panel-demo" class="panel">
    <div class="card">
      <h3>📊 演示报告</h3>
      <p style="color:var(--sub);margin-bottom:12px">选择一个预设场景，查看 AI 分析后生成的完整教师版和家长版报告示例。无需上传图片。</p>
      <div class="form-row">
        <div class="form-group" style="flex:2">
          <select id="demoScenario">
            <option value="advanced">🌟 优秀案例 — 大班小明，图形与空间能力强</option>
            <option value="typical" selected>🎯 典型案例 — 中班小华，各维度均衡发展</option>
            <option value="developing">🌱 发展中案例 — 小班小花，点数与模式正在成长</option>
          </select>
        </div>
        <div class="form-group" style="flex:0 0 auto">
          <button class="btn btn-pri btn-block" onclick="loadDemo()">🎬 生成演示报告</button>
        </div>
      </div>
    </div>
    <div id="demoResults"></div>
  </div>

  <!-- ═══════════════════ TAB: PCK ═══════════════════ -->
  <div id="panel-pck" class="panel">
    <div class="card">
      <h3>📚 PCK 教学内容知识框架</h3>
      <p style="color:var(--sub)">基于《学前儿童数学学习与发展核心经验》（PCK 理论），本框架是整个系统的知识底座。</p>
    </div>
    <div id="pckContent">加载中…</div>
  </div>
</div>

<div class="toast" id="toast"></div>

<script>
// ═══════════════════════════════ Tabs ═══════════════════════════════
document.querySelectorAll('.tab-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById('panel-' + btn.dataset.tab).classList.add('active');
    if (btn.dataset.tab === 'pck') loadPCK();
  });
});

// ═══════════════════════════════ Upload ═══════════════════════════════
let selectedFile = null;

function onFileSelected(e) {
  selectedFile = e.target.files[0];
  const zone = document.getElementById('uploadZone');
  const nameEl = document.getElementById('fileName');
  const btn = document.getElementById('analyzeBtn');
  if (selectedFile) {
    zone.classList.add('has-file');
    zone.querySelector('.icon').textContent = '✅';
    nameEl.textContent = '已选择: ' + selectedFile.name;
    btn.disabled = false;
  } else {
    zone.classList.remove('has-file');
    zone.querySelector('.icon').textContent = '📸';
    nameEl.textContent = '';
    btn.disabled = true;
  }
}

// Drag & drop
const dropZone = document.getElementById('uploadZone');
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.style.borderColor = 'var(--pri2)'; });
dropZone.addEventListener('dragleave', e => { e.preventDefault(); dropZone.style.borderColor = ''; });
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.style.borderColor = '';
  if (e.dataTransfer.files.length) {
    selectedFile = e.dataTransfer.files[0];
    dropZone.classList.add('has-file');
    dropZone.querySelector('.icon').textContent = '✅';
    document.getElementById('fileName').textContent = '已选择: ' + selectedFile.name;
    document.getElementById('analyzeBtn').disabled = false;
  }
});

// ═══════════════════════════════ Analyze ═══════════════════════════════
async function startAnalysis() {
  if (!selectedFile) return;
  const btn = document.getElementById('analyzeBtn');
  btn.disabled = true;
  btn.textContent = '⏳ 分析中…';
  document.getElementById('progressWrap').style.display = 'block';
  document.getElementById('results').innerHTML = '';

  const form = new FormData();
  form.append('file', selectedFile);
  form.append('age_group', document.getElementById('ageGroup').value);
  form.append('child_name', document.getElementById('childName').value || '幼儿');
  form.append('quality', document.getElementById('quality').value);

  // Progress simulation
  const steps = [
    {pct:10, text:'🖼️ 正在预处理图片…'},
    {pct:20, text:'🤖 正在调用 AI 视觉识别（可能需要 15-30 秒）…'},
    {pct:50, text:'📊 正在评估能力发展水平…'},
    {pct:75, text:'📝 正在生成报告…'},
  ];
  let stepIdx = 0;
  const progressInterval = setInterval(() => {
    if (stepIdx < steps.length) {
      const s = steps[stepIdx];
      document.getElementById('progressFill').style.width = s.pct + '%';
      document.getElementById('progressText').textContent = s.text;
      stepIdx++;
    }
  }, 800);

  try {
    const resp = await fetch('/api/analyze', { method:'POST', body:form });
    const data = await resp.json();
    clearInterval(progressInterval);

    if (!data.success) {
      showToast('分析失败: ' + (data.error || '未知错误'), 'err');
      document.getElementById('progressFill').style.width = '0%';
      document.getElementById('progressText').textContent = '失败';
    } else {
      document.getElementById('progressFill').style.width = '100%';
      document.getElementById('progressText').textContent = '✅ 分析完成！';
      renderTiming(data.timing);
      renderResults(data);
    }
  } catch (err) {
    clearInterval(progressInterval);
    showToast('网络错误: ' + err.message, 'err');
  }
  btn.disabled = false;
  btn.textContent = '🔍 开始 AI 分析';
}

function renderTiming(t) {
  document.getElementById('timing').innerHTML =
    `<span>🖼️ 预处理 ${t.preprocess}s</span>` +
    `<span>🤖 AI识别 ${t.vision}s</span>` +
    `<span>📊 评估 ${t.assessment}s</span>` +
    `<span>📝 报告 ${t.report}s</span>` +
    `<span>⏱️ 总计 ${t.total}s</span>`;
}

function renderResults(data) {
  const a = data.assessment;
  const t = data.teacher_report;
  const p = data.parent_report;
  const m = data.meta;

  let html = '';

  // Meta info
  html += `<div class="card"><div style="display:flex;gap:16px;flex-wrap:wrap;font-size:.85rem;color:var(--sub)">`;
  html += `<span>🤖 ${m.model || '?'}</span><span>📋 ${m.problem_count || 0} 道题</span>`;
  if (m.cache_hit) html += `<span>💾 缓存命中</span>`;
  html += `<span>🔤 Token: ${m.usage?.total_tokens || '?'}</span>`;
  html += `</div></div>`;

  // Metric cards
  html += `<div class="metrics">`;
  const dims = a.assessment || [];
  dims.forEach(d => {
    const lvl = d.level || 'L1';
    html += `<div class="metric" style="border-top-color:${levelColor(lvl)}">`;
    html += `<div class="score">${d.score || 0}<span style="font-size:.7em">%</span></div>`;
    html += `<div class="label">${d.display_name || d.dimension || ''}</div>`;
    html += `<div class="level"><span class="tag tag-${lvl.toLowerCase()}">${d.level_emoji||''} ${d.level_name||''}</span></div>`;
    html += `</div>`;
  });
  html += `</div>`;

  // Teacher Report
  html += `<div class="card"><h3>📋 教师版报告 — PCK 分析</h3>`;
  html += `<p>${t.pck_analysis || ''}</p>`;

  // Per dimension detail
  dims.forEach(d => {
    html += `<div class="accordion">`;
    html += `<div class="accordion-header" onclick="this.parentElement.classList.toggle('open')">`;
    html += `${d.display_name||''} — ${d.level_emoji||''} ${d.level_name||''} (${d.score||0}%)`;
    html += `<span>▼</span></div>`;
    html += `<div class="accordion-body">`;
    html += `<p><b>PCK 阶段：</b>${d.pck_stage||'暂无'}</p>`;
    html += `<p><b>年龄基准对比：</b>${d.age_benchmark_comparison||''}</p>`;
    html += `<p><b>该年龄段期望：</b>${d.age_milestones||'暂无数据'}</p>`;
    if (d.recommendations) html += `<p><b>教学建议：</b>${d.recommendations}</p>`;
    if (d.sub_skills && d.sub_skills.length) {
      html += `<p><b>子技能得分：</b></p>`;
      d.sub_skills.forEach(s => {
        html += `<span style="display:inline-block;margin:2px 4px;padding:2px 8px;background:#f1f5f9;border-radius:4px;font-size:.85rem">${s.name}: ${s.score.toFixed(0)}%</span>`;
      });
    }
    html += `</div></div>`;
  });
  html += `</div>`;

  // Error diagnosis
  if (t.error_diagnosis && t.error_diagnosis.length) {
    html += `<div class="card"><h3>🔍 发展性现象诊断</h3>`;
    t.error_diagnosis.forEach(e => { html += `<p>• ${e}</p>`; });
    html += `</div>`;
  }

  // Parent Report
  html += `<div class="card"><h3>👨‍👩‍👧 家长版报告</h3>`;
  const strengths = p.strengths || [];
  const growing = p.growing_areas || [];

  html += `<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">`;
  html += `<div><h4>🌟 优势领域</h4>`;
  strengths.forEach(s => html += `<div class="strength-item"><b>${s.dimension||''}</b>: ${s.detail||''}</div>`);
  if (!strengths.length) html += `<p style="color:var(--sub)">暂无数据</p>`;
  html += `</div><div><h4>🌱 成长领域</h4>`;
  growing.forEach(g => html += `<div class="growing-item"><b>${g.dimension||''}</b>: ${g.detail||''}</div>`);
  if (!growing.length) html += `<p style="color:var(--sub)">暂无数据</p>`;
  html += `</div></div>`;

  // Family activities
  const acts = p.family_activities || [];
  if (acts.length) {
    html += `<h4 style="margin-top:12px">🎮 推荐家庭游戏</h4>`;
    acts.forEach(a => {
      html += `<div class="strength-item" style="margin:4px 0">`;
      html += `<b>${a.title||''}</b><br>📦 ${a.materials||''}<br>📝 ${a.steps||''}</div>`;
    });
  }
  html += `</div>`;

  // Overall summary
  html += `<div class="card"><h3>💬 综合评语</h3>`;
  html += `<p style="color:var(--sub)">${a.overall_summary||''}</p>`;
  html += `</div>`;

  document.getElementById('results').innerHTML = html;
}

// ═══════════════════════════════ Demo ═══════════════════════════════
async function loadDemo() {
  const scenario = document.getElementById('demoScenario').value;
  document.getElementById('demoResults').innerHTML = '<div class="card"><p>⏳ 正在生成演示报告…</p></div>';
  try {
    const resp = await fetch('/api/demo/' + scenario, { method:'POST' });
    const data = await resp.json();
    if (data.success) {
      // Reuse the same render with a fake timing
      document.getElementById('timing').innerHTML = '<span>🎬 演示模式（跳过AI调用）</span>';
      renderResults(data);
      document.getElementById('demoResults').innerHTML = document.getElementById('results').innerHTML;
      document.getElementById('results').innerHTML = '';
      showToast('✅ 演示报告已生成 — ' + data.child_name + '（' + data.age_display + '）', 'suc');
    }
  } catch (err) {
    showToast('加载失败: ' + err.message, 'err');
  }
}

// ═══════════════════════════════ PCK ═══════════════════════════════
let pckData = null;

async function loadPCK() {
  if (pckData) { renderPCK(pckData); return; }
  try {
    const resp = await fetch('/api/pck');
    pckData = await resp.json();
    renderPCK(pckData);
  } catch (err) {
    document.getElementById('pckContent').innerHTML = '<p style="color:var(--err)">加载失败</p>';
  }
}

function renderPCK(d) {
  let html = '';

  // Levels
  html += `<div class="card"><h3>📊 发展水平判定 (L1-L4)</h3><div class="metrics">`;
  Object.entries(d.levels).forEach(([k,v]) => {
    html += `<div class="metric" style="border-top-color:${levelColor(k)}">`;
    html += `<div class="score" style="font-size:1.2rem">${v.emoji||''} ${v.name||''}</div>`;
    html += `<div class="level"><span class="tag tag-${k.toLowerCase()}">${k}</span></div>`;
    html += `<div class="label">${v.meaning||''}</div>`;
    html += `<div class="label">PCK: ${v.pck_stage||''}</div>`;
    html += `</div>`;
  });
  html += `</div></div>`;

  // Milestones
  html += `<div class="card"><h3>📈 年龄段发展里程碑</h3>`;
  const ageKeys = ['small','middle','large'];
  ageKeys.forEach(ak => {
    const adata = d.milestones[ak] || {};
    html += `<div class="accordion"><div class="accordion-header" onclick="this.parentElement.classList.toggle('open')">`;
    html += `${ak==='small'?'小班（3-4岁）':ak==='middle'?'中班（4-5岁）':'大班（5-6岁）'}<span>▼</span></div>`;
    html += `<div class="accordion-body">`;
    Object.entries(adata).forEach(([dim, items]) => {
      html += `<h4>${dim}</h4><ul>`;
      items.forEach(i => { html += `<li>${i}</li>`; });
      html += `</ul>`;
    });
    html += `</div></div>`;
  });
  html += `</div>`;

  // Sub-skills
  html += `<div class="card"><h3>🎯 四维评估体系与子技能</h3><div class="k-grid">`;
  Object.entries(d.sub_skills).forEach(([dim, skills]) => {
    html += `<div class="k-card"><h4>${dim}</h4><ul>`;
    skills.forEach(s => { html += `<li>${s}</li>`; });
    html += `</ul></div>`;
  });
  html += `</div></div>`;

  // Counting principles
  if (d.counting_principles) {
    html += `<div class="card"><h3>🧠 格尔曼计数五原则</h3><ul>`;
    Object.entries(d.counting_principles).forEach(([k,v]) => {
      html += `<li><b>${k}</b> — ${v}</li>`;
    });
    html += `</ul></div>`;
  }

  // Error patterns
  html += `<div class="card"><h3>⚠️ 发展性错误模式库</h3>`;
  html += `<p style="color:var(--sub);margin-bottom:8px">这些是幼儿数学发展中正常的阶段性现象，是成长的足迹。</p>`;
  Object.entries(d.error_patterns).forEach(([dim, patterns]) => {
    if (!patterns.length) return;
    html += `<div class="accordion"><div class="accordion-header" onclick="this.parentElement.classList.toggle('open')">`;
    html += `${dim} — ${patterns.length} 种常见模式<span>▼</span></div>`;
    html += `<div class="accordion-body">`;
    patterns.forEach(ep => {
      html += `<div class="k-card"><b>${ep.name}</b> (${(ep.age_groups||[]).join('、')})<br>`;
      html += `<span style="color:var(--sub)">${ep.description||''}</span><br>`;
      html += `<span style="color:var(--pri)">💡 ${ep.teaching_implication||''}</span></div>`;
    });
    html += `</div></div>`;
  });
  html += `</div>`;

  document.getElementById('pckContent').innerHTML = html;
}

// ═══════════════════════════════ Helpers ═══════════════════════════════
function levelColor(lvl) {
  return {L1:'#ef4444',L2:'#f59e0b',L3:'#10b981',L4:'#6366f1'}[lvl] || '#6366f1';
}

function showToast(msg, type) {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = 'toast toast-' + type + ' show';
  setTimeout(() => { t.classList.remove('show'); }, 3000);
}
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import io
    import sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("Mathsprout Competition App")
    print("   URL: http://localhost:8000")
    print("   API docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
