"""
output_generator.py — 三份标准化工程输出文件生成模块

生成内容：
  1. 元器件选型清单（BOM）         — 纯结构化，无需 LLM
  2. 供应链与工程风险评估报告      — 规则验证事实 + LLM 叙述综合
  3. 电路功能模块拓扑结构分析      — 规则模板 + LLM 工程细化

报告风格：学术化、产业规范化，参照 IPC/IEC/IEEE 术语体系。
"""

from __future__ import annotations

import os
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from .schemas import SelectionReport, RequirementConstraints, ScoredPart, RiskItem


# ═══════════════════════════════════════════════════════════════════
# 工具函数
# ═══════════════════════════════════════════════════════════════════

def _severity_cn(severity: str) -> str:
    return {"high": "高 (High)", "medium": "中 (Medium)", "low": "低 (Low)"}.get(
        severity.lower(), severity
    )


def _risk_type_cn(risk_type: str) -> str:
    return {"supply": "供应链风险", "engineering": "工程技术风险"}.get(risk_type, risk_type)


def _lifecycle_cn(status: Optional[str]) -> str:
    if not status:
        return "未知"
    mapping = {
        "active": "现行 (Active)",
        "obsolete": "停产 (Obsolete)",
        "discontinued": "停产 (Discontinued)",
        "nrnd": "不推荐新设计 (NRND)",
    }
    return mapping.get(status.lower(), status)


def _rec_level_cn(level: Optional[str]) -> str:
    return {"recommended": "推荐", "backup": "备选", "not_recommended": "不推荐"}.get(
        level or "", "-"
    )


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def _call_llm(system: str, user: str) -> str:
    """调用 LLM，失败时返回空字符串。"""
    try:
        from .llm_client import call_openai_chat
        if not os.getenv("OPENAI_API_KEY", "").strip():
            return ""
        return call_openai_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.0,
        )
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════════
# 1. 元器件选型清单（BOM）
# ═══════════════════════════════════════════════════════════════════

def generate_bom(report: SelectionReport) -> str:
    """生成符合 IPC 命名规范的元器件选型清单（Markdown）。"""
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
        f"| 工作温度范围 | {f'{c.temperature_min_c} ~ {c.temperature_max_c} °C' if c.temperature_min_c is not None else '未指定'} |",
        f"| 应用等级 | {c.grade or '工业级 (Industrial)'} |",
        f"| 检索候选数量 | {len(report.candidates)} |",
        f"| 推荐器件数量 | {len(rec)} |",
        "",
    ]

    # ── 推荐器件清单 ─────────────────────────────────────────────
    lines += [
        "## 一、推荐器件清单（Recommended Components）",
        "",
        "> 推荐级别说明：推荐器件满足全部关键约束，综合评分达标；备选器件参数部分满足，供工程师进一步评估。",
        "",
        "| 序号 | 制造商型号 (MPN) | 制造商 | 规格描述 | 封装 | 生命周期状态 | 综合评分 | 参数评分 | 供应链评分 | 评分模式 | 推荐级别 |",
        "|------|----------------|--------|---------|------|------------|---------|---------|----------|---------|---------|",
    ]
    for idx, s in enumerate(rec, 1):
        p = s.part
        sc = s.score
        desc = (p.description or "-")[:40]
        lines.append(
            f"| {idx} | {p.part_number} | {p.manufacturer or '-'} | {desc} "
            f"| {p.package or '-'} | {_lifecycle_cn(p.lifecycle_status)} "
            f"| {sc.total_score:.2f} | {sc.parameter_match_score:.2f} "
            f"| {sc.supply_risk_score:.2f} | {sc.scoring_mode} | 推荐 |"
        )

    if not rec:
        lines.append("| — | 无满足推荐门槛的器件，请参阅备选清单 | | | | | | | | | |")

    lines.append("")

    # ── 备选器件清单 ─────────────────────────────────────────────
    lines += [
        "## 二、备选器件清单（Alternative Components）",
        "",
        "| 序号 | 制造商型号 (MPN) | 制造商 | 规格描述 | 封装 | 生命周期状态 | 综合评分 | 推荐级别 |",
        "|------|----------------|--------|---------|------|------------|---------|---------|",
    ]
    for idx, s in enumerate(bak[:10], 1):
        p = s.part
        desc = (p.description or "-")[:40]
        lines.append(
            f"| {idx} | {p.part_number} | {p.manufacturer or '-'} | {desc} "
            f"| {p.package or '-'} | {_lifecycle_cn(p.lifecycle_status)} "
            f"| {s.score.total_score:.2f} | 备选 |"
        )
    if not bak:
        lines.append("| — | 无备选器件 | | | | | | |")

    lines.append("")

    # ── 关键参数对比（推荐器件前 5） ─────────────────────────────
    lines += [
        "## 三、关键电气参数对比（Key Electrical Parameters）",
        "",
        "| 制造商型号 (MPN) | 输入电压范围 (V) | 最大输出电流 (A) | 工作温度范围 (°C) | 车规认证 |",
        "|----------------|---------------|----------------|----------------|---------|",
    ]
    for s in (rec + bak)[:5]:
        p = s.part
        vin = (f"{p.input_voltage_min_v} ~ {p.input_voltage_max_v}"
               if p.input_voltage_min_v is not None else "-")
        iout = str(p.output_current_max_a) if p.output_current_max_a is not None else "-"
        temp = (f"{p.temperature_min_c} ~ {p.temperature_max_c}"
                if p.temperature_min_c is not None else "-")
        auto = "是 (AEC-Q100/Q101)" if p.automotive_grade else "否"
        lines.append(f"| {p.part_number} | {vin} | {iout} | {temp} | {auto} |")

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
        "---",
        "",
        f"*本文件由 ezplm-component-risk-agent 自动生成，生成时间：{_now()}。*",
        "*评分结果仅供参考，最终选型须结合完整数据手册、实际工况及企业器件合格供应商清单（AVL）综合评估。*",
    ]

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 2. 供应链与工程风险评估报告
# ═══════════════════════════════════════════════════════════════════

