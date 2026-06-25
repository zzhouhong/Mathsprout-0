"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { AssessmentResult, DimensionProblemGroup } from "@/lib/api-client";

const LEVEL_COLORS: Record<string, string> = {
  L1: "bg-red-100 text-red-700 border-red-200",
  L2: "bg-amber-100 text-amber-700 border-amber-200",
  L3: "bg-green-100 text-green-700 border-green-200",
  L4: "bg-indigo-100 text-indigo-700 border-indigo-200",
};

const DIMENSION_ICONS: Record<string, string> = {
  counting: "🔢",
  addition_sub: "➕",
  shapes_space: "🔺",
  patterns: "🔮",
};

interface AssessmentOverviewProps {
  assessment: AssessmentResult;
}

export function AssessmentOverview({ assessment }: AssessmentOverviewProps) {
  const [expandedDim, setExpandedDim] = useState<string | null>(null);

  const dimProblems = assessment.dimension_problems || {};

  const toggleExpand = (dim: string) => {
    setExpandedDim((prev) => (prev === dim ? null : dim));
  };

  return (
    <Card className="p-6">
      <h2 className="text-lg font-bold text-slate-800 mb-4">
        📊 {assessment.child_name} · {assessment.age_display} · 能力评估
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {assessment.assessment.map((dim) => {
          const dimGroup: DimensionProblemGroup | undefined = dimProblems[dim.dimension];
          const isExpanded = expandedDim === dim.dimension;

          return (
            <div key={dim.dimension}>
              <div
                onClick={() => toggleExpand(dim.dimension)}
                className={`bg-slate-50 rounded-xl p-4 border-2 transition-colors cursor-pointer hover:border-indigo-300 ${
                  isExpanded ? "border-indigo-400 shadow-md" : "border-slate-200"
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-slate-600">
                    {DIMENSION_ICONS[dim.dimension] || "📋"} {dim.display_name}
                  </span>
                  <Badge
                    className={`text-xs ${LEVEL_COLORS[dim.level] || "bg-slate-100"}`}
                  >
                    {dim.level_emoji} {dim.level_name}
                  </Badge>
                </div>
                <div className="text-2xl font-bold text-slate-800">
                  {dim.score}%
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  {dim.score_details.correct}/{dim.score_details.total} 题正确
                  {dimGroup && (
                    <span className="text-indigo-500 ml-1">· 点击查看详情</span>
                  )}
                </p>
                {dim.error_patterns.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {dim.error_patterns.map((err, i) => (
                      <span
                        key={i}
                        className="block text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded"
                      >
                        ⚠️ {err}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* ── Expanded: problem-level detail + dimension analysis ── */}
              {isExpanded && dimGroup && (
                <div className="mt-2 p-4 bg-white rounded-xl border-2 border-indigo-200 shadow-sm space-y-3">
                  {/* Problem list */}
                  <div>
                    <h5 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                      📝 该维度题目明细
                    </h5>
                    <div className="space-y-1.5">
                      {dimGroup.problems.map((p) => (
                        <div
                          key={p.id}
                          className={`flex items-center justify-between rounded-lg px-3 py-2 text-sm ${
                            p.is_correct
                              ? "bg-emerald-50 border border-emerald-100"
                              : "bg-red-50 border border-red-100"
                          }`}
                        >
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-mono text-slate-400">
                              {p.id}
                            </span>
                            <span className="text-xs bg-slate-100 px-1.5 py-0.5 rounded text-slate-600">
                              {p.type_name}
                            </span>
                            <span className="font-medium text-slate-700">
                              答: {p.child_answer}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 text-xs">
                            {!p.is_correct && (
                              <span className="text-red-500">
                                正确: {p.correct_answer}
                              </span>
                            )}
                            <Badge
                              className={
                                p.is_correct
                                  ? "bg-emerald-100 text-emerald-700"
                                  : "bg-red-100 text-red-700"
                              }
                            >
                              {p.is_correct ? "✓" : "✗"}
                            </Badge>
                          </div>
                        </div>
                      ))}
                    </div>
                    <p className="text-xs text-slate-400 mt-2">
                      共 {dimGroup.total_count} 题 · 正确 {dimGroup.correct_count} 题 · 得分 {dimGroup.score}%
                    </p>
                  </div>

                  {/* Dimension-specific PCK analysis */}
                  {dimGroup.dimension_analysis && (
                    <div className="p-3 bg-indigo-50 rounded-lg border border-indigo-100">
                      <h5 className="text-xs font-semibold text-indigo-600 mb-1">
                        🧠 {dim.display_name}维度分析
                      </h5>
                      <p className="text-sm text-indigo-800 leading-relaxed">
                        {dimGroup.dimension_analysis}
                      </p>
                    </div>
                  )}

                  {/* PCK reasoning chain summary */}
                  {dim.reasoning_chain && (
                    <div className="p-3 bg-slate-50 rounded-lg border border-slate-200">
                      <h5 className="text-xs font-semibold text-slate-500 mb-1">
                        🔍 PCK推理链
                      </h5>
                      <p className="text-xs text-slate-600">
                        {dim.reasoning_chain.summary}
                      </p>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Overall summary */}
      <div className="mt-4 p-4 bg-blue-50 rounded-xl border border-blue-100">
        <p className="text-sm text-blue-800 leading-relaxed">
          {assessment.overall_summary}
        </p>
      </div>

      {/* PCK observation */}
      {assessment.observations?.overall_pck_notes && (
        <div className="mt-3 p-3 bg-purple-50 rounded-xl border border-purple-100">
          <span className="text-xs font-medium text-purple-600">
            🧠 PCK分析：
          </span>
          <p className="text-sm text-purple-800 mt-1">
            {assessment.observations.overall_pck_notes}
          </p>
        </div>
      )}
    </Card>
  );
}
