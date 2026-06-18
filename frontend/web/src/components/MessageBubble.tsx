"use client";

import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import Image from "next/image";
import { ChevronDown, ChevronRight, Brain } from "lucide-react";
import { cn, formatElapsed, LLM_MODEL } from "@/lib/utils";
import { ReportCard } from "@/components/ReportCard";
import { SchematicPanel } from "@/components/SchematicPanel";
import type { ChatMessage } from "@/types";

interface ProgInfo { current: number; total: number; pct: number; }

/* ── 思考过程折叠块 ──────────────────────────────────────────── */
function ThinkingBlock({ content, isStreaming }: { content: string; isStreaming?: boolean }) {
  const [expanded, setExpanded] = useState(false);
  const lines = content.trim().split("\n").filter(Boolean);
  if (!lines.length) return null;

  return (
    <div className="mb-3 border border-purple-100 rounded-xl overflow-hidden bg-purple-50/40">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-1.5 px-3 py-2 text-left hover:bg-purple-50/60 transition-colors"
      >
        <Brain className={cn("w-3 h-3 shrink-0", isStreaming && !expanded ? "text-purple-400 animate-pulse" : "text-purple-400")} />
        <span className="text-[10px] text-purple-600 font-medium flex-1">
          思考过程
          {isStreaming && <span className="ml-1 text-purple-400">（推理中…）</span>}
          {!isStreaming && <span className="ml-1 text-purple-400">({lines.length} 步)</span>}
        </span>
        {expanded
          ? <ChevronDown className="w-3 h-3 text-purple-400 shrink-0" />
          : <ChevronRight className="w-3 h-3 text-purple-400 shrink-0" />}
      </button>
      {expanded && (
        <div className="px-3 pb-3 space-y-1 border-t border-purple-100">
          {lines.map((line, i) => (
            <p key={i} className="text-[10px] text-purple-700/80 leading-relaxed font-mono">
              {line}
            </p>
          ))}
        </div>
      )}
    </div>
  );
}

export function MessageBubble({ message, progress }: { message: ChatMessage; progress?: ProgInfo }) {
  const isUser = message.role === "user";
  const [showReport, setShowReport] = useState(false);

  return (
    <div className={cn("flex gap-3 animate-slide-up", isUser ? "justify-end" : "justify-start")}>
      {!isUser && (
        <div className="w-8 h-8 rounded-lg bg-brand-100 flex items-center justify-center overflow-hidden shrink-0 mt-1">
          <Image src="/icon.svg" alt="eZmanbo" width={20} height={20} className="w-5 h-5 object-contain" />
        </div>
      )}

      <div className={cn("max-w-[72%]", isUser ? "order-first" : "")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "bg-brand-700 text-white rounded-br-md"
              : "bg-surface-card border border-gray-200 rounded-bl-md shadow-sm"
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : message.content ? (
            <div>
              {message.isStreaming && (
                <div className="mb-2">
                  <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-brand-50 text-brand-600 font-medium">
                    选型分析中
                  </span>
                </div>
              )}
              {!message.isStreaming && !message.report && message.content.length > 0 && (
                <div className="mb-2">
                  <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-gray-50 text-gray-500 font-medium">
                    对话模式
                  </span>
                </div>
              )}
              {message.report && (
                <div className="mb-2 flex items-center gap-2">
                  <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-green-50 text-green-700 font-medium">
                    选型完成
                  </span>
                  {message.report.risks?.overall_risk_level && (
                    <span className={cn(
                      "text-[9px] px-1.5 py-0.5 rounded-full font-medium",
                      message.report.risks.overall_risk_level === "high"
                        ? "bg-red-50 text-red-700"
                        : message.report.risks.overall_risk_level === "medium"
                          ? "bg-orange-50 text-orange-700"
                          : "bg-green-50 text-green-700"
                    )}>
                      {message.report.risks.overall_risk_level === "high" ? "高风险" :
                       message.report.risks.overall_risk_level === "medium" ? "中风险" : "低风险"}
                    </span>
                  )}
                </div>
              )}

              {/* ── 思考过程折叠块（在正文上方）── */}
              {message.thinking && (
                <ThinkingBlock
                  content={message.thinking}
                  isStreaming={message.isStreaming && !message.thinkingDone}
                />
              )}

              {progress && message.isStreaming && (
                <div className="mb-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] text-brand-600 font-medium">
                      {progress.pct < 10 ? "解析需求" :
                       progress.pct < 30 ? "检索器件库" :
                       progress.pct < 60 ? `评分中 ${progress.current}/${progress.total}` :
                       progress.pct < 80 ? "构建证据链" :
                       progress.pct < 95 ? "风险评估" : "生成报告"}
                    </span>
                    <span className="text-[10px] text-brand-500 font-mono">{progress.pct}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-brand-100 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-brand-500 transition-all duration-500 ease-out"
                      style={{ width: `${progress.pct}%` }}
                    />
                  </div>
                </div>
              )}

              <div className={cn("markdown-body", message.isStreaming && "typing-cursor")}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>

              {!message.isStreaming && (
                <div className="mt-2 pt-2 border-t border-gray-100">
                  <span className="text-[9px] text-gray-400">{LLM_MODEL}</span>
                </div>
              )}
            </div>
          ) : (
            <div>
              {/* 仅有 thinking 尚无正文内容时，也展示思考块 */}
              {message.thinking && (
                <ThinkingBlock
                  content={message.thinking}
                  isStreaming={message.isStreaming && !message.thinkingDone}
                />
              )}
              {progress ? (
                <div className="mb-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] text-brand-600 font-medium">初始化中</span>
                    <span className="text-[10px] text-brand-500 font-mono">{progress.pct}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-brand-100 overflow-hidden">
                    <div className="h-full rounded-full bg-brand-500 transition-all duration-500 ease-out" style={{ width: `${progress.pct}%` }} />
                  </div>
                </div>
              ) : null}
              <div className="flex items-center gap-2 text-gray-400 text-xs">
                <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse-dot" />
                <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse-dot" style={{ animationDelay: "0.2s" }} />
                <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse-dot" style={{ animationDelay: "0.4s" }} />
              </div>
            </div>
          )}
        </div>

        {!isUser && message.report && !message.isStreaming && (
          <div className="mt-2 space-y-2">
            <div className="flex items-center gap-3 text-[11px] text-gray-500 px-1">
              <span className="font-medium">已选 {message.report.recommended_parts?.length || 0} 款</span>
              <span>证据 {message.report.evidence_count || 0} 条</span>
              <span>耗时 {formatElapsed(message.report.elapsed_s || 0)}</span>
              <button
                onClick={() => setShowReport(!showReport)}
                className="text-brand-600 hover:text-brand-800 font-medium ml-auto"
              >
                {showReport ? "收起报告" : "查看报告"}
              </button>
            </div>

            {showReport && message.report && (
              <div className="animate-fade-in">
                <ReportCard report={message.report} />
                {message.report.constraints?.topology && (
                  <SchematicPanel
                    topology={message.report.constraints.topology}
                    vin={message.report.constraints.input_voltage_nominal_v || 12}
                    vout={message.report.constraints.output_voltage_v || 5}
                    iout={message.report.constraints.output_current_a || 1}
                  />
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center shrink-0 mt-1">
          <span className="text-xs text-gray-600 font-medium">U</span>
        </div>
      )}
    </div>
  );
}
