// API 基地址配置：
//   - 本地开发：保持默认 http://localhost:8000（需在微信开发者工具勾选"不校验合法域名"）
//   - 生产部署：将 API_BASE_PROD 改为你的 HTTPS 域名，并把 isProd 设为 true
//     生产域名必须在小程序管理后台「开发设置 > 服务器域名 > request合法域名」中配置
const API_BASE_DEV = "http://localhost:8000/api/v1";
const API_BASE_PROD = "https://your-domain.com/api/v1";

// 切换开关：发布正式版时改为 true。也可通过 accountInfo/wx.getAccountInfoSync 区分体验版。
const isProd = false;

App({
  globalData: {
    childId: null,
    childName: "",
    token: "",
    apiBase: isProd ? API_BASE_PROD : API_BASE_DEV,
    isProd,
  },
});
