from typing import List, Optional
from .schemas import ScoredPart, EvidenceIR, RequirementConstraints


def build_evidence(
    scored_parts: List[ScoredPart],
    constraints: Optional[RequirementConstraints] = None,
) -> List[EvidenceIR]:
    evidence = []
    for sp in scored_parts:
        p = sp.part
        pn = p.part_number
        src_type = "ezplm_api" if getattr(p, "source", "mock") == "api" else "mock_data"

        # ── 电压证据 ──────────────────────────────────────────────
        if p.input_voltage_min_v is not None and p.input_voltage_max_v is not None:
            evidence.append(EvidenceIR(
                part_number=pn,
                claim=f"输入电压范围 {p.input_voltage_min_v}–{p.input_voltage_max_v}V",
                evidence_type=src_type,
                source=pn,
                source_field="input_voltage",
                confidence=0.95,
            ))

        # ── 电流证据 ──────────────────────────────────────────────
        if p.output_current_max_a is not None:
            evidence.append(EvidenceIR(
                part_number=pn,
                claim=f"最大输出电流 {p.output_current_max_a}A",
                evidence_type=src_type,
                source=pn,
                source_field="output_current_max_a",
                confidence=0.90,
            ))

        # ── 温度证据 ──────────────────────────────────────────────
        if p.temperature_min_c is not None and p.temperature_max_c is not None:
            evidence.append(EvidenceIR(
                part_number=pn,
                claim=f"工作温度范围 {p.temperature_min_c}–{p.temperature_max_c}°C",
                evidence_type=src_type,
                source=pn,
                source_field="temperature",
                confidence=0.95,
            ))

        # ── 库存证据 ──────────────────────────────────────────────
        if p.stock is not None:
            is_zero = p.stock == 0
            evidence.append(EvidenceIR(
                part_number=pn,
                claim=(
                    f"当前库存 {p.stock} 件（零库存，存在供应中断风险）"
                    if is_zero else f"当前库存 {p.stock} 件"
                ),
                evidence_type=src_type,
                source=pn,
                source_field="stock",
                confidence=0.90,
                need_human_review=is_zero,
            ))

        # ── 生命周期证据 ──────────────────────────────────────────
        if p.lifecycle_status:
            is_eol = p.lifecycle_status.lower() in ("obsolete", "discontinued")
            evidence.append(EvidenceIR(
                part_number=pn,
                claim=(
                    f"生命周期状态：{p.lifecycle_status}（停产，不建议用于新项目）"
                    if is_eol else f"生命周期状态：{p.lifecycle_status}"
                ),
                evidence_type=src_type,
                source=pn,
                source_field="lifecycle_status",
                confidence=0.95,
                need_human_review=is_eol,
            ))

        # ── 车规认证证据 ──────────────────────────────────────────
        if p.automotive_grade:
            has_datasheet = bool(p.datasheet_url)
            evidence.append(EvidenceIR(
                part_number=pn,
                claim=f"{pn} 具备车规认证（AEC-Q100/Q101）",
                evidence_type="automotive_cert",
                source=p.datasheet_url or pn,
                source_field="automotive_grade",
                # 有数据手册可核查置高置信；无则需人工复核
                confidence=0.85 if has_datasheet else 0.60,
                need_human_review=not has_datasheet,
            ))
        elif constraints and getattr(constraints, "grade", None) == "automotive":
            # 需求要求车规，但该器件未标注车规认证
            evidence.append(EvidenceIR(
                part_number=pn,
                claim=f"{pn} 未标注车规认证，但需求要求车规等级，需人工确认是否可用",
                evidence_type="automotive_cert",
                source=pn,
                source_field="automotive_grade",
                confidence=0.30,
                need_human_review=True,
            ))

        # ── 国产化证据 ────────────────────────────────────────────
        if p.is_domestic:
            mfr = p.manufacturer or "国内厂商"
            evidence.append(EvidenceIR(
                part_number=pn,
                claim=f"{pn} 为国产器件（{mfr}），满足国产化替代需求",
                evidence_type="domestic_origin",
                source=pn,
                source_field="is_domestic",
                confidence=0.90,
            ))

        # ── 价格证据 ──────────────────────────────────────────────
        if p.unit_price_cny is not None:
            evidence.append(EvidenceIR(
                part_number=pn,
                claim=f"参考单价 ¥{p.unit_price_cny}（人民币，仅供参考）",
                evidence_type=src_type,
                source=pn,
                source_field="unit_price_cny",
                confidence=0.80,
            ))

        # ── 数据手册证据 / 缺失标记 ──────────────────────────────
        if p.datasheet_url:
            evidence.append(EvidenceIR(
                part_number=pn,
                claim=f"{pn} 数据手册可查，规格参数可进一步核实",
                evidence_type="datasheet",
                source=p.datasheet_url,
                source_field="datasheet_url",
                confidence=0.95,
            ))
        else:
            evidence.append(EvidenceIR(
                part_number=pn,
                claim=f"{pn} 无已知数据手册链接，规格核实依赖平台数据，建议人工复核",
                evidence_type="missing_datasheet",
                source=pn,
                source_field="datasheet_url",
                confidence=0.50,
                need_human_review=True,
            ))

    return evidence
