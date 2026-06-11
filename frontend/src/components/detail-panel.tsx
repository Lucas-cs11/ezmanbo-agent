"use client";

interface RiskItem {
  category: string;
  level: "HIGH" | "MEDIUM" | "LOW";
  description: string;
  recommendation: string;
}

const mockRiskAnalysis: RiskItem[] = [
  {
    category: "电压应力",
    level: "HIGH",
    description: "LM2596 输入电压 24V，耐压裕量仅 33%，低于推荐 50% 裕量",
    recommendation: "建议更换为耐压 ≥40V 的降压转换器，如 LM2596HV",
  },
  {
    category: "热管理",
    level: "MEDIUM",
    description: "预估结温 Tj=112°C，接近 125°C 上限",
    recommendation: "增加散热铜皮面积或考虑外部散热器",
  },
  {
    category: "输出纹波",
    level: "LOW",
    description: "计算输出纹波 15mVpp，在目标 20mVpp 范围内",
    recommendation: "当前布局满足要求，可维持设计",
  },
  {
    category: "电感选型",
    level: "MEDIUM",
    description: "推荐电感饱和电流 2.5A，需求峰值电流 2.8A",
    recommendation: "更换为饱和电流 ≥3.5A 的电感（如 CDRH127 系列）",
  },
];

const levelConfig = {
  HIGH: {
    label: "高",
    bgClass: "risk-badge-high",
    borderClass: "border-risk-high",
    textClass: "text-risk-high",
  },
  MEDIUM: {
    label: "中",
    bgClass: "risk-badge-medium",
    borderClass: "border-risk-medium",
    textClass: "text-risk-medium",
  },
  LOW: {
    label: "低",
    bgClass: "risk-badge-low",
    borderClass: "border-risk-low",
    textClass: "text-risk-low",
  },
};

export function DetailPanel() {
  return (
    <aside className="w-panel h-screen border-l border-[var(--color-border)] bg-[var(--color-card)] flex flex-col shrink-0 overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-[var(--color-border)]">
        <h2 className="text-sm font-bold text-[var(--color-text-primary)]">
          风险详情
        </h2>
        <p className="text-[11px] text-[var(--color-text-secondary)] mt-0.5">
          LM2596 降压电路 · 4 项风险
        </p>
      </div>

      {/* Summary Cards */}
      <div className="p-3 grid grid-cols-3 gap-2 border-b border-[var(--color-border)]">
        <div className="p-2 rounded-lg bg-risk-high/10 text-center">
          <p className="text-lg font-bold text-risk-high">
            {mockRiskAnalysis.filter((r) => r.level === "HIGH").length}
          </p>
          <p className="text-[10px] text-risk-high font-medium">高风险</p>
        </div>
        <div className="p-2 rounded-lg bg-risk-medium/10 text-center">
          <p className="text-lg font-bold text-risk-medium">
            {mockRiskAnalysis.filter((r) => r.level === "MEDIUM").length}
          </p>
          <p className="text-[10px] text-risk-medium font-medium">中风险</p>
        </div>
        <div className="p-2 rounded-lg bg-risk-low/10 text-center">
          <p className="text-lg font-bold text-risk-low">
            {mockRiskAnalysis.filter((r) => r.level === "LOW").length}
          </p>
          <p className="text-[10px] text-risk-low font-medium">低风险</p>
        </div>
      </div>

      {/* Risk List */}
      <div className="flex-1 overflow-y-auto scrollbar-thin p-3 space-y-3">
        {mockRiskAnalysis.map((item, index) => {
          const config = levelConfig[item.level];
          return (
            <div
              key={index}
              className={`p-3 rounded-lg border-l-4 ${config.borderClass} bg-[var(--color-background)]`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <h3 className="text-[13px] font-semibold text-[var(--color-text-primary)]">
                  {item.category}
                </h3>
                <span
                  className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${config.bgClass}`}
                >
                  {config.label}
                </span>
              </div>
              <p className="text-[12px] text-[var(--color-text-secondary)] leading-relaxed mb-2">
                {item.description}
              </p>
              <div className="p-2 rounded bg-[var(--color-card)] border border-[var(--color-border)]">
                <p className="text-[11px] text-[var(--color-text-primary)] font-medium mb-0.5">
                  💡 建议
                </p>
                <p className="text-[11px] text-[var(--color-text-secondary)] leading-relaxed">
                  {item.recommendation}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}