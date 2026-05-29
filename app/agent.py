"""Agent inference pipeline that orchestrates tool calls and captures ToolSteps for visualization."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.models import (
    AnalyzeRequest,
    AnalyzeResponse,
    EvidenceRecord,
    PartInfo,
    RiskAssessment,
    RiskItem,
    ScoreBreakdown,
    ScoredPart,
    ToolStep,
)
from app.tools import (
    ToolException,
    tool_assess_risks,
    tool_generate_evidence,
    tool_parse_requirement,
    tool_score_candidates,
    tool_search_parts,
)


def run_agent(request: AnalyzeRequest) -> AnalyzeResponse:
    """Execute the full agent pipeline and return a response with tool_steps included."""
    tool_steps: List[ToolStep] = []
    step_counter = 1

    def _record_step(
        tool_name: str,
        tool_label: str,
        tool_icon: str,
        input_summary: str,
        output_summary: str = "",
        status: str = "success",
        intermediate_result: Any = None,
        error_message: str = "",
        duration_ms: float = 0.0,
    ) -> ToolStep:
        nonlocal step_counter
        ts = ToolStep(
            step_index=step_counter,
            tool_name=tool_name,
            tool_label=tool_label,
            tool_icon=tool_icon,
            status=status,
            duration_ms=duration_ms,
            input_summary=input_summary,
            output_summary=output_summary,
            intermediate_result=intermediate_result,
            error_message=error_message,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        tool_steps.append(ts)
        step_counter += 1
        return ts

    # ============================================================
    # STEP 1: Parse Requirement
    # ============================================================
    t0 = time.perf_counter()
    try:
        constraints = tool_parse_requirement(request.user_input)
        duration = (time.perf_counter() - t0) * 1000
        _record_step(
            tool_name="requirement_parser",
            tool_label="解析需求约束",
            tool_icon="📝",
            input_summary=f'需求文本: "{request.user_input[:80]}{"..." if len(request.user_input) > 80 else ""}"',
            output_summary=f"提取到 {len(constraints)} 个约束字段, 首选项: {constraints.get('preferences', [])}",
            status="success",
            intermediate_result=constraints,
            duration_ms=round(duration, 1),
        )
    except ToolException as exc:
        duration = (time.perf_counter() - t0) * 1000
        _record_step(
            tool_name="requirement_parser",
            tool_label="解析需求约束",
            tool_icon="📝",
            input_summary=f'需求文本: "{request.user_input[:80]}"',
            status="error",
            error_message=str(exc),
            duration_ms=round(duration, 1),
        )
        return AnalyzeResponse(
            request_id=str(uuid.uuid4())[:8],
            tool_steps=tool_steps,
        )

    # ============================================================
    # STEP 2: Search Parts
    # ============================================================
    t0 = time.perf_counter()
    try:
        search_result = tool_search_parts(constraints)
        candidates_raw = search_result.get("candidates", [])
        duration = (time.perf_counter() - t0) * 1000
        _record_step(
            tool_name="parts_search",
            tool_label="候选器件检索",
            tool_icon="🔍",
            input_summary=f'约束: Vin={constraints.get("input_voltage_nominal_v")}V, Vout={constraints.get("output_voltage_v")}V, Iout={constraints.get("output_current_a")}A, Grade={constraints.get("grade")}',
            output_summary=f"从 {len(_ALL_PARTS())} 个器件中检索到 {len(candidates_raw)} 个候选",
            status="success",
            intermediate_result={
                "total_candidates": len(candidates_raw),
                "candidates_preview": [c["part_number"] for c in candidates_raw[:10]],
                "filters_applied": search_result.get("filters_applied", {}),
            },
            duration_ms=round(duration, 1),
        )
    except ToolException as exc:
        duration = (time.perf_counter() - t0) * 1000
        _record_step(
            tool_name="parts_search",
            tool_label="候选器件检索",
            tool_icon="🔍",
            input_summary=f'约束: Vin={constraints.get("input_voltage_nominal_v")}V',
            status="error",
            error_message=str(exc),
            duration_ms=round(duration, 1),
        )
        return AnalyzeResponse(
            request_id=str(uuid.uuid4())[:8],
            constraints=constraints,
            tool_steps=tool_steps,
        )

    if not candidates_raw:
        # No candidates – still record but stop
        _record_step(
            tool_name="scoring",
            tool_label="多维评分",
            tool_icon="📊",
            input_summary=f"候选数: 0",
            output_summary="无可用候选，跳过评分",
            status="success",
            intermediate_result=None,
            duration_ms=0.0,
        )
        return AnalyzeResponse(
            request_id=str(uuid.uuid4())[:8],
            constraints=constraints,
            tool_steps=tool_steps,
        )

    # ============================================================
    # STEP 3: Score Candidates
    # ============================================================
    t0 = time.perf_counter()
    try:
        score_result = tool_score_candidates(candidates_raw, constraints)
        scored = score_result.get("scored_candidates", [])
        duration = (time.perf_counter() - t0) * 1000
        score_counts = {
            "recommended": len([s for s in scored if s.get("recommendation_level") == "recommended"]),
            "backup": len([s for s in scored if s.get("recommendation_level") == "backup"]),
            "not_recommended": len([s for s in scored if s.get("recommendation_level") == "not_recommended"]),
        }
        _record_step(
            tool_name="scoring",
            tool_label="多维度评分与排序",
            tool_icon="📊",
            input_summary=f"对 {len(candidates_raw)} 个候选进行 5 维评分",
            output_summary=f'评分完成: ⭐{score_counts["recommended"]} 推荐 / 🟡{score_counts["backup"]} 备选 / 🔴{score_counts["not_recommended"]} 不推荐',
            status="success",
            intermediate_result={
                "score_distribution": score_counts,
                "top_3": [
                    {
                        "pn": s["part"]["part_number"],
                        "total": s["score"]["total_score"],
                        "level": s["recommendation_level"],
                    }
                    for s in scored[:3]
                ],
            },
            duration_ms=round(duration, 1),
        )
    except ToolException as exc:
        duration = (time.perf_counter() - t0) * 1000
        _record_step(
            tool_name="scoring",
            tool_label="多维评分",
            tool_icon="📊",
            input_summary=f"候选数: {len(candidates_raw)}",
            status="error",
            error_message=str(exc),
            duration_ms=round(duration, 1),
        )
        return AnalyzeResponse(
            request_id=str(uuid.uuid4())[:8],
            constraints=constraints,
            tool_steps=tool_steps,
        )

    # ============================================================
    # STEP 4: Generate Evidence
    # ============================================================
    t0 = time.perf_counter()
    try:
        evidence_result = tool_generate_evidence(scored, constraints)
        evidence_raw = evidence_result.get("evidence", [])
        duration = (time.perf_counter() - t0) * 1000
        _record_step(
            tool_name="evidence_generator",
            tool_label="证据链生成",
            tool_icon="📄",
            input_summary=f"为 {len(scored)} 个已评分候选生成证据",
            output_summary=f"生成 {len(evidence_raw)} 条证据记录",
            status="success",
            intermediate_result={
                "total_records": len(evidence_raw),
                "evidence_types": list({e["evidence_type"] for e in evidence_raw}),
            },
            duration_ms=round(duration, 1),
        )
    except ToolException as exc:
        duration = (time.perf_counter() - t0) * 1000
        _record_step(
            tool_name="evidence_generator",
            tool_label="证据链生成",
            tool_icon="📄",
            input_summary=f"候选数: {len(scored)}",
            status="error",
            error_message=str(exc),
            duration_ms=round(duration, 1),
        )
        evidence_raw = []

    # ============================================================
    # STEP 5: Risk Assessment
    # ============================================================
    t0 = time.perf_counter()
    try:
        risk_result = tool_assess_risks(scored, constraints)
        duration = (time.perf_counter() - t0) * 1000
        _record_step(
            tool_name="risk_assessor",
            tool_label="综合风险评估",
            tool_icon="⚠️",
            input_summary=f"对 {len(scored)} 个候选进行整体风险分析",
            output_summary=f'风险等级: {risk_result.get("overall_risk_level", "N/A").upper()}, 风险项: {len(risk_result.get("risk_items", []))} 条',
            status="success",
            intermediate_result=risk_result,
            duration_ms=round(duration, 1),
        )
    except ToolException as exc:
        duration = (time.perf_counter() - t0) * 1000
        _record_step(
            tool_name="risk_assessor",
            tool_label="综合风险评估",
            tool_icon="⚠️",
            input_summary=f"候选数: {len(scored)}",
            status="error",
            error_message=str(exc),
            duration_ms=round(duration, 1),
        )
        risk_result = {"overall_risk_level": "unknown", "risk_items": []}

    # ============================================================
    # Build response
    # ============================================================
    scored_parts = [
        ScoredPart(
            part=PartInfo(**s["part"]),
            score=ScoreBreakdown(**s["score"]),
            rank=s.get("rank", i + 1),
            recommendation_level=s.get("recommendation_level", "not_recommended"),
        )
        for i, s in enumerate(scored)
    ]

    evidence_records = [EvidenceRecord(**e) for e in evidence_raw]

    risk_assessment = RiskAssessment(
        overall_risk_level=risk_result.get("overall_risk_level", ""),
        risk_items=[RiskItem(**ri) for ri in risk_result.get("risk_items", [])],
    )

    recommended_parts = [s.part.part_number for s in scored_parts if s.recommendation_level == "recommended"]

    return AnalyzeResponse(
        request_id=str(uuid.uuid4())[:8],
        constraints=constraints,
        candidates=scored_parts,
        recommended_parts=recommended_parts,
        evidence=evidence_records,
        risks=risk_assessment,
        tool_steps=tool_steps,
    )


def _ALL_PARTS():
    """Lazy-load total parts count without re-parsing (used for step summary)."""
    from app.tools import _load_parts
    return _load_parts()