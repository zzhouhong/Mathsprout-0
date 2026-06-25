"use client";

import { useState, useEffect, useCallback } from "react";
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
}

interface ChildRecord {
  id: number;
  name: string;
  age_group: string;
}

const DIM_COLORS: Record<string, string> = {
  counting: "#6366f1",
  addition_sub: "#f59e0b",
  shapes_space: "#10b981",
  patterns: "#ec4899",
};

export default function TrackingPage() {
  const [children, setChildren] = useState<ChildRecord[]>([]);
  const [selectedChild, setSelectedChild] = useState<ChildRecord | null>(null);
  const [growthData, setGrowthData] = useState<GrowthData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchChildren = useCallback(async () => {
    try {
      const { api } = await import("@/lib/api-client");
      const data = await api.children.list();
      setChildren(data.children || []);
      if (data.children?.length > 0 && !selectedChild) {
        setSelectedChild(data.children[0]);
      }
    } catch {
      toast.error("加载幼儿列表失败");
    }
  }, [selectedChild]);

  const fetchGrowth = useCallback(async (child: ChildRecord) => {
    setLoading(true);
    try {
      const { api } = await import("@/lib/api-client");
      const data = await api.tracking.demoTrajectory(child.age_group, child.name);
      setGrowthData(data);
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
                        trajectory.trend === "improving" ? "bg-green-100 text-green-700" :
                        trajectory.trend === "declining" ? "bg-red-100 text-red-700" :
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