def _build_risk_context(report: SelectionReport) -> str:
    """为 LLM 构建结构化风险事实文本（仅包含规则验证结果）。"""
    risks = report.risks
    if not risks:
        return "无风险数据。"
    lines = [f"整体风险等级：{risks.overall_risk_level.upper()}"]
    for i, item in enumerate(risks.risk_items, 1):
        lines.append(
            f"[R{i:02d}] 类型：{_risk_type_cn(item.risk_type)} | "
            f"严重程度：{_severity_cn(item.severity)} | "
            f"描述：{item.description} | "
            f"缓解建议：{item.mitigation or '待评估'}"
        )
    return "\n".join(lines)


def _llm_executive_summary(report: SelectionReport, constraints: RequirementConstraints) -> str:
    """LLM 生成执行摘要，仅基于规则验证的风险事实，不得新增声明。"""
    risk_context = _build_risk_context(report)
    rec_count = len(report.recommended_parts)
    top_pn = report.recommended_parts[0].part.part_number if report.recommended_parts else "无"

    system = (
        "你是一名专业的电子工程供应链风险分析师，负责撰写学术化、产业规范化的风险评估报告执行摘要。"
        "你的摘要必须严格基于提供的规则验证风险条目，不得引入未经规则识别的新风险声明，不得使用非正式语言或表情符号。"
        "摘要使用正式中文，段落简洁，最多 200 字。"
    )
    user = (
        f"选型需求：{constraints.raw_input}\n"
        f"推荐器件数量：{rec_count}，首选型号：{top_pn}\n"
        f"规则验证风险条目：\n{risk_context}\n\n"
        "请撰写风险评估报告执行摘要（2~3 段，不超过 200 字，不含标题，不含序号）。"
        "内容须涵盖：整体风险等级说明、主要风险来源概述、建议行动要点。"
    )
    result = _call_llm(system, user)
    return result.strip() if result else (
        f"本次选型检索到 {len(report.candidates)} 条候选器件，其中 {rec_count} 条满足推荐门槛。"
        f"规则评估识别到 {len(report.risks.risk_items if report.risks else [])} 项风险条目，"
        f"整体风险等级为 {(report.risks.overall_risk_level.upper() if report.risks else '未知')}。"
        "详细风险分析见各章节。"
    )


