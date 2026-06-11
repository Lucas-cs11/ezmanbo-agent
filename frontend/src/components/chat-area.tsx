"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useStore } from "@/store/useStore";
import type { Message, Session } from "@/store/useStore";
import { MessageBubble } from "@/components/MessageBubble";
import { ReportCard } from "@/components/ReportCard";
import { PdfViewer } from "@/components/PdfViewer";
import { SchematicPanel } from "@/components/SchematicPanel";
import { RiskHeatmap } from "@/components/RiskHeatmap";
import type { ReportBundle } from "@/store/useStore";

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

  const {
    setReportBundle,
    setPdfUrl,
    setPdfLoading,
    reportBundle,
  } = useStore();

  const activeSession = sessions.find((s) => s.id === activeSessionId);

  /* ── 报告加载 ── */
  const fetchReports = useCallback(
    async (query: string) => {
      setPdfLoading(true);
      const backendUrl =
        process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

      try {
        // 1. 请求结构化报告 JSON
        const jsonRes = await fetch(
          `${backendUrl}/api/report/json?q=${encodeURIComponent(query)}`
        );
        if (jsonRes.ok) {
          const bundle: ReportBundle = await jsonRes.json();
          setReportBundle(bundle);
        }
      } catch {
        // 如果后端未实现，使用 mock 数据演示
        setReportBundle({
          selection: {
            type: "selection",
            title: "选型报告 · LM2596 降压电路",
            parts: [
              {
                partNumber: "LM2596T-5.0",
                manufacturer: "TI",
                description: "3A 150kHz 降压转换器",
                score: 85,
                level: "HIGH",
                params: { Vin: "40V", Iout: "3A", Freq: "150kHz" },
              },
              {
                partNumber: "LM2596HV",
                manufacturer: "TI",
                description: "3A 150kHz 高压降压转换器",
                score: 92,
                level: "HIGH",
                params: { Vin: "60V", Iout: "3A", Freq: "150kHz" },
              },
              {
                partNumber: "TPS5430",
                manufacturer: "TI",
                description: "3A 500kHz 降压转换器",
                score: 78,
                level: "MEDIUM",
                params: { Vin: "36V", Iout: "3A", Freq: "500kHz" },
              },
            ],
          },
          risk: {
            type: "risk",
            title: "风险评估报告 · LM2596 降压电路",
            risks: [
              {
                id: "r1",
                category: "电压应力",
                level: "HIGH",
                description:
                  "LM2596 输入电压 24V，耐压裕量仅 33%，低于推荐 50% 裕量",
                recommendation: "建议更换为耐压 ≥40V 的降压转换器",
                confidence: 0.92,
              },
              {
                id: "r2",
                category: "热管理",
                level: "MEDIUM",
                description: "预估结温 Tj=112°C，接近 125°C 上限",
                recommendation: "增加散热铜皮面积或考虑外部散热器",
                confidence: 0.78,
              },
              {
                id: "r3",
                category: "输出纹波",
                level: "LOW",
                description: "计算输出纹波 15mVpp，在目标 20mVpp 范围内",
                recommendation: "当前布局满足要求，可维持设计",
                confidence: 0.95,
              },
              {
                id: "r4",
                category: "电感选型",
                level: "MEDIUM",
                description: "推荐电感饱和电流 2.5A，需求峰值电流 2.8A",
                recommendation: "更换为饱和电流 ≥3.5A 的电感",
                confidence: 0.85,
              },
            ],
          },
          replacement: {
            type: "replacement",
            title: "替换建议报告 · LM2596 降压电路",
            replacements: [
              {
                originalPart: "LM2596T-5.0",
                alternativePart: "LM2596HVT-5.0",
                manufacturer: "TI",
                reason: "输入电压裕量不足，LM2596HV 支持 60V 耐压，裕量提升至 60%",
                paramDifferences: [
                  {
                    param: "Vin(max)",
                    original: "40V",
                    alternative: "60V",
                  },
                  {
                    param: "Iout",
                    original: "3A",
                    alternative: "3A",
                  },
                  {
                    param: "Freq",
                    original: "150kHz",
                    alternative: "150kHz",
                  },
                  {
                    param: "Tj(max)",
                    original: "125°C",
                    alternative: "125°C",
                  },
                ],
              },
            ],
          },
        });
      }

      // 2. 请求 PDF 报告
      try {
        const pdfRes = await fetch(
          `${backendUrl}/api/report/pdf?q=${encodeURIComponent(query)}`
        );
        if (pdfRes.ok) {
          const blob = await pdfRes.blob();
          const url = URL.createObjectURL(blob);
          setPdfUrl(url);
        }
      } catch {
        // PDF 暂不可用
        setPdfUrl(null);
      }

      setPdfLoading(false);
    },
    [setReportBundle, setPdfUrl, setPdfLoading]
  );

  /* ── BOM 导出 ── */
  const handleBomExport = useCallback(async () => {
    const backendUrl =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    try {
      const res = await fetch(`${backendUrl}/export/bom`);
      if (res.ok) {
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "BOM_Report.xlsx";
        a.click();
        URL.revokeObjectURL(url);
      }
    } catch {
      // Backend not available - show info
      alert("BOM 导出需要后端支持。当前为演示模式。");
    }
  }, []);

  /* ── SSE 完成后加载报告 ── */
  useEffect(() => {
    if (streamComplete && streamDuration !== null) {
      const lastUserMsg = activeSession?.messages
        .slice()
        .reverse()
        .find((m) => m.role === "user");
      if (lastUserMsg) {
        fetchReports(lastUserMsg.content);
      }
    }
  }, [streamComplete, streamDuration, activeSession?.messages, fetchReports]);

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
      if (streamingContent) {
        const assistMsg: Message = {
          id: streamAssistIdRef.current,
          role: "assistant",
          content: streamingContent,
          timestamp: getTimeString(),
        };
        addMessage(activeSession.id, assistMsg);
      }
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

        {/* Report Card */}
        {!isStreaming && reportBundle && (
          <div className="max-w-4xl mx-auto">
            <ReportCard />
          </div>
        )}

        {/* Schematic + Heatmap + BOM (after report bundle is loaded) */}
        {!isStreaming && reportBundle && (
          <div className="max-w-4xl mx-auto space-y-4">
            <SchematicPanel />
            <RiskHeatmap />

            {/* BOM Export Button */}
            <div className="flex justify-end">
              <button
                onClick={handleBomExport}
                className="flex items-center gap-2 px-4 py-2.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-card)] text-[12px] font-medium text-[var(--color-text-primary)] hover:bg-brand hover:text-white hover:border-brand transition-all cursor-pointer group"
                title="导出 BOM 清单 (.xlsx)"
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
                  className="text-risk-low group-hover:text-white transition-colors"
                >
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <path d="M8 13h2" />
                  <path d="M8 17h2" />
                  <path d="M14 13h2" />
                  <path d="M14 17h2" />
                </svg>
                导出 BOM 清单 (.xlsx)
              </button>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* PdfViewer - fullscreen overlay */}
      <PdfViewer />

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