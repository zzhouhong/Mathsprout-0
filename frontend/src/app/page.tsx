import Link from "next/link";
import { MascotCharacter } from "@/components/kid";

export default function Home() {
  return (
    <main className="flex-1 flex flex-col items-center justify-center p-8 kid-bg-dots">
      <div className="max-w-2xl text-center space-y-10">
        {/* Hero with mascot */}
        <div className="space-y-6">
          <div className="flex justify-center">
            <MascotCharacter size="lg" />
          </div>
          <h1 className="text-5xl font-extrabold kid-rainbow-text">
            萌芽数学
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
