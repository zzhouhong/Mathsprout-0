"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { api } from "@/lib/api-client";
import Link from "next/link";

const TYPE_LABELS: Record<string, string> = {
  teacher: "📋 教师版",
  parent: "👨‍👩‍👧 家长版",
};

export default function ChildReportsPage() {
  const params = useParams();
  const childId = parseInt(params.id as string);

  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!childId || isNaN(childId)) return;
    api.children
      .reports(childId)
      .then((d) => {
        setData(d);
        setLoading(false);
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : "加载失败");
        setLoading(false);
      });
  }, [childId]);

  if (loading) {
    return (
      <div className="flex-1 p-6 max-w-4xl mx-auto flex items-center justify-center">
        <div className="text-center space-y-3">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-sm text-slate-500">正在加载报告历史...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex-1 p-6 max-w-4xl mx-auto">
        <Card className="p-12 text-center border-red-200 bg-red-50">
          <div className="text-4xl mb-3">⚠️</div>
          <h3 className="font-semibold text-red-700 mb-2">加载失败</h3>
          <p className="text-sm text-red-500">{error}</p>
        </Card>
      </div>
    );
  }

  const child = data?.child;
  const reports = data?.reports || [];

  return (
    <div className="flex-1 p-6 max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Link href="/dashboard/children" className="text-sm text-indigo-600 hover:underline">
              ← 幼儿管理
            </Link>
          </div>
          <h1 className="text-2xl font-bold text-slate-800">
            📊 {child?.name} 的分析报告
          </h1>
          {child && (
            <p className="text-sm text-slate-500 mt-1">
              {child.age_group === "small" ? "小班" : child.age_group === "middle" ? "中班" : "大班"}
              {child.class_name ? ` · ${child.class_name}` : ""}
              {" · "}共 {reports.length} 份报告
            </p>
          )}
        </div>
        <Link
          href={`/dashboard/analyze?child=${encodeURIComponent(child?.name || "")}&age=${child?.age_group || "middle"}`}
          className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          📸 新分析
        </Link>
      </div>

      {/* Reports list */}
      {reports.length === 0 ? (
        <Card className="p-12 text-center">
          <div className="text-4xl mb-3">📭</div>
          <h3 className="font-semibold text-slate-700 mb-2">暂无分析报告</h3>
          <p className="text-sm text-slate-500">
            对该幼儿上传操作单进行分析后，报告将自动出现在这里
          </p>
        </Card>
      ) : (
        <div className="space-y-4">
          {reports.map((r: any) => (
            <Card key={r.report_id} className="p-5 hover:shadow-md transition-shadow">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <Badge className={r.type === "teacher" ? "bg-blue-100 text-blue-700" : "bg-emerald-100 text-emerald-700"}>
                      {TYPE_LABELS[r.type] || r.type}
                    </Badge>
                    <span className="text-xs text-slate-400">
                      {r.generated_at ? new Date(r.generated_at).toLocaleDateString("zh-CN") : ""}
                    </span>
                  </div>
                  <p className="text-sm text-slate-600 line-clamp-2">{r.summary}</p>
                  {r.dimensions && r.dimensions.length > 0 && (
                    <div className="flex gap-2 mt-2">
                      {r.dimensions.map((d: any) => (
                        <span key={d.name} className="text-xs px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">
                          {d.name}: {d.score}分 ({d.level})
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <Link
                  href={`/dashboard/reports/teacher/demo`}
                  className="ml-4 px-3 py-1.5 rounded-lg bg-slate-100 text-slate-600 text-xs font-medium hover:bg-slate-200 transition-colors whitespace-nowrap"
                >
                  查看详情 →
                </Link>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Separator />

      {/* Footer */}
      <div className="p-4 bg-slate-50 rounded-xl border border-slate-200">
        <p className="text-sm text-slate-500">
          💡 <span className="font-medium">提示：</span>
          每次分析操作单时会自动生成教师版和家长版两份报告，刷新和重启不会丢失。
        </p>
      </div>
    </div>
  );
}
