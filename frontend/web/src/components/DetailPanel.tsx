"use client";

import { useChatStore } from "@/store/chat";
import { X, Cpu, AlertTriangle, ShieldCheck } from "lucide-react";
import { cn, RISK_COLORS, RISK_LABELS, formatElapsed } from "@/lib/utils";
import type { AnalysisReport, PartIR } from "@/types";

export function DetailPanel() {
  const { activeSession } = useChatStore();
  const session = activeSession();
  const lastReport = session?.messages
    .filter((m) => m.role === "assistant" && m.report)
    .pop()?.report;

  if (!lastReport) {
    return (
      <aside className="w-[400px] h-full border-l border-gray-200 bg-surface shrink-0 flex items-center justify-center">
        <div className="text-center text-gray-400">
          <Cpu className="w-12 h-12 mx-auto mb-3 opacity-30" />
          <p className="text-sm">完成一次选型分析后</p>
          <p className="text-xs mt-1">详情将在此显示</p>
        </div>
      </aside>
    );
  }

  return (
    <aside className="w-[400px] h-full border-l border-gray-200 bg-surface shrink-0 overflow-y-auto">
      <ReportDetail report={lastReport} />
    </aside>
  );
}

function ReportDetail({ report }: { report: AnalysisReport }) {
  const { risks, recommended_parts: recommended, evidence_count, avg_confidence, elapsed_s, request_id, constraints } = report;
  const level = risks?.overall_risk_level || "low";

  return (
    <div className="p-4 space-y-4">
      {/* Header */}
      <div className={cn("rounded-xl p-4 border", RISK_COLORS[level]?.split(" ").slice(0, 2).join(" "), `border-${level === "high" ? "red" : level === "medium" ? "orange" : "green"}-200`)}>
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xl font-bold">{RISK_LABELS[level]}</span>
          <span className="font-bold text-sm capitalize">{level} Risk</span>
        </div>
        <div className="text-xs space-y-1">
          <div className="flex justify-between">
            <span>推荐器件</span>
            <span className="font-mono font-medium">{recommended?.length || 0} 款</span>
          </div>
          <div className="flex justify-between">
            <span>证据条目</span>
            <span className="font-mono font-medium">{evidence_count || 0}</span>
          </div>
          <div className="flex justify-between">
            <span>平均置信度</span>
            <span className="font-mono font-medium">{(avg_confidence || 0).toFixed(3)}</span>
          </div>
          <div className="flex justify-between">
            <span>总耗时</span>
            <span className="font-mono font-medium">{formatElapsed(elapsed_s || 0)}</span>
          </div>
          {request_id && (
            <div className="flex justify-between">
              <span>Request ID</span>
              <span className="font-mono text-[10px] text-gray-400">{request_id.slice(0, 12)}</span>
            </div>
          )}
        </div>
      </div>

      {/* Constraints summary */}
      {constraints && (
        <div className="rounded-xl border border-gray-200 p-3">
          <h4 className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">解析约束</h4>
          <div className="grid grid-cols-2 gap-1 text-xs">
            {constraints.category && <Row label="类别" value={constraints.category} />}
            {constraints.topology && <Row label="拓扑" value={constraints.topology} />}
            {constraints.input_voltage_nominal_v && <Row label="Vin" value={`${constraints.input_voltage_nominal_v}V`} />}
            {constraints.output_voltage_v && <Row label="Vout" value={`${constraints.output_voltage_v}V`} />}
            {constraints.output_current_a && <Row label="Iout" value={`${constraints.output_current_a}A`} />}
            {constraints.temperature_min_c != null && <Row label="Tmin" value={`${constraints.temperature_min_c}°C`} />}
            {constraints.temperature_max_c != null && <Row label="Tmax" value={`${constraints.temperature_max_c}°C`} />}
            {constraints.grade && <Row label="等级" value={constraints.grade} />}
          </div>
        </div>
      )}

      {/* Risk breakdown */}
      {risks?.risk_items && risks.risk_items.length > 0 && (
        <div className="rounded-xl border border-gray-200 p-3">
          <h4 className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">
            <AlertTriangle className="w-3 h-3 inline mr-1" />
            风险项 ({risks.risk_items.length})
          </h4>
          <div className="space-y-2">
            {risks.risk_items.map((r, i) => (
              <div key={i} className={cn("text-xs p-2 rounded-lg border", RISK_COLORS[r.severity]?.split(" ").slice(0, 3).join(" "))}>
                <div className="font-medium flex items-center gap-1">
                  <span className={cn("px-1 py-0.5 rounded text-[10px] font-bold",
                    r.severity === "high" ? "bg-red-200 text-red-800" :
                    r.severity === "medium" ? "bg-orange-200 text-orange-800" :
                    "bg-green-200 text-green-800"
                  )}>
                    {r.severity.toUpperCase()}
                  </span>
                  <span className="text-gray-500">{r.risk_type}</span>
                </div>
                <p className="mt-1 text-gray-700">{r.description}</p>
                {r.mitigation && (
                  <p className="mt-1 text-gray-500 italic">→ {r.mitigation}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Top recommendations */}
      {recommended && recommended.length > 0 && (
        <div className="rounded-xl border border-gray-200 p-3">
          <h4 className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">
            <ShieldCheck className="w-3 h-3 inline mr-1" />
            推荐器件
          </h4>
          <div className="space-y-2">
            {recommended.slice(0, 5).map((sp, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className={cn(
                  "w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold text-white shrink-0",
                  i === 0 ? "bg-brand-700" : i === 1 ? "bg-brand-400" : "bg-gray-400"
                )}>
                  {i + 1}
                </span>
                <span className="font-mono font-medium">{sp.part.part_number}</span>
                <span className="text-gray-400">{sp.part.manufacturer}</span>
                <span className="ml-auto font-mono font-bold">{sp.score.total_score}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ label, value }: { label: string; value: string | number }) {
  return (
    <>
      <span className="text-gray-500">{label}</span>
      <span className="font-mono font-medium text-right">{value}</span>
    </>
  );
}
