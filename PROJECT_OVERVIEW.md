# Mathsprout-0 项目理解（接手笔记）

> 本地接手时间：2026-08-03
> 维护者：ujvu（你） + zzhouhong（owner）
> 用途：省级幼儿园教育智能体比赛（非商业产品）
> 上游：https://github.com/zzhouhong/Mathsprout-0

## 一句话定位

**萌芽数学 Mathsprout**——基于 AI Vision（qwen-vl-max / Claude Vision 双提供商可切换）的**幼儿园数学操作单识别 + 能力发展评估系统**，依据《学前儿童数学学习与发展核心经验》（黄瑾、田方 2015）构建 PCK 知识底座，输出**教师版（含反思）+ 家长版（禁用"分数/排名/落后"字眼）**双份报告。

## 关键事实速览

| 项 | 数字 / 描述 |
|---|---|
| 贡献者 | ujvu **16 commits**、zzhouhong **1 commit**（PR #2 合并），外加 `Zred` 2 个 init commit |
| 累计 commits | 19 条（main） |
| 后端 | FastAPI + SQLAlchemy + SQLite（开发）/ PostgreSQL（生产），Python 3.12 |
| 前端 | Next.js 16 + React 19 + Tailwind v4，**必须** `npm run dev`（即 `--webpack`，SWC 二进制在 Windows 失效） |
| 评估核心 | 4 主维度 × 13 子维度 × 3 年龄段（小/中/大班）× 4 等级（L1-L4）+ 18 个错误模式 |
| AI 识别 | 3-pass：Pass1 读印刷题 → Pass2 题型归类 → Pass3 读幼儿笔迹；Pass3 失败时 `_opencv_circle_fallback` |
| 默认 Provider | `offline`（无 API key 也能跑完整闭环，CI 友好） |
| Demo 账户 | 教师 `teacher@kindergarten.cn / demo123`、管理员 `admin@kindergarten.cn / admin123`、3 个示范幼儿 + 访问码 `XIAOMING01/XIAOHONG02/XIAOHUA003` |
| 测试 | 16 个测试文件、~3.3k 行；CI 跳 `test_vision_golden.py` 与 `test_parent_dashboard_api.py` |

## 你的 commit 历史（参考）

```
2026-07-26  fix(miniprogram): 修复报告路由与操作单预览
2026-07-26  fix(backend): 教师批注从内存字典改为数据库持久化（Bug#8/#9）
2026-07-26  fix(frontend): demo 报告页加 ?id= 支持 + 移除真实报告时的「演示」后缀
2026-07-26  fix(backend): 修复 3 个 API bug（手动 API 测试发现）
2026-07-26  fix(frontend): 家长端 3 个真实可用性 bug
2026-07-26  fix(miniprogram): 去除遗漏文件的 BOM + fix(frontend): child-detail 跳真实报告
2026-07-25  fix: offline 模式不再 500 + 绑定页补教师入口
2026-07-25  fix(miniprogram): 去除所有 json/wxss/wxml 文件的 BOM 残留
2026-07-25  feat(miniprogram): 完善家长端体验与教师端功能闭环（6 项）
2026-07-25  fix(frontend): next.config.js 补 ignoreBuildErrors 与 .ts 一致
2026-07-25  ci: 修复 CI 配置，让 backend 通过、frontend 能构建
2026-07-24  feat(miniprogram): 完善小程序 4 项功能
2026-07-24  fix(frontend): 修复 4 类 bug
2026-07-24  test: 补全 4 个 service 的单元测试（78 个用例）
2026-07-24  fix(security): 修复 4 个安全风险
2026-07-24  feat(vision): 新增 offline 视觉 provider，无 API key 也能跑通完整闭环
```

## 核心架构（数据流）

```
教师浏览器 / 家长浏览器 / 微信小程序
  │
  ▼
Next.js 前端  :3000  ──rewrites──▶  FastAPI 后端 :8000
                                      │
                                      ├─ image_processor.py        (预处理：缩放/CLAHE/锐化/deskew/PDF)
                                      ├─ worksheet_recognizer.py   (3-pass Vision + 重试 + LRU 缓存)
                                      │     ├─ Pass1: 读印刷题
                                      │     ├─ Pass2: 题型归类 + 标准答案
                                      │     └─ Pass3: 读幼儿笔迹（裁剪 + 3x 放大）
                                      │           └─ 失败时 _opencv_circle_fallback
                                      ├─ pck_reference.py          (PCK 知识底座)
                                      ├─ assessment_engine.py      (4 维评分 + L1-L4 + 18 错模式)
                                      ├─ report_generator.py       (教师版 + 家长版)
                                      ├─ memory_service.py         (B5-B8 智能体记忆)
                                      └─ db: SQLite (开发) / PostgreSQL (生产)
```

## 改一个功能要看哪些文件（速查表）

