#!/bin/sh
# 最终生产启动脚本
#   - import 预检，结果落盘 /tmp/import_result.txt 并上报 ntfy（便于无公网时远程诊断）
#   - import 成功 -> exec uvicorn 前台（容器 PID1=uvicorn，真实服务）
#   - import 失败 -> 启动保底诊断 HTTP 服务返回诊断（版本仍 normal，便于排查）
set -u

PORT="${PORT:-8000}"
LOG="/tmp/mathsprout_start.log"
echo "=== start $(date -u) PORT=$PORT ===" | tee -a "$LOG"

echo "=== import app.main (pre-check) ===" | tee -a "$LOG"
python -c "from app.main import app; print('IMPORT_OK routes=', len(app.routes))" > /tmp/import_result.txt 2>&1
cat /tmp/import_result.txt | tee -a "$LOG"

# 把诊断主动上报到 ntfy（本机可读，无需公网/Webshell）
python report_diag.py | tee -a "$LOG"

if python -c "from app.main import app" >/dev/null 2>&1; then
  echo ">>> launching uvicorn (foreground) on 0.0.0.0:$PORT" | tee -a "$LOG"
  exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --proxy-headers --forwarded-allow-ips='*'
else
  echo ">>> IMPORT FAILED; starting fallback diag http server on 0.0.0.0:$PORT" | tee -a "$LOG"
  PORT="$PORT" python - <<'PY'
import http.server, socketserver, os
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            txt = open('/tmp/import_result.txt').read()
        except Exception as e:
            txt = 'no import result: %s' % e
        body = ('IMPORT_DIAG:\n' + txt).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *a):
        pass
p = int(os.environ.get('PORT', '8000'))
with socketserver.TCPServer(('0.0.0.0', p), H) as s:
    s.serve_forever()
PY
fi
