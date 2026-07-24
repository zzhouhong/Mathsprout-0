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

      const assessment = res.assessment?.assessment || res.assessment || [];
      const dims = (Array.isArray(assessment) ? assessment : []).map((d) => ({
        name: d.display_name || d.dimension || "",
        score: d.score ?? 0,
        level: (d.level_emoji || "") + (d.level_name || ""),
      }));

      this.setData({ result: { dims } });
      wx.showToast({ title: "分析完成，已保存", icon: "success" });
    } catch (e) {
      this.setData({ error: e.message || "分析失败，请重试" });
    } finally {
      this.setData({ analyzing: false });
    }
  },
});
