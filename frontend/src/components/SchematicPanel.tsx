"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";

interface AnnotPoint {
  x: number;
  y: number;
  label: string;
  value: string;
  tooltip: string;
}

interface TopologyInfo {
  type: string;
  description: string;
  equations: { name: string; formula: string }[];
  params: Record<string, string>;
}

interface SchematicData {
  svg: string;
  annotations: AnnotPoint[];
  topology: TopologyInfo;
}

export function SchematicPanel() {
  const [data, setData] = useState<SchematicData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [scale, setScale] = useState(1);
  const [fullscreen, setFullscreen] = useState(false);
  const [hoveredAnnot, setHoveredAnnot] = useState<AnnotPoint | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const fetchSchematic = useCallback(async () => {
    setLoading(true);
    setError(null);
    const backendUrl =
      process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

    try {
      const res = await fetch(
        `${backendUrl}/schematic/buck?Vin=24&Vout=5&Iout=3`
      );
      if (res.ok) {
        const json = await res.json();
        setData(json);
      }
    } catch {
      // Mock data for demo
      setData({
        svg: `<svg viewBox="0 0 600 350" xmlns="http://www.w3.org/2000/svg">
  <rect x="50" y="130" width="80" height="50" rx="4" fill="#e8eaf6" stroke="#1a237e" stroke-width="2"/>
  <text x="90" y="160" text-anchor="middle" font-size="12" font-weight="bold" fill="#1a237e">Vin</text>
  <text x="90" y="175" text-anchor="middle" font-size="9" fill="#666">24V DC</text>

  <rect x="190" y="90" width="60" height="40" rx="4" fill="#fff3e0" stroke="#f57c00" stroke-width="2"/>
  <text x="220" y="114" text-anchor="middle" font-size="11" font-weight="bold" fill="#f57c00">SW</text>

  <circle cx="330" cy="110" r="22" fill="#e8f5e9" stroke="#2e7d32" stroke-width="2"/>
  <text x="330" y="106" text-anchor="middle" font-size="9" fill="#2e7d32">L1</text>
  <text x="330" y="118" text-anchor="middle" font-size="7" fill="#666">47µH</text>

  <rect x="410" y="85" width="60" height="45" rx="4" fill="#fce4ec" stroke="#c62828" stroke-width="2"/>
  <text x="440" y="103" text-anchor="middle" font-size="9" fill="#c62828">Cout</text>
  <text x="440" y="117" text-anchor="middle" font-size="7" fill="#666">220µF</text>

  <rect x="530" y="130" width="60" height="40" rx="4" fill="#e8eaf6" stroke="#1a237e" stroke-width="2"/>
  <text x="560" y="154" text-anchor="middle" font-size="11" font-weight="bold" fill="#1a237e">Vout</text>
  <text x="560" y="167" text-anchor="middle" font-size="8" fill="#666">5V/3A</text>

  <!-- D1 -->
  <path d="M320 160 L320 200 L310 200 L330 210 L350 200 L320 200" fill="none" stroke="#c62828" stroke-width="2"/>
  <text x="322" y="225" font-size="8" fill="#c62828">D1</text>
  <text x="322" y="237" font-size="7" fill="#666">SS34</text>

  <!-- R1, R2 -->
  <rect x="440" y="175" width="35" height="20" rx="2" fill="#f3e5f5" stroke="#7b1fa2" stroke-width="1.5"/>
  <text x="457" y="188" text-anchor="middle" font-size="7" fill="#7b1fa2">R1</text>
  <rect x="440" y="210" width="35" height="20" rx="2" fill="#f3e5f5" stroke="#7b1fa2" stroke-width="1.5"/>
  <text x="457" y="223" text-anchor="middle" font-size="7" fill="#7b1fa2">R2</text>

  <!-- wires -->
  <line x1="130" y1="155" x2="190" y2="110" stroke="#333" stroke-width="2"/>
  <line x1="250" y1="110" x2="308" y2="110" stroke="#333" stroke-width="2"/>
  <line x1="352" y1="110" x2="410" y2="110" stroke="#333" stroke-width="2"/>
  <line x1="470" y1="110" x2="530" y2="150" stroke="#333" stroke-width="2"/>
  <line x1="320" y1="160" x2="320" y2="180" stroke="#333" stroke-width="1.5" stroke-dasharray="4,2"/>
  <line x1="50" y1="180" x2="320" y2="180" stroke="#333" stroke-width="1.5" stroke-dasharray="4,2"/>
  <line x1="320" y1="210" x2="530" y2="170" stroke="#333" stroke-width="1.5" stroke-dasharray="4,2"/>
</svg>`,
        annotations: [
          {
            x: 220,
            y: 80,
            label: "开关频率",
            value: "150kHz",
            tooltip: "LM2596 固定开关频率 150kHz",
          },
          {
            x: 330,
            y: 80,
            label: "电感",
            value: "47µH",
            tooltip: "L = (Vout×(Vin-Vout))/(Vin×ΔIL×f) ≈ 47µH",
          },
          {
            x: 440,
            y: 75,
            label: "输出电容",
            value: "220µF",
            tooltip: "Cout ≥ (ΔIL)/(8×f×ΔVout) ≈ 220µF",
          },
        ],
        topology: {
          type: "Buck (降压)",
          description: "输入 24V → 输出 5V，压差 19V，占空比 D = Vout/Vin = 20.8%",
          equations: [
            {
              name: "占空比",
              formula: "D = Vout / Vin = 5V / 24V ≈ 0.208",
            },
            {
              name: "电感电流纹波",
              formula: "ΔIL = (Vin - Vout) × D / (f × L) ≈ 0.55A",
            },
            {
              name: "输出纹波",
              formula: "ΔVout = ΔIL / (8 × f × Cout) ≈ 15mV",
            },
          ],
          params: {
            Vin: "24V",
            Vout: "5V",
            Iout: "3A",
            Freq: "150kHz",
            L: "47µH",
            Cout: "220µF",
            D1: "SS34",
            R1: "3.3kΩ",
            R2: "1.2kΩ",
          },
        },
      });
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    fetchSchematic();
  }, [fetchSchematic]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8 text-[var(--color-text-secondary)]">
        <div className="w-5 h-5 border-2 border-[var(--color-border)] border-t-brand rounded-full animate-spin mr-2" />
        加载电路图...
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-4 text-center text-[13px] text-risk-high">{error}</div>
    );
  }

  if (!data) return null;

  return (
    <>
      <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] overflow-hidden my-3">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--color-border)]">
          <div className="flex items-center gap-2">
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              className="text-brand"
            >
              <rect x="3" y="3" width="7" height="7" />
              <rect x="14" y="3" width="7" height="7" />
              <rect x="3" y="14" width="7" height="7" />
              <rect x="14" y="14" width="7" height="7" />
            </svg>
            <h3 className="text-sm font-bold text-[var(--color-text-primary)]">
              参数化应用电路图
            </h3>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-brand/10 text-brand font-medium">
              {data.topology.type}
            </span>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setScale((s) => Math.min(s + 0.25, 2.5))}
              className="p-1.5 rounded hover:bg-[var(--color-background)] transition-colors cursor-pointer"
              title="放大"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </button>
            <button
              onClick={() => setScale((s) => Math.max(s - 0.25, 0.5))}
              className="p-1.5 rounded hover:bg-[var(--color-background)] transition-colors cursor-pointer"
              title="缩小"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
            </button>
            <span className="text-[11px] text-[var(--color-text-secondary)] w-10 text-center">
              {Math.round(scale * 100)}%
            </span>
            <button
              onClick={() => setFullscreen(true)}
              className="p-1.5 rounded hover:bg-[var(--color-background)] transition-colors cursor-pointer"
              title="全屏"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
              >
                <polyline points="15 3 21 3 21 9" />
                <polyline points="9 21 3 21 3 15" />
                <line x1="21" y1="3" x2="14" y2="10" />
                <line x1="3" y1="21" x2="10" y2="14" />
              </svg>
            </button>
          </div>
        </div>

        {/* SVG Circuit */}
        <div
          ref={containerRef}
          className="relative overflow-auto bg-[#fafbfc] p-4"
          style={{ minHeight: 300 }}
        >
          <div
            className="relative mx-auto"
            style={{
              width: 600,
              transform: `scale(${scale})`,
              transformOrigin: "top center",
              transition: "transform 0.2s ease",
            }}
          >
            <div
              dangerouslySetInnerHTML={{ __html: data.svg }}
              className="block"
            />

            {/* Annotations */}
            {data.annotations.map((a, i) => (
              <div
                key={i}
                className="absolute cursor-pointer group"
                style={{ left: a.x, top: a.y, transform: "translate(-50%, -100%)" }}
                onMouseEnter={() => setHoveredAnnot(a)}
                onMouseLeave={() => setHoveredAnnot(null)}
              >
                <div className="bg-brand text-white text-[9px] px-1.5 py-0.5 rounded whitespace-nowrap">
                  {a.label}: {a.value}
                </div>
                {hoveredAnnot === a && (
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 bg-[#1e1e1e] text-white text-[10px] px-2 py-1 rounded shadow-lg whitespace-nowrap z-10">
                    {a.tooltip}
                    <div className="absolute top-full left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-[#1e1e1e]" />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Topology Info Card */}
        <div className="px-4 py-3 border-t border-[var(--color-border)] bg-[var(--color-background)]">
          <h4 className="text-[12px] font-semibold text-[var(--color-text-primary)] mb-2">
            拓扑分析
          </h4>
          <p className="text-[12px] text-[var(--color-text-secondary)] mb-2">
            {data.topology.description}
          </p>

          <div className="grid grid-cols-3 gap-2 mb-2">
            {data.topology.equations.map((eq, i) => (
              <div
                key={i}
                className="p-2 rounded-lg bg-[var(--color-card)] border border-[var(--color-border)]"
              >
                <p className="text-[10px] text-[var(--color-text-secondary)] mb-0.5">
                  {eq.name}
                </p>
                <p className="text-[11px] font-mono text-[var(--color-text-primary)]">
                  {eq.formula}
                </p>
              </div>
            ))}
          </div>

          {/* Key params */}
          <details>
            <summary className="text-[11px] text-brand font-medium cursor-pointer hover:underline">
              关键参数
            </summary>
            <div className="mt-2 grid grid-cols-4 gap-1.5">
              {Object.entries(data.topology.params).map(([k, v]) => (
                <div key={k} className="text-center p-1.5 rounded bg-[var(--color-card)] border border-[var(--color-border)]">
                  <p className="text-[10px] text-[var(--color-text-secondary)]">{k}</p>
                  <p className="text-[11px] font-semibold text-[var(--color-text-primary)]">{v}</p>
                </div>
              ))}
            </div>
          </details>
        </div>
      </div>

      {/* Fullscreen Modal */}
      <AnimatePresence>
        {fullscreen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex flex-col bg-black/80 backdrop-blur-sm"
            onClick={() => setFullscreen(false)}
          >
            <div className="flex items-center justify-between h-12 px-4 bg-[#1e1e1e] text-white shrink-0">
              <h3 className="text-sm font-medium">电路图 - {data.topology.type}</h3>
              <button
                onClick={() => setFullscreen(false)}
                className="p-1.5 rounded hover:bg-white/10 transition-colors cursor-pointer"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
            <div
              className="flex-1 flex items-center justify-center p-8"
              onClick={(e) => e.stopPropagation()}
            >
              <div
                dangerouslySetInnerHTML={{ __html: data.svg }}
                className="bg-white rounded-lg p-4 shadow-2xl"
                style={{ transform: `scale(${scale})`, transformOrigin: "center" }}
              />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}