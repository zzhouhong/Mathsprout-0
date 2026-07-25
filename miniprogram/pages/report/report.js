const api = require("../../utils/api");
const app = getApp();

Page({
  data: {
    report: {},
    loading: true,
    error: "",
  },

  onLoad(options) {
    // 冷启动后从 storage 恢复绑定信息
    const stored = wx.getStorageSync("bindInfo");
    if (stored && stored.childId) {
      app.globalData.childId = stored.childId;
      app.globalData.childName = stored.childName;
    }

    const childId = app.globalData.childId;
    if (!childId) {
      wx.redirectTo({ url: "/pages/index/index" });
      return;
    }

    this.setData({ loading: true, error: "" });

    // 支持从历史记录跳转：有 reportId 则加载指定报告，否则加载最新
    const reportId = options.id;
    const request = reportId
      ? api.getReportDetail(reportId)
      : api.getLatestReport(childId);

    request
      .then((r) => this.setData({ report: r, loading: false }))
      .catch(() => this.setData({ loading: false, error: "加载失败，请返回重试" }));
  },

  onPullDownRefresh() {
    this.onLoad(this.options || {});
    setTimeout(() => wx.stopPullDownRefresh(), 1000);
  },

  onShareAppMessage() {
    const name = (app.globalData.childName || "") ;
    return {
      title: name ? name + "的成长报告 📊" : "萌芽数学 · 成长报告",
      path: "/pages/index/index",
    };
  },
});
