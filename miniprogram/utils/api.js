/**
 * 萌芽数学 Mathsprout — API 客户端
 *
 * 自动处理：
 * - Bearer token 注入（从 globalData 或 storage 读取）
 * - 请求前 loading toast
 * - 错误统一弹窗提示
 *
 * 调用通道（由 app.js 的 globalData.useCloud 决定）：
 * - false → wx.request 直连 apiBase（本地调试）
 * - true  → wx.cloud.callContainer 走云托管（免域名 / 备案 / HTTPS）
 *   路径统一拼 /api/v1 前缀；method / data / header 与 wx.request 完全一致。
 */

const app = getApp();

function buildHeaders(extra, auth) {
  const headers = { "Content-Type": "application/json", ...extra };
  if (auth) {
    const token =
      app.globalData.token ||
      wx.getStorageSync("teacher_token") ||
      wx.getStorageSync("token") ||
      "";
    if (token) {
      headers["Authorization"] = "Bearer " + token;
    }
  }
  return headers;
}

function handleResponse(res, showLoading) {
  if (showLoading) wx.hideLoading();
  const statusCode = res.statusCode;
  const body = res.data;
  if (statusCode >= 200 && statusCode < 300) {
    return { ok: true, data: body };
  }
  const msg = body?.detail || body?.message || "请求失败";
  wx.showToast({ title: msg, icon: "none", duration: 2500 });
  return { ok: false, error: { statusCode, message: msg } };
}

function handleFail(err, showLoading) {
  if (showLoading) wx.hideLoading();
  const msg = err.errMsg || "网络连接失败，请检查网络后重试";
  wx.showToast({ title: msg, icon: "none", duration: 2500 });
  return { ok: false, error: err };
}

/**
 * 通用请求函数
 * @param {string} path - API 相对路径（如 /parent/bind，不含 /api/v1 前缀）
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

  if (showLoading) wx.showLoading({ title: "加载中...", mask: true });

  const headers = buildHeaders(header, auth);
  const useCloud = app.globalData.useCloud;

  return new Promise((resolve, reject) => {
    const onResult = (r) => {
      const out = handleResponse(r, showLoading);
      out.ok ? resolve(out.data) : reject(out.error);
    };
    const onError = (e) => {
      const out = handleFail(e, showLoading);
      reject(out.error);
    };

    if (useCloud) {
      // 微信云托管：内网调用，免域名 / 备案 / HTTPS
      wx.cloud
        .callContainer({
          config: { env: app.globalData.cloudEnv },
          path: "/api/v1" + path,
          method,
          data,
          header: {
            ...headers,
            "X-WX-SERVICE": app.globalData.cloudService,
          },
        })
        .then(onResult)
        .catch(onError);
    } else {
      wx.request({
        url: app.globalData.apiBase + path,
        method,
        data,
        header: headers,
        success: onResult,
        fail: onError,
      });
    }
  });
}

/**
 * 文件上传（教师拍照分析）
 *
 * 注意：云托管通道暂不支持 multipart 文件直传。useCloud=true 时，
 * 需先改造为「wx.cloud.uploadFile 上传云存储 → 后端按 fileID 取文件分析」，
 * 该改造属于部署阶段任务；此处先给出友好提示，避免教师端直接崩溃。
 */
function uploadFile(path, filePath, formData = {}) {
  if (app.globalData.useCloud) {
    wx.showToast({
      title: "云托管文件上传待部署后开启",
      icon: "none",
      duration: 2500,
    });
    return Promise.reject({ message: "cloud-upload-not-ready" });
  }

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

  getChildren: () => request("/children", { auth: true }),

  createChild: (data) =>
    request("/children", { method: "POST", auth: true, data }),

  getChildDetail: (childId) => request("/children/" + childId, { auth: true }),

  updateChild: (childId, data) =>
    request("/children/" + childId, { method: "PUT", auth: true, data }),

  deleteChild: (childId) =>
    request("/children/" + childId, { method: "DELETE", auth: true }),

  getChildReports: (childId) =>
    request("/reports/history/" + childId, { auth: true, showLoading: true }),

  getTeacherReport: (reportId) =>
    request("/reports/teacher/" + reportId, { auth: true, showLoading: true }),

  uploadAndAnalyze: (filePath, formData) =>
    uploadFile("/worksheets/demo", filePath, formData),

  // ─── 工作单生成 ───────────────────────────────
  generateWorksheet: (params) => {
    const qs = Object.keys(params)
      .filter((k) => params[k] !== undefined && params[k] !== null && params[k] !== "")
      .map((k) => encodeURIComponent(k) + "=" + encodeURIComponent(params[k]))
      .join("&");
    return request("/worksheets/generate?" + qs, { auth: true, showLoading: true });
  },
};
