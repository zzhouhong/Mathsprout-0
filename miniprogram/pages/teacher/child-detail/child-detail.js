const api = require("../../../utils/api");

const AGE_LABELS = { small: "小班", middle: "中班", large: "大班" };

Page({
  data: {
    childId: null,
    child: {},
    reports: [],
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

    this.setData({ childId: id });
    this.loadData();
  },

  loadData() {
    const id = this.data.childId;
    this.setData({ loading: true, error: "" });

    Promise.all([
      api.getChildDetail(id).catch(() => null),
      api.getChildReports(id).catch(() => null),
    ])
      .then(([childData, reportsData]) => {
        const c = childData || {};
        const ageLabel = AGE_LABELS[c.age_group] || c.age_group || "";
        this.setData({
          child: {
            name: c.name || "幼儿 #" + id,
            class_name: c.class_name || "",
            age_group: ageLabel,
            birth_date: c.birth_date ? c.birth_date.substring(0, 10) : "",
            notes: c.notes || "",
            access_code: c.parent_access_code || "",
          },
          reports: (reportsData?.reports || []).map((r) => ({
            id: r.report_id,
            reportType: r.type === "teacher" ? "teacher" : "parent",
            type: r.type === "teacher" ? "👩‍🏫 教师报告" : "👨‍👩‍👧 家长报告",
            date: r.generated_at ? r.generated_at.substring(0, 10) : "",
            summary: (r.summary || "").substring(0, 60),
          })),
          loading: false,
        });
      })
      .catch(() => {
        this.setData({ loading: false, error: "加载失败，请返回重试" });
      });
  },

  copyAccessCode() {
    if (this.data.child.access_code) {
      wx.setClipboardData({
        data: this.data.child.access_code,
        success: () => wx.showToast({ title: "访问码已复制", icon: "success" }),
      });
    }
  },

  goReport(e) {
    const id = e.currentTarget.dataset.id;
    const type = e.currentTarget.dataset.type || "parent";
    if (id) {
      wx.navigateTo({
        url: "/pages/report/report?id=" + id + "&type=" + type,
      });
    }
  },

  onEdit() {
    wx.showToast({ title: "编辑功能开发中", icon: "none" });
    // TODO: 后续可跳转到 child-form 的编辑模式（PUT /children/{id}，api.updateChild 已就绪）
  },

  onDelete() {
    wx.showModal({
      title: "删除幼儿",
      content: "将永久删除该幼儿及其所有报告，不可恢复",
      confirmText: "删除",
      confirmColor: "#DC2626",
      success: (res) => {
        if (res.confirm) {
          api.deleteChild(this.data.childId)
            .then(() => {
              wx.showToast({ title: "已删除", icon: "success" });
              setTimeout(() => wx.navigateBack(), 800);
            })
            .catch((e) => wx.showToast({ title: e.message || "删除失败", icon: "none" }));
        }
      },
    });
  },
});
