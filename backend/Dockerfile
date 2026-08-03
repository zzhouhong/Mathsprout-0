FROM python:3.12-slim
WORKDIR /app
# Debian 12 (bookworm) 包名修正：libgl1-mesa-glx 已重命名为 libgl1；
# 另补 cv2(opencv-headless) 运行所需的 libsm6/libxext6/libxrender1
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender1 poppler-utils \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# 数据/上传/缓存目录必须位于「运行时可写层」（即容器最上层 union FS），不要用镜像层 ./data
# 云托管 Pod 内 /tmp 与 /var/lib 都保证可写；用 /var/lib/mathsprout 作为根
RUN mkdir -p /var/lib/mathsprout/data /var/lib/mathsprout/uploads /var/lib/mathsprout/reports /var/lib/mathsprout/cache
# 云端默认配置：自包含 SQLite 数据库 + 离线 AI 识别，零外部依赖。
# 如需真实识别/持久化数据库，可在云托管控制台用环境变量覆盖以下值：
#   DATABASE_URL / DATABASE_URL_SYNC → 例如 postgresql+asyncpg://...
#   VISION_PROVIDER → 例如 qwen（需配合 VISION_API_KEY）
ENV DATABASE_URL=sqlite+aiosqlite:////var/lib/mathsprout/data/mathsprout.db \
    DATABASE_URL_SYNC=sqlite:////var/lib/mathsprout/data/mathsprout.db \
    VISION_PROVIDER=offline \
    UPLOAD_DIR=/var/lib/mathsprout/uploads \
    REPORT_DIR=/var/lib/mathsprout/reports \
    ENVIRONMENT=production
EXPOSE 8000
# 临时诊断 CMD：先打印所有诊断到 stdout + 文件，再 sleep 600 保持容器活着（让我用 Webshell 看 stdout）
# 注意：sleep 在前台，容器进程不会退出
CMD ["sh", "-c", "echo === boot diag ===; echo DATABASE_URL=$DATABASE_URL; echo VISION_PROVIDER=$VISION_PROVIDER; echo ENVIRONMENT=$ENVIRONMENT; echo PYTHON_VERSION=$(python --version); echo PWD=$(pwd); echo USER=$(id); ls -la /var/lib/mathsprout 2>&1; ls -la /app | head -20; which uvicorn; uvicorn --version 2>&1; echo === uvicorn app.main import test ===; python -c 'from app.main import app; print(\"app import OK, routes:\", len(app.routes))' 2>&1; echo === will sleep 600s to keep container alive ===; sleep 600"]
