"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { TeacherReport } from "@/lib/api-client";
import { api } from "@/lib/api-client";
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
        {reportId && (
          <button
            onClick={handleDownloadPdf}
            disabled={downloading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-1.5 text-xs font-medium text-indigo-700 hover:bg-indigo-100 disabled:opacity-50 transition-colors"
          >
            {downloading ? (
              <>⏳ 生成中...</>
            ) : (
              <>📥 导出PDF</>
            )}
          </button>
        )}
      </div>
      {downloadError && (
        <p className="text-xs text-red-500 mb-2">⚠️ {downloadError}</p>
      )}
      <Separator className="mb-4" />

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

      {/* Teaching Suggestions */}
      {report.teaching_suggestions && Object.keys(report.teaching_suggestions).length > 0 && (
        <div className="p-4 bg-emerald-50 rounded-xl mb-4">
          <h4 className="text-sm font-semibold text-emerald-700 mb-2">
            💡 教学建议
          </h4>
          <div className="space-y-2">
            {Object.entries(report.teaching_suggestions).map(([key, suggestion]) => {
              const s = suggestion as Record<string, unknown>;
              return (
                <div key={key} className="text-sm text-emerald-800">
                  <span className="font-medium">{key}</span>
                  {s.current_stage && (
                    <span className="text-xs text-emerald-600 ml-2">
                      ({s.level} · {s.current_stage as string})
                    </span>
                  )}
                  {s.recommendations && (
                    <p className="text-xs mt-0.5">{s.recommendations as string}</p>
                  )}
                </div>
              );
            })}
          </div>
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

      {/* Radar chart placeholder */}
      {report.radar_chart_data && (
        <div className="p-4 bg-slate-50 rounded-xl">
          <h4 className="text-sm font-semibold text-slate-700 mb-2">
            📊 能力雷达图
          </h4>
          <div className="text-xs text-slate-500">
            雷达图数据已生成（{report.dimensions.length} 个维度）
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
