/**
 * 萌芽数学 Mathsprout — API 客户端
 *
 * 自动处理：
 * - Bearer token 注入（从 globalData 或 storage 读取）
 * - 请求前 loading toast
 * - 错误统一弹窗提示
 */

const app = getApp();

/**
 * 通用请求函数
 * @param {string} path - API 路径（如 /parent/bind）
 * @param {object} options
 * @param {string} options.method - HTTP 方法
 * @param {object} options.data - 请求体
 * @param {boolean} options.showLoading - 是否显示 loading toast（默认 true）
 * @param {boolean} options.auth - 是否需要认证 token（默认 false）
 * @returns {Promise<any>}
 */
function request(path, options = {}) {
  const {
    method = "GET",
    data,
    showLoading = true,
    auth = false,
    header = {},
  } = options;

  if (showLoading) {
    wx.showLoading({ title: "加载中...", mask: true });
  }

  // 自动注入认证 token
  const headers = { "Content-Type": "application/json", ...header };
  if (auth) {
    const token = app.globalData.token || wx.getStorageSync("token") || "";
    if (token) {
      headers["Authorization"] = "Bearer " + token;
    }
  }

  return new Promise((resolve, reject) => {
    wx.request({
      url: app.globalData.apiBase + path,
      method,
      data,
      header: headers,
      success(res) {
        if (showLoading) wx.hideLoading();
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          const msg = res.data?.detail || res.data?.message || "请求失败";
          wx.showToast({ title: msg, icon: "none", duration: 2500 });
          reject({ statusCode: res.statusCode, message: msg });
        }
      },
      fail(err) {
        if (showLoading) wx.hideLoading();
        const msg = err.errMsg || "网络连接失败，请检查网络后重试";
        wx.showToast({ title: msg, icon: "none", duration: 2500 });
        reject(err);
      },
    });
  });
}

/**
 * 文件上传（用于教师拍照分析）
 */
function uploadFile(path, filePath, formData = {}) {
  wx.showLoading({ title: "分析中...", mask: true });

  const token = app.globalData.token || wx.getStorageSync("token") || "";
  const headers = {};
  if (token) {
    headers["Authorization"] = "Bearer " + token;
  }

  return new Promise((resolve, reject) => {
    wx.uploadFile({
      url: app.globalData.apiBase + path,
      filePath,
      name: "file",
      formData,
      header: headers,
      success(res) {
        wx.hideLoading();
        try {
          const data = JSON.parse(res.data);
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve(data);
          } else {
            const msg = data?.detail || data?.message || "分析失败";
            wx.showToast({ title: msg, icon: "none", duration: 2500 });
            reject({ statusCode: res.statusCode, message: msg });
          }
        } catch (e) {
          wx.showToast({ title: "响应解析失败", icon: "none" });
          reject(e);
        }
      },
      fail(err) {
        wx.hideLoading();
        const msg = err.errMsg || "上传失败，请检查网络";
        wx.showToast({ title: msg, icon: "none", duration: 2500 });
        reject(err);
      },
    });
  });
}

module.exports = {
  request,
  uploadFile,

  // ─── 家长端 ─────────────────────────────────
  bind: (code) =>
    request("/parent/bind", { method: "POST", data: { access_code: code } }),

  getChildProfile: (childId) =>
    request("/parent/child-profile?child_id=" + childId),

  getLatestReport: (childId) =>
    request("/parent/latest-report?child_id=" + childId, { showLoading: true }),

  getReportDetail: (reportId) =>
    request("/reports/parent/" + reportId, { showLoading: true }),

  getReportHistory: (childId) =>
    request("/parent/report-history?child_id=" + childId, { showLoading: true }),

  getGrowthTrend: (childId) =>
    request("/parent/growth-trend?child_id=" + childId, { showLoading: false }),

  // ─── 教师端 ─────────────────────────────────
  login: (email, password) =>
    request("/auth/login", {
      method: "POST",
      data: { email, password },
      auth: false,
    }),

  getChildren: () =>
    request("/children", { auth: true }),

  getChildDetail: (childId) =>
    request("/children/" + childId, { auth: true }),

  getChildReports: (childId) =>
    request("/reports/history/" + childId, { auth: true, showLoading: true }),

  getTeacherReport: (reportId) =>
    request("/reports/teacher/" + reportId, { auth: true, showLoading: true }),

  uploadAndAnalyze: (filePath, formData) =>
    uploadFile("/worksheets/demo", filePath, formData),
};
