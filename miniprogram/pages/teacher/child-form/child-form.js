const api = require("../../../utils/api");

const AGE_GROUPS = ["small", "middle", "large"];
const AGE_LABELS = ["小班（3-4岁）", "中班（4-5岁）", "大班（5-6岁）"];

Page({
  data: {
    name: "",
    ageIndex: 1,
    ageLabels: AGE_LABELS,
    className: "",
    birthDate: "",
    notes: "",
    submitting: false,
    error: "",
    // 提交成功后展示生成的访问码
    created: null,
  },

  onNameInput(e) {
    this.setData({ name: e.detail.value });
  },

  onAgeChange(e) {
    this.setData({ ageIndex: Number(e.detail.value) });
  },

  onClassInput(e) {
    this.setData({ className: e.detail.value });
  },

  onBirthChange(e) {
    this.setData({ birthDate: e.detail.value });
  },

  onNotesInput(e) {
    this.setData({ notes: e.detail.value });
  },

  async submit() {
    const name = this.data.name.trim();
    if (!name) {
      wx.showToast({ title: "请输入幼儿姓名", icon: "none" });
      return;
    }

    this.setData({ submitting: true, error: "" });

    const data = {
      name,
      age_group: AGE_GROUPS[this.data.ageIndex],
    };
    if (this.data.className.trim()) data.class_name = this.data.className.trim();
    if (this.data.birthDate) data.birth_date = this.data.birthDate;
    if (this.data.notes.trim()) data.notes = this.data.notes.trim();

    try {
      const res = await api.createChild(data);
      this.setData({ created: res, submitting: false });
      wx.showToast({ title: "添加成功", icon: "success" });
    } catch (e) {
      this.setData({ error: e.message || "添加失败，请重试", submitting: false });
    }
  },

  copyCode() {
    if (this.data.created && this.data.created.parent_access_code) {
      wx.setClipboardData({
        data: this.data.created.parent_access_code,
        success: () => wx.showToast({ title: "访问码已复制", icon: "success" }),
      });
    }
  },

  backToList() {
    wx.redirectTo({ url: "/pages/teacher/class-view/class-view" });
  },
});
