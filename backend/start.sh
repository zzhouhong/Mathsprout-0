#!/bin/sh
# 云托管启动脚本
# 解决两类经典部署失败：
#   1) uvicorn 默认只监听 127.0.0.1，而云托管探针从容器外访问 0.0.0.0:PORT → 连不上 → 探针失败 → 容器被杀
#   2) 预先 import app 做预检，失败时落盘并保持容器存活，便于 Webshell 诊断，而不是静默退出
set -u

PORT="${PORT:-8000}"
LOG="/tmp/mathsprout_start.log"

echo "=== mathsprout start $(date -u) ===" | tee -a "$LOG"
echo "PORT=$PORT  PYTHON=$(python --version 2>&1)" | tee -a "$LOG"
echo "PWD=$(pwd)  USER=$(id -u)" | tee -a "$LOG"

echo "=== pre-import app.main (catch import-time errors early) ===" | tee -a "$LOG"
if python -c "from app.main import app; print('IMPORT_OK routes=', len(app.routes))" >> "$LOG" 2>&1; then
  echo "=== import OK, launching uvicorn on 0.0.0.0:${PORT} ===" | tee -a "$LOG"
  # --host 0.0.0.0 让探针可达；--proxy-headers 适配小程序 callContainer 经 CLB 代理
  exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --proxy-headers --forwarded-allow-ips='*'
else
  echo "=== IMPORT FAILED (see /tmp/mathsprout_start.log), keep container alive 600s for diagnosis ===" | tee -a "$LOG"
  sleep 600
  exit 1
fi
