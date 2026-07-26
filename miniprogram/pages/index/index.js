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
      // 完整持久化绑定信息到 storage（避免重启后需要重新输码）
      const bindInfo = {
        childId: result.child_id,
        childName: result.child_name,
        ageGroup: result.age_group || "middle",
        className: result.class_name || "",
        token: result.token,
      };
      app.globalData.childId = bindInfo.childId;
      app.globalData.childName = bindInfo.childName;
      app.globalData.token = bindInfo.token;
      wx.setStorageSync("bindInfo", bindInfo);
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
