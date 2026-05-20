import re
import uuid
from .schemas import RequirementConstraints

VOLTAGE_PAT = re.compile(r"(\d+(?:\.\d+)?)\s*[Vv]")
CURRENT_PAT = re.compile(r"(\d+(?:\.\d+)?)\s*[Aa]")
TEMP_PAT = re.compile(r"(-?\d+)[°º]?C")


def parse_requirement(text: str) -> RequirementConstraints:
    rc = RequirementConstraints(raw_input=text)
    lower = text.lower()

    # category / topology
    if "buck" in lower or "降压" in lower:
        rc.category = "dc_dc_converter"
        rc.topology = "buck"

    # voltages: look for patterns like '12V 转 5V' or '12V to 5V'
    m = re.search(r"(\d+(?:\.\d+)?)\s*[Vv].{0,8}?[转to]+.{0,8}?(\d+(?:\.\d+)?)\s*[Vv]", text)
    if m:
        try:
            rc.input_voltage_nominal_v = float(m.group(1))
            rc.output_voltage_v = float(m.group(2))
        except Exception:
            pass
    else:
        vs = VOLTAGE_PAT.findall(text)
        if vs:
            if len(vs) >= 2:
                rc.input_voltage_nominal_v = float(vs[0])
                rc.output_voltage_v = float(vs[1])
            elif len(vs) == 1:
                # assume this is output voltage
                rc.output_voltage_v = float(vs[0])

    # current
    c = CURRENT_PAT.findall(text)
    if c:
        # take first numeric as current if context contains A and number near '3A'
        # prefer current values after '转 X' pattern - simple heuristic
        try:
            # find numbers followed by A that are likely output current
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
            rc.temperature_min_c = min(nums)
            rc.temperature_max_c = max(nums)
        elif len(nums) == 1:
            rc.temperature_min_c = nums[0]

    # grade
    if "车规" in lower or "automotive" in lower:
        rc.grade = "automotive"

    # preferences
    if "国产" in lower or "国产替代" in lower or "优先国产" in lower:
        rc.preferences.append("domestic_alternative")
    if "低供应" in lower or "低供应链风险" in lower:
        rc.preferences.append("low_supply_risk")

    # request id placeholder if needed
    return rc