def _llm_risk_elaboration(risk_items: list, section_type: str) -> str:
    """LLM 对规则验证的风险条目进行工程语境下的补充说明。"""
    if not risk_items:
        return "本评估周期内，规则引擎未识别到该类别下的风险条目。"

    items_text = "\n".join(
        f"- [{_severity_cn(r.severity)}] {r.description}（建议：{r.mitigation or '待评估'}）"
        for r in risk_items
    )
    system = (
        "你是一名电子工程师，专注于元器件选型与供应链风险评估。"
        "请对以下规则验证的风险条目进行简要的工程背景说明，不超过 150 字，不得引入新风险声明，使用正式中文。"
    )
    user = (
        f"以下为规则引擎验证的{section_type}风险条目：\n{items_text}\n\n"
        "请从工程实践角度补充说明这些风险的潜在影响，并概述优先应对策略（不含序号、标题，纯段落文字）。"
    )
    result = _call_llm(system, user)
    return result.strip() if result else "（LLM 叙述不可用，请参阅上方规则验证条目。）"


def generate_risk_report(
    report: SelectionReport,
    constraints: RequirementConstraints,
) -> str:
    """生成供应链与工程风险评估报告（Markdown）。

    架构原则：
    - 规则引擎(_assess_risks)识别的风险条目为事实基础，不可篡改
    - LLM 仅负责叙述综合与工程背景补充，不新增风险声明
    - 每节明确标注数据来源（规则验证 / AI 辅助分析）
    """
    risks = report.risks
    risk_items = risks.risk_items if risks else []
    supply_items = [r for r in risk_items if r.risk_type == "supply"]
    eng_items    = [r for r in risk_items if r.risk_type == "engineering"]
    review_items = [e for e in report.evidence if e.need_human_review]
    overall = risks.overall_risk_level.upper() if risks else "UNKNOWN"

    lines: List[str] = []

    # ── 文件头 ──────────────────────────────────────────────────────
    lines += [
        "# 供应链与工程风险评估报告",
        "",
        "## 文件信息",
        "",
        f"| 字段 | 内容 |",
        f"|------|------|",
        f"| 生成日期 | {_now()} |",
        f"| 需求标识 | {report.request_id[:8]} |",
        f"| 原始需求 | {constraints.raw_input} |",
        f"| 整体风险等级 | {overall} |",
        f"| 规则验证风险条目数 | {len(risk_items)} |",
        f"| 供应链风险 | {len(supply_items)} 条 |",
        f"| 工程技术风险 | {len(eng_items)} 条 |",
        f"| 需人工复核项 | {len(review_items)} 条 |",
        "",
    ]

    # ── 执行摘要 ─────────────────────────────────────────────────
    lines += [
        "## 一、执行摘要",
        "",
        "> **数据来源声明**：本节综合摘要由 AI 语言模型基于规则验证风险条目生成，",
        "> 所有结论均可在后续章节中追溯至具体规则触发依据。",
        "",
        _llm_executive_summary(report, constraints),
        "",
    ]

    # ── 评估方法与数据来源 ────────────────────────────────────────
    lines += [
        "## 二、评估方法与数据来源",
        "",
        "### 2.1 评估方法",
        "",
        "本报告采用双层评估架构：",
        "",
        "**第一层：规则引擎验证（Rule-Based Verification）**",
        "",
        "基于预定义规则集对候选器件进行确定性风险识别，共覆盖 9 类风险规则：",
        "- 供应链规则（7 条）：无候选器件、无推荐器件、单点依赖、库存水平、",
        "  生命周期状态、供应商集中度；",
        "- 工程技术规则（2 条）：车规认证符合性、参数匹配充裕度。",
        "",
        "规则验证结论具有确定性，不受模型推理影响。",
        "",
        "**第二层：AI 辅助分析（AI-Assisted Analysis）**",
        "",
        "基于 eZ-PLM 参考设计库数据，由 LLM 对规则验证结论进行工程背景补充说明。",
        "AI 辅助分析仅在规则识别结论基础上进行叙述综合，不独立产生风险判定。",
        "",
        "### 2.2 数据来源",
        "",
        "| 数据类型 | 来源 | 置信度评估 |",
        "|---------|------|-----------|",
        "| 器件电气参数 | eZ-PLM API 实时查询 / Mock 数据 | 高（平台字段） |",
        "| 库存与生命周期 | eZ-PLM API | 中（实时性依赖平台更新频率） |",
        "| 参考设计 | eZ-PLM 参考设计库 | 中（案例覆盖度因器件而异） |",
        "| 规则推理 | 本地规则引擎 | 高（确定性逻辑） |",
        "| AI 叙述 | LLM 综合生成 | 低至中（须工程师核实） |",
        "",
    ]

    # ── 风险识别结果 ─────────────────────────────────────────────
    lines += [
        "## 三、风险识别结果",
        "",
        "### 3.1 风险汇总矩阵",
        "",
        "> **来源**：规则引擎验证（Rule-Based Verification）",
        "",
        "| 编号 | 风险类型 | 严重程度 | 风险描述摘要 | 相关器件 | 缓解建议 |",
        "|------|---------|---------|------------|---------|---------|",
    ]
    for i, item in enumerate(risk_items, 1):
        related = item.related_part_number or "-"
        desc_short = item.description[:50] + ("..." if len(item.description) > 50 else "")
        mit_short  = (item.mitigation or "-")[:50] + ("..." if item.mitigation and len(item.mitigation) > 50 else "")
        lines.append(
            f"| R{i:02d} | {_risk_type_cn(item.risk_type)} | {_severity_cn(item.severity)} "
            f"| {desc_short} | {related} | {mit_short} |"
        )
    if not risk_items:
        lines.append("| — | — | — | 规则引擎未识别到风险条目，当前选型结果可接受 | — | — |")

    lines.append("")

    # ── 供应链风险详述 ────────────────────────────────────────────
    lines += [
        "### 3.2 供应链风险详述",
        "",
        "> **来源**：规则引擎验证（Rule-Based Verification）",
        "",
    ]
    if supply_items:
        for i, item in enumerate(supply_items, 1):
            lines += [
                f"#### 3.2.{i} {item.description[:40]}",
                "",
                f"- **严重程度**：{_severity_cn(item.severity)}",
                f"- **风险描述**：{item.description}",
                f"- **相关器件**：{item.related_part_number or '—'}",
                f"- **缓解建议**：{item.mitigation or '待评估'}",
                "",
            ]
        lines += [
            "**供应链风险工程背景说明**（AI 辅助分析）：",
            "",
            "> 以下说明由 AI 基于规则验证结果生成，仅供工程师参考，不构成独立风险判定。",
            "",
            _llm_risk_elaboration(supply_items, "供应链"),
            "",
        ]
    else:
        lines += ["当前评估周期内，规则引擎未识别到供应链风险条目。", ""]

    # ── 工程技术风险详述 ──────────────────────────────────────────
    lines += [
        "### 3.3 工程技术风险详述",
        "",
        "> **来源**：规则引擎验证（Rule-Based Verification）",
        "",
    ]
    if eng_items:
        for i, item in enumerate(eng_items, 1):
            lines += [
                f"#### 3.3.{i} {item.description[:40]}",
                "",
                f"- **严重程度**：{_severity_cn(item.severity)}",
                f"- **风险描述**：{item.description}",
                f"- **相关器件**：{item.related_part_number or '—'}",
                f"- **缓解建议**：{item.mitigation or '待评估'}",
                "",
            ]
        lines += [
            "**工程技术风险背景说明**（AI 辅助分析）：",
            "",
            "> 以下说明由 AI 基于规则验证结果生成，仅供工程师参考，不构成独立风险判定。",
            "",
            _llm_risk_elaboration(eng_items, "工程技术"),
            "",
        ]
    else:
        lines += ["当前评估周期内，规则引擎未识别到工程技术风险条目。", ""]

    # ── 需人工复核项 ──────────────────────────────────────────────
    lines += [
        "## 四、需人工复核项清单",
        "",
        "> 以下条目由证据链分析模块标记为置信度不足或数据缺失，须工程师结合数据手册及",
        "> 企业合格供应商清单（AVL）进行核实后方可采用。",
        "",
        "| 序号 | 器件型号 | 证据类型 | 复核内容 | 置信度 |",
        "|------|---------|---------|---------|-------|",
    ]
    if review_items:
        for i, ev in enumerate(review_items, 1):
            lines.append(
                f"| {i} | {ev.part_number or '-'} | {ev.evidence_type} "
                f"| {ev.claim[:60]} | {ev.confidence:.2f} |"
            )
    else:
        lines.append("| — | — | — | 无需人工复核项 | — |")

    lines.append("")

    # ── 结论与建议 ────────────────────────────────────────────────
    rec_count = len(report.recommended_parts)
    top_part = report.recommended_parts[0] if report.recommended_parts else None

    lines += [
        "## 五、结论与建议",
        "",
        f"本次选型评估检索到 {len(report.candidates)} 条候选器件，"
        f"其中 {rec_count} 条满足推荐门槛。",
        "",
    ]

    if top_part:
        lines += [
            f"首选推荐型号为 **{top_part.part.part_number}**"
            f"（{top_part.part.manufacturer or '未知厂商'}），"
            f"综合评分 {top_part.score.total_score:.2f} 分，"
            f"评分模式为 {top_part.score.scoring_mode}。",
            "",
        ]

    lines += [
        f"整体供应链与工程风险等级评定为 **{overall}**，"
        "主要风险分布见第三章风险矩阵。",
        "",
        "**建议行动事项：**",
        "",
    ]

    if any(r.severity == "high" for r in risk_items):
        lines += [
            "1. 针对高严重度（High）风险条目，须在器件锁定前完成整改或获得工程豁免。",
        ]
    if any(r.severity == "medium" for r in risk_items):
        lines += [
            "2. 中等严重度（Medium）风险条目须在量产评审（DFM/DVT）阶段进行跟踪确认。",
        ]
    if review_items:
        lines += [
            f"3. 共 {len(review_items)} 项证据置信度不足，须核查数据手册原始参数后方可定案。",
        ]
    lines += [
        "4. 推荐器件列入企业 AVL 前，须完成样品认证、AEC-Q100/Q101 符合性核实（如适用）。",
        "",
        "---",
        "",
        f"*本报告由 ezplm-component-risk-agent 自动生成，生成时间：{_now()}。*",
        "*规则验证结论具有确定性；AI 辅助分析内容标有专门声明，须经工程师审核。*",
        "*本报告不构成最终选型决策依据，最终采购须符合企业质量管理体系规定。*",
    ]

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 3. 电路功能模块拓扑结构分析
# ═══════════════════════════════════════════════════════════════════

