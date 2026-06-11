"use client";

import { useState } from "react";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

interface HeatmapPoint {
  partNumber: string;
  severity: number; // 1-5
  probability: number; // 1-5
  risk: "HIGH" | "MEDIUM" | "LOW";
  description: string;
}

const mockData: HeatmapPoint[] = [
  {
    partNumber: "LM2596T-5.0",
    severity: 4,
    probability: 3,
    risk: "HIGH",
    description: "电压裕量不足，结温偏高",
  },
  {
    partNumber: "LM2596HV",
    severity: 2,
    probability: 2,
    risk: "LOW",
    description: "60V 耐压，裕量充足",
  },
  {
    partNumber: "TPS5430",
    severity: 3,
    probability: 3,
    risk: "MEDIUM",
    description: "频率高 EMI 风险，耐压裕量偏紧",
  },
  {
    partNumber: "MP2315",
    severity: 2,
    probability: 1,
    risk: "LOW",
    description: "集成 MOSFET，外围简洁",
  },
  {
    partNumber: "XL4015",
    severity: 3,
    probability: 4,
    risk: "HIGH",
    description: "国产器件，批次一致性存疑",
  },
  {
    partNumber: "RT8279",
    severity: 2,
    probability: 3,
    risk: "MEDIUM",
    description: "Richtek 方案，供货周期不稳定",
  },
];

const riskColorMap = {
  HIGH: "#c62828",
  MEDIUM: "#f57c00",
  LOW: "#2e7d32",
};

const gridLines = [
  { severity: 1, probability: 1 },
  { severity: 2, probability: 1 },
  { severity: 3, probability: 1 },
  { severity: 4, probability: 1 },
  { severity: 5, probability: 1 },
  { severity: 1, probability: 2 },
  { severity: 1, probability: 3 },
  { severity: 1, probability: 4 },
  { severity: 1, probability: 5 },
];

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    payload: HeatmapPoint;
  }>;
}

function CustomTooltip({ active, payload }: CustomTooltipProps) {
  if (active && payload && payload.length) {
    const pt = payload[0].payload;
    return (
      <div className="bg-[#1e1e1e] text-white text-[11px] px-3 py-2 rounded-lg shadow-xl max-w-[220px]">
        <p className="font-bold text-[12px] mb-1">{pt.partNumber}</p>
        <p className="text-[10px] opacity-80 mb-1">
          严重度: {pt.severity} / 发⽣概率: {pt.probability}
        </p>
        <p className="text-[10px] opacity-70">{pt.description}</p>
        <span
          className="inline-block mt-1 px-1.5 py-0.5 rounded text-[9px] font-bold"
          style={{
            backgroundColor: `${riskColorMap[pt.risk]}20`,
            color: riskColorMap[pt.risk],
          }}
        >
          {pt.risk === "HIGH" ? "高风险" : pt.risk === "MEDIUM" ? "中等风险" : "低风险"}
        </span>
      </div>
    );
  }
  return null;
}

