"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
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

export default function ArchivePage() {
  const [activeTab, setActiveTab] = useState<SubTab>("children");
  const [children, setChildren] = useState<ChildRecord[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.children.list()
      .then((d) => setChildren(d.children))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

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

      {/* Other tabs */}
      {activeTab !== "children" && (
        <div
          className="text-center py-16 rounded-[--kid-radius-xl] animate-kid-slide-up"
          style={{ backgroundColor: "var(--kid-bg-sky)" }}
        >
          <span className="animate-kid-float inline-block">
            <MascotCharacter size="md" />
          </span>
          <div className="mt-4 space-y-4">
            {activeTab === "reports" && (
              <>
                <h3 className="font-bold text-slate-700">📊 报告档案</h3>
                <p className="text-sm text-slate-500">查看和管理所有幼儿的分析报告</p>
                <div className="flex gap-3 justify-center">
                  <Link
                    href="/dashboard/reports/teacher/demo"
                    className="px-5 py-2.5 rounded-full text-sm font-bold text-white transition-transform hover:scale-105"
                    style={{ backgroundColor: "var(--kid-blue)" }}
                  >
                    演示教师报告
                  </Link>
                  <Link
                    href="/dashboard/reports/parent/demo"
                    className="px-5 py-2.5 rounded-full text-sm font-bold text-white transition-transform hover:scale-105"
                    style={{ backgroundColor: "var(--kid-coral)" }}
                  >
                    演示家长报告
                  </Link>
                </div>
              </>
            )}
            {activeTab === "tracking" && (
              <>
                <h3 className="font-bold text-slate-700">📈 成长轨迹</h3>
                <p className="text-sm text-slate-500">选择一个幼儿查看发展轨迹</p>
                {children.slice(0, 4).map((c, i) => (
                  <Link
                    key={c.id}
                    href={`/dashboard/tracking?child=${c.id}`}
                    className="block mx-auto max-w-xs px-4 py-3 rounded-xl bg-white text-left hover:shadow-md transition-shadow"
                    style={{ animationDelay: `${i * 100}ms` }}
                  >
                    <span className="font-bold text-slate-700">{c.name}</span>
                    <span className="text-xs text-slate-400 ml-2">
                      {c.age_group === "small" ? "小班" :
                       c.age_group === "middle" ? "中班" : "大班"}
                    </span>
                    <span className="float-right" style={{ color: "var(--kid-green)" }}>→</span>
                  </Link>
                ))}
              </>
            )}
            {activeTab === "class" && (
              <>
                <h3 className="font-bold text-slate-700">🏫 班级分析</h3>
                <p className="text-sm text-slate-500">班级维度热力图、错误模式分布、发展水平统计</p>
                <Link
                  href="/dashboard/class-analysis"
                  className="inline-block mt-2 px-6 py-3 rounded-full text-sm font-bold text-white transition-transform hover:scale-105"
                  style={{ backgroundColor: "var(--kid-orange)" }}
                >
                  查看班级分析
                </Link>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
