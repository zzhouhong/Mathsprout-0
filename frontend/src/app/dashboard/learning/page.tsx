"use client";

import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { authFetch } from "@/lib/api-client";
import { PckRadarChart, EvaluationTrace } from "@/components/learning";
import { WorksheetGenerator } from "@/components/WorksheetGenerator";
import { Card } from "@/components/ui/card";
import { MascotCharacter } from "@/components/kid";

interface PckFramework {
  dimensions: Array<{
    key: string;
    name: string;
    sub_dimensions: Array<{ key: string; name: string }>;
    sub_skills: string[];
    milestones_by_age: Record<string, string[]>;
  }>;
  development_stages: {
    counting: { stages: Array<{ key: string; name: string; age: string; description: string }> };
    operation: { stages: Array<{ key: string; name: string; age: string; description: string }> };
    pattern: { stages: Array<{ key: string; name: string; age_anchor: string; description: string }> };
  };
  teaching_principles: Array<{ id: string; name: string; description: string }>;
  age_groups: Array<{ key: string; name: string }>;
}

const stageIcons: Record<string, string> = {
  counting: "🔢", operation: "➕", pattern: "🔁",
};

const stageColors: Record<string, string> = {
  counting: "kid-blue", operation: "kid-orange", pattern: "kid-purple",
};

