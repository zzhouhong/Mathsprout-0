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
  TeacherReviewPanel,
} from "@/components/analysis";
import { EvaluationTrace } from "@/components/learning/evaluation-trace";
import { MascotCharacter } from "@/components/kid";
import type {
  AssessmentResult,
  TeacherReport,
  ParentReport,
  VisionResult,
  ProblemForReview,
} from "@/lib/api-client";

type AgeGroup = "small" | "middle" | "large";
type ReportTab = "teacher" | "parent";

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

  // ─── Error transparency state ─────────────────────────────────────
  const [lastError, setLastError] = useState<string | null>(null);

  // ─── Evaluation trace state ───────────────────────────────────────
  const [evaluationTrace, setEvaluationTrace] = useState<any>(null);
  const [traceLoading, setTraceLoading] = useState(false);

  // ─── Teacher Review state ──────────────────────────────────────────
  const [visionResult, setVisionResult] = useState<VisionResult | null>(null);
  const [reviewPhase, setReviewPhase] = useState<"idle" | "reviewing" | "confirmed">("idle");

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

  const handleAnalyze = useCallback(async () => {
    if (!file) return;
    setLoading(true);
    setLastError(null);
    setEvaluationTrace(null);
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
      const realReportId = (data as any).persisted?.report_id;
      setResult({
        assessment: data.assessment,
        teacherReport: data.reports.teacher,
        parentReport: data.reports.parent,
        reportId: realReportId,
        analysisId: realAnalysisId,
      });
      // Use inline evaluation_trace from response if available, otherwise fetch separately
      if ((data as any).evaluation_trace) {
        setEvaluationTrace((data as any).evaluation_trace);
      } else if (realAnalysisId) {
        setTraceLoading(true);
        try {
          const trace = await api.worksheets.traceByAnalysis(realAnalysisId);
          setEvaluationTrace(trace);
        } catch { /* trace is optional */ }
        setTraceLoading(false);
      }
      setProgress(100);
      setProgressStep("分析完成！");
      toast.success("操作单分析完成 🎉");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "分析失败，请重试";
      setLastError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [file, ageGroup, childName, selectedChildId]);

  // ─── Teacher Review handlers ───────────────────────────────────────

  const handleRecognize = useCallback(async () => {
    if (!file) return;
    setLoading(true);
    setLastError(null);
    setProgress(20);
    setProgressStep("正在预处理...");
    try {
      setProgress(40);
      setProgressStep("正在 AI 识别操作单（可能需要15-30秒）...");
      const data = await api.worksheets.recognize(file, ageGroup, childName || "小朋友");
      setVisionResult(data.vision);
      setReviewPhase("reviewing");
      setProgress(100);
      setProgressStep("识别完成，请复核幼儿答案");
      toast.success("识别完成，请确认每题答案是否准确 📝");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "识别失败，请重试";
      setLastError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }, [file, ageGroup, childName]);

  const handleConfirmAnswers = useCallback(
    async (correctedProblems: ProblemForReview[]) => {
      setLoading(true);
      setProgress(50);
      setProgressStep("正在重新评估...");
      try {
        setProgress(80);
        setProgressStep("正在生成报告...");
        const data = await api.worksheets.confirm({
          child_name: childName || "小朋友",
          age_group: ageGroup,
          problems: correctedProblems,
          observations: visionResult?.observations as Record<string, unknown> | undefined,
        });
        setResult({
          assessment: data.assessment,
          teacherReport: data.reports.teacher,
          parentReport: data.reports.parent,
        });
        // Confirm endpoint now returns evaluation_trace too — surface it so
        // the 13-sub-dimension trace panel stays populated after teacher review.
        if ((data as any).evaluation_trace) {
          setEvaluationTrace((data as any).evaluation_trace);
        }
        setReviewPhase("confirmed");
        setProgress(100);
        setProgressStep("复核评估完成！");
        toast.success("复核评估完成 🎉");
      } catch (err) {
        const msg = err instanceof Error ? err.message : "评估失败，请重试";
        setLastError(msg);
        toast.error(msg);
      } finally {
        setLoading(false);
      }
    },
    [childName, ageGroup, visionResult]
  );

  const handleSkipReview = useCallback(async () => {
    if (!visionResult) return;
    const problemsAsIs: ProblemForReview[] = (visionResult.problems || []).map((p) => ({
      id: p.id,
      type: p.type,
      child_answer: p.child_answer || "",
      correct_answer: p.correct_answer,
      is_correct: (p.child_answer || "").trim() === (p.correct_answer || "").trim(),
      confidence: 1.0,
      handwriting_quality: p.handwriting_quality || "clear",
      has_erasure: p.has_erasure || false,
      erasure_pattern: p.erasure_pattern || "none",
      strategy_indicators: p.strategy_indicators || "",
    }));
    await handleConfirmAnswers(problemsAsIs);
  }, [visionResult, handleConfirmAnswers]);

  return (
    <div
      className="flex-1 p-4 md:p-6 max-w-6xl mx-auto space-y-6 min-h-[calc(100vh-112px)] md:min-h-[calc(100vh-56px)]"
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
            onFileChange={(f, url) => { setFile(f); setPreview(url); setResult(null); setVisionResult(null); setReviewPhase("idle"); }}
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
            onRecognize={handleRecognize}
            loading={loading}
            hasFile={!!file}
            actionLabel="开始分析"
          />
        </div>
      </div>

      {/* Progress with step indicator */}
      {loading && (
        <div className="animate-kid-slide-up">
          <AnalysisProgress
            progress={progress}
            progressStep={progressStep}
          />
        </div>
      )}

      {/* ── Error transparency: show detailed error when analysis fails ── */}
      {lastError && !loading && (
        <div className="animate-kid-slide-up p-4 bg-red-50 border-2 border-red-200 rounded-xl">
          <div className="flex items-start gap-3">
            <span className="text-xl flex-shrink-0">⚠️</span>
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-semibold text-red-700 mb-1">分析遇到问题</h4>
              <p className="text-sm text-red-600 break-words">{lastError}</p>
              <div className="flex gap-2 mt-3">
                <button
                  onClick={() => setLastError(null)}
                  className="px-3 py-1.5 text-xs rounded-lg bg-red-100 text-red-700 hover:bg-red-200 transition-colors"
                >
                  关闭
                </button>
                <button
                  onClick={() => { setLastError(null); handleAnalyze(); }}
                  className="px-3 py-1.5 text-xs rounded-lg bg-white text-red-600 border border-red-200 hover:bg-red-50 transition-colors"
                >
                  🔄 重试
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Teacher Review Panel (between recognition and assessment) ── */}
      {reviewPhase === "reviewing" && visionResult && !loading && (
        <div className="animate-kid-slide-up">
          <TeacherReviewPanel
            visionResult={visionResult}
            previewUrl={preview}
            childName={childName || "小朋友"}
            ageGroup={ageGroup}
            onConfirm={handleConfirmAnswers}
            onSkip={handleSkipReview}
            loading={false}
          />
        </div>
      )}

      {/* Loading during confirm */}
      {loading && reviewPhase === "reviewing" && (
        <div className="animate-kid-slide-up">
          <AnalysisProgress progress={progress} progressStep={progressStep} />
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

          {/* ── Evaluation Trace ── */}
          <div
            className="rounded-[--kid-radius-xl] border-2 border-kid-purple/20 overflow-hidden"
            style={{ boxShadow: "var(--kid-shadow-card)" }}
          >
            <div
              className="px-4 py-3 font-bold text-sm"
              style={{ backgroundColor: "var(--kid-bg-lavender, #f5f0ff)", color: "var(--kid-purple)" }}
            >
              🔍 评估过程追溯
            </div>
            <div className="p-4 bg-white">
              {traceLoading ? (
                <div className="animate-pulse space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-16 bg-slate-100 rounded-xl" />
                  ))}
                </div>
              ) : (
                <EvaluationTrace
                  data={evaluationTrace}
                  loading={false}
                />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