# ── 规则模板 ──────────────────────────────────────────────────────

def _topology_mermaid_buck(
    ctrl_pn: str, vin_str: str, vout_str: str, iout_str: str
) -> str:
    return f"""```mermaid
graph LR
    VIN["输入电源<br/>{vin_str}"] --> FIN["输入滤波网络<br/>EMI 滤波 + 防反接"]
    FIN --> CTRL["Buck 控制器<br/>{ctrl_pn}"]
    CTRL -->|"PWM 驱动"| HS["上管 (High-Side MOSFET)"]
    HS --> LS["下管 (Low-Side MOSFET) / 续流二极管"]
    LS --> IND["储能电感 (L)"]
    IND --> FOUT["输出滤波电容 (COUT)"]
    FOUT --> VOUT["负载输出<br/>{vout_str} / {iout_str}"]
    FOUT -->|"电压反馈 (FB)"| CTRL
    GND["GND"] --- CTRL
    GND --- LS
```"""


def _topology_mermaid_boost(
    ctrl_pn: str, vin_str: str, vout_str: str, iout_str: str
) -> str:
    return f"""```mermaid
graph LR
    VIN["输入电源<br/>{vin_str}"] --> FIN["输入滤波网络"]
    FIN --> IND["储能电感 (L)"]
    IND --> SW["功率开关 (MOSFET)"]
    IND --> DIODE["整流二极管 (D)"]
    DIODE --> FOUT["输出滤波电容 (COUT)"]
    FOUT --> VOUT["负载输出<br/>{vout_str} / {iout_str}"]
    FOUT -->|"电压反馈 (FB)"| CTRL["Boost 控制器<br/>{ctrl_pn}"]
    CTRL -->|"PWM 驱动"| SW
    GND["GND"] --- SW
    GND --- CTRL
```"""


