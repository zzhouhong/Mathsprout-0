# mgya 环境部署手册（个人主体 · 个人新账号 · 微信云托管）

> 目标：在**当前腾讯云账号**（萌芽记录助手 / 100051286939 / APPID 1462714319）下，
> 把 Mathsprout 后端 + PostgreSQL db 服务部署到 **mgya-d8gg4dtm6a418a70b** 环境，让小程序能通过 `wx.cloud.callContainer` 调通。
> 写于 2026-08-03，账号余额 0 元（注意预算）。

---

## 〇、你的现状（已核实）

| 项 | 值 |
|---|---|
| 账号昵称 | 萌芽记录助手 |
| 账号 ID | `100051286939` |
| APPID | `1462714319` |
| 主体 | 个人 |
| 行业 | 网站 - 小程序开发 |
| CloudBase 环境 | 1 个：`mgya-d8gg4dtm6a418a70b`（上海，体验版，**云托管未启用**）|
| 余额 | 0 元 |
| 小程序 AppID | `wxbff15ebad1d7a2f6` |
| 小程序备案 | 管局审核中（被动等待）|

代码侧已同步：
- `cloudbaserc.json`（root + backend/）→ `envId: mgya-d8gg4dtm6a418a70b`
- `miniprogram/app.js` → `CLOUD_ENV = "mgya-d8gg4dtm6a418a70b"`
- `backend/Dockerfile` → `TEACHER_PASSWORD` 占位符（不再明文写密码）

---

## 一、启用 mgya 环境的云托管（需付费，按量）

> ⚠️ 这一步会**启用云托管能力**并产生费用（按量计费，体验版有基础配额）。
> 请确认腾讯云账号**已充值**或同意按量扣费（当前余额 0 元）。

**操作步骤：**

1. 浏览器打开 https://tcb.cloud.tencent.com/dev?envId=mgya-d8gg4dtm6a418a70b
2. 左侧菜单 → **云函数 / 托管** → **服务管理**
3. 页面正文会看到「启用云托管」按钮（灰色）+ 「我已知晓《腾讯云云开发服务条款》及云托管付费模式」复选框
4. **勾选** 复选框
5. 点 **启用云托管**（按钮变为可点）
6. 等待 1-2 分钟，刷新页面看到「服务管理」页面有「新建服务」入口 → 表示已启用

---

## 二、创建 PostgreSQL `db` 服务（生产用）

**操作步骤：**

1. 仍在 https://tcb.cloud.tencent.com/dev?envId=mgya-d8gg4dtm6a418a70b#/platform-run
2. **新建服务** 按钮 → 选 **从镜像创建**
3. 镜像：`postgres:16-alpine`
4. 服务名：`db`
5. 容器端口：`5432`
6. 实例规格：最小（0.25 核 / 0.5G，dev 阶段够用）
7. **关键 - 环境变量**：
   ```
   POSTGRES_DB=kindergarten_math
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=【点击"随机生成"或自己填一个强密码，复制下来，下面要用】
   ```
8. **关键 - 持久卷**：在「存储」区域**添加文件存储**：
   - 挂载路径：`/var/lib/postgresql/data`
   - 大小：5 GB
9. 点 **创建** → 等待「运行中」（约 1-2 分钟）

> 🔑 记住 `POSTGRES_PASSWORD` 的值，下面给 backend 用。
> 验证：`db-5432.tcb-api.tencentcloud.com:5432` 在云托管内网互通，**不要用公网 IP**。

---

## 三、创建 `backend` 服务（FastAPI）

**操作步骤：**

1. **服务管理** → **新建服务** → **从代码仓库** 或 **本地上传**
2. 推荐：**上传本地代码**
   - 选「上传代码包」→ 上传整个 `Mathsprout-0/` 目录的 zip（不含 `.venv`、`node_modules`、`__pycache__`、`*.png` 大文件）
   - 构建目录：`./`（即根目录）
   - 构建上下文：会自动找 `backend/Dockerfile` → **改用 `backend/` 作为构建目录**（CloudBase 的 cloudbaserc.json 已指定 `dockerfilePath: Dockerfile`，从 `buildDir: .` 出发）
3. 服务名：`backend`
4. 容器端口：`8000`
5. 实例规格：
   - CPU 1 / 内存 2 GB（与 cloudbaserc.json 一致）
   - min 1 / max 3
