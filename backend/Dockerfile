FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgl1-mesa-glx libglib2.0-0 poppler-utils && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p uploads reports cache data
# 云端默认配置：自包含 SQLite 数据库 + 离线 AI 识别，零外部依赖。
# 如需真实识别/持久化数据库，可在云托管控制台用环境变量覆盖以下值：
#   DATABASE_URL / DATABASE_URL_SYNC → 例如 postgresql+asyncpg://...
#   VISION_PROVIDER → 例如 qwen（需配合 VISION_API_KEY）
ENV DATABASE_URL=sqlite+aiosqlite:///./data/mathsprout.db \
    DATABASE_URL_SYNC=sqlite:///./data/mathsprout.db \
    VISION_PROVIDER=offline
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
