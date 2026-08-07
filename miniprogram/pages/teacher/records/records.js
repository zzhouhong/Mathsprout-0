const api = require("../../../utils/api");

Page({
  data: {
    records: [],
    loading: true,
  },

  onLoad() {
    this.loadRecords();
  },

  loadRecords() {
    this.setData({ loading: true });
    api
      .getRecords()
      .then((res) => {
        this.setData({ records: (res && res.records) || [] });
      })
      .catch(() => {})
      .finally(() => this.setData({ loading: false }));
  },

  // 查看详情：用记录里的 pdf_base64 直接打开
  openRecord(e) {
    const id = e.currentTarget.dataset.id;
    const rec = this.data.records.find((r) => r.id === id);
    if (!rec) return;
    wx.showLoading({ title: "加载中..." });
    api
      .getRecord(id)
      .then((detail) => {
        wx.hideLoading();
        if (detail && detail.pdf_base64) {
          const arrayBuffer = wx.base64ToArrayBuffer(detail.pdf_base64);
          const fs = wx.getFileSystemManager();
          const tmp = wx.env.USER_DATA_PATH + "/record_" + id + ".pdf";
          fs.writeFileSync(tmp, arrayBuffer, "binary");
          wx.openDocument({ filePath: tmp, fileType: "pdf", showMenu: true });
        } else {
          wx.showToast({ title: "该记录无 PDF", icon: "none" });
        }
      })
      .catch(() => {
        wx.hideLoading();
        wx.showToast({ title: "加载失败", icon: "none" });
      });
  },

  // 分享：复制 markdown 文本
  copyRecord(e) {
    const id = e.currentTarget.dataset.id;
    api
      .getRecord(id)
      .then((detail) => {
        if (detail && detail.markdown) {
          wx.setClipboardData({ data: detail.markdown });
        }
      })
      .catch(() => {});
  },
});
