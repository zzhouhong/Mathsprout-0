/**
 * 萌芽助手 Mathsprout — 比赛Demo主页
 *
 * 单页纵向流：上传操作单 → AI分析进度 → 教师/家长双版报告
 * 无登录、无侧边栏、无批量——只聚焦核心故事线。
 */
"use client";

import { useState, useCallback } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api-client";
import {
  AssessmentOverview,
  TeacherReportView,
  ParentReportView,
  UploadPanel,
  AnalysisProgress,
} from "@/components/analysis";
import type {
  AssessmentResult,
  TeacherReport,
  ParentReport,
  ProgressEvent,
} from "@/lib/api-client";

// ─── Types ────────────────────────────────────────────────────────────

type AgeGroup = "small" | "middle" | "large";

const AGE_OPTIONS: { value: AgeGroup; label: string; emoji: string; desc: string }[] = [
  { value: "small", label: "小班", emoji: "🌱", desc: "3–4岁" },
  { value: "middle", label: "中班", emoji: "🌿", desc: "4–5岁" },
  { value: "large", label: "大班", emoji: "🌳", desc: "5–6岁" },
];

// ─── Steps indicator ──────────────────────────────────────────────────

const STEPS = [
  { step: "preprocess", label: "图片预处理", icon: "🖼️" },
  { step: "recognize", label: "AI 识别题目", icon: "🧠" },
  { step: "assess", label: "四维评估", icon: "📊" },
  { step: "report", label: "生成报告", icon: "📝" },
];

function getStepIndex(progressStep: string): number {
  if (!progressStep) return -1;
  if (progressStep.includes("预处理") || progressStep.includes("preprocess")) return 0;
  if (progressStep.includes("识别") || progressStep.includes("recognize")) return 1;
  if (progressStep.includes("评估") || progressStep.includes("assess")) return 2;
  if (progressStep.includes("报告") || progressStep.includes("report")) return 3;
  if (progressStep.includes("完成") || progressStep.includes("complete")) return 4;
  return -1;
}

// ─── Page ─────────────────────────────────────────────────────────────

