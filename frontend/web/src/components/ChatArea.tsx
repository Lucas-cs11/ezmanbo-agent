"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useChatStore, generateId } from "@/store/chat";
import { MessageBubble } from "@/components/MessageBubble";
import { PdfReportViewer } from "@/components/PdfReportViewer";
import { QuickPhrases } from "@/components/QuickPhrases";
import { ThinkingDepthPanel } from "@/components/ThinkingDepth";
import { FileUpload } from "@/components/FileUpload";
import { Send, Loader2, Slash, PanelLeftOpen, PanelLeftClose, PanelRightOpen, PanelRightClose, Brain, Upload, Zap } from "lucide-react";
import { getThinkingDepth } from "@/components/ThinkingDepth";
import { estimateConversationTokens, COMPACT_THRESHOLD } from "@/lib/tokenBudget";
import { buildSelectionContext } from "@/lib/utils";
import type { AnalysisReport } from "@/types";

interface SSEStage { stage: string; status: string; total?: number; }
interface SSEScore { index: number; total: number; part_number: string; total_score: number; recommendation_level?: string; }

/* ── Slash 命令注册 ─────────────────────────────── */
const SLASH_COMMANDS: Record<string, { desc: string; action: (ctx: CmdCtx) => void }> = {
  clear: {
    desc: "清空当前对话",
    action: ({ clearMessages }) => clearMessages(),
  },
  new: {
    desc: "创建新对话",
    action: ({ createSession }) => createSession(),
  },
  compact: {
    desc: "压缩对话生成摘要",
    action: ({ compact }) => compact(),
  },
  export: {
    desc: "下载 BOM Excel",
    action: () => {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
      fetch(`${API_BASE}/export/bom`, { method: "POST" })
        .then(r => r.blob())
        .then(blob => {
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url; a.download = "BOM.xlsx"; a.click();
          URL.revokeObjectURL(url);
        })
        .catch(() => {});
    },
  },
  risk: {
    desc: "查看风险评估报告",
    action: ({ showReport }) => showReport("risk"),
  },

  schematic: {
    desc: "显示应用电路图",
    action: ({ toggleSchematic }) => toggleSchematic(),
  },
  save: {
    desc: "导出对话为 Markdown",
    action: ({ exportChat }) => exportChat(),
  },
  replace: {
    desc: "查询替代器件 /replace <型号>",
    action: ({ replacePart }) => replacePart(),
  },
};
type CmdCtx = {
  clearMessages: () => void;
  createSession: () => void;
  compact: () => void;
  showReport: (t: "bom" | "risk") => void;
  toggleSchematic: () => void;
  exportChat: () => void;
  replacePart: () => void;
};

/* ── 阶段映射（含百分比估算）────────────────────── */
const STAGE_INFO: Record<string, { label: string; pct: number }> = {
  parse:    { label: "解析需求", pct: 10 },
  search:   { label: "检索器件库", pct: 25 },
  score:    { label: "评分中", pct: 55 },
  evidence: { label: "构建证据链", pct: 75 },
  risk:     { label: "风险评估", pct: 90 },
  report:   { label: "生成报告", pct: 98 },
};

/* ══════════════════════════════════════════════════════════════ */