def _topology_mermaid_ldo(
    ctrl_pn: str, vin_str: str, vout_str: str, iout_str: str
) -> str:
    return f"""```mermaid
graph LR
    VIN["输入电源<br/>{vin_str}"] --> FIN["输入旁路电容 (CIN)"]
    FIN --> ADJ["调整管 (Pass Element)<br/>PMOS / NPN"]
    ADJ --> FOUT["输出滤波电容 (COUT)"]
    FOUT --> VOUT["稳压输出<br/>{vout_str} / {iout_str}"]
    FOUT -->|"反馈分压"| ERR["误差放大器 (EA)<br/>{ctrl_pn}"]
    ERR -->|"驱动信号"| ADJ
    GND["GND"] --- ERR
```"""


def _get_topology_mermaid(
    topology: Optional[str],
    ctrl_pn: str,
    vin_str: str,
    vout_str: str,
    iout_str: str,
) -> str:
    t = (topology or "").lower()
    if t == "boost":
        return _topology_mermaid_boost(ctrl_pn, vin_str, vout_str, iout_str)
    elif t in ("ldo", "linear"):
        return _topology_mermaid_ldo(ctrl_pn, vin_str, vout_str, iout_str)
    else:
        return _topology_mermaid_buck(ctrl_pn, vin_str, vout_str, iout_str)


