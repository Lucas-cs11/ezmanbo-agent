"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useStore } from "@/store/useStore";
import type { Message, Session } from "@/store/useStore";
import { MessageBubble } from "@/components/MessageBubble";

function generateId() {
  return `msg-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function getTimeString() {
  const now = new Date();
  return `${String(now.getHours()).padStart(2, "0")}:${String(now.getMinutes()).padStart(2, "0")}`;
}

function getFullTimeString() {
  const now = new Date();
  const y = now.getFullYear();
  const M = String(now.getMonth() + 1).padStart(2, "0");
  const d = String(now.getDate()).padStart(2, "0");
  const h = String(now.getHours()).padStart(2, "0");
  const m = String(now.getMinutes()).padStart(2, "0");
  return `${y}-${M}-${d} ${h}:${m}`;
}

export function ChatArea() {
  const [input, setInput] = useState("");
  const [streamProgress, setStreamProgress] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const streamAssistIdRef = useRef<string | null>(null);
  const startTimeRef = useRef<number | null>(null);

  const {
    sessions,
    activeSessionId,
    addSession,
    addMessage,
    setStreamingContent,
    appendStreamingContent,
    setStreaming,
    isStreaming,
    streamingContent,
    setStreamComplete,
    setStreamDuration,
    streamComplete,
    streamDuration,
    setActiveSession,
  } = useStore();

  const activeSession = sessions.find((s) => s.id === activeSessionId);

  const cancelStream = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setStreaming(false);
    setStreamComplete(true);
    if (startTimeRef.current) {
      const duration = (Date.now() - startTimeRef.current) / 1000;
      setStreamDuration(duration);
    }
  }, [setStreaming, setStreamComplete, setStreamDuration]);

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  useEffect(() => {
    if (streamComplete && streamAssistIdRef.current && activeSession) {
      const assistMsg: Message = {
        id: streamAssistIdRef.current,
        role: "assistant",
        content: streamingContent,
        timestamp: getTimeString(),
      };
      addMessage(activeSession.id, assistMsg);
      streamAssistIdRef.current = null;
      setStreamingContent("");
      setStreaming(false);
    }
  }, [
    streamComplete,
    streamingContent,
    activeSession,
    addMessage,
    setStreamingContent,
    setStreaming,
  ]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [
    activeSession?.messages,
    streamingContent,
  ]);

  const startStream = useCallback(
    (sessionId: string, userInput: string) => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }

      setStreamingContent("");
      setStreaming(true);
      setStreamComplete(false);
      setStreamDuration(null);
      startTimeRef.current = Date.now();
      streamAssistIdRef.current = generateId();

      const backendUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const url = `${backendUrl}/analyze/stream?input=${encodeURIComponent(userInput)}`;
      const eventSource = new EventSource(url);

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.token) {
            appendStreamingContent(data.token);
          }
          if (data.done) {
            eventSource.close();
            eventSourceRef.current = null;
            setStreamComplete(true);
            setStreamProgress(`已完成 · 耗时 ${((Date.now() - startTimeRef.current!) / 1000).toFixed(1)}s`);
          }
        } catch {
          appendStreamingContent(event.data);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
        eventSourceRef.current = null;
        cancelStream();
      };

      eventSourceRef.current = eventSource;
    },
    [
      setStreamingContent,
      setStreaming,
      setStreamComplete,
      setStreamDuration,
      appendStreamingContent,
      cancelStream,
    ]
  );

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    let sessionId = activeSessionId;
    if (!sessionId || !sessions.find((s) => s.id === sessionId)) {
      const newSession: Session = {
        id: `session-${Date.now()}`,
        title: trimmed.length > 30 ? trimmed.slice(0, 30) + "..." : trimmed,
        timestamp: getFullTimeString(),
        messages: [],
      };
      addSession(newSession);
      sessionId = newSession.id;
    }

    const userMsg: Message = {
      id: generateId(),
      role: "user",
      content: trimmed,
      timestamp: getTimeString(),
    };
    addMessage(sessionId, userMsg);
    setInput("");
    setStreamProgress(null);

    startStream(sessionId, trimmed);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const messages = activeSession?.messages || [];

  if (!activeSession) {
    return (
      <main className="flex-1 flex flex-col h-screen min-w-0 bg-[var(--color-background)] items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 rounded-2xl bg-brand flex items-center justify-center mx-auto mb-4">
            <svg
              width="32"
              height="32"
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
          <h2 className="text-lg font-bold text-[var(--color-text-primary)] mb-2">
            EZPLM 器件风险分析
          </h2>
          <p className="text-[13px] text-[var(--color-text-secondary)] max-w-md">
            输入电路拓扑信息、器件型号和工作参数，AI 将帮你分析潜在风险。
          </p>
        </div>
        <div className="absolute bottom-6 w-full max-w-2xl px-4">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <div className="flex-1 relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="输入器件型号或电路参数..."
                rows={2}
                className="w-full px-4 py-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] text-[13px] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] outline-none focus:border-brand focus:ring-1 focus:ring-brand/20 transition-all resize-none scrollbar-thin"
              />
            </div>
            <button
              type="submit"
              disabled={!input.trim() || isStreaming}
              className="px-5 py-3 rounded-xl bg-brand text-white text-[13px] font-medium hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed shrink-0 cursor-pointer flex items-center gap-1.5"
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

  return (
    <main className="flex-1 flex flex-col h-screen min-w-0 bg-[var(--color-background)]">
      {/* Header */}
      <header className="h-14 border-b border-[var(--color-border)] bg-[var(--color-card)] flex items-center px-4 shrink-0">
        <h2 className="text-sm font-semibold text-[var(--color-text-primary)] truncate max-w-[60%]">
          {activeSession.title}
        </h2>
        <div className="ml-auto flex items-center gap-3">
          {isStreaming ? (
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-risk-medium animate-pulse" />
              <span className="text-[11px] text-risk-medium font-medium">
                分析中...
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-risk-low" />
              <span className="text-[11px] text-[var(--color-text-secondary)]">
                就绪
              </span>
            </div>
          )}
        </div>
      </header>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-4 py-4">
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}

        {/* Streaming message */}
        {isStreaming && (
          <div>
            <MessageBubble
              message={{
                id: streamAssistIdRef.current || "streaming",
                role: "assistant",
                content: "",
                timestamp: "",
              }}
              isStreaming={true}
              streamingContent={streamingContent}
            />
            {streamComplete && streamDuration !== null && (
              <div className="flex items-center gap-2 ml-10 mb-4">
                <span className="text-[11px] text-[var(--color-text-secondary)]">
                  <span className="inline-block w-1.5 h-1.5 rounded-full bg-risk-low mr-1" />
                  已完成 · 耗时 {streamDuration.toFixed(1)}s
                </span>
              </div>
            )}
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-3 border-t border-[var(--color-border)] bg-[var(--color-card)] shrink-0">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="flex-1 relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="输入器件型号或电路参数... (Enter 发送, Shift+Enter 换行)"
              rows={2}
              className="w-full px-4 py-3 rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] text-[13px] text-[var(--color-text-primary)] placeholder:text-[var(--color-text-secondary)] outline-none focus:border-brand focus:ring-1 focus:ring-brand/20 transition-all resize-none scrollbar-thin"
            />
          </div>
          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className="px-5 py-3 rounded-xl bg-brand text-white text-[13px] font-medium hover:opacity-90 transition-all disabled:opacity-50 disabled:cursor-not-allowed shrink-0 cursor-pointer flex items-center gap-1.5"
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