from typing import List
from .schemas import ScoredPart, EvidenceIR


def build_evidence(scored_parts: List[ScoredPart]) -> List[EvidenceIR]:
    evidence = []
    for sp in scored_parts:
        p = sp.part
        pn = p.part_number
        # temperature evidence
        if p.temperature_min_c is not None and p.temperature_max_c is not None:
            evidence.append(EvidenceIR(part_number=pn, claim=f"supports temperature range {p.temperature_min_c}C to {p.temperature_max_c}C", evidence_type="mock_ezplm_field", source=pn, source_field="temperature_min_c", confidence=0.95))
        # voltage evidence
        if p.input_voltage_min_v is not None and p.input_voltage_max_v is not None:
            evidence.append(EvidenceIR(part_number=pn, claim=f"input voltage range {p.input_voltage_min_v}V to {p.input_voltage_max_v}V", evidence_type="mock_ezplm_field", source=pn, source_field="input_voltage_min_v", confidence=0.95))
        # current evidence
        if p.output_current_max_a is not None:
            evidence.append(EvidenceIR(part_number=pn, claim=f"output current max {p.output_current_max_a}A", evidence_type="mock_ezplm_field", source=pn, source_field="output_current_max_a", confidence=0.9))
        # stock/lifecycle evidence
        if p.stock is not None:
            evidence.append(EvidenceIR(part_number=pn, claim=f"stock {p.stock}", evidence_type="mock_ezplm_field", source=pn, source_field="stock", confidence=0.9))
        if p.lifecycle_status:
            evidence.append(EvidenceIR(part_number=pn, claim=f"lifecycle {p.lifecycle_status}", evidence_type="mock_ezplm_field", source=pn, source_field="lifecycle_status", confidence=0.9))
    return evidence

