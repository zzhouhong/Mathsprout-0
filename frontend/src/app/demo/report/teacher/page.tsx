/**
 * 教师报告 — 全屏展示页（比赛视频用）
 * 通过 URL search params 接收报告数据或加载 demo
 */
"use client";

import { useEffect, useState } from "react";
import { TeacherReportView } from "@/components/analysis";
import { api, type TeacherReport } from "@/lib/api-client";

export default function TeacherReportPage() {
  const [report, setReport] = useState<TeacherReport | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const ageGroup = params.get("age_group") || "middle";
    const childName = params.get("child_name") || "小明";

    api.reports
      .demoTeacher(ageGroup, childName)
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
      <TeacherReportView report={report} reportId={report.report_id} />
    </div>
  );
}
