const api = require("../../../utils/api");

const AGE_GROUPS = ["small", "middle", "large"];
const AGE_LABELS = ["小班（3-4岁）", "中班（4-5岁）", "大班（5-6岁）"];
const DIM_OPTIONS = [
  { key: "counting", label: "数数练习" },
  { key: "addition_sub", label: "加减运算" },
  { key: "shapes_space", label: "图形与空间" },
  { key: "patterns", label: "规律模式" },
];

Page({
  data: {
    ageIndex: 1,
    ageLabels: AGE_LABELS,
    difficulty: 2,
    selectedDims: ["counting", "shapes_space"],
    dimOptions: DIM_OPTIONS,
    generating: false,
    html: "",
    error: "",
  },

  onAgeChange(e) {
    this.setData({ ageIndex: Number(e.detail.value) });
  },

  onDifficultyChange(e) {
    this.setData({ difficulty: Number(e.detail.value) });
  },

  onDimToggle(e) {
    const dim = e.currentTarget.dataset.dim;
    const dims = [...this.data.selectedDims];
    const idx = dims.indexOf(dim);
    if (idx >= 0) {
      dims.splice(idx, 1);
    } else {
      dims.push(dim);
    }
    if (dims.length === 0) {
      wx.showToast({ title: "至少选择一个维度", icon: "none" });
      return;
    }
    this.setData({ selectedDims: dims });
  },

  async generate() {
    this.setData({ generating: true, error: "", html: "" });
    try {
      const res = await api.generateWorksheet({
        age_group: AGE_GROUPS[this.data.ageIndex],
        difficulty: this.data.difficulty,
        dimensions: this.data.selectedDims.join(","),
        format: "html",
      });
      // 后端返回 HTMLResponse，wx.request 已解析为文本
      this.setData({ html: typeof res === "string" ? res : (res.html || JSON.stringify(res)) });
    } catch (e) {
      this.setData({ error: e.message || "生成失败，请重试" });
    } finally {
      this.setData({ generating: false });
    }
  },
});
