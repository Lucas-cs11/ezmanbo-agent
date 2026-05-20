import json
from pathlib import Path
from typing import List
from .schemas import PartIR, RequirementConstraints

DATA_FILE = Path(__file__).parents[1] / "data" / "mock_parts.json"


def _load_parts() -> List[dict]:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def search_parts(constraints: RequirementConstraints) -> List[PartIR]:
    parts = _load_parts()
    results: List[PartIR] = []

    for p in parts:
        # basic category/topology filter
        if constraints.category and p.get("category") != constraints.category:
            continue
        if constraints.topology and p.get("topology") != constraints.topology:
            continue

        # input voltage must cover nominal if given
        if constraints.input_voltage_nominal_v is not None:
            vin = constraints.input_voltage_nominal_v
            if p.get("input_voltage_min_v") is not None and p.get("input_voltage_max_v") is not None:
                if not (p["input_voltage_min_v"] <= vin <= p["input_voltage_max_v"]):
                    continue
        # output current requirement
        if constraints.output_current_a is not None:
            req_i = constraints.output_current_a
            if p.get("output_current_max_a") is None or p.get("output_current_max_a") < req_i:
                continue
        # temperature
        if constraints.temperature_min_c is not None and constraints.temperature_max_c is not None:
            if p.get("temperature_min_c") is None or p.get("temperature_max_c") is None:
                continue
            if not (p["temperature_min_c"] <= constraints.temperature_min_c and p["temperature_max_c"] >= constraints.temperature_max_c):
                continue
        # automotive grade
        if constraints.grade == "automotive":
            if not p.get("automotive_grade", False):
                continue

        # passed hard filters
        try:
            results.append(PartIR.parse_obj(p))
        except Exception:
            # skip unparsable
            continue

    return results


def find_replacements(part_number: str) -> List[PartIR]:
    parts = _load_parts()
    replacements = []
    # strategy: find parts that list the original in their replacement_for OR share category/topology and are domestic
    for p in parts:
        if part_number in p.get("replacement_for", []):
            try:
                replacements.append(PartIR.parse_obj(p))
            except Exception:
                pass
    # fallback: same category and topology, prefer domestic
    if not replacements:
        orig = None
        for p in parts:
            if p.get("part_number") == part_number:
                orig = p
                break
        if orig:
            for p in parts:
                if p.get("category") == orig.get("category") and p.get("topology") == orig.get("topology") and p.get("part_number") != part_number:
                    try:
                        replacements.append(PartIR.parse_obj(p))
                    except Exception:
                        pass
    return replacements

