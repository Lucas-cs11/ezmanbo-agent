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
    except Exception:
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
        # EZ-PLM API only supports keyword search (by MPN/name), not spec-based filtering.
        topology = getattr(constraints, "topology", None) or ""
        category = getattr(constraints, "category", None) or ""
        if topology == "buck":
            keyword = "DC-DC Buck"
        elif topology == "boost":
            keyword = "DC-DC Boost"
        elif category == "dc_dc_converter":
            keyword = "DC-DC"
        else:
            keyword = topology or category or "DC-DC"
        params: Dict[str, Any] = {"keyword": keyword, "pageSize": 50}
        status, body = _request_json(ez_base, ez_key, "/api/v1/api-key/parts", params)
        api_items = []
        if status == 200:
            api_items = body.get("data") or []
        if api_items:
            for p in api_items:
                mapped = _map_api_part_to_partir(p)
                if mapped and _part_matches_constraints(mapped, constraints):
                    results.append(mapped)
            return results
        # API returned empty (whitelist restriction) — fall through to mock data

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

        return PartIR.parse_obj({
            "part_number": part_number,
            "manufacturer": manufacturer,
            "category": category,
            "topology": api_obj.get("topology"),
            "is_domestic": is_domestic,
            "description": api_obj.get("description") or api_obj.get("summary"),
            "input_voltage_min_v": attrs.get("input_voltage_min_v"),
            "input_voltage_max_v": attrs.get("input_voltage_max_v"),
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
    # output current
    if constraints.output_current_a is not None and (part.output_current_max_a is None or part.output_current_max_a < constraints.output_current_a):
        return False
    # temperature
    if constraints.temperature_min_c is not None and constraints.temperature_max_c is not None:
        if part.temperature_min_c is None or part.temperature_max_c is None:
            return False
        if not (part.temperature_min_c <= constraints.temperature_min_c and part.temperature_max_c >= constraints.temperature_max_c):
            return False
    # automotive
    if constraints.grade == "automotive" and not part.automotive_grade:
        return False
    return True


