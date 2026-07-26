"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { toast } from "sonner";
import { api, type ChildRecord } from "@/lib/api-client";
import { Card } from "@/components/ui/card";
import { MascotCharacter, MascotBubble } from "@/components/kid";

const SUB_TABS = [
  { key: "children", label: "👶 幼儿列表", color: "kid-purple" },
  { key: "reports", label: "📊 报告档案", color: "kid-blue" },
  { key: "tracking", label: "📈 成长轨迹", color: "kid-green" },
  { key: "class", label: "🏫 班级分析", color: "kid-orange" },
] as const;

type SubTab = typeof SUB_TABS[number]["key"];

const ageColors: Record<string, string> = {
  small: "kid-coral", middle: "kid-orange", large: "kid-blue",
};

const ageLabels: Record<string, string> = {
  small: "小班", middle: "中班", large: "大班",
};

// ─── Report Archive types ────────────────────────────────────────────

interface ReportSummary {
  child_name: string;
  report_id: number;
  type: string;
  generated_at: string;
  summary: string;
  dimensions: Array<{ name: string; score: number; level: string }>;
}

// ─── Tracking summary types ──────────────────────────────────────────

interface TrajectorySummary {
  child_id: number;
  child_name: string;
  age_group: string;
  assessment_count: number;
  latest_scores: Record<string, { score: number; level: string }>;
  trends: Record<string, string>;
}

// ─── Class summary types ─────────────────────────────────────────────

interface ClassSummary {
  total_classes: number;
  total_children: number;
  classes: Array<{
    class_name: string;
    total: number;
    age_groups: { small: number; middle: number; large: number };
  }>;
}

