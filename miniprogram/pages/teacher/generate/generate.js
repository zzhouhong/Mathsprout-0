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
    scenario: "",
    previewText: "",
    lastResult: null, // 最近一次生成结果（含 pdf_base64，供导出用）
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

  onScenarioInput(e) {
    this.setData({ scenario: e.detail.value || "" });
  },

  // 轮询等待异步生成任务（AI 情境化生成需 20-30s，callContainer 15s 会超时）
  async _waitGenerateTask(taskId) {
    for (let i = 0; i < 50; i++) {
      await new Promise((res) => setTimeout(res, 2000));
      const st = await api.getGenerateTaskStatus(taskId);
      if (st.status === "completed") return st.result;
      if (st.status === "failed") throw new Error(st.error || "AI 生成失败，请重试");
      if (st.status === "not_found") throw new Error("生成任务不存在，请重试");
    }
    throw new Error("AI 生成超时，请重试");
  },

  _markdownToPreview(markdown) {
    return (markdown || "")
      .replace(/^#{1,6}\s*/gm, "")
      .replace(/\*\*(.*?)\*\*/g, "$1")
      .replace(/^>\s?/gm, "")
      .replace(/^---+$/gm, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  },

  async generate() {
    this.setData({ generating: true, error: "", previewText: "" });
    try {
      const params = {
        age_group: AGE_GROUPS[this.data.ageIndex],
        difficulty: this.data.difficulty,
        dimensions: this.data.selectedDims.join(","),
        activity_theme: this.data.scenario,
        format: "markdown",
      };
      let result;
      if (this.data.scenario && this.data.scenario.trim()) {
        // AI 情境化：创建异步任务 + 轮询（耗时 20-30s）
        const { task_id } = await api.createGenerateTask(params);
        result = await this._waitGenerateTask(task_id);
      } else {
        // 无情境：同步快速生成
        result = await api.generateWorksheetPost(params);
      }
      const markdown = (result && (result.markdown || result.markdown_res)) || "";
      const previewText = this._markdownToPreview(markdown);
      if (!previewText) {
        throw new Error("操作单内容为空，请重试");
      }
      this.setData({
        previewText,
        lastResult: result,
      });
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
      // 优先用最近一次生成结果的 pdf_base64（异步任务已含）；没有则同步请求
      let contentBase64 = this.data.lastResult && this.data.lastResult.pdf_base64;
      if (!contentBase64) {
        const params = {
          age_group: AGE_GROUPS[this.data.ageIndex],
          difficulty: this.data.difficulty,
          dimensions: this.data.selectedDims.join(","),
          activity_theme: this.data.scenario,
          include_answer: true,
        };
        let taskResult;
        if (this.data.scenario && this.data.scenario.trim()) {
          // 有情境：异步任务（同步请求会超 15s）
          const { task_id } = await api.createGenerateTask(params);
          taskResult = await this._waitGenerateTask(task_id);
          contentBase64 = taskResult && taskResult.pdf_base64;
        } else {
          const res = await api.generateWorksheetPdf(params);
          contentBase64 = res && res.content_base64;
        }
      }
      if (!contentBase64) {
        throw new Error("导出失败：未获取到文件数据");
      }
      const arrayBuffer = wx.base64ToArrayBuffer(contentBase64);
      const fs = wx.getFileSystemManager();
      const tmp = wx.env.USER_DATA_PATH + "/worksheet_" + Date.now() + ".pdf";
      fs.writeFileSync(tmp, arrayBuffer, "binary");
      // 打开 PDF 预览（用户可保存/转发）
      wx.openDocument({
        filePath: tmp,
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
