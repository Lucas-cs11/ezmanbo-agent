"""Tool definitions for the Component Risk Agent.

Each tool is a callable that receives a typed input dict and returns a typed output dict,
plus throws a ToolException on failure so the agent can capture error ToolSteps.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------- Exception ----------


class ToolException(Exception):
    """Raised when a tool fails – the agent will capture this as an error ToolStep."""


# ---------- Helper ----------

_PARTS_CACHE: Optional[List[Dict[str, Any]]] = None


def _load_parts() -> List[Dict[str, Any]]:
    global _PARTS_CACHE
    if _PARTS_CACHE is not None:
        return _PARTS_CACHE
    data_path = Path(__file__).resolve().parent.parent / "data" / "mock_parts.json"
    if not data_path.exists():
        raise ToolException(f"Parts database not found: {data_path}")
    _PARTS_CACHE = json.loads(data_path.read_text(encoding="utf-8"))
    return _PARTS_CACHE


# ---------- Tool implementations ----------


def tool_parse_requirement(user_input: str) -> Dict[str, Any]:
    """Parse a natural-language requirement into structured constraints."""
    time.sleep(0.3)  # simulate parsing delay

    text = user_input.lower()

    # ------- simple keyword-based parser (can be replaced with LLM) -------
    constraints: Dict[str, Any] = {
        "category": "dc_dc_converter",
        "topology": "buck",
        "application": "",
        "grade": "",
        "input_voltage_nominal_v": None,
        "output_voltage_v": None,
        "output_current_a": None,
        "temperature_min_c": None,
        "temperature_max_c": None,
        "preferences": [],
    }

    # voltage pattern: XXV → YYV  or  XXV 转 YYV
    import re

    vpat = re.findall(r"(\d+\.?\d*)\s*v\s*(?:转|→|to|\s+)*\s*(\d+\.?\d*)\s*v", text)
    if vpat:
        constraints["input_voltage_nominal_v"] = float(vpat[0][0])
        constraints["output_voltage_v"] = float(vpat[0][1])

    # current: X.XA or XA
    cpat = re.findall(r"(\d+\.?\d*)\s*a", text)
    if cpat:
        constraints["output_current_a"] = float(cpat[0])

    # temperature range
    tpat = re.findall(r"(-?\d+)\s*°?c?\s*(?:~|到|to|\s+)*\s*(-?\d+)\s*°?c?", text)
    if tpat:
        constraints["temperature_min_c"] = float(tpat[0][0])
        constraints["temperature_max_c"] = float(tpat[0][1])
    elif re.search(r"(-?\d+)\s*°?c", text):
        # single temperature
        tm = re.findall(r"(-?\d+)\s*°?c", text)
        if tm:
            t = float(tm[0])
            constraints["temperature_min_c"] = t
            constraints["temperature_max_c"] = t + 20  # guess range

    # grade
    if any(k in text for k in ("车规", "automotive", "aec", "aec-q100")):
        constraints["grade"] = "automotive"
        constraints["application"] = "automotive"
    elif any(k in text for k in ("工业", "industrial")):
        constraints["grade"] = "industrial"
        constraints["application"] = "industrial"
    else:
        constraints["grade"] = "commercial"
        constraints["application"] = "general"

    # preferences
    if any(k in text for k in ("国产", "国内", "domestic", "china")):
        constraints["preferences"].append("domestic")
    if any(k in text for k in ("低供应风险", "供应风险低", "low supply risk", "低风险")):
        constraints["preferences"].append("low_supply_risk")
    if any(k in text for k in ("性价比", "成本最低", "便宜", "cheap", "low cost")):
        constraints["preferences"].append("cost_sensitive")
    if any(k in text for k in ("大功率", "高功率", "high power")):
        constraints["preferences"].append("high_power")

    return constraints


def tool_search_parts(constraints: Dict[str, Any]) -> Dict[str, Any]:
    """Search the parts database with structured constraints and return matching candidates."""
    time.sleep(0.25)

    parts = _load_parts()
    matches: List[Dict[str, Any]] = []

    vin = constraints.get("input_voltage_nominal_v")
    vout = constraints.get("output_voltage_v")
    iout = constraints.get("output_current_a")
    tmin = constraints.get("temperature_min_c")
    tmax = constraints.get("temperature_max_c")
    grade = constraints.get("grade", "")
    preferences = constraints.get("preferences", [])

    for p in parts:
        # must cover input voltage range
        if vin is not None:
            vmin = p.get("input_voltage_min_v", 0)
            vmax = p.get("input_voltage_max_v", 0)
            if vin < vmin or vin > vmax:
                continue

        # output current must be ≥ required
        if iout is not None:
            if (p.get("output_current_max_a") or 0) < iout:
                continue

        # temperature range must cover required
        if tmin is not None and tmax is not None:
            ptmin = p.get("temperature_min_c", -1000)
            ptmax = p.get("temperature_max_c", 1000)
            if tmin < ptmin or tmax > ptmax:
                continue

        # grade filter (loose)
        if grade == "automotive" and not p.get("automotive_grade"):
            continue

        matches.append(p)

    # If nothing matches, relax grade constraint
    if not matches and grade == "automotive":
        for p in parts:
            if vin is not None:
                vmin = p.get("input_voltage_min_v", 0)
                vmax = p.get("input_voltage_max_v", 0)
                if vin < vmin or vin > vmax:
                    continue
            if iout is not None and (p.get("output_current_max_a") or 0) < iout:
                continue
            if tmin is not None and tmax is not None:
                ptmin = p.get("temperature_min_c", -1000)
                ptmax = p.get("temperature_max_c", 1000)
                if tmin < ptmin or tmax > ptmax:
                    continue
            matches.append(p)

    return {"candidates": matches, "total": len(matches), "filters_applied": {"vin": vin, "vout": vout, "iout": iout, "tmin": tmin, "tmax": tmax, "grade": grade}}


def tool_score_candidates(candidates: List[Dict[str, Any]], constraints: Dict[str, Any]) -> Dict[str, Any]:
    """Multi-dimensional scoring of candidate parts."""
    time.sleep(0.2)
    scored: List[Dict[str, Any]] = []

    preferences = constraints.get("preferences", [])
    grade = constraints.get("grade", "")
    iout_req = constraints.get("output_current_a")

    for part in candidates:
        reasons: List[str] = []

        # 1. Parameter match (0-100)
        param_score = 80.0
        if iout_req and (part.get("output_current_max_a") or 0) >= iout_req * 1.5:
            param_score += 10
            reasons.append("充足的电流裕量 (≥1.5x)")
        if grade == "automotive" and part.get("automotive_grade"):
            param_score += 10
            reasons.append("满足车规认证")
        param_score = min(param_score, 100)

        # 2. Supply risk (0-100)
        stock = part.get("stock", 0)
        lifecycle = part.get("lifecycle_status", "")
        if lifecycle == "active" and stock > 5000:
            supply_score = 100.0
            reasons.append("库存充足，活跃量产")
        elif lifecycle == "active" and stock > 1000:
            supply_score = 80.0
            reasons.append("库存适中，活跃量产")
        elif lifecycle == "active":
            supply_score = 60.0
            reasons.append("库存偏低")
        elif lifecycle == "obsolete":
            supply_score = 10.0
            reasons.append("已停产，供应风险极高")
        elif lifecycle == "discontinued":
            supply_score = 5.0
            reasons.append("已停售")
        else:
            supply_score = 40.0

        # 3. Cost score (0-100): cheaper → higher
        price = part.get("unit_price_cny", 100)
        if price <= 3:
            cost_score = 100.0
            reasons.append("单价极低 (≤¥3)")
        elif price <= 6:
            cost_score = 85.0
            reasons.append("单价较低 (≤¥6)")
        elif price <= 10:
            cost_score = 65.0
            reasons.append("单价中等 (≤¥10)")
        elif price <= 15:
            cost_score = 45.0
            reasons.append("单价偏高")
        else:
            cost_score = 25.0
            reasons.append("单价高")

        # 4. Domestic score (0-100)
        dom_score = 100.0 if part.get("is_domestic") else 30.0
        if part.get("is_domestic"):
            reasons.append("国产器件")
        else:
            reasons.append("进口器件")

        # 5. Evidence score (0-100)
        evidence_score = 70.0
        if part.get("datasheet_url"):
            evidence_score += 15
        if part.get("replacement_for"):
            evidence_score += 15
            reasons.append(f'可替代 {", ".join(part["replacement_for"])}')
        evidence_score = min(evidence_score, 100)

        # Weighted total
        total = (
            param_score * 0.35 +
            supply_score * 0.25 +
            cost_score * 0.15 +
            dom_score * 0.10 +
            evidence_score * 0.15
        )

        # Boost for matching preferences
        if "domestic" in preferences and part.get("is_domestic"):
            total += 8
            reasons.append("满足国产偏好")
        if "low_supply_risk" in preferences and supply_score >= 80:
            total += 5
            reasons.append("低供应风险")
        if "cost_sensitive" in preferences and cost_score >= 80:
            total += 5
            reasons.append("满足成本敏感偏好")
        if "high_power" in preferences and (part.get("output_current_max_a") or 0) >= 8:
            total += 5
            reasons.append("大功率满足")

        total = min(round(total, 1), 100)

        scored.append({
            "part": part,
            "score": {
                "total_score": total,
                "parameter_match_score": round(param_score, 1),
                "supply_risk_score": round(supply_score, 1),
                "cost_score": round(cost_score, 1),
                "domestic_score": round(dom_score, 1),
                "evidence_score": round(evidence_score, 1),
                "reasons": reasons,
            },
        })

    # Sort by total descending
    scored.sort(key=lambda x: x["score"]["total_score"], reverse=True)

    # Recommendation level
    for i, s in enumerate(scored):
        t = s["score"]["total_score"]
        if t >= 70:
            s["recommendation_level"] = "recommended"
        elif t >= 45:
            s["recommendation_level"] = "backup"
        else:
            s["recommendation_level"] = "not_recommended"
        s["rank"] = i + 1

    return {"scored_candidates": scored}


def tool_generate_evidence(scored_candidates: List[Dict[str, Any]], constraints: Dict[str, Any]) -> Dict[str, Any]:
    """Generate evidence records for each scored candidate."""
    time.sleep(0.25)
    evidence_records: List[Dict[str, Any]] = []

    for sc in scored_candidates:
        p = sc["part"]
        pn = p.get("part_number", "N/A")

        # Datasheet evidence
        if p.get("datasheet_url"):
            evidence_records.append({
                "part_number": pn,
                "evidence_type": "datasheet",
                "claim": f"技术规格来自官方数据手册",
                "source": p.get("datasheet_url", ""),
                "source_field": "electrical_characteristics",
                "confidence": 0.98,
            })

        # Lifecycle
        evidence_records.append({
            "part_number": pn,
            "evidence_type": "lifecycle",
            "claim": f"生命周期状态: {p.get('lifecycle_status', 'N/A')}",
            "source": f"mock://lifecycle/{pn}",
            "source_field": "lifecycle_status",
            "confidence": 0.90 if p.get("lifecycle_status") == "active" else 0.70,
        })

        # Stock
        stock = p.get("stock", 0)
        evidence_records.append({
            "part_number": pn,
            "evidence_type": "stock",
            "claim": f"当前库存: {stock} pcs",
            "source": f"mock://inventory/{pn}",
            "source_field": "available_stock",
            "confidence": 0.85 if stock > 500 else 0.60,
        })

        # Cross reference
        repl = p.get("replacement_for", [])
        if repl:
            evidence_records.append({
                "part_number": pn,
                "evidence_type": "cross_ref",
                "claim": f'可替代型号: {", ".join(repl)}',
                "source": "mock://cross_reference/db",
                "source_field": "replacement_for",
                "confidence": 0.82,
            })

        # Compliance / Automotive
        if p.get("automotive_grade"):
            evidence_records.append({
                "part_number": pn,
                "evidence_type": "compliance",
                "claim": "通过 AEC-Q100 车规认证",
                "source": "mock://cert/aec-q100",
                "source_field": "qualification",
                "confidence": 0.95,
            })

    return {"evidence": evidence_records, "total_records": len(evidence_records)}


def tool_assess_risks(scored_candidates: List[Dict[str, Any]], constraints: Dict[str, Any]) -> Dict[str, Any]:
    """Assess overall risks across the candidate pool."""
    time.sleep(0.2)

    risk_items: List[Dict[str, Any]] = []

    # Check if any are not recommended
    not_rec = [s for s in scored_candidates if s.get("recommendation_level") == "not_recommended"]
    if not_rec:
        risk_items.append({
            "severity": "medium",
            "description": f"{len(not_rec)} 个候选器件未达到推荐标准",
            "mitigation": "考虑放宽部分约束条件或更换选型视角",
        })

    # Stock risk
    low_stock = [s for s in scored_candidates if s["part"].get("stock", 0) < 500]
    if low_stock:
        risk_items.append({
            "severity": "high",
            "description": f"{len(low_stock)} 个候选器件库存不足 (<500 pcs)，存在供应中断风险",
            "mitigation": "优先选择库存 > 5000 的器件，联系供应商确认交期",
        })

    # Domestic preference not met
    if "domestic" in constraints.get("preferences", []):
        non_dom = [s for s in scored_candidates if not s["part"].get("is_domestic")]
        if non_dom and not any(s["part"].get("is_domestic") for s in scored_candidates):
            risk_items.append({
                "severity": "medium",
                "description": "未找到满足需求的国产替代器件",
                "mitigation": "补充更多国产器件数据源，或考虑调整电气参数范围",
            })

    # Lifecycle risk
    obsolete_parts = [s for s in scored_candidates if s["part"].get("lifecycle_status") in ("obsolete", "discontinued")]
    if obsolete_parts:
        risk_items.append({
            "severity": "high",
            "description": f"{len(obsolete_parts)} 个候选器件已停产或停售",
            "mitigation": "立即排除停产器件，寻找 cross-reference 替代",
        })

    # Determine overall
    if any(r["severity"] == "high" for r in risk_items):
        overall = "high"
    elif any(r["severity"] == "medium" for r in risk_items):
        overall = "medium"
    else:
        overall = "low"

    return {
        "overall_risk_level": overall,
        "risk_items": risk_items,
    }