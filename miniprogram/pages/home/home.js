const api = require("../../utils/api");
const app = getApp();

Page({
  data: {
    childName: "",
    loading: true,
    error: "",
    report: { has_report: false },
    trends: [],
  },

  onShow() {
    const childId = app.globalData.childId;
    if (!childId) {
      wx.redirectTo({ url: "/pages/index/index" });
      return;
    }

    this.setData({ childName: app.globalData.childName, loading: true, error: "" });

    Promise.all([
      api.getLatestReport(childId).catch(() => ({ has_report: false })),
      api.getGrowthTrend(childId).catch(() => ({ dimensions: {} })),
    ])
      .then(([report, trend]) => {
        const trendList = Object.entries(trend.dimensions || {}).map(([dim, d]) => ({
          dimension: dim,
          trend: d.trend,
        }));
        this.setData({
          report: report || { has_report: false },
          trends: trendList,
          loading: false,
        });
      })
      .catch(() => {
        this.setData({ loading: false, error: "加载失败，下拉刷新重试" });
      });
  },

  onPullDownRefresh() {
    this.onShow();
    setTimeout(() => wx.stopPullDownRefresh(), 1000);
  },

  goReport() {
    wx.navigateTo({ url: "/pages/report/report" });
  },
});
