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
    // 优先从 storage 恢复绑定信息（冷启动后 globalData 会丢失）
    const stored = wx.getStorageSync("bindInfo");
    if (stored && stored.childId) {
      app.globalData.childId = stored.childId;
      app.globalData.childName = stored.childName;
      app.globalData.token = stored.token;
    }

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

  onUnbind() {
    wx.showModal({
      title: "解除绑定",
      content: "将清除当前幼儿的绑定信息，需要重新输入访问码",
      confirmText: "解除",
      confirmColor: "#DC2626",
      success: (res) => {
        if (res.confirm) {
          wx.removeStorageSync("bindInfo");
          wx.removeStorageSync("token");
          app.globalData.childId = null;
          app.globalData.childName = "";
          app.globalData.token = "";
          wx.reLaunch({ url: "/pages/index/index" });
        }
      },
    });
  },

  onShareAppMessage() {
    return {
      title: this.data.childName ? this.data.childName + "的成长档案 🌱" : "萌芽数学 · 成长档案",
      path: "/pages/index/index",
    };
  },
});
