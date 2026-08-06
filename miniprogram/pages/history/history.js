const api = require("../../utils/api");
const app = getApp();

Page({
  data: {
    reports: [],
    loading: true,
    error: "",
  },

  onShow() {
    // 冷启动后从 storage 恢复绑定信息
    const stored = wx.getStorageSync("bindInfo");
    if (stored && stored.childId) {
      app.globalData.childId = stored.childId;
      app.globalData.childName = stored.childName;
    }

    if (!app.globalData.childId) {
      wx.redirectTo({ url: "/pages/index/index" });
      return;
    }

    this.setData({ loading: true, error: "" });

    api.getReportHistory(app.globalData.childId)
      .then((r) => this.setData({ reports: r.reports || [], loading: false }))
      .catch(() => this.setData({ loading: false, error: "加载失败，下拉刷新重试" }));
  },

  onPullDownRefresh() {
    this.onShow();
    setTimeout(() => wx.stopPullDownRefresh(), 1000);
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: "/pages/report/report?id=" + id });
  },

  onShareAppMessage() {
    const name = (app.globalData.childName || "");
    return {
      title: name ? name + "的成长记录 📝" : "萌芽助手 · 成长记录",
      path: "/pages/index/index",
    };
  },
});
