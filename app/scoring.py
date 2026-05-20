from typing import List
from .schemas import RequirementConstraints, PartIR, ScoredPart, ScoreBreakdown


def _normalize(v, vmin, vmax):
    if v is None:
        return 0.0
    if vmax == vmin:
        return 1.0
    return max(0.0, min(1.0, (v - vmin) / (vmax - vmin)))


def score_candidates(constraints: RequirementConstraints, candidates: List[PartIR]) -> List[ScoredPart]:
    scored = []

    # define weights matching docs
    weights = {
        "parameter": 0.35,
        "supply": 0.25,
        "cost": 0.15,
        "domestic": 0.15,
        "evidence": 0.10,
    }

    # precompute for cost normalization
    prices = [p.unit_price_cny for p in candidates if p.unit_price_cny is not None]
    min_price = min(prices) if prices else 0.0
    max_price = max(prices) if prices else min_price + 1.0

    for p in candidates:
        reasons = []
        # parameter matching
        param_score = 0.0
        param_components = []
        # voltage coverage
        if constraints.input_voltage_nominal_v is not None and p.input_voltage_min_v is not None and p.input_voltage_max_v is not None:
            if p.input_voltage_min_v <= constraints.input_voltage_nominal_v <= p.input_voltage_max_v:
                param_score += 1.0
                param_components.append("input_voltage_ok")
            else:
                param_components.append("input_voltage_mismatch")
        # output current
        if constraints.output_current_a is not None and p.output_current_max_a is not None:
            # give partial credit if margin exists
            if p.output_current_max_a >= constraints.output_current_a:
                margin = p.output_current_max_a / max(constraints.output_current_a, 1e-6)
                param_score += min(1.0, margin / 2.0)  # cap
                param_components.append(f"current_margin_{margin:.2f}")
            else:
                param_components.append("current_insufficient")
        # temperature
        if constraints.temperature_min_c is not None and constraints.temperature_max_c is not None and p.temperature_min_c is not None and p.temperature_max_c is not None:
            if p.temperature_min_c <= constraints.temperature_min_c and p.temperature_max_c >= constraints.temperature_max_c:
                param_score += 1.0
                param_components.append("temp_range_ok")
            else:
                param_components.append("temp_range_mismatch")

        # normalize parameter score (max possible 3)
        param_score_norm = (param_score / 3.0) * 100.0

        # supply risk score: stock and lifecycle
        supply_score = 50.0
        if p.stock is not None:
            if p.stock > 1000:
                supply_score = 100.0
            elif p.stock > 100:
                supply_score = 70.0
            elif p.stock > 0:
                supply_score = 40.0
            else:
                supply_score = 10.0
        if p.lifecycle_status and p.lifecycle_status.lower() in ("obsolete", "discontinued"):
            supply_score = min(supply_score, 10.0)

        # cost: lower price -> higher score
        cost_score = 50.0
        if p.unit_price_cny is not None:
            # invert normalized price
            price_norm = _normalize(p.unit_price_cny, min_price, max_price)
            cost_score = (1.0 - price_norm) * 100.0

        # domestic
        domestic_score = 100.0 if p.is_domestic else 0.0

        # evidence: presence of datasheet_url and lifecycle/stock fields
        evidence_score = 0.0
        ev_reasons = []
        if p.datasheet_url:
            evidence_score += 0.5
            ev_reasons.append("datasheet")
        if p.stock is not None:
            evidence_score += 0.3
            ev_reasons.append("stock_field")
        if p.lifecycle_status:
            evidence_score += 0.2
            ev_reasons.append("lifecycle_field")
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
            reasons=param_components + ev_reasons,
        )

        sp = ScoredPart(part=p, score=sb)
        scored.append(sp)

    # sort by total score desc
    scored.sort(key=lambda s: s.score.total_score, reverse=True)
    # assign ranks and recommendation level
    for idx, s in enumerate(scored, start=1):
        s.rank = idx
        if s.score.total_score >= 75:
            s.recommendation_level = "recommended"
        elif s.score.total_score >= 50:
            s.recommendation_level = "backup"
        else:
            s.recommendation_level = "not_recommended"

    return scored

