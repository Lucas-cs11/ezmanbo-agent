"use client";

import { useEffect } from "react";
import Image from "next/image";
import { useChatStore } from "@/store/chat";
import { Plus, Trash2, MessageSquare } from "lucide-react";
import { cn, buildSelectionContext } from "@/lib/utils";

export function Sidebar() {
  const { sessions, activeSessionId, createSession, switchSession, deleteSession, syncSessionsFromBackend } = useChatStore();

  // ── 挂载时同步后端会话 ──────────────────────────────
  useEffect(() => {
    syncSessionsFromBackend();
  }, [syncSessionsFromBackend]);

  // ── 新建会话：注入最近的选型上下文 ────────────────────
  const handleCreateSession = () => {
    // 创建新会话前捕获当前活跃会话的选型报告
    const prevActive = useChatStore.getState().activeSession();
    const lastReport = prevActive?.messages
      .filter((m) => m.role === "assistant" && m.report)
      .pop()?.report;

    const newId = createSession();

    if (lastReport?.constraints) {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
      fetch(`${API_BASE}/agent/init_session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: newId,
          context_type: "selection_context",
          context: buildSelectionContext(lastReport),
        }),
      }).catch(() => {});
    }
  };

  return (
    <aside className="w-[260px] h-full flex flex-col bg-surface-sidebar border-r border-gray-200 shrink-0 overflow-y-auto">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-8 h-8 rounded-lg bg-brand-700 flex items-center justify-center overflow-hidden">
            <Image src="/icon.svg" alt="eZmanbo" width={24} height={24} className="w-6 h-6 object-contain" />
          </div>
          <div>
            <div className="text-sm font-bold text-brand-900">eZmanbo</div>
            <div className="text-[10px] text-gray-500">智能元器件选型</div>
          </div>
        </div>
        <button
          onClick={handleCreateSession}
          className="w-full flex items-center justify-center gap-2 py-2 rounded-lg border border-brand-200 text-brand-700 text-sm hover:bg-brand-50 transition-colors"
        >
          <Plus className="w-4 h-4" />
          新对话
        </button>
      </div>

      {/* Session list */}
      <nav className="flex-1 overflow-y-auto py-2 min-h-0">
        {sessions.map((s) => (
          <button
            key={s.id}
            onClick={() => switchSession(s.id)}
            className={cn(
              "w-full flex items-center gap-2 px-4 py-2.5 text-sm text-left transition-colors group",
              s.id === activeSessionId
                ? "bg-brand-50 text-brand-800 font-medium border-r-2 border-warm-500"
                : "text-gray-600 hover:bg-gray-100"
            )}
          >
            <MessageSquare className="w-4 h-4 shrink-0 opacity-60" />
            <span className="truncate flex-1">{s.title}</span>
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (sessions.length > 1) deleteSession(s.id);
              }}
              className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-100 rounded transition-all"
            >
              <Trash2 className="w-3 h-3 text-gray-400 hover:text-red-500" />
            </button>
          </button>
        ))}
        {sessions.length === 0 && (
          <p className="px-4 py-8 text-xs text-gray-400 text-center">暂无对话记录</p>
        )}
      </nav>

      {/* Footer */}
      <div className="p-3 border-t border-gray-200">
        <div className="text-[10px] text-gray-400 text-center">
          eZmanbo · FastAPI
        </div>
      </div>
    </aside>
  );
}
