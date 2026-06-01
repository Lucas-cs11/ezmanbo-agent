import json
import os
import time
import uuid
import hmac
import hashlib
import base64
import urllib.parse
import urllib.request
from pathlib import Path
from typing import List, Dict, Any
from .schemas import PartIR, RequirementConstraints

DATA_FILE = Path(__file__).parents[1] / "data" / "mock_parts.json"


def _load_parts() -> List[dict]:
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        from .log_util import warn_swallow; warn_swallow("ezplm_client", e, "load_parts")
        return []


def _canonical_query(params: Dict[str, Any]) -> str:
    items: List[tuple] = []
    for k, v in params.items():
        if v is None or v == "":
            continue
        items.append((str(k), str(v)))
    items.sort(key=lambda it: (it[0], it[1]))
    return "&".join(f"{urllib.parse.quote(k, safe='')}={urllib.parse.quote(v, safe='')}" for k, v in items)


def _build_signature(api_key: str, method: str, path: str, params: Dict[str, Any], timestamp: str, nonce: str) -> str:
    canonical = "\n".join([method.upper(), path, _canonical_query(params), timestamp, nonce])
    digest = hmac.new(api_key.encode("utf-8"), canonical.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def _request_json(base_url: str, api_key: str, path: str, params: Dict[str, Any]) -> tuple[int, Dict[str, Any]]:
    timestamp = str(int(time.time()))
    nonce = str(uuid.uuid4())
    signature = _build_signature(api_key, "GET", path, params, timestamp, nonce)
    query = _canonical_query(params)
    url = base_url.rstrip("/") + path
    if query:
        url = f"{url}?{query}"
    req = urllib.request.Request(url, method="GET", headers={
        "X-API-Key": api_key,
        "X-Timestamp": timestamp,
        "X-Nonce": nonce,
        "X-Signature": signature,
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"raw": body}
        return exc.code, parsed
    except Exception as e:
        return 0, {"error": str(e)}


def search_parts(constraints: RequirementConstraints) -> List[PartIR]:
    """
    优先使用真实 EZ-PLM API（若环境变量提供 EZPLM_API_KEY 和 EZPLM_BASE_URL），否则回退到本地 mock 数据。
    """
    ez_key = os.getenv("EZPLM_API_KEY", "").strip()
    ez_base = os.getenv("EZPLM_BASE_URL", "https://www.ezplm.cn").strip()
    results: List[PartIR] = []

    if ez_key:
        # EZ-PLM API only supports MPN-prefix search; category/topology keywords return 0.
        # Use manufacturer-prefix keywords grouped by category/topology.
        category = getattr(constraints, "category", None) or ""
        topology = getattr(constraints, "topology", None)

        cat_map = _API_KEYWORDS.get(category) or _API_KEYWORDS.get("dc_dc_converter", {})
        keywords: list = cat_map.get(topology) or cat_map.get(None) or []

        seen_pns: set = set()
        api_results: list = []

        for kw in keywords:
            if len(api_results) >= _API_MAX_TOTAL:
                break
            status, body = _request_json(
                ez_base, ez_key, "/api/v1/api-key/parts",
                {"keyword": kw, "pageSize": str(_API_MAX_PER_KEYWORD)},
            )
            if status != 200:
                continue
            for raw in (body.get("data") or []):
                mapped = _map_api_part_to_partir(raw)
                if not mapped or mapped.part_number in seen_pns:
                    continue
                seen_pns.add(mapped.part_number)
                if _part_matches_constraints(mapped, constraints):
                    api_results.append(mapped)

        if api_results:
            return api_results
        # No API results for any prefix → fall through to mock data

    # local mock filtering (also used as fallback when API is empty)
    parts = _load_parts()
    for p in parts:
        try:
            part = PartIR.parse_obj(p)
        except Exception:
            continue
        if _part_matches_constraints(part, constraints):
            results.append(part)
    return results


def fetch_reference_designs(part_id: str) -> List[Dict[str, Any]]:
    """调用 /api/v1/api-key/reference-designs 获取该器件的参考设计列表。"""
    ez_key = os.getenv("EZPLM_API_KEY", "").strip()
    ez_base = os.getenv("EZPLM_BASE_URL", "https://www.ezplm.cn").strip()
    if not ez_key or not part_id:
        return []
    status, body = _request_json(
        ez_base, ez_key,
        "/api/v1/api-key/reference-designs",
        {"partlibId": part_id, "pageSize": "5"},
    )
    if status == 200:
        return body.get("data") or []
    return []


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


_EZPLM_CATEGORY_MAP = {
    "DC-DC": "dc_dc_converter",
    "电源管理": "dc_dc_converter",
    "PMIC": "dc_dc_converter",
    "降压": "dc_dc_converter",
    "升压": "dc_dc_converter",
    "buck": "dc_dc_converter",
    "boost": "dc_dc_converter",
}

_DOMESTIC_MANUFACTURERS = {
    "立锜", "圣邦", "南芯", "华润", "矽力杰", "思瑞浦", "芯朋", "英集芯",
    "纳芯微", "杰华特", "芯源系统", "美芯晟", "晶丰明源", "上海贝岭",
}

# EZ-PLM API 仅支持型号前缀搜索，按 category/topology 分组
# 覆盖已开放的 TI / ADI(含 LTC) / Microchip / ST 四大厂
_API_KEYWORDS: Dict[str, Dict] = {
    "dc_dc_converter": {
        "buck":  ["TPS54", "TPS62", "LM2596", "LM2576", "ADP23", "LTC388", "LTC365", "ST1S", "L5970"],
        "boost": ["TPS61", "TPS63", "LTC370", "LTC358", "MCP1640"],
        None:    ["TPS54", "TPS62", "TPS61", "LM2596", "ADP23", "LTC388"],
    },
    "ldo": {
        None:    ["TPS79", "TPS72", "MCP1703", "MCP1700", "ADP312", "LT1763", "MCP1501"],
    },
}
_API_MAX_PER_KEYWORD = 50   # 每个 keyword 最多取 N 条
_API_MAX_TOTAL = 200        # 总条数上限，避免过多请求


# ── 型号输出固定电压解析（如 LM2596S-5.0 → 5.0V）────────────
import re as _re_mpn

_MPN_VOUT_PAT = _re_mpn.compile(
    r"(?:^|[-\s])(\d+[.]?\d*)\s*[Vv]?(?:$|[-\s/])"
)


def _infer_output_voltage_from_mpn(part_number: str) -> "float | None":
    """从型号中推断固定输出电压（如 LM2596S-5.0 → 5.0V）。
    仅当型号含有明确电压数字时提取，ADJ 后缀的不提取。
    """
    if not part_number:
        return None
    if "ADJ" in part_number.upper():
        return None
    # 查找 -X.X 或 -XXV 模式（如 -5.0, -12, -3.3, -1.8V）
    m = _re_mpn.search(_MPN_VOUT_PAT, part_number)
    if not m:
        return None
    try:
        v = float(m.group(1))
        if 0.5 <= v <= 60:  # 合理的输出电压范围
            return v
    except ValueError:
        pass
    return None


def _parse_attrs(attrs: list) -> Dict[str, Any]:
    """从 EZ-PLM attributes 数组中提取电气参数。"""
    result: Dict[str, Any] = {}
    for a in (attrs or []):
        name = str(a.get("name", ""))
        val = str(a.get("value", "")).strip()
        if not val or val == "None":
            continue
        try:
            if "输入电压" in name and "最大" in name:
                result["input_voltage_max_v"] = float(val)
            elif "输入电压" in name and "最小" in name:
                result["input_voltage_min_v"] = float(val)
            elif "输出电压" in name and ("标称" in name or "nominal" in name.lower()):
                result["output_voltage_v"] = float(val)
            elif "输出电压" in name:
                result["output_voltage_v"] = float(val)
            elif "输出电流" in name and "最大" in name:
                result["output_current_max_a"] = float(val)
            elif "温度" in name and ("范围" in name or "工作" in name):
                import re as _re
                m = _re.search(r"(-?\d+(?:\.\d+)?)\s*(?:to|~|至|～)\s*(-?\d+(?:\.\d+)?)", val)
                if m:
                    result["temperature_min_c"] = float(m.group(1))
                    result["temperature_max_c"] = float(m.group(2))
            elif "封装" in name or "package" in name.lower():
                result["package"] = val
            elif "拓扑" in name:
                _topo_map = {
                    "buck": "buck", "boost": "boost", "ldo": "ldo",
                    "buck/boost": "buck_boost", "降压": "buck", "升压": "boost",
                }
                topo_raw = val.lower().strip()
                result["topology"] = next(
                    (v for k, v in _topo_map.items() if k in topo_raw), topo_raw
                )
        except (ValueError, TypeError):
            pass
    return result


def _map_api_part_to_partir(api_obj: Dict[str, Any]) -> "PartIR | None":
    """把 EZ-PLM API 真实返回格式映射到 PartIR。

    实际字段：mpn, manufacturer{name}, category{name}, attributes[], pdf{url}, id
    """
    if not isinstance(api_obj, dict):
        return None
    try:
        part_number = (
            api_obj.get("mpn") or api_obj.get("partNumber")
            or api_obj.get("pn") or api_obj.get("part_number")
            or api_obj.get("id")
        )
        if not part_number:
            return None

        # manufacturer: may be nested {"name": "..."}
        mfr_raw = api_obj.get("manufacturer") or {}
        if isinstance(mfr_raw, dict):
            manufacturer = mfr_raw.get("name") or mfr_raw.get("id")
        else:
            manufacturer = str(mfr_raw)

        # category: may be nested {"name": "..."}
        cat_raw = api_obj.get("category") or {}
        cat_name = cat_raw.get("name", "") if isinstance(cat_raw, dict) else str(cat_raw)
        category = next(
            (v for k, v in _EZPLM_CATEGORY_MAP.items() if k in cat_name), None
        )

        # is_domestic: check manufacturer name against known domestic list
        is_domestic = False
        if manufacturer:
            is_domestic = any(d in manufacturer for d in _DOMESTIC_MANUFACTURERS)

        # pdf url as datasheet
        pdf_raw = api_obj.get("pdf") or {}
        datasheet_url = (
            pdf_raw.get("url") if isinstance(pdf_raw, dict)
            else api_obj.get("datasheetUrl") or api_obj.get("datasheet_url")
        )

        # parse attributes array for electrical specs
        attrs = _parse_attrs(api_obj.get("attributes") or [])

        # MPN 推断优先于 API attrs：固定电压器件的型号电压比 API 属性更可靠
        # （API attrs 可能返回"最大输出电压"等范围值，不可用于固定输出判定）
        output_voltage_v = _infer_output_voltage_from_mpn(part_number)
        if output_voltage_v is None:
            output_voltage_v = attrs.get("output_voltage_v")

        return PartIR.parse_obj({
            "part_number": part_number,
            "manufacturer": manufacturer,
            "category": category,
            "topology": attrs.get("topology") or api_obj.get("topology"),
            "is_domestic": is_domestic,
            "description": api_obj.get("description") or api_obj.get("summary"),
            "input_voltage_min_v": attrs.get("input_voltage_min_v"),
            "input_voltage_max_v": attrs.get("input_voltage_max_v"),
            "output_voltage_v": output_voltage_v,
            "output_current_max_a": attrs.get("output_current_max_a"),
            "temperature_min_c": attrs.get("temperature_min_c"),
            "temperature_max_c": attrs.get("temperature_max_c"),
            "package": attrs.get("package") or api_obj.get("package"),
            "automotive_grade": False,
            "lifecycle_status": api_obj.get("lifecycleStatus") or api_obj.get("lifecycle_status"),
            "stock": api_obj.get("stock") or api_obj.get("inventory"),
            "unit_price_cny": api_obj.get("unitPriceCny") or api_obj.get("unit_price"),
            "datasheet_url": datasheet_url,
            "ezplm_part_id": api_obj.get("id"),
            "replacement_for": api_obj.get("replacementFor") or api_obj.get("replacement_for") or [],
            "source": "ezplm",
        })
    except Exception:
        return None


def _part_matches_constraints(part: PartIR, constraints: RequirementConstraints) -> bool:
    # category/topology — skip filter if part field is None (API may not return these)
    if constraints.category and part.category and part.category != constraints.category:
        return False
    if constraints.topology and part.topology and part.topology != constraints.topology:
        return False
    # input voltage nominal
    if constraints.input_voltage_nominal_v is not None and part.input_voltage_min_v is not None and part.input_voltage_max_v is not None:
        if not (part.input_voltage_min_v <= constraints.input_voltage_nominal_v <= part.input_voltage_max_v):
            return False
    # ── 输出固定电压匹配（P0修复：过滤固定电压不匹配的器件）────
    part_vout = part.output_voltage_v
    if part_vout is None:
        # 尝试从型号推断
        part_vout = _infer_output_voltage_from_mpn(part.part_number)
        if part_vout is not None:
            part.output_voltage_v = part_vout  # 回填
    if (constraints.output_voltage_v is not None
            and part_vout is not None
            and part.topology in ("buck", None)):
        # 对于固定输出器件，允许 ±5% 容差匹配
        if not (0.95 * constraints.output_voltage_v <= part_vout <= 1.05 * constraints.output_voltage_v):
            return False
    # output current
    if constraints.output_current_a is not None and (part.output_current_max_a is None or part.output_current_max_a < constraints.output_current_a):
        return False
    # temperature
    if constraints.temperature_min_c is not None and constraints.temperature_max_c is not None:
        if part.temperature_min_c is None or part.temperature_max_c is None:
            return False
        if not (part.temperature_min_c <= constraints.temperature_min_c and part.temperature_max_c >= constraints.temperature_max_c):
            return False
    # automotive — 不执行硬过滤（mock/API 数据普遍无车规认证字段），
    # 车规需求仅在风险报告中标注"未确认车规认证"作为提示
    return True


