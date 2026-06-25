"use client";

import { useState, useEffect, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import Link from "next/link";

interface ReportEntry {
  report_id: number;
  type: string;
  child_name: string;
  generated_at: string;
}

interface ChildRecord {
  id: number;
  name: string;
  age_group: string;
}

export default function ReportsPage() {
  const [children, setChildren] = useState<ChildRecord[]>([]);
  const [selectedChild, setSelectedChild] = useState<string>("");
  const [reports, setReports] = useState<ReportEntry[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchChildren = useCallback(async () => {
    try {
      const { api } = await import("@/lib/api-client");
      const data = await api.children.list();
      setChildren(data.children || []);
      if (data.children?.length > 0 && !selectedChild) {
        setSelectedChild(data.children[0].name);
      }
    } catch {
      toast.error("加载幼儿列表失败");
    }
  }, [selectedChild]);

  const fetchReports = useCallback(async (childName: string) => {
    if (!childName) return;
    setLoading(true);
    try {
      const { api } = await import("@/lib/api-client");
      const data = await api.reports.getHistory(childName);
      setReports(data.reports || []);
    } catch {
      setReports([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchChildren();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (selectedChild) {
      fetchReports(selectedChild);
    }
  }, [selectedChild, fetchReports]);

  return (
    <div className="flex-1 p-6 max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">📊 报告中心</h1>
          <p className="text-sm text-slate-500 mt-1">查看和管理所有分析报告</p>
        </div>
      </div>

      {/* Child selector */}
      <Card className="p-4">
        <div className="flex items-center gap-4">
          <label className="text-sm font-medium text-slate-600">选择幼儿：</label>
          <select
            value={selectedChild}
            onChange={(e) => setSelectedChild(e.target.value)}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm flex-1"
          >
            {children.map((c) => (
              <option key={c.id} value={c.name}>
                👶 {c.name} ({c.age_group === "small" ? "小班" : c.age_group === "middle" ? "中班" : "大班"})
              </option>
            ))}
          </select>
        </div>
      </Card>

      {/* Loading */}
      {loading && (
        <div className="flex justify-center py-8">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {/* Reports list */}
      {!loading && reports.length === 0 && (
        <Card className="p-12 text-center">
          <div className="text-4xl mb-3">📋</div>
          <h3 className="font-semibold text-slate-700 mb-2">暂无报告</h3>
          <p className="text-sm text-slate-500 mb-4">
            {selectedChild ? `${selectedChild} 还没有分析报告` : "请先选择幼儿"}
          </p>
          <Link
            href="/dashboard/analyze"
            className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm hover:bg-indigo-700"
          >
            📸 开始分析
          </Link>
        </Card>
      )}

      {!loading && reports.length > 0 && (
        <div className="space-y-3">
          {reports.map((r) => (
            <Card key={r.report_id} className="p-4 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="text-2xl">
                    {r.type === "teacher" ? "📝" : "💚"}
                  </div>
                  <div>
                    <h3 className="font-medium text-slate-800">
                      {r.type === "teacher" ? "教师报告" : "家长报告"}
                    </h3>
                    <p className="text-xs text-slate-400">
                      {new Date(r.generated_at).toLocaleString("zh-CN")}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge className={r.type === "teacher" ? "bg-indigo-100 text-indigo-700" : "bg-green-100 text-green-700"}>
                    {r.type === "teacher" ? "教师版" : "家长版"}
                  </Badge>
                  <Link
                    href={`/dashboard/reports/${r.type}/demo`}
                    className="px-3 py-1.5 rounded-lg bg-slate-100 text-slate-600 text-xs hover:bg-slate-200"
                  >
                    查看 →
                  </Link>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Separator />

      {/* Quick links */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link href="/dashboard/reports/teacher/demo">
          <Card className="p-4 hover:shadow-md text-center cursor-pointer border-indigo-100 hover:border-indigo-300">
            <div className="text-2xl mb-2">📝</div>
            <h3 className="font-medium text-slate-700">演示教师报告</h3>
          </Card>
        </Link>
        <Link href="/dashboard/reports/parent/demo">
          <Card className="p-4 hover:shadow-md text-center cursor-pointer border-green-100 hover:border-green-300">
            <div className="text-2xl mb-2">💚</div>
            <h3 className="font-medium text-slate-700">演示家长报告</h3>
          </Card>
        </Link>
        <Link href="/dashboard/analyze">
          <Card className="p-4 hover:shadow-md text-center cursor-pointer border-amber-100 hover:border-amber-300">
            <div className="text-2xl mb-2">📸</div>
            <h3 className="font-medium text-slate-700">上传新操作单</h3>
          </Card>
        </Link>
      </div>
    </div>
  );
}
