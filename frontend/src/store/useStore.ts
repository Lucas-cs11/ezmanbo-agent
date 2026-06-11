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

interface StoreState {
  sessions: Session[];
  activeSessionId: string | null;
  streamingContent: string;
  isStreaming: boolean;
  streamComplete: boolean;
  streamDuration: number | null;
  addSession: (session: Session) => void;
  deleteSession: (id: string) => void;
  setActiveSession: (id: string | null) => void;
  addMessage: (sessionId: string, message: Message) => void;
  setStreamingContent: (content: string) => void;
  appendStreamingContent: (chunk: string) => void;
  setStreaming: (value: boolean) => void;
  setStreamComplete: (value: boolean) => void;
  setStreamDuration: (duration: number | null) => void;
  getActiveSession: () => Session | undefined;
}

export const useStore = create<StoreState>((set, get) => ({
  sessions: [],
  activeSessionId: null,
  streamingContent: "",
  isStreaming: false,
  streamComplete: false,
  streamDuration: null,

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

  getActiveSession: () => {
    const state = get();
    return state.sessions.find((s) => s.id === state.activeSessionId);
  },
}));