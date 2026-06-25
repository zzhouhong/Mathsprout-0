const api = require("../../utils/api");
const app = getApp();

Page({
  data: {
    report: {},
    loading: true,
    error: "",
  },

  onLoad(options) {
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
});
