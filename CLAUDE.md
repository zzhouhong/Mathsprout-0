# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

萌芽助手 Mathsprout — 基于 Claude Vision API 的幼儿数学操作单识别与能力发展评估系统。

## 常用命令

```bash
# 后端（本地 venv — Docker 网络不稳定时的首选方式）
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端（开发模式，--webpack 是因为 SWC 二进制在 Windows 上有兼容问题）
cd frontend
npm run dev            # 即 next dev --webpack

# 前端构建
cd frontend
npm run build          # next build --webpack

# 测试（全部）
cd backend
python -m pytest tests/ -v

# 测试（单个文件/用例）
cd backend
python -m pytest tests/test_assessment_engine.py -v
python -m pytest tests/test_assessment_engine.py::test_counting_dimension -v

# 测试（场景回归 — 29 条 PCK 规则验证）
cd backend
python -m pytest tests/test_scenarios.py -v

# 独立评估核心 CLI（零 AI 调用，JSON→评估+双报告）
cd backend
.\venv\Scripts\python.exe assess.py --demo --format markdown
.\venv\Scripts\python.exe assess.py --input tests/scenarios/

# 视觉识别独立评估（单图→3-pass 识别，支持 --provider claude/qwen）
cd backend
.\venv\Scripts\python.exe vision_eval.py --image tests/images/ws.jpg --provider claude --format markdown

# Docker（仅用于 PostgreSQL — 拉取新镜像可能失败）
docker run -d --name kindergarten-db \
  -e POSTGRES_DB=kindergarten_math \
  -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 postgres:16-alpine

# 数据库迁移
cd backend
.\venv\Scripts\python.exe -m alembic upgrade head
```

## 核心架构：分析管线

```
上传图片 → image_processor.py → worksheet_recognizer.py → assessment_engine.py → report_generator.py
              (预处理)              (Claude Vision API)       (4维度评分)          (双版报告)
```

### 数据流
1. **`image_processor.py`** — 缩放/格式转换/PDF 提取 → 输出规范化 PNG
2. **`worksheet_recognizer.py`** — 调用 Claude Vision API，传入 PCK 知识库作为 system prompt（开启 ephemeral caching），要求结构化 JSON 输出。内置指数退避重试（最多 3 次）+ 图片哈希内存缓存。
3. **`assessment_engine.py`** — 将识别结果（题目列表）映射到 4 个维度，按年龄段锚定评分，判定 L1-L4 发展水平，检测已知错误模式（镜像书写、运算混淆、实物依赖等），生成粒化学科技能分。
4. **`report_generator.py`** — 教师版（PCK 分析 + 教学反思 + 错误诊断 + 雷达图）和家长版（优势/成长区 + 家庭游戏 + 学习品质 — **严格禁用"分数/排名/落后/成绩"等词**）。

### PCK 框架（系统基石）
`backend/app/core/prompts/pck_reference.py` 是整个系统的知识底座，被三处消费：
- `worksheet_recognizer.py`：构建 system prompt
- `assessment_engine.py`：维度映射 + 水平判定 + 错误模式
- `report_generator.py`：报告语言 + 教学建议

关键枚举：
- **AgeGroup**: `small`（小班 3-4岁）, `middle`（中班 4-5岁）, `large`（大班 5-6岁）
- **Dimension**: `counting`, `addition_sub`, `shapes_space`, `patterns`
- **DevLevel**: `L1` 萌芽 0-40%, `L2` 发展 41-70%, `L3` 熟练 71-90%, `L4` 进阶 91-100%
- 每个年龄段×维度都有具体的 `MILESTONES` 期望表现条目

### 数据库：双模式

ORM 模型定义在 `backend/app/models/__init__.py`（7个模型：Child → Worksheet → AnalysisResult → ProblemResult + AbilityAssessment + Report + AIRequestLog）。

开发环境用 SQLite（`backend/.env` 中 `DATABASE_URL=sqlite+aiosqlite:///...`），生产用 PostgreSQL。`database.py` 的引擎会检测 URL scheme，SQLite 模式下跳过连接池配置。启动时自动执行 `Base.metadata.create_all()`（生产环境应用 Alembic 迁移替代）。

### 后端关键模式

- **配置**: `pydantic-settings` 的 `BaseSettings`，自动读 `.env`。通过 `get_settings()` 获取（有 `@lru_cache`）。
- **数据库会话**: `get_db()` 是 FastAPI dependency，yield 异步会话 + 自动 commit/rollback。
- **JWT 认证**: `core/security.py` — PBKDF2-SHA256 密码哈希，`get_current_user` / `get_current_teacher` / `get_current_admin` 三个 FastAPI Depends 保护端点。
- **重试策略**: `worksheet_recognizer.py` 的 `RETRYABLE_ERRORS` 包括 `APITimeoutError`, `APIConnectionError`, `RateLimitError`, `InternalServerError`，最多重试 3 次，指数退避 2s→4s→8s（上限 30s）。

### 前端关键模式

- **API 客户端**: `lib/api-client.ts` 暴露 `api` 对象，按模块组织——`api.auth.login()`, `api.children.list()`, `api.worksheets.uploadAndAnalyze()` 等。自动从 localStorage 注入 Bearer token。FormData 上传时不设 Content-Type（让浏览器自动带 boundary）。
- **Auth 流程**: `AuthProvider`（`lib/auth-context.tsx`）挂载时从 localStorage 恢复 token → 调 `/auth/me` 验证 → 设 user state。`login()` 成功后设 token + user。`logout()` 清 token + user。
- **分析页组件拆分**: 原 520 行单体页面拆为 6 个组件：`UploadPanel`, `AnalysisSettingsPanel`, `AnalysisProgress`, `AssessmentOverview`, `TeacherReportView`, `ParentReportView`。
- **SSE 流式分析**: `worksheets.analyzeWithStream()` 读取 `text/event-stream`，逐行解析 `data: {...}` 事件，通过 `onProgress` 回调推送进度。

## 路由注册

`app/main.py` 中按以下 prefix 注册：
| Router | Prefix | 依赖 |
|--------|--------|------|
| auth | `/api/v1/auth` | 无（公开） |
| worksheets | `/api/v1/worksheets` | 部分需认证 |
| analysis | `/api/v1/analysis` | 无（demo） |
| reports | `/api/v1/reports` | GET by id 公开，history 需认证 |
| tracking | `/api/v1/tracking` | class-analysis 需教师认证 |
| children | `/api/v1/children` | 需认证 |

## Demo 账户

- 教师: `teacher@kindergarten.cn` / `demo123`
- 管理员: `admin@kindergarten.cn` / `admin123`

## 当前环境状态 (2026-06-18)

- **运行时**: 后端 `localhost:8000` (venv + uvicorn)，前端 `localhost:3000` (npm run dev)，PostgreSQL `localhost:5432` (Docker 容器)
- **Python**: 3.12.10 (venv: `backend\venv`)
- **Node**: v24.16.0
- **Claude 模型**: `claude-sonnet-4-6`（在 `backend/.env` 中配置 `ANTHROPIC_MODEL`）
- **Docker 已知问题**: Docker Desktop 无法拉取新镜像（IPv6 连接 Docker Hub 失败），已有本地镜像可正常用
- **前端已知问题**: SWC 二进制 (`@next/swc-win32-x64-msvc`) 无效，自动回退 WASM；需用 `--webpack` 模式
