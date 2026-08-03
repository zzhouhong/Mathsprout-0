"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";
import { WorksheetComparison } from "@/components/analysis";

interface TrajectoryPoint {
  x: string;
  y: number;
  level: string;
}

interface Trajectory {
  dimension: string;
  display_name: string;
  has_data: boolean;
  first_score?: number;
  latest_score?: number;
  delta?: number;
  trend?: string;
  trend_emoji?: string;
  trend_text?: string;
  chart_points?: TrajectoryPoint[];
  assessment_count?: number;
}

interface GrowthData {
  child_name: string;
  age_group: string;
  has_data: boolean;
  assessment_count: number;
  trajectories: Trajectory[];
  overall_growth_summary: string;
  error_evolution: ErrorEvolution[];
}

interface ErrorEvolution {
  error: string;
  first_seen: string;
  last_seen: string;
  count: number;
  dates: string[];
  status: "resolved" | "recurring" | "new";
}

interface ChildRecord {
  id: number;
  name: string;
  age_group: string;
}

const DIM_DISPLAY: Record<string, string> = {
  counting: "数概念与数数",
  addition_sub: "加减运算",
  shapes_space: "图形与空间",
  patterns: "集合与模式",
};

const TREND_EMOJI: Record<string, { emoji: string; text: string }> = {
  up: { emoji: "📈", text: "上升" },
  down: { emoji: "📉", text: "下降" },
  stable: { emoji: "➡️", text: "稳定" },
  insufficient_data: { emoji: "•", text: "数据不足" },
};

const DIM_COLORS: Record<string, string> = {
  counting: "#6366f1",
  addition_sub: "#f59e0b",
  shapes_space: "#10b981",
  patterns: "#ec4899",
};

