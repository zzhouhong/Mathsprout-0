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

> ⚠️ **两个必踩的坑**（已实测验证）：
>
> **坑 1：postgres:16-alpine 强制要求 `POSTGRES_PASSWORD`**，不能留空启动。
> 留空会报错：
> ```
> Error: Database is uninitialized and superuser password is not specified.
> You must specify POSTGRES_PASSWORD to a non-empty value for the superuser.
> ```
> 解决：环境变量里必须填 `POSTGRES_PASSWORD`（强密码，保存下来后面给 backend 用）。
>
> **坑 2：不能用"对象存储"挂持久卷**（即使加了 COS / API Key 也会失败）。
> PostgreSQL 启动时要 `chmod /var/lib/postgresql/data`，COS 不支持 POSIX 文件系统操作，会报：
> ```
> chmod: /var/lib/postgresql/data: I/O error
> chown: /var/lib/postgresql/data: I/O error
> Back-off restarting failed container
> ```
> 解决：要么不挂持久卷（评估期可接受），要么用"CFS 文件存储"（POSIX 兼容，需 ¥0.2/GB/月）。

**操作步骤：**

1. 仍在 https://tcb.cloud.tencent.com/dev?envId=mgya-d8gg4dtm6a418a70b#/platform-run
2. **新建服务** 按钮 → 选 **从镜像创建**
3. 镜像：`postgres:16-alpine`
4. 服务名：`db`
5. 容器端口：`5432`
6. 实例规格：最小（0.25 核 / 0.5G，dev 阶段够用）
7. **必填 - 环境变量**（**必须包含 POSTGRES_PASSWORD**，否则 pod 反复重启失败）：
   - 点开"环境变量设置"折叠面板
   - 加 3 条：
     | Key | Value |
     |---|---|
     | `POSTGRES_DB` | `kindergarten_math` |
     | `POSTGRES_USER` | `postgres` |
     | `POSTGRES_PASSWORD` | **强密码**（如 `d409fc5d4c1463f9abeaf42a3f9ba9a54da7f5c804c35a8f` 或自己生成，保存好） |
8. **持久卷（可选）**：评估期可跳过。如需保留数据：
   - 评估期：**不勾存储挂载**，容器重建 = 数据丢失（可接受）
   - 生产：勾选"存储挂载" → 选**"文件存储 CFS"**（不是 COS）→ 挂 `/var/lib/postgresql/data`
9. 点 **部署** → 等待「运行中」（约 1-2 分钟）

> 🔑 记住 `POSTGRES_PASSWORD` 的值，下面给 backend 用 `postgresql+asyncpg://postgres:你的密码@db:5432/kindergarten_math`。
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
3. **PostgreSQL 持久卷**：评估期可不挂（数据会丢）；生产要挂请选 **CFS 文件存储**（不是 COS，详见 §二坑 2）。
4. **费用监控**：体验版基础配额较小，跑通后切正式版或随时看费用中心。
5. **环境变量里的密码**：云托管控制台只会显示一次，**截屏保存**或复制到密码管理器。

---

## 八、当前真实阻塞点（2026-08-04 实测状态）

- [x] mgya 环境 **启用云托管** ✅（已完成）
- [x] ~db 服务第 1 次创建（失败：COS 持久卷 I/O error）~
- [x] ~db 服务第 2 次创建（失败：缺 POSTGRES_PASSWORD）~
- [ ] **删除当前失败 db** + **重建 db**（填 POSTGRES_PASSWORD，**不挂持久卷**）
- [ ] **创建 backend 服务**（上传代码 + 设环境变量）
- [ ] **验证 backend 跑通**（curl）
- [ ] 小程序**关联云开发环境** + 联调
- [ ] **上传代码 + 提交审核**
- [ ] 等小程序**备案通过**
- [ ] 等审核**过审**
- [ ] 点「发布」

> 完成到「验证 backend 跑通」我可以从代码侧直接帮；其他步骤（启用服务/上传审核）需要你手动操作。