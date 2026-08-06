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
    exporting: false,
    previewText: "",
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
    this.setData({ generating: true, error: "", previewText: "" });
    try {
      const res = await api.generateWorksheet({
        age_group: AGE_GROUPS[this.data.ageIndex],
        difficulty: this.data.difficulty,
        dimensions: this.data.selectedDims.join(","),
        format: "markdown",
      });
      const markdown = res?.markdown || "";
      const previewText = markdown
        .replace(/^#{1,6}\s*/gm, "")
        .replace(/\*\*(.*?)\*\*/g, "$1")
        .replace(/^>\s?/gm, "")
        .replace(/^---+$/gm, "")
        .replace(/\n{3,}/g, "\n\n")
        .trim();
      if (!previewText) {
        throw new Error("操作单内容为空，请重试");
      }
      this.setData({ previewText });
    } catch (e) {
      this.setData({ error: e.message || "生成失败，请重试" });
    } finally {
      this.setData({ generating: false });
    }
  },

  copyPreview() {
    if (!this.data.previewText) return;
    wx.setClipboardData({
      data: this.data.previewText,
      success: () => wx.showToast({ title: "操作单已复制", icon: "success" }),
    });
  },

  // 导出操作单为 PDF（下载 → 预览 → 可保存/分享）
  async exportPdf() {
    if (!this.data.previewText) {
      wx.showToast({ title: "请先生成操作单", icon: "none" });
      return;
    }
    this.setData({ exporting: true });
    try {
      const res = await api.generateWorksheetPdf({
        age_group: AGE_GROUPS[this.data.ageIndex],
        difficulty: this.data.difficulty,
        dimensions: this.data.selectedDims.join(","),
        include_answer: true,
      });
      // callContainer 二进制：res.data 是 ArrayBuffer；downloadFile：res.tempFilePath
      let filePath = res.tempFilePath;
      if (!filePath && res.data && typeof res.data === "object") {
        // callContainer 二进制响应需要转本地文件
        const fs = wx.getFileSystemManager();
        const tmp = wx.env.USER_DATA_PATH + "/worksheet_" + Date.now() + ".pdf";
        fs.writeFileSync(tmp, res.data, "binary");
        filePath = tmp;
      }
      if (!filePath) {
        throw new Error("导出失败：未获取到文件");
      }
      // 打开 PDF 预览（用户可保存/转发）
      wx.openDocument({
        filePath,
        fileType: "pdf",
        showMenu: true,
        fail: (err) => {
          console.error("[exportPdf] openDocument fail:", err);
          wx.showToast({ title: "PDF 已下载，请用其他方式打开", icon: "none", duration: 3000 });
        },
      });
    } catch (e) {
      console.error("[exportPdf] err:", e);
      wx.showToast({ title: (e && e.message) || "导出失败，请重试", icon: "none", duration: 3000 });
    } finally {
      this.setData({ exporting: false });
    }
  },
});
