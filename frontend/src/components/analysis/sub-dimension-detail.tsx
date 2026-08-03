"use client";

/**
 * SubDimensionDetail — Reusable sub-dimension score card with PCK indicator reference.
 *
 * Used by:
 * - assessment-overview.tsx (in dimension cards — 13-sub-dimension breakdown)
 * - evaluation-trace.tsx (per-problem trace)
 *
 * Shows: sub-dimension name, score bar (or "本张未考查" badge), PCK indicator,
 * and teaching context. Indicator text comes from the backend (INDICATOR_EXPLANATIONS),
 * so this component no longer depends on a frontend-hardcoded name→indicator map.
 */

export interface SubSkillScore {
  name: string;
  score: number;
  max_score: number;
}

/**
 * SubDimensionScore — the 13-sub-dimension entry produced by the backend
 * (assess() → sub_dimensions). Carries its own indicator text + assessed flag
 * so the UI can render assessed vs. not-assessed-this-time distinctly.
 */
export interface SubDimensionScore {
  sub_dimension: string;
  name: string;
  score: number;
  max_score: number;
  assessed: boolean;
  correct: number;
  total: number;
  indicator?: string;
  why_this_matters?: string;
}

export interface PCKIndicatorRef {
  indicator: string;
  why_this_matters?: string;
  teaching_tips?: string;
}

interface SubDimensionDetailProps {
  /** Sub-dimension / sub-skill display name */
  name: string;
  /** Score (0-100) */
  score: number;
  /** Max score (default 100) */
  maxScore?: number;
  /** Whether this sub-dimension had any problems on this worksheet */
  assessed?: boolean;
  /** PCK indicator reference (legacy: name-keyed lookup) */
  indicator?: PCKIndicatorRef;
  /** Inline indicator text (from backend SubDimensionScore.indicator) */
  indicatorText?: string;
  /** Inline why-this-matters text (from backend) */
  whyThisMatters?: string;
  /** Whether to show the PCK indicator text inline */
  showIndicator?: boolean;
  /** Compact mode: smaller padding, smaller text */
  compact?: boolean;
  /** Children: additional content (e.g., per-problem evidence) */
  children?: React.ReactNode;
}

const SCORE_COLORS = (score: number) => {
  if (score >= 71) return { bar: "bg-green-500", bg: "bg-green-50", text: "text-green-700" };
  if (score >= 41) return { bar: "bg-amber-500", bg: "bg-amber-50", text: "text-amber-700" };
  return { bar: "bg-red-400", bg: "bg-red-50", text: "text-red-600" };
};

