# 萌芽记录助手 · 微信云托管（CloudBase Run）迁移方案

> 决策：放弃「买云服务器 + 域名 + ICP 备案 + HTTPS」路线，改用**微信云托管**直接跑现有 FastAPI 后端容器。
> 依据：微信官方社区确认「小程序调用云托管服务无需配置服务器域名、无需备案」，通过 `wx.cloud.callContainer` 调用即可。
> 目标：后端代码几乎不改，小程序改调用方式，永久省掉域名/备案/HTTPS/服务器运维。

---

## 〇、为什么选云托管而不是云函数

本项目后端不是薄上传层，包含：
- JWT 鉴权（`parent/bind` 访问码绑幼儿、`teacher/login`）
- **PCK 评分引擎**（`app/services/assessment_engine.py`，纯 Python 算分）
- 关系型数据库（SQLAlchemy：幼儿/用户/评估/工作单/报告）
- 报告/Excel/PDF 生成

| 路线 | 后端改动 | 数据库 | 工作量 |
|------|----------|--------|--------|
| **云托管（容器）✅** | 原样跑 `backend/Dockerfile` | 容器内带 Postgres / 云 MySQL | 最小 |
| 云开发（云函数） | 拆成云函数重写 | 重构成 NoSQL | 大（几天级）|

云托管能直接吃下你现有的 Docker 镜像，**评分引擎、鉴权、关系库全部原样保留**。

---

## 一、最终架构

```
微信小程序
  │  wx.cloud.callContainer（微信内网，免备案/免域名/免HTTPS）
  ▼
微信云托管（CloudBase Run）
  ├── 服务 backend  (FastAPI 容器, 端口 8000, 由 backend/Dockerfile 构建)
  │     └── 环境变量注入：ENVIRONMENT / DATABASE_URL / SECRET_KEY / VISION_PROVIDER=offline
  └── 服务 db       (PostgreSQL 容器, 端口 5432, 同环境内网互通)
  └── 云存储        (可选：图片走 wx.cloud.uploadFile，比走容器上传更省)
```

**关键**：小程序只认「云托管环境 ID」，不认域名，所以微信后台「服务器域名」**一处都不用填**。

---

## 二、前置条件

- [ ] 小程序备案通过（后台「管局审核中」必须过，云托管不解决小程序自身备案）
- [ ] 微信开发者工具已导入 `miniprogram/`，AppID `wxbff15ebad1d7a2f6`
- [ ] 小程序账号下已开通**云开发**（开发者工具顶部「云开发」按钮开通，建一个环境）
- [ ] 本地 `backend/` 能正常 build（Docker 可构建 `backend/Dockerfile`）

---

## 三、步骤 1：创建云托管环境与 backend 服务

1. 微信开发者工具 → 顶部「云开发」→ 进入 CloudBase 控制台
2. 左侧「**云托管**」→ 开通云托管（首次需授权）
3. 新建**服务** `backend`：
   - 来源：选「代码仓库」或「本地代码/镜像」。最简单：把 `backend/` 目录上传，或连接 Git 仓库
   - 构建：云托管会读取 `backend/Dockerfile` 自动 build
   - **服务端口填 `8000`**（与 uvicorn 一致）
   - 实例规格：选最小（0.25 核 / 0.5G 起步，低流量够用）
4. 配置**环境变量**（在服务设置里，不要写进代码）：
   ```
   ENVIRONMENT=production
   DEBUG=false
   VISION_PROVIDER=offline
   OFFLINE_RESULTS_DIR=./tests/images/golden
   DATABASE_URL=postgresql+asyncpg://postgres:你的强密码@db:5432/kindergarten_math
   SECRET_KEY=<openssl rand -hex 32 生成>
   ```
   > `offline` 模式不依赖任何外部 AI，golden 结果已随 `COPY .` 打进镜像。

---

## 四、步骤 2：部署数据库（db 服务）

同一云托管环境再建一个服务 `db`：
- 镜像直接用 `postgres:16-alpine`
- 端口 `5432`
- 环境变量：`POSTGRES_DB=kindergarten_math`、`POSTGRES_USER=postgres`、`POSTGRES_PASSWORD=你的强密码`
- 开通**文件持久化**（挂载 `/var/lib/postgresql/data` 到云托管存储，避免容器重建丢数据）

**backend 连 db**：同环境服务间内网互通，backend 用 `db:5432` 即可访问（无需公网）。

> 备选：不想管 Postgres，可在环境变量里把 `DATABASE_URL` 改成 SQLite（如 `sqlite+aiosqlite:////data/mathsprout.db`，挂载 `/data` 持久化）。数据量小完全够用，运维更省。