_TOPO_TYPE_CN = {
    "buck": "降压型 (Buck) DC-DC 转换器",
    "boost": "升压型 (Boost) DC-DC 转换器",
    "buck_boost": "升降压型 (Buck-Boost) DC-DC 转换器",
    "ldo": "低压差线性稳压器 (LDO)",
    "linear": "线性稳压器 (Linear Regulator)",
}

_TOPO_STD_DESC = {
    "buck": (
        "降压型 DC-DC 转换器采用脉冲宽度调制（PWM）技术，通过控制功率开关管的导通占空比，"
        "将较高的输入电压转换为较低的稳定输出电压。电路拓扑由高边开关管（High-Side MOSFET）、"
        "低边同步整流管（Low-Side MOSFET）或续流二极管、储能电感及输出滤波电容构成。"
        "控制器通过对输出电压的闭环反馈调节占空比，维持输出稳定。"
    ),
    "boost": (
        "升压型 DC-DC 转换器利用电感储能原理，将较低的输入电压提升至较高的输出电压。"
        "其基本拓扑由输入滤波电感、功率开关管、整流二极管及输出滤波电容构成。"
        "当开关管导通时，电感储能；断开时，电感释放能量通过二极管向输出端充电，"
        "形成高于输入电压的输出。"
    ),
    "ldo": (
        "低压差线性稳压器（Low Dropout Regulator, LDO）通过调整串联调整管的工作点，"
        "在较小压差（通常低于 1 V）条件下实现电压稳定。相比开关电源，LDO 具有低噪声、"
        "低 EMI 的优点，适用于对纹波敏感的模拟及射频电路供电场景。"
        "其核心结构由调整管（PMOS 或 NPN 达林顿管）、误差放大器及反馈分压网络构成。"
    ),
}


def _llm_topology_details(
    constraints: RequirementConstraints,
    top_part: Optional[ScoredPart],
    mermaid_diagram: str,
) -> str:
    """LLM 生成拓扑工程细节说明（设计注意事项、关键元件选型指导）。"""
    part_info = ""
    if top_part:
        p = top_part.part
        part_info = (
            f"首选控制器：{p.part_number}（{p.manufacturer or '未知'}）\n"
            f"描述：{p.description or '—'}\n"
            f"输入电压范围：{p.input_voltage_min_v} ~ {p.input_voltage_max_v} V\n"
            f"最大输出电流：{p.output_current_max_a} A\n"
            f"工作温度范围：{p.temperature_min_c} ~ {p.temperature_max_c} °C\n"
        )

    system = (
        "你是一名资深模拟/电源电路工程师，擅长撰写专业技术文档。"
        "请基于提供的需求参数和拓扑框图，撰写拓扑结构的工程设计要点说明，"
        "包括关键无源元件（电感、电容）的典型参数估算方法和设计注意事项。"
        "不使用表情符号，语言正式，最多 300 字，纯段落，不含标题。"
    )
    user = (
        f"电路需求：{constraints.raw_input}\n"
        f"拓扑类型：{constraints.topology or '降压'}\n"
        f"输入电压：{constraints.input_voltage_nominal_v or '—'} V\n"
        f"输出电压：{constraints.output_voltage_v or '—'} V\n"
        f"输出电流：{constraints.output_current_a or '—'} A\n"
        f"{part_info}\n"
        "请说明该拓扑的主要无源元件参数估算要点及工程设计注意事项。"
    )
    result = _call_llm(system, user)
    return result.strip() if result else "（LLM 工程细节分析不可用，请参阅相关数据手册应用笔记。）"


