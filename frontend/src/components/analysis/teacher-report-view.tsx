"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { TeacherReport } from "@/lib/api-client";
import { api } from "@/lib/api-client";
import { PckRadarChart } from "@/components/learning";
import { AnnotationPanel } from "./annotation-panel";

interface TeacherReportViewProps {
  report: TeacherReport;
  reportId?: number;
}

export function TeacherReportView({ report, reportId }: TeacherReportViewProps) {
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownloadPdf = async () => {
    if (!reportId || downloading) return;
    setDownloading(true);
    setDownloadError(null);
    try {
      await api.reports.downloadPdf(reportId, "teacher");
    } catch (e: unknown) {
      setDownloadError(e instanceof Error ? e.message : "下载失败");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Card className="p-6" id="teacher-report">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xl">📝</span>
          <h2 className="text-lg font-bold text-slate-800">教师报告</h2>
          <Badge className="bg-indigo-100 text-indigo-700 text-xs">
            PCK框架分析
          </Badge>
        </div>
        <button
          onClick={reportId ? handleDownloadPdf : () => window.print()}
          disabled={downloading}
          title={reportId ? "下载PDF报告" : "打印当前页面（浏览器打印功能）"}
          className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-100 disabled:opacity-50 transition-colors"
        >
          {downloading ? (
            <>⏳ 生成中...</>
          ) : reportId ? (
            <>📥 导出PDF</>
          ) : (
            <>🖨️ 打印报告</>
          )}
        </button>
      </div>
      {downloadError && (
        <p className="text-xs text-red-500 mb-2">⚠️ {downloadError}</p>
      )}
      <Separator className="mb-4" />

      {/* B6: "🧠 我记得这个孩子" — memory card from prior assessments */}
      {report.child_memory_card && report.child_memory_card.remembered && (
        <div className="p-4 rounded-xl mb-4 border border-purple-200 bg-gradient-to-br from-purple-50 to-fuchsia-50">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-base">🧠</span>
            <h4 className="text-sm font-semibold text-purple-700">我记得这个孩子</h4>
            <Badge className="bg-purple-100 text-purple-700 text-[10px]">
              第 {report.child_memory_card.session_count} 次评估 · {report.child_memory_card.last_seen}
            </Badge>
          </div>
          <p className="text-sm text-slate-700 font-medium leading-relaxed mb-3">
            {report.child_memory_card.summary}
          </p>
          {(report.child_memory_card.improving.length > 0 ||
            report.child_memory_card.still_struggling.length > 0) && (
            <div className="space-y-2">
              {report.child_memory_card.improving.map((i) => (
                <div key={i.dimension} className="text-xs bg-white/60 rounded-lg px-3 py-2">
                  <span className="font-semibold text-emerald-700">📈 进步</span>
                  <span className="text-slate-700"> {i.display_name}：</span>
                  <span className="text-slate-600">{Math.round(i.prior_score)}% → {Math.round(i.current_score)}%（+{Math.round(i.delta)}）</span>
                  {i.resolved_errors.length > 0 && (
                    <span className="text-emerald-600"> · 已克服：{i.resolved_errors.join("、")}</span>
                  )}
                </div>
              ))}
              {report.child_memory_card.still_struggling.map((s) => (
                <div key={s.dimension} className="text-xs bg-white/60 rounded-lg px-3 py-2">
                  <span className="font-semibold text-rose-700">⚠️ 仍需关注</span>
                  <span className="text-slate-700"> {s.display_name}：</span>
                  <span className="text-slate-600">{Math.round(s.prior_score)}% → {Math.round(s.current_score)}%（{s.delta >= 0 ? "+" : ""}{Math.round(s.delta)}）</span>
                  {s.persisted_errors.length > 0 && (
                    <span className="text-rose-600"> · 仍出现：{s.persisted_errors.join("、")}</span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Core Experience Targeting — 顶部结论：本操作单指向哪类核心经验 */}
      {report.core_experience_analysis &&
        report.core_experience_analysis.targets?.length > 0 && (
          <div className="p-4 bg-indigo-50 rounded-xl mb-4 border border-indigo-100">
            <h4 className="text-sm font-semibold text-indigo-700 mb-2">
              🎯 核心经验定位
            </h4>
            {report.core_experience_analysis.learning_objective && (
              <p className="text-xs text-slate-500 mb-2 leading-relaxed">
                操作单学习目标（印刷识别）：
                <span className="text-slate-700">
                  「{report.core_experience_analysis.learning_objective}」
                </span>
              </p>
            )}
            <p className="text-sm text-slate-700 font-medium mb-3 leading-relaxed">
              {report.core_experience_analysis.summary}
            </p>
            <div className="space-y-2">
              {report.core_experience_analysis.targets.map((t) => (
                <div
                  key={t.sub_dimension}
                  className="flex flex-wrap items-center gap-2 text-xs bg-white/60 rounded-lg px-3 py-2"
                >
                  <Badge className="bg-indigo-100 text-indigo-700 text-[10px]">
                    {t.dimension_name}
                  </Badge>
                  <span className="font-medium text-slate-700">{t.name}</span>
                  {t.source === "assessed" ? (
                    <span className="text-slate-500">
                      {t.level_emoji} {t.level_name} · {t.score}%（{t.correct}/{t.total}题）
                    </span>
                  ) : (
                    <span className="text-slate-400">◽ 指向未测查（本单未含该题型）</span>
                  )}
                </div>
              ))}
            </div>
            {report.core_experience_analysis.targets.some(
              (t) => t.why_this_matters
            ) && (
              <div className="mt-3 space-y-2">
                {report.core_experience_analysis.targets
                  .filter((t) => t.why_this_matters)
                  .map((t) => (
                    <div key={t.sub_dimension} className="text-xs text-slate-600">
                      <span className="font-medium text-slate-700">【{t.name}】</span>
                      {t.indicator && (
                        <span className="text-slate-500"> 该年龄段期望：{t.indicator}。</span>
                      )}
                      <span> {t.why_this_matters}</span>
                    </div>
                  ))}
              </div>
            )}
          </div>
        )}

      {/* Teacher Follow-up Support — 按核心经验组织的教师后续支持 */}
      {report.core_experience_support &&
        Object.keys(report.core_experience_support).length > 0 && (
          <div className="p-4 bg-emerald-50 rounded-xl mb-4 border border-emerald-100">
            <h4 className="text-sm font-semibold text-emerald-700 mb-2">
              💡 教师后续支持（按核心经验）
            </h4>
            <div className="space-y-3">
              {Object.entries(report.core_experience_support).map(([key, s]) => (
                <div
                  key={key}
                  className="text-sm text-emerald-900 bg-white/60 rounded-lg px-3 py-2"
                >
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span className="font-semibold text-slate-800">
                      【{s.dimension_name}】{key}
                    </span>
                    {s.source === "assessed" && s.level_name && (
                      <span className="text-[10px] text-emerald-600">
                        {s.level_emoji} {s.level_name}
                        {typeof s.score === "number" ? ` · ${s.score}%` : ""}
                      </span>
                    )}
                    {s.source === "pointed" && (
                      <span className="text-[10px] text-slate-400">指向未测查</span>
                    )}
                  </div>
                  {s.strategy && (
                    <p className="text-xs text-slate-600 mb-1 leading-relaxed">
                      <span className="text-emerald-700">▸ 教学策略：</span>
                      {s.strategy}
                    </p>
                  )}
                  {s.observation_points?.length > 0 && (
                    <p className="text-xs text-slate-600 mb-1 leading-relaxed">
                      <span className="text-emerald-700">▸ 观察要点：</span>
                      {s.observation_points.join("；")}
                    </p>
                  )}
                  {s.materials && (
                    <p className="text-xs text-slate-600 leading-relaxed">
                      <span className="text-emerald-700">▸ 区角材料：</span>
                      {s.materials}
                    </p>
                  )}
                  {report.teaching_suggestions?.[s.dimension_name]?.comparison_to_last && (
                    <p className="text-xs text-purple-700 leading-relaxed mt-1">
                      {report.teaching_suggestions[s.dimension_name].comparison_to_last}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

      {/* PCK Analysis */}
      <div className="p-4 bg-slate-50 rounded-xl mb-4">
        <h4 className="text-sm font-semibold text-slate-700 mb-2">
          🧠 PCK发展分析
        </h4>
        <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-line">
          {report.pck_analysis}
        </p>
      </div>

      {/* Error Diagnosis */}
      {report.typical_errors_diagnosis.length > 0 &&
        report.typical_errors_diagnosis[0] !== "未发现明显错误模式" && (
          <div className="p-4 bg-amber-50 rounded-xl mb-4">
            <h4 className="text-sm font-semibold text-amber-700 mb-2">
              ⚠️ 典型错误诊断
            </h4>
            <ul className="space-y-1">
              {report.typical_errors_diagnosis.map((err, i) => (
                <li
                  key={i}
                  className="text-sm text-amber-800 flex items-start gap-2"
                >
                  <span>•</span> {err}
                </li>
              ))}
            </ul>
          </div>
        )}

      {/* Teaching Reflection */}
      {report.teaching_reflection_questions.length > 0 && (
        <div className="p-4 bg-indigo-50 rounded-xl mb-4">
          <h4 className="text-sm font-semibold text-indigo-700 mb-2">
            🤔 教学反思引导
          </h4>
          <ul className="space-y-1">
            {report.teaching_reflection_questions.map((q, i) => (
              <li
                key={i}
                className="text-sm text-indigo-800 flex items-start gap-2"
              >
                <span>{i + 1}.</span> {q}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* PCK Radar Chart — 仅展示本操作单实际涉及的维度 */}
      {report.radar_chart_data &&
        report.dimensions.filter((d) => (d.score_details?.total || 0) > 0)
          .length > 0 && (
          <div className="p-4 bg-slate-50 rounded-xl">
            <h4 className="text-sm font-semibold text-slate-700 mb-2">
              📊 能力雷达图
            </h4>
            <div className="flex justify-center">
              <PckRadarChart
                dimensions={report.dimensions
                  .filter((d) => (d.score_details?.total || 0) > 0)
                  .map((d) => ({
                    key: d.dimension,
                    name: d.display_name,
                    sub_dimensions: (d.sub_dimensions ?? []).map((sd) => ({
                      key: sd.sub_dimension,
                      name: sd.name,
                    })),
                  }))}
                scores={Object.fromEntries(
                  report.dimensions
                    .filter((d) => (d.score_details?.total || 0) > 0)
                    .map((d) => [d.dimension, d.score])
                )}
                baseline={report.radar_chart_data.age_expectation?.data?.[0]}
                baselineLabel={report.radar_chart_data.age_expectation?.label}
                size={320}
              />
            </div>
          </div>
        )}

      {/* Annotation Panel */}
      {reportId && (
        <div className="mt-6">
          <AnnotationPanel reportId={reportId} />
        </div>
      )}
    </Card>
  );
}
