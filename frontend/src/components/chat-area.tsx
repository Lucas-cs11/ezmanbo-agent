"use client";

import { useState } from "react";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}

const welcomeMessage: Message = {
  id: "0",
  role: "assistant",
  content:
    "你好，我是器件风险分析助手。请输入电路拓扑信息、器件型号和工作参数，我将帮你分析潜在风险。",
  timestamp: "",
};

const mockMessages: Message[] = [
  welcomeMessage,
  {
    id: "1",
    role: "user",
    content:
      "分析 LM2596 降压电路：Vin=24V, Vout=5V, Iout=2A, 环境温度 45°C",
    timestamp: "14:30",
  },
  {
    id: "2",
    role: "assistant",
    content:
      "已收到您的输入。正在分析 LM2596 降压拓扑...\n\n## 拓扑审核\n- 拓扑：Buck（降压）✅\n- Vin=24V → Vout=5V，压差 19V，方向一致\n\n## 器件审核\n- LM2596 额定电流 3A ≥ 需求 2A ✅\n- 耐压 40V，输入 24V，裕量 40%\n\n## 风险提示\n发现以下需要关注的问题：",
    timestamp: "14:31",
  },
];

export function ChatArea() {
  const [input, setInput] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    // Placeholder: will connect to AI backend
    setInput("");
  };

  return (
    <main className="flex-1 flex flex-col h-screen min-w-0 bg-[var(--color-background)]">
      {/* Header */}
      <header className="h-14 border-b border-[var(--color-border)] bg-[var(--color-card)] flex items-center px-4 shrink-0">
        <h2 className="text-sm font-semibold text-[var(--color-text-primary)]">
          LM2596 降压电路风险分析
        </h2>
        <div className="ml-auto flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-risk-high" />
          <span className="text-[11px] text-[var(--color-text-secondary)]">
            在线
          </span>
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-4 space-y-4">
        {mockMessages.map((msg) => (
          <div
            key={msg.id}
            className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}
          >
            <div
              className={`max-w-[75%] rounded-xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-brand text-white"
                  : msg.role === "system"
                    ? "bg-risk-high/10 border border-risk-high/30 text-[var(--color-text-primary)]"
                    : "bg-[var(--color-card)] border border-[var(--color-border)] text-[var(--color-text-primary)]"
              }`}
            >
              {msg.role === "assistant" && (
                <div className="flex items-center gap-2 mb-2">
                  <div className="w-6 h-6 rounded-md bg-brand flex items-center justify-center shrink-0">
                    <svg
                      width="12"
                      height="12"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="white"
                      strokeWidth="2"
                    >
                      <path d="M12 2L2 7l10 5 10-5-10-5z" />
                      <path d="M2 17l10 5 10-5" />
                      <path d="M2 12l10 5 10-5" />
                    </svg>
                  </div>
                  <span className="text-[11px] font-semibold text-brand">
                    EZPLM
                  </span>
                </div>
              )}
              <div className="text-[13px] leading-relaxed whitespace-pre-wrap">
                {msg.content}
              </div>
              {msg.timestamp && (
                <p className="text-[10px] mt-1.5 opacity-50">{msg.timestamp}</p>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Input Area */}
      <div className="p-3 border-t border-[var(--color-border)] bg-[var(--color-card)] shrink-0">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="输入器件型号或电路参数..."
            className="flex-1 px-4 py-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] text-[13px] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] outline-none focus:border-brand focus:ring-1 focus:ring-brand/20 transition-all"
          />
          <button
            type="submit"
            className="px-4 py-2.5 rounded-lg bg-brand text-white text-[13px] font-medium hover:bg-brand-800 transition-colors shrink-0 cursor-pointer flex items-center gap-1.5"
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
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
            发送
          </button>
        </form>
      </div>
    </main>
  );
}