def generate_topology(
    constraints: RequirementConstraints,
    report: SelectionReport,
) -> str:
    """生成电路功能模块拓扑结构分析文档（Markdown + Mermaid）。"""
    topology = constraints.topology or "buck"
    topo_cn = _TOPO_TYPE_CN.get(topology.lower(), topology)
    topo_desc = _TOPO_STD_DESC.get(topology.lower(), "")

    top_part = report.recommended_parts[0] if report.recommended_parts else None
    ctrl_pn = top_part.part.part_number if top_part else "待定"

    vin_str = f"{constraints.input_voltage_nominal_v} V" if constraints.input_voltage_nominal_v else "VIN"
    vout_str = f"{constraints.output_voltage_v} V" if constraints.output_voltage_v else "VOUT"
    iout_str = f"{constraints.output_current_a} A" if constraints.output_current_a else "IOUT"

    mermaid = _get_topology_mermaid(topology, ctrl_pn, vin_str, vout_str, iout_str)

    lines: List[str] = []

    # ── 文件头 ──────────────────────────────────────────────────────
    lines += [
        "# 电路功能模块拓扑结构分析",
        "",
        "## 文件信息",
        "",
        f"| 字段 | 内容 |",
        f"|------|------|",
        f"| 生成日期 | {_now()} |",
        f"| 需求标识 | {report.request_id[:8]} |",
        f"| 原始需求 | {constraints.raw_input} |",
        f"| 拓扑类型 | {topo_cn} |",
        f"| 首选控制器 | {ctrl_pn} |",
        f"| 设计参数 | 输入 {vin_str}，输出 {vout_str} / {iout_str} |",
        "",
        "> **说明**：本文件给出功能模块级（Block Level）拓扑描述，",
        "> 对应电子工程设计文档层次中的方框图（Block Diagram）阶段，",
        "> 而非完整元件级原理图（Schematic Diagram）。",
        "> 各功能模块的详细实现须参照控制器数据手册应用电路章节。",
        "",
    ]

    # ── 拓扑类型说明 ──────────────────────────────────────────────
    lines += [
        "## 一、拓扑类型及工作原理",
        "",
        f"**选定拓扑：{topo_cn}**",
        "",
        topo_desc or f"当前拓扑类型（{topology}）的标准描述不可用，请参阅相关教材。",
        "",
    ]

    # ── 功能模块框图 ──────────────────────────────────────────────
    lines += [
        "## 二、功能模块框图（Block Diagram）",
        "",
        "> 框图采用 Mermaid 流程图语法描述，可在 GitHub、Obsidian 等环境中直接渲染。",
        "> 框图中各节点代表功能子模块，箭头表示信号或功率流向，不代表物理连线关系。",
        "",
        mermaid,
        "",
    ]

    # ── 模块功能说明 ──────────────────────────────────────────────
    topo_modules = {
        "buck": [
            ("输入滤波网络", "抑制来自输入电源的差模与共模噪声，防止开关噪声反向传导；通常包含 EMI 滤波电感、X/Y 电容及输入旁路电容（CIN）。"),
            ("控制器（Controller IC）", f"核心控制单元（型号：{ctrl_pn}），内置振荡器、误差放大器、PWM 比较器及栅极驱动器，实现对输出电压的闭环调节。"),
            ("功率开关网络（High/Low Side）", "由上管（High-Side MOSFET）与下管（Low-Side MOSFET 或续流二极管）构成，承担功率变换的核心开关动作。"),
            ("储能电感（L）", "在开关管导通与截止期间储存和释放磁能，实现能量的连续传递，是 Buck 拓扑的核心储能元件。"),
            ("输出滤波电容（COUT）", "滤除电感纹波电流引起的输出电压波动，维持输出电压稳定；低 ESR 特性对动态响应至关重要。"),
        ],
        "boost": [
            ("输入滤波网络", "防止开关噪声反向传导至输入电源。"),
            ("储能电感（L）", "在开关管导通期间储能，断开期间释放能量，驱动输出电压高于输入电压。"),
            ("功率开关（MOSFET）", f"由控制器（{ctrl_pn}）的 PWM 信号驱动，控制电感充放电节奏。"),
            ("整流二极管（D）", "阻断开关管导通期间的反向电流，确保能量单向流向输出端；同步整流可替代二极管以降低导通损耗。"),
            ("输出滤波电容（COUT）", "滤除纹波电流，稳定输出电压。"),
        ],
        "ldo": [
            ("输入旁路电容（CIN）", "稳定输入端电压，抑制高频噪声，通常取值 1 ~ 10 µF。"),
            ("调整管（Pass Element）", f"LDO 核心功率器件（由 {ctrl_pn} 内部集成或外置），工作在线性区，通过动态调节压降维持输出稳定。"),
            ("误差放大器（EA）", "将输出反馈电压与内部基准电压比较，输出误差信号驱动调整管，构成闭环控制。"),
            ("反馈分压网络", "由两只精密电阻构成，将输出电压按比例缩放后送至误差放大器反相输入端。"),
            ("输出滤波电容（COUT）", "维持环路稳定性，抑制瞬态响应时的电压跌落；LDO 对 COUT 的 ESR 范围通常有明确要求。"),
        ],
    }

    modules = topo_modules.get(topology.lower(), topo_modules.get("buck", []))
    if modules:
        lines += [
            "## 三、功能模块说明",
            "",
            "| 功能模块 | 功能描述 |",
            "|---------|---------|",
        ]
        for mod_name, mod_desc in modules:
            lines.append(f"| **{mod_name}** | {mod_desc} |")
        lines.append("")

    # ── 关键设计参数 ──────────────────────────────────────────────
    lines += [
        "## 四、关键设计参数（参考值）",
        "",
        "以下参数为典型工程估算值，最终取值须依据控制器数据手册应用笔记进行精确计算。",
        "",
        "| 设计参数 | 需求值 | 说明 |",
        "|---------|-------|------|",
        f"| 输入电压（VIN） | {vin_str} | 标称工作电压 |",
        f"| 输出电压（VOUT） | {vout_str} | 稳压目标值 |",
        f"| 最大输出电流（IOUT） | {iout_str} | 峰值负载电流 |",
    ]
    if constraints.temperature_min_c is not None:
        lines.append(f"| 工作温度范围 | {constraints.temperature_min_c} ~ {constraints.temperature_max_c} °C | 环境温度要求 |")
    if constraints.grade:
        lines.append(f"| 应用等级 | {constraints.grade} | 认证等级要求 |")
    lines.append("")

    # ── LLM 工程设计要点 ──────────────────────────────────────────
    lines += [
        "## 五、工程设计要点（AI 辅助分析）",
        "",
        "> **数据来源声明**：本节内容由 AI 语言模型基于电路拓扑参数及器件规格生成，",
        "> 属于工程参考建议，不构成正式设计规范。所有参数须依据控制器原厂数据手册",
        "> 及应用笔记进行核算验证。",
        "",
        _llm_topology_details(constraints, top_part, mermaid),
        "",
        "---",
        "",
        f"*本文件由 ezplm-component-risk-agent 自动生成，生成时间：{_now()}。*",
        "*框图为功能模块级描述，完整原理图设计须参照控制器原厂参考设计（Reference Design）。*",
    ]

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
# 统一入口：生成并保存三份报告
# ═══════════════════════════════════════════════════════════════════

def generate_all_reports(
    report: SelectionReport,
    constraints: RequirementConstraints,
    output_dir: str = "docs/reports",
) -> Dict[str, str]:
    """生成并保存三份报告，返回 {文件名: 文件路径} 映射。"""
    import os as _os
    from pathlib import Path

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    req_short = constraints.raw_input[:20].replace(" ", "_").replace("/", "-")
    base = Path(output_dir) / f"{ts}_{req_short}"
    base.mkdir(parents=True, exist_ok=True)

    files: Dict[str, str] = {}

    bom_path = base / "01_BOM_元器件选型清单.md"
    bom_path.write_text(generate_bom(report), encoding="utf-8")
    files["BOM"] = str(bom_path)

    risk_path = base / "02_风险评估报告.md"
    risk_path.write_text(generate_risk_report(report, constraints), encoding="utf-8")
    files["RiskReport"] = str(risk_path)

    topo_path = base / "03_电路拓扑结构分析.md"
    topo_path.write_text(generate_topology(constraints, report), encoding="utf-8")
    files["Topology"] = str(topo_path)

    return files
