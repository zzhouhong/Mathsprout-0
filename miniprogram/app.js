// ───────────────────────────────────────────────
// 萌芽数学 Mathsprout — 小程序入口配置
//
// 两种后端调用方式（通过 USE_CLOUD 切换）：
//   1) USE_CLOUD = false → wx.request 直连本地 / 自有服务器
//      开发调试用，需在开发者工具勾选「不校验合法域名」
//   2) USE_CLOUD = true  → wx.cloud.callContainer 走微信云托管
//      免域名 / 免 ICP 备案 / 免 HTTPS，正式发布推荐
// ───────────────────────────────────────────────

// 是否走微信云托管。部署到云托管并拿到环境 ID 后改为 true
const USE_CLOUD = false;

// 云开发环境 ID（微信开发者工具 → 云开发 → 环境设置，形如 cloud1-xxxxxxxx）
// USE_CLOUD = true 时必须填入真实环境 ID，否则 callContainer 会失败
const CLOUD_ENV = "请替换为你的云开发环境ID";

// 云托管服务名称（微信云托管 → 服务管理 → 服务列表中的服务名）
const CLOUD_SERVICE = "backend";

// 本地开发基地址（本机测试用；手机真机调试改成电脑局域网 IP，如 http://192.168.3.7:8000/api/v1）
const API_BASE_DEV = "http://192.168.3.7:8000/api/v1";

App({
  onLaunch() {
    // 走云托管时只需初始化一次，后续 callContainer 会自动复用该环境
    if (USE_CLOUD) {
      wx.cloud.init({
        env: CLOUD_ENV,
        traceUser: true,
      });
    }
  },
  globalData: {
    childId: null,
    childName: "",
    token: "",
    // 以下字段供 utils/api.js 判断调用通道
    useCloud: USE_CLOUD,
    cloudEnv: CLOUD_ENV,
    cloudService: CLOUD_SERVICE,
    apiBase: API_BASE_DEV,
  },
});
