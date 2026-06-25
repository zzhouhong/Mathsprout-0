"use client";

import { useState } from "react";

/**
 * Evaluation Trace Component
 *
 * Shows the AI's assessment reasoning process:
 * Problem → Sub-Dimension → PCK Indicator → Evidence → Score
 *
 * This is the "transparent AI" feature — teachers can inspect exactly
 * why each problem received its score.
 */

interface ProblemDetail {
  problem_id: string;
  type: string;
  type_description: string;
  child_answer: string;
  correct_answer: string;
  is_correct: boolean;
  evidence: string;
  strategy: string;
  handwriting_quality: string;
  teaching_hint: string;
  score_impact: string;
}

interface SubTrace {
  sub_dimension: string;
  sub_dimension_name: string;
  indicator: string;
  why_this_matters: string;
  score: number;
  correct: number;
  total: number;
  problems: ProblemDetail[];
}

interface DimTrace {
  dimension: string;
  dimension_name: string;
  score: number;
  level: string;
  level_name: string;
  correct: number;
  total: number;
  sub_traces: SubTrace[];
}

interface EvaluationTraceProps {
  data: {
    child_name?: string;
    age_display?: string;
    worksheet_type?: string;
    total_problems?: number;
    total_correct?: number;
    dimensions?: DimTrace[];
  } | null;
  loading?: boolean;
}

const dimColors: Record<string, string> = {
  counting: "border-l-green-500 bg-green-50",
  addition_sub: "border-l-amber-500 bg-amber-50",
  shapes_space: "border-l-blue-500 bg-blue-50",
  patterns: "border-l-purple-500 bg-purple-50",
};

const dimLabels: Record<string, string> = {
  counting: "数概念与运算",
  addition_sub: "数运算能力",
  shapes_space: "图形与空间",
  patterns: "集合与模式",
};

