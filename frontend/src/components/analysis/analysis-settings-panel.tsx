"use client";

import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import type { ChildRecord } from "@/lib/api-client";

type AgeGroup = "small" | "middle" | "large";

const AGE_GROUPS: Record<AgeGroup, string> = {
  small: "小班（3-4岁）",
  middle: "中班（4-5岁）",
  large: "大班（5-6岁）",
};

interface AnalysisSettingsPanelProps {
  childName: string;
  ageGroup: AgeGroup;
  hasFile: boolean;
  loading: boolean;
  selectedChildId: number | null;
  children_list: ChildRecord[];
  onChildNameChange: (name: string) => void;
  onAgeGroupChange: (age: AgeGroup) => void;
  onChildSelect: (child: ChildRecord) => void;
  onAnalyze: () => void;
  onLoadDemo: () => void;
  actionLabel?: string;
}

export function AnalysisSettingsPanel({
  childName,
  ageGroup,
  hasFile,
  loading,
  selectedChildId,
  children_list,
  onChildNameChange,
  onAgeGroupChange,
  onChildSelect,
  onAnalyze,
  onLoadDemo,
  actionLabel,
}: AnalysisSettingsPanelProps) {
  const hasChildren = children_list.length > 0;

  return (
    <Card className="p-6 space-y-4">
      <h3 className="font-semibold text-slate-700">⚙️ 分析设置</h3>

      {/* Child selection: dropdown if children exist, else text input */}
      {hasChildren ? (
        <div>
          <label className="text-sm font-medium text-slate-600 block mb-1">
            选择幼儿
          </label>
          <select
            value={selectedChildId ?? ""}
            onChange={(e) => {
              const id = parseInt(e.target.value);
              const child = children_list.find((c) => c.id === id);
              if (child) onChildSelect(child);
            }}
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="" disabled>选择已建档的幼儿...</option>
            {children_list.map((child) => (
              <option key={child.id} value={child.id}>
                {child.name} — {AGE_GROUPS[child.age_group as AgeGroup]?.replace(/（.*）/, "") || child.age_group}
                {child.class_name ? ` (${child.class_name})` : ""}
              </option>
            ))}
          </select>
          {selectedChildId && (
            <p className="text-xs text-green-600 mt-1">
              ✅ 分析结果将自动保存到该幼儿的成长档案
            </p>
          )}
        </div>
      ) : (
        <div>
          <label className="text-sm font-medium text-slate-600 block mb-1">
            幼儿姓名
          </label>
          <input
            type="text"
            value={childName}
            onChange={(e) => onChildNameChange(e.target.value)}
            placeholder="输入幼儿姓名（请先在幼儿管理中建档）"
            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
      )}

      <div>
        <label className="text-sm font-medium text-slate-600 block mb-1">
          年龄段
        </label>
        <div className="grid grid-cols-3 gap-2">
          {(Object.entries(AGE_GROUPS) as [AgeGroup, string][]).map(
            ([key, label]) => (
              <button
                key={key}
                onClick={() => onAgeGroupChange(key)}
                className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  ageGroup === key
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {label.replace(/（.*）/, "")}
              </button>
            )
          )}
        </div>
      </div>

      <Separator />

      <div className="space-y-2">
        <button
          onClick={onAnalyze}
          disabled={!hasFile || loading}
          className="w-full py-2.5 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? "分析中..." : actionLabel || "🚀 开始分析"}
        </button>

        <button
          onClick={onLoadDemo}
          disabled={loading}
          className="w-full py-2.5 rounded-xl bg-white text-slate-600 font-medium border border-slate-300 hover:bg-slate-50 disabled:opacity-50 transition-colors"
        >
          💡 查看演示数据
        </button>
      </div>
    </Card>
  );
}