---

## 五、步骤 3：小程序改造（核心代码改动）

### 5.1 `miniprogram/app.js` 初始化云

```javascript
App({
  globalData: {
    // 你的云托管环境 ID（CloudBase 控制台获取，形如 xxxx-env-id）
    cloudEnv: '你的云托管环境ID'
  },
  onLaunch() {
    if (!wx.cloud) {
      console.error('请使用 2.2.3 以上的基础库以使用云能力')
      return
    }
    wx.cloud.init({
      env: this.globalData.cloudEnv,
      traceUser: true
    })
  }
})
```

### 5.2 `miniprogram/utils/api.js` 改用 callContainer

把原来 `wx.request({ url: API_BASE + path })` 的请求，统一换成 `wx.cloud.callContainer`：

```javascript
// 原来的写法（删掉）
// wx.request({ url: API_BASE_DEV + path, method, data, ... })

// 新写法
function request(path, method = 'GET', data = {}, header = {}) {
  return new Promise((resolve, reject) => {
    wx.cloud.callContainer({
      config: { env: getApp().globalData.cloudEnv },
      path: '/api/v1' + path,   // 与原后端路由一致
      method: method,
      data: data,
      header: Object.assign({ 'content-type': 'application/json' }, header),
      success: res => resolve(res),
      fail: err => reject(err)
    })
  })
}

// 导出原接口（路径保持不变，只是底层换了通道）
module.exports = {
  parentBind: (code) => request('/parent/bind', 'POST', { access_code: code }),
  teacherLogin: (email, pwd) => request('/teacher/login', 'POST', { email, password: pwd }),
  // ... 其余接口照旧，只是调用 request() 而非 wx.request
}
```

> 路由路径（`/api/v1/...`）和请求/响应字段**完全不变**，因为后端原样跑，所以 `api.js` 里只换"通道"，业务代码几乎不动。

### 5.3 图片上传（可选优化）

原本 `wx.uploadFile` 到后端。更省事的做法：图片直接传云存储，再把 `fileID` 交给后端：

```javascript
async function uploadImageToCloud(filePath) {
  const suffix = filePath.match(/\.[^.]+$/) ?.[0] || '.jpg'
  const cloudPath = `uploads/${Date.now()}-${Math.random().toString(36).slice(2)}${suffix}`
  const res = await wx.cloud.uploadFile({ cloudPath, filePath })
  return res.fileID   // 存进后端即可
}
```

> 如果暂时不想动上传逻辑，也可以让后端容器继续接收 `wx.cloud.callContainer` 传的文件——容器能正常收 multipart。两条都行，按需选。

> ✅ 已落地（2026-08-04）：教师端拍照走 `wx.cloud.uploadFile` → `wx.cloud.getTempFileURL`
> 拿临时链接 → `POST /api/v1/worksheets/cloud-analyze`（后端 `httpx` 下载后复用完整分析流水线）。
> 因为 `callContainer` 请求体上限 100K，图片不能走 JSON 直传；临时链接方案
> **不需要开启「开放接口服务」**（COS-SDK + `/_/cos/getauth` 方案留作后续备用，
> 后端 `cloud_storage.py` 已实现，需控制台开启开关后版本重建才生效）。

---

## 六、步骤 4：联调与上线

1. 开发者工具里「云开发」→ 确认 backend 服务「运行中」，点开「测试」能调到 `/api/v1/health`
2. 小程序编译，首页输生产环境真实访问码绑定测试（走的是云托管，不是本机）：
   `1923BF95`（测试幼儿）或 `7C7427EB`（测试宝宝）；`XIAOMING01` 等演示码只在
   development 环境播种，生产环境返回「访问码无效」。
3. 真机预览 / 体验版测试
4. 微信公众平台 → 版本管理 → 上传代码 → 提交审核 → 发布
   - 此时**仍要小程序备案通过**（管局审核中→通过）
   - 服务器域名**不用配**（云托管免此步）

---

## 七、成本

- 云托管新用户有免费额度；超出按**实例运行时长 + 流量**计费
- 低流量（一个幼儿园、几十个家庭）日常几乎在免费额度内，或个位数元/月
- 比「轻量服务器 60–120 元/年 + 域名 + 备案时间成本」更省，且**零运维**

---

## 八、上线前检查清单

