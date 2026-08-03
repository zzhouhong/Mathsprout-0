// API 基地址配置：
//   - 本地开发：默认 http://localhost:8000（需在微信开发者工具勾选"不校验合法域名"）
//     或用局域网 IP 让手机真机调试：http://<你的电脑IP>:8000（手机和电脑连同一 Wi-Fi）
//   - 生产部署：将 API_BASE_PROD 改为你的 HTTPS 域名，并把 isProd 设为 true
//     生产域名必须在小程序管理后台「开发设置 > 服务器域名 > request合法域名」中配置
const API_BASE_DEV = "http://192.168.3.7:8000/api/v1"; // ← 改成你的电脑局域网 IP（本机测试也可用 http://localhost:8000/api/v1）
const API_BASE_PROD = "https://your-domain.com/api/v1"; // ← 生产时改为你的 HTTPS 域名

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
