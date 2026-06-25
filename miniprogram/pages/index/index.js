const api = require("../../utils/api");
const app = getApp();

Page({
  data: { code: "", loading: false, error: "" },

  onCodeInput(e) {
    this.setData({ code: e.detail.value.toUpperCase(), error: "" });
  },

  async onBind() {
    const code = this.data.code.trim();
    if (!code || code.length < 6) {
      this.setData({ error: "请输入至少 6 位访问码" });
      return;
    }

    this.setData({ loading: true, error: "" });

    try {
      const result = await api.bind(code);
      app.globalData.childId = result.child_id;
      app.globalData.childName = result.child_name;
      app.globalData.token = result.token;
      wx.setStorageSync("token", result.token);
      wx.switchTab({ url: "/pages/home/home" });
    } catch (err) {
      this.setData({
        error: err.message || "访问码无效，请检查后重试",
      });
    } finally {
      this.setData({ loading: false });
    }
  },
});