- [ ] CloudBase 环境已建，云托管已开通
- [ ] backend 服务部署成功，端口 8000，环境变量已注入（SECRET_KEY 已换随机值）
- [ ] db 服务（或 SQLite 持久化）就绪，数据不丢
- [ ] `/api/v1/health` 在云托管内可通
- [ ] 小程序 `app.js` 已 `wx.cloud.init` 且 env 正确
- [ ] `api.js` 已改用 `wx.cloud.callContainer`，路径/字段未变
- [ ] 图片上传走云存储或容器，二选一已通
- [ ] 小程序备案已通过（管局审核中 → 通过）
- [ ] 代码已上传、提审、发布

---

## 九、与原「买服务器」方案对比（原方案已放弃）

| 维度 | 原方案（服务器+域名+ICP） | 本方案（云托管） |
|------|--------------------------|------------------|
| 域名购买 | 需要 | 不需要 |
| ICP 备案 | 1–3 周 | 不需要 |
| HTTPS 配置 | 需要 | 腾讯自动 |
| 服务器运维 | 自己管 | 腾讯托管 |
| 后端代码改动 | 小 | 极小（容器原样） |
| 上线等待 | 备案通过才上线 | 仅等小程序备案 |
| 月成本 | 服务器+域名费 | 低流量近乎免费 |

> 唯一不能省的：小程序自身备案（管局审核中）。那是微信对小程序主体的要求，云托管解决的是「服务器侧」。

---

## 十、风险与注意

- **冷启动**：云托管实例缩容到 0 后首次请求会慢几百毫秒~几秒。可在服务设置里设「最小实例数 = 1」保活（略增成本）。
- **镜像体积**：`backend/Dockerfile` 装了 opencv-headless + numpy（离线模式其实用不到 opencv），镜像偏大、构建偏慢。可裁剪 `requirements.txt` 去掉 opencv 进一步加速（可选优化，不影响功能）。
- **密钥**：`SECRET_KEY`、数据库密码务必走云托管环境变量，**不要写进代码或提交到 Git**。
- **数据备份**：db 服务务必开启存储持久化 + 定期备份，否则容器重建数据丢失。

---

## 附：2026-08-04 实测记录（重要）

### 环境真相
- 浏览器 UI 只显示 1 个环境（有 bug），但 **CLI（tcb env list）显示 2 个**，都在账号 100051286939 下：
  - `prod-d6gj3mfkye02c4455`（按量付费，**真实生产环境**，backend 部署于此）
  - `mgya-d8gg4dtm6a418a70b`（体验版，勿用）
- **判断环境以 CLI 为准，不要信浏览器 UI**

### 正式教师账号登录的坑（已解决）
- cloudbaserc.json 的 `envParams` 字段**无效**，正确字段是 **`envVariables`**
- 但实测 **envVariables 也没注入**（CLI 3.7.1 的 bug 或字段路径不对）
- **当前可行方案**：把 TEACHER_PASSWORD 写进 Dockerfile `ENV`（临时验证通过，登录成功）
- 更安全的长期方案：用云托管控制台 UI 设环境变量（但浏览器 UI 对 prod 报"环境不存在"，待修复）

### 已验证通过（curl 直测公网）
```
POST /api/v1/auth/login      → 崔老师登录成功 ✅
POST /api/v1/children        → 创建幼儿成功（自动生成访问码）✅
POST /api/v1/parent/bind     → 家长绑定成功 ✅
GET  /api/v1/parent/latest-report → 正常返回 ✅
```
公网入口（HTTP 网关路由已配）：
`https://prod-d6gj3mfkye02c4455-1462714319.ap-shanghai.app.tcloudbase.com/api/v1`

### 生产环境行为（设计如此）
- demo 账号（teacher@/demo123）在生产被禁用 ✅
- demo 幼儿（XIAOMING01 等）在生产不 seed（main.py:122 仅 development）✅
- 真实幼儿由教师创建后才有访问码

### 遗留
- [ ] 浏览器 UI 对 prod 环境报"环境不存在"（登录态/权限问题，不影响 CLI）
- [ ] envVariables 注入机制待修复（当前靠 Dockerfile ENV 兜底）
- [ ] mgya 体验版环境可删（已无服务）

---

## 附二：数据持久化方案（2026-08-05 定案）

### 结论：微信云托管不支持 CFS 挂载，方案 A 不可行

排查证据：
1. 微信云托管官方操作指南只提供 **MySQL / 对象存储 / 静态资源存储**，没有「存储挂载 / 文件系统(CFS)」；
2. 服务管理控制台 5 个 TAB（部署发布、云端调试、服务日志、资源监控、服务设置）无任何存储挂载入口；
3. TCBR API 存在 `VolumesConf` 字段，但本账号无 CAM 权限创建 CFS（`cfs:DescribeCfsFileSystems` 未授权），
   且微信云托管环境也没有创建 CFS 的控制台入口——「挂 CFS 让 SQLite 持久化」这条路走不通。

