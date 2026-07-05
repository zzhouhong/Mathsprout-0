"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { MascotCharacter } from "@/components/kid";

const TABS = [
  { href: "/dashboard/assessment", label: "📸 AI评价", short: "评价", icon: "📸", color: "kid-blue" },
  { href: "/dashboard/learning", label: "📚 AI助学", short: "助学", icon: "📚", color: "kid-green" },
  { href: "/dashboard/archive", label: "🌱 成长档案", short: "档案", icon: "🌱", color: "kid-purple" },
];

export function DashboardTabs() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <>
      {/* ─── Top header (logo + user; pill tabs hidden on mobile) ─── */}
      <header
        className="sticky top-0 z-40 border-b-2 border-kid-yellow/30"
        style={{ backgroundColor: "var(--kid-cream)" }}
      >
        <div className="flex items-center justify-between px-4 h-14 max-w-7xl mx-auto">
          {/* Logo + Mascot */}
          <div className="flex items-center gap-1">
            <Link href="/" className="flex items-center gap-2 mr-3 shrink-0 group">
              <span className="animate-kid-float">
                <MascotCharacter size="sm" />
              </span>
              <span className="font-bold text-base text-slate-700 hidden sm:inline group-hover:text-kid-green transition-colors">
                萌芽数学
              </span>
            </Link>

            {/* Pill Tabs — desktop only */}
            <nav className="hidden md:flex items-center gap-1.5">
              {TABS.map((tab) => {
                const isActive = pathname.startsWith(tab.href);
                const colorVar = `var(--${tab.color})`;
                return (
                  <Link
                    key={tab.href}
                    href={tab.href}
                    className="px-3.5 py-2 rounded-full text-sm font-semibold transition-all duration-200"
                    style={
                      isActive
                        ? {
                            backgroundColor: colorVar,
                            color: "#fff",
                            boxShadow: `0 2px 8px ${colorVar}40`,
                          }
                        : { color: "#64748b" }
                    }
                    onMouseEnter={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.backgroundColor = `${colorVar}18`;
                        e.currentTarget.style.color = "#334155";
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (!isActive) {
                        e.currentTarget.style.backgroundColor = "transparent";
                        e.currentTarget.style.color = "#64748b";
                      }
                    }}
                  >
                    {tab.label}
                  </Link>
                );
              })}
            </nav>
          </div>

          {/* User */}
          <div className="flex items-center gap-2">
            {user ? (
              <div className="flex items-center gap-2 bg-white/60 rounded-full px-3 py-1.5">
                <span className="text-xs text-slate-500 hidden sm:inline font-medium">
                  {user.name || user.email}
                </span>
                <button
                  onClick={logout}
                  className="text-xs text-slate-400 hover:text-kid-coral transition-colors font-medium"
                >
                  退出
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                className="text-xs font-medium px-3 py-1.5 rounded-full bg-white/60 text-sky-600 hover:text-sky-700 hover:bg-white transition-colors"
              >
                登录
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* ─── Bottom tab bar — mobile only (thumb-friendly) ─── */}
      <nav
        className="md:hidden fixed bottom-0 inset-x-0 z-40 border-t-2 border-kid-yellow/40"
        style={{
          backgroundColor: "var(--kid-cream)",
          paddingBottom: "env(safe-area-inset-bottom, 0px)",
          boxShadow: "0 -4px 20px rgba(0,0,0,0.06)",
        }}
        aria-label="主导航"
      >
        <div className="flex items-stretch justify-around h-14">
          {TABS.map((tab) => {
            const isActive = pathname.startsWith(tab.href);
            const colorVar = `var(--${tab.color})`;
            return (
              <Link
                key={tab.href}
                href={tab.href}
                className="relative flex flex-col items-center justify-center gap-0.5 flex-1 min-w-0 transition-colors"
                style={{
                  color: isActive ? colorVar : "#94a3b8",
                  WebkitTapHighlightColor: "transparent",
                }}
                aria-current={isActive ? "page" : undefined}
              >
                <span
                  className={`text-lg leading-none ${isActive ? "animate-kid-pop-in" : ""}`}
                  style={isActive ? { filter: `drop-shadow(0 2px 6px ${colorVar}50)` } : undefined}
                >
                  {tab.icon}
                </span>
                <span className="text-[11px] font-semibold">{tab.short}</span>
                <span
                  className="absolute bottom-1 w-1 h-1 rounded-full transition-opacity"
                  style={{
                    backgroundColor: colorVar,
                    opacity: isActive ? 1 : 0,
                  }}
                />
              </Link>
            );
          })}
        </div>
      </nav>
    </>
  );
}
