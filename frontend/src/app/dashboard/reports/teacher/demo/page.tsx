"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { TeacherReportView } from "@/components/analysis";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import type { TeacherReport } from "@/lib/api-client";

type AgeGroup = "small" | "middle" | "large";

const AGE_GROUPS: Record<AgeGroup, string> = {
  small: "小班（3-4岁）",
  middle: "中班（4-5岁）",
  large: "大班（5-6岁）",
};

export default function TeacherReportDemo() {
  const [report, setReport] = useState<TeacherReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [ageGroup, setAgeGroup] = useState<AgeGroup>("middle");
  const [childName, setChildName] = useState("小明");

  const loadReport = useCallback(async () => {
    setLoading(true);
    try {
      const { api } = await import("@/lib/api-client");
      const data = await api.reports.demoTeacher(ageGroup, childName);
      setReport(data);
    } catch (err) {
      const message = err instanceof Error ? err.message : "加载失败";
      toast.error(message);
    } finally {
      setLoading(false);
    }
  }, [ageGroup, childName]);

  useEffect(() => {
    loadReport();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="flex-1 p-6 max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 text-sm text-slate-400 mb-1">
            <Link href="/dashboard" className="hover:text-indigo-600">
              教师工作台
            </Link>
            <span>/</span>
            <span className="text-slate-600">教师报告（演示）</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-800">📝 教师报告（演示）</h1>
          <p className="text-sm text-slate-500 mt-1">
            基于 PCK 框架的专业教学分析报告
          </p>
        </div>
        <Badge className="bg-amber-100 text-amber-700">演示数据</Badge>
      </div>

      {/* Settings */}
      <Card className="p-4">
        <div className="flex flex-wrap items-end gap-4">
          <div>
            <label className="text-xs font-medium text-slate-500 block mb-1">
              幼儿姓名
            </label>
            <input
              type="text"
              value={childName}
              onChange={(e) => setChildName(e.target.value)}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm w-32"
            />
          </div>
          <div>
            <label className="text-xs font-medium text-slate-500 block mb-1">
              年龄段
            </label>
            <select
              value={ageGroup}
              onChange={(e) => setAgeGroup(e.target.value as AgeGroup)}
              className="px-3 py-2 border border-slate-300 rounded-lg text-sm"
            >
              {Object.entries(AGE_GROUPS).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={loadReport}
            disabled={loading}
            className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? "加载中..." : "🔄 刷新报告"}
          </button>
        </div>
      </Card>

      {/* Loading */}
      {loading && (
        <Card className="p-12 text-center">
          <div className="animate-spin text-4xl mb-3">⏳</div>
          <p className="text-slate-500">正在生成教师报告...</p>
        </Card>
      )}

      {/* Report */}
      {report && !loading && <TeacherReportView report={report} />}

      {/* Footer */}
      <div className="text-center pb-8">
        <Separator className="mb-4" />
        <div className="flex justify-center gap-4">
          <Link
            href="/dashboard/reports/parent/demo"
            className="text-sm text-indigo-600 hover:text-indigo-800"
          >
            💚 查看演示家长报告
          </Link>
          <Link
            href="/dashboard/assessment"
            className="text-sm text-indigo-600 hover:text-indigo-800"
          >
            📸 上传操作单分析
          </Link>
          <Link
            href="/dashboard"
            className="text-sm text-slate-400 hover:text-slate-600"
          >
            ← 返回工作台
          </Link>
        </div>
      </div>
    </div>
  );
}
