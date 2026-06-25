# 幼儿园数学教育智能体 — 项目完整档案

> 导出时间: 2026-06-21
> 总计优化: Phase 1-4, 38 项

---

## 项目概要

幼儿园数学教育智能体 — 基于 AI Vision 的幼儿数学操作单识别与能力发展评估系统。

- **技术栈**: FastAPI (Python 3.12) + Next.js (React/TypeScript) + SQLite + AI Vision API
- **路径**: `C:\Users\Zred\Desktop\first CC`
- **AI 模型**: 阿里云百炼 `qwen-vl-max`（OpenAI 兼容 SDK）

---

## 启动命令

```bash
# 后端
cd "C:\Users\Zred\Desktop\first CC\backend"
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端
cd "C:\Users\Zred\Desktop\first CC\frontend"
npm run dev    # next dev --webpack
```

## Demo 账户

- 教师: `teacher@kindergarten.cn` / `demo123`
- 管理员: `admin@kindergarten.cn` / `admin123`

---

## 核心架构：分析管线

```
上传图片 → image_processor.py → worksheet_recognizer.py → assessment_engine.py → report_generator.py
              (预处理)              (AI Vision API)           (4维度评分)          (双版报告)
```

### PCK 框架

`backend/app/core/prompts/pck_reference.py` 是知识底座

- **AgeGroup**: small（小班 3-4岁）, middle（中班 4-5岁）, large（大班 5-6岁）
- **Dimension**: counting, addition_sub, shapes_space, patterns
- **DevLevel**: L1 萌芽 0-40%, L2 发展 41-70%, L3 熟练 71-90%, L4 进阶 91-100%

---

## API 端点（44个）

| Router | Prefix | 说明 |
|--------|--------|------|
| auth | `/api/v1/auth` | 公开 |
| worksheets | `/api/v1/worksheets` | 部分需认证 |
| analysis | `/api/v1/analysis` | demo |
| reports | `/api/v1/reports` | GET by id 公开 |
| tracking | `/api/v1/tracking` | 教师认证 |
| children | `/api/v1/children` | 需认证 |
| games | `/api/v1/games` | 需认证（11个端点） |

---

## 已完成优化全览

### Phase 1（8项）
数据库模型、评估引擎、分析端点、SSE 推送、API 重试、PDF 支持、缓存服务、前端集成

### Phase 2（6项）
Alembic 迁移、JWT 认证、纵向追踪、班级分析、测试套件、摄像头拍照

### Phase 3（8项）
全局错误处理、幼儿 CRUD、报告持久化、前端 API 客户端、Auth 集成、分析页组件拆分、演示报告页、布局导航改进

### Phase 4（16项 — 互动游戏系统）
游戏逻辑引擎、游戏配置库、动态操作单生成器、游戏进度追踪、ORM 模型扩展、游戏 API 路由、操作单生成 API、游戏中心页面、游戏交互面板、操作单生成页面、成就进度页面、家长访问功能、报告历史页面、成长轨迹页面、班级分析页面、侧边栏+仪表板导航

---

## 6 类数学游戏

| ID | 名称 | 维度 | 难度 |
|----|------|------|------|
| counting | 数数小达人 | counting | 1-5 |
| addition_sub | 运算小能手 | addition_sub | 1-5 |
| shapes_space | 图形探险家 | shapes_space | 1-5 |
| patterns | 模式小侦探 | patterns | 1-5 |
| mixed | 综合挑战 | mixed | 1-3 |
| daily_challenge | 每日闯关 | mixed | 自适应 |

---

## 项目文件统计

- 后端：33 个 Python 文件
- 前端：33 个 TS/TSX 文件
- 测试：5 文件，71 通过
- ORM 模型：9 个

---

## 已知问题

1. 前端 SWC 二进制无效，必须用 `--webpack` 模式
2. Docker 无法拉取新镜像（IPv6 连 Docker Hub 失败）
3. `.env` 改动不触发 uvicorn `--reload`，需手动重启
4. SQLite schema 变更需删库重建
5. API 首次请求可能较慢（uvicorn reload 延迟）
