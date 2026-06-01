import uuid
from typing import List, Optional
from .schemas import (
    SelectionReport, RequirementConstraints, ScoredPart,
    RiskIR, RiskItem,
)


def _assess_risks(constraints: RequirementConstraints, scored: List[ScoredPart]) -> RiskIR:
    """基于候选器件列表和需求约束，规则化生成风险条目。"""
    risk_items: List[RiskItem] = []
    recommended = [s for s in scored if s.recommendation_level == "recommended"]

    # ── 供应链风险 ────────────────────────────────────────────────

    # 1. 无任何候选
    if not scored:
        risk_items.append(RiskItem(
            risk_type="supply",
            severity="high",
            description="检索无结果，请确认类别/拓扑约束或扩充数据源。",
            mitigation="检查 EZ-PLM API 白名单覆盖情况，或补充 mock 数据。",
        ))

    # 2. 有候选但无推荐（全部 backup/not_recommended）
    elif not recommended:
        risk_items.append(RiskItem(
            risk_type="supply",
            severity="high",
            description=f"共 {len(scored)} 条候选器件，但无满足推荐门槛（≥75分）的结果，需放宽约束或补充数据。",
            mitigation="考虑放宽温度范围或电流要求，或引入更多国产器件数据。",
        ))

    else:
        # 3. 推荐仅一条（单点风险）
        if len(recommended) == 1:
            risk_items.append(RiskItem(
                risk_type="supply",
                severity="medium",
                description=f"仅 1 款推荐器件（{recommended[0].part.part_number}），备选方案不足。",
                mitigation="纳入 backup 级器件作为冗余，或向供应商确认长期备货计划。",
            ))

        # 4. 推荐器件库存全部偏低
        low_stock = [s for s in recommended if s.part.stock is not None and s.part.stock < 100]
        if low_stock:
            pns = "、".join(s.part.part_number for s in low_stock)
            if len(low_stock) == len(recommended):
                risk_items.append(RiskItem(
                    risk_type="supply",
                    severity="high",
                    description=f"所有推荐器件库存均低于 100 件（{pns}），存在断货风险。",
                    related_part_number=pns,
                    mitigation="立即确认补货周期；向分销商预定或启用 backup 器件。",
                ))
            else:
                risk_items.append(RiskItem(
                    risk_type="supply",
                    severity="medium",
                    description=f"部分推荐器件库存偏低（{pns}）。",
                    related_part_number=pns,
                    mitigation="关注上述器件库存动态，提前预定。",
                ))

        # 5. 推荐列表含停产器件
        eol = [s for s in recommended
               if s.part.lifecycle_status
               and s.part.lifecycle_status.lower() in ("obsolete", "discontinued")]
        for s in eol:
            risk_items.append(RiskItem(
                risk_type="supply",
                severity="high",
                description=f"{s.part.part_number} 已停产（{s.part.lifecycle_status}），不建议新项目选用。",
                related_part_number=s.part.part_number,
                mitigation="切换至同系列在产型号，或选用国产替代。",
            ))

        # 6. 供应商集中度风险（3 条以上全来自同一厂商）
        mfrs = [s.part.manufacturer for s in recommended if s.part.manufacturer]
        if len(recommended) >= 3 and mfrs and len(set(mfrs)) == 1:
            risk_items.append(RiskItem(
                risk_type="supply",
                severity="medium",
                description=f"推荐器件全部来自同一制造商（{mfrs[0]}），存在供应商集中风险。",
                mitigation="建议引入第二供应商，降低单一来源依赖。",
            ))

        # 7. 要求国产替代但推荐全为进口
        prefs = getattr(constraints, "preferences", []) or []
        if "domestic_alternative" in prefs and all(not s.part.is_domestic for s in recommended):
            risk_items.append(RiskItem(
                risk_type="supply",
                severity="medium",
                description="用户偏好国产替代，但当前推荐器件均为进口，国产化目标未达成。",
                mitigation="扩充国产器件库，或联系国产厂商获取样品评估。",
            ))

    # ── 工程/技术风险 ─────────────────────────────────────────────

    if recommended:
        # 8. 要求车规但无车规认证器件
        if getattr(constraints, "grade", None) == "automotive":
            non_auto = [s for s in recommended if not s.part.automotive_grade]
            if len(non_auto) == len(recommended):
                pns = "、".join(s.part.part_number for s in non_auto)
                risk_items.append(RiskItem(
                    risk_type="engineering",
                    severity="high",
                    description="需求要求车规等级，但所有推荐器件均非车规认证，不可直接用于车载产品。",
                    related_part_number=pns,
                    mitigation="重新筛选 AEC-Q100 认证器件，或向制造商确认车规版本。",
                ))

        # 9. 参数匹配平均分偏低
        avg_param = sum(s.score.parameter_match_score for s in recommended) / len(recommended)
        if avg_param < 50:
            risk_items.append(RiskItem(
                risk_type="engineering",
                severity="medium",
                description=f"推荐器件参数匹配度偏低（均值 {avg_param:.0f} 分），部分参数余量不足。",
                mitigation="核实输入电压范围、输出电流余量是否满足实际工况，必要时重新选型。",
            ))

    # ── P0 新增：数据完整性风险 ──────────────────────────────────
    _all_parts = scored or []
    # 10. 生命周期状态全部未知
    if _all_parts and all(not p.part.lifecycle_status for p in _all_parts):
        risk_items.append(RiskItem(
            risk_type="supply",
            severity="medium",
            description=f"全部 {len(_all_parts)} 条候选器件的生命周期状态未知，无法评估停产/断供风险。",
            mitigation="从制造商官网或授权分销商处确认各器件当前生命周期状态（Active/NRND/EOL）。",
        ))

    # 11. 库存信息全部缺失
    if _all_parts and all(p.part.stock is None for p in _all_parts):
        risk_items.append(RiskItem(
            risk_type="supply",
            severity="medium",
            description="全部候选器件的当前库存信息缺失，无法评估现货供应能力与交期。",
            mitigation="通过 eZ-PLM API 或分销商接口获取实时库存数据。",
        ))

    # 12. 封装信息全部缺失
    if _all_parts and all(not p.part.package for p in _all_parts):
        risk_items.append(RiskItem(
            risk_type="engineering",
            severity="low",
            description="全部候选器件的封装信息缺失，PCB Layout 评估缺少依据。",
            mitigation="从数据手册或制造商网站获取封装代码与推荐焊盘图纸。",
        ))

    # 13. 地缘政治/贸易合规风险（推荐器件全部来自单一非国产供应商）
    if recommended:
        all_mfrs = {p.part.manufacturer for p in recommended if p.part.manufacturer}
        if len(recommended) >= 2 and len(all_mfrs) == 1:
            sole_mfr = next(iter(all_mfrs))
            if not any(p.part.is_domestic for p in recommended):
                risk_items.append(RiskItem(
                    risk_type="supply",
                    severity="medium",
                    description=f"推荐器件全部来自境外单一供应商 {sole_mfr}，存在贸易管制/关税变动的地缘政治风险。",
                    mitigation="纳入至少 1 家国产兼容型号作为第二供应源，或评估非美国来源替代方案。",
                ))

    # ── 整体风险等级 ──────────────────────────────────────────────
    severities = {r.severity for r in risk_items}
    if "high" in severities:
        overall = "high"
    elif "medium" in severities:
        overall = "medium"
    else:
        overall = "low"

    supply_items = [r for r in risk_items if r.risk_type == "supply"]
    eng_items = [r for r in risk_items if r.risk_type == "engineering"]

    return RiskIR(
        overall_risk_level=overall,
        risk_items=risk_items,
        supply_risk_summary=(
            "；".join(r.description for r in supply_items) if supply_items else "供应链风险可控"
        ),
        engineering_risk_summary=(
            "；".join(r.description for r in eng_items) if eng_items else "工程参数匹配正常"
        ),
    )


