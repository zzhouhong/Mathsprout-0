"use client";

import { useState, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { toast } from "sonner";

type AgeGroup = "small" | "middle" | "large";
type Dimension = "counting" | "addition_sub" | "shapes_space" | "patterns";

const AGE_LABELS: Record<AgeGroup, string> = {
  small: "小班（3-4岁）",
  middle: "中班（4-5岁）",
  large: "大班（5-6岁）",
};

const DIMENSION_CONFIG: { key: Dimension; name: string; emoji: string; description: string }[] = [
  { key: "counting", name: "数数练习", emoji: "🔢", description: "点数、比较、序数、数的组成" },
  { key: "addition_sub", name: "加减练习", emoji: "➕", description: "实物加减、符号运算、应用题" },
  { key: "shapes_space", name: "图形练习", emoji: "🔺", description: "图形识别、空间方位、拼搭" },
  { key: "patterns", name: "规律练习", emoji: "🔍", description: "分类、模式识别、排序" },
];

export function WorksheetGenerator() {
  const [childName, setChildName] = useState("");
  const [ageGroup, setAgeGroup] = useState<AgeGroup>("middle");
  const [difficulty, setDifficulty] = useState(2);
  const [selectedDims, setSelectedDims] = useState<Set<Dimension>>(new Set(["counting", "shapes_space"]));
  const [problemCount, setProblemCount] = useState(1);
  const [includeAnswerKey, setIncludeAnswerKey] = useState(true);
  const [generatedHtml, setGeneratedHtml] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const toggleDim = (dim: Dimension) => {
    setSelectedDims((prev) => {
      const next = new Set(prev);
      if (next.has(dim)) {
        if (next.size > 1) next.delete(dim); // Keep at least 1
      } else {
        next.add(dim);
      }
      return next;
    });
  };

  const generate = useCallback(async () => {
    if (!childName.trim()) {
      toast.error("请输入幼儿姓名");
      return;
    }

    setLoading(true);
    try {
      const { authFetch } = await import("@/lib/api-client");
      const params = new URLSearchParams({
        child_name: childName,
        age_group: ageGroup,
        difficulty: String(difficulty),
        dimensions: Array.from(selectedDims).join(","),
        problem_count: String(problemCount),
        include_answer: String(includeAnswerKey),
        format: "html",
      });

      const res = await authFetch(`/api/v1/worksheets/generate?${params}`);

      if (!res.ok) throw new Error("生成失败");

      const html = await res.text();
      setGeneratedHtml(html);
      toast.success("操作单生成成功！");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "生成操作单失败");
    } finally {
      setLoading(false);
    }
  }, [childName, ageGroup, difficulty, selectedDims, problemCount, includeAnswerKey]);

  const print = () => {
    if (!generatedHtml) return;
    const win = window.open("", "_blank");
    if (win) {
      win.document.write(generatedHtml);
      win.document.close();
      win.focus();
      setTimeout(() => win.print(), 500);
    }
  };

  return (
    <div className="flex-1 p-6 max-w-5xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-800">📝 生成操作单</h1>
        <p className="text-sm text-slate-500 mt-1">
          根据幼儿水平自动生成可打印的数学练习操作单
        </p>
      </div>

      {/* Config Panel */}
      <Card className="p-6 space-y-4">
        <h3 className="font-semibold text-slate-700">⚙️ 操作单设置</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Child name */}
          <div>
            <label className="text-sm font-medium text-slate-600 block mb-1">幼儿姓名</label>
            <input
              type="text"
              value={childName}
              onChange={(e) => setChildName(e.target.value)}
              placeholder="输入幼儿姓名"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>

          {/* Age group */}
          <div>
            <label className="text-sm font-medium text-slate-600 block mb-1">年龄段</label>
            <select
              value={ageGroup}
              onChange={(e) => setAgeGroup(e.target.value as AgeGroup)}
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
            >
              {Object.entries(AGE_LABELS).map(([k, v]) => (
                <option key={k} value={k}>{v}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Difficulty */}
        <div>
          <label className="text-sm font-medium text-slate-600 block mb-1">
            难度等级：{"⭐".repeat(difficulty)}
          </label>
          <input
            type="range"
            min="1"
            max="5"
            value={difficulty}
            onChange={(e) => setDifficulty(Number(e.target.value))}
            className="w-full accent-indigo-600"
          />
          <div className="flex justify-between text-xs text-slate-400">
            <span>简单（Lv.1）</span>
            <span>中等（Lv.3）</span>
            <span>挑战（Lv.5）</span>
          </div>
        </div>

        {/* Dimensions */}
        <div>
          <label className="text-sm font-medium text-slate-600 block mb-2">练习内容（可多选）</label>
          <div className="flex flex-wrap gap-2">
            {DIMENSION_CONFIG.map((dim) => (
              <button
                key={dim.key}
                onClick={() => toggleDim(dim.key)}
                className={`px-3 py-2 rounded-lg text-sm transition-colors ${
                  selectedDims.has(dim.key)
                    ? "bg-indigo-100 text-indigo-700 border-2 border-indigo-400"
                    : "bg-white text-slate-500 border-2 border-slate-200 hover:border-slate-300"
                }`}
              >
                {dim.emoji} {dim.name}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Problem count */}
          <div>
            <label className="text-sm font-medium text-slate-600 block mb-1">
              题目数量：{problemCount} 题（建议每次1题，卡通大卡片适合幼儿）
            </label>
            <input
              type="range"
              min="1"
              max="20"
              step="2"
              value={problemCount}
              onChange={(e) => setProblemCount(Number(e.target.value))}
              className="w-full accent-indigo-600"
            />
          </div>

          {/* Include answer key */}
          <div className="flex items-center gap-3 pt-6">
            <input
              type="checkbox"
              id="includeAnswer"
              checked={includeAnswerKey}
              onChange={(e) => setIncludeAnswerKey(e.target.checked)}
              className="w-4 h-4 accent-indigo-600"
            />
            <label htmlFor="includeAnswer" className="text-sm text-slate-600">
              包含答案页
            </label>
          </div>
        </div>

        {/* Generate button */}
        <button
          onClick={generate}
          disabled={loading}
          className="w-full py-3 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-700 disabled:opacity-50 transition-colors"
        >
          {loading ? "⏳ 正在生成..." : "🖨️ 生成操作单"}
        </button>
      </Card>

      {/* Preview */}
      {generatedHtml && (
        <Card className="p-2 overflow-hidden">
          <div className="flex items-center justify-between p-3 bg-slate-50 rounded-t-xl">
            <span className="text-sm font-medium text-slate-600">📄 预览</span>
            <div className="flex gap-2">
              <button
                onClick={print}
                className="px-3 py-1.5 rounded-lg bg-green-600 text-white text-xs hover:bg-green-700"
              >
                🖨️ 打印
              </button>
              <button
                onClick={() => setGeneratedHtml(null)}
                className="px-3 py-1.5 rounded-lg bg-slate-100 text-slate-600 text-xs hover:bg-slate-200"
              >
                ✕ 关闭
              </button>
            </div>
          </div>
          <iframe
            srcDoc={generatedHtml}
            className="w-full border-0"
            style={{ height: "600px" }}
            title="操作单预览"
          />
        </Card>
      )}

      {/* Tips */}
      <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
        <p className="text-sm text-amber-700">
          💡 <span className="font-medium">使用提示：</span>
          操作单根据幼儿年龄和选择的难度自动生成。低难度使用更多图画和实物表征，
          高难度逐步引入符号和抽象问题。打印时建议使用A4纸。
        </p>
      </div>
    </div>
  );
}
