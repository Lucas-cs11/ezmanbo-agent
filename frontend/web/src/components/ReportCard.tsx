"use client";

import { useState } from "react";
import { cn, RISK_COLORS } from "@/lib/utils";
import type { AnalysisReport } from "@/types";
import { ChevronLeft, ChevronRight, AlertTriangle, CheckCircle, FileText } from "lucide-react";

type Tab = "selection" | "risk" | "evidence";

const PAGE_SIZE = 10;

export function ReportCard({ report }: { report: AnalysisReport }) {
  const [tab, setTab] = useState<Tab>("selection");
  const [evidencePage, setEvidencePage] = useState(0);
  const { recommended_parts: parts, risks, evidence_count, avg_confidence, evidence_items } = report;

  const tabs: { key: Tab; label: string }[] = [
    { key: "selection", label: "选型结果" },
    { key: "risk", label: "风险评估" },
    { key: "evidence", label: "证据链" },
  ];

  return (
    <div className="rounded-xl border border-gray-200 bg-white overflow-hidden shadow-sm">
      {/* Tab bar */}
      <div className="flex border-b border-gray-100 bg-gray-50">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={cn(
              "px-4 py-2 text-xs font-medium transition-colors",
              tab === t.key
                ? "text-brand-700 border-b-2 border-brand-600 bg-white"
                : "text-gray-500 hover:text-gray-700"
            )}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div className="p-3 max-h-[320px] overflow-y-auto">
        {tab === "selection" && (
          <div className="space-y-2">
            {parts?.slice(0, 8).map((sp, i) => (
              <div key={i} className="flex items-center gap-3 p-2 rounded-lg border border-gray-100 hover:bg-gray-50">
                <span className={cn(
                  "w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold text-white shrink-0",
                  sp.recommendation_level === "recommended" ? "bg-brand-600" :
                  sp.recommendation_level === "backup" ? "bg-amber-500" : "bg-gray-400"
                )}>
                  {i + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-medium text-sm">{sp.part.part_number}</span>
                    <span className="text-[10px] text-gray-400">{sp.part.manufacturer}</span>
                    {sp.part.automotive_grade && (
                      <span className="text-[9px] px-1 py-0.5 rounded bg-blue-50 text-blue-600 font-medium">AEC-Q100</span>
                    )}
                  </div>
                  <div className="flex gap-3 text-[10px] text-gray-500 mt-0.5">
                    {sp.part.output_voltage_v && <span>Vout: {sp.part.output_voltage_v}V</span>}
                    {sp.part.output_current_max_a && <span>Imax: {sp.part.output_current_max_a}A</span>}
                    {sp.part.package && <span>{sp.part.package}</span>}
                    {sp.part.stock != null && <span>库存: {sp.part.stock}</span>}
                  </div>
                </div>
                <div className="text-right shrink-0">
                  <div className="font-mono font-bold text-sm">{sp.score.total_score}</div>
                  <div className="text-[9px] text-gray-400">总分</div>
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "risk" && risks?.risk_items && (
          <div className="space-y-2">
            {risks.risk_items.map((r, i) => (
              <div key={i} className={cn("p-3 rounded-lg border text-xs", RISK_COLORS[r.severity]?.split(" ").slice(0, 3).join(" "))}>
                <div className="flex items-center gap-2 mb-1">
                  <span className={cn(
                    "px-1.5 py-0.5 rounded text-[10px] font-bold uppercase",
                    r.severity === "high" ? "bg-red-200 text-red-800" :
                    r.severity === "medium" ? "bg-orange-200 text-orange-800" : "bg-green-200 text-green-800"
                  )}>{r.severity}</span>
                  <span className="text-gray-500">{r.risk_type}</span>
                  {r.related_part_number && (
                    <span className="font-mono text-gray-400">{r.related_part_number}</span>
                  )}
                </div>
                <p className="text-gray-700">{r.description}</p>
                {r.mitigation && (
                  <p className="mt-1 text-gray-500 italic">建议: {r.mitigation}</p>
                )}
              </div>
            ))}
          </div>
        )}

        {tab === "evidence" && (
          <div className="space-y-3">
            {/* Summary stats */}
            <div className="grid grid-cols-2 gap-3">
              <div className="text-center p-3 rounded-lg bg-brand-50 border border-brand-100">
                <div className="text-2xl font-bold text-brand-700">{evidence_count || 0}</div>
                <div className="text-[10px] text-gray-500 mt-1">证据条目</div>
              </div>
              <div className="text-center p-3 rounded-lg bg-green-50 border border-green-100">
                <div className="text-2xl font-bold text-green-700">{(avg_confidence || 0).toFixed(2)}</div>
                <div className="text-[10px] text-gray-500 mt-1">平均置信度</div>
              </div>
            </div>

            {/* Evidence list with pagination */}
            {evidence_items && evidence_items.length > 0 ? (
              <>
                <div className="text-[10px] text-gray-400 flex items-center justify-between px-1">
                  <span>共 {evidence_items.length} 条，第 {evidencePage + 1}/{Math.ceil(evidence_items.length / PAGE_SIZE)} 页</span>
                  <div className="flex gap-1">
                    <button
                      onClick={() => setEvidencePage(p => Math.max(0, p - 1))}
                      disabled={evidencePage === 0}
                      className="p-0.5 rounded hover:bg-gray-100 disabled:opacity-30"
                    >
                      <ChevronLeft className="w-3 h-3" />
                    </button>
                    <button
                      onClick={() => setEvidencePage(p => Math.min(Math.ceil(evidence_items.length / PAGE_SIZE) - 1, p + 1))}
                      disabled={(evidencePage + 1) * PAGE_SIZE >= evidence_items.length}
                      className="p-0.5 rounded hover:bg-gray-100 disabled:opacity-30"
                    >
                      <ChevronRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>

                <div className="space-y-1.5">
                  {evidence_items
                    .slice(evidencePage * PAGE_SIZE, (evidencePage + 1) * PAGE_SIZE)
                    .map((e, i) => (
                      <div
                        key={i}
                        className={cn(
                          "flex items-start gap-2 p-2 rounded-lg border text-xs",
                          e.need_human_review
                            ? "border-amber-200 bg-amber-50"
                            : "border-gray-100 bg-white"
                        )}
                      >
                        {e.need_human_review ? (
                          <AlertTriangle className="w-3.5 h-3.5 text-amber-500 shrink-0 mt-0.5" />
                        ) : (
                          <CheckCircle className="w-3.5 h-3.5 text-green-500 shrink-0 mt-0.5" />
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="text-gray-800 leading-relaxed">{e.claim}</p>
                          <div className="flex items-center gap-2 mt-1">
                            <span className="font-mono text-[10px] text-brand-600 bg-brand-50 px-1 rounded">
                              {e.part_number}
                            </span>
                            <span className="text-[10px] text-gray-400">
                              {e.evidence_type === "mock_data" ? "本地数据" :
                               e.evidence_type === "ezplm_api" ? "eZ-PLM" :
                               e.evidence_type === "datasheet" ? "数据手册" :
                               e.evidence_type === "automotive_cert" ? "车规认证" :
                               e.evidence_type === "domestic_origin" ? "国产化" :
                               e.evidence_type === "missing_datasheet" ? "缺数据手册" :
                               e.evidence_type}
                            </span>
                            <div className="flex items-center gap-1 ml-auto">
                              <div className="w-12 h-1 rounded-full bg-gray-200">
                                <div
                                  className={cn(
                                    "h-full rounded-full",
                                    e.confidence >= 0.9 ? "bg-green-500" :
                                    e.confidence >= 0.7 ? "bg-amber-500" : "bg-red-500"
                                  )}
                                  style={{ width: `${Math.round(e.confidence * 100)}%` }}
                                />
                              </div>
                              <span className="text-[10px] text-gray-400 font-mono w-7 text-right">
                                {(e.confidence * 100).toFixed(0)}%
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              </>
            ) : (
              <div className="text-center py-6 text-gray-400">
                <FileText className="w-8 h-8 mx-auto mb-2 opacity-30" />
                <p className="text-xs">暂无详细证据条目</p>
                <p className="text-[10px] mt-1">完整证据链可在 BOM 导出中查看</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
