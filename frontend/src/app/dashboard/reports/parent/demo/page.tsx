"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { ParentReportView } from "@/components/analysis";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import type { ParentReport } from "@/lib/api-client";

type AgeGroup = "small" | "middle" | "large";

const AGE_GROUPS: Record<AgeGroup, string> = {
  small: "小班（3-4岁）",
  middle: "中班（4-5岁）",
  large: "大班（5-6岁）",
};

export default function ParentReportDemo() {
  const [report, setReport] = useState<ParentReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [ageGroup, setAgeGroup] = useState<AgeGroup>("middle");
  const [childName, setChildName] = useState("小明");

  const loadReport = useCallback(async () => {
    setLoading(true);
    try {
      const { api } = await import("@/lib/api-client");
      const data = await api.reports.demoParent(ageGroup, childName);
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
            <span className="text-slate-600">家长报告（演示）</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-800">💚 家长报告（演示）</h1>
          <p className="text-sm text-slate-500 mt-1">
            温暖鼓励的家长沟通报告，关注成长过程
          </p>
        </div>
        <Badge className="bg-amber-100 text-amber-700">演示数据</Badge>
      </div>

      {/* Note for teachers */}
      <Card className="p-4 bg-green-50 border-green-200">
        <p className="text-sm text-green-700">
          💡 <span className="font-medium">教师提示：</span>
          这是家长将看到的报告。报告使用成长性语言，避免分数、排名等术语。
          家长报告的核心目的是促进家园共育，而非告知"成绩"。
        </p>
      </Card>

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
            className="px-4 py-2 rounded-lg bg-green-600 text-white text-sm hover:bg-green-700 disabled:opacity-50"
          >
            {loading ? "加载中..." : "🔄 刷新报告"}
          </button>
        </div>
      </Card>

      {/* Loading */}
      {loading && (
        <Card className="p-12 text-center">
          <div className="animate-spin text-4xl mb-3">⏳</div>
          <p className="text-slate-500">正在生成家长报告...</p>
        </Card>
      )}

      {/* Report */}
      {report && !loading && <ParentReportView report={report} />}

      {/* Footer */}
      <div className="text-center pb-8">
        <Separator className="mb-4" />
        <p className="text-xs text-slate-400 mb-4">
          此报告由萌芽数学 Mathsprout 生成 · 基于《学前儿童数学学习与发展核心经验》
          <br />
          每个孩子都有自己独特的成长节奏，无需与其他孩子比较 🌈
        </p>
        <div className="flex justify-center gap-4">
          <Link
            href="/dashboard/reports/teacher/demo"
            className="text-sm text-indigo-600 hover:text-indigo-800"
          >
            📝 查看演示教师报告
          </Link>
          <Link
            href="/dashboard/analyze"
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
