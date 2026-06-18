"use client";

import { useState, useEffect, useRef } from "react";
import { Zap, Plus, X, Edit3, Check } from "lucide-react";

interface Phrase {
  id: string;
  label: string;
  template: string;   // e.g. "[Vin]V转[Vout]V, [Iout]A, [Grade]"
}

const STORAGE_KEY = "ezplm_quick_phrases";

const DEFAULT_PHRASES: Phrase[] = [
  { id: "1", label: "Buck Step-Down",  template: "[12]V转[5]V, [3]A, Buck降压, [车规级], [-40]~[125]C" },
  { id: "2", label: "LDO Low-Power",   template: "[5]V转[3.3]V LDO, 输出[500]mA, [工业级], [SOT-23]" },
  { id: "3", label: "Boost Step-Up",   template: "[3.3]V升压到[5]V, [2]A, Boost, [非车规]" },
  { id: "4", label: "Buck Domestic",   template: "[24]V转[12]V Buck, [5]A, [工业级], [优先国产器件]" },
];

function loadPhrases(): Phrase[] {
  if (typeof window === "undefined") return DEFAULT_PHRASES;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : DEFAULT_PHRASES;
  } catch { return DEFAULT_PHRASES; }
}

function savePhrases(items: Phrase[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(items));
}

export function QuickPhrases({ onSelect }: { onSelect: (text: string) => void }) {
  const [open, setOpen] = useState(false);
  const [phrases, setPhrases] = useState<Phrase[]>([]);
  const [editing, setEditing] = useState<string | null>(null);
  const [editLabel, setEditLabel] = useState("");
  const [editTemplate, setEditTemplate] = useState("");
  const [adding, setAdding] = useState(false);
  const [newLabel, setNewLabel] = useState("");
  const [newTemplate, setNewTemplate] = useState("");
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => { setPhrases(loadPhrases()); }, []);

  // 点击外部关闭
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    if (open) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const handleSelect = (tpl: string) => {
    onSelect(tpl);
    setOpen(false);
  };

  const startEdit = (p: Phrase) => {
    setEditing(p.id);
    setEditLabel(p.label);
    setEditTemplate(p.template);
  };

  const saveEdit = () => {
    const updated = phrases.map((p) =>
      p.id === editing ? { ...p, label: editLabel.trim() || p.label, template: editTemplate.trim() || p.template } : p
    );
    setPhrases(updated);
    savePhrases(updated);
    setEditing(null);
  };

  const deletePhrase = (id: string) => {
    const updated = phrases.filter((p) => p.id !== id);
    setPhrases(updated);
    savePhrases(updated);
  };

  const addPhrase = () => {
    if (!newLabel.trim() || !newTemplate.trim()) return;
    const p: Phrase = {
      id: Date.now().toString(36),
      label: newLabel.trim(),
      template: newTemplate.trim(),
    };
    const updated = [...phrases, p];
    setPhrases(updated);
    savePhrases(updated);
    setAdding(false);
    setNewLabel("");
    setNewTemplate("");
  };

  return (
    <div className="relative" ref={ref}>
      {/* Trigger button */}
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-gray-100 hover:bg-brand-50 hover:text-brand-700 text-[10px] text-gray-600 transition-colors"
      >
        <Zap className="w-3 h-3 text-amber-500" />
        <span>模板</span>
      </button>

      {/* Dropdown */}
      {open && (
        <div className="absolute bottom-full left-0 mb-2 w-96 bg-white border border-gray-200 rounded-xl shadow-xl z-50 animate-slide-up overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-3 py-2 bg-gray-50 border-b border-gray-100">
            <span className="text-xs font-semibold text-gray-600">快捷模板</span>
            <button
              onClick={() => setAdding(true)}
              className="flex items-center gap-1 text-[10px] text-brand-600 hover:text-brand-800"
            >
              <Plus className="w-3 h-3" /> 新增
            </button>
          </div>

          {/* List */}
          <div className="max-h-[280px] overflow-y-auto p-2 space-y-1">
            {phrases.map((p) => (
              <div key={p.id} className="group flex items-start gap-2 p-2 rounded-lg hover:bg-gray-50 transition-colors">
                {editing === p.id ? (
                  <div className="flex-1 space-y-1">
                    <input
                      value={editLabel}
                      onChange={(e) => setEditLabel(e.target.value)}
                      className="w-full text-xs px-2 py-1 rounded border border-gray-200 focus:outline-none focus:ring-1 focus:ring-brand-400"
                      placeholder="Label"
                    />
                    <input
                      value={editTemplate}
                      onChange={(e) => setEditTemplate(e.target.value)}
                      className="w-full text-[10px] font-mono px-2 py-1 rounded border border-gray-200 focus:outline-none focus:ring-1 focus:ring-brand-400"
                      placeholder="Template: [Vin]V转[Vout]V, [Iout]A"
                    />
                    <div className="flex gap-1">
                      <button onClick={saveEdit} className="text-[10px] px-2 py-0.5 rounded bg-brand-600 text-white">保存</button>
                      <button onClick={() => setEditing(null)} className="text-[10px] px-2 py-0.5 rounded bg-gray-200 text-gray-600">取消</button>
                    </div>
                  </div>
                ) : (
                  <>
                    <button
                      onClick={() => handleSelect(p.template)}
                      className="flex-1 text-left"
                    >
                      <div className="text-xs font-medium text-gray-800">{p.label}</div>
                      <div className="text-[10px] font-mono text-gray-400 mt-0.5 truncate">{p.template}</div>
                    </button>
                    <div className="opacity-0 group-hover:opacity-100 flex gap-0.5 transition-opacity">
                      <button onClick={() => startEdit(p)} className="p-0.5 hover:bg-gray-200 rounded">
                        <Edit3 className="w-3 h-3 text-gray-400" />
                      </button>
                      <button onClick={() => deletePhrase(p.id)} className="p-0.5 hover:bg-red-100 rounded">
                        <X className="w-3 h-3 text-gray-400 hover:text-red-500" />
                      </button>
                    </div>
                  </>
                )}
              </div>
            ))}

            {/* Add new form */}
            {adding && (
              <div className="p-2 border-t border-gray-100 space-y-1">
                <input
                  value={newLabel}
                  onChange={(e) => setNewLabel(e.target.value)}
                  placeholder="Label (e.g. Buck 12V)"
                  className="w-full text-xs px-2 py-1 rounded border border-gray-200 focus:outline-none focus:ring-1 focus:ring-brand-400"
                />
                <input
                  value={newTemplate}
                  onChange={(e) => setNewTemplate(e.target.value)}
                  placeholder="Template: [12]V转[5]V, [3]A, [车规级]"
                  className="w-full text-[10px] font-mono px-2 py-1 rounded border border-gray-200 focus:outline-none focus:ring-1 focus:ring-brand-400"
                />
                <div className="flex gap-1">
                  <button onClick={addPhrase} className="text-[10px] px-2 py-0.5 rounded bg-brand-600 text-white">添加</button>
                  <button onClick={() => setAdding(false)} className="text-[10px] px-2 py-0.5 rounded bg-gray-200 text-gray-600">取消</button>
                </div>
              </div>
            )}
          </div>

          {/* Footer hint */}
          <div className="px-3 py-1.5 bg-gray-50 border-t border-gray-100 text-[9px] text-gray-400">
            Use <code className="text-brand-500">[value]</code> as placeholders. Click template to fill input.
          </div>
        </div>
      )}
    </div>
  );
}
