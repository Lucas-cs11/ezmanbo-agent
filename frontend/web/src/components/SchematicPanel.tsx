"use client";

import { useState, useEffect, useMemo } from "react";
import { Maximize2, Minimize2 } from "lucide-react";
import DOMPurify from "dompurify";
import { cn } from "@/lib/utils";

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

  // 对后端返回的 SVG 字符串进行 XSS 净化。
  //
  // `ADD_ATTR: ["dominant-baseline"]` 是实测加上的：schemdraw 用它把电压/位号标签贴在
  // 导线上（每张图 5–7 处），而 DOMPurify 的 svg profile 默认会把它剥掉——图还在，标签
  // 却会整体上浮/下沉着离开导线。加进来只放行这一个**表现属性**，
  // `onload` / `<script>` / `javascript:` href / `foreignObject` 依旧全被剥除（已实测）。
  const sanitizedSvg = useMemo(() => {
    if (!svg) return null;
    return DOMPurify.sanitize(svg, {
      USE_PROFILES: { svg: true, svgFilters: true },
      ADD_ATTR: ["dominant-baseline"],
    });
  }, [svg]);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        // 后端这个端点的根级路径就是 `/schematic/{topology}`（app/main.py 的
        // get_schematic），next.config.js 里登记的转发规则也是 `/schematic/:path*`。
        // 多写一层 `/api` 会落到并不存在的 `/api/schematic` 上，拿到 404——此前就是这么坏的。
        const url = `/schematic/${topology}?Vin=${vin}&Vout=${vout}&Iout=${iout}`;
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

      {/* 商用产品必须说清这张图是什么：它是按报数参数生成的**示意**拓扑，不是网表、也没跑过仿真。
          不标这一句，用户可能把它当成可以直接投产的设计依据，那是我们的责任。 */}
      {sanitizedSvg && (
        <p className="px-4 py-1.5 border-t border-gray-100 text-2xs text-gray-400">
          示意图 · 非 EDA 网表 · 未经仿真，不作为设计依据
        </p>
      )}
    </div>
  );
}
