"use client";

import { useState } from "react";
import Link from "next/link";
import { MascotCharacter } from "@/components/kid";

// ─── PCK Knowledge Base Data ─────────────────────────────────────────

const PCK_DIMENSIONS = [
  {
    key: "counting",
    name: "数概念与运算",
    emoji: "🔢",
    color: "var(--kid-green)",
    bgColor: "var(--kid-bg-grass)",
    subDimensions: [
      { name: "点数准确性", indicator: "能手口一致地点数5以内物体，说出总数" },
      { name: "唱数与群数", indicator: "能口头唱数1-10，理解数字的序列意义" },
      { name: "数量比较", indicator: "能用一一对应的方法比较两组物体的多少" },
      { name: "数的组成", indicator: "能进行5以内数的分解与组合" },
    ],
  },
  {
    key: "addition_sub",
    name: "数运算能力",
    emoji: "➕",
    color: "var(--kid-orange)",
    bgColor: "var(--kid-bg-sunshine)",
    subDimensions: [
      { name: "实物操作正确率", indicator: "能借助实物进行5以内加减运算" },
      { name: "策略水平", indicator: "能使用多种策略解决问题（实物、手指、心算）" },
      { name: "运算思维灵活性", indicator: "能用不同方法解决同一问题，理解互逆关系" },
      { name: "应用题理解", indicator: "能理解简单的口头应用题情境" },
    ],
  },
  {
    key: "shapes_space",
    name: "图形与空间",
    emoji: "🔺",
    color: "var(--kid-blue)",
    bgColor: "var(--kid-bg-sky)",
    subDimensions: [
      { name: "平面图形识别", indicator: "能识别并命名圆形、正方形、三角形等基本图形" },
      { name: "空间方位", indicator: "能用上下、前后、里外等方位词描述位置" },
      { name: "图形拼搭", indicator: "能用基本图形拼搭出有意义的图案" },
    ],
  },
  {
    key: "patterns",
    name: "集合与模式",
    emoji: "🔮",
    color: "var(--kid-purple)",
    bgColor: "var(--kid-bg-bubblegum)",
    subDimensions: [
      { name: "模式识别", indicator: "能发现并描述简单的AB模式规律" },
      { name: "分类能力", indicator: "能按一种属性（颜色、大小、形状）对物体进行分类" },
      { name: "模式扩展", indicator: "能延续简单的AB或ABC模式序列" },
      { name: "排序能力", indicator: "能按大小、长短等特征对3-5个物体排序" },
      { name: "规律语言描述", indicator: "能用语言描述发现的规律" },
    ],
  },
];

const AGE_GROUPS = [
  { key: "small", name: "小班", age: "3-4岁", desc: "动作感知阶段：通过具体实物操作建立数学概念" },
  { key: "middle", name: "中班", age: "4-5岁", desc: "表象过渡阶段：借助图像、点卡从动作思维向表象思维发展" },
  { key: "large", name: "大班", age: "5-6岁", desc: "符号萌芽阶段：开始使用数字符号，发展初步的数学思维" },
];