export function RiskHeatmap() {
  const [hoveredPart, setHoveredPart] = useState<string | null>(null);

  return (
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
            className="text-risk-medium"
          >
            <rect x="3" y="3" width="18" height="18" rx="2" />
            <rect x="7" y="7" width="4" height="4" fill="var(--color-risk-high)" />
            <rect x="13" y="7" width="4" height="4" fill="var(--color-risk-medium)" />
            <rect x="7" y="13" width="4" height="4" fill="var(--color-risk-medium)" />
            <rect x="13" y="13" width="4" height="4" fill="var(--color-risk-low)" />
          </svg>
          <h3 className="text-sm font-bold text-[var(--color-text-primary)]">
            风险热力矩阵
          </h3>
        </div>
        <div className="flex items-center gap-3 text-[10px]">
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-risk-high" />
            高
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-risk-medium" />
            中
          </span>
          <span className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-risk-low" />
            低
          </span>
        </div>
      </div>

      {/* Heatmap */}
      <div className="p-4">
        <div className="flex items-center gap-2 mb-3">
          <div className="flex-1 text-center">
            <div className="grid grid-cols-3 gap-1.5">
              <div className="p-2 rounded-lg bg-risk-high/10">
                <p className="text-lg font-bold text-risk-high">
                  {mockData.filter((d) => d.risk === "HIGH").length}
                </p>
                <p className="text-[10px] text-risk-high font-medium">高风险</p>
              </div>
              <div className="p-2 rounded-lg bg-risk-medium/10">
                <p className="text-lg font-bold text-risk-medium">
                  {mockData.filter((d) => d.risk === "MEDIUM").length}
                </p>
                <p className="text-[10px] text-risk-medium font-medium">中风险</p>
              </div>
              <div className="p-2 rounded-lg bg-risk-low/10">
                <p className="text-lg font-bold text-risk-low">
                  {mockData.filter((d) => d.risk === "LOW").length}
                </p>
                <p className="text-[10px] text-risk-low font-medium">低风险</p>
              </div>
            </div>
          </div>
        </div>

        <div style={{ width: "100%", height: 340 }}>
          <ResponsiveContainer>
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              {/* Risk zone backgrounds */}
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis
                type="number"
                dataKey="severity"
                name="严重度"
                domain={[0, 6]}
                ticks={[1, 2, 3, 4, 5]}
                stroke="var(--color-text-secondary)"
                tick={{ fontSize: 11 }}
                label={{
                  value: "严重度 →",
                  position: "insideBottom",
                  offset: -8,
                  style: { fontSize: 11, fill: "var(--color-text-secondary)" },
                }}
              />
              <YAxis
                type="number"
                dataKey="probability"
                name="发⽣概率"
                domain={[0, 6]}
                ticks={[1, 2, 3, 4, 5]}
                stroke="var(--color-text-secondary)"
                tick={{ fontSize: 11 }}
                label={{
                  value: "发⽣概率 →",
                  angle: -90,
                  position: "insideLeft",
                  offset: 10,
                  style: { fontSize: 11, fill: "var(--color-text-secondary)" },
                }}
              />
              <ZAxis range={[120, 120]} />
              <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: "3 3" }} />
              <Scatter data={mockData} fill="#888">
                {mockData.map((entry, index) => (
                  <Cell
                    key={index}
                    fill={riskColorMap[entry.risk]}
                    fillOpacity={hoveredPart === entry.partNumber ? 1 : 0.75}
                    stroke={riskColorMap[entry.risk]}
                    strokeWidth={hoveredPart === entry.partNumber ? 2 : 0}
                    style={{
                      transition: "all 0.2s ease",
                      cursor: "pointer",
                    }}
                    onClick={() =>
                      setHoveredPart(
                        hoveredPart === entry.partNumber ? null : entry.partNumber
                      )
                    }
                  />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Legend list */}
        <div className="mt-3 space-y-1">
          {mockData.map((pt) => (
            <div
              key={pt.partNumber}
              className={`flex items-center gap-2 px-2 py-1 rounded text-[11px] transition-colors ${
                hoveredPart === pt.partNumber
                  ? "bg-[var(--color-background)]"
                  : ""
              }`}
              onMouseEnter={() => setHoveredPart(pt.partNumber)}
              onMouseLeave={() => setHoveredPart(null)}
            >
              <span
                className="w-2.5 h-2.5 rounded-full shrink-0"
                style={{ backgroundColor: riskColorMap[pt.risk] }}
              />
              <span className="font-medium text-[var(--color-text-primary)] w-32">
                {pt.partNumber}
              </span>
              <span className="text-[var(--color-text-secondary)] flex-1 truncate">
                S{pt.severity} / P{pt.probability}
              </span>
              <span className="text-[var(--color-text-secondary)] text-[10px] truncate max-w-[160px]">
                {pt.description}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}