def _build_summary(
    constraints: RequirementConstraints,
    scored: List[ScoredPart],
    risks: RiskIR,
) -> str:
    recommended = [s for s in scored if s.recommendation_level == "recommended"]
    backup = [s for s in scored if s.recommendation_level == "backup"]

    lines = [
        "## 选型报告摘要",
        "",
        f"**需求**：{constraints.raw_input}",
        "",
        f"**检索结果**：共 {len(scored)} 条候选，"
        f"**{len(recommended)} 条推荐**，{len(backup)} 条备选。",
    ]

    if recommended:
        top = recommended[0]
        p = top.part
        mfr = f"（{p.manufacturer}）" if p.manufacturer else ""
        lines += [
            "",
            f"**首选推荐**：`{p.part_number}`{mfr}",
            f"- 综合得分：**{top.score.total_score}**"
            f"（参数 {top.score.parameter_match_score}"
            f" | 供应 {top.score.supply_risk_score}"
            f" | 成本 {top.score.cost_score}"
            f" | 国产 {top.score.domestic_score}）",
        ]
        key_reasons = [r for r in top.score.reasons if "✓" in r or "满足" in r]
        if key_reasons:
            lines.append(f"- 关键依据：{key_reasons[0]}")

    risk_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(risks.overall_risk_level, "⚪")
    lines += [
        "",
        f"**整体风险**：{risk_emoji} {risks.overall_risk_level.upper()}",
        f"- 供应链：{risks.supply_risk_summary}",
        f"- 工程：{risks.engineering_risk_summary}",
    ]

    return "\n".join(lines)


def build_report(
    constraints: RequirementConstraints,
    scored: List[ScoredPart],
    evidence: List,
    request_id: Optional[str] = None,
) -> SelectionReport:
    if request_id is None:
        request_id = str(uuid.uuid4())
    recommended = [s for s in scored if s.recommendation_level == "recommended"]
    risks = _assess_risks(constraints, scored)
    summary = _build_summary(constraints, scored, risks)
    return SelectionReport(
        request_id=request_id,
        user_input=constraints.raw_input if constraints else "",
        constraints=constraints,
        candidates=scored,
        recommended_parts=recommended,
        risks=risks,
        evidence=evidence,
        summary_markdown=summary,
    )