export function ChatArea({ leftOpen, rightOpen, onToggleLeft, onToggleRight }: {
  leftOpen: boolean; rightOpen: boolean;
  onToggleLeft: () => void; onToggleRight: () => void;
}) {
  const { activeSession, addMessage, updateMessage, setStreaming, createSession, setSessionTitle, healthStatus, setHealthStatus } = useChatStore();
  const session = activeSession();
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [stage, setStage] = useState("");
  const [progress, setProgress] = useState({ current: 0, total: 0, pct: 0 });
  const [showCmdMenu, setShowCmdMenu] = useState(false);
  const [compactResult, setCompactResult] = useState<string | null>(null);
  const [activeReport, setActiveReport] = useState<"bom" | "risk" | null>(null);
  const [currentIntent, setCurrentIntent] = useState<"selection" | "chat" | "adjustment" | "clarify" | null>(null);
  const [showThinking, setShowThinking] = useState(false);
  const [showUpload, setShowUpload] = useState(false);
  const [accumulatedInput, setAccumulatedInput] = useState("");  // 跨轮累积的约束文本
  const bottomRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const streamingMsgId = useRef<string | null>(null);
  const inputTextRef = useRef("");  // 同步最新输入值，供 slash command 读取参数

  // ── 派生：当前会话是否有活跃选型结果 ──────────────
  const hasActiveSelection = session?.messages.some(
    (m) => m.role === "assistant" && m.report && !m.isStreaming
  ) ?? false;

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [session?.messages]);

  // ── 后端连接健康检查（10s 轮询，15s 超时）──────────────────
  useEffect(() => {
    const checkHealth = async () => {
      const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
      setHealthStatus("checking");
      try {
        const resp = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(15000) });
        setHealthStatus(resp.ok ? "connected" : "disconnected");
      } catch {
        setHealthStatus("disconnected");
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 10000);
    return () => clearInterval(interval);
  }, [setHealthStatus]);

  /* ── 快速短语 ────────────────────────────────── */
  const handleQuickPhrase = (phrase: string) => setInput(phrase);

  /* ── Slash 命令 ────────────────────────────────── */
  const handleCmd = useCallback((cmd: string) => {
    const ctx: CmdCtx = {
      clearMessages: () => {
        if (session) {
          session.messages.forEach((m) => {
            updateMessage(m.id, { content: "", report: undefined });
          });
        }
        // Actually remove messages: use store actions
        useChatStore.setState((s) => ({
          sessions: s.sessions.map((ss) =>
            ss.id === s.activeSessionId ? { ...ss, messages: [] } : ss
          ),
        }));
      },
      createSession,
      compact: async () => {
        if (!session || session.messages.length < 2) return;
        const summary = session.messages.map((m) =>
          `[${m.role}]: ${m.content.slice(0, 200)}`
        ).join("\n");
        const aid = generateId();
        addMessage({ id: aid, role: "assistant", content: "", timestamp: Date.now() });
        const _API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
        try {
          const resp = await fetch(`${_API}/agent/chat`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              user_input: `请将以下对话历史压缩为一段简洁摘要（不超过200字），保留关键器件型号和参数：\n${summary}`,
              session_id: session?.id,
            }),
          });
          const data = await resp.json();
          const text = data.response || data.output || JSON.stringify(data);
          updateMessage(aid, { content: `**对话摘要**\n\n${text}` });
          setCompactResult(text);
        } catch {
          updateMessage(aid, { content: "压缩失败" });
        }
      },
      showReport: (t) => setActiveReport(t),
      toggleSchematic: () => setActiveReport(null),
      replacePart: async () => {
        const fullCmd = inputTextRef.current.trim();
        const mpn = fullCmd.replace(/^\/replace\s+/i, "").trim();
        if (!mpn) return;
        const API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
        const aid = generateId();
        addMessage({ id: aid, role: "assistant", content: `正在查询 \`${mpn}\` 的替代器件...`, timestamp: Date.now(), isStreaming: true });
        try {
          const resp = await fetch(`${API}/replacement`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ original_part_number: mpn }),
          });
          if (!resp.ok) {
            const err = await resp.json().catch(() => ({}));
            updateMessage(aid, { content: `> 替代料查询失败: ${err.detail || resp.statusText}`, isStreaming: false });
            return;
          }
          const data = await resp.json();
          const lines: string[] = [
            `**替代料查询: \`${mpn}\`**`,
            "",
          ];
          const orig = data.original_part;
          if (orig) {
            const oPn = orig.part_number || "?";
            const oMfr = orig.manufacturer || "未知厂商";
            const oCat = orig.category || "";
            lines.push(`**原器件**: \`${oPn}\` — ${oMfr}${oCat ? " | " + oCat : ""}`);
            if (orig.description) lines.push(`> ${(orig.description as string).slice(0, 150)}`);
            lines.push("");
          }
          const candidates = data.replacement_candidates || [];
          lines.push(`**兼容性**: ${data.compatibility_level || "?"}`);
          lines.push("");
          if (candidates.length === 0) {
            lines.push("> 未找到替代器件。");
          } else {
            lines.push(`共 **${candidates.length}** 款替代候选：`);
            lines.push("");
            candidates.forEach((c: any, i: number) => {
              const p = c.part || {};
              const s = c.score || {};
              const pn = p.part_number || "?";
              const mfr = p.manufacturer || "—";
              const score = Math.round(s.total_score || 0);
              const level = c.recommendation_level || "—";
              lines.push(`**#${i + 1}** \`${pn}\` — ${mfr} | 综合 **${score}** 分 | ${level}`);
            });
          }
          lines.push("");
          if (data.comparison_summary) {
            lines.push(`> ${data.comparison_summary}`);
          }
          updateMessage(aid, { content: lines.join("\n"), isStreaming: false });
        } catch (err: unknown) {
          const msg = err instanceof Error ? err.message : "Unknown";
          updateMessage(aid, { content: `> 替代料查询失败: ${msg}`, isStreaming: false });
        }
      },
      exportChat: () => {
        if (!session || session.messages.length === 0) return;
        const title = session.messages.find(m => m.role === "user")?.content?.slice(0, 60) || "对话记录";
        const date = new Date().toISOString().slice(0, 10);
        const lines: string[] = [
          `# ${title}`,
          "",
          `> 导出时间：${new Date().toLocaleString("zh-CN")}`,
          `> 生成工具：eZmanbo / eZ-PLM Agent`,
          "",
        ];
        for (const m of session.messages) {
          if (m.role === "user") {
            lines.push(`> ${m.content}`);
            lines.push("");
          } else {
            if (m.report) {
              lines.push(`*[选型完成 · ${m.report.recommended_parts?.length || 0} 款推荐 · ${m.report.risks?.overall_risk_level?.toUpperCase() || "?"} 风险]*`);
              lines.push("");
            }
            lines.push(m.content);
            lines.push("");
            lines.push("---");
            lines.push("");
          }
        }
        const md = lines.join("\n");
        const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `eZmanbo_${date}_${title.slice(0, 20).replace(/[/\\?%*:|"<>]/g, "_")}.md`;
        a.click();
        URL.revokeObjectURL(url);
      },
    };
    if (SLASH_COMMANDS[cmd]) {
      SLASH_COMMANDS[cmd].action(ctx);
    }
    setInput("");
    setShowCmdMenu(false);
  }, [session, addMessage, updateMessage, createSession]);

  /* ── 检测 / 命令 (onKeyDown 确保即时响应) ─────── */
  const handleKeyDownIntercept = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // 先处理 slash 菜单的键盘导航
    if (showCmdMenu) {
      if (e.key === "Escape") {
        e.preventDefault();
        setShowCmdMenu(false);
        return;
      }
      if (e.key === "Enter" && !e.shiftKey) {
        // 如果有筛选结果，选择第一个
        const cmds = Object.entries(SLASH_COMMANDS).filter(
          ([k]) => k.startsWith(input.slice(1).split(" ")[0].toLowerCase())
        );
        if (cmds.length > 0) {
          e.preventDefault();
          handleCmd(cmds[0][0]);
          return;
        }
      }
    }

    // Enter 发送
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInputChange = (val: string) => {
    setInput(val);
    inputTextRef.current = val;
    setShowCmdMenu(val.startsWith("/"));
  };

  /* ── SSE 流式接收器（共享） ────────────────────── */
  const consumeSelectionStream = async (aid: string, resp: Response) => {
    const reader = resp.body?.getReader();
    if (!reader) throw new Error("No stream");
    const decoder = new TextDecoder();
    let buffer = "", fullText = "", thinkingText = "", thinkingDone = false;
    const report: Partial<AnalysisReport> = {};

    try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      let ce = "";
      for (const line of lines) {
        if (line.startsWith("event:")) { ce = line.slice(6).trim(); continue; }
        if (!line.startsWith("data:")) continue;
        try {
          const d = JSON.parse(line.slice(5));
          if (ce === "thinking_delta") {
            thinkingText += (d.text || "") + "\n";
            updateMessage(aid, { thinking: thinkingText });
          } else if (ce === "stage") {
            const s = d as SSEStage;
            setStage(s.stage);
            const info = STAGE_INFO[s.stage] || { label: s.stage, pct: 50 };
            if (s.total) setProgress({ current: 0, total: s.total, pct: info.pct });
            else setProgress((p) => ({ ...p, pct: info.pct }));
          } else if (ce === "score_update") {
            const su = d as SSEScore;
            const pct = su.total > 0 ? Math.round(25 + (su.index / su.total) * 35) : 55;
            setProgress({ current: su.index, total: su.total, pct });
            const line = `- \`${su.part_number}\` — **${su.total_score}** _${su.recommendation_level || ""}_\n`;
            fullText += line;
            // 首条正文到来时标记思考完成
            if (!thinkingDone && thinkingText) {
              thinkingDone = true;
              updateMessage(aid, { content: fullText, thinkingDone: true });
            } else {
              updateMessage(aid, { content: fullText });
            }
          } else if (ce === "text_delta") {
            if (!thinkingDone && thinkingText) {
              thinkingDone = true;
              updateMessage(aid, { thinkingDone: true });
            }
            fullText += (d.text || "") + "\n";
            updateMessage(aid, { content: fullText });
          } else if (ce === "parse_done") {
            if (d.constraints) report.constraints = d.constraints;
          } else if (ce === "risk_done") {
            report.risks = d;
          } else if (ce === "evidence_done") {
            report.evidence_count = d.evidence_count;
            report.avg_confidence = d.avg_confidence;
            if (d.evidence_items) report.evidence_items = d.evidence_items;
          } else if (ce === "done") {
            report.elapsed_s = d.elapsed_s;
            report.request_id = d.request_id;
            if (d.summary) report.summary = d.summary;
            // 提取选型标题（≤10字）
            if (report.constraints) {
              const c = report.constraints;
              const parts: string[] = [];
              if (c.topology) parts.push(c.topology === "buck" ? "Buck" : c.topology === "boost" ? "Boost" : c.topology === "ldo" ? "LDO" : c.topology);
              if (c.output_voltage_v) parts.push(`${c.output_voltage_v}V`);
              if (c.output_current_a) parts.push(`${c.output_current_a}A`);
              const title = parts.join(" ") + " 选型";
              if (title.length <= 12 && session) {
                setSessionTitle(session.id, title);
              }
            }
          } else if (ce === "error") {
            const errMsg = d.message || d.detail || "服务器内部错误";
            updateMessage(aid, { content: `> ⚠️ 分析失败：${errMsg}`, isStreaming: false });
            setStreaming(aid, false);
            return;
          }
        } catch { /* skip */ }
        ce = "";
      }
    }
    updateMessage(aid, { content: fullText, report: report as AnalysisReport, isStreaming: false, thinkingDone: true });

    // ── 选型完成后将上下文注入后端 Agent 会话 ────────
    if (session && (report as AnalysisReport).constraints) {
      const _API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
      fetch(`${_API}/agent/init_session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: session.id,
          context_type: "selection_context",
          context: buildSelectionContext(report as AnalysisReport),
        }),
      }).catch(() => {});
    }
    } catch (_streamErr) {
      // M6: 连接中断时保留已接收内容并提示重发
      const retained = fullText ? fullText + "\n\n> ⚠️ 连接中断，请点击重新发送" : "> ⚠️ 连接中断，请点击重新发送";
      updateMessage(aid, { content: retained, report: Object.keys(report).length > 0 ? (report as AnalysisReport) : undefined, isStreaming: false, thinkingDone: true });
      setProgress((p) => ({ ...p, pct: 0 }));
    }
  };

  const consumeChatStream = async (aid: string, resp: Response) => {
    const reader = resp.body?.getReader();
    if (!reader) throw new Error("No stream");
    const decoder = new TextDecoder();
    let buffer = "", fullText = "", thinkingText = "";
    try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";
      let ce = "";
      for (const line of lines) {
        if (line.startsWith("event:")) { ce = line.slice(6).trim(); continue; }
        if (!line.startsWith("data:")) continue;
        try {
          const d = JSON.parse(line.slice(5));
          if (ce === "thinking_delta") {
            thinkingText += (d.text || "") + "\n";
            updateMessage(aid, { thinking: thinkingText });
          } else if (ce === "text_delta" || ce === "start") {
            if (ce === "text_delta" && thinkingText && !fullText) {
              // 首条正文到来 → 标记思考完成
              updateMessage(aid, { thinkingDone: true });
            }
            fullText += (d.text || "") + "\n";
            updateMessage(aid, { content: fullText });
          } else if (ce === "done") {
            if (d.text) fullText = d.text;
          } else if (ce === "error") {
            const errMsg = d.message || d.detail || "服务器内部错误";
            updateMessage(aid, { content: `> ⚠️ ${errMsg}`, isStreaming: false });
            setStreaming(aid, false);
            return;
          }
        } catch { /* skip */ }
        ce = "";
      }
    }
    updateMessage(aid, { content: fullText || "已处理", isStreaming: false, thinkingDone: true });
    } catch (_streamErr) {
      // M6: 连接中断时保留已接收内容并提示重发
      const retained = fullText ? fullText + "\n\n> ⚠️ 连接中断，请点击重新发送" : "> ⚠️ 连接中断，请点击重新发送";
      updateMessage(aid, { content: retained, isStreaming: false, thinkingDone: true });
    }
  };

  /* ── 发送消息 + 意图分流 ──────────────────────── */
  const handleSend = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;
    setInput("");
    setLoading(true);
    setStage("");
    setProgress({ current: 0, total: 0, pct: 0 });
    setActiveReport(null);

    // Slash command?
    if (text.startsWith("/")) {
      const cmd = text.slice(1).split(" ")[0].toLowerCase();
      if (SLASH_COMMANDS[cmd]) {
        handleCmd(cmd);
        setLoading(false);
        return;
      }
    }

    // ── Auto-compact: token 预算检查 ──────────────────
    const msgs = (session?.messages || []).map(m => ({ role: m.role, content: m.content }));
    const estimatedTokens = estimateConversationTokens(msgs);
    if (estimatedTokens > COMPACT_THRESHOLD && session) {
      // 自动压缩：调用 LLM 摘要
      const compactId = generateId();
      addMessage({ id: compactId, role: "assistant", content: "对话较长，自动压缩上下文中...", timestamp: Date.now(), isStreaming: false });
      const _COMPACT_API = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
      try {
        const compactResp = await fetch(`${_COMPACT_API}/agent/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_input: `总结以下对话的关键信息（器件型号、参数、约束），不超过150字：\n${msgs.slice(-10).map(m => `[${m.role}]: ${m.content.slice(0, 200)}`).join("\n")}`,
            session_id: useChatStore.getState().activeSessionId,
          }),
        });
        const compactData = await compactResp.json();
        const compactText = compactData.response || compactData.output || "";
        // 清理旧消息，仅保留压缩摘要 + 最近 2 轮
        if (session.messages.length > 6) {
          const recentMsgs = session.messages.slice(-4);
          useChatStore.setState((s) => ({
            sessions: s.sessions.map((ss) =>
              ss.id === s.activeSessionId
                ? { ...ss, messages: [{ id: compactId, role: "assistant", content: `上下文已压缩：\n${compactText}`, timestamp: Date.now() }, ...recentMsgs] }
                : ss
            ),
          }));
        }
      } catch { /* non-critical */ }
    }

    const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
    const aid = generateId();
    const uid = generateId();
    streamingMsgId.current = aid;
    addMessage({ id: uid, role: "user", content: text, timestamp: Date.now() });
    addMessage({ id: aid, role: "assistant", content: "", timestamp: Date.now(), isStreaming: true });
    setStreaming(aid, true);

    try {
      // ── Step 1: 意图分类 ──────────────────────────
      const clsResp = await fetch(`${API_BASE}/classify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_input: text, has_active_selection: hasActiveSelection, accumulated_input: accumulatedInput, thinking_depth: getThinkingDepth(), session_id: useChatStore.getState().activeSessionId }),
      });
      const cls = await clsResp.json();
      const intent: string = cls.intent || "chat";
      setCurrentIntent(intent as "selection" | "chat" | "adjustment" | "clarify");

      // ── Step 2: 按意图路由 ─────────────────────────
      if (intent === "clarify") {
        // 约束不完整 → 显示追问，累积上下文
        const clarifyText = cls.clarify_response || "请提供更完整的器件参数信息。";
        setAccumulatedInput(prev => prev ? `${prev}; ${text}` : text);
        updateMessage(aid, { content: clarifyText, isStreaming: false });
        setStreaming(aid, false);
        // 同时发送到 agent 保存会话上下文（fire-and-forget）
        fetch(`${API_BASE}/agent/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_input: text, session_id: useChatStore.getState().activeSessionId }),
        }).catch(() => {});
        setLoading(false);
        setCurrentIntent(null);
        streamingMsgId.current = null;
        return;
      }

      if (intent === "selection" || intent === "adjustment") {
        // 选型 or 调整 → 合并累积上下文后触发完整流水线
        const adjMsg = intent === "adjustment" ? "检测到调整意图，重新选型中...\n\n" : "";
        updateMessage(aid, { content: adjMsg });

        // 合并累积的约束上下文（优先用后端 merged_input）
        let fetchInput = cls.merged_input || (accumulatedInput ? `${accumulatedInput}; ${text}` : text);
        setAccumulatedInput("");  // 选型触发后清空累积
        if (intent === "adjustment" && cls.adjustments) {
          fetchInput = text;
        }

        const resp = await fetch(`${API_BASE}/analyze/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_input: fetchInput, thinking_depth: getThinkingDepth(), session_id: useChatStore.getState().activeSessionId }),
        });
        await consumeSelectionStream(aid, resp);

      } else {
        // 纯对话 → ReAct Agent
        updateMessage(aid, { content: "" });
        const resp = await fetch(`${API_BASE}/agent/chat/stream`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ user_input: text, thinking_depth: getThinkingDepth(), session_id: useChatStore.getState().activeSessionId }),
        });
        await consumeChatStream(aid, resp);
      }

      setStreaming(aid, false);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Unknown error";
      updateMessage(aid, { content: `> 连接失败: ${msg}`, isStreaming: false });
      setStreaming(aid, false);
    }
    setLoading(false);
    setStage("");
    setCurrentIntent(null);
    streamingMsgId.current = null;
  }, [input, loading, session, accumulatedInput, setAccumulatedInput, addMessage, updateMessage, setStreaming, setSessionTitle, handleCmd, hasActiveSelection]);

  return (
    <main className="flex-1 flex flex-col min-w-0 bg-white">
      {/* Toolbar — sidebar toggles + token budget */}
      <div className="flex items-center justify-between px-3 py-1.5 border-b border-gray-100 bg-gray-50">
        <div className="flex items-center gap-2">
          <button onClick={onToggleLeft} className="p-1 rounded hover:bg-gray-200 transition-colors" title={leftOpen ? "收起侧栏" : "展开侧栏"}>
            {leftOpen ? <PanelLeftClose className="w-4 h-4 text-gray-500" /> : <PanelLeftOpen className="w-4 h-4 text-gray-500" />}
          </button>
          <span className="text-[10px] text-gray-400 select-none">eZmanbo</span>
          {(() => {
            const msgs = (session?.messages || []).map(m => ({ role: m.role, content: m.content }));
            const tokens = estimateConversationTokens(msgs);
            return (
              <span className={`text-[9px] font-mono ${tokens > COMPACT_THRESHOLD ? 'text-amber-600' : 'text-gray-400'}`}>
                ~{tokens}t
              </span>
            );
          })()}
        </div>
        <div className="flex items-center gap-2">
          {/* Health indicator */}
          <span
            className="inline-flex items-center gap-1"
            title={
              healthStatus === "connected"
                ? "服务已连接"
                : healthStatus === "disconnected"
                ? "后端服务未连接，请确认已启动 Python 服务"
                : "正在检查连接状态..."
            }
          >
            <span
              className={`w-2 h-2 rounded-full shrink-0 ${
                healthStatus === "connected"
                  ? "bg-green-500"
                  : healthStatus === "disconnected"
                  ? "bg-red-500"
                  : "bg-yellow-400 animate-pulse"
              }`}
            />
            {healthStatus === "disconnected" && (
              <span className="text-[9px] text-red-400 hidden sm:inline">离线</span>
            )}
          </span>
          <button onClick={onToggleRight} className="p-1 rounded hover:bg-gray-200 transition-colors" title={rightOpen ? "收起面板" : "展开面板"}>
            {rightOpen ? <PanelRightClose className="w-4 h-4 text-gray-500" /> : <PanelRightOpen className="w-4 h-4 text-gray-500" />}
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {session?.messages.map((m) => (
          <div key={m.id}>
            <MessageBubble message={m} progress={m.id === streamingMsgId.current ? progress : undefined} />
            {m.report && !m.isStreaming && m.id === session.messages.filter((x) => x.role === "assistant" && x.report).pop()?.id && (
              <div className="ml-11 mt-2 animate-fade-in">
                {activeReport && <PdfReportViewer reportType={activeReport} />}
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="border-t border-gray-200 p-4 bg-white relative">
        {/* Slash command menu */}
        {showCmdMenu && (
          <div className="absolute bottom-full left-0 right-0 mx-4 mb-2 p-2 bg-white border border-gray-200 rounded-xl shadow-xl z-50 animate-fade-in">
            {Object.entries(SLASH_COMMANDS)
              .filter(([k]) => k.startsWith(input.slice(1).split(" ")[0].toLowerCase()))
              .map(([k, v]) => (
                <button key={k} onClick={() => handleCmd(k)} className="w-full flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-brand-50 text-sm transition-colors">
                  <Slash className="w-4 h-4 text-brand-500" />
                  <span className="font-mono text-brand-700">/{k}</span>
                  <span className="text-gray-500 text-xs ml-auto">{v.desc}</span>
                </button>
              ))}
          </div>
        )}

        {/* Thinking popover */}
        {showThinking && (
          <div className="absolute bottom-full left-16 mb-2 w-64 bg-white border border-gray-200 rounded-xl shadow-xl z-50 p-3 animate-fade-in">
            <ThinkingDepthPanel />
          </div>
        )}
        {/* Upload popover */}
        {showUpload && (
          <div className="absolute bottom-full left-28 mb-2 w-72 bg-white border border-gray-200 rounded-xl shadow-xl z-50 p-3 animate-fade-in">
            <FileUpload />
          </div>
        )}

        {/* Action buttons row */}
        <div className="max-w-3xl mx-auto flex items-center gap-1.5 mb-2">
          <QuickPhrases onSelect={handleQuickPhrase} />
          <button
            onClick={() => { setShowThinking(!showThinking); setShowUpload(false); }}
            className={`flex items-center gap-1 px-2 py-1 rounded-full text-[10px] transition-colors ${showThinking ? "bg-purple-100 text-purple-700" : "bg-gray-100 text-gray-600 hover:bg-purple-50 hover:text-purple-600"}`}
          >
            <Brain className="w-3 h-3" /> 思考
          </button>
          <button
            onClick={() => { setShowUpload(!showUpload); setShowThinking(false); }}
            className={`flex items-center gap-1 px-2 py-1 rounded-full text-[10px] transition-colors ${showUpload ? "bg-blue-100 text-blue-700" : "bg-gray-100 text-gray-600 hover:bg-blue-50 hover:text-blue-600"}`}
          >
            <Upload className="w-3 h-3" /> 上传
          </button>
        </div>

        {/* Text input */}
        <div className="max-w-3xl mx-auto flex gap-3 items-end">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => handleInputChange(e.target.value)}
            onKeyDown={handleKeyDownIntercept}
            placeholder="输入选型需求，或输入 / 查看命令..."
            rows={2}
            className="flex-1 resize-none rounded-xl border border-gray-300 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 focus:border-transparent placeholder:text-gray-400"
            disabled={loading}
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="shrink-0 w-10 h-10 rounded-xl bg-brand-700 text-white flex items-center justify-center hover:bg-brand-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
          </button>
        </div>
        <p className="text-[10px] text-gray-400 text-center mt-2">
          Enter 发送 · Shift+Enter 换行 · 输入 / 使用命令
        </p>
      </div>
    </main>
  );
}
