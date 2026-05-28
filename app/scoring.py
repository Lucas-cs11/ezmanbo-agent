import os
from typing import List, Optional, Dict, Any
from .schemas import RequirementConstraints, PartIR, ScoredPart, ScoreBreakdown

# ── 权重配置 ──────────────────────────────────────────────────────
# 纯规则模式（无 LLM 或无参考设计）
_RULE_WEIGHTS = {"parameter": 0.80, "supply": 0.20}

# 混合模式（LLM + 参考设计可用）
_HYBRID_WEIGHTS = {
    "parameter":        0.40,
    "supply":           0.10,
    "llm_application":  0.25,
    "llm_design_risk":  0.25,
}


def _normalize(v, vmin, vmax):
    if v is None:
        return 0.0
    if vmax == vmin:
        return 0.5
    return max(0.0, min(1.0, (v - vmin) / (vmax - vmin)))


def _compute_param_score(constraints: RequirementConstraints, p: PartIR) -> tuple:
    """计算参数匹配分（0-100）和说明列表。"""
    param_score = 0.0
    param_checks = 0
    reasons = []

    if (constraints.input_voltage_nominal_v is not None
            and p.input_voltage_min_v is not None
            and p.input_voltage_max_v is not None):
        param_checks += 1
        if p.input_voltage_min_v <= constraints.input_voltage_nominal_v <= p.input_voltage_max_v:
            param_score += 1.0
            reasons.append(
                f"输入电压覆盖 ✓（{p.input_voltage_min_v}–{p.input_voltage_max_v}V"
                f" 含标称 {constraints.input_voltage_nominal_v}V）"
            )
        else:
            reasons.append(
                f"输入电压不匹配（需 {constraints.input_voltage_nominal_v}V，"
                f"范围 {p.input_voltage_min_v}–{p.input_voltage_max_v}V）"
            )

    if constraints.output_current_a is not None and p.output_current_max_a is not None:
        param_checks += 1
        if p.output_current_max_a >= constraints.output_current_a:
            margin_pct = (p.output_current_max_a / max(constraints.output_current_a, 1e-6) - 1.0) * 100
            param_score += min(1.0, p.output_current_max_a / max(constraints.output_current_a, 1e-6) / 2.0)
            reasons.append(
                f"输出电流满足 ✓（{p.output_current_max_a}A，余量 {margin_pct:.0f}%）"
            )
        else:
            reasons.append(
                f"输出电流不足（需 {constraints.output_current_a}A，最大 {p.output_current_max_a}A）"
            )

    if (constraints.temperature_min_c is not None
            and constraints.temperature_max_c is not None
            and p.temperature_min_c is not None
            and p.temperature_max_c is not None):
        param_checks += 1
        if p.temperature_min_c <= constraints.temperature_min_c and p.temperature_max_c >= constraints.temperature_max_c:
            param_score += 1.0
            reasons.append(
                f"温度范围覆盖 ✓（{p.temperature_min_c}–{p.temperature_max_c}°C）"
            )
        else:
            reasons.append(
                f"温度范围不足（需 {constraints.temperature_min_c}–{constraints.temperature_max_c}°C，"
                f"实际 {p.temperature_min_c}–{p.temperature_max_c}°C）"
            )

    if param_checks == 0:
        score_norm = 50.0
    else:
        score_norm = (param_score / param_checks) * 100.0

    return score_norm, reasons


def _compute_supply_score(p: PartIR) -> tuple:
    """计算供应链稳定性分（0-100）和说明列表。"""
    supply_score = 50.0
    reasons = []

    if p.stock is not None:
        if p.stock > 1000:
            supply_score = 100.0
            reasons.append(f"库存充足（{p.stock} 件）")
        elif p.stock > 100:
            supply_score = 70.0
            reasons.append(f"库存一般（{p.stock} 件）")
        elif p.stock > 0:
            supply_score = 40.0
            reasons.append(f"库存偏低（{p.stock} 件），建议关注备货")
        else:
            supply_score = 10.0
            reasons.append("库存为零，供应风险极高")

    if p.lifecycle_status:
        if p.lifecycle_status.lower() in ("obsolete", "discontinued"):
            supply_score = min(supply_score, 10.0)
            reasons.append(f"⚠ 生命周期：{p.lifecycle_status}（停产）")
        elif p.lifecycle_status.lower() == "active":
            reasons.append("生命周期：在产")

    return supply_score, reasons


