from __future__ import annotations
try:
    from pydantic import BaseModel, Field
    HAS_PYDANTIC = True
except Exception:
    HAS_PYDANTIC = False

from typing import List, Optional
if not HAS_PYDANTIC:
    from dataclasses import dataclass, field, asdict

    def _parse_obj_dataclass(cls, obj: dict):
        # create kwargs selecting keys matching dataclass fields
        return cls(**{k: obj.get(k) for k in cls.__annotations__.keys()})

if HAS_PYDANTIC:
    class RequirementConstraints(BaseModel):
        raw_input: str
        application: Optional[str] = None
        category: Optional[str] = None
        topology: Optional[str] = None
        input_voltage_nominal_v: Optional[float] = None
        input_voltage_min_v: Optional[float] = None
        input_voltage_max_v: Optional[float] = None
        output_voltage_v: Optional[float] = None
        output_current_a: Optional[float] = None
        temperature_min_c: Optional[float] = None
        temperature_max_c: Optional[float] = None
        grade: Optional[str] = None
        package_preference: Optional[str] = None
        preferences: List[str] = Field(default_factory=list)
        must_have: List[str] = Field(default_factory=list)
        nice_to_have: List[str] = Field(default_factory=list)

    class PartIR(BaseModel):
        part_number: str
        manufacturer: Optional[str] = None
        category: Optional[str] = None
        topology: Optional[str] = None
        is_domestic: bool = False
        description: Optional[str] = None
        input_voltage_min_v: Optional[float] = None
        input_voltage_max_v: Optional[float] = None
        output_current_max_a: Optional[float] = None
        temperature_min_c: Optional[float] = None
        temperature_max_c: Optional[float] = None
        package: Optional[str] = None
        automotive_grade: bool = False
        lifecycle_status: Optional[str] = None
        stock: Optional[int] = None
        unit_price_cny: Optional[float] = None
        datasheet_url: Optional[str] = None
        ezplm_part_id: Optional[str] = None
        replacement_for: List[str] = Field(default_factory=list)
        source: str = "mock"

    class ScoreBreakdown(BaseModel):
        parameter_match_score: float = 0.0
        supply_risk_score: float = 0.0
        cost_score: float = 0.0
        domestic_score: float = 0.0
        evidence_score: float = 0.0
        total_score: float = 0.0
        reasons: List[str] = Field(default_factory=list)
        scoring_mode: str = "rule_only"
        llm_application_score: Optional[float] = None
        llm_design_risk_score: Optional[float] = None
        llm_reasoning: Optional[str] = None

    class ScoredPart(BaseModel):
        part: PartIR
        score: ScoreBreakdown
        rank: Optional[int] = None
        recommendation_level: Optional[str] = None

    class EvidenceIR(BaseModel):
        part_number: Optional[str] = None
        claim: str
        evidence_type: str
        source: str
        source_field: Optional[str] = None
        confidence: float = 0.0
        need_human_review: bool = False

    class RiskItem(BaseModel):
        risk_type: str
        severity: str
        description: str
        related_part_number: Optional[str] = None
        mitigation: Optional[str] = None
        evidence_refs: List[str] = Field(default_factory=list)

    class RiskIR(BaseModel):
        overall_risk_level: str
        risk_items: List[RiskItem] = Field(default_factory=list)
        supply_risk_summary: Optional[str] = None
        engineering_risk_summary: Optional[str] = None

    class SelectionReport(BaseModel):
        request_id: str
        user_input: str
        constraints: RequirementConstraints
        candidates: List[ScoredPart] = Field(default_factory=list)
        recommended_parts: List[ScoredPart] = Field(default_factory=list)
        risks: Optional[RiskIR] = None
        evidence: List[EvidenceIR] = Field(default_factory=list)
        summary_markdown: Optional[str] = None
        ir_version: str = "0.1"

    class ReplacementReport(BaseModel):
        original_part: PartIR
        replacement_candidates: List[ScoredPart] = Field(default_factory=list)
        compatibility_level: str
        comparison_summary: str
        risks: Optional[RiskIR] = None
        evidence: List[EvidenceIR] = Field(default_factory=list)

