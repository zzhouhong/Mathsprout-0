const api = require("../../../utils/api");

Page({
  data: {
    src: "",
    analyzing: false,
    error: "",
    result: null,
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
      const res = await api.uploadAndAnalyze(this.data.src, {});

      const assessment = res.assessment?.assessment || res.assessment || [];
      const dims = (Array.isArray(assessment) ? assessment : []).map((d) => ({
        name: d.display_name || d.dimension || "",
        score: d.score ?? 0,
        level: (d.level_emoji || "") + (d.level_name || ""),
      }));

      this.setData({ result: { dims } });
    } catch (e) {
      this.setData({ error: e.message || "分析失败，请重试" });
    } finally {
      this.setData({ analyzing: false });
    }
  },
});
