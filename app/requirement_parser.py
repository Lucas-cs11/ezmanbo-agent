import re
import os
from .schemas import RequirementConstraints

VOLTAGE_PAT    = re.compile(r"(\d+(?:\.\d+)?)\s*[Vv]")
CURRENT_PAT    = re.compile(r"(\d+(?:\.\d+)?)\s*[Aa]")
CURRENT_MA_PAT = re.compile(r"(\d+(?:\.\d+)?)\s*m[Aa]")   # 毫安，需转换 ÷1000
TEMP_PAT       = re.compile(r"(-?\d+)[°º]?C")

try:
    from .llm_client import parse_requirement_with_llm
except Exception:
    parse_requirement_with_llm = None

# ── LLM 输出归一化映射 ────────────────────────────────────────────
_CAT_NORM: dict = {
    "dc_dc_converter": "dc_dc_converter",
    "dc-dc": "dc_dc_converter", "dc_dc": "dc_dc_converter",
    "电源转换": "dc_dc_converter", "电源管理": "dc_dc_converter",
    "降压": "dc_dc_converter", "升压": "dc_dc_converter",
    "buck": "dc_dc_converter", "boost": "dc_dc_converter",
    "pmic": "dc_dc_converter",
    "ldo": "ldo", "线性稳压": "ldo", "低压差": "ldo",
    "linear": "ldo",
}
_TOPO_NORM: dict = {
    "降压": "buck",  "buck": "buck",  "buck converter": "buck",
    "升压": "boost", "boost": "boost", "boost converter": "boost",
    "buck/boost": "buck_boost",
    "ldo": "ldo", "线性": "ldo", "linear regulator": "ldo",
}

# ── 已知封装名（用于 package_preference 提取）────────────────────
_KNOWN_PACKAGES = [
    "SOT-23-5", "SOT-23-6", "SOT-23", "SOT23",
    "QFN", "DFN", "WSON",
    "SOP-8", "SOP8", "SOP",
    "SOIC", "TSSOP", "HSOP",
    "TO-263", "TO-252",
    "LGA", "BGA",
]


def _norm_cat(v: str) -> "str | None":
    if not v:
        return None
    vl = str(v).lower().strip()
    for k, mapped in _CAT_NORM.items():
        if k in vl:
            return mapped
    return None


def _norm_topo(v: str) -> "str | None":
    if not v:
        return None
    vl = str(v).lower().strip()
    return _TOPO_NORM.get(vl) or next(
        (mapped for k, mapped in _TOPO_NORM.items() if k in vl), None
    )


def _extract_package(text: str) -> "str | None":
    """从文本中提取封装名称。"""
    upper = text.upper()
    for pkg in _KNOWN_PACKAGES:
        if pkg.upper() in upper:
            return pkg
    # 支持"XXX封装"中文句式，如"QFN封装"
    m = re.search(r"([A-Za-z0-9\-]{2,10})\s*封装", text)
    if m:
        return m.group(1).upper()
    return None


