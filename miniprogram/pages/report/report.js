const api = require("../../utils/api");
const app = getApp();

Page({
  data: {
    report: {},
    reportId: null,
    reportType: "parent",
    isTeacher: false,
    loading: true,
    error: "",
  },

  onLoad(options) {
    const reportId = options.id || null;
    const reportType = options.type === "teacher" ? "teacher" : "parent";
    this.setData({
      reportId,
      reportType,
      isTeacher: reportType === "teacher",
    });
    this.loadReport();
  },

  loadReport() {
    const { reportId, reportType } = this.data;
    this.setData({ loading: true, error: "" });

    let request;
    if (reportType === "teacher") {
      const teacherToken =
        app.globalData.token || wx.getStorageSync("teacher_token") || "";
      if (!teacherToken) {
        wx.redirectTo({ url: "/pages/teacher/login/login" });
        return;
      }
      app.globalData.token = teacherToken;
      if (!reportId) {
        this.setData({ loading: false, error: "缺少教师报告ID" });
        return;
      }
      request = api.getTeacherReport(reportId);
    } else {
      // 家长端冷启动后从 storage 恢复绑定信息
      const stored = wx.getStorageSync("bindInfo");
      if (stored && stored.childId) {
        app.globalData.childId = stored.childId;
        app.globalData.childName = stored.childName;
        app.globalData.token = stored.token || wx.getStorageSync("token") || "";
      }

      const childId = app.globalData.childId;
      if (!childId) {
        wx.redirectTo({ url: "/pages/index/index" });
        return;
      }
      request = reportId
        ? api.getReportDetail(reportId)
        : api.getLatestReport(childId);
    }

    request
      .then((result) => {
        const report = reportType === "teacher"
          ? this.normalizeTeacherReport(result)
          : this.normalizeParentReport(result);
        this.setData({ report, loading: false });
      })
      .catch(() => {
        this.setData({ loading: false, error: "加载失败，请返回重试" });
      });
  },

  normalizeParentReport(report = {}) {
    return {
      ...report,
      strengths: report.strengths || [],
      growing_areas: report.growing_areas || [],
      family_activities: report.family_activities || [],
    };
  },

  normalizeTeacherReport(report = {}) {
    const teachingSuggestions = Object.entries(
      report.teaching_suggestions || {}
    ).map(([name, value]) => ({
      name,
      currentStage: value.current_stage || "",
      level: value.level || "",
      recommendations: value.recommendations || "",
      nextGoal: value.next_stage_goal || "",
      materials: value.materials_suggestion || "",
      activities: value.classroom_activities || [],
    }));

    return {
      ...report,
      dimensions: report.dimensions || [],
      typical_errors_diagnosis: report.typical_errors_diagnosis || [],
      teaching_reflection_questions:
        report.teaching_reflection_questions || [],
      teachingSuggestions,
      coreExperienceSummary:
        report.core_experience_analysis?.summary || "",
    };
  },

  onPullDownRefresh() {
    this.loadReport();
    setTimeout(() => wx.stopPullDownRefresh(), 1000);
  },

  onShareAppMessage() {
    const name = app.globalData.childName || "";
    return {
      title: name ? name + "的成长报告 📊" : "萌芽数学 · 成长报告",
      path: "/pages/index/index",
    };
  },
});
