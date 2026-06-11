"use client";

import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { useStore } from "@/store/useStore";
import type { Session } from "@/store/useStore";

export function Sidebar() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  const sessions = useStore((s) => s.sessions);
  const activeSessionId = useStore((s) => s.activeSessionId);
  const setActiveSession = useStore((s) => s.setActiveSession);
  const deleteSession = useStore((s) => s.deleteSession);
  const isStreaming = useStore((s) => s.isStreaming);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleNewChat = () => {
    setActiveSession(null);
  };

  if (!mounted) {
    return (
      <aside className="w-sidebar h-screen border-r border-[var(--color-border)] bg-[var(--color-card)] flex flex-col shrink-0">
        <div className="p-4" />
      </aside>
    );
  }

  return (
    <aside className="w-sidebar h-screen border-r border-[var(--color-border)] bg-[var(--color-card)] flex flex-col shrink-0 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-[var(--color-border)]">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-brand flex items-center justify-center shrink-0">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="white"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 2L2 7l10 5 10-5-10-5z" />
              <path d="M2 17l10 5 10-5" />
              <path d="M2 12l10 5 10-5" />
            </svg>
          </div>
          <div>
            <h1 className="text-sm font-bold text-[var(--color-text-primary)] leading-tight">
              EZPLM
            </h1>
            <p className="text-[10px] text-[var(--color-text-secondary)] leading-tight">
              器件风险分析
            </p>
          </div>
        </div>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <button
          onClick={handleNewChat}
          disabled={isStreaming}
          className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg border border-[var(--color-border)] bg-transparent text-[var(--color-text-primary)] text-sm font-medium hover:bg-brand hover:text-white hover:border-brand transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          新建分析
        </button>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-2">
        <p className="px-3 py-2 text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-secondary)]">
          历史记录
        </p>
        {sessions.length === 0 ? (
          <p className="px-3 py-4 text-[12px] text-[var(--color-text-secondary)] text-center">
            暂无历史记录
          </p>
        ) : (
          <nav className="space-y-0.5">
            {sessions.map((session) => (
              <div
                key={session.id}
                className={`group flex items-center rounded-lg transition-all duration-150 ${
                  activeSessionId === session.id
                    ? "bg-brand/10"
                    : "hover:bg-[var(--color-background)]"
                }`}
              >
                <button
                  onClick={() => setActiveSession(session.id)}
                  className={`flex-1 text-left px-3 py-2.5 rounded-lg text-sm cursor-pointer min-w-0 ${
                    activeSessionId === session.id
                      ? "text-brand font-medium"
                      : "text-[var(--color-text-secondary)]"
                  }`}
                >
                  <p className="truncate text-[13px] leading-tight">
                    {session.title}
                  </p>
                  <p className="text-[10px] mt-0.5 opacity-60">
                    {session.timestamp}
                  </p>
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(session.id);
                  }}
                  className="px-2 py-2.5 text-[var(--color-text-secondary)] hover:text-risk-high opacity-0 group-hover:opacity-100 transition-all cursor-pointer shrink-0"
                  title="删除会话"
                >
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    <line x1="10" y1="11" x2="10" y2="17" />
                    <line x1="14" y1="11" x2="14" y2="17" />
                  </svg>
                </button>
              </div>
            ))}
          </nav>
        )}
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-[var(--color-border)]">
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs text-[var(--color-text-secondary)] hover:bg-[var(--color-background)] transition-colors cursor-pointer"
        >
          {theme === "dark" ? (
            <>
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <circle cx="12" cy="12" r="5" />
                <line x1="12" y1="1" x2="12" y2="3" />
                <line x1="12" y1="21" x2="12" y2="23" />
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                <line x1="1" y1="12" x2="3" y2="12" />
                <line x1="21" y1="12" x2="23" y2="12" />
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
              </svg>
              浅色模式
            </>
          ) : (
            <>
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <path d="M21 12.79A9 9 0 1 1 11.21 3a7 7 0 0 0 9.79 9.79z" />
              </svg>
              暗色模式
            </>
          )}
        </button>
      </div>
    </aside>
  );
}