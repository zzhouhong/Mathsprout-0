/**
 * 萌芽助手 Mathsprout — API 客户端
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
 * 云托管通道（useCloud=true）：
 *   1) wx.cloud.uploadFile 把图片传到对象存储，拿到 fileID
 *   2) wx.cloud.getTempFileURL 拿临时访问链接（callContainer 请求体上限 100K，不能直传图片）
 *   3) 后端 POST /worksheets/cloud-analyze 下载临时链接并跑完整分析流水线
 * 本地调试通道（useCloud=false）：走 wx.uploadFile 直传后端。
 */
function uploadFile(path, filePath, formData = {}) {
  if (app.globalData.useCloud) {
    wx.showLoading({ title: "分析中...", mask: true });
    return new Promise((resolve, reject) => {
      const extMatch = filePath.match(/\.[^.]+$/) || [".jpg"];
      const cloudPath =
        "uploads/" +
        Date.now() +
        "-" +
        Math.random().toString(36).slice(2, 10) +
        extMatch[0];

      wx.cloud.uploadFile({
        cloudPath,
        filePath,
        config: { env: app.globalData.cloudEnv },
        success: (res) => {
          // 拿临时访问链接交给后端（callContainer 请求体上限 100K，不能直传图片；
          // 临时链接 *.tcb.qcloud.la 可被后端直接读取，绕开「开放接口服务」开关）
          wx.cloud.getTempFileURL({
            fileList: [res.fileID],
            config: { env: app.globalData.cloudEnv },
            success: (urlRes) => {
              const fileUrl = urlRes.fileList && urlRes.fileList[0] && urlRes.fileList[0].tempFileURL;
              if (!fileUrl) {
                wx.hideLoading();
                wx.showToast({ title: "获取图片链接失败", icon: "none", duration: 2500 });
                reject({ message: "get-temp-url-failed" });
                return;
              }
              request("/worksheets/cloud-analyze", {
                method: "POST",
                auth: true,
                showLoading: false,
                data: {
                  file_id: res.fileID,
                  file_url: fileUrl,
                  age_group: formData.age_group || "middle",
                  child_name: formData.child_name || "小朋友",
                  child_id: formData.child_id || null,
                },
              })
                .then((data) => {
                  wx.hideLoading();
                  resolve(data);
                })
                .catch((err) => {
                  wx.hideLoading();
                  reject(err);
                });
            },
            fail: (urlErr) => {
              wx.hideLoading();
              const msg = urlErr.errMsg || "获取图片链接失败";
              wx.showToast({ title: msg, icon: "none", duration: 2500 });
              reject({ message: msg });
            },
          });
        },
        fail: (err) => {
          wx.hideLoading();
          const msg = err.errMsg || "图片上传失败，请重试";
          wx.showToast({ title: msg, icon: "none", duration: 2500 });
          reject({ message: msg });
        },
      });
    });
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

  // 导出操作单 PDF（直接下载文件，不走 JSON request）
  generateWorksheetPdf: (params) => {
    const qs = Object.keys(params)
      .filter((k) => params[k] !== undefined && params[k] !== null && params[k] !== "")
      .map((k) => encodeURIComponent(k) + "=" + encodeURIComponent(params[k]))
      .join("&");
    const qs2 = qs + (qs ? "&" : "") + "format=pdf";
    if (app.globalData.useCloud) {
      // 云托管：callContainer 支持二进制响应
      wx.showLoading({ title: "导出中...", mask: true });
      return new Promise((resolve, reject) => {
        wx.cloud
          .callContainer({
            config: { env: app.globalData.cloudEnv },
            path: "/api/v1/worksheets/generate?" + qs2,
            method: "GET",
            header: { "X-WX-SERVICE": app.globalData.cloudService },
            success: (res) => {
              wx.hideLoading();
              resolve(res);
            },
            fail: (err) => {
              wx.hideLoading();
              reject(err);
            },
          });
      });
    }
    // 本地调试：wx.downloadFile 直连
    wx.showLoading({ title: "导出中...", mask: true });
    return new Promise((resolve, reject) => {
      wx.downloadFile({
        url: app.globalData.apiBase + "/worksheets/generate?" + qs2,
        success: (res) => {
          wx.hideLoading();
          resolve(res);
        },
        fail: (err) => {
          wx.hideLoading();
          reject(err);
        },
      });
    });
  },
};
