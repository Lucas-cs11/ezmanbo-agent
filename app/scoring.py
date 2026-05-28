from typing import List
from .schemas import RequirementConstraints, PartIR, ScoredPart, ScoreBreakdown

_BASE_WEIGHTS = {
    "parameter": 0.35,
    "supply": 0.25,
    "cost": 0.15,
    "domestic": 0.15,
    "evidence": 0.10,
}


def _normalize(v, vmin, vmax):
    if v is None:
        return 0.0
    if vmax == vmin:
        # single candidate or all same price → neutral, avoid (1-1)*100=0 bug
        return 0.5
    return max(0.0, min(1.0, (v - vmin) / (vmax - vmin)))


def _resolve_weights(constraints: RequirementConstraints) -> dict:
    """根据用户偏好动态调整各维度权重，调整后归一化至 1.0。"""
    w = dict(_BASE_WEIGHTS)
    prefs = getattr(constraints, "preferences", []) or []
    if "domestic_alternative" in prefs:
        # 优先国产：提升国产权重，微降参数匹配和成本权重
        w["domestic"] = min(0.30, w["domestic"] + 0.10)
        w["parameter"] = max(0.20, w["parameter"] - 0.05)
        w["cost"] = max(0.10, w["cost"] - 0.05)
    if "low_supply_risk" in prefs:
        # 低供应风险：提升供应权重，微降成本和证据权重
        w["supply"] = min(0.35, w["supply"] + 0.10)
        w["cost"] = max(0.05, w["cost"] - 0.05)
        w["evidence"] = max(0.05, w["evidence"] - 0.05)
    total = sum(w.values())
    return {k: v / total for k, v in w.items()}


def score_candidates(constraints: RequirementConstraints, candidates: List[PartIR]) -> List[ScoredPart]:
    scored = []
    weights = _resolve_weights(constraints)

    # 预计算成本归一化区间
    prices = [p.unit_price_cny for p in candidates if p.unit_price_cny is not None]
    min_price = min(prices) if prices else 0.0
    max_price = max(prices) if prices else min_price + 1.0

    for p in candidates:
        reasons = []

        # ── 参数匹配 ─────────────────────────────────────────────
        param_score = 0.0
        param_checks = 0  # 实际执行了多少项检查（约束非空 且 器件有对应数据）

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

        # 按实际有效检查数归一化；无可检查项时给中性分 50
        if param_checks == 0:
            param_score_norm = 50.0
        else:
            param_score_norm = (param_score / param_checks) * 100.0

        # ── 供应链风险 ────────────────────────────────────────────
        supply_score = 50.0
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

        # ── 成本 ──────────────────────────────────────────────────
        cost_score = 50.0
        if p.unit_price_cny is not None:
            price_norm = _normalize(p.unit_price_cny, min_price, max_price)
            cost_score = (1.0 - price_norm) * 100.0
            level = "较低" if price_norm < 0.33 else ("中等" if price_norm < 0.67 else "较高")
            reasons.append(f"单价 {p.unit_price_cny} 元（{level}）")

        # ── 国产化 ────────────────────────────────────────────────
        domestic_score = 100.0 if p.is_domestic else 0.0
        if p.is_domestic:
            reasons.append(f"国产器件 ✓（{p.manufacturer}）")
        else:
            reasons.append(f"进口器件（{p.manufacturer}）")

        # ── 证据覆盖 ──────────────────────────────────────────────
        evidence_score = 0.0
        if p.datasheet_url:
            evidence_score += 0.5
            reasons.append("有数据手册")
        if p.stock is not None:
            evidence_score += 0.3
        if p.lifecycle_status:
            evidence_score += 0.2
        evidence_score_norm = min(1.0, evidence_score) * 100.0

        total = (
            param_score_norm * weights["parameter"]
            + supply_score * weights["supply"]
            + cost_score * weights["cost"]
            + domestic_score * weights["domestic"]
            + evidence_score_norm * weights["evidence"]
        )

        sb = ScoreBreakdown(
            parameter_match_score=round(param_score_norm, 2),
            supply_risk_score=round(supply_score, 2),
            cost_score=round(cost_score, 2),
            domestic_score=round(domestic_score, 2),
            evidence_score=round(evidence_score_norm, 2),
            total_score=round(total, 2),
            reasons=reasons,
        )

        scored.append(ScoredPart(part=p, score=sb))

    scored.sort(key=lambda s: s.score.total_score, reverse=True)
    for idx, s in enumerate(scored, start=1):
        s.rank = idx
        # Real EZ-PLM API parts lack stock/price/domestic data → structural score cap ~60.
        # Use a lower threshold so high-parameter-match API parts can be recommended.
        is_api = getattr(s.part, "source", "mock") == "ezplm"
        rec_threshold = 55 if is_api else 75
        bak_threshold = 40 if is_api else 50
        if s.score.total_score >= rec_threshold:
            s.recommendation_level = "recommended"
        elif s.score.total_score >= bak_threshold:
            s.recommendation_level = "backup"
        else:
            s.recommendation_level = "not_recommended"

    return scored
