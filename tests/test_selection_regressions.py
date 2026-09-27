import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.schemas import PartIR, RequirementConstraints
from app.scoring import _gate_evaluate
from app.semantic_cache import (
    SemanticCache,
    canonical_constraint_fingerprint,
)


def test_cache_fingerprint_changes_when_electrical_requirements_change():
    base = {
        "category": "dc_dc_converter",
        "topology": "buck",
        "input_voltage_nominal_v": 12,
        "output_voltage_v": 5,
        "output_current_a": 2,
        "grade": "industrial",
    }
    changed_output = {**base, "output_voltage_v": 3.3}
    changed_topology = {**base, "topology": "boost"}

    assert canonical_constraint_fingerprint(base) != canonical_constraint_fingerprint(changed_output)
    assert canonical_constraint_fingerprint(base) != canonical_constraint_fingerprint(changed_topology)


def test_cache_fingerprint_normalizes_numeric_and_key_order():
    first = {
        "output_current_a": 2.0,
        "output_voltage_v": 5,
        "input_voltage_nominal_v": 12.00,
        "topology": "buck",
    }
    second = {
        "topology": " BUCK ",
        "input_voltage_nominal_v": 12,
        "output_voltage_v": 5.0,
        "output_current_a": 2,
    }

    assert canonical_constraint_fingerprint(first) == canonical_constraint_fingerprint(second)


def test_cache_fingerprint_rejects_incomplete_constraints():
    incomplete = {"topology": "buck", "output_voltage_v": 5}

    assert canonical_constraint_fingerprint(incomplete) is None


def test_exact_cache_round_trip_does_not_cross_constraint_fingerprints():
    constraints = {
        "category": "dc_dc_converter",
        "topology": "buck",
        "input_voltage_nominal_v": 12,
        "output_voltage_v": 5,
        "output_current_a": 2,
    }
    different_constraints = {**constraints, "output_voltage_v": 3.3}
    report = {
        "constraints": constraints,
        "candidates": [{"part": {"part_number": "TEST-5V-2A"}}],
        "recommended_parts": [],
        "risks": {"overall_risk_level": "low", "risk_items": []},
        "evidence": [{"part_number": "TEST-5V-2A", "claim": "output verified"}],
    }

    with tempfile.TemporaryDirectory() as directory:
        cache = SemanticCache(persist_dir=directory)
        fingerprint = canonical_constraint_fingerprint(constraints)

        assert cache.set_exact(fingerprint, report)
        assert cache.get_exact(fingerprint)["cached_result"] == report
        assert cache.get_exact(canonical_constraint_fingerprint(different_constraints)) is None


# ──────────────────────────────────────────────────────────────────────────────
# Gate 硬门禁（app/scoring.py::_gate_evaluate）
#
# 硬门禁是选型结果里最不能被高总分抵消的一环：Gate FAIL 的器件一律降到
# not_recommended。这里逐个规则钉死边界值——尤其是「刚好不达标」的那一侧，
# 免得有人把比较方向改反之后没有任何用例变红。
# ──────────────────────────────────────────────────────────────────────────────

def _constraints(**overrides) -> RequirementConstraints:
    base = {
        "raw_input": "12V 转 5V / 3A 降压",
        "input_voltage_nominal_v": 12,
        "output_voltage_v": 5,
        "output_current_a": 3,
    }
    base.update(overrides)
    return RequirementConstraints(**base)


def _part(**overrides) -> PartIR:
    base = {
        "part_number": "TEST-PART-001",
        "manufacturer": "TestCorp",
        "input_voltage_min_v": 6,
        "input_voltage_max_v": 18,
        "output_voltage_v": 5,
        "output_current_max_a": 3,
    }
    base.update(overrides)
    return PartIR(**base)


def test_gate_passes_when_part_meets_all_hard_constraints():
    result = _gate_evaluate(_part(), _constraints())

    assert result.status == "PASS"
    assert result.fail_reasons == []
    assert result.gate_factor == 1.0


def test_gate_fails_when_output_current_insufficient():
    """G1：输出能力只有需求的 83%（2.5A vs 3A 的 90% 门槛 = 2.7A）→ 硬失败。"""
    part = _part(output_current_max_a=2.5)
    result = _gate_evaluate(part, _constraints(output_current_a=3))

    assert result.status == "FAIL"
    assert result.gate_factor == 0.0
    assert any(r.startswith("[G1]") for r in result.fail_reasons), result.fail_reasons


def test_gate_does_not_fail_when_output_current_just_meets_the_90pct_floor():
    """G1 的另一侧边界：刚好等于门槛（3A 需求的 90% = 2.7A）不能判失败。"""
    part = _part(output_current_max_a=2.7)
    result = _gate_evaluate(part, _constraints(output_current_a=3))

    assert result.status == "PASS", result.fail_reasons
    assert result.fail_reasons == []


