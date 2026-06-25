"""
萌芽数学 Mathsprout — 自动重连隧道
bore 断线自动重连，刷新桌面地址文件
"""
import subprocess, re, urllib.request, json, os, time, sys

BORE = os.path.expandvars(r"%USERPROFILE%\bore\bore.exe")
DESKTOP = os.path.expandvars(r"%USERPROFILE%\Desktop")
URL_FILE = os.path.join(DESKTOP, "萌芽数学-访问地址.txt")

def start_bore():
    """启动 bore 并返回公网 URL"""
    proc = subprocess.Popen(
        [BORE, "local", "3000", "--to", "bore.pub"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    for line in proc.stdout:
        m = re.search(r"listening at (bore\.pub:\d+)", line)
        if m:
            return proc, "http://" + m.group(1)
    proc.terminate()
    return None, None

def test_url(url):
    """测试 URL 是否可访问"""
    try:
        req = urllib.request.Request(f"{url}/api/health")
        resp = urllib.request.urlopen(req, timeout=8)
        data = json.loads(resp.read())
        return data.get("status") == "ok"
    except:
        return False

def save_url(url):
    with open(URL_FILE, "w", encoding="utf-8") as f:
        f.write(f"萌芽数学 Mathsprout\n\n")
        f.write(f"{url}\n")
        f.write(f"教师: teacher@kindergarten.cn / demo123\n")
        f.write(f"隧道自动重连中，如失效请等待几秒刷新\n")

print("=" * 50)
print("  萌芽数学 Mathsprout — 自动重连隧道")
print("=" * 50)

retry_delay = 5
max_delay = 60

while True:
    print(f"\n[{time.strftime('%H:%M:%S')}] 连接 bore...")
    proc, url = start_bore()

    if not url:
        print("连接失败，重试...")
        time.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, max_delay)
        continue

    retry_delay = 5  # reset
    print(f"地址: {url}")

    if test_url(url):
        print("✅ 连通！")
        save_url(url)
        # 保持运行直到断线
        try:
            proc.wait()
        except:
            pass
        print("⚠️ 连接断开，自动重连...")
    else:
        print("❌ 测试失败，重试...")
        proc.terminate()

    time.sleep(2)
