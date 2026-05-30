"""
output_bom.py — BOM（元器件选型清单）生成模块

报告风格：学术化、产业规范化，参照 IPC 命名规范。
"""

from __future__ import annotations

from typing import List
from .schemas import SelectionReport


def generate_bom(report: SelectionReport, rag_context: str = "") -> str:
    """生成符合 IPC 命名规范的元器件选型清单（Markdown）。"""
    from .output_generator import _now, _lifecycle_cn

    c = report.constraints
    rec = [s for s in report.candidates if s.recommendation_level == "recommended"]
    bak = [s for s in report.candidates if s.recommendation_level == "backup"]

    lines: List[str] = []

    # ── 文件头 ──────────────────────────────────────────────────────
    lines += [
        "# 元器件选型清单",
        "",
        "## 文件信息",
        "",
        f"| 字段 | 内容 |",
        f"|------|------|",
        f"| 生成日期 | {_now()} |",
        f"| 需求标识 | {report.request_id[:8]} |",
        f"| 原始需求 | {c.raw_input} |",
        f"| 器件类别 | {c.category or '未指定'} |",
        f"| 电路拓扑 | {c.topology or '未指定'} |",
        f"| 标称输入电压 | {f'{c.input_voltage_nominal_v} V' if c.input_voltage_nominal_v else '未指定'} |",
        f"| 输出电压 | {f'{c.output_voltage_v} V' if c.output_voltage_v else '未指定'} |",
        f"| 最大输出电流 | {f'{c.output_current_a} A' if c.output_current_a else '未指定'} |",
        f"| 工作温度范围 | {f'{c.temperature_min_c} ~ {c.temperature_max_c} °C' if c.temperature_min_c is not None and c.temperature_max_c is not None else '未指定'} |",
        f"| 应用等级 | {c.grade or '工业级 (Industrial)'} |",
        f"| 检索候选数量 | {len(report.candidates)} |",
        f"| 推荐器件数量 | {len(rec)} |",
        "",
    ]

    # ── 推荐器件清单 ─────────────────────────────────────────────
    lines += [
        "## 一、推荐器件清单（Recommended Components）",
        "",
        "> 推荐级别说明：推荐器件为经去重合并后的 Top 5 候选，综合评分最高且满足全部关键约束；",
        "> 备选器件为其余满足基本参数匹配的候选型号。",
        "",
        "| 序号 | 制造商型号 (MPN) | 制造商 | 规格描述 | 封装 | Vin范围 | Vout | Iout(A) | 生命周期 | 综合评分 | 参数 | 供应 | 推荐等级 |",
        "|------|----------------|--------|---------|------|---------|------|---------|---------|---------|------|------|---------|",
    ]
    for idx, s in enumerate(rec, 1):
        p = s.part
        sc = s.score
        desc = (p.description or "-")
        if len(desc) > 50:
            desc = desc[:47] + "..."
        vin_range = f"{p.input_voltage_min_v:.1f}~{p.input_voltage_max_v:.1f}" if p.input_voltage_min_v is not None else "-"
        vout_str = f"{p.output_voltage_v}V" if p.output_voltage_v is not None else ("可调(ADJ)" if "ADJ" in (p.part_number or "").upper() else "-")
        iout_str = str(p.output_current_max_a) if p.output_current_max_a is not None else "-"
        lifecycle = _lifecycle_cn(p.lifecycle_status)
        if not p.lifecycle_status:
            lifecycle = "⚠ 待确认"
        package = p.package or ("⚠ 待确认" if idx <= 3 else "-")
        lines.append(
            f"| {idx} | {p.part_number} | {p.manufacturer or '-'} | {desc} "
            f"| {package} | {vin_range} | {vout_str} | {iout_str} "
            f"| {lifecycle} "
            f"| {sc.total_score:.2f} | {sc.parameter_match_score:.0f} | {sc.supply_risk_score:.0f} | 推荐 |"
        )

    if not rec:
        lines.append("| — | 无满足推荐门槛的器件，请参阅备选清单 | | | | | | | | | | | |")

    lines.append("")

    # ── 备选器件清单 ─────────────────────────────────────────────
    lines += [
        "## 二、备选器件清单（Alternative Components）",
        "",
        "| 序号 | 制造商型号 (MPN) | 制造商 | 封装 | Vout | Iout(A) | 生命周期 | 综合评分 | 推荐等级 |",
        "|------|----------------|--------|------|------|---------|---------|---------|---------|",
    ]
    for idx, s in enumerate(bak[:10], 1):
        p = s.part
        vout_str = f"{p.output_voltage_v}V" if p.output_voltage_v is not None else ("可调" if "ADJ" in (p.part_number or "").upper() else "-")
        iout_str = str(p.output_current_max_a) if p.output_current_max_a is not None else "-"
        lifecycle = _lifecycle_cn(p.lifecycle_status)
        if not p.lifecycle_status:
            lifecycle = "⚠ 待确认"
        lines.append(
            f"| {idx} | {p.part_number} | {p.manufacturer or '-'} "
            f"| {p.package or '-'} | {vout_str} | {iout_str} "
            f"| {lifecycle} "
            f"| {s.score.total_score:.2f} | 备选 |"
        )
    if not bak:
        lines.append("| — | 无备选器件 | | | | | | | |")

    lines.append("")

    # ── 关键参数对比 ─────────────────────────────────────────────
    lines += [
        "## 三、关键电气参数对比（Key Electrical Parameters）",
        "",
        "| 制造商型号 (MPN) | 输入电压范围 (V) | 输出电压 (V) | 最大输出电流 (A) | 工作温度范围 (°C) | 车规认证 |",
        "|----------------|---------------|------------|----------------|----------------|---------|",
    ]
    for s in (rec + bak)[:5]:
        p = s.part
        vin = (f"{p.input_voltage_min_v} ~ {p.input_voltage_max_v}"
               if p.input_voltage_min_v is not None else "-")
        vout_str = f"{p.output_voltage_v}" if p.output_voltage_v is not None else "可调"
        iout = str(p.output_current_max_a) if p.output_current_max_a is not None else "-"
        temp = (f"{p.temperature_min_c} ~ {p.temperature_max_c}"
                if p.temperature_min_c is not None else "-")
        auto = "是 (AEC-Q100/Q101)" if p.automotive_grade else "否"
        lines.append(f"| {p.part_number} | {vin} | {vout_str} | {iout} | {temp} | {auto} |")

    # ── 评分方法说明 ─────────────────────────────────────────────
    lines += [
        "",
        "## 四、评分方法说明",
        "",
        "本清单综合评分采用以下模型：",
        "",
        "**规则评分模式（rule_only）：**",
        "- 参数匹配分（Parameter Match Score）：权重 80%。评估器件电气参数（输入电压范围、输出电流、工作温度）与需求约束的覆盖程度。",
        "- 供应链稳定性分（Supply Reliability Score）：权重 20%。基于库存水平与生命周期状态评估供货连续性风险。",
        "",
        "**LLM 增强模式（llm_enhanced）：**",
        "- 参数匹配分：权重 40%。",
        "- 供应链稳定性分：权重 10%。",
        "- 应用场景适配分（Application Fit Score）：权重 25%。基于 eZ-PLM 参考设计库，由 LLM 评估器件在同类应用中的匹配度。",
        "- 设计成熟度分（Design Maturity Score）：权重 25%。基于参考设计，由 LLM 评估器件工程可靠性与应用成熟程度。",
        "",
        "推荐门槛：综合评分 >= 75 分列为推荐器件；50 ~ 74 分列为备选器件；低于 50 分不推荐。",
        "",
    ]

    # ── RAG 工程知识参考 ──────────────────────────────────────────
    if rag_context:
        lines += [
            "## 五、工程知识库参考（RAG-Enhanced）",
            "",
            "> 以下知识由 ChromaDB 向量检索从工程知识库中提取，用于辅助选型决策。",
            "> 嵌入模型：sentence-transformers all-MiniLM-L6-v2",
            "",
            rag_context,
            "",
        ]

    lines += [
        "---",
        "",
        f"*本文件由 ezplm-component-risk-agent 自动生成，生成时间：{_now()}。*",
        "*评分结果仅供参考，最终选型须结合完整数据手册、实际工况及企业器件合格供应商清单（AVL）综合评估。*",
    ]

    return "\n".join(lines)
