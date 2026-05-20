import uuid
from typing import List
from .schemas import SelectionReport, RequirementConstraints, ScoredPart, RiskIR


def build_report(constraints: RequirementConstraints, scored: List[ScoredPart], evidence: List, request_id: str = None) -> SelectionReport:
    if request_id is None:
        request_id = str(uuid.uuid4())
    recommended = [s for s in scored if s.recommendation_level == "recommended"]
    risks = RiskIR(overall_risk_level="medium", risk_items=[])
    summary = f"Found {len(scored)} candidates, {len(recommended)} recommended."
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

