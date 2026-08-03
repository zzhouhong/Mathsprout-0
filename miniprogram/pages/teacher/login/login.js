const api = require("../../../utils/api");
const app = getApp();

Page({
  data: { email: "", password: "", loading: false, error: "" },

  onEmail(e) { this.setData({ email: e.detail.value, error: "" }); },
  onPwd(e) { this.setData({ password: e.detail.value, error: "" }); },

  async onLogin() {
    const { email, password } = this.data;
    if (!email.trim() || !password.trim()) {
      this.setData({ error: "请输入邮箱和密码" });
      return;
    }

    this.setData({ loading: true, error: "" });

    try {
      const res = await api.login(email, password);
      const token = res.access_token || res.token;
      app.globalData.token = token;
      wx.setStorageSync("teacher_token", token);
      wx.redirectTo({ url: "/pages/teacher/class-view/class-view" });
    } catch (e) {
      this.setData({ error: e.message || "登录失败，请检查邮箱和密码" });
    } finally {
      this.setData({ loading: false });
    }
  },
});
