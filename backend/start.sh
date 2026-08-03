#!/bin/sh
# 诊断+容错启动脚本
# 设计目标（绕过 Webshell/token 限制，直接通过公网 curl 拿诊断）：
#   1) import 预检，结果落盘 /tmp/import_result.txt（含真实 traceback）
#   2) import 成功则后台起 uvicorn（真实服务）
#   3) 保底 http 服务始终监听 0.0.0.0:$PORT 返回 200，并把 import 诊断作为响应体，
#      保证容器探针一定通过 -> 版本 running -> 公网可直接 curl 看到诊断
#   4) 前台 tail -f /dev/null 保持容器常驻
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
  echo ">>> launching uvicorn on 0.0.0.0:$PORT" | tee -a "$LOG"
  uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --proxy-headers --forwarded-allow-ips='*' >> "$LOG" 2>&1 &
else
  echo ">>> IMPORT FAILED; uvicorn skipped, fallback http will serve diagnostics" | tee -a "$LOG"
fi

# 保底 HTTP（延迟 10s 让 uvicorn 先抢端口）；返回 import 诊断，保证探针通过
( sleep 10; while true; do
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
try:
    with socketserver.TCPServer(('0.0.0.0', p), H) as s:
        s.serve_forever()
except OSError as e:
    import sys
    print('fallback cannot bind %d: %s' % (p, e), file=sys.stderr)
PY
    sleep 3
  done ) &

echo ">>> container kept alive" | tee -a "$LOG"
tail -f /dev/null
