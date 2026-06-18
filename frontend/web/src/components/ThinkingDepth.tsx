"use client";

import { useState, useEffect } from "react";
import { Layers, Zap, Brain, Telescope } from "lucide-react";

export type ThinkingLevel = "off" | "default" | "contemplation" | "exhaustive";

const LEVELS: { key: ThinkingLevel; label: string; desc: string; icon: typeof Layers }[] = [
  { key: "off",            label: "关闭",    desc: "直接回复，不展开推理",              icon: Zap },
  { key: "default",        label: "默认",    desc: "基础分步推理",                      icon: Layers },
  { key: "contemplation",  label: "沉思",    desc: "详细链式推理，多角度验证",          icon: Brain },
  { key: "exhaustive",     label: "穷究",    desc: "穷尽分析 + 自检修正，最高深度",    icon: Telescope },
];

const STORAGE_KEY = "ezmanbo_thinking_depth";

export function getThinkingDepth(): ThinkingLevel {
  if (typeof window === "undefined") return "default";
  return (localStorage.getItem(STORAGE_KEY) as ThinkingLevel) || "default";
}

export function setThinkingDepth(level: ThinkingLevel) {
  localStorage.setItem(STORAGE_KEY, level);
}

export function ThinkingDepthPanel() {
  const [level, setLevel] = useState<ThinkingLevel>("default");

  useEffect(() => { setLevel(getThinkingDepth()); }, []);

  const handleChange = (l: ThinkingLevel) => {
    setLevel(l);
    setThinkingDepth(l);
  };

  return (
    <div className="p-4">
      <div className="flex items-center gap-2 mb-3">
        <Brain className="w-4 h-4 text-purple-600" />
        <span className="text-xs font-bold text-gray-700 uppercase tracking-wide">思考深度</span>
      </div>

      <div className="space-y-1">
        {LEVELS.map((l) => {
          const Icon = l.icon;
          const active = l.key === level;
          return (
            <button
              key={l.key}
              onClick={() => handleChange(l.key)}
              className={`w-full flex items-start gap-2 p-2 rounded-lg text-left transition-colors ${
                active
                  ? "bg-purple-50 border border-purple-200"
                  : "hover:bg-gray-50 border border-transparent"
              }`}
            >
              <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${active ? "text-purple-600" : "text-gray-400"}`} />
              <div className="flex-1 min-w-0">
                <div className={`text-xs font-medium ${active ? "text-purple-800" : "text-gray-700"}`}>
                  {l.label}
                </div>
                <div className="text-[10px] text-gray-400 mt-0.5">{l.desc}</div>
              </div>
              {active && (
                <div className="w-2 h-2 rounded-full bg-purple-500 mt-1.5 shrink-0" />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
