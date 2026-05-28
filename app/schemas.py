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
        output_voltage_v: Optional[float] = None
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

    # ── TopologyIR — 电路拓扑结构化数据（eZ-PLM 兼容）─────────────

    class TopoNode(BaseModel):
        """拓扑功能节点"""
        node_id: str                              # e.g. "vin_cin", "buck_ic", "power_ind"
        node_type: str                            # input_filter | controller_ic | power_switch | diode | passive_inductor | passive_capacitor | passive_resistor | output_filter | feedback | ground | enable
        label: str                                # 中文标签，如 "输入滤波电容"
        description: str = ""                     # 功能描述
        connected_to: List[str] = Field(default_factory=list)  # 邻接 node_id 列表
        signal_type: str = "power"                # power | control | feedback | ground

    class ExternalComponent(BaseModel):
        """外围元件（围绕核心 IC 的被动器件）"""
        refdes: str = ""                          # 参考位号，如 "L1", "CIN1", "RFBT"
        component_type: str = ""                  # inductor | capacitor_mlcc | capacitor_electrolytic | resistor | diode | ferrite_bead
        value: Optional[str] = None               # 典型值，如 "6.8μH", "22μF"
        tolerance: Optional[str] = None           # 容差，如 "±20%"
        voltage_rating: Optional[str] = None      # 耐压，如 "25V"
        temperature_coefficient: Optional[str] = None  # 温度系数，如 "X7R"
        package: Optional[str] = None             # 封装，如 "0805"
        connected_nodes: List[str] = Field(default_factory=list)
        selection_notes: Optional[str] = None     # 选型备注

    class ThermalEstimate(BaseModel):
        """热性能估算"""
        estimated_efficiency_pct: float = 0.0
        output_power_w: float = 0.0
        total_power_loss_w: float = 0.0
        junction_temp_c: float = 0.0
        junction_temp_max_c: float = 125.0
        thermal_margin_c: float = 0.0
        theta_ja_assumed: float = 50.0
        needs_heatsink: bool = False

    class TopologyIR(BaseModel):
        """电路拓扑结构化中间表示 — 对接 eZ-PLM 平台"""
        topology_id: str = ""
        topology_type: str = ""                   # buck | boost | ldo | buck_boost
        controller_mpn: str = ""                  # 核心控制器型号
        controller_manufacturer: Optional[str] = None
        topology_description: str = ""            # 拓扑工作原理简述
        primary_parameters: dict = Field(default_factory=dict)
        # {vin_nominal_v, vin_min_v, vin_max_v, vout_v, iout_a, fsw_khz,
        #  temp_min_c, temp_max_c, grade}
        nodes: List[TopoNode] = Field(default_factory=list)
        external_components: List[ExternalComponent] = Field(default_factory=list)
        thermal_estimate: Optional[ThermalEstimate] = None
        mermaid_diagram: Optional[str] = None     # 功能模块框图 Mermaid 源码
        layout_rules: List[str] = Field(default_factory=list)  # PCB Layout 规则
        design_references: List[str] = Field(default_factory=list)  # 数据手册/标准引用
        rag_knowledge_refs: List[str] = Field(default_factory=list)  # RAG 知识引用
        ir_version: str = "0.1"
        generated_at: str = ""                    # ISO timestamp

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
        output_voltage_v: Optional[float] = None
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

    # ── TopologyIR dataclass 版本 ──────────────────────────────────

    @dataclass
    class TopoNode:
        node_id: str = ""
        node_type: str = ""
        label: str = ""
        description: str = ""
        connected_to: List[str] = field(default_factory=list)
        signal_type: str = "power"

        @classmethod
        def parse_obj(cls, obj: dict):
            return _parse_obj_dataclass(cls, obj)
        def dict(self):
            return asdict(self)

    @dataclass
    class ExternalComponent:
        refdes: str = ""
        component_type: str = ""
        value: Optional[str] = None
        tolerance: Optional[str] = None
        voltage_rating: Optional[str] = None
        temperature_coefficient: Optional[str] = None
        package: Optional[str] = None
        connected_nodes: List[str] = field(default_factory=list)
        selection_notes: Optional[str] = None

        @classmethod
        def parse_obj(cls, obj: dict):
            return _parse_obj_dataclass(cls, obj)
        def dict(self):
            return asdict(self)

    @dataclass
    class ThermalEstimate:
        estimated_efficiency_pct: float = 0.0
        output_power_w: float = 0.0
        total_power_loss_w: float = 0.0
        junction_temp_c: float = 0.0
        junction_temp_max_c: float = 125.0
        thermal_margin_c: float = 0.0
        theta_ja_assumed: float = 50.0
        needs_heatsink: bool = False

        @classmethod
        def parse_obj(cls, obj: dict):
            return _parse_obj_dataclass(cls, obj)
        def dict(self):
            return asdict(self)

    @dataclass
    class TopologyIR:
        topology_id: str = ""
        topology_type: str = ""
        controller_mpn: str = ""
        controller_manufacturer: Optional[str] = None
        topology_description: str = ""
        primary_parameters: dict = field(default_factory=dict)
        nodes: List = field(default_factory=list)
        external_components: List = field(default_factory=list)
        thermal_estimate: Optional[ThermalEstimate] = None  # type: ignore
        mermaid_diagram: Optional[str] = None
        layout_rules: List[str] = field(default_factory=list)
        design_references: List[str] = field(default_factory=list)
        rag_knowledge_refs: List[str] = field(default_factory=list)
        ir_version: str = "0.1"
        generated_at: str = ""

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