export default function Home() {
  const [showPCK, setShowPCK] = useState(false);
  const [expandedDim, setExpandedDim] = useState<string | null>(null);

  return (
    <main className="flex-1 flex flex-col items-center p-8 kid-bg-dots" style={{ overflowY: "auto" }}>
      <div className="max-w-3xl w-full text-center space-y-10">
        {/* Hero with mascot */}
        <div className="space-y-6">
          <div className="flex justify-center">
            <MascotCharacter size="lg" />
          </div>
          <h1 className="text-5xl font-extrabold kid-rainbow-text">
            萌芽助手
          </h1>
          <p className="text-xl text-gray-600 font-medium">Mathsprout</p>
          <p className="text-lg text-gray-500 leading-relaxed max-w-md mx-auto">
            为每一位幼儿的数学成长
            <br />
            <span className="text-gray-400">提供温暖而专业的观察与陪伴</span>
          </p>
          <div className="flex items-center justify-center gap-2 text-sm text-gray-400">
            <span>📖 依据《学前儿童数学学习与发展核心经验》</span>
          </div>
        </div>

        {/* Feature cards — 3 main sections */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-left kid-stagger">
          <div className="kid-card animate-kid-slide-up bg-gradient-to-br from-kid-bg-sunshine to-white">
            <div className="text-4xl mb-3">📸</div>
            <h3 className="font-bold text-lg text-gray-700 mb-2">AI评价</h3>
            <p className="text-sm text-gray-500 leading-relaxed">
              拍照或上传幼儿数学操作单，AI 自动识别答案、分析策略、生成4维度能力评估报告
            </p>
          </div>
          <div className="kid-card animate-kid-slide-up bg-gradient-to-br from-kid-bg-grass to-white">
            <div className="text-4xl mb-3">📚</div>
            <h3 className="font-bold text-lg text-gray-700 mb-2">AI助学</h3>
            <p className="text-sm text-gray-500 leading-relaxed">
              生成个性化练习操作单 · PCK维度雷达图可视化
              <br />
              <span className="text-kid-green font-medium">评估过程透明展示，教师看得懂</span>
            </p>
          </div>
          <div className="kid-card animate-kid-slide-up bg-gradient-to-br from-kid-bg-bubblegum to-white">
            <div className="text-4xl mb-3">🌱</div>
            <h3 className="font-bold text-lg text-gray-700 mb-2">成长档案</h3>
            <p className="text-sm text-gray-500 leading-relaxed">
              幼儿管理 · 报告历史 · 成长轨迹
              <br />
              班级分析 · 发展趋势一目了然
            </p>
          </div>
        </div>

        {/* ── PCK Knowledge Base (collapsible) ── */}
        <div className="text-left">
          <button
            onClick={() => setShowPCK(!showPCK)}
            className="w-full flex items-center justify-between px-5 py-4 rounded-2xl bg-white/80 backdrop-blur border-2 border-purple-200 hover:border-purple-300 transition-all"
            style={{ boxShadow: "var(--kid-shadow-card)" }}
          >
            <div className="flex items-center gap-3">
              <span className="text-2xl">📖</span>
              <div className="text-left">
                <h3 className="font-bold text-slate-800">PCK 知识底座</h3>
                <p className="text-xs text-slate-500">
                  依据《学前儿童数学学习与发展核心经验》· 4维度 · 16项子技能
                </p>
              </div>
            </div>
            <span className={`text-xl text-purple-400 transition-transform duration-300 ${showPCK ? "rotate-180" : ""}`}>
              ▾
            </span>
          </button>

          {showPCK && (
            <div className="mt-4 space-y-4 animate-kid-slide-up">
              {/* Age group overview */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {AGE_GROUPS.map((ag) => (
                  <div
                    key={ag.key}
                    className="bg-white rounded-xl p-4 border border-slate-100"
                    style={{ boxShadow: "var(--kid-shadow-card)" }}
                  >
                    <div className="font-bold text-slate-800 mb-1">{ag.name} ({ag.age})</div>
                    <p className="text-xs text-slate-500 leading-relaxed">{ag.desc}</p>
                  </div>
                ))}
              </div>

              {/* Dimension cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {PCK_DIMENSIONS.map((dim) => {
                  const isExpanded = expandedDim === dim.key;
                  return (
                    <div
                      key={dim.key}
                      className="bg-white rounded-xl overflow-hidden border border-slate-100 transition-all"
                      style={{ boxShadow: "var(--kid-shadow-card)" }}
                    >
                      <button
                        onClick={() => setExpandedDim(isExpanded ? null : dim.key)}
                        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-slate-50 transition-colors"
                      >
                        <span
                          className="w-10 h-10 rounded-full flex items-center justify-center text-lg flex-shrink-0"
                          style={{ backgroundColor: dim.bgColor }}
                        >
                          {dim.emoji}
                        </span>
                        <div className="text-left flex-1 min-w-0">
                          <div className="font-bold text-slate-800 text-sm">{dim.name}</div>
                          <div className="text-xs text-slate-400">{dim.subDimensions.length}项子技能</div>
                        </div>
                        <span className={`text-slate-400 transition-transform ${isExpanded ? "rotate-180" : ""}`}>▾</span>
                      </button>

                      {isExpanded && (
                        <div className="border-t px-4 py-3 space-y-2 bg-slate-50/50">
                          {dim.subDimensions.map((sd) => (
                            <div key={sd.name} className="flex items-start gap-2">
                              <span className="w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0" style={{ backgroundColor: dim.color }} />
                              <div>
                                <div className="text-sm font-medium text-slate-700">{sd.name}</div>
                                <div className="text-xs text-slate-500">📋 {sd.indicator}</div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Teaching principles */}
              <div className="bg-purple-50 rounded-xl p-4 border border-purple-100">
                <h4 className="text-sm font-bold text-purple-700 mb-2">🧠 教学原则</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs text-purple-800">
                  <div>• 实物操作先于符号表征</div>
                  <div>• 关注过程而非仅看对错</div>
                  <div>• 镜像书写是正常发展现象</div>
                  <div>• 每名幼儿有自己的发展节奏</div>
                  <div>• 数学融入日常生活和游戏</div>
                  <div>• 鼓励幼儿用语言表达思考</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* CTA buttons — big & inviting */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            href="/dashboard"
            className="kid-btn kid-btn-primary text-xl px-10"
          >
            🧑‍🏫 进入教师端
          </Link>
          <Link
            href="/parent"
            className="kid-btn kid-btn-fun text-xl px-10"
          >
            👨‍👩‍👧 家长入口
          </Link>
        </div>

        {/* Footer note */}
        <div className="bg-white/60 backdrop-blur rounded-2xl p-4 max-w-md mx-auto">
          <p className="text-xs text-gray-400 leading-relaxed">
            🌱 本工具定位为教师观察辅助工具，操作单是幼儿自然学习活动的产出。
            <br />
            报告中不会出现"分数""排名""落后"等字样，使用温暖、成长导向的语言。
          </p>
        </div>
      </div>
    </main>
  );
}
