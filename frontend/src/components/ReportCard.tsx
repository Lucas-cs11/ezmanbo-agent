"use client";

import { useState } from "react";
import { useStore } from "@/store/useStore";
import type {
  SelectionReport,
  RiskIR,
  ReplacementReport,
  PartItem,
  RiskItem,
  ReplacementPair,
} from "@/store/useStore";

const levelConfig = {
  HIGH: {
    label: "高",
    bgClass: "bg-risk-high/10 text-risk-high",
    dotClass: "bg-risk-high",
  },
  MEDIUM: {
    label: "中",
    bgClass: "bg-risk-medium/10 text-risk-medium",
    dotClass: "bg-risk-medium",
  },
  LOW: {
    label: "低",
    bgClass: "bg-risk-low/10 text-risk-low",
    dotClass: "bg-risk-low",
  },
};

function LevelBadge({ level }: { level: "HIGH" | "MEDIUM" | "LOW" }) {
  const config = levelConfig[level];
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold ${config.bgClass}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${config.dotClass}`} />
      {config.label}
    </span>
  );
}

function ConfidenceChip({ confidence }: { confidence: number }) {
  const color =
    confidence >= 0.8
      ? "bg-risk-low/10 text-risk-low"
      : confidence >= 0.5
        ? "bg-risk-medium/10 text-risk-medium"
        : "bg-risk-high/10 text-risk-high";
  return (
    <span
      className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-semibold ${color}`}
    >
      {(confidence * 100).toFixed(0)}% 置信
    </span>
  );
}

