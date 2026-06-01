import os
from typing import List, Optional, Dict, Any
from .requirement_parser import parse_requirement
from .ezplm_client import search_parts, find_replacements, fetch_reference_designs
from .scoring import score_candidates
from .evidence import build_evidence
from .report_generator import build_report, _assess_risks
from .schemas import (
    SelectionReport, ReplacementReport,
    RequirementConstraints, PartIR, ScoredPart, EvidenceIR,
)


def _build_rag_query(user_input: str, req: RequirementConstraints) -> str:
    """从用户需求和解析后的约束构建 RAG 查询文本。"""
    parts = [user_input]
    if req.topology:
        parts.append(req.topology)
    if req.category:
        parts.append(req.category)
    if req.output_voltage_v and req.output_current_a:
        parts.append(f"{req.output_voltage_v}V {req.output_current_a}A")
    if req.grade == "automotive":
        parts.append("车规 AEC-Q100")
    return " ".join(parts)


def _query_rag_knowledge(user_input: str, req: RequirementConstraints) -> List[Dict[str, Any]]:
    """查询 RAG 知识库，获取与当前需求相关的工程知识。"""
    try:
        from .rag import get_rag_store
        store = get_rag_store()
        if store.count == 0:
            return []
        query_text = _build_rag_query(user_input, req)
        return store.query(query_text, top_k=5)
    except Exception as e:
        from .log_util import warn_swallow; warn_swallow("agent_orchestrator", e, "RAG query")
        return []


def analyze(user_input: str) -> SelectionReport:
    req = parse_requirement(user_input)
    candidates = search_parts(req)

    # ── RAG 工程知识检索 ────────────────────────────────────────
    rag_results = _query_rag_knowledge(user_input, req)

    # ── 参考设计获取（仅 EZ-PLM API 器件，LLM key 存在时）────────
    ref_designs_map = {}
    if os.getenv("OPENAI_API_KEY", "").strip():
        api_parts = [c for c in candidates if getattr(c, "source", "mock") == "ezplm"][:10]
        for p in api_parts:
            if p.ezplm_part_id:
                designs = fetch_reference_designs(p.ezplm_part_id)
                if designs:
                    ref_designs_map[p.part_number] = designs

    scored = score_candidates(req, candidates, ref_designs_map=ref_designs_map or None)
    evidence = build_evidence(scored, req)

    # ── RAG 证据注入 ────────────────────────────────────────────
    if rag_results:
        from .rag import build_context_from_results
        rag_context = build_context_from_results(rag_results)
        # 将 RAG 检索结果作为证据链的一条独立证据
        evidence.append(EvidenceIR(
            part_number=None,
            claim=f"已从工程知识库检索到 {len(rag_results)} 条相关参考知识，用于增强选型决策。",
            evidence_type="rag_knowledge",
            source="ChromaDB 向量知识库",
            confidence=min(0.85, max(r["score"] for r in rag_results) + 0.3),
        ))

    report = build_report(req, scored, evidence)
    return report


# ── 替换报告辅助函数 ───────────────────────────────────────────────

def _assess_compatibility(scored: List[ScoredPart]) -> str:
    """根据最优推荐器件的综合得分估算兼容等级。"""
    if not scored:
        return "none"
    top_score = scored[0].score.total_score
    if top_score >= 85:
        return "drop_in"
    elif top_score >= 70:
        return "functional_equivalent"
    elif top_score >= 50:
        return "pin_compatible"
    return "not_recommended"


def _build_comparison_summary(
    original_pn: str,
    scored: List[ScoredPart],
    compat: str,
) -> str:
    """生成结构化中文替换报告摘要（Markdown）。"""
    compat_label = {
        "drop_in":             "直接替换（Drop-in）",
        "functional_equivalent": "功能等效替代",
        "pin_compatible":      "引脚兼容，需验证参数",
        "not_recommended":     "不推荐，参数差异较大",
        "none":                "无可用替代",
    }.get(compat, compat)

    recommended = [s for s in scored if s.recommendation_level == "recommended"]
    backup = [s for s in scored if s.recommendation_level == "backup"]

    lines = [
        f"## 替换报告：`{original_pn}`",
        "",
        f"**兼容等级**：{compat_label}",
        f"**检索结果**：共 {len(scored)} 款候选，"
        f"**{len(recommended)} 款推荐**，{len(backup)} 款备选。",
    ]

    if recommended:
        top = recommended[0]
        p = top.part
        mfr = f"（{p.manufacturer}）" if p.manufacturer else ""
        lines += [
            "",
            f"**首选替代**：`{p.part_number}`{mfr}",
            f"- 综合得分：**{top.score.total_score}**"
            f"（参数 {top.score.parameter_match_score}"
            f" | 供应 {top.score.supply_risk_score}）",
        ]

    if scored:
        lines += [
            "",
            "| 排名 | 型号 | 厂商 | 得分 | 推荐级别 |",
            "|------|------|------|------|----------|",
        ]
        level_map = {
            "recommended": "推荐",
            "backup": "备选",
            "not_recommended": "不推荐",
        }
        for s in scored[:5]:
            p = s.part
            lvl = level_map.get(s.recommendation_level or "", "-")
            lines.append(
                f"| {s.rank} | `{p.part_number}` | {p.manufacturer or '-'} "
                f"| {s.score.total_score} | {lvl} |"
            )

    return "\n".join(lines)


# ── 主入口 ────────────────────────────────────────────────────────

def replacement_report(original_part_number: str) -> ReplacementReport:
    replacements = find_replacements(original_part_number)

    if not replacements:
        return ReplacementReport(
            original_part=PartIR(part_number=original_part_number),
            replacement_candidates=[],
            compatibility_level="none",
            comparison_summary=(
                f"## 替换报告：`{original_part_number}`\n\n"
                f"未找到该器件的替代型号，建议扩充数据源或联系供应商。"
            ),
        )

    req = RequirementConstraints(raw_input=f"替换 {original_part_number}")
    scored = score_candidates(req, replacements)
    evidence = build_evidence(scored, req)
    risks = _assess_risks(req, scored)
    compat = _assess_compatibility(scored)
    summary = _build_comparison_summary(original_part_number, scored, compat)

    return ReplacementReport(
        original_part=PartIR(part_number=original_part_number),
        replacement_candidates=scored,
        compatibility_level=compat,
        comparison_summary=summary,
        risks=risks,
        evidence=evidence,
    )
