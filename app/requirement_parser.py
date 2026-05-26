import re
import os
from .schemas import RequirementConstraints

VOLTAGE_PAT = re.compile(r"(\d+(?:\.\d+)?)\s*[Vv]")
CURRENT_PAT = re.compile(r"(\d+(?:\.\d+)?)\s*[Aa]")
TEMP_PAT = re.compile(r"(-?\d+)[°º]?C")

try:
    from .llm_client import parse_requirement_with_llm
except Exception:
    parse_requirement_with_llm = None


def parse_requirement(text: str) -> RequirementConstraints:
    rc = RequirementConstraints(raw_input=text)
    lower = text.lower()

    # Try LLM first if OPENAI_API_KEY set and llm_client available
    if os.getenv("OPENAI_API_KEY") and parse_requirement_with_llm is not None:
        try:
            llm_res = parse_requirement_with_llm(text)
            # apply fields from llm_res if present
            for k, v in llm_res.items():
                if hasattr(rc, k) and v is not None:
                    try:
                        setattr(rc, k, v)
                    except Exception:
                        pass
        except Exception:
            # fallback to rule-based if LLM fails
            pass

    # rule-based extraction (complements LLM or acts as fallback)
    # category / topology
    if "buck" in lower or "降压" in lower:
        rc.category = rc.category or "dc_dc_converter"
        rc.topology = rc.topology or "buck"
    # detect patterns like '12V转5V' without the word 降压
    if ("转" in text and re.search(r"\d+\s*[Vv]", text)) or re.search(r"\d+V\s*to\s*\d+V", text.lower()):
        rc.category = rc.category or "dc_dc_converter"
        rc.topology = rc.topology or "buck"

    # voltages: look for patterns like '12V 转 5V' or '12V to 5V'
    m = re.search(r"(\d+(?:\.\d+)?)\s*[Vv].{0,8}?[转to]+.{0,8}?(\d+(?:\.\d+)?)\s*[Vv]", text)
    if m:
        try:
            rc.input_voltage_nominal_v = rc.input_voltage_nominal_v or float(m.group(1))
            rc.output_voltage_v = rc.output_voltage_v or float(m.group(2))
        except Exception:
            pass
    else:
        vs = VOLTAGE_PAT.findall(text)
        if vs:
            try:
                if len(vs) >= 2:
                    rc.input_voltage_nominal_v = rc.input_voltage_nominal_v or float(vs[0])
                    rc.output_voltage_v = rc.output_voltage_v or float(vs[1])
                elif len(vs) == 1:
                    rc.output_voltage_v = rc.output_voltage_v or float(vs[0])
            except Exception:
                pass

    # current
    c = CURRENT_PAT.findall(text)
    if c and rc.output_current_a is None:
        try:
            m2 = re.search(r"(\d+(?:\.\d+)?)\s*[Aa]", text)
            if m2:
                rc.output_current_a = float(m2.group(1))
        except Exception:
            pass

    # temperature range
    temps = TEMP_PAT.findall(text)
    if temps:
        nums = [int(t) for t in temps]
        if len(nums) >= 2:
            rc.temperature_min_c = rc.temperature_min_c or min(nums)
            rc.temperature_max_c = rc.temperature_max_c or max(nums)
        elif len(nums) == 1 and rc.temperature_min_c is None:
            rc.temperature_min_c = nums[0]

    # grade
    if "车规" in lower or "automotive" in lower:
        rc.grade = rc.grade or "automotive"

    # preferences
    if ("国产" in lower or "国产替代" in lower or "优先国产" in lower) and "domestic_alternative" not in rc.preferences:
        rc.preferences.append("domestic_alternative")
    if ("低供应" in lower or "低供应链风险" in lower) and "low_supply_risk" not in rc.preferences:
        rc.preferences.append("low_supply_risk")

    return rc
