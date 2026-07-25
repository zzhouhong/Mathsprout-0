const api = require("../../../utils/api");

Page({
  data: {
    src: "",
    analyzing: false,
    error: "",
    result: null,
    // 幼儿选择
    children: [],
    childIndex: -1,
    childNames: [],
    selectedChildId: null,
    selectedAgeGroup: "middle",
  },

  onLoad() {
    // 加载幼儿列表供选择
    api.getChildren()
      .then((r) => {
        const children = r.children || r.data || [];
        this.setData({
          children,
          childNames: children.map((c) => c.name + (c.class_name ? "（" + c.class_name + "）" : "")),
        });
      })
      .catch(() => {
        // 加载失败不阻断，教师仍可匿名分析
      });
  },

  onChildChange(e) {
    const idx = Number(e.detail.value);
    const child = this.data.children[idx];
    this.setData({
      childIndex: idx,
      selectedChildId: child ? child.id : null,
      selectedAgeGroup: child ? (child.age_group || "middle") : "middle",
    });
  },

  onAgeChange(e) {
    this.setData({ selectedAgeGroup: e.detail.value });
  },

  takePhoto() {
    this.setData({ result: null, error: "" });
    wx.chooseMedia({
      count: 1,
      mediaType: ["image"],
      sourceType: ["camera"],
      success: (r) => this.setData({ src: r.tempFiles[0].tempFilePath }),
      fail: () => wx.showToast({ title: "拍照取消", icon: "none" }),
    });
  },

  choosePhoto() {
    this.setData({ result: null, error: "" });
    wx.chooseMedia({
      count: 1,
      mediaType: ["image"],
      sourceType: ["album"],
      success: (r) => this.setData({ src: r.tempFiles[0].tempFilePath }),
      fail: () => wx.showToast({ title: "选择取消", icon: "none" }),
    });
  },

  async analyze() {
    if (!this.data.src) {
      wx.showToast({ title: "请先拍照或选择图片", icon: "none" });
      return;
    }

    this.setData({ analyzing: true, error: "", result: null });

    try {
      // 构造完整 formData：age_group + child_id + child_name，使分析结果可持久化到幼儿档案
      const child = this.data.childIndex >= 0 ? this.data.children[this.data.childIndex] : null;
      const formData = {
        age_group: this.data.selectedAgeGroup,
        child_name: child ? child.name : "小朋友",
      };
      if (child) {
        formData.child_id = String(child.id);
      }

      const res = await api.uploadAndAnalyze(this.data.src, formData);

      // 提取完整分析结果（之前只取维度分数，丢弃了教学建议等核心价值）
      const assessment = res.assessment?.assessment || res.assessment || [];
      const dims = (Array.isArray(assessment) ? assessment : []).map((d) => ({
        name: d.display_name || d.dimension || "",
        score: d.score ?? 0,
        level: (d.level_emoji || "") + (d.level_name || ""),
      }));

      // 教师报告：总评 + 教学建议
      const teacher = res.reports?.teacher || {};
      const suggestions = Object.entries(teacher.teaching_suggestions || {}).map(
        ([dim, s]) => ({
          dimension: dim,
          level: s.level || "",
          recommendations: s.recommendations || "",
          activities: s.classroom_activities || "",
        })
      );

      // 每题识别明细（evaluation_trace）
      const traces = Array.isArray(res.evaluation_trace) ? res.evaluation_trace.map((t) => ({
        problem: t.problem_text || t.id || "",
        dimension: t.dimension_name || t.dimension || "",
        child_answer: t.child_answer ?? "—",
        correct_answer: t.correct_answer ?? "—",
        is_correct: t.is_correct,
      })) : [];

      this.setData({
        result: {
          dims,
          summary: teacher.overall_summary || "",
          suggestions,
          traces,
          reportId: res.persisted?.report_id || null,
        },
      });
      wx.showToast({
        title: res.persisted ? "分析完成，已保存" : "分析完成",
        icon: "success",
      });
    } catch (e) {
      this.setData({ error: e.message || "分析失败，请重试" });
    } finally {
      this.setData({ analyzing: false });
    }
  },

  previewImg() {
    if (this.data.src) {
      wx.previewImage({ urls: [this.data.src] });
    }
  },

  viewFullReport() {
    if (this.data.result && this.data.result.reportId) {
      wx.navigateTo({ url: "/pages/report/report?id=" + this.data.result.reportId });
    } else {
      wx.showToast({ title: "本次分析未持久化，无完整报告", icon: "none" });
    }
  },
});