def parse_requirement(text: str) -> RequirementConstraints:
    rc = RequirementConstraints(raw_input=text)
    lower = text.lower()

    # ── LLM 优先解析（若 API Key 存在）──────────────────────────
    if os.getenv("OPENAI_API_KEY") and parse_requirement_with_llm is not None:
        try:
            llm_res = parse_requirement_with_llm(text)
            if "category" in llm_res:
                llm_res["category"] = _norm_cat(llm_res["category"])
            if "topology" in llm_res:
                llm_res["topology"] = _norm_topo(llm_res["topology"])
            for k, v in llm_res.items():
                if hasattr(rc, k) and v is not None:
                    try:
                        setattr(rc, k, v)
                    except Exception:
                        pass
        except Exception:
            pass

    # ── 规则化 category / topology（规则优先，覆盖 LLM）─────────
    if "buck" in lower or "降压" in lower:
        rc.category = "dc_dc_converter"
        rc.topology = "buck"
    elif "boost" in lower or "升压" in lower:
        rc.category = "dc_dc_converter"
        rc.topology = "boost"
    elif "ldo" in lower or "低压差" in lower or "线性稳压" in lower:
        rc.category = "ldo"
        rc.topology = rc.topology or "ldo"
    elif ("转" in text and re.search(r"\d+\s*[Vv]", text)) or re.search(r"\d+V\s*to\s*\d+V", lower):
        rc.category = "dc_dc_converter"
        rc.topology = rc.topology or "buck"
    elif re.search(r"输入.{0,6}\d+\s*[Vv]", text) and re.search(r"输出.{0,6}\d+\s*[Vv]", text):
        rc.category = "dc_dc_converter"
        rc.topology = rc.topology or "buck"

    # ── 电压提取 ──────────────────────────────────────────────────
    # 优先匹配"输入 NV / 输出 NV"句式
    m_io = re.search(r"输入\D{0,6}?(\d+(?:\.\d+)?)\s*[Vv]", text)
    m_oo = re.search(r"输出\D{0,6}?(\d+(?:\.\d+)?)\s*[Vv]", text)
    if m_io:
        try:
            rc.input_voltage_nominal_v = rc.input_voltage_nominal_v or float(m_io.group(1))
        except Exception:
            pass
    if m_oo:
        try:
            rc.output_voltage_v = rc.output_voltage_v or float(m_oo.group(1))
        except Exception:
            pass

    # 其次匹配"NV 转/to NV"句式
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

    # ── 电流提取（优先 mA，再匹配 A）────────────────────────────
    if rc.output_current_a is None:
        try:
            m_ma = CURRENT_MA_PAT.search(text)
            if m_ma:
                rc.output_current_a = float(m_ma.group(1)) / 1000.0
            else:
                m2 = CURRENT_PAT.search(text)
                if m2:
                    rc.output_current_a = float(m2.group(1))
        except Exception:
            pass

    # ── 温度范围提取 ──────────────────────────────────────────────
    temps = TEMP_PAT.findall(text)
    if temps:
        nums = [int(t) for t in temps]
        if len(nums) >= 2:
            rc.temperature_min_c = rc.temperature_min_c or min(nums)
            rc.temperature_max_c = rc.temperature_max_c or max(nums)
        elif len(nums) == 1 and rc.temperature_min_c is None:
            rc.temperature_min_c = nums[0]

    # ── 等级 ──────────────────────────────────────────────────────
    if "车规" in lower or "automotive" in lower:
        rc.grade = rc.grade or "automotive"

    # ── 封装偏好 ──────────────────────────────────────────────────
    if not rc.package_preference:
        rc.package_preference = _extract_package(text)

    # ── preferences ───────────────────────────────────────────────
    if ("国产" in lower or "国产替代" in lower or "优先国产" in lower) and "domestic_alternative" not in rc.preferences:
        rc.preferences.append("domestic_alternative")
    if ("低供应" in lower or "低供应链风险" in lower) and "low_supply_risk" not in rc.preferences:
        rc.preferences.append("low_supply_risk")

    # ── must_have ─────────────────────────────────────────────────
    _MUST_TRIGGERS = ["必须", "强制", "一定要", "不可缺少"]
    is_must = any(t in text for t in _MUST_TRIGGERS)
    if is_must:
        if ("车规" in lower or "automotive" in lower) and "automotive_grade" not in rc.must_have:
            rc.must_have.append("automotive_grade")
        if ("国产" in lower) and "domestic" not in rc.must_have:
            rc.must_have.append("domestic")
        if rc.package_preference and "package" not in rc.must_have:
            rc.must_have.append(f"package:{rc.package_preference}")

    # ── nice_to_have ──────────────────────────────────────────────
    _NICE_TRIGGERS = ["最好", "如果可以", "尽量", "可选", "nice to have"]
    is_nice = any(t in lower for t in _NICE_TRIGGERS)
    if is_nice:
        if ("国产" in lower) and "domestic" not in rc.nice_to_have:
            rc.nice_to_have.append("domestic")
        if rc.package_preference and f"package:{rc.package_preference}" not in rc.nice_to_have:
            rc.nice_to_have.append(f"package:{rc.package_preference}")

    return rc