### 两条可行路线（二选一）

| 路线 | 持久化程度 | 你需要做的 | 状态 |
|------|-----------|-----------|------|
| **A. 微信云托管 MySQL（推荐）** | 真正持久化，官方 Serverless 数据库 | 控制台 → MySQL → 开通（输密码）→ 把内网地址/账号给我 | 后端已加 `asyncmy` 驱动，镜像已就绪，就差接线 |
| **B. 对象存储备份 SQLite（过渡）** | 每 3 分钟 + 关停前备份，冷启动自动恢复；多实例同时写有极小覆盖风险 | 服务管理 → 云调用 → 开「开放接口服务」+ 微信令牌白名单加两个路径 | **代码已上线 backend-031**，翻开关即生效 |

### 路线 B 的开关（1 分钟搞定，已随 backend-031 生效）

1. 微信云托管控制台 → 服务管理 → backend → **云调用** → 开启「**开放接口服务**」；
2. 同一页「微信令牌配置」白名单添加：
   - `/_/cos/getauth`
   - `/_/cos/metaid/encode`
3. 无需重新部署：后端每 180s 自动把 `/var/lib/mathsprout/data/mathsprout.db`
   备份到对象存储 `backup/mathsprout.db`，容器冷启动时自动恢复。

验证方法：开完开关后等 5 分钟，用管理端/CLI 看对象存储里应出现 `backup/mathsprout.db`；
之后任何一次重部署/缩容，幼儿和报告数据都会保留。

### 路线 A 的接线（你开通后我 5 分钟完成）

1. 控制台 → MySQL → 开通（选 5.7 或 8.0，记下密码）；
2. 把「数据库信息」页的**内网地址/端口**和账号密码发我；
3. 我改环境变量：
   ```
   DATABASE_URL=mysql+asyncmy://账号:密码@内网地址:3306/mathsprout?charset=utf8mb4
   ```
4. 重灌环境变量（镜像已含 asyncmy，无需重新构建）→ 重启验证。

⚠️ MySQL 迁移注意事项（后端代码已排查）：
- ORM 枚举列默认存**成员名（大写）**，但部分接口用 `.value`（小写）写入——现有 SQLite 里两种值混杂；
  MySQL 原生 ENUM 只认其中一种，迁移前需给枚举列加 `values_callable=lambda e: [m.value for m in e]`
  并归一化存量数据（工作量约 30 分钟，迁移时我来处理）。
- 表结构由 `init_db()` 启动时自动创建（`create_all`），无需手写建表 SQL。

### 部署/恢复命令备忘（2026-08-05 实测）

```bash
# 1. 构建新镜像（灰度，避免交互卡住）
tcb cloudrun deploy -e prod-d6gj3mfkye02c4455 -s backend --port 8000 --source ./backend --force --traffic

# 2. 若灰度任务卡在 GrayRelease（镜像大拉取慢），取消后全量切换：
tcb api tcbr OperateServerManage --api-version 2022-02-17 \
  --body '{"EnvId":"prod-d6gj3mfkye02c4455","ServerName":"backend","OperateType":"cancel","TaskId":<任务ID>}'

# 3. 全量发布 + 重灌环境变量（ReleaseType 必填）
tcb api tcbr UpdateCloudRunServer --api-version 2022-02-17 --body '{
  "EnvId":"prod-d6gj3mfkye02c4455","ServerName":"backend",
  "DeployInfo":{"DeployType":"image","ImageUrl":"ccr.ccs.tencentyun.com/tcb-100051286939-kiph/ca-xgkrzbge_backend:<新镜像tag>","ReleaseType":"FULL"},
  "Items":[{"Key":"EnvParam","Value":"{\"ENVIRONMENT\":\"production\",\"TEACHER_EMAIL\":\"ujvush@dingtalk.com\",\"TEACHER_PASSWORD\":\"<密码>\",\"TEACHER_NAME\":\"崔老师\",\"CLOUD_STORAGE_BUCKET\":\"7072-prod-d6gj3mfkye02c4455-1462714319\",\"CLOUD_STORAGE_REGION\":\"ap-shanghai\"}"}]
}'
```

> 注：CLI 3.7.1 的 `tcb cloudrun deploy` 本次实测**保留了**服务级环境变量（合并了旧 EnvParams），
> 但为稳妥仍建议发布后核一遍 `DescribeCloudRunServerDetail` 里的 `EnvParams`。
