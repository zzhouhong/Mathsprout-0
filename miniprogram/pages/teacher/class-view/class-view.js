const api = require("../../../utils/api");

Page({
  data: {
    children: [],
    loading: true,
    error: "",
  },

  onShow() {
    const token = wx.getStorageSync("teacher_token");
    if (!token) {
      wx.redirectTo({ url: "/pages/teacher/login/login" });
      return;
    }

    this.setData({ loading: true, error: "" });

    api.getChildren()
      .then((r) => {
        const children = r.children || r.data || [];
        this.setData({ children, loading: false });
      })
      .catch(() => {
        this.setData({ loading: false, error: "加载失败，请下拉刷新" });
      });
  },

  onPullDownRefresh() {
    this.onShow();
    setTimeout(() => wx.stopPullDownRefresh(), 1000);
  },

  goChild(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: "/pages/teacher/child-detail/child-detail?id=" + id });
  },

  goCapture() {
    wx.navigateTo({ url: "/pages/teacher/capture/capture" });
  },
});
