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
    console.log('[capture] takePhoto button tapped');
    this.setData({ result: null, error: "" });
    this.chooseMedia({ sourceType: ["camera"], label: "拍照" });
  },

  choosePhoto() {
    console.log('[capture] choosePhoto button tapped');
    this.setData({ result: null, error: "" });
    this.chooseMedia({ sourceType: ["album"], label: "选择图片" });
  },

  // 统一选图入口：微信要求真机调相机/相册前先完成隐私授权，
  // 主动调 requirePrivacyAuthorize 触发 app.js 里的授权弹窗，
  // 否则体验版/正式版真机上 chooseMedia 会静默失败（点了没反应）。
  chooseMedia(opts) {
    // v1.0.3：彻底调试 + 多重 fallback
    console.log('[capture] === chooseMedia v1.0.3 ===', opts);
    // 立即可见的反馈
    this.setData({ error: '正在打开' + opts.label + '...' });
    
    const showResult = (title, msg, isError) => {
      console.log('[capture] RESULT:', title, msg);
      // 用 setData 显示（modal 可能被遮挡）
      this.setData({ error: isError ? ('❌ ' + msg) : ('✅ ' + msg) });
      if (isError) {
        wx.showToast({ title: title + '失败', icon: 'none', duration: 4000 });
      }
    };
    
    const tryChooseMedia = () => {
      console.log('[capture] trying wx.chooseMedia...');
      wx.chooseMedia({
        count: 1,
        mediaType: ['image'],
        sourceType: opts.sourceType,
        sizeType: ['original', 'compressed'],
        camera: 'back',
        success: (r) => {
          console.log('[capture] chooseMedia SUCCESS:', JSON.stringify(r));
          if (r && r.tempFiles && r.tempFiles[0]) {
            this.setData({ src: r.tempFiles[0].tempFilePath, error: '' });
            wx.showToast({ title: '✅ 已选图片', icon: 'success', duration: 1500 });
          } else {
            showResult(opts.label, '返回为空 (tempFiles=' + JSON.stringify(r) + ')', true);
          }
        },
        fail: (err) => {
          console.log('[capture] chooseMedia FAIL:', JSON.stringify(err));
          // 尝试 fallback 到 chooseImage
          this.tryChooseImage(opts);
        },
        complete: (r) => {
          console.log('[capture] chooseMedia COMPLETE:', JSON.stringify(r));
        }
      });
    };
    
    // 暴露 tryChooseImage 给 fail 回调
    this.tryChooseImage = (opts) => {
      console.log('[capture] trying wx.chooseImage...');
      if (typeof wx.chooseImage !== 'function') {
        showResult(opts.label, 'wx.chooseImage 不存在', true);
        return;
      }
      wx.chooseImage({
        count: 1,
        sizeType: ['original', 'compressed'],
        sourceType: opts.sourceType,
        success: (r) => {
          console.log('[capture] chooseImage SUCCESS:', JSON.stringify(r));
          const tf = r.tempFilePaths && r.tempFilePaths[0];
          if (tf) {
            this.setData({ src: tf, error: '' });
            wx.showToast({ title: '✅ 已选图片', icon: 'success', duration: 1500 });
          } else {
            showResult(opts.label, 'chooseImage 返回为空', true);
          }
        },
        fail: (err) => {
          console.log('[capture] chooseImage FAIL:', JSON.stringify(err));
          const msg = (err && err.errMsg) || '未知错误';
          showResult(opts.label, msg, true);
          // 给用户操作建议
          if (msg.indexOf('privacy') > -1 || msg.indexOf('authorize') > -1) {
            this.setData({ error: '❌ 隐私授权问题：' + msg + '\n\n请到公众平台后台「设置→服务内容声明→用户隐私保护指引」勾选「拍摄/相册」接口' });
          }
        },
        complete: (r) => {
          console.log('[capture] chooseImage COMPLETE:', JSON.stringify(r));
        }
      });
    };
    
    // 直接尝试 chooseImage（绕过 requirePrivacyAuthorize）
    if (typeof wx.chooseImage === 'function') {
      console.log('[capture] direct chooseImage first');
      this.tryChooseImage(opts);
    } else {
      tryChooseMedia();
    }
  },

  // 失败时展示真实原因，避免真机"点了没反应"无法排查
  onChooseFail(err, label) {
    console.error("chooseMedia fail:", err);
    const msg = (err && err.errMsg) || "";
    if (msg.indexOf("cancel") > -1) {
      wx.showToast({ title: label + "已取消", icon: "none" });
    } else if (msg.indexOf("privacy") > -1) {
      wx.showModal({
        title: "隐私授权未完成",
        content:
          "请在弹窗中同意《隐私保护指引》后重试。若仍失败，需管理员在微信公众平台「设置 → 服务内容声明 → 用户隐私保护指引」完善相机/相册声明后重新进入小程序。",
        showCancel: false,
      });
    } else {
      wx.showModal({
        title: label + "失败",
        content: msg || "未知错误，请退出小程序重试",
        showCancel: false,
      });
    }
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
