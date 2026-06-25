"use client";

import { useState, useCallback, useEffect } from "react";
import { toast } from "sonner";
import Link from "next/link";
import { api, type ChildRecord } from "@/lib/api-client";
import {
  AssessmentOverview,
  TeacherReportView,
  ParentReportView,
  UploadPanel,
  AnalysisSettingsPanel,
  AnalysisProgress,
} from "@/components/analysis";
import { MascotCharacter } from "@/components/kid";
import type {
  AssessmentResult,
  TeacherReport,
  ParentReport,
} from "@/lib/api-client";

type AgeGroup = "small" | "middle" | "large";
type ReportTab = "teacher" | "parent";

const PROGRESS_STEPS = [
  { label: "预处理", icon: "🖼️" },
  { label: "AI识别", icon: "🔍" },
  { label: "评估", icon: "📊" },
  { label: "报告", icon: "📝" },
];

export default function AssessmentPage() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [ageGroup, setAgeGroup] = useState<AgeGroup>("middle");
  const [childName, setChildName] = useState("");
  const [childrenList, setChildrenList] = useState<ChildRecord[]>([]);
  const [selectedChildId, setSelectedChildId] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressStep, setProgressStep] = useState("");
  const [activeReportTab, setActiveReportTab] = useState<ReportTab>("teacher");
  const [result, setResult] = useState<{
    assessment: AssessmentResult;
    teacherReport: TeacherReport;
    parentReport: ParentReport;
    reportId?: number;
    analysisId?: number;
  } | null>(null);

  useEffect(() => {
    api.children.list().then((d) => setChildrenList(d.children)).catch(() => {});
  }, []);

  const handleChildSelect = useCallback((child: ChildRecord) => {
    setSelectedChildId(child.id);
    setChildName(child.name);
    setAgeGroup((child.age_group as AgeGroup) || "middle");
  }, []);

  const handleCameraCapture = useCallback((capturedFile: File, previewUrl: string) => {
    setFile(capturedFile);
    setPreview(previewUrl);
    setResult(null);
  }, []);

  const loadDemo = useCallback(async () => {
    setLoading(true);
    setProgressStep("正在加载演示数据...");
    setProgress(50);
    try {
      const [assessment, teacher, parent] = await Promise.all([
        api.analysis.demo(ageGroup, childName || "小明"),
        api.reports.demoTeacher(ageGroup, childName || "小明"),
        api.reports.demoParent(ageGroup, childName || "小明"),
      ]);
      setProgress(100);
      setProgressStep("完成！");
      setActiveReportTab("teacher");
      setResult({
        assessment,
        teacherReport: teacher,
        parentReport: parent,
        reportId: (teacher as any).report_id ?? (parent as any).report_id,
      });
      toast.success("演示数据加载完成 🎉");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "加载演示数据失败");
    } finally {
      setLoading(false);
    }
  }, [ageGroup, childName]);

  const handleAnalyze = useCallback(async () => {
    if (!file) return;
    setLoading(true);
    setProgress(10);
    setProgressStep("正在预处理图片...");
    try {
      setProgress(30);
      setProgressStep("正在 AI 识别操作单...");
      const data = await api.worksheets.uploadAndAnalyze(
        file, ageGroup, childName || "小朋友",
        selectedChildId ?? undefined,
      );
      setProgress(80);
      setProgressStep("正在生成报告...");
      setActiveReportTab("teacher");
      const realAnalysisId = (data as any).persisted?.analysis_id;
      setResult({
        assessment: data.assessment,
        teacherReport: data.reports.teacher,
        parentReport: data.reports.parent,
        reportId: undefined,
        analysisId: realAnalysisId,
      });
      setProgress(100);
      setProgressStep("分析完成！");
      toast.success("操作单分析完成 🎉");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "分析失败，请重试");
    } finally {
      setLoading(false);
    }
  }, [file, ageGroup, childName, selectedChildId]);

  // Determine current progress step index
  const progressIndex = progress <= 0 ? -1
    : progress < 30 ? 0
    : progress < 60 ? 1
    : progress < 90 ? 2
    : progress >= 100 ? 3
    : 2;

  return (
    <div
      className="flex-1 p-4 md:p-6 max-w-6xl mx-auto space-y-6"
      style={{ minHeight: "calc(100vh - 56px)" }}
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <span className="animate-kid-float"><MascotCharacter size="sm" /></span>
        <div>
          <h1 className="text-2xl font-extrabold" style={{ color: "var(--kid-blue)" }}>
            📸 AI评价
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            上传幼儿数学操作单，AI自动识别并进行4维度能力评估
          </p>
        </div>
      </div>

      {/* Upload & Settings */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 kid-stagger">
        <div className="lg:col-span-2 animate-kid-slide-up">
          <UploadPanel
            onFileChange={(f, url) => { setFile(f); setPreview(url); setResult(null); }}
            onCameraCapture={handleCameraCapture}
            preview={preview}
          />
        </div>
        <div className="animate-kid-slide-up" style={{ animationDelay: "100ms" }}>
          <AnalysisSettingsPanel
            ageGroup={ageGroup}
            onAgeGroupChange={setAgeGroup}
            childName={childName}
            onChildNameChange={setChildName}
            children_list={childrenList}
            onChildSelect={handleChildSelect}
            selectedChildId={selectedChildId}
            onAnalyze={handleAnalyze}
            onLoadDemo={loadDemo}
            loading={loading}
            hasFile={!!file}
            actionLabel="开始分析"
          />
        </div>
      </div>

      {/* Progress with step dots */}
      {loading && (
        <div className="animate-kid-slide-up">
          <AnalysisProgress
            progress={progress}
            progressStep={progressStep}
          />
          {/* Step indicator dots */}
          <div className="flex items-center justify-center gap-2 mt-4">
            {PROGRESS_STEPS.map((step, i) => {
              const done = i < progressIndex;
              const active = i === progressIndex;
              return (
                <div key={i} className="flex items-center gap-2">
                  <div
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all duration-300 ${
                      done
                        ? "bg-green-100 text-green-700"
                        : active
                        ? "bg-blue-100 text-blue-700 scale-110"
                        : "bg-slate-100 text-slate-400"
                    }`}
                  >
                    <span>{done ? "✅" : step.icon}</span>
                    <span className="hidden sm:inline">{step.label}</span>
                  </div>
                  {i < PROGRESS_STEPS.length - 1 && (
                    <div
                      className={`w-6 h-0.5 rounded transition-colors ${
                        i < progressIndex ? "bg-green-400" : "bg-slate-200"
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Results */}
      {result && !loading && (
        <div className="space-y-6 animate-kid-slide-up">
          <AssessmentOverview assessment={result.assessment} />

          {/* Report Tabs */}
          <div
            className="rounded-[--kid-radius-xl] border-2 border-kid-blue/20 overflow-hidden"
            style={{ boxShadow: "var(--kid-shadow-card)" }}
          >
            <div className="flex" style={{ backgroundColor: "var(--kid-bg-sky)" }}>
              <button
                onClick={() => setActiveReportTab("teacher")}
                className="flex-1 px-4 py-3 text-sm font-bold transition-all"
                style={{
                  backgroundColor: activeReportTab === "teacher" ? "#fff" : "transparent",
                  color: activeReportTab === "teacher" ? "var(--kid-blue)" : "var(--kid-blue)",
                  opacity: activeReportTab === "teacher" ? 1 : 0.55,
                  borderTopLeftRadius: "var(--kid-radius-xl)",
                }}
              >
                📋 教师版报告
              </button>
              <button
                onClick={() => setActiveReportTab("parent")}
                className="flex-1 px-4 py-3 text-sm font-bold transition-all"
                style={{
                  backgroundColor: activeReportTab === "parent" ? "#fff" : "transparent",
                  color: "var(--kid-coral)",
                  opacity: activeReportTab === "parent" ? 1 : 0.55,
                  borderTopRightRadius: "var(--kid-radius-xl)",
                }}
              >
                🏠 家长版报告
              </button>
            </div>
            <div className="p-4 bg-white">
              {activeReportTab === "teacher" ? (
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
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
