# 部署指南：让老师通过外网访问萌芽数学 Mathsprout

## 架构

```
教师浏览器 (外网)
    │  HTTPS
    ▼
cpolar 隧道 (xxxx.cpolar.cn)
    │
    ▼
localhost:3000 (Next.js 前端)
    │  /api/* → rewrites 代理
    ▼
backend:8000 (FastAPI) ← db:5432 (PostgreSQL)
```

**核心**：只暴露前端端口 3000，API 请求由 Next.js 内部代理到后端，无需处理 CORS。

## 方式一：内网穿透（立即可用）

### 1. 前置条件

- Docker Desktop 已安装并运行
- Node.js 24+ 已安装

### 2. 启动服务

```powershell
# 在项目根目录
cd "C:\Users\Zred\Desktop\first CC"

# 确认 PostgreSQL 容器在运行
docker ps --filter name=kindergarten-db

# 启动后端 (venv + uvicorn)
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 新开一个终端，启动前端
cd frontend
npm run dev
```

### 3. 安装隧道工具

#### 首选：cpolar（国内服务器，速度快）

1. 访问 https://www.cpolar.com 注册免费账号
2. 下载 Windows 版：https://www.cpolar.com/download
3. 安装后，登录认证：
   ```powershell
   cpolar authtoken <你的认证令牌>
   ```
4. 启动隧道：
   ```powershell
   cpolar http 3000
   ```
5. 输出中会显示公网地址，如 `https://xxxx.cpolar.cn`

#### 备选：bore（无需注册，但服务器在境外）

1. 下载 bore：https://github.com/ekzhang/bore/releases
2. 启动隧道：
   ```powershell
   bore local 3000 --to bore.pub
   ```
3. 输出公网地址（延迟可能较高）

### 4. 分享给老师

将隧道生成的公网 URL 发给老师即可。

Demo 账号：`teacher@kindergarten.cn` / `demo123`

---

## 方式二：Docker Compose 生产部署

适合有云服务器时使用。

### 1. 准备

```powershell
# 设置环境变量
$env:SECRET_KEY = "2b230a453427c9f630caf78f20147d07d84cd2ff7e6e95580f406da63ddff287"
$env:VISION_API_KEY = "sk-ws-H.RPDLEIM.fYrx.MEQCIBe_DibPn083lhx3LlNTNRHw3SDvuUNGYeMMxEEAmqdiAiBH3UG4tG74ePlGEXyqkRJRgQ3IHKaotQ5-l5UVOhQvcA"

# 构建并启动
docker compose -f docker-compose.prod.yml build
docker compose -f docker-compose.prod.yml up -d
```

### 2. 验证

```powershell
# 检查服务状态
docker compose -f docker-compose.prod.yml ps

# 测试 API
curl http://localhost:3000/api/health

# 浏览器访问
start http://localhost:3000
```

### 3. 配置防火墙 + 域名（可选）

在云服务器安全组中开放 3000 端口，配置 Nginx 反向代理 + SSL 证书。

---

## 常见问题

### Q: 隧道断开怎么办？
重新运行 `cpolar http 3000`，新地址发给老师即可。cpolar 免费版每次重启地址会变。

### Q: 上传图片失败？
检查 `backend/.env` 中 VISION_API_KEY 是否有效。

### Q: 登录后页面空白？
F12 打开浏览器控制台查看错误。常见原因：API 请求被 CORS 拦截（已通过 rewrites 方案解决）。

### Q: 想用回本地直连模式？
```powershell
$env:NEXT_PUBLIC_API_URL = "http://localhost:8000"
npm run dev
```
