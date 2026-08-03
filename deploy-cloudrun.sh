#!/usr/bin/env bash
# ============================================================
# 微信云托管部署脚本 — Mathsprout 后端 (FastAPI)
# ------------------------------------------------------------
# 前置条件（需你本人完成，脚本无法代劳）：
#   1. 微信开发者工具 → 云开发 → 开通环境
#      ⚠️ 云托管目前仅支持「上海」地域
#   2. 拿到环境 ID（形如 cloud1-xxxxxxxx），替换下面 ENV_ID 或作为第 1 个参数
#   3. 安装并登录 CLI：  npm i -g @cloudbase/cli && tcb login  （首次弹浏览器扫码）
#   4. 在云托管控制台 backend 服务的「环境变量」里配置：
#        VISION_PROVIDER = offline
#        DATABASE_URL    = sqlite:///./mathsprout.db
#      （离线模式不调任何外部 AI 接口，无需密钥）
#   5. 数据库初始化：控制台「Web Shell」执行  python -m app.init_db
#      （或首次请求时由代码自动建表，取决于 main.py 的 lifespan 逻辑）
# ============================================================
set -e

ENV_ID="${1:-请替换为你的云开发环境ID}"

echo "▶ 部署 Mathsprout 后端到微信云托管 (env: $ENV_ID)"
echo "▶ 使用 backend/ 下的 Dockerfile 构建镜像，容器端口 8000"

# 安装 CLI（如未安装）
if ! command -v tcb >/dev/null 2>&1; then
  echo "▶ 安装 @cloudbase/cli ..."
  npm i -g @cloudbase/cli
fi

# 登录（首次需扫码，浏览器会弹出）
tcb login

# 部署：从 backend/ 目录构建镜像并推送到云托管
# 镜像构建后会自动滚动重启 backend 服务
tcb cloudrun deploy --port 8000 --source ./backend --force

echo ""
echo "✅ 部署完成。"
echo "   1) 去云托管控制台确认 backend 服务「运行中」"
echo "   2) 在 backend 服务「环境变量」配置 VISION_PROVIDER=offline（如未配）"
echo "   3) 小程序侧：把 miniprogram/app.js 的"
echo "        USE_CLOUD 改为 true"
echo "        CLOUD_ENV 改为 '$ENV_ID'"
echo "        CLOUD_SERVICE 保持 'backend'"
echo "      然后微信开发者工具「上传」代码 → 体验版验证"
