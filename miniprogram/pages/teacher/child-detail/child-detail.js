const api = require("../../../utils/api");

Page({
  data: {
    child: { name: "", class_name: "", age_group: "" },
    report: null,
    loading: true,
    error: "",
  },

  onLoad(options) {
    const id = options.id;
    if (!id) {
      wx.showToast({ title: "缺少幼儿ID", icon: "error" });
      return;
    }

    const token = wx.getStorageSync("teacher_token");
    if (!token) {
      wx.redirectTo({ url: "/pages/teacher/login/login" });
      return;
    }

    this.setData({ loading: true, error: "" });

    // 并行获取幼儿信息和报告列表（取最新一条）
    Promise.all([
      api.getChildDetail(id).catch(() => null),
      api.getChildReports(id).catch(() => null),
    ])
      .then(([childData, reportsData]) => {
        const reports = reportsData?.reports || [];
        const latest = reports.length > 0 ? reports[0] : null;
        this.setData({
          child: {
            name: childData?.name || "幼儿 #" + id,
            class_name: childData?.class_name || "",
            age_group: childData?.age_group || "",
          },
          report: latest,
          loading: false,
        });
      })
      .catch(() => {
        this.setData({ loading: false, error: "加载失败，请返回重试" });
      });
  },
});
