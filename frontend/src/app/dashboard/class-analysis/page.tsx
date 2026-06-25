"use client";

import { useState, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

interface HeatmapCell {
  pattern: string;
  count: number;
  child_count: number;
}

interface HeatmapRow {
  dimension: string;
  display_name: string;
  cells: HeatmapCell[];
}

interface ErrorHeatmap {
  dimensions: string[];
  rows: HeatmapRow[];
  max_count: number;
  total_children: number;
}

interface ChildSummary {
  name: string;
  overall_score: number;
  strengths: string[];
  needs_attention: string[];
}

interface ClassData {
  class_name: string;
  child_count: number;
  average_scores: Record<string, number>;
  distribution: Record<string, { L1: number; L2: number; L3: number; L4: number }>;
  children: ChildSummary[];
  overall_summary: string;
  error_heatmap?: ErrorHeatmap;
  common_error_patterns?: Array<{
    pattern: string;
    count: number;
    dimension: string;
    affected_children: string[];
  }>;
}

export default function ClassAnalysisPage() {
  const [classData, setClassData] = useState<ClassData | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchAnalysis = useCallback(async () => {
    setLoading(true);
    try {
      const { api } = await import("@/lib/api-client");
      const demoChildren = [
        { child_name: "小明", age_group: "middle" },
        { child_name: "小红", age_group: "large" },
        { child_name: "小华", age_group: "small" },
      ];

      const data = await api.tracking.classAnalysis(demoChildren as any, "向日葵班");
      setClassData(data as unknown as ClassData);
    } catch (err) {
      toast.error("加载班级分析失败，请确保有足够的评估数据");
    } finally {
      setLoading(false);
    }
  }, []);

  const DIM_NAMES: Record<string, string> = {
    counting: "数数与数量对应",
    addition_sub: "简单加减运算",
    shapes_space: "图形与空间",
    patterns: "模式与规律",
  };

  const LEVEL_COLORS: Record<string, string> = {
    L1: "bg-red-400",
    L2: "bg-amber-400",
    L3: "bg-green-400",
    L4: "bg-indigo-400",
  };

  /** Compute heatmap cell color based on count intensity. */
  function heatColor(count: number, max: number): string {
    if (count === 0) return "bg-slate-50";
    const ratio = count / Math.max(max, 1);
    if (ratio >= 0.8) return "bg-red-500 text-white";
    if (ratio >= 0.6) return "bg-orange-400 text-white";
    if (ratio >= 0.4) return "bg-amber-300 text-amber-900";
    if (ratio >= 0.2) return "bg-yellow-200 text-yellow-900";
    return "bg-slate-100 text-slate-600";
  }

  return (
    <div className="flex-1 p-6 max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-800">🏫 班级分析</h1>
          <p className="text-sm text-slate-500 mt-1">全班幼儿数学能力概览与分布分析</p>
        </div>
        <button
          onClick={fetchAnalysis}
          disabled={loading}
          className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "加载中..." : "🔄 刷新分析"}
        </button>
      </div>

      {!classData && !loading && (
        <Card className="p-12 text-center">
          <div className="text-4xl mb-3">🏫</div>
          <h3 className="font-semibold text-slate-700 mb-2">班级分析</h3>
          <p className="text-sm text-slate-500 mb-4">
            点击"刷新分析"按钮，系统将根据所有幼儿的评估数据生成班级统计报告。
          </p>
          <button
            onClick={fetchAnalysis}
            className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm hover:bg-indigo-700"
          >
            📊 生成班级分析
          </button>
        </Card>
      )}

      {loading && (
        <div className="flex justify-center py-12">
          <div className="w-8 h-8 border-2 border-indigo-600 border-t-transparent rounded-full animate-spin" />
        </div>
      )}

      {classData && (
        <div className="space-y-6">
          {/* Header */}
          <Card className="p-6 bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
            <div className="flex items-center gap-4">
              <div className="text-3xl">🏫</div>
              <div>
                <h2 className="font-bold text-blue-800">{classData.class_name}</h2>
                <p className="text-sm text-blue-600">
                  {classData.child_count} 名幼儿 · {classData.overall_summary}
                </p>
              </div>
            </div>
          </Card>

          {/* Average scores */}
          <Card className="p-6">
            <h3 className="font-semibold text-slate-700 mb-4">📊 各维度平均分</h3>
            <div className="space-y-4">
              {Object.entries(classData.average_scores || {}).map(([dim, score]) => (
                <div key={dim}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-slate-600">{DIM_NAMES[dim] || dim}</span>
                    <span className="font-medium text-slate-700">{score}%</span>
                  </div>
                  <Progress value={score} />
                </div>
              ))}
            </div>
          </Card>

          {/* Level distribution */}
          <Card className="p-6">
            <h3 className="font-semibold text-slate-700 mb-4">👥 发展水平分布</h3>
            <div className="space-y-4">
              {Object.entries(classData.distribution || {}).map(([dim, dist]) => {
                const total = (dist.L1 + dist.L2 + dist.L3 + dist.L4) || 1;
                return (
                  <div key={dim}>
                    <p className="text-sm font-medium text-slate-600 mb-1">
                      {DIM_NAMES[dim] || dim}
                    </p>
                    <div className="flex h-6 rounded-full overflow-hidden">
                      {(["L1", "L2", "L3", "L4"] as const).map((level) => (
                        <div
                          key={level}
                          className={`${LEVEL_COLORS[level]} flex items-center justify-center text-[10px] text-white font-medium`}
                          style={{ width: `${(dist[level] / total) * 100}%` }}
                          title={`${level}: ${dist[level]}人`}
                        >
                          {dist[level] > 0 ? dist[level] : ""}
                        </div>
                      ))}
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
                      <span>🌱 萌芽 L1</span>
                      <span>🌿 发展 L2</span>
                      <span>🌳 熟练 L3</span>
                      <span>⭐ 进阶 L4</span>
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* Error Heatmap */}
          {classData.error_heatmap && classData.error_heatmap.rows.some(r => r.cells.length > 0) && (
            <Card className="p-6">
              <h3 className="font-semibold text-slate-700 mb-2">
                🔥 常见错误模式热力图
              </h3>
              <p className="text-xs text-slate-400 mb-4">
                颜色越深表示出现该错误的人数越多（共 {classData.error_heatmap.total_children} 名幼儿）
              </p>
              <div className="space-y-4">
                {classData.error_heatmap.rows.map((row) => (
                  <div key={row.dimension}>
                    <p className="text-sm font-medium text-slate-600 mb-2">
                      {row.display_name}
                    </p>
                    {row.cells.length === 0 ? (
                      <p className="text-xs text-slate-400 italic pl-2">
                        暂未发现明显错误模式 ✨
                      </p>
                    ) : (
                      <div className="flex flex-wrap gap-2">
                        {row.cells.map((cell, ci) => (
                          <div
                            key={ci}
                            className={`rounded-lg px-3 py-2 text-xs font-medium ${heatColor(
                              cell.count,
                              classData.error_heatmap!.max_count
                            )}`}
                            title={`${cell.pattern}: ${cell.count}/${cell.child_count} 人`}
                          >
                            {cell.pattern.length > 24
                              ? cell.pattern.slice(0, 22) + "…"
                              : cell.pattern}
                            <span className="ml-1.5 opacity-70">{cell.count}人</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Common Error Patterns List */}
          {classData.common_error_patterns && classData.common_error_patterns.length > 0 && (
            <Card className="p-6">
              <h3 className="font-semibold text-slate-700 mb-3">
                ⚠️ 高频错误详情
              </h3>
              <div className="space-y-2">
                {classData.common_error_patterns.map((err, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg"
                  >
                    <span className="text-amber-600 font-bold text-sm mt-0.5">
                      {i + 1}.
                    </span>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-700">{err.pattern}</p>
                      <p className="text-xs text-slate-400 mt-0.5">
                        {err.dimension} · {err.count} 名幼儿
                        {err.affected_children?.length > 0 &&
                          `：${err.affected_children.join("、")}`}
                      </p>
                    </div>
                    <Badge className="bg-amber-100 text-amber-700 text-xs shrink-0">
                      {err.count}人
                    </Badge>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Children summary */}
          <Card className="p-6">
            <h3 className="font-semibold text-slate-700 mb-4">👶 幼儿概览</h3>
            <div className="space-y-3">
              {(classData.children || []).map((child, i) => (
                <div key={i} className="flex items-center gap-4 p-3 bg-slate-50 rounded-xl">
                  <div className="w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-sm">
                    👶
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-slate-700 text-sm">{child.name}</p>
                    <div className="flex gap-2 mt-0.5">
                      {(child.strengths || []).slice(0, 2).map((s, j) => (
                        <Badge key={j} className="bg-green-100 text-green-700 text-[10px]">
                          💪 {s}
                        </Badge>
                      ))}
                      {(child.needs_attention || []).slice(0, 2).map((n, j) => (
                        <Badge key={j} className="bg-amber-100 text-amber-700 text-[10px]">
                          🎯 {n}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="font-bold text-indigo-600 text-lg">
                      {child.overall_score}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}

      <Separator />
      <p className="text-xs text-slate-400 text-center">
        班级分析基于所有幼儿的最新评估数据，帮助教师了解全班整体水平和个别差异。
        建议每学期初、期中、期末各进行一次班级分析。
      </p>
    </div>
  );
}
