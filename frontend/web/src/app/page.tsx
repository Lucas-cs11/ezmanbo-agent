"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import { useChatStore } from "@/store/chat";
import { Sidebar } from "@/components/Sidebar";
import { ChatArea } from "@/components/ChatArea";
import { DetailPanel } from "@/components/DetailPanel";

export default function Home() {
  const { sessions, createSession, hydrate } = useChatStore();
  const initialized = useRef(false);
  const [leftOpen, setLeftOpen] = useState(true);
  const [rightOpen, setRightOpen] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    if (!initialized.current) {
      hydrate();
      initialized.current = true;
    }
  }, []);

  useEffect(() => {
    if (!mounted || !initialized.current) return;
    if (sessions.length === 0) {
      createSession();
    }
  }, [mounted, sessions.length, createSession]);

  const toggleLeft = useCallback(() => setLeftOpen(v => !v), []);
  const toggleRight = useCallback(() => setRightOpen(v => !v), []);

  return (
    <div className="flex h-screen">
      {leftOpen && <Sidebar />}
      <ChatArea
        leftOpen={leftOpen} rightOpen={rightOpen}
        onToggleLeft={toggleLeft} onToggleRight={toggleRight}
      />
      {rightOpen && <DetailPanel />}
    </div>
  );
}
