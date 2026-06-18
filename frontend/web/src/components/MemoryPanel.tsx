"use client";

import { useState, useEffect } from "react";
import { Brain, Plus, Trash2, Save } from "lucide-react";

interface MemoryEntry {
  id: string;
  text: string;
  createdAt: number;
}

const STORAGE_KEY = "ezplm_memory_entries";

function loadMemories(): MemoryEntry[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
  } catch { return []; }
}

function saveMemories(entries: MemoryEntry[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(entries));
}

export function MemoryPanel() {
  const [entries, setEntries] = useState<MemoryEntry[]>([]);
  const [newText, setNewText] = useState("");

  useEffect(() => { setEntries(loadMemories()); }, []);

  const add = () => {
    if (!newText.trim()) return;
    const entry: MemoryEntry = {
      id: Date.now().toString(36),
      text: newText.trim(),
      createdAt: Date.now(),
    };
    const updated = [entry, ...entries];
    setEntries(updated);
    saveMemories(updated);
    setNewText("");
  };

  const remove = (id: string) => {
    const updated = entries.filter((e) => e.id !== id);
    setEntries(updated);
    saveMemories(updated);
  };

  return (
    <div className="p-4">
      <div className="flex items-center gap-2 mb-3">
        <Brain className="w-4 h-4 text-purple-600" />
        <span className="text-xs font-bold text-gray-700 uppercase tracking-wide">思考沉淀</span>
      </div>

      {/* Input */}
      <div className="flex gap-2 mb-3">
        <input
          value={newText}
          onChange={(e) => setNewText(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && add()}
          placeholder="记录选型心得..."
          className="flex-1 text-xs px-2 py-1.5 rounded-lg border border-gray-200 focus:outline-none focus:ring-1 focus:ring-purple-400"
        />
        <button onClick={add} className="p-1.5 rounded-lg bg-purple-100 text-purple-600 hover:bg-purple-200 transition-colors">
          <Save className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Entries */}
      <div className="space-y-2 max-h-[300px] overflow-y-auto">
        {entries.map((e) => (
          <div key={e.id} className="group p-2 rounded-lg bg-purple-50 border border-purple-100 text-xs text-gray-700 flex items-start gap-2">
            <span className="flex-1">{e.text}</span>
            <button onClick={() => remove(e.id)} className="opacity-0 group-hover:opacity-100 p-0.5 hover:bg-red-100 rounded transition-all">
              <Trash2 className="w-3 h-3 text-gray-400 hover:text-red-500" />
            </button>
          </div>
        ))}
        {entries.length === 0 && (
          <p className="text-[10px] text-gray-400 text-center py-4">暂无沉淀记录</p>
        )}
      </div>
    </div>
  );
}
