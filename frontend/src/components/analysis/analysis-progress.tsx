"use client";

import { Card } from "@/components/ui/card";

const STEPS = [
  { label: "预处理", icon: "🖼️", color: "var(--kid-orange)" },
  { label: "AI识别", icon: "🔍", color: "var(--kid-blue)" },
  { label: "评估", icon: "📊", color: "var(--kid-green)" },
  { label: "报告", icon: "📝", color: "var(--kid-purple)" },
];

interface AnalysisProgressProps {
  progressStep: string;
  progress: number;
}

export function AnalysisProgress({ progressStep, progress }: AnalysisProgressProps) {
  // Map percentage → active step index (-1 = not started, 3 = all done)
  const currentIndex =
    progress <= 0 ? -1
    : progress < 30 ? 0
    : progress < 60 ? 1
    : progress < 90 ? 2
    : 3;

  return (
    <Card className="p-5 md:p-6" style={{ boxShadow: "var(--kid-shadow-card)" }}>
      {/* Header: spinner + step text + percentage */}
      <div className="flex items-center gap-3 mb-4">
        <span className="text-2xl animate-kid-float">⏳</span>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-bold text-slate-700 truncate">
            {progressStep}
          </div>
          <div className="text-xs text-slate-400 mt-0.5">
            {progress >= 100 ? "已完成" : "正在分析，请稍候..."}
          </div>
        </div>
        <div
          className="text-lg font-extrabold tabular-nums"
          style={{ color: "var(--kid-green)" }}
        >
          {Math.round(progress)}%
        </div>
      </div>

      {/* Animated kid progress bar */}
      <div className="kid-progress mb-5">
        <div
          className="kid-progress-fill"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* 4-step indicator */}
      <div className="flex items-center">
        {STEPS.map((step, i) => {
          const done = i < currentIndex;
          const active = i === currentIndex;
          const colorVar = step.color;
          return (
            <div key={i} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center gap-1.5 shrink-0">
                <div
                  className="flex items-center justify-center w-9 h-9 md:w-10 md:h-10 rounded-full text-base transition-all duration-300"
                  style={{
                    backgroundColor: done
                      ? "var(--kid-green)"
                      : active
                      ? colorVar
                      : "#F1F5F9",
                    color: done || active ? "#fff" : "#94a3b8",
                    boxShadow: active ? `0 0 0 4px ${colorVar}30` : "none",
                    transform: active ? "scale(1.12)" : "scale(1)",
                  }}
                >
                  <span className={done ? "animate-kid-pop-in" : active ? "animate-kid-float" : ""}>
                    {done ? "✅" : step.icon}
                  </span>
                </div>
                <span
                  className="text-[10px] md:text-xs font-semibold transition-colors"
                  style={{
                    color: done ? "var(--kid-green)" : active ? colorVar : "#94a3b8",
                  }}
                >
                  {step.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div
                  className="flex-1 h-1 mx-1 md:mx-2 rounded-full transition-colors duration-500"
                  style={{
                    backgroundColor: i < currentIndex ? "var(--kid-green)" : "#E2E8F0",
                    marginTop: "-1.25rem",
                  }}
                />
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
