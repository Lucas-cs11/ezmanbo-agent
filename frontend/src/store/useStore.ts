"use client";

import { create } from "zustand";

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: string;
}

export interface Session {
  id: string;
  title: string;
  timestamp: string;
  messages: Message[];
}

/* ── 选型报告 ── */
export interface PartItem {
  partNumber: string;
  manufacturer: string;
  description: string;
  score: number; // 0–100
  level: "HIGH" | "MEDIUM" | "LOW";
  params: Record<string, string>;
}

export interface SelectionReport {
  type: "selection";
  title: string;
  parts: PartItem[];
}

/* ── 风险评估报告 ── */
export interface RiskItem {
  id: string;
  category: string;
  level: "HIGH" | "MEDIUM" | "LOW";
  description: string;
  recommendation: string;
  confidence: number;
}

export interface RiskIR {
  type: "risk";
  title: string;
  risks: RiskItem[];
}

/* ── 替换建议报告 ── */
export interface ReplacementPair {
  originalPart: string;
  alternativePart: string;
  manufacturer: string;
  reason: string;
  paramDifferences: {
    param: string;
    original: string;
    alternative: string;
  }[];
}

export interface ReplacementReport {
  type: "replacement";
  title: string;
  replacements: ReplacementPair[];
}

export type ReportData = SelectionReport | RiskIR | ReplacementReport;

export interface ReportBundle {
  selection?: SelectionReport;
  risk?: RiskIR;
  replacement?: ReplacementReport;
}

interface StoreState {
  sessions: Session[];
  activeSessionId: string | null;
  streamingContent: string;
  isStreaming: boolean;
  streamComplete: boolean;
  streamDuration: number | null;
  reportBundle: ReportBundle | null;
  pdfUrl: string | null;
  pdfLoading: boolean;
  showPdfViewer: boolean;
  addSession: (session: Session) => void;
  deleteSession: (id: string) => void;
  setActiveSession: (id: string | null) => void;
  addMessage: (sessionId: string, message: Message) => void;
  setStreamingContent: (content: string) => void;
  appendStreamingContent: (chunk: string) => void;
  setStreaming: (value: boolean) => void;
  setStreamComplete: (value: boolean) => void;
  setStreamDuration: (duration: number | null) => void;
  setReportBundle: (bundle: ReportBundle | null) => void;
  setPdfUrl: (url: string | null) => void;
  setPdfLoading: (value: boolean) => void;
  setShowPdfViewer: (value: boolean) => void;
  getActiveSession: () => Session | undefined;
}

export const useStore = create<StoreState>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  streamingContent: "",
  isStreaming: false,
  streamComplete: false,
  streamDuration: null,
  reportBundle: null,
  pdfUrl: null,
  pdfLoading: false,
  showPdfViewer: false,

  addSession: (session) =>
    set((state) => ({
      sessions: [...state.sessions, session],
      activeSessionId: session.id,
    })),

  deleteSession: (id) =>
    set((state) => ({
      sessions: state.sessions.filter((s) => s.id !== id),
      activeSessionId:
        state.activeSessionId === id
          ? state.sessions.find((s) => s.id !== id)?.id ?? null
          : state.activeSessionId,
    })),

  setActiveSession: (id) => set({ activeSessionId: id }),

  addMessage: (sessionId, message) =>
    set((state) => ({
      sessions: state.sessions.map((s) =>
        s.id === sessionId
          ? { ...s, messages: [...s.messages, message] }
          : s
      ),
    })),

  setStreamingContent: (content) => set({ streamingContent: content }),
  appendStreamingContent: (chunk) =>
    set((state) => ({
      streamingContent: state.streamingContent + chunk,
    })),
  setStreaming: (value) => set({ isStreaming: value }),
  setStreamComplete: (value) => set({ streamComplete: value }),
  setStreamDuration: (duration) => set({ streamDuration: duration }),
  setReportBundle: (bundle) => set({ reportBundle: bundle }),
  setPdfUrl: (url) => set({ pdfUrl: url }),
  setPdfLoading: (value) => set({ pdfLoading: value }),
  setShowPdfViewer: (value) => set({ showPdfViewer: value }),

  getActiveSession: () => {
    const state = get();
    return state.sessions.find((s) => s.id === state.activeSessionId);
  },
}));