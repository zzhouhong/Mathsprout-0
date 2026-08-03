"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import type { ParentReport } from "@/lib/api-client";
import { api } from "@/lib/api-client";

interface ParentReportViewProps {
  report: ParentReport;
  reportId?: number;
}

export function ParentReportView({ report, reportId }: ParentReportViewProps) {
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownloadPdf = async () => {
    if (!reportId || downloading) return;
    setDownloading(true);
    setDownloadError(null);
    try {
      await api.reports.downloadPdf(reportId, "parent");
    } catch (e: unknown) {
      setDownloadError(e instanceof Error ? e.message : "下载失败");
    } finally {
      setDownloading(false);
    }
  };

  return (
    <Card className="p-6" id="parent-report">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="text-xl">💚</span>
          <h2 className="text-lg font-bold text-slate-800">家长报告</h2>
          <Badge className="bg-green-100 text-green-700 text-xs">温暖·鼓励</Badge>
        </div>
        <button
          onClick={reportId ? handleDownloadPdf : () => window.print()}
          disabled={downloading}
          title={reportId ? "下载PDF报告" : "打印当前页面（浏览器打印功能）"}
          className="inline-flex items-center gap-1.5 rounded-lg border border-green-200 bg-green-50 px-3 py-1.5 text-xs font-medium text-green-700 hover:bg-green-100 disabled:opacity-50 transition-colors"
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

      {/* B6: parent memory card — warm, encouraging framing */}
      {report.parent_memory_card && report.parent_memory_card.remembered && (
        <div className="p-4 rounded-xl mb-4 border border-pink-200 bg-gradient-to-br from-pink-50 to-rose-50">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-base">💖</span>
            <h4 className="text-sm font-semibold text-pink-700">萌芽还记得宝宝哦</h4>
            <span className="text-[10px] text-pink-500 bg-white/70 px-2 py-0.5 rounded-full">
              第 {report.parent_memory_card.session_count} 次见面
            </span>
          </div>
          <p className="text-sm text-slate-700 leading-relaxed">
            {report.parent_memory_card.summary}
          </p>
        </div>
      )}

      {/* Overall Summary */}
      <div className="p-4 bg-green-50 rounded-xl mb-4">
        <p className="text-sm text-green-800 leading-relaxed whitespace-pre-line">
          {report.overall_summary}
        </p>
      </div>

      {/* Strengths & Growing Areas */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div className="p-4 bg-emerald-50 rounded-xl">
          <h4 className="text-sm font-semibold text-emerald-700 mb-2">
            🌟 宝宝已经能...
          </h4>
          {report.strengths.length === 0 ? (
            <p className="text-xs text-emerald-600">正在全面成长中</p>
          ) : (
            <ul className="space-y-2">
              {report.strengths.map((s, i) => (
                <li key={i} className="text-sm text-emerald-800">
                  <span className="font-medium">
                    {s.emoji} {s.area}
                  </span>
                  <p className="mt-0.5 text-xs">{s.description}</p>
                  <p className="mt-0.5 text-xs text-emerald-600">
                    💡 {s.parent_observation_tip}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="p-4 bg-teal-50 rounded-xl">
          <h4 className="text-sm font-semibold text-teal-700 mb-2">
            🌱 正在学习...
          </h4>
          {report.growing_areas.length === 0 ? (
            <p className="text-xs text-teal-600">各方面都在稳步发展</p>
          ) : (
            <ul className="space-y-2">
              {report.growing_areas.map((g, i) => (
                <li key={i} className="text-sm text-teal-800">
                  <span className="font-medium">
                    {g.emoji} {g.area}
                  </span>
                  <p className="mt-0.5 text-xs">{g.description}</p>
                  <p className="mt-0.5 text-xs text-teal-600">
                    💡 {g.parent_observation_tip}
                  </p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Family Activities */}
      <div className="p-4 bg-orange-50 rounded-xl mb-4">
        <h4 className="text-sm font-semibold text-orange-700 mb-3">
          🎮 家庭小游戏
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {report.family_activities.map((act, i) => (
            <div
              key={i}
              className="bg-white rounded-lg p-3 border border-orange-200"
            >
              <h5 className="font-medium text-sm text-slate-800">
                {act.title}
              </h5>
              <p className="text-xs text-slate-500 mt-1">
                <span className="font-medium">材料：</span>
                {act.materials}
              </p>
              <p className="text-xs text-slate-500 mt-1">
                <span className="font-medium">玩法：</span>
                {act.steps}
              </p>
              <p className="text-xs text-orange-600 mt-1">✨ {act.why}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Learning Quality Notes */}
      <div className="p-4 bg-yellow-50 rounded-xl mb-4">
        <p className="text-sm text-yellow-800 leading-relaxed whitespace-pre-line">
          {report.learning_quality_notes}
        </p>
      </div>

      {/* Parent Tips */}
      <div className="p-4 bg-pink-50 rounded-xl">
        <p className="text-sm text-pink-800 leading-relaxed whitespace-pre-line">
          {report.parent_tips}
        </p>
      </div>
    </Card>
  );
}