export default function LearningPage() {
  const searchParams = useSearchParams();
  const realAnalysisId = searchParams.get("analysisId");
  const [pck, setPck] = useState<PckFramework | null>(null);
  const [evalTrace, setEvalTrace] = useState<any>(null);
  const [traceLoading, setTraceLoading] = useState(false);
  const [showMobilePCK, setShowMobilePCK] = useState(false);
  const [demoAge, setDemoAge] = useState("middle");
  const [demoType, setDemoType] = useState("counting");
  const [isRealTrace, setIsRealTrace] = useState(false);

  useEffect(() => {
    authFetch("/api/v1/analysis/pck-framework")
      .then((r) => r.json())
      .then((data) => setPck(data))
      .catch(() => toast.error("加载PCK框架数据失败"));
  }, []);

  const loadTrace = useCallback(async () => {
    setTraceLoading(true);
    try {
      const url = realAnalysisId
        ? `/api/v1/analysis/${realAnalysisId}/evaluation-trace`
        : `/api/v1/analysis/evaluation-trace?worksheet_type=${demoType}&age_group=${demoAge}`;
      setIsRealTrace(!!realAnalysisId);
      const r = await authFetch(url);
      const data = await r.json();
      setEvalTrace(data);
    } catch {
      toast.error("加载评估过程数据失败");
    } finally {
      setTraceLoading(false);
    }
  }, [demoAge, demoType, realAnalysisId]);

  useEffect(() => { loadTrace(); }, [loadTrace]);

  const demoScores: Record<string, number> = {};
  if (evalTrace?.dimensions) {
    for (const d of evalTrace.dimensions) {
      demoScores[d.dimension] = d.score;
    }
  }

  return (
    <div
      className="flex-1 p-4 md:p-6 max-w-7xl mx-auto space-y-6"
      style={{ minHeight: "calc(100vh - 56px)" }}
    >
      {/* Header */}
      <div className="flex items-center gap-3">
        <span className="animate-kid-float"><MascotCharacter size="sm" /></span>
        <div>
          <h1 className="text-2xl font-extrabold" style={{ color: "var(--kid-green)" }}>
            📚 AI助学
          </h1>
          <p className="text-sm text-slate-500 mt-0.5">
            生成练习操作单 · PCK维度可视化 · 评估过程透明展示
          </p>
        </div>
      </div>

      {/* Mobile toggle — only shown on small screens */}
      <div className="lg:hidden flex gap-2">
        <button
          onClick={() => setShowMobilePCK(false)}
          className="flex-1 px-4 py-2.5 rounded-full text-sm font-bold transition-all"
          style={{
            backgroundColor: !showMobilePCK ? "var(--kid-green)" : "var(--kid-bg-grass)",
            color: !showMobilePCK ? "#fff" : "var(--kid-green)",
          }}
        >
          📝 操作单生成器
        </button>
        <button
          onClick={() => setShowMobilePCK(true)}
          className="flex-1 px-4 py-2.5 rounded-full text-sm font-bold transition-all"
          style={{
            backgroundColor: showMobilePCK ? "var(--kid-blue)" : "var(--kid-bg-sky)",
            color: showMobilePCK ? "#fff" : "var(--kid-blue)",
          }}
        >
          🧠 PCK评估过程
        </button>
      </div>

      {/* Main content — side by side on desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6 kid-stagger">
        {/* Left: Worksheet Generator (2 cols on desktop) */}
        <div
          className={`lg:col-span-2 animate-kid-slide-up ${
            showMobilePCK ? "hidden lg:block" : ""
          }`}
        >
          <div
            className="rounded-[--kid-radius-xl] p-5"
            style={{ backgroundColor: "var(--kid-bg-grass)", border: "2px dashed var(--kid-green)" }}
          >
            <div className="flex items-center gap-2 mb-3">
              <span className="text-xl">📝</span>
              <h2 className="font-bold" style={{ color: "var(--kid-green)" }}>
                操作单生成器
              </h2>
            </div>
            <WorksheetGenerator />
          </div>
        </div>

        {/* Right: PCK Panel (3 cols on desktop) */}
        <div
          className={`lg:col-span-3 space-y-5 animate-kid-slide-up ${
            !showMobilePCK ? "hidden lg:block" : ""
          }`}
          style={{ animationDelay: "100ms" }}
        >
          {/* Controls */}
          <div
            className="rounded-[--kid-radius-md] px-4 py-3 flex items-center gap-3 flex-wrap"
            style={{ backgroundColor: "var(--kid-bg-sky)" }}
          >
            <span className="text-sm font-bold" style={{ color: "var(--kid-blue)" }}>
              🧪 演示数据
            </span>
            <select
              value={demoType}
              onChange={(e) => setDemoType(e.target.value)}
              className="text-xs border-2 border-kid-blue/20 rounded-full px-3 py-1.5 bg-white font-medium"
            >
              <option value="counting">数数操作单</option>
              <option value="shapes">图形操作单</option>
              <option value="patterns">模式操作单</option>
            </select>
            <select
              value={demoAge}
              onChange={(e) => setDemoAge(e.target.value)}
              className="text-xs border-2 border-kid-blue/20 rounded-full px-3 py-1.5 bg-white font-medium"
            >
              <option value="small">小班 (3-4岁)</option>
              <option value="middle">中班 (4-5岁)</option>
              <option value="large">大班 (5-6岁)</option>
            </select>
            <button
              onClick={loadTrace}
              className="text-xs px-4 py-1.5 rounded-full font-bold text-white transition-transform hover:scale-105 active:scale-95"
              style={{ backgroundColor: "var(--kid-blue)" }}
            >
              🔄 刷新
            </button>
          </div>

          {/* Radar + Stages row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Radar Chart */}
            <div
              className="rounded-[--kid-radius-xl] p-5 bg-white"
              style={{ boxShadow: "var(--kid-shadow-card)" }}
            >
              <h3 className="font-bold text-slate-700 mb-3 text-center">
                🧭 PCK 4维度雷达图
              </h3>
              {pck ? (
                <PckRadarChart dimensions={pck.dimensions} scores={demoScores} size={280} />
              ) : (
                <div className="animate-pulse h-[280px] bg-slate-100 rounded-xl flex items-center justify-center">
                  <span className="text-slate-400">加载中...</span>
                </div>
              )}
              <p className="text-xs text-slate-400 mt-3 text-center">
                虚线 = 年龄段参考 · 实心 = 当前表现
              </p>
            </div>

            {/* Development Stages */}
            {pck && (
              <div
                className="rounded-[--kid-radius-xl] p-5 bg-white"
                style={{ boxShadow: "var(--kid-shadow-card)" }}
              >
                <h3 className="font-bold text-slate-700 mb-3">📈 认知发展阶段</h3>
                <div className="space-y-3">
                  {Object.entries(pck.development_stages || {}).map(([key, stageData]) => {
                    const c = stageColors[key] || "kid-teal";
                    return (
                      <div
                        key={key}
                        className="rounded-xl p-3"
                        style={{ border: `2px solid var(--${c})20`, backgroundColor: `var(--${c})08` }}
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-base">{stageIcons[key] || "📌"}</span>
                          <span className="font-bold text-sm" style={{ color: `var(--${c})` }}>
                            {key === "counting" ? "计数发展" :
                             key === "operation" ? "运算发展" : "模式发展"}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-1">
                          {(stageData.stages || []).map((stage) => (
                            <div
                              key={stage.key}
                              className="flex-1 min-w-[70px] rounded-lg px-2 py-1.5 text-center bg-white"
                              style={{ border: `1px solid var(--${c})30` }}
                            >
                              <div className="text-xs font-bold text-slate-700">{stage.name}</div>
                              <div className="text-[10px] text-slate-400">
                                {(stage as any).age || (stage as any).age_anchor || ""}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* Evaluation Trace */}
          <div
            className="rounded-[--kid-radius-xl] p-5 bg-white"
            style={{ boxShadow: "var(--kid-shadow-card)" }}
          >
            <EvaluationTrace data={evalTrace} loading={traceLoading} />
          </div>

          {/* Teaching Principles */}
          {pck && (
            <div
              className="rounded-[--kid-radius-xl] p-5"
              style={{ backgroundColor: "var(--kid-bg-sunshine)" }}
            >
              <h3 className="font-bold text-slate-700 mb-3">🎯 教学原则</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {(pck.teaching_principles || []).slice(0, 3).map((tp, i) => (
                  <div
                    key={tp.id}
                    className="bg-white rounded-xl p-3 animate-kid-slide-up"
                    style={{ animationDelay: `${i * 100}ms`, boxShadow: "var(--kid-shadow-card)" }}
                  >
                    <div className="font-bold text-sm text-slate-700 mb-1">
                      {["🌱", "🌿", "🌳"][i]} {tp.name}
                    </div>
                    <p className="text-xs text-slate-500 leading-relaxed">{tp.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