def score_candidates(
    constraints: RequirementConstraints,
    candidates: List[PartIR],
    ref_designs_map: Optional[Dict[str, List[Any]]] = None,
) -> List[ScoredPart]:
    """对候选器件评分。

    Args:
        constraints: 解析后的需求约束
        candidates:  候选器件列表
        ref_designs_map: {part_number: [reference_design, ...]}
                          由 agent_orchestrator 预先从 EZ-PLM API 拉取
    """
    has_llm_key = bool(os.getenv("OPENAI_API_KEY", "").strip())
    use_llm_scoring = has_llm_key and ref_designs_map is not None

    # 懒加载 LLM 评分函数（避免循环导入）
    _score_with_llm = None
    if use_llm_scoring:
        try:
            from .llm_client import score_part_with_llm as _score_with_llm
        except Exception:
            use_llm_scoring = False

    scored = []

    for p in candidates:
        # ── 规则评分 ──────────────────────────────────────────────
        param_score, reasons = _compute_param_score(constraints, p)
        supply_score, supply_reasons = _compute_supply_score(p)
        reasons.extend(supply_reasons)

        # 数据手册存在性
        if p.datasheet_url:
            reasons.append("有数据手册")

        # ── LLM 软评分（可选）────────────────────────────────────
        ref_designs = (ref_designs_map or {}).get(p.part_number, [])
        llm_app = None
        llm_risk = None
        llm_reasoning = None
        scoring_mode = "rule_only"

        if use_llm_scoring and ref_designs and _score_with_llm:
            part_info = {
                "part_number": p.part_number,
                "manufacturer": p.manufacturer,
                "description": p.description,
                "vin_min": p.input_voltage_min_v,
                "vin_max": p.input_voltage_max_v,
                "iout_max": p.output_current_max_a,
                "temp_min": p.temperature_min_c,
                "temp_max": p.temperature_max_c,
            }
            try:
                llm_result = _score_with_llm(
                    constraints.raw_input, part_info, ref_designs
                )
                if "application_score" in llm_result and "design_risk_score" in llm_result:
                    llm_app = float(llm_result["application_score"])
                    llm_risk = float(llm_result["design_risk_score"])
                    llm_reasoning = llm_result.get("reasoning")
                    scoring_mode = "llm_enhanced"
            except Exception:
                pass  # 出错退回 rule_only

        # ── 合并总分 ──────────────────────────────────────────────
        if scoring_mode == "llm_enhanced":
            w = _HYBRID_WEIGHTS
            total = (
                param_score  * w["parameter"]
                + supply_score * w["supply"]
                + llm_app      * w["llm_application"]
                + llm_risk     * w["llm_design_risk"]
            )
            if llm_reasoning:
                reasons.append(f"LLM 评估：{llm_reasoning}")
        else:
            w = _RULE_WEIGHTS
            total = param_score * w["parameter"] + supply_score * w["supply"]

        sb = ScoreBreakdown(
            parameter_match_score=round(param_score, 2),
            supply_risk_score=round(supply_score, 2),
            cost_score=0.0,
            domestic_score=0.0,
            evidence_score=0.0,
            total_score=round(total, 2),
            reasons=reasons,
            scoring_mode=scoring_mode,
            llm_application_score=round(llm_app, 2) if llm_app is not None else None,
            llm_design_risk_score=round(llm_risk, 2) if llm_risk is not None else None,
            llm_reasoning=llm_reasoning,
        )
        scored.append(ScoredPart(part=p, score=sb))

    scored.sort(key=lambda s: s.score.total_score, reverse=True)
    for idx, s in enumerate(scored, start=1):
        s.rank = idx
        if s.score.total_score >= 75:
            s.recommendation_level = "recommended"
        elif s.score.total_score >= 50:
            s.recommendation_level = "backup"
        else:
            s.recommendation_level = "not_recommended"

    return scored
