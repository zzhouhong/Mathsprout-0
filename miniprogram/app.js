App({
  globalData: {
    childId: null,
    childName: "",
    token: "",
    // 本地开发：连接本机后端（需在微信开发者工具中勾选"不校验合法域名"）
    // 生产部署：替换为你的 HTTPS 域名
    apiBase: "http://localhost:8000/api/v1"
  }
});