export function SubDimensionDetail({
  name,
  score,
  maxScore = 100,
  assessed = true,
  indicator,
  indicatorText,
  whyThisMatters,
  showIndicator = true,
  compact = false,
  children,
}: SubDimensionDetailProps) {
  const colors = SCORE_COLORS(score);
  const pct = maxScore > 0 ? Math.round((score / maxScore) * 100) : 0;

  // Resolve inline indicator text: prefer backend-provided indicatorText,
  // fall back to the legacy indicator object.
  const indicatorLine = indicatorText || indicator?.indicator || "";
  const whyLine = whyThisMatters ?? indicator?.why_this_matters ?? "";
  const hasIndicator = Boolean(indicatorLine);

  if (!assessed) {
    // 未考查 — muted card, no score bar, still shows the PCK indicator so
    // teachers see what this sub-dimension is about.
    return (
      <div className={`rounded-lg border border-dashed border-slate-200 bg-slate-50/60 ${compact ? "p-2" : "p-3"}`}>
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2 min-w-0">
            <span className="w-2 h-2 rounded-full flex-shrink-0 bg-slate-300" />
            <span className={`${compact ? "text-xs" : "text-sm"} font-medium text-slate-500 truncate`}>
              {name}
            </span>
            {hasIndicator && showIndicator && (
              <span className="text-xs text-slate-400 flex-shrink-0" title="有PCK指标参照">
                📋
              </span>
            )}
          </div>
          <span className="text-[10px] font-medium text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded flex-shrink-0">
            本张未考查
          </span>
        </div>
        {hasIndicator && showIndicator && (
          <div className="mt-1.5 text-xs text-slate-500 leading-relaxed">
            <span className="font-semibold text-slate-600">📋 PCK指标：</span>
            <span>{indicatorLine}</span>
          </div>
        )}
        {children && <div className="mt-2 space-y-1.5">{children}</div>}
      </div>
    );
  }

  return (
    <div className={`rounded-lg border shadow-sm ${compact ? "p-2" : "p-3"} bg-white`}>
      {/* Header row: name + score */}
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span
            className={`w-2 h-2 rounded-full flex-shrink-0 ${colors.bar}`}
          />
          <span className={`${compact ? "text-xs" : "text-sm"} font-medium text-slate-700 truncate`}>
            {name}
          </span>
          {hasIndicator && showIndicator && (
            <span className="text-xs text-blue-400 flex-shrink-0" title="有PCK指标参照">
              📋
            </span>
          )}
        </div>
        <span className={`${compact ? "text-xs" : "text-sm"} font-bold ${colors.text} flex-shrink-0`}>
          {score}%
        </span>
      </div>

      {/* Score bar */}
      <div className="mt-1.5 h-1.5 bg-slate-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${colors.bar}`}
          style={{ width: `${Math.max(pct, 2)}%` }}
        />
      </div>

      {/* PCK indicator reference */}
      {hasIndicator && showIndicator && (
        <div className={`mt-2 ${colors.bg} rounded-lg ${compact ? "p-1.5" : "p-2"} text-xs`}>
          <span className="font-semibold text-blue-700">📋 PCK指标：</span>
          <span className="text-blue-800">{indicatorLine}</span>
          {whyLine && (
            <p className="text-blue-600 mt-0.5">
              💡 {whyLine}
            </p>
          )}
        </div>
      )}

      {/* Children (e.g., problem details) */}
      {children && (
        <div className="mt-2 space-y-1.5">
          {children}
        </div>
      )}
    </div>
  );
}

/**
 * SubDimensionDetailList — Renders a list of sub-dimension cards with a title.
 *
 * Two input shapes supported:
 * - subDimensions: SubDimensionScore[] (preferred — backend 13-sub-dimension data,
 *   carries assessed flag + inline indicator text)
 * - subSkills: SubSkillScore[] (legacy — 23-item SUB_SKILLS, needs indicatorMap)
 */
interface SubDimensionDetailListProps {
  subSkills?: SubSkillScore[];
  subDimensions?: SubDimensionScore[];
  /** Optional PCK indicator lookup by sub-skill name (legacy subSkills path) */
  indicatorMap?: Record<string, PCKIndicatorRef>;
  compact?: boolean;
}

export function SubDimensionDetailList({
  subSkills,
  subDimensions,
  indicatorMap,
  compact = false,
}: SubDimensionDetailListProps) {
  // Preferred path: render backend-provided 13-sub-dimension data.
  if (subDimensions && subDimensions.length > 0) {
    return (
      <div className="space-y-2">
        {subDimensions.map((sd) => (
          <SubDimensionDetail
            key={sd.sub_dimension || sd.name}
            name={sd.name}
            score={sd.score}
            maxScore={sd.max_score}
            assessed={sd.assessed}
            indicatorText={sd.indicator}
            whyThisMatters={sd.why_this_matters}
            compact={compact}
          />
        ))}
      </div>
    );
  }

  // Legacy path: 23-item sub_skills with name-keyed indicator lookup.
  if (!subSkills || subSkills.length === 0) {
    return (
      <p className="text-xs text-slate-400 text-center py-2">
        暂无子维度数据
      </p>
    );
  }

  return (
    <div className="space-y-2">
      {subSkills.map((skill) => (
        <SubDimensionDetail
          key={skill.name}
          name={skill.name}
          score={skill.score}
          maxScore={skill.max_score}
          indicator={indicatorMap?.[skill.name]}
          compact={compact}
        />
      ))}
    </div>
  );
}
