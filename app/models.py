"""Pydantic data models for the Component Risk Agent."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------- Request / Response Envelope ----------

class AnalyzeRequest(BaseModel):
    user_input: str


class AnalyzeResponse(BaseModel):
    request_id: str
    ir_version: str = "0.2"
    constraints: Dict[str, Any] = {}
    candidates: List[ScoredPart] = []
    recommended_parts: List[str] = []
    evidence: List[EvidenceRecord] = []
    risks: Optional[RiskAssessment] = None
    tool_steps: List[ToolStep] = []


# ---------- Requirement Constraints ----------

class RequirementConstraints(BaseModel):
    category: str = ""
    topology: str = ""
    application: str = ""
    grade: str = ""
    input_voltage_nominal_v: Optional[float] = None
    output_voltage_v: Optional[float] = None
    output_current_a: Optional[float] = None
    temperature_min_c: Optional[float] = None
    temperature_max_c: Optional[float] = None
    preferences: List[str] = []


# ---------- Part ----------

class PartInfo(BaseModel):
    part_number: str
    manufacturer: str
    category: str = ""
    topology: str = ""
    is_domestic: bool = False
    input_voltage_min_v: Optional[float] = None
    input_voltage_max_v: Optional[float] = None
    output_current_max_a: Optional[float] = None
    temperature_min_c: Optional[float] = None
    temperature_max_c: Optional[float] = None
    automotive_grade: bool = False
    package: str = ""
    stock: int = 0
    unit_price_cny: float = 0.0
    lifecycle_status: str = ""
    datasheet_url: str = ""
    image_url: str = ""
    replacement_for: List[str] = []


# ---------- Score ----------

class ScoreBreakdown(BaseModel):
    total_score: float = 0.0
    parameter_match_score: float = 0.0
    supply_risk_score: float = 0.0
    cost_score: float = 0.0
    domestic_score: float = 0.0
    evidence_score: float = 0.0
    reasons: List[str] = []


class ScoredPart(BaseModel):
    part: PartInfo
    score: ScoreBreakdown
    rank: int = 0
    recommendation_level: str = "not_recommended"  # recommended | backup | not_recommended


# ---------- Evidence ----------

class EvidenceRecord(BaseModel):
    part_number: str
    evidence_type: str  # datasheet | lifecycle | stock | cross_ref | compliance
    claim: str
    source: str
    source_field: str = ""
    confidence: float = 0.0
    extracted_at: str = ""


# ---------- Risk ----------

class RiskItem(BaseModel):
    severity: str = ""  # low | medium | high
    description: str = ""
    mitigation: str = ""


class RiskAssessment(BaseModel):
    overall_risk_level: str = ""
    risk_items: List[RiskItem] = []


# ---------- Tool Step (for visualization) ----------

class ToolStep(BaseModel):
    """Represents a single tool-call step in the agent pipeline, exposed for UI visualization."""
    step_index: int
    tool_name: str
    tool_label: str  # human-readable label for the card header
    tool_icon: str = "🔧"
    status: str = "running"  # running | success | error
    duration_ms: float = 0.0
    input_summary: str = ""  # short description of what was passed in
    output_summary: str = ""  # short description of what was returned
    intermediate_result: Any = None  # full intermediate payload (collapsible)
    error_message: str = ""
    timestamp: str = ""