export default function ArchivePage() {
  const [activeTab, setActiveTab] = useState<SubTab>("children");
  const [children, setChildren] = useState<ChildRecord[]>([]);
  const [loading, setLoading] = useState(true);

  // ─── Report archive state ──────────────────────────────────────────
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [reportsLoading, setReportsLoading] = useState(false);

  // ─── Tracking state ────────────────────────────────────────────────
  const [trajectories, setTrajectories] = useState<TrajectorySummary[]>([]);
  const [trackingLoading, setTrackingLoading] = useState(false);

  // ─── Class summary state ───────────────────────────────────────────
  const [classSummary, setClassSummary] = useState<ClassSummary | null>(null);
  const [classLoading, setClassLoading] = useState(false);

  useEffect(() => {
    api.children.list()
      .then((d) => setChildren(d.children))
      .catch(() => toast.error("加载幼儿列表失败，请检查网络后刷新"))
      .finally(() => setLoading(false));
  }, []);

  // Fetch reports when switching to reports tab
  useEffect(() => {
    if (activeTab !== "reports" || reports.length > 0) return;
    setReportsLoading(true);
    Promise.all(
      children.slice(0, 10).map((c) =>
        api.children.reports(c.id).catch(() => null)
      )
    )
      .then((results) => {
        const allReports: ReportSummary[] = [];
        results.forEach((r) => {
          if (r?.reports) {
            r.reports.forEach((rep: any) => {
              allReports.push({
                child_name: r.child.name,
                report_id: rep.report_id,
                type: rep.type,
                generated_at: rep.generated_at,
                summary: rep.summary || "",
                dimensions: rep.dimensions || [],
              });
            });
          }
        });
        // Sort by date descending
        allReports.sort((a, b) => b.generated_at.localeCompare(a.generated_at));
        setReports(allReports);
      })
      .catch(() => toast.error("加载报告档案失败，请稍后重试"))
      .finally(() => setReportsLoading(false));
  }, [activeTab, children, reports.length]);

  // Fetch trajectories when switching to tracking tab
  useEffect(() => {
    if (activeTab !== "tracking" || trajectories.length > 0) return;
    if (children.length === 0) return;
    setTrackingLoading(true);
    Promise.all(
      children.slice(0, 8).map(async (c) => {
        try {
          const stats = await api.children.stats(c.id);
          return {
            child_id: c.id,
            child_name: c.name,
            age_group: c.age_group,
            assessment_count: stats.worksheet_count,
            latest_scores: {} as Record<string, { score: number; level: string }>,
            trends: {} as Record<string, string>,
          } as TrajectorySummary;
        } catch {
          return {
            child_id: c.id,
            child_name: c.name,
            age_group: c.age_group,
            assessment_count: 0,
            latest_scores: {},
            trends: {},
          } as TrajectorySummary;
        }
      })
    )
      .then((results) => {
        setTrajectories(results.filter((t) => t.assessment_count > 0));
      })
      .catch(() => toast.error("加载成长轨迹失败，请稍后重试"))
      .finally(() => setTrackingLoading(false));
  }, [activeTab, children, trajectories.length]);

  // Fetch class summary when switching to class tab
  useEffect(() => {
    if (activeTab !== "class" || classSummary) return;
    setClassLoading(true);
    api.children.classSummary()
      .then((d) => setClassSummary(d))
      .catch(() => toast.error("加载班级分析失败，请稍后重试"))
      .finally(() => setClassLoading(false));
  }, [activeTab, classSummary]);

  return (
    <div
      className="flex-1 p-4 md:p-6 max-w-7xl mx-auto space-y-6"
      style={{ minHeight: "calc(100vh - 56px)" }}
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <span className="animate-kid-float"><MascotCharacter size="sm" /></span>
        <div>
          <h1 className="text-2xl font-extrabold" style={{ color: "var(--kid-purple)" }}>
            🌱 成长档案
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            幼儿管理 · 报告历史 · 成长追踪 · 班级分析
          </p>
        </div>
      </div>

      {/* Sub-tabs — colorful underline style */}
      <div className="flex gap-0 border-b-2 border-slate-100">
        {SUB_TABS.map((tab) => {
          const isActive = activeTab === tab.key;
          return (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className="px-4 py-2.5 text-sm font-bold transition-all relative"
              style={{
                color: isActive ? `var(--${tab.color})` : "#94a3b8",
              }}
            >
              {tab.label}
              {isActive && (
                <div
                  className="absolute bottom-0 left-2 right-2 h-0.5 rounded-full"
                  style={{
                    backgroundColor: `var(--${tab.color})`,
                    bottom: "-2px",
                  }}
                />
              )}
            </button>
          );
        })}
      </div>

      {/* Tab: Children List */}
      {activeTab === "children" && (
        <div className="space-y-4 kid-stagger">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-slate-700">
              班级幼儿 <span style={{ color: "var(--kid-purple)" }}>{children.length}人</span>
            </h2>
          </div>
          {loading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1,2,3].map(i => (
                <div key={i} className="h-28 bg-slate-100 rounded-[--kid-radius-xl] animate-pulse" />
              ))}
            </div>
          ) : children.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {children.map((c, i) => {
                const cVar = ageColors[c.age_group] || "kid-teal";
                return (
                  <div
                    key={c.id}
                    className="animate-kid-slide-up bg-white rounded-[--kid-radius-xl] p-5 transition-transform hover:-translate-y-1"
                    style={{
                      animationDelay: `${i * 80}ms`,
                      boxShadow: "var(--kid-shadow-card)",
                      borderLeft: `4px solid var(--${cVar})`,
                    }}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-9 h-9 rounded-full flex items-center justify-center text-white font-bold text-sm"
                          style={{ backgroundColor: `var(--${cVar})` }}
                        >
                          {c.name[0]}
                        </div>
                        <div>
                          <div className="font-bold text-slate-800">{c.name}</div>
                          <div className="text-xs text-slate-500">
                            {c.age_group === "small" ? "小班" :
                             c.age_group === "middle" ? "中班" : "大班"}
                            {" · "}{c.class_name || "未分班"}
                          </div>
                        </div>
                      </div>
                      <span
                        className="text-[10px] font-bold px-2 py-0.5 rounded-full"
                        style={{
                          backgroundColor: `var(--${cVar})18`,
                          color: `var(--${cVar})`,
                        }}
                      >
                        {c.parent_access_code}
                      </span>
                    </div>
                    <div className="flex gap-3 mt-3 pt-3 border-t border-slate-100">
                      <Link
                        href={`/dashboard/children/${c.id}/reports`}
                        className="text-xs font-medium hover:underline"
                        style={{ color: `var(--kid-blue)` }}
                      >
                        📋 查看报告
                      </Link>
                      <Link
                        href={`/dashboard/tracking?child=${c.id}`}
                        className="text-xs font-medium hover:underline"
                        style={{ color: `var(--kid-green)` }}
                      >
                        📈 成长轨迹
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div
              className="text-center py-16 rounded-[--kid-radius-xl]"
              style={{ backgroundColor: "var(--kid-bg-bubblegum)" }}
            >
              <span className="animate-kid-float inline-block">
                <MascotCharacter size="md" />
              </span>
              <MascotBubble emotion="think" className="max-w-xs mx-auto mt-4">
                <p className="text-sm text-slate-500">
                  还没有添加幼儿哦～快去添加第一位小朋友吧！
                </p>
              </MascotBubble>
              <Link
                href="/dashboard/children"
                className="inline-block mt-4 px-6 py-3 rounded-full font-bold text-white transition-transform hover:scale-105"
                style={{ backgroundColor: "var(--kid-purple)" }}
              >
                ➕ 添加幼儿
              </Link>
            </div>
          )}
        </div>
      )}

      {/* Tab: Report Archive */}
      {activeTab === "reports" && (
        <div className="space-y-4 kid-stagger">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-slate-700">
              报告档案 <span style={{ color: "var(--kid-blue)" }}>{reports.length}份</span>
            </h2>
          </div>
          {reportsLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-20 bg-slate-100 rounded-[--kid-radius-xl] animate-pulse" />
              ))}
            </div>
          ) : reports.length > 0 ? (
            <div className="space-y-3">
              {reports.map((r, i) => (
                <div
                  key={`${r.report_id}-${i}`}
                  className="animate-kid-slide-up bg-white rounded-[--kid-radius-xl] p-4 flex items-center gap-4 transition-transform hover:-translate-y-0.5"
                  style={{
                    animationDelay: `${i * 60}ms`,
                    boxShadow: "var(--kid-shadow-card)",
                    borderLeft: `4px solid ${r.type === "teacher" ? "var(--kid-blue)" : "var(--kid-coral)"}`,
                  }}
                >
                  <div className="flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center text-xl"
                    style={{ backgroundColor: r.type === "teacher" ? "var(--kid-bg-sky)" : "var(--kid-bg-bubblegum)" }}
                  >
                    {r.type === "teacher" ? "📋" : "🏠"}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="font-bold text-slate-800">{r.child_name}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full font-medium"
                        style={{
                          backgroundColor: r.type === "teacher" ? "var(--kid-bg-sky)" : "var(--kid-bg-bubblegum)",
                          color: r.type === "teacher" ? "var(--kid-blue)" : "var(--kid-coral)",
                        }}
                      >
                        {r.type === "teacher" ? "教师版" : "家长版"}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-xs text-slate-400">
                      <span>{new Date(r.generated_at).toLocaleDateString("zh-CN")}</span>
                      {r.dimensions.slice(0, 3).map((d) => (
                        <span key={d.name} className="text-slate-500">
                          {d.name} {d.score}%
                        </span>
                      ))}
                    </div>
                  </div>
                  <Link
                    href={`/dashboard/reports/${r.type}/demo?id=${r.id}`}
                    className="flex-shrink-0 px-4 py-2 rounded-full text-xs font-bold text-white transition-transform hover:scale-105"
                    style={{ backgroundColor: "var(--kid-blue)" }}
                  >
                    查看 →
                  </Link>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-16 rounded-[--kid-radius-xl]" style={{ backgroundColor: "var(--kid-bg-sky)" }}>
              <MascotCharacter size="md" />
              <p className="text-sm text-slate-500 mt-4">暂无报告记录，完成一次操作单分析后这里将展示报告</p>
            </div>
          )}
        </div>
      )}

      {/* Tab: Growth Tracking */}
      {activeTab === "tracking" && (
        <div className="space-y-4 kid-stagger">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-slate-700">
              成长轨迹 <span style={{ color: "var(--kid-green)" }}>{trajectories.length}人有数据</span>
            </h2>
          </div>
          {trackingLoading ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-28 bg-slate-100 rounded-[--kid-radius-xl] animate-pulse" />
              ))}
            </div>
          ) : trajectories.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {trajectories.map((t, i) => (
                <Link
                  key={t.child_id}
                  href={`/dashboard/tracking?child=${t.child_id}`}
                  className="animate-kid-slide-up bg-white rounded-[--kid-radius-xl] p-4 transition-transform hover:-translate-y-1 block"
                  style={{
                    animationDelay: `${i * 80}ms`,
                    boxShadow: "var(--kid-shadow-card)",
                    borderLeft: `4px solid var(--kid-green)`,
                  }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center text-sm font-bold"
                        style={{ color: "var(--kid-green)" }}
                      >
                        {t.child_name[0]}
                      </div>
                      <div>
                        <span className="font-bold text-slate-800">{t.child_name}</span>
                        <span className="text-xs text-slate-400 ml-1">
                          {ageLabels[t.age_group] || t.age_group}
                        </span>
                      </div>
                    </div>
                    <span className="text-xs px-2 py-0.5 rounded-full font-medium"
                      style={{ backgroundColor: "var(--kid-bg-grass)", color: "var(--kid-green)" }}
                    >
                      {t.assessment_count}次分析
                    </span>
                  </div>
                  {/* Mini progress bars for each dimension */}
                  <div className="grid grid-cols-4 gap-1.5">
                    {(["counting", "addition_sub", "shapes_space", "patterns"] as const).map((dim) => {
                      const score = t.latest_scores?.[dim]?.score;
                      const level = t.latest_scores?.[dim]?.level;
                      const dimLabels: Record<string, string> = {
                        counting: "数概念", addition_sub: "运算", shapes_space: "图形", patterns: "模式",
                      };
                      return (
                        <div key={dim} className="text-center">
                          <div className="text-[10px] text-slate-400 mb-0.5">{dimLabels[dim]}</div>
                          <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className="h-full rounded-full transition-all"
                              style={{
                                width: `${score || 0}%`,
                                backgroundColor: (score || 0) >= 71 ? "var(--kid-green)" :
                                  (score || 0) >= 41 ? "var(--kid-orange)" : "var(--kid-coral)",
                              }}
                            />
                          </div>
                          <div className="text-[10px] font-bold mt-0.5" style={{ color: "var(--kid-green)" }}>
                            {level || "—"}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </Link>
              ))}
            </div>
          ) : (
            <div className="text-center py-16 rounded-[--kid-radius-xl]" style={{ backgroundColor: "var(--kid-bg-grass)" }}>
              <MascotCharacter size="md" />
              <p className="text-sm text-slate-500 mt-4">暂无成长数据，完成多次分析后将自动生成成长轨迹</p>
            </div>
          )}
          {/* Link to full tracking page */}
          {children.length > 0 && (
            <div className="text-center">
              <Link
                href="/dashboard/tracking"
                className="inline-block px-5 py-2.5 rounded-full text-sm font-bold text-white transition-transform hover:scale-105"
                style={{ backgroundColor: "var(--kid-green)" }}
              >
                查看完整成长轨迹 →
              </Link>
            </div>
          )}
        </div>
      )}

      {/* Tab: Class Analysis */}
      {activeTab === "class" && (
        <div className="space-y-4 kid-stagger">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-slate-700">
              班级分析
            </h2>
          </div>
          {classLoading ? (
            <div className="space-y-4">
              <div className="h-24 bg-slate-100 rounded-[--kid-radius-xl] animate-pulse" />
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-32 bg-slate-100 rounded-[--kid-radius-xl] animate-pulse" />
                ))}
              </div>
            </div>
          ) : classSummary ? (
            <div className="space-y-4">
              {/* Summary stats */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div className="animate-kid-slide-up bg-white rounded-[--kid-radius-xl] p-5 text-center"
                  style={{ boxShadow: "var(--kid-shadow-card)" }}
                >
                  <div className="text-3xl font-extrabold" style={{ color: "var(--kid-purple)" }}>
                    {classSummary.total_classes}
                  </div>
                  <div className="text-sm text-slate-500 mt-1">班级总数</div>
                </div>
                <div className="animate-kid-slide-up bg-white rounded-[--kid-radius-xl] p-5 text-center"
                  style={{ animationDelay: "80ms", boxShadow: "var(--kid-shadow-card)" }}
                >
                  <div className="text-3xl font-extrabold" style={{ color: "var(--kid-orange)" }}>
                    {classSummary.total_children}
                  </div>
                  <div className="text-sm text-slate-500 mt-1">幼儿总数</div>
                </div>
                <div className="animate-kid-slide-up bg-white rounded-[--kid-radius-xl] p-5 text-center"
                  style={{ animationDelay: "160ms", boxShadow: "var(--kid-shadow-card)" }}
                >
                  <div className="text-3xl font-extrabold" style={{ color: "var(--kid-blue)" }}>
                    {reports.length}
                  </div>
                  <div className="text-sm text-slate-500 mt-1">报告总数</div>
                </div>
              </div>

              {/* Per-class breakdown */}
              {classSummary.classes.map((cls, i) => (
                <div
                  key={cls.class_name}
                  className="animate-kid-slide-up bg-white rounded-[--kid-radius-xl] p-5"
                  style={{
                    animationDelay: `${i * 100}ms`,
                    boxShadow: "var(--kid-shadow-card)",
                    borderLeft: `4px solid var(--kid-orange)`,
                  }}
                >
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-bold text-slate-800">🏫 {cls.class_name}</h3>
                    <span className="text-sm text-slate-500">{cls.total}名幼儿</span>
                  </div>
                  <div className="flex gap-4 text-sm">
                    <div className="flex items-center gap-1.5">
                      <span className="w-3 h-3 rounded-full" style={{ backgroundColor: "var(--kid-coral)" }} />
                      <span className="text-slate-600">小班 {cls.age_groups.small}人</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="w-3 h-3 rounded-full" style={{ backgroundColor: "var(--kid-orange)" }} />
                      <span className="text-slate-600">中班 {cls.age_groups.middle}人</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <span className="w-3 h-3 rounded-full" style={{ backgroundColor: "var(--kid-blue)" }} />
                      <span className="text-slate-600">大班 {cls.age_groups.large}人</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-16 rounded-[--kid-radius-xl]" style={{ backgroundColor: "var(--kid-bg-sunshine)" }}>
              <MascotCharacter size="md" />
              <p className="text-sm text-slate-500 mt-4">暂无班级数据</p>
            </div>
          )}
          {/* Link to full class analysis */}
          <div className="text-center">
            <Link
              href="/dashboard/class-analysis"
              className="inline-block px-5 py-2.5 rounded-full text-sm font-bold text-white transition-transform hover:scale-105"
              style={{ backgroundColor: "var(--kid-orange)" }}
            >
              查看详细班级分析 →
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}
