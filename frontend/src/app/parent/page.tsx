"use client";

import { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ParentReportView } from "@/components/analysis";
import { toast } from "sonner";
import Link from "next/link";
import type { ParentReport } from "@/lib/api-client";

/** Detect WeChat in-app browser for UA-specific fixes. */
function isWeChat(): boolean {
  if (typeof navigator === "undefined") return false;
  return /micromessenger/i.test(navigator.userAgent);
}

type Screen = "login" | "loading" | "report";

/** 从 localStorage 读之前的绑定信息（避免重启/刷新后要求重新输码） */
function readStoredBind() {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem("parent_bind");
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export default function ParentPage() {
  const [accessCode, setAccessCode] = useState("");
  const [screen, setScreen] = useState<Screen>("login");
  const [report, setReport] = useState<ParentReport | null>(null);
  const [childName, setChildName] = useState("");
  const [error, setError] = useState("");
  const [noReport, setNoReport] = useState(false);

  // Cold start 自动恢复绑定：直接从 localStorage 拿 childId，跳过输码
  useEffect(() => {
    const stored = readStoredBind();
    if (stored && stored.child_id) {
      void loadLatestReport(stored.child_id, stored.child_name || "宝宝");
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /** 根据 childId 加载最新报告（供初次绑定和 cold start 共用） */
  const loadLatestReport = async (childId: number, name: string) => {
    setScreen("loading");
    setChildName(name);
    setError("");
    try {
      const { api } = await import("@/lib/api-client");
      const latest = await api.parent.latestReport(childId);
      if (latest.has_report) {
        // 适配 latest-report 的精简结构 → ParentReport 的展示结构
        // strengths/growing_areas 已是对象数组；family_activities 是字符串数组
        const adaptItem = (it: { area?: string; emoji?: string; description?: string; parent_observation_tip?: string }) => ({
          area: it.area || "",
          emoji: it.emoji || "⭐",
          description: it.description || "",
          parent_observation_tip: it.parent_observation_tip || "",
        });
        setReport({
          child_name: name,
          age_group: latest.age_group || "middle",
          generated_at: latest.generated_at || "",
          report_type: "parent",
          overall_summary: latest.overall_summary || "",
          strengths: (latest.strengths || []).map(adaptItem),
          growing_areas: (latest.growing_areas || []).map(adaptItem),
          family_activities: (latest.family_activities || []).map((it) => ({
            title: it.title || "",
            materials: it.materials || "",
            steps: it.steps || "",
            math_concept: it.why || "",
          })),
          learning_quality_notes: latest.learning_quality_notes || "",
          parent_tips: latest.parent_tips || "",
        } as unknown as ParentReport);
        setScreen("report");
      } else {
        setScreen("login");
        setNoReport(true);
        toast.info(latest.message || "该幼儿暂无分析报告，请联系老师生成");
      }
    } catch (err) {
      // 加载失败（storage 失效、网络问题等）—— 退到登录页
      const message = err instanceof Error ? err.message : "加载失败";
      toast.error(message);
      setScreen("login");
      setError(message);
    }
  };

  const handleAccess = async () => {
    const code = accessCode.trim();
    if (!code) {
      toast.error("请输入访问码");
      return;
    }

    setScreen("loading");
    setError("");

    try {
      // 用 api-client 统一发请求（走 next.config 的 rewrite 到后端，base URL 正确）
      const { api } = await import("@/lib/api-client");
      const bindData = await api.parent.bind(code);
      const childId = bindData.child_id as number;
      const name = (bindData.child_name as string) || "宝宝";

      // 持久化绑定信息（cold start 自动恢复用）
      try {
        window.localStorage.setItem(
          "parent_bind",
          JSON.stringify({
            child_id: childId,
            child_name: name,
            age_group: bindData.age_group,
            bound_at: Date.now(),
          })
        );
      } catch {
        // storage 可能被禁用，不阻断主流程
      }

      // 复用 loadLatestReport（带绑定信息）
      await loadLatestReport(childId, name);
    } catch (err) {
      const message = err instanceof Error ? err.message : "访问码无效";
      setError(message);
      setScreen("login");
      toast.error(message);
    }
  };

  // Login screen — mobile-first layout
  if (screen === "login") {
    return (
      <main
        className="min-h-[100dvh] flex items-center justify-center px-5 py-10 bg-gradient-to-b from-green-50 to-white"
        style={{
          paddingTop: "env(safe-area-inset-top, 16px)",
          paddingBottom: "env(safe-area-inset-bottom, 16px)",
        }}
      >
        <Card className="w-full max-w-md p-6 sm:p-8 space-y-5 shadow-lg border-green-100">
          <div className="text-center space-y-2">
            <div className="text-4xl sm:text-5xl mb-1">👨‍👩‍👧</div>
            <h1 className="text-lg sm:text-xl font-bold text-slate-800">家长入口</h1>
            <p className="text-xs sm:text-sm text-slate-500 px-2">
              输入老师提供的访问码，查看宝宝的学习观察记录
            </p>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-600 block mb-1.5">
              访问码
            </label>
            <input
              type="text"
              value={accessCode}
              onChange={(e) => setAccessCode(e.target.value)}
              placeholder="请输入老师提供的访问码"
              className="w-full px-4 py-3.5 border border-slate-300 rounded-xl text-base sm:text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              style={{ fontSize: "16px" }}
              onKeyDown={(e) => e.key === "Enter" && handleAccess()}
              autoFocus
            />
            {error && (
              <p className="text-sm text-red-500 mt-2">{error}</p>
            )}
            {noReport && !error && (
              <p className="text-sm text-amber-600 mt-2 bg-amber-50 p-2.5 rounded-lg border border-amber-200">
                ✅ 访问码正确（{childName}），但该幼儿暂无分析报告。
                <br />请联系老师先上传操作单生成报告。
              </p>
            )}
          </div>

          <button
            onClick={handleAccess}
            className="w-full py-3.5 rounded-xl bg-green-600 text-white text-base font-medium hover:bg-green-700 active:bg-green-800 transition-colors"
            style={{ minHeight: "48px", WebkitTapHighlightColor: "transparent" }}
          >
            查看报告
          </button>

          <div className="text-center space-y-2.5">
            <Link
              href="/dashboard/reports/parent/demo"
              className="text-sm text-indigo-600 hover:text-indigo-800 block py-1"
            >
              💡 查看演示家长报告
            </Link>
            <Link
              href="/login"
              className="text-xs text-slate-400 hover:text-slate-600 block py-1"
            >
              🔐 教师登录
            </Link>
          </div>

          <div className="p-3.5 bg-amber-50 rounded-xl border border-amber-200">
            <p className="text-xs text-amber-700 leading-relaxed">
              🌈 此报告不是考试或测评，而是帮助您发现孩子独特成长轨迹的观察记录。
              每个孩子都有自己独特的成长节奏。
            </p>
          </div>
        </Card>
      </main>
    );
  }

  // Loading screen
  if (screen === "loading") {
    return (
      <main className="min-h-screen flex items-center justify-center p-8">
        <div className="text-center space-y-4">
          <div className="w-10 h-10 border-2 border-green-600 border-t-transparent rounded-full animate-spin mx-auto" />
          <p className="text-slate-500">正在验证访问码...</p>
        </div>
      </main>
    );
  }

  // Report screen — mobile-optimized
  if (screen === "report" && report) {
    return (
      <main
        className="min-h-[100dvh] bg-gradient-to-b from-green-50 to-white"
        style={{
          paddingTop: "env(safe-area-inset-top, 0px)",
          paddingBottom: "env(safe-area-inset-bottom, 32px)",
        }}
      >
        <div className="max-w-2xl mx-auto px-4 sm:px-6 py-4 sm:py-6 space-y-4 sm:space-y-6">
          {/* Sticky header */}
          <div className="sticky top-0 z-10 flex items-center justify-between py-3 bg-green-50/90 backdrop-blur-sm -mx-4 px-4 border-b border-green-100">
            <div>
              <h1 className="text-base sm:text-xl font-bold text-slate-800">
                💚 {childName}的观察记录
              </h1>
              <p className="text-xs text-slate-400 hidden sm:block">基于数学操作单分析生成</p>
            </div>
            <button
              onClick={() => {
                setScreen("login");
                setReport(null);
                try { window.localStorage.removeItem("parent_bind"); } catch {}
              }}
              className="text-sm text-slate-400 hover:text-slate-600 active:text-slate-800 py-2 px-1"
              style={{ minHeight: "44px", minWidth: "44px" }}
            >
              ← 退出
            </button>
          </div>

          <ParentReportView report={report} />

          <div className="text-center pb-8 pt-4">
            <p className="text-xs text-slate-400 leading-relaxed px-4">
              此报告由萌芽数学 Mathsprout 生成
              <br className="sm:hidden" />
              <span className="hidden sm:inline"> · </span>
              基于《学前儿童数学学习与发展核心经验》
              <br />
              每个孩子都有自己独特的成长节奏，无需与其他孩子比较 🌈
            </p>
          </div>
        </div>
      </main>
    );
  }

  return null;
}
