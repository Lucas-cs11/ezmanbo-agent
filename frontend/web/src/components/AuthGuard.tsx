"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/store/authStore";

const PUBLIC_PATHS = ["/login", "/register"];

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { ensureFresh } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);

  // 每次进入应用都先静默续期：访问令牌没过期就沿用，过期则用刷新令牌换新，
  // 两者都不行才判为登出。这样有效期内刷新或重开页面都不用重新登录。
  useEffect(() => {
    let cancelled = false;
    const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));

    ensureFresh().then((ok) => {
      if (cancelled) return;
      if (isPublic) {
        if (ok) router.replace("/");
        else setReady(true);
        return;
      }
      if (!ok) {
        router.replace("/login");
        return;
      }
      setReady(true);
    });

    return () => { cancelled = true; };
  }, [pathname, ensureFresh, router]);

  // 页面长期挂在后台时访问令牌会过期，回到前台立刻补一次
  useEffect(() => {
    const recheck = () => {
      ensureFresh().then((ok) => { if (!ok) router.replace("/login"); });
    };
    const onVisible = () => {
      if (document.visibilityState === "visible") recheck();
    };
    window.addEventListener("focus", recheck);
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.removeEventListener("focus", recheck);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [ensureFresh, router]);

  if (!ready) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-sm text-gray-400">加载中…</div>
      </div>
    );
  }

  return <>{children}</>;
}
