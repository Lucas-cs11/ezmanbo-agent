import os
import re as _re_core
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

# ── 推荐上限 ──────────────────────────────────────────────────────
_MAX_RECOMMENDED = 5   # 最多推荐 Top N 款
_MAX_LISTED = 15       # BOM 最多列出 N 款（含推荐+备选）

# ── 核心型号归一化（去重合并用）────────────────────────────────────
_CORE_MPN_RE = _re_core.compile(
    r"^([A-Za-z]+[0-9]+[A-Za-z0-9]*)"  # 基础型号前缀
)


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

    # ── 输出电压匹配（P0修复：固定电压器件须匹配需求输出）────────
    if constraints.output_voltage_v is not None and p.output_voltage_v is not None:
        param_checks += 1
        delta = abs(p.output_voltage_v - constraints.output_voltage_v)
        if delta < 0.01:  # 几乎精确匹配
            param_score += 1.0
            reasons.append(f"输出电压匹配 ✓（{p.output_voltage_v}V = 需求 {constraints.output_voltage_v}V）")
        elif delta / constraints.output_voltage_v <= 0.05:  # 5% 容差
            param_score += 0.6
            reasons.append(f"输出电压接近（{p.output_voltage_v}V vs 需求 {constraints.output_voltage_v}V, 偏差 {delta/constraints.output_voltage_v*100:.1f}%）")
        else:
            param_score += 0.1
            reasons.append(f"⚠ 输出电压偏差大（{p.output_voltage_v}V vs 需求 {constraints.output_voltage_v}V）")

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


def _extract_core_mpn(part_number: str) -> str:
    """从完整型号中提取核心型号（去掉封装/卷带后缀）。
    如 LM2596S-5.0/NOPB → LM2596S, TPS54020RUWT → TPS54020
    """
    if not part_number:
        return part_number
    # 常见分隔符截断
    for sep in ("/", "-TR", "-T&R", "T&R", "TR-"):
        idx = part_number.find(sep)
        if idx > 3:
            part_number = part_number[:idx]
    # 去掉末尾的封装后缀（如 RUWT, RUWR）
    m = _CORE_MPN_RE.match(part_number)
    if m:
        return m.group(1)
    return part_number


def _merge_variant_info(kept: ScoredPart, dropped: ScoredPart):
    """将 dropped 的变体信息合并到 kept 的 reasons 中。"""
    if dropped.part.package and dropped.part.package != kept.part.package:
        kept.score.reasons.append(
            f"同类变体：{dropped.part.part_number}（{dropped.part.package}）"
        )
    else:
        kept.score.reasons.append(
            f"同类变体：{dropped.part.part_number}"
        )


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

    # ── 去重合并：同核心型号保留最高分变体 ────────────────────────
    seen_cores: Dict[str, int] = {}  # core_mpn → index in scored
    deduped: List[ScoredPart] = []
    for s in scored:
        core = _extract_core_mpn(s.part.part_number)
        if core and core in seen_cores:
            prev_idx = seen_cores[core]
            prev = deduped[prev_idx]
            # 保留得分更高者，合并变体信息到 reasons
            if s.score.total_score > prev.score.total_score:
                _merge_variant_info(s, prev)
                deduped[prev_idx] = s
                seen_cores[core] = prev_idx
            else:
                _merge_variant_info(prev, s)
            continue
        if core:
            seen_cores[core] = len(deduped)
        deduped.append(s)

    # ── 排名 + 分级（Top-N 限制）─────────────────────────────────
    for idx, s in enumerate(deduped, start=1):
        s.rank = idx
        if s.score.total_score >= 75 and idx <= _MAX_RECOMMENDED:
            s.recommendation_level = "recommended"
        elif s.score.total_score >= 50:
            s.recommendation_level = "backup"
        else:
            s.recommendation_level = "not_recommended"

    # 仅返回前 _MAX_LISTED 条
    return deduped[:_MAX_LISTED]