function SelectionView({ data }: { data: SelectionReport }) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-bold text-[var(--color-text-primary)]">
        {data.title}
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-[12px]">
          <thead>
            <tr className="border-b border-[var(--color-border)]">
              <th className="text-left py-2 px-2 text-[var(--color-text-secondary)] font-medium">
                器件型号
              </th>
              <th className="text-left py-2 px-2 text-[var(--color-text-secondary)] font-medium">
                厂商
              </th>
              <th className="text-left py-2 px-2 text-[var(--color-text-secondary)] font-medium">
                描述
              </th>
              <th className="text-left py-2 px-2 text-[var(--color-text-secondary)] font-medium">
                评分
              </th>
              <th className="text-left py-2 px-2 text-[var(--color-text-secondary)] font-medium">
                等级
              </th>
            </tr>
          </thead>
          <tbody>
            {data.parts.map((part, i) => (
              <tr
                key={i}
                className="border-b border-[var(--color-border)]/50 hover:bg-[var(--color-background)]/50"
              >
                <td className="py-2.5 px-2 font-medium text-[var(--color-text-primary)]">
                  {part.partNumber}
                </td>
                <td className="py-2.5 px-2 text-[var(--color-text-secondary)]">
                  {part.manufacturer}
                </td>
                <td className="py-2.5 px-2 text-[var(--color-text-secondary)] max-w-[200px] truncate">
                  {part.description}
                </td>
                <td className="py-2.5 px-2">
                  <div className="flex items-center gap-2">
                    <div className="flex-1 h-1.5 rounded-full bg-[var(--color-border)] overflow-hidden">
                      <div
                        className="h-full rounded-full bg-brand transition-all"
                        style={{ width: `${part.score}%` }}
                      />
                    </div>
                    <span className="text-[11px] font-semibold text-[var(--color-text-primary)] w-8 text-right">
                      {part.score}
                    </span>
                  </div>
                </td>
                <td className="py-2.5 px-2">
                  <LevelBadge level={part.level} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {/* 参数对照 */}
      <details className="mt-3">
        <summary className="text-[12px] text-brand font-medium cursor-pointer hover:underline">
          查看参数对照
        </summary>
        <div className="mt-2 overflow-x-auto">
          <table className="w-full text-[11px] border border-[var(--color-border)] rounded-lg">
            <thead>
              <tr className="bg-[var(--color-background)]">
                <th className="py-1.5 px-2 text-left text-[var(--color-text-secondary)]">
                  参数
                </th>
                {data.parts.map((p, i) => (
                  <th
                    key={i}
                    className="py-1.5 px-2 text-left text-[var(--color-text-primary)]"
                  >
                    {p.partNumber}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.keys(data.parts[0]?.params || {}).map((key) => (
                <tr
                  key={key}
                  className="border-t border-[var(--color-border)]/50"
                >
                  <td className="py-1.5 px-2 text-[var(--color-text-secondary)]">
                    {key}
                  </td>
                  {data.parts.map((p, i) => (
                    <td
                      key={i}
                      className="py-1.5 px-2 text-[var(--color-text-primary)]"
                    >
                      {p.params[key] ?? "-"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </div>
  );
}

function RiskView({ data }: { data: RiskIR }) {
  const highCount = data.risks.filter((r) => r.level === "HIGH").length;
  const mediumCount = data.risks.filter((r) => r.level === "MEDIUM").length;
  const lowCount = data.risks.filter((r) => r.level === "LOW").length;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-bold text-[var(--color-text-primary)]">
          {data.title}
        </h3>
        <div className="flex items-center gap-2 text-[11px]">
          <span className="flex items-center gap-1 text-risk-high">
            <span className="w-2 h-2 rounded-full bg-risk-high" />
            {highCount} 高
          </span>
          <span className="flex items-center gap-1 text-risk-medium">
            <span className="w-2 h-2 rounded-full bg-risk-medium" />
            {mediumCount} 中
          </span>
          <span className="flex items-center gap-1 text-risk-low">
            <span className="w-2 h-2 rounded-full bg-risk-low" />
            {lowCount} 低
          </span>
        </div>
      </div>

      {/* 风险热力矩阵 */}
      <div className="grid grid-cols-3 gap-2 p-3 rounded-lg bg-[var(--color-background)]">
        <div className="text-center">
          <p className="text-lg font-bold text-risk-high">{highCount}</p>
          <p className="text-[10px] text-risk-high font-medium">高风险</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-bold text-risk-medium">{mediumCount}</p>
          <p className="text-[10px] text-risk-medium font-medium">中风险</p>
        </div>
        <div className="text-center">
          <p className="text-lg font-bold text-risk-low">{lowCount}</p>
          <p className="text-[10px] text-risk-low font-medium">低风险</p>
        </div>
      </div>

      {/* 风险列表 */}
      <div className="space-y-2">
        {data.risks.map((risk) => {
          const config = levelConfig[risk.level];
          return (
            <div
              key={risk.id}
              className={`p-3 rounded-lg border-l-4 ${
                risk.level === "HIGH"
                  ? "border-risk-high bg-risk-high/5"
                  : risk.level === "MEDIUM"
                    ? "border-risk-medium bg-risk-medium/5"
                    : "border-risk-low bg-risk-low/5"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-2">
                  <h4 className="text-[13px] font-semibold text-[var(--color-text-primary)]">
                    {risk.category}
                  </h4>
                  <LevelBadge level={risk.level} />
                </div>
                <ConfidenceChip confidence={risk.confidence} />
              </div>
              <p className="text-[12px] text-[var(--color-text-secondary)] leading-relaxed mb-1.5">
                {risk.description}
              </p>
              <div className="p-2 rounded bg-[var(--color-card)] border border-[var(--color-border)]">
                <p className="text-[11px] text-brand font-medium">💡 {risk.recommendation}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function ReplacementView({ data }: { data: ReplacementReport }) {
  return (
    <div className="space-y-3">
      <h3 className="text-sm font-bold text-[var(--color-text-primary)]">
        {data.title}
      </h3>
      <div className="space-y-3">
        {data.replacements.map((pair, i) => (
          <div
            key={i}
            className="p-3 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)]"
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2 text-[13px]">
                <span className="font-semibold text-risk-high line-through">
                  {pair.originalPart}
                </span>
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className="text-[var(--color-text-secondary)]"
                >
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
                <span className="font-semibold text-risk-low">
                  {pair.alternativePart}
                </span>
              </div>
              <span className="text-[11px] text-[var(--color-text-secondary)]">
                {pair.manufacturer}
              </span>
            </div>
            <p className="text-[12px] text-[var(--color-text-secondary)] mb-2">
              {pair.reason}
            </p>
            {/* 参数差异对⽐ */}
            <div className="overflow-x-auto">
              <table className="w-full text-[11px] border border-[var(--color-border)] rounded-lg">
                <thead>
                  <tr className="bg-[var(--color-card)]">
                    <th className="py-1.5 px-2 text-left text-[var(--color-text-secondary)]">
                      参数
                    </th>
                    <th className="py-1.5 px-2 text-left text-risk-high">
                      {pair.originalPart}
                    </th>
                    <th className="py-1.5 px-2 text-left text-risk-low">
                      {pair.alternativePart}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {pair.paramDifferences.map((diff, j) => (
                    <tr
                      key={j}
                      className="border-t border-[var(--color-border)]/50"
                    >
                      <td className="py-1.5 px-2 text-[var(--color-text-secondary)] font-medium">
                        {diff.param}
                      </td>
                      <td className="py-1.5 px-2 bg-risk-high/5 text-risk-high">
                        {diff.original}
                      </td>
                      <td className="py-1.5 px-2 bg-risk-low/5 text-risk-low">
                        {diff.alternative}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

type TabType = "selection" | "risk" | "replacement";

export function ReportCard() {
  const [activeTab, setActiveTab] = useState<TabType>("selection");
  const reportBundle = useStore((s) => s.reportBundle);
  const setShowPdfViewer = useStore((s) => s.setShowPdfViewer);
  const pdfLoading = useStore((s) => s.pdfLoading);

  if (!reportBundle) return null;

  const tabs: { key: TabType; label: string; data: unknown }[] = [];
  if (reportBundle.selection)
    tabs.push({
      key: "selection",
      label: "选型报告",
      data: reportBundle.selection,
    });
  if (reportBundle.risk)
    tabs.push({
      key: "risk",
      label: "风险评估",
      data: reportBundle.risk,
    });
  if (reportBundle.replacement)
    tabs.push({
      key: "replacement",
      label: "替换建议",
      data: reportBundle.replacement,
    });

  if (tabs.length === 0) return null;

  // Ensure active tab exists
  if (!tabs.find((t) => t.key === activeTab) && tabs.length > 0) {
    setActiveTab(tabs[0].key);
  }

  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-card)] overflow-hidden my-3">
      {/* Tab Bar */}
      <div className="flex border-b border-[var(--color-border)]">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 py-2.5 text-[12px] font-medium cursor-pointer border-b-2 transition-all ${
              activeTab === tab.key
                ? "border-brand text-brand"
                : "border-transparent text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="p-4">
        {activeTab === "selection" && reportBundle.selection && (
          <SelectionView data={reportBundle.selection} />
        )}
        {activeTab === "risk" && reportBundle.risk && (
          <RiskView data={reportBundle.risk} />
        )}
        {activeTab === "replacement" && reportBundle.replacement && (
          <ReplacementView data={reportBundle.replacement} />
        )}
      </div>

      {/* Footer: 查看完整 PDF */}
      <div className="px-4 py-3 border-t border-[var(--color-border)] bg-[var(--color-background)]">
        <button
          onClick={() => setShowPdfViewer(true)}
          disabled={pdfLoading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-brand text-white text-[12px] font-medium hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-60"
        >
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
            <line x1="16" y1="13" x2="8" y2="13" />
            <line x1="16" y1="17" x2="8" y2="17" />
            <polyline points="10 9 9 9 8 9" />
          </svg>
          {pdfLoading ? "加载中..." : "查看完整 PDF 报告"}
        </button>
      </div>
    </div>
  );
}