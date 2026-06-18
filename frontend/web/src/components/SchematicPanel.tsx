"use client";

import { useState, useEffect, useMemo } from "react";
import { Maximize2, Minimize2 } from "lucide-react";
import DOMPurify from "dompurify";

interface Props {
  topology: string;
  vin: number;
  vout: number;
  iout: number;
}

export function SchematicPanel({ topology, vin, vout, iout }: Props) {
  const [svg, setSvg] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 对后端返回的 SVG 字符串进行 XSS 净化
  const sanitizedSvg = useMemo(() => {
    if (!svg) return null;
    return DOMPurify.sanitize(svg, { USE_PROFILES: { svg: true, svgFilters: true } });
  }, [svg]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const url = `/api/schematic/${topology}?Vin=${vin}&Vout=${vout}&Iout=${iout}`;
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const text = await resp.text();
        if (!cancelled) setSvg(text);
      } catch (err: unknown) {
        if (!cancelled) setError(err instanceof Error ? err.message : "加载失败");
      }
    }
    load();
    return () => { cancelled = true; };
  }, [topology, vin, vout, iout]);

  const topologyLabel: Record<string, string> = {
    buck: "Buck 降压拓扑",
    boost: "Boost 升压拓扑",
    ldo: "LDO 线性稳压",
  };

  return (
    <div className="mt-3 rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
      <div className="flex items-center justify-between px-4 py-2 bg-gray-50 border-b border-gray-100">
        <h4 className="text-xs font-semibold text-gray-600">
          {topologyLabel[topology] || topology} — {vin}V to {vout}V @ {iout}A
        </h4>
        <button
          onClick={() => setExpanded(!expanded)}
          className="p-1 hover:bg-gray-200 rounded transition-colors"
        >
          {expanded ? <Minimize2 className="w-4 h-4 text-gray-500" /> : <Maximize2 className="w-4 h-4 text-gray-500" />}
        </button>
      </div>

      <div className={cn("flex items-center justify-center bg-white", expanded ? "p-6" : "p-3")}>
        {error ? (
          <p className="text-xs text-gray-400 py-4">电路图加载失败: {error}</p>
        ) : sanitizedSvg ? (
          <div
            dangerouslySetInnerHTML={{ __html: sanitizedSvg }}
            className={cn("[&>svg]:max-w-full [&>svg]:h-auto", expanded && "[&>svg]:max-w-[600px]")}
          />
        ) : (
          <div className="flex items-center gap-2 text-xs text-gray-400 py-4">
            <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse-dot" />
            加载电路图中...
          </div>
        )}
      </div>
    </div>
  );
}

function cn(...classes: (string | false | undefined | null)[]): string {
  return classes.filter(Boolean).join(" ");
}