def test_gate_fails_when_nominal_input_voltage_out_of_range():
    """G1：标称输入电压落在器件范围之外 → 硬失败。"""
    result = _gate_evaluate(
        _part(input_voltage_min_v=6, input_voltage_max_v=18),
        _constraints(input_voltage_nominal_v=24),
    )

    assert result.status == "FAIL"
    assert any(r.startswith("[G1]") for r in result.fail_reasons), result.fail_reasons


def test_gate_accepts_nominal_input_voltage_on_the_boundary():
    """G1 边界：标称值恰好等于范围端点时应当通过。"""
    for vin in (6, 18):
        result = _gate_evaluate(
            _part(input_voltage_min_v=6, input_voltage_max_v=18),
            _constraints(input_voltage_nominal_v=vin),
        )
        assert result.status == "PASS", (vin, result.fail_reasons)


def test_gate_fails_when_temperature_range_too_narrow():
    """G2：器件工作温度覆盖不了需求温度 → 硬失败。"""
    result = _gate_evaluate(
        _part(temperature_min_c=-20, temperature_max_c=85),
        _constraints(temperature_min_c=-40, temperature_max_c=85),
    )

    assert result.status == "FAIL"
    assert any(r.startswith("[G2]") for r in result.fail_reasons), result.fail_reasons


def test_gate_passes_when_temperature_range_covers_requirement():
    result = _gate_evaluate(
        _part(temperature_min_c=-40, temperature_max_c=125),
        _constraints(temperature_min_c=-40, temperature_max_c=85),
    )

    assert result.status == "PASS", result.fail_reasons


def test_gate_fails_for_obsolete_part():
    """G3：停产器件禁止新设计导入 → 硬失败。"""
    result = _gate_evaluate(_part(lifecycle_status="Obsolete"), _constraints())

    assert result.status == "FAIL"
    assert any(r.startswith("[G3]") for r in result.fail_reasons), result.fail_reasons


def test_gate_makes_eol_and_nrnd_conditional():
    """G3：EOL / NRND 是「条件通过」，不是放行，也不是硬失败。"""
    for status in ("EOL", "NRND"):
        result = _gate_evaluate(_part(lifecycle_status=status), _constraints())

        assert result.status == "CONDITIONAL", status
        assert result.gate_factor == 0.85, status
        assert result.fail_reasons == [], status
        assert any(r.startswith("[G3]") for r in result.conditional_reasons), status


def test_gate_fails_when_automotive_required_but_part_is_not():
    """G4：项目要求车规但器件没有 AEC-Q → 硬失败。"""
    result = _gate_evaluate(
        _part(automotive_grade=False), _constraints(grade="automotive")
    )

    assert result.status == "FAIL"
    assert any(r.startswith("[G4]") for r in result.fail_reasons), result.fail_reasons


def test_gate_passes_automotive_part_for_automotive_project():
    result = _gate_evaluate(
        _part(automotive_grade=True), _constraints(grade="automotive")
    )

    assert result.status == "PASS", result.fail_reasons


def test_gate_fails_when_mpn_missing():
    """G5：没有 MPN 就没有工程判断的依据 → 硬失败。"""
    result = _gate_evaluate(_part(part_number=""), _constraints())

    assert result.status == "FAIL"
    assert any(r.startswith("[G5]") for r in result.fail_reasons), result.fail_reasons


def test_gate_is_conditional_when_manufacturer_missing():
    """G5：制造商缺失只降级为「条件通过」，不是硬失败。"""
    result = _gate_evaluate(_part(manufacturer=None), _constraints())

    assert result.status == "CONDITIONAL"
    assert result.gate_factor == 0.85
    assert result.fail_reasons == []
    assert any(r.startswith("[G5]") for r in result.conditional_reasons)


def test_gate_fail_beats_conditional():
    """同时命中硬失败与条件项时，必须判 FAIL（硬门槛优先）。"""
    result = _gate_evaluate(
        _part(manufacturer=None, lifecycle_status="obsolete"), _constraints()
    )

    assert result.status == "FAIL"
    assert result.gate_factor == 0.0
    assert result.fail_reasons


def test_gate_ignores_constraints_that_are_not_specified():
    """需求没提的维度不该凭空产生门禁结论。"""
    result = _gate_evaluate(
        _part(),
        RequirementConstraints(raw_input="随便看看"),
    )

    assert result.status == "PASS"
    assert result.fail_reasons == []
    assert result.conditional_reasons == []