export default function DemoPage() {
  // File state
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);

  // Settings
  const [ageGroup, setAgeGroup] = useState<AgeGroup>("middle");
  const [childName, setChildName] = useState("");

  // Analysis state
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressStep, setProgressStep] = useState("");

  // Result state
  const [activeTab, setActiveTab] = useState<"teacher" | "parent">("teacher");
  const [result, setResult] = useState<{
    assessment: AssessmentResult;
    teacherReport: TeacherReport;
    parentReport: ParentReport;
    reportId?: number;
  } | null>(null);

  // ── Handlers ──────────────────────────────────────────────────────

  const handleFileChange = useCallback((f: File, previewUrl: string) => {
    setFile(f);
    setPreview(previewUrl);
    setResult(null);
  }, []);

  const handleCameraCapture = useCallback((f: File, previewUrl: string) => {
    setFile(f);
    setPreview(previewUrl);
    setResult(null);
  }, []);

  const handleAnalyze = useCallback(async () => {
    if (!file) return;

    setLoading(true);
    setProgress(5);
    setProgressStep("正在预处理图片...");
    setResult(null);

    try {
      await api.worksheets.analyzeWithStream(
        file,
        ageGroup,
        childName || "小朋友",
        // onProgress
        (event: ProgressEvent) => {
          setProgress(event.progress_pct ?? 0);
          setProgressStep(event.message || event.step);
        },
        // onComplete
        (data) => {
          setResult({
            assessment: data.assessment,
            teacherReport: data.reports.teacher,
            parentReport: data.reports.parent,
            reportId:
              data.reports.teacher.report_id ?? data.reports.parent.report_id,
          });
          setProgress(100);
          setProgressStep("分析完成！");
          toast.success("操作单分析完成 ✅");
          setLoading(false);
        },
        // onError
        (error) => {
          toast.error(error.message || "分析失败，请重试");
          setProgressStep("分析失败");
          setLoading(false);
        }
      );
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "分析失败";
      toast.error(message);
      setProgressStep("分析失败，请重试");
      setLoading(false);
    }
  }, [file, ageGroup, childName]);

  const currentStep = getStepIndex(progressStep);

  // ── Render ─────────────────────────────────────────────────────────

  return (
    <main className="max-w-3xl mx-auto px-4 py-8 md:py-12 space-y-8">
      {/* ═══ Hero ═══ */}
      <header className="text-center space-y-3">
        <div className="inline-flex items-center gap-2 bg-white/70 backdrop-blur rounded-full px-4 py-1.5 border border-amber-200 shadow-sm">
          <span className="text-sm text-amber-700 font-medium">
            📖 依据《学前儿童数学学习与发展核心经验》PCK框架
          </span>
        </div>
        <h1 className="text-3xl md:text-4xl font-extrabold text-slate-800 tracking-tight">
          🌱 萌芽助手{" "}
          <span className="text-slate-400 font-normal text-xl">Mathsprout</span>
        </h1>
        <p className="text-lg text-slate-500 max-w-lg mx-auto leading-relaxed">
          AI 幼儿数学操作单分析智能体
          <br />
          <span className="text-sm text-slate-400">
            拍照上传 → 自动识别分析 → 教师PCK报告 + 家长指导报告
          </span>
        </p>
      </header>

      {/* ═══ Upload + Settings ═══ */}
      <section className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-5">
        <h2 className="text-lg font-bold text-slate-700 flex items-center gap-2">
          <span>📸</span> 上传幼儿数学操作单
        </h2>

        {/* Age group selector */}
        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-500">选择年龄段</label>
          <div className="flex gap-2">
            {AGE_OPTIONS.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setAgeGroup(opt.value)}
                className={`flex-1 py-2.5 px-3 rounded-xl border-2 text-sm font-medium transition-all ${
                  ageGroup === opt.value
                    ? "border-amber-400 bg-amber-50 text-amber-800 shadow-sm"
                    : "border-slate-200 bg-white text-slate-500 hover:border-slate-300"
                }`}
              >
                <span className="text-lg">{opt.emoji}</span>
                <br />
                {opt.label}
                <span className="block text-xs opacity-60">{opt.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Child name (optional) */}
        <div>
          <label className="text-sm font-medium text-slate-500">
            幼儿姓名 <span className="text-slate-300">（选填）</span>
          </label>
          <input
            type="text"
            value={childName}
            onChange={(e) => setChildName(e.target.value)}
            placeholder="如：小明"
            className="mt-1 w-full max-w-xs rounded-lg border border-slate-200 px-3 py-2 text-sm focus:outline-none focus:border-amber-400 focus:ring-2 focus:ring-amber-100"
          />
        </div>

        {/* Upload area */}
        <UploadPanel
          preview={preview}
          onFileChange={handleFileChange}
          onCameraCapture={handleCameraCapture}
        />

        {/* Analyze button */}
        <button
          onClick={handleAnalyze}
          disabled={!file || loading}
          className={`w-full py-3 rounded-xl text-base font-bold transition-all ${
            !file || loading
              ? "bg-slate-100 text-slate-400 cursor-not-allowed"
              : "bg-amber-500 text-white hover:bg-amber-600 shadow-md hover:shadow-lg active:scale-[0.98]"
          }`}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="animate-spin">⏳</span> 分析中...
            </span>
          ) : (
            "🚀 开始 AI 分析"
          )}
        </button>
      </section>

      {/* ═══ Progress (shown during analysis) ═══ */}
      {loading && (
        <section className="space-y-4">
          <AnalysisProgress progressStep={progressStep} progress={progress} />

          {/* Step indicators */}
          <div className="grid grid-cols-4 gap-2">
            {STEPS.map((s, i) => {
              const isDone = currentStep > i;
              const isActive = currentStep === i;

              return (
                <div
                  key={s.step}
                  className={`text-center py-2.5 px-2 rounded-xl border text-xs transition-all ${
                    isDone
                      ? "border-green-200 bg-green-50 text-green-700"
                      : isActive
                        ? "border-amber-300 bg-amber-50 text-amber-700 shadow-sm"
                        : "border-slate-100 bg-slate-50 text-slate-300"
                  }`}
                >
                  <div className="text-lg mb-0.5">
                    {isDone ? "✅" : isActive ? "⏳" : s.icon}
                  </div>
                  {s.label}
                </div>
              );
            })}
          </div>
        </section>
      )}

      {/* ═══ Results ═══ */}
      {result && !loading && (
        <section className="space-y-4">
          {/* Tab toggle */}
          <div className="flex bg-white rounded-xl border border-slate-200 p-1 shadow-sm">
            <button
              onClick={() => setActiveTab("teacher")}
              className={`flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                activeTab === "teacher"
                  ? "bg-indigo-100 text-indigo-700 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              📝 教师报告
            </button>
            <button
              onClick={() => setActiveTab("parent")}
              className={`flex-1 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                activeTab === "parent"
                  ? "bg-green-100 text-green-700 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              💚 家长报告
            </button>
          </div>

          {/* Overview (always visible) */}
          <AssessmentOverview assessment={result.assessment} />

          {/* Report content */}
          {activeTab === "teacher" ? (
            <TeacherReportView
              report={result.teacherReport}
              reportId={result.reportId}
            />
          ) : (
            <ParentReportView
              report={result.parentReport}
              reportId={result.reportId}
            />
          )}
        </section>
      )}

      {/* ═══ Footer ═══ */}
      <footer className="text-center space-y-2 pt-4 pb-8">
        <div className="flex items-center justify-center gap-4 text-xs text-slate-400">
          <span>🧠 AI Vision 驱动</span>
          <span>·</span>
          <span>📖 PCK 知识库</span>
          <span>·</span>
          <span>🔒 教师辅助工具</span>
        </div>
        <p className="text-xs text-slate-300">
          本工具定位为教师观察辅助工具，不替代专业教育判断
        </p>
      </footer>
    </main>
  );
}
