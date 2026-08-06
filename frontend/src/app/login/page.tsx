"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { useAuth } from "@/lib/auth-context";
import { toast } from "sonner";

export default function LoginPage() {
  const router = useRouter();
  const { login, isLoading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email.trim() || !password.trim()) {
      setError("请输入邮箱和密码");
      return;
    }

    try {
      await login(email, password);
      toast.success("登录成功");
      router.push("/dashboard");
    } catch (err) {
      const message = err instanceof Error ? err.message : "登录失败";
      setError(message);
    }
  };

  return (
    <main className="flex-1 flex items-center justify-center p-8">
      <Card className="max-w-sm w-full p-8 space-y-6">
        <div className="text-center space-y-2">
          <div className="text-4xl">🧮</div>
          <h1 className="text-xl font-bold text-slate-800">教师登录</h1>
          <p className="text-sm text-slate-500">
            萌芽助手 Mathsprout
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="text-sm font-medium text-slate-600 block mb-1">
              邮箱
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="teacher@kindergarten.cn"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              autoComplete="email"
            />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-600 block mb-1">
              密码
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••"
              className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              autoComplete="current-password"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isLoading}
            className="w-full py-2.5 rounded-xl bg-indigo-600 text-white font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? "登录中..." : "🔐 登录"}
          </button>
        </form>

        <div className="text-center space-y-2">
          <p className="text-xs text-slate-400">
            Demo 账户：
          </p>
          <div className="space-y-1">
            <button
              onClick={() => {
                setEmail("teacher@kindergarten.cn");
                setPassword("demo123");
              }}
              className="block w-full text-xs text-indigo-600 hover:text-indigo-800 py-1 rounded bg-indigo-50 hover:bg-indigo-100 transition-colors"
            >
              👩‍🏫 教师: teacher@kindergarten.cn / demo123
            </button>
            <button
              onClick={() => {
                setEmail("admin@kindergarten.cn");
                setPassword("admin123");
              }}
              className="block w-full text-xs text-indigo-600 hover:text-indigo-800 py-1 rounded bg-indigo-50 hover:bg-indigo-100 transition-colors"
            >
              🔧 管理员: admin@kindergarten.cn / admin123
            </button>
          </div>
        </div>

        <div className="text-center">
          <Link href="/" className="text-xs text-slate-400 hover:text-slate-600">
            ← 返回首页
          </Link>
        </div>
      </Card>
    </main>
  );
}