export function EvaluationTrace({ data, loading }: EvaluationTraceProps) {
  const [expandedDim, setExpandedDim] = useState<string | null>(null);
  const [expandedSub, setExpandedSub] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="animate-pulse space-y-4">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-24 bg-slate-100 rounded-xl" />
        ))}
      </div>
    );
  }

  if (!data || !data.dimensions || data.dimensions.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        <div className="text-4xl mb-3">📊</div>
        <p className="text-sm">暂无评估过程数据</p>
        <p className="text-xs mt-1">完成一次操作单分析后，这里将展示AI的评估推理过程</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary header */}
      <div className="bg-gradient-to-r from-sky-50 to-indigo-50 rounded-xl p-4 border border-sky-100">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-slate-800">
              📊 评估过程追溯
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {data.child_name || "幼儿"} · {data.age_display || ""} ·{" "}
              {data.total_problems || 0}题 · 正确{data.total_correct || 0}题
            </p>
          </div>
        </div>
      </div>

      {/* Per-dimension traces */}
      {data.dimensions.map((dim) => (
        <div key={dim.dimension} className="border rounded-xl overflow-hidden">
          {/* Dimension header */}
          <button
            onClick={() =>
              setExpandedDim(expandedDim === dim.dimension ? null : dim.dimension)
            }
            className="w-full flex items-center justify-between px-4 py-3 bg-white hover:bg-slate-50 transition-colors"
          >
            <div className="flex items-center gap-3">
              <span
                className={`w-10 h-10 rounded-full flex items-center justify-center text-lg ${
                  dim.level === "L4" ? "bg-yellow-100" :
                  dim.level === "L3" ? "bg-green-100" :
                  dim.level === "L2" ? "bg-amber-100" : "bg-red-100"
                }`}
              >
                {dim.level === "L4" ? "⭐" :
                 dim.level === "L3" ? "🌳" :
                 dim.level === "L2" ? "🌿" : "🌱"}
              </span>
              <div className="text-left">
                <div className="font-semibold text-slate-800">
                  {dimLabels[dim.dimension] || dim.dimension_name}
                </div>
                <div className="text-xs text-slate-500">
                  {dim.correct}/{dim.total}题正确 · {dim.level_name} · {dim.score}%
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* Mini progress bar */}
              <div className="w-20 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${
                    dim.score >= 71 ? "bg-green-500" :
                    dim.score >= 41 ? "bg-amber-500" : "bg-red-400"
                  }`}
                  style={{ width: `${dim.score}%` }}
                />
              </div>
              <span className="text-slate-400 text-sm">
                {expandedDim === dim.dimension ? "▾" : "▸"}
              </span>
            </div>
          </button>

          {/* Expanded sub-traces */}
          {expandedDim === dim.dimension && (
            <div className="border-t bg-slate-50/50 p-3 space-y-2">
              {dim.sub_traces.map((st) => (
                <div
                  key={st.sub_dimension}
                  className="bg-white rounded-lg border shadow-sm"
                >
                  {/* Sub-dim header */}
                  <button
                    onClick={() =>
                      setExpandedSub(
                        expandedSub === `${dim.dimension}-${st.sub_dimension}`
                          ? null
                          : `${dim.dimension}-${st.sub_dimension}`
                      )
                    }
                    className="w-full flex items-center justify-between px-3 py-2 hover:bg-slate-50 transition-colors"
                  >
                    <div className="flex items-center gap-2 text-left">
                      <span
                        className={`w-2 h-2 rounded-full ${
                          st.score >= 71 ? "bg-green-500" :
                          st.score >= 41 ? "bg-amber-500" : "bg-red-400"
                        }`}
                      />
                      <span className="text-sm font-medium text-slate-700">
                        {st.sub_dimension_name}
                      </span>
                      <span className="text-xs text-slate-400">
                        {st.correct}/{st.total} · {st.score}%
                      </span>
                    </div>
                    <span className="text-xs text-slate-400">
                      {st.indicator ? "📋" : ""} {expandedSub === `${dim.dimension}-${st.sub_dimension}` ? "▾" : "▸"}
                    </span>
                  </button>

                  {/* Expanded problem details */}
                  {expandedSub === `${dim.dimension}-${st.sub_dimension}` && (
                    <div className="border-t px-3 py-2 space-y-2">
                      {/* PCK indicator */}
                      {st.indicator && (
                        <div className="bg-blue-50 rounded-lg p-2 text-xs">
                          <span className="font-semibold text-blue-700">📋 PCK指标：</span>
                          <span className="text-blue-800">{st.indicator}</span>
                          {st.why_this_matters && (
                            <p className="text-blue-600 mt-0.5">
                              💡 {st.why_this_matters}
                            </p>
                          )}
                        </div>
                      )}

                      {/* Per-problem details */}
                      {st.problems.map((p) => (
                        <div
                          key={p.problem_id}
                          className={`border-l-2 pl-3 py-1.5 ${
                            p.is_correct
                              ? "border-l-green-400"
                              : "border-l-red-400"
                          }`}
                        >
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-mono text-slate-500">
                                  {p.problem_id}
                                </span>
                                <span className="text-xs bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">
                                  {p.type_description}
                                </span>
                                {p.is_correct ? (
                                  <span className="text-green-500 text-xs font-bold">✓</span>
                                ) : (
                                  <span className="text-red-500 text-xs font-bold">✗</span>
                                )}
                              </div>
                              <div className="text-sm mt-1">
                                幼儿答案：<span className={p.is_correct ? "text-green-700 font-medium" : "text-red-600 font-medium"}>{p.child_answer}</span>
                                {!p.is_correct && (
                                  <span className="text-slate-400 text-xs ml-1">
                                    （标准：{p.correct_answer}）
                                  </span>
                                )}
                              </div>
                              <p className="text-xs text-slate-500 mt-0.5">
                                🔍 证据：{p.evidence}
                              </p>
                              {p.teaching_hint && (
                                <p className="text-xs text-amber-600 mt-0.5">
                                  💡 教学建议：{p.teaching_hint}
                                </p>
                              )}
                            </div>
                            <span
                              className={`text-xs font-semibold px-1.5 py-0.5 rounded ${
                                p.is_correct
                                  ? "bg-green-100 text-green-700"
                                  : "bg-red-100 text-red-600"
                              }`}
                            >
                              {p.score_impact}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
