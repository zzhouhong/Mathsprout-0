/**
 * 家长报告 — 全屏展示页（比赛视频用）
 */
"use client";

import { useEffect, useState } from "react";
import { ParentReportView } from "@/components/analysis";
import { api, type ParentReport } from "@/lib/api-client";

export default function ParentReportPage() {
  const [report, setReport] = useState<ParentReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const ageGroup = params.get("age_group") || "middle";
    const childName = params.get("child_name") || "小明";

    api.reports
      .demoParent(ageGroup, childName)
      .then(setReport)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#FFFDF5" }}>
        <div className="text-center space-y-4">
          <div className="animate-spin text-4xl">⏳</div>
          <p className="text-slate-500">加载报告中...</p>
        </div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: "#FFFDF5" }}>
        <p className="text-slate-500">报告加载失败，请返回重试</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-8 px-4 max-w-4xl mx-auto" style={{ background: "#FFFDF5" }}>
      <ParentReportView report={report} reportId={report.report_id} />
    </div>
  );
}