6. **关键 - 环境变量**（不要复制 Dockerfile 里的硬编码值，**只在这里填密码**）：
   ```
   ENVIRONMENT=production
   DEBUG=false
   VISION_PROVIDER=offline
   OFFLINE_RESULTS_DIR=./tests/images/golden
   DATABASE_URL=postgresql+asyncpg://postgres:你的POSTGRES_PASSWORD@db:5432/kindergarten_math
   DATABASE_URL_SYNC=postgresql://postgres:你的POSTGRES_PASSWORD@db:5432/kindergarten_math
   SECRET_KEY=【openssl rand -hex 32 生成的 64 位十六进制】
   TEACHER_EMAIL=ujvush@dingtalk.com
   TEACHER_PASSWORD=【你想用的真实密码；生产环境真实可用，demo 账号被禁用】
   TEACHER_NAME=崔老师
   CORS_ORIGINS=["https://your-domain.com"]
   ```
7. 访问策略：**公网访问** ✅（小程序 callContainer 不需要公网，但首次调试/排错时方便）
8. 点 **创建** → 等镜像构建（首次约 3-5 分钟）→ 状态「运行中」

---

## 四、验证后端跑通

**操作步骤：**

1. 在 `backend` 服务详情页，复制 **访问域名**（形如 `https://xxxxx.ap-shanghai.app.tcloudbase.com`）
2. 浏览器或 curl：
   ```bash
   curl https://你的访问域名/healthz
   # 期望：200 / "ok" / 任何 2xx
   ```
3. 测 `/api/v1/worksheets/demo`（上传 1 张图）：
   ```bash
   curl -X POST https://你的访问域名/api/v1/worksheets/demo \
     -F "file=@backend/tests/images/golden/shapes-triangle-2/image.png" \
     -F "age_group=middle"
   ```
4. 测登录：
   ```bash
   curl -X POST https://你的访问域名/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"ujvush@dingtalk.com","password":"你刚才设的TEACHER_PASSWORD"}'
   # 期望：返回 {"access_token":"...","token_type":"bearer",...}
   ```

如果都通过 → 后端已上线。

---

## 五、小程序联调

**操作步骤：**

1. 微信开发者工具 → 导入 `miniprogram/` → AppID 用 `wxbff15ebad1d7a2f6`
2. 顶部「云开发」→ 关联云开发环境 → 选 `mgya-d8gg4dtm6a418a70b`
3. 详情 → 本地设置 → 勾选「不校验合法域名」
4. 编译 → 首页应是家长绑定页
5. 输入访问码 `XIAOMING01` → 应该跳到「小明」成长档案页（说明 `wx.cloud.callContainer` 通）
6. 切到教师登录（页面底部入口）→ `ujvush@dingtalk.com` / `TEACHER_PASSWORD` → 应能进教师工作台

---

## 六、上传小程序代码 + 提交审核

**操作步骤：**

1. 微信开发者工具 → 上传代码（右上角）→ 填版本号 `1.0.0` + 备注 `首版发布`
2. 微信公众平台（mp.weixin.qq.com）→ 版本管理 → **提交审核**
3. 等待审核（约 1-3 天）
4. **小程序备案通过** + **审核通过** → 点「发布」上线

---

## 七、关键提醒

1. **真实教师账号**：上面 `TEACHER_PASSWORD` 是审核测试账号，需要填真实强密码。**Dockerfile 里已经清空，不会泄漏**。
2. **demo 账号被禁用**：内置的 `teacher@kindergarten.cn / demo123` 在生产环境（ENVIRONMENT=production）会被后端拒绝，避免弱口令后门。
3. **PostgreSQL 持久卷**：必须挂！否则实例重建 = 数据全丢。
4. **费用监控**：体验版基础配额较小，跑通后切正式版或随时看费用中心。
5. **环境变量里的密码**：云托管控制台只会显示一次，**截屏保存**或复制到密码管理器。

---

## 八、当前真实阻塞点（2026-08-03 状态）

- [ ] mgya 环境 **启用云托管**（要做，但需要勾协议 + 余额或按量付费授权）
- [ ] **创建 db 服务**（PostgreSQL + 持久卷）
- [ ] **创建 backend 服务**（上传代码 + 设环境变量）
- [ ] **验证 backend 跑通**（curl）
- [ ] 小程序**关联云开发环境** + 联调
- [ ] **上传代码 + 提交审核**
- [ ] 等小程序**备案通过**
- [ ] 等审核**过审**
- [ ] 点「发布」

> 完成到「验证 backend 跑通」我可以从代码侧直接帮；其他步骤（启用服务/上传审核）需要你手动操作。