export default function TrackingPage() {
  const searchParams = useSearchParams();
  const [children, setChildren] = useState<ChildRecord[]>([]);
  const [selectedChild, setSelectedChild] = useState<ChildRecord | null>(null);
  const [growthData, setGrowthData] = useState<GrowthData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchChildren = useCallback(async () => {
    try {
      const { api } = await import("@/lib/api-client");
      const data = await api.children.list();
      setChildren(data.children || []);
      if (data.children?.length > 0) {
        // 优先按 URL 的 ?child= id 预选（从成长档案等页面跳转时携带）
        const paramId = searchParams.get("child");
        const matched = paramId
          ? data.children.find((c) => String(c.id) === paramId)
          : null;
        if (!selectedChild) {
          setSelectedChild(matched || data.children[0]);
        }
      }
    } catch {
      toast.error("加载幼儿列表失败");
    }
  }, [selectedChild, searchParams]);

  const fetchGrowth = useCallback(async (child: ChildRecord) => {
    setLoading(true);
    try {
      const { api } = await import("@/lib/api-client");
      const t = await api.dashboard.childTrajectory(child.id);
      // Adapt DB trajectory → GrowthData shape used by the charts below
      const dimOrder = ["counting", "addition_sub", "shapes_space", "patterns"];
      const trajectories: Trajectory[] = dimOrder.map((dim) => {
        const series = t.dimensions[dim] || [];
        const has = series.length > 0;
        const first = series[0];
        const last = series[series.length - 1];
        const trend = t.trends[dim] || "insufficient_data";
        const te = TREND_EMOJI[trend] || TREND_EMOJI.insufficient_data;
        return {
          dimension: dim,
          display_name: DIM_DISPLAY[dim] || dim,
          has_data: has,
          first_score: first?.score,
          latest_score: last?.score,
          delta: has && first && last ? last.score - first.score : undefined,
          trend,
          trend_emoji: te.emoji,
          trend_text: te.text,
          chart_points: series.map((s) => ({ x: s.date || "", y: s.score, level: s.level })),
          assessment_count: series.length,
        };
      });
      const summary = t.assessment_count === 0
        ? "暂无历史评估数据，完成首次分析后可查看成长轨迹。"
        : `共 ${t.assessment_count} 次评估记录，覆盖 ${trajectories.filter((x) => x.has_data).length} 个维度。`;
      setGrowthData({
        child_name: t.child_name,
        age_group: t.age_group,
        has_data: t.assessment_count > 0,
        assessment_count: t.assessment_count,
        trajectories,
        overall_growth_summary: summary,
        error_evolution: t.error_evolution || [],
      });
    } catch {
      toast.error("加载成长轨迹失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchChildren();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (selectedChild) {
      fetchGrowth(selectedChild);
    }
  }, [selectedChild, fetchGrowth]);

  // Simple chart renderer (bar chart for dimension scores)
  const renderChart = (trajectory: Trajectory) => {
    if (!trajectory.has_data || !trajectory.chart_points?.length) {
      return (
        <div className="h-20 flex items-center justify-center text-xs text-slate-400">
          暂无数据
        </div>
      );
    }

    const maxY = 100;
    const color = DIM_COLORS[trajectory.dimension] || "#6366f1";

    return (
      <div className="space-y-1">
        <div className="flex items-end gap-2 h-20 px-2">
          {trajectory.chart_points.map((point, i) => (
            <div
              key={i}
              className="flex-1 flex flex-col items-center justify-end h-full"
              title={`${point.x}: ${point.y}分 (${point.level})`}
            >
              <div
                className="w-full rounded-t transition-all duration-500 min-w-[20px]"
                style={{
                  height: `${(point.y / maxY) * 100}%`,
                  backgroundColor: color,
                  opacity: 0.7 + (i / trajectory.chart_points!.length) * 0.3,
                }}
              />
            </div>
          ))}
        </div>
        <div className="flex justify-between text-[10px] text-slate-400">
          {trajectory.chart_points.map((point, i) => (
            <span key={i} className="truncate">{point.x}</span>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="flex-1 p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">📈 成长轨迹</h1>
          <p className="text-sm text-slate-500 mt-1">追踪幼儿在 4 个数学维度上的长期发展趋势</p>
        </div>
        {children.length > 0 && (
          <select
            value={selectedChild?.id || ""}
            onChange={(e) => {
              const child = children.find((c) => c.id === Number(e.target.value));
              if (child) setSelectedChild(child);
            }}
            className="px-3 py-2 border border-slate-300 rounded-lg text-sm"
          >
            {children.map((c) => (
              <option key={c.id} value={c.id}>
                👶 {c.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {loading && (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {!loading && growthData && !growthData.has_data && (
        <Card className="p-12 text-center">
          <div className="text-4xl mb-3">📈</div>
          <h3 className="font-semibold text-slate-700 mb-2">数据积累中</h3>
          <p className="text-sm text-slate-500">
            完成多次操作单分析后，这里将展示成长曲线。请先上传操作单进行分析。
          </p>
        </Card>
      )}

      {!loading && growthData?.has_data && (
        <div className="space-y-6">
          {/* Summary */}
          <Card className="p-6 bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200">
            <div className="flex items-center gap-4">
              <div className="text-3xl">📈</div>
              <div>
                <h2 className="font-bold text-indigo-800">
                  {growthData.child_name} · {growthData.assessment_count} 次评估
                </h2>
                <p className="text-sm text-indigo-600">{growthData.overall_growth_summary}</p>
              </div>
            </div>
          </Card>

          {/* Per-dimension trajectories */}
          {growthData.trajectories
            .filter((t) => t.has_data)
            .map((trajectory) => (
              <Card key={trajectory.dimension} className="p-5">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-slate-700">
                      {trajectory.display_name}
                    </h3>
                    {trajectory.trend_emoji && (
                      <Badge className={
                        trajectory.trend === "up" ? "bg-green-100 text-green-700" :
                        trajectory.trend === "down" ? "bg-red-100 text-red-700" :
                        "bg-slate-100 text-slate-600"
                      }>
                        {trajectory.trend_emoji} {trajectory.trend_text}
                      </Badge>
                    )}
                  </div>
                  <div className="text-sm">
                    {trajectory.first_score !== undefined && trajectory.latest_score !== undefined && (
                      <span className="text-slate-500">
                        {trajectory.first_score} →{" "}
                        <span className={`font-bold ${
                          (trajectory.delta || 0) > 0 ? "text-green-600" :
                          (trajectory.delta || 0) < 0 ? "text-red-600" : "text-slate-600"
                        }`}>
                          {trajectory.latest_score}
                        </span>
                        {trajectory.delta !== undefined && (
                          <span className="text-xs ml-1">
                            ({trajectory.delta > 0 ? "+" : ""}{trajectory.delta})
                          </span>
                        )}
                      </span>
                    )}
                  </div>
                </div>

                {renderChart(trajectory)}
              </Card>
            ))}
        </div>
      )}

      {/* B7: Error-pattern evolution timeline */}
      {!loading && growthData?.has_data && growthData.error_evolution.length > 0 && (
        <Card className="p-5">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-lg">🔬</span>
            <h3 className="font-semibold text-slate-700">错误模式演变时间线</h3>
          </div>
          <p className="text-xs text-slate-500 mb-4">
            追踪各类错误模式在历次评估中的消退与反复——绿色=已克服，橙色=反复出现，红色=本次新出现。
          </p>
          <div className="space-y-2">
            {growthData.error_evolution.map((e, i) => {
              const palette = e.status === "resolved"
                ? { bg: "bg-emerald-50", border: "border-emerald-200", dot: "bg-emerald-500", label: "已克服", labelColor: "text-emerald-700" }
                : e.status === "recurring"
                ? { bg: "bg-amber-50", border: "border-amber-200", dot: "bg-amber-500", label: "反复出现", labelColor: "text-amber-700" }
                : { bg: "bg-rose-50", border: "border-rose-200", dot: "bg-rose-500", label: "本次新出现", labelColor: "text-rose-700" };
              return (
                <div key={i} className={`flex items-center gap-3 rounded-lg border ${palette.border} ${palette.bg} px-3 py-2`}>
                  <span className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${palette.dot}`} />
                  <span className="text-sm text-slate-700 font-medium flex-1 truncate">{e.error}</span>
                  <span className={`text-[10px] font-semibold ${palette.labelColor}`}>{palette.label}</span>
                  <span className="text-[11px] text-slate-400 flex-shrink-0">
                    {e.first_seen} → {e.last_seen} · {e.count}次
                  </span>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Comparison View */}
      {!loading && growthData?.has_data && growthData.assessment_count >= 2 && (
        <WorksheetComparison
          childName={growthData.child_name}
          earlier={{
            label: "首次评估",
            date: growthData.trajectories[0]?.chart_points?.[0]?.x || "",
            dimensions: growthData.trajectories
              .filter((t) => t.has_data)
              .map((t) => ({
                dimension: t.dimension,
                display_name: t.display_name,
                score: t.chart_points?.[0]?.y ?? 0,
                level: t.chart_points?.[0]?.level ?? "L1",
                level_name:
                  t.chart_points?.[0]?.level === "L4"
                    ? "进阶期"
                    : t.chart_points?.[0]?.level === "L3"
                    ? "熟练期"
                    : t.chart_points?.[0]?.level === "L2"
                    ? "发展期"
                    : "萌芽期",
                level_emoji:
                  t.chart_points?.[0]?.level === "L4"
                    ? "⭐"
                    : t.chart_points?.[0]?.level === "L3"
                    ? "🌳"
                    : t.chart_points?.[0]?.level === "L2"
                    ? "🌿"
                    : "🌱",
                error_patterns: [],
              })),
          }}
          later={{
            label: "最近评估",
            date: growthData.trajectories[0]?.chart_points?.slice(-1)[0]?.x || "",
            dimensions: growthData.trajectories
              .filter((t) => t.has_data)
              .map((t) => {
                const last = t.chart_points?.slice(-1)[0];
                return {
                  dimension: t.dimension,
                  display_name: t.display_name,
                  score: last?.y ?? 0,
                  level: last?.level ?? "L1",
                  level_name:
                    last?.level === "L4"
                      ? "进阶期"
                      : last?.level === "L3"
                      ? "熟练期"
                      : last?.level === "L2"
                      ? "发展期"
                      : "萌芽期",
                  level_emoji:
                    last?.level === "L4"
                      ? "⭐"
                      : last?.level === "L3"
                      ? "🌳"
                      : last?.level === "L2"
                      ? "🌿"
                      : "🌱",
                  error_patterns: [],
                };
              }),
          }}
        />
      )}

      <Separator />

      <p className="text-xs text-slate-400 text-center">
        成长轨迹数据基于历次操作单分析结果，反映幼儿数学能力的长期发展趋势。
        建议每月进行 1-2 次评估以获得更准确的趋势判断。
      </p>
    </div>
  );
}