| 你想改... | 主要文件 |
|---|---|
| 一种新题型如何被识别/评估/报告 | `worksheet_recognizer.py:91-179`、`pck_reference.py:229-246`+`681-801`、`assessment_engine.py:38-60`、`report_generator.py:_build_*_*` |
| 教师报告的某段文案（如教学反思） | `report_generator.py:339-410`、`418-447` |
| 家长报告的某段文案 | `report_generator.py:142-272`、`471-` |
| 新的"核心经验关键词" | `pck_reference.py:1354-1456` |
| 某年龄段某维度的里程碑 | `pck_reference.py:91-197` |
| 评分阈值（小/中/大班） | `pck_reference.py:1214-1218` (`AGE_LEVEL_THRESHOLDS`) |
| 图像预处理参数 | `image_processor.py:53-58` |
| SSE 事件类型 | 后端 `worksheets.py:_stream_progress`，前端 `api-client.ts:627-695` |
| 智能体记忆行为（B5-B8） | `backend/app/services/memory_service.py` + `report_generator.py:30-200` |
| 操作单生成 | `worksheet_generator.py`（933 行） |
| 家长端 API | `backend/app/api/routes/parent.py`、`dashboard.py` |
| CI 检查 | `.github/workflows/ci.yml` |

## 已知风险与 TODO（接手后第一周建议优先看）

### P0（比赛前必修，作者立项）
1. 评估页教师/家长报告 Tab 切换修复
2. 评估过程接入真实分析结果
3. AI 助学页改为左右并排布局
4. Demo 演示流程完善

### P0.5 UI 卡通化（3 小时）— 最大比赛加分项
基于 `kid-theme` 三板块卡通化 + 吉祥物贯穿

### Bug 风险
1. **`/analyze` 端点用 hash 推断文件路径**（`worksheets.py:154-177`），多并发会拿错文件
2. **`/analyze-stream` SSE 完成后又调一次** `uploadAndAnalyze`（`api-client.ts:680-683`）—— 实际多花一次 AI 调用
3. **`auth-context.tsx:5`** 类型断言不安全，过期 token 也能拿到对象
4. **PDF 上传缺后端依赖**（`requirements.txt` 把两个 PDF 库都注释掉）

### 文档与代码不一致
- CLAUDE.md 提到 "ephemeral caching" 但代码未实现
- `智能体完整档案.md` 报告 "208 passed"，但测试文件 16 个、CI 跳过 2 个

### 架构债
- `PROBLEM_TYPE_TO_DIMENSION` 双重定义（`pck_reference.py:229` vs `assessment_engine.py:40-60`）
- 死代码：`_detect_circled_number`、`_call_pass_dual_image`、`_call_anthropic_dual`、`_call_openai_compatible_dual`、`_single_pass_analyze`、`_build_system_prompt` 都未调用
- `interactive_content/` 子目录是孤儿（前端 game 组件已删）
- `passlib[bcrypt]` 在 requirements.txt 但代码用 `hashlib.pbkdf2_hmac`
- `anthropic` SDK 不在 requirements.txt
- `betterbaby-ui` 在 package.json 但无 import

## 本地启动（macOS）

```bash
cd /Users/cuishiming/.zcode/workspace/default/Mathsprout-0

# 1. Python 3.12 + venv（强推 3.12，3.11 可能坑）
brew install python@3.12
python3.12 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
pip install pytest pytest-asyncio aiosqlite openpyxl anthropic

# 2. .env
cat > backend/.env <<EOF
VISION_PROVIDER=offline
DATABASE_URL=sqlite+aiosqlite:////$(pwd)/backend/mathsprout.db
SECRET_KEY=$(python -c 'import secrets;print(secrets.token_hex(32))')
EOF

# 3. 后端
cd backend
./venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000

# 4. 测试（offline 模式不需要 API key）
./venv/bin/python -m pytest tests/ -v \
  --ignore=tests/test_vision_golden.py \
  --ignore=tests/test_parent_dashboard_api.py \
  --tb=short

# 5. 前端（另一终端）
cd /Users/cuishiming/.zcode/workspace/default/Mathsprout-0/frontend
npm install --legacy-peer-deps
npm run dev          # = next dev --webpack

# 6. 浏览器
#   http://localhost:3000              → 首页
#   http://localhost:3000/login        → teacher@kindergarten.cn / demo123
#   http://localhost:3000/dashboard/assessment → 上传 ./backend/tests/images/golden/* 体验完整流程
```

## 待办（接手时第一周）

- [ ] 跑通本地 pytest（先跑 14 个不依赖 AI 的单测）
- [ ] 跑通 offline 模式 demo（确认 `/api/v1/worksheets/demo` 端到端通）
- [ ] 评估页教师/家长 Tab 切换确认现状
- [ ] 决定是否清理 `_pass/_dual` 系列死代码
- [ ] 评估 P0.5 UI 卡通化工作量（参考 `萌芽数学.md`）
- [ ] 与 zzhouhong 沟通比赛时间表与分工
