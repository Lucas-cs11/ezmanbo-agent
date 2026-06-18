"use client";

import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer, Label } from "recharts";
import type { RiskItem } from "@/types";

interface RiskPoint {
  x: number;
  y: number;
  z: number;
  name: string;
  desc: string;
  severity: string;
}

function riskToPoint(r: RiskItem, idx: number): RiskPoint {
  const sevMap: Record<string, number> = { low: 2, medium: 3.5, high: 5 };
  // 发生概率映射（对齐后端 _dim_to_risk_type: supply/compliance/engineering/gate）
  const probMap: Record<string, number> = {
    supply: 3.5,       // 供应链风险（D3/D4/D6/D7/D9）— 中高概率
    engineering: 2,    // 工程风险（D1/D2/D8/D10）— 较低概率
    compliance: 3,     // 合规风险（D5）— 中等概率
    gate: 4.5,         // 门禁触发项 — 高概率
  };
  return {
    x: sevMap[r.severity] || 3,
    y: probMap[r.risk_type] || 3,
    z: 60,
    name: `${r.severity.toUpperCase()} · ${r.risk_type}`,
    desc: r.description.slice(0, 60),
    severity: r.severity,
  };
}

const SEVERITY_COLORS: Record<string, string> = {
  high: "#c62828",
  medium: "#f57c00",
  low: "#2e7d32",
};

export function RiskHeatmap({ risks }: { risks: RiskItem[] }) {
  const data = risks.map(riskToPoint);

  return (
    <div className="rounded-xl border border-gray-200 bg-white p-4">
      <h4 className="text-xs font-semibold text-gray-500 mb-3 uppercase tracking-wide">
        风险热力矩阵
      </h4>
      <ResponsiveContainer width="100%" height={220}>
        <ScatterChart margin={{ top: 10, right: 10, bottom: 30, left: 30 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis type="number" dataKey="x" domain={[0, 5.5]} tickCount={6} tick={{ fontSize: 10 }}>
            <Label value="严重度 →" offset={-10} position="insideBottom" style={{ fontSize: 10, fill: "#888" }} />
          </XAxis>
          <YAxis type="number" dataKey="y" domain={[0, 5.5]} tickCount={6} tick={{ fontSize: 10 }}>
            <Label value="发生概率 →" angle={-90} offset={0} position="insideLeft" style={{ fontSize: 10, fill: "#888" }} />
          </YAxis>
          <ZAxis type="number" dataKey="z" range={[40, 120]} />
          <Tooltip
            contentStyle={{ fontSize: 11, borderRadius: 8, border: "1px solid #eee" }}
            formatter={(value: unknown, name: string) => {
              if (name === "x") return [`严重度: ${value}`, ""];
              if (name === "y") return [`概率: ${value}`, ""];
              return [String(value), ""];
            }}
            labelFormatter={(idx: number) => data[idx]?.name || ""}
          />
          <Scatter data={data} fill="#888">
            {data.map((entry, idx) => (
              <Cell key={idx} fill={SEVERITY_COLORS[entry.severity] || "#888"} fillOpacity={0.7} stroke={SEVERITY_COLORS[entry.severity] || "#888"} />
            ))}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
      <div className="flex justify-center gap-4 mt-2">
        {Object.entries(SEVERITY_COLORS).map(([key, color]) => (
          <div key={key} className="flex items-center gap-1 text-[10px] text-gray-500">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            {key.toUpperCase()}
          </div>
        ))}
      </div>
    </div>
  );
}
