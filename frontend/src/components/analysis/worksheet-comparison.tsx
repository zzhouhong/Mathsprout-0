"use client";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";

/** Lightweight dimension snapshot for comparison. */
interface DimensionSnapshot {
  dimension: string;
  display_name: string;
  score: number;
  level: string;
  level_name: string;
  level_emoji: string;
  sub_skills?: Array<{ name: string; score: number }>;
  error_patterns?: string[];
}

interface ComparisonProps {
  earlier: {
    label: string;
    date?: string;
    dimensions: DimensionSnapshot[];
  };
  later: {
    label: string;
    date?: string;
    dimensions: DimensionSnapshot[];
  };
  childName?: string;
}

const DIM_KEYS = ["counting", "addition_sub", "shapes_space", "patterns"];

const LEVEL_ORDER: Record<string, number> = {
  L1: 1, L2: 2, L3: 3, L4: 4,
};

function deltaBadge(delta: number) {
  if (delta > 5) return { emoji: "⬆️", color: "text-green-600", bg: "bg-green-50" };
  if (delta > 0) return { emoji: "↗️", color: "text-emerald-500", bg: "bg-emerald-50" };
  if (delta >= -5) return { emoji: "➡️", color: "text-slate-400", bg: "bg-slate-50" };
  return { emoji: "↘️", color: "text-amber-600", bg: "bg-amber-50" };
}

export function WorksheetComparison({
  earlier,
  later,
  childName,
}: ComparisonProps) {
  // Merge dimensions from both snapshots
  const merged = DIM_KEYS.map((dimKey) => {
    const e = earlier.dimensions.find((d) => d.dimension === dimKey);
    const l = later.dimensions.find((d) => d.dimension === dimKey);
    if (!e && !l) return null;
    const delta = (l?.score ?? 0) - (e?.score ?? 0);
    const levelUp =
      e && l
        ? (LEVEL_ORDER[l.level] || 0) > (LEVEL_ORDER[e.level] || 0)
        : false;
    const levelDown =
      e && l
        ? (LEVEL_ORDER[l.level] || 0) < (LEVEL_ORDER[e.level] || 0)
        : false;
    return { dimKey, earlier: e, later: l, delta, levelUp, levelDown };
  }).filter(Boolean) as Array<{
    dimKey: string;
    earlier: DimensionSnapshot | undefined;
    later: DimensionSnapshot | undefined;
    delta: number;
    levelUp: boolean;
    levelDown: boolean;
  }>;

  return (
    <Card className="p-6">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">🔍</span>
        <h2 className="text-lg font-bold text-slate-800">
          {childName ? `${childName} 的` : ""}操作单对比
        </h2>
      </div>
      <Separator className="mb-4" />

      {/* Two-column header */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        <div className="text-center p-3 bg-slate-50 rounded-lg">
          <p className="text-xs text-slate-400">📄 之前</p>
          <p className="font-medium text-slate-700 text-sm">{earlier.label}</p>
          {earlier.date && (
            <p className="text-xs text-slate-400">{earlier.date}</p>
          )}
        </div>
        <div className="text-center p-3 bg-indigo-50 rounded-lg">
          <p className="text-xs text-indigo-400">📄 最近</p>
          <p className="font-medium text-indigo-700 text-sm">{later.label}</p>
          {later.date && (
            <p className="text-xs text-indigo-400">{later.date}</p>
          )}
        </div>
      </div>

      {/* Per-dimension comparison rows */}
      <div className="space-y-3">
        {merged.map(({ dimKey, earlier: e, later: l, delta, levelUp, levelDown }) => {
          const badge = deltaBadge(delta);
          const displayName = l?.display_name || e?.display_name || dimKey;

          return (
            <div
              key={dimKey}
              className="border border-slate-200 rounded-xl p-4 hover:border-indigo-200 transition-colors"
            >
              {/* Dimension header */}
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-slate-700 text-sm">
                  {displayName}
                </span>
                <div className="flex items-center gap-2">
                  {levelUp && (
                    <Badge className="bg-green-100 text-green-700 text-xs">
                      ⬆️ 升级
                    </Badge>
                  )}
                  {levelDown && (
                    <Badge className="bg-amber-100 text-amber-700 text-xs">
                      ⚠️ 下降
                    </Badge>
                  )}
                  <span
                    className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full ${badge.bg} ${badge.color}`}
                  >
                    {badge.emoji}
                    {delta > 0 ? "+" : ""}
                    {delta.toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Two-column scores */}
              <div className="grid grid-cols-2 gap-4">
                {/* Earlier */}
                <div className="p-2 bg-slate-50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-slate-600">
                    {e ? `${e.score.toFixed(0)}%` : "—"}
                  </p>
                  <p className="text-xs text-slate-400">
                    {e ? `${e.level_emoji} ${e.level_name}` : "无数据"}
                  </p>
                </div>
                {/* Later */}
                <div className="p-2 bg-indigo-50 rounded-lg text-center">
                  <p className="text-2xl font-bold text-indigo-600">
                    {l ? `${l.score.toFixed(0)}%` : "—"}
                  </p>
                  <p className="text-xs text-indigo-400">
                    {l ? `${l.level_emoji} ${l.level_name}` : "无数据"}
                  </p>
                </div>
              </div>

              {/* Sub-skill changes */}
              {e?.sub_skills && l?.sub_skills && (
                <div className="mt-3 pt-3 border-t border-slate-100">
                  <p className="text-xs text-slate-400 mb-1">技能变化</p>
                  <div className="flex flex-wrap gap-1.5">
                    {l.sub_skills.map((sk) => {
                      const prev = e.sub_skills?.find(
                        (ps) => ps.name === sk.name
                      );
                      const skDelta = prev ? sk.score - prev.score : 0;
                      const improved = skDelta > 3;
                      const declined = skDelta < -3;
                      return (
                        <span
                          key={sk.name}
                          className={`inline-flex items-center gap-0.5 text-[10px] px-1.5 py-0.5 rounded ${
                            improved
                              ? "bg-green-50 text-green-700"
                              : declined
                              ? "bg-amber-50 text-amber-700"
                              : "bg-slate-100 text-slate-500"
                          }`}
                        >
                          {sk.name}
                          {skDelta !== 0 && (
                            <span className="opacity-70">
                              {skDelta > 0 ? "+" : ""}
                              {skDelta.toFixed(0)}
                            </span>
                          )}
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Error pattern change */}
              {e?.error_patterns && l?.error_patterns && (
                <div className="mt-2">
                  {e.error_patterns.length > 0 && l.error_patterns.length === 0 && (
                    <p className="text-xs text-green-600">
                      ✅ 之前的错误模式已消除：{e.error_patterns.join("、")}
                    </p>
                  )}
                  {l.error_patterns.length > 0 && (
                    <p className="text-xs text-amber-600">
                      ⚠️ 仍需关注：{l.error_patterns.join("、")}
                    </p>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
