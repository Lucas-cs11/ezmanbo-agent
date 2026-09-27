"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/store/authStore";
import { Lock, User, ArrowRight, Cpu, Shield } from "lucide-react";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login } = useAuthStore();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const resp = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const data = await resp.json();
      if (!resp.ok) { setError(data.detail || "认证失败，请检查账号密码"); return; }
      // 200 但响应体不完整（异常代理、半截响应）：不能拿着 undefined 去写存储，
      // 那会把字面量字符串 "undefined" 当成令牌存下来。与 ensureFresh 的同类防护对齐。
      if (!data?.token || !data?.user) { setError("登录响应异常，请稍后重试"); return; }
      try {
        login(data.token, data.user, data.refresh_token);
      } catch {
        // 接口已经成功，失败的是本地存储。这里若沿用「连接失败」会把人引去查网络。
        setError("浏览器无法保存登录状态（可能禁用了存储或空间已满），请检查浏览器设置后重试");
        return;
      }
      router.replace("/");
    } catch { setError("连接失败，请检查网络"); }
    finally { setLoading(false); }
  };

  const handleGuest = async () => {
    setError("");
    setLoading(true);
    try {
      const resp = await fetch("/auth/guest", { method: "POST" });
      const data = await resp.json();
      if (!resp.ok) { setError(data.detail || "游客进入失败，请稍后再试"); return; }
      if (!data?.token || !data?.user) { setError("登录响应异常，请稍后重试"); return; }
      try {
        login(data.token, data.user);
      } catch {
        setError("浏览器无法保存登录状态（可能禁用了存储或空间已满），请检查浏览器设置后重试");
        return;
      }
      router.replace("/");
    } catch { setError("连接失败，请检查网络"); }
    finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#022c22] via-[#044f3f] to-[#0f172a] flex items-center justify-center p-4 relative overflow-hidden">
      {/* Dot-grid ambient overlay */}
      <div className="absolute inset-0 bg-dot-grid opacity-25 pointer-events-none" />
      {/* Glow blob */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[500px] bg-teal-500/8 rounded-full blur-3xl pointer-events-none" />

      <div className="relative w-full max-w-[420px]">
        {/* Brand header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/10 border border-white/15 backdrop-blur-sm mb-5 shadow-xl">
            <Cpu className="w-8 h-8 text-teal-400" />
          </div>
          <h1 className="text-4xl font-black text-white tracking-tight mb-2 font-premium-display">
            eZmanbo
          </h1>
          <p className="text-sm text-white/45 font-medium tracking-widest uppercase">
            智能元器件选型与评估平台
          </p>
        </div>

        {/* Glass login card */}
        <div className="bg-white/96 backdrop-blur-xl rounded-3xl shadow-2xl shadow-black/40 border border-white/20 overflow-hidden">
          <div className="px-8 pt-8 pb-4">
            <h2 className="text-xl font-extrabold text-slate-800 mb-1">账号登录</h2>
            <p className="text-xs text-slate-400 font-medium">使用您的企业账号访问智能选型平台</p>
          </div>

          <form onSubmit={handleSubmit} className="px-8 pb-8 space-y-4">
            <div>
              <label className="block text-xs font-bold text-slate-500 mb-2 tracking-wide">用户名</label>
              <div className="relative">
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="text"
                  value={username}
                  onChange={e => setUsername(e.target.value)}
                  className="w-full h-11 bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-teal-400 focus:bg-white transition-all"
                  placeholder="请输入用户名"
                  required autoFocus
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-500 mb-2 tracking-wide">密码</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={e => setPassword(e.target.value)}
                  className="w-full h-11 bg-slate-50 border border-slate-200 rounded-xl pl-10 pr-4 text-sm text-slate-800 placeholder:text-slate-400 focus:outline-none focus:border-teal-400 focus:bg-white transition-all"
                  placeholder="请输入登录密码"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2.5 p-3 bg-red-50 border border-red-100 rounded-xl">
                <div className="w-1.5 h-1.5 rounded-full bg-red-500 shrink-0" />
                <span className="text-xs font-medium text-red-700">{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full h-12 bg-gradient-to-r from-teal-600 to-teal-500 hover:from-teal-500 hover:to-teal-400 text-white text-sm font-extrabold rounded-xl flex items-center justify-center gap-2 transition-all shadow-lg shadow-teal-600/25 disabled:opacity-60 mt-2"
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />
                  验证中…
                </span>
              ) : (
                <>登录平台 <ArrowRight className="w-4 h-4" /></>
              )}
            </button>

            <div className="relative py-2">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-slate-200" />
              </div>
              <div className="relative flex justify-center">
                <span className="bg-white px-3 text-2xs font-medium text-slate-400 tracking-wide">或</span>
              </div>
            </div>

            <button
              type="button"
              onClick={handleGuest}
              disabled={loading}
              className="w-full h-11 bg-white border border-slate-200 hover:border-teal-400 hover:bg-teal-50/40 text-slate-700 text-sm font-bold rounded-xl flex items-center justify-center gap-2 transition-all disabled:opacity-60"
            >
              以游客身份进入 <ArrowRight className="w-4 h-4" />
            </button>

            <p className="text-2xs text-slate-400 text-center leading-relaxed">
              游客可直接体验，对话不会保存；账号由管理员统一创建
            </p>
          </form>
        </div>

        <div className="flex items-center justify-center gap-2 mt-6">
          <Shield className="w-3 h-3 text-white/20" />
          <p className="text-white/20 text-xs font-medium">eZmanbo v2.5 · 账号由管理员统一分配</p>
        </div>
      </div>
    </div>
  );
}