else:
    # dataclass-based lightweight implementations for environments without pydantic
    @dataclass
    class RequirementConstraints:
        raw_input: str
        application: Optional[str] = None
        category: Optional[str] = None
        topology: Optional[str] = None
        input_voltage_nominal_v: Optional[float] = None
        input_voltage_min_v: Optional[float] = None
        input_voltage_max_v: Optional[float] = None
        output_voltage_v: Optional[float] = None
        output_current_a: Optional[float] = None
        temperature_min_c: Optional[float] = None
        temperature_max_c: Optional[float] = None
        grade: Optional[str] = None
        package_preference: Optional[str] = None
        preferences: List[str] = field(default_factory=list)
        must_have: List[str] = field(default_factory=list)
        nice_to_have: List[str] = field(default_factory=list)

        @classmethod
        def parse_obj(cls, obj: dict):
            return _parse_obj_dataclass(cls, obj)

        def dict(self):
            return asdict(self)

    @dataclass
    class PartIR:
        part_number: str
        manufacturer: Optional[str] = None
        category: Optional[str] = None
        topology: Optional[str] = None
        is_domestic: bool = False
        description: Optional[str] = None
        input_voltage_min_v: Optional[float] = None
        input_voltage_max_v: Optional[float] = None
        output_current_max_a: Optional[float] = None
        temperature_min_c: Optional[float] = None
        temperature_max_c: Optional[float] = None
        package: Optional[str] = None
        automotive_grade: bool = False
        lifecycle_status: Optional[str] = None
        stock: Optional[int] = None
        unit_price_cny: Optional[float] = None
        datasheet_url: Optional[str] = None
        ezplm_part_id: Optional[str] = None
        replacement_for: List[str] = field(default_factory=list)
        source: str = "mock"

        @classmethod
        def parse_obj(cls, obj: dict):
            return _parse_obj_dataclass(cls, obj)

        def dict(self):
            return asdict(self)

    @dataclass
    class ScoreBreakdown:
        parameter_match_score: float = 0.0
        supply_risk_score: float = 0.0
        cost_score: float = 0.0
        domestic_score: float = 0.0
        evidence_score: float = 0.0
        total_score: float = 0.0
        reasons: List[str] = field(default_factory=list)
        scoring_mode: str = "rule_only"
        llm_application_score: Optional[float] = None
        llm_design_risk_score: Optional[float] = None
        llm_reasoning: Optional[str] = None

        @classmethod
        def parse_obj(cls, obj: dict):
            return _parse_obj_dataclass(cls, obj)

        def dict(self):
            return asdict(self)

    @dataclass
    class ScoredPart:
        part: PartIR
        score: ScoreBreakdown
        rank: Optional[int] = None
        recommendation_level: Optional[str] = None

        @classmethod
        def parse_obj(cls, obj: dict):
            return _parse_obj_dataclass(cls, obj)

        def dict(self):
            return {"part": self.part.dict(), "score": self.score.dict(), "rank": self.rank, "recommendation_level": self.recommendation_level}

    @dataclass
    class EvidenceIR:
        part_number: Optional[str] = None
        claim: str = ""
        evidence_type: str = ""
        source: str = ""
        source_field: Optional[str] = None
        confidence: float = 0.0
        need_human_review: bool = False

        @classmethod
        def parse_obj(cls, obj: dict):
            return _parse_obj_dataclass(cls, obj)

        def dict(self):
            return asdict(self)

    @dataclass
    class RiskItem:
        risk_type: str = ""
        severity: str = ""
        description: str = ""
        related_part_number: Optional[str] = None
        mitigation: Optional[str] = None
        evidence_refs: List[str] = field(default_factory=list)

        @classmethod
        def parse_obj(cls, obj: dict):
            return _parse_obj_dataclass(cls, obj)

        def dict(self):
            return asdict(self)

    @dataclass
    class RiskIR:
        overall_risk_level: str = ""
        risk_items: List[RiskItem] = field(default_factory=list)
        supply_risk_summary: Optional[str] = None
        engineering_risk_summary: Optional[str] = None

        @classmethod
        def parse_obj(cls, obj: dict):
            return _parse_obj_dataclass(cls, obj)

        def dict(self):
            return asdict(self)

    @dataclass
    class SelectionReport:
        request_id: str = ""
        user_input: str = ""
        constraints: RequirementConstraints = field(default_factory=lambda: RequirementConstraints(raw_input=""))
        candidates: List[ScoredPart] = field(default_factory=list)
        recommended_parts: List[ScoredPart] = field(default_factory=list)
        risks: Optional[RiskIR] = None
        evidence: List[EvidenceIR] = field(default_factory=list)
        summary_markdown: Optional[str] = None
        ir_version: str = "0.1"

        @classmethod
        def parse_obj(cls, obj: dict):
            return _parse_obj_dataclass(cls, obj)

        def dict(self):
            return asdict(self)

    @dataclass
    class ReplacementReport:
        original_part: PartIR = field(default_factory=lambda: PartIR(part_number=""))
        replacement_candidates: List[ScoredPart] = field(default_factory=list)
        compatibility_level: str = ""
        comparison_summary: str = ""
        risks: Optional[RiskIR] = None
        evidence: List[EvidenceIR] = field(default_factory=list)

        @classmethod
        def parse_obj(cls, obj: dict):
            return _parse_obj_dataclass(cls, obj)

        def dict(self):
            return asdict(self)
