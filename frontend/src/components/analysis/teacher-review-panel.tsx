"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { VisionResult, ProblemForReview } from "@/lib/api-client";

// ─── Helpers ───────────────────────────────────────────────────────────

const TYPE_NAMES: Record<string, string> = {
  counting: "点数题",
  compare: "比较题",
  number_composition: "数的组成",
  add_10: "10以内加法",
  sub_10: "10以内减法",
  shape_id: "图形识别",
  spatial: "空间方位",
  pattern_next: "模式规律",
  classify: "分类题",
  sort: "排序题",
};

function describeType(t: string): string {
  return TYPE_NAMES[t] || t;
}

// ─── Props ─────────────────────────────────────────────────────────────

interface TeacherReviewPanelProps {
  visionResult: VisionResult;
  previewUrl: string | null;
  childName: string;
  ageGroup: string;
  onConfirm: (correctedProblems: ProblemForReview[]) => void;
  onSkip: () => void;
  loading: boolean;
}

// ─── Component ─────────────────────────────────────────────────────────

export function TeacherReviewPanel({
  visionResult,
  previewUrl,
  childName,
  ageGroup,
  onConfirm,
  onSkip,
  loading,
}: TeacherReviewPanelProps) {
  // Initialize mutable problem list from AI guesses
  const [problems, setProblems] = useState<ProblemForReview[]>(() =>
    (visionResult.problems || []).map((p) => ({
      id: p.id,
      type: p.type,
      child_answer: p.child_answer || "",
      correct_answer: p.correct_answer,
      is_correct:
        (p.child_answer || "").trim() === (p.correct_answer || "").trim() &&
        (p.child_answer || "").trim() !== "",
      confidence: p.confidence ?? 0.7,
      handwriting_quality: p.handwriting_quality || "unknown",
      has_erasure: p.has_erasure || false,
      erasure_pattern: p.erasure_pattern || "none",
      strategy_indicators: p.strategy_indicators || "",
    }))
  );

  const [editedIds, setEditedIds] = useState<Set<string>>(new Set());

  const ageLabels: Record<string, string> = {
    small: "小班(3-4岁)",
    middle: "中班(4-5岁)",
    large: "大班(5-6岁)",
  };

  const handleAnswerChange = (problemId: string, newAnswer: string) => {
    setProblems((prev) =>
      prev.map((p) => {
        if (p.id !== problemId) return p;
        const trimmed = newAnswer.trim();
        return {
          ...p,
          child_answer: trimmed,
          is_correct:
            trimmed === (p.correct_answer || "").trim() && trimmed !== "",
          confidence: 1.0, // teacher-edited = confirmed
        };
      })
    );
    setEditedIds((prev) => {
      const next = new Set(prev);
      next.add(problemId);
      return next;
    });
  };

  const allAnswered = problems.every(
    (p) => p.child_answer && p.child_answer.trim() !== ""
  );

  return (
    <Card className="p-5 space-y-4">
      {/* ── Header ─────────────────────────────────────────────── */}
      <div className="flex items-center gap-2 flex-wrap">
        <span className="text-lg font-bold text-slate-800">🔍 教师复核</span>
        <Badge variant="secondary" className="text-xs">
          {childName}
        </Badge>
        <Badge variant="secondary" className="text-xs">
          {ageLabels[ageGroup] || ageGroup}
        </Badge>
        <span className="text-xs text-amber-600 font-medium ml-auto">
          请逐一核对 AI 识别的幼儿答案，修改有误的项
        </span>
      </div>

      {/* ── Worksheet Preview ──────────────────────────────────── */}
      {previewUrl && (
        <div className="flex justify-center">
          <img
            src={previewUrl}
            alt="操作单原图"
            className="max-w-[320px] max-h-[240px] rounded-lg border border-slate-200 object-contain shadow-sm"
          />
        </div>
      )}

      {/* ── Problem List ───────────────────────────────────────── */}
      <div className="space-y-2 max-h-[400px] overflow-y-auto">
        {problems.map((p) => {
          const isEdited = editedIds.has(p.id);
          const statusColor = p.is_correct
            ? "border-emerald-200 bg-emerald-50/60"
            : isEdited
            ? "border-amber-300 bg-amber-50/60"
            : "border-red-200 bg-red-50/60";

          return (
            <div
              key={p.id}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg border ${statusColor} transition-colors`}
            >
              {/* Problem ID */}
              <Badge variant="secondary" className="font-mono text-xs shrink-0">
                {p.id}
              </Badge>

              {/* Problem type */}
              <Badge
                variant="ghost"
                className="text-xs bg-slate-100 text-slate-600 shrink-0"
              >
                {describeType(p.type)}
              </Badge>

              {/* Editable child answer */}
              <div className="flex items-center gap-1">
                <span className="text-xs text-slate-400 shrink-0">幼儿答:</span>
                <input
                  type="text"
                  value={p.child_answer}
                  onChange={(e) => handleAnswerChange(p.id, e.target.value)}
                  disabled={loading}
                  className={`w-16 px-2 py-1 border rounded text-sm font-medium text-center
                    focus:outline-none focus:ring-2 focus:ring-indigo-400
                    disabled:opacity-50 disabled:cursor-not-allowed
                    ${isEdited ? "border-amber-400 bg-amber-50" : "border-slate-300"}
                  `}
                />
              </div>

              {/* Correct answer (read-only) */}
              <div className="flex items-center gap-1">
                <span className="text-xs text-slate-400 shrink-0">正确答案:</span>
                <span className="font-mono text-sm font-medium text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                  {p.correct_answer}
                </span>
              </div>

              {/* Status indicator */}
              <Badge
                variant={p.is_correct ? "default" : "destructive"}
                className={`text-xs shrink-0 ${
                  p.is_correct
                    ? "bg-emerald-100 text-emerald-700"
                    : "bg-red-100 text-red-700"
                }`}
              >
                {p.is_correct ? "✓" : "✗"}
              </Badge>

              {/* AI confidence */}
              <span className="text-[10px] text-slate-400 ml-auto shrink-0">
                AI:
                {p.confidence != null
                  ? `${(p.confidence * 100).toFixed(0)}%`
                  : "—"}
              </span>
            </div>
          );
        })}

        {problems.length === 0 && (
          <p className="text-center text-slate-400 py-8">
            AI 未能识别到题目，请使用"快速分析"重试
          </p>
        )}
      </div>

      {/* ── Actions ─────────────────────────────────────────────── */}
      <div className="flex items-center gap-3 pt-3 border-t border-slate-100">
        <button
          onClick={() => onConfirm(problems)}
          disabled={loading || !allAnswered}
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-indigo-600 text-white rounded-lg
            text-sm font-semibold hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed
            transition-colors shadow-sm"
        >
          {loading ? "评估中..." : "✅ 确认并评估"}
        </button>

        <button
          onClick={onSkip}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-white text-slate-600 border border-slate-300
            rounded-lg text-sm font-medium hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed
            transition-colors"
        >
          ⏭️ 跳过复核，直接评估
        </button>

        {editedIds.size > 0 && (
          <span className="text-xs text-amber-600 ml-auto">
            已修改 {editedIds.size} 题
          </span>
        )}
      </div>
    </Card>
  );
}
