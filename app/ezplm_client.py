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
        # Use remote API search endpoint; use raw_input as keyword if specific fields not available
        keyword = constraints.raw_input if getattr(constraints, "raw_input", None) else None
        params: Dict[str, Any] = {}
        if keyword:
            params["keyword"] = keyword
        if getattr(constraints, "output_current_a", None):
            params["minOutputCurrentA"] = constraints.output_current_a
        # pageSize default
        params.setdefault("pageSize", 50)
        status, body = _request_json(ez_base, ez_key, "/api/v1/api-key/parts", params)
        items = []
        if status == 200:
            items = body.get("data") or []
        else:
            # fallback to mock on error
            items = _load_parts()
        for p in items:
            mapped = _map_api_part_to_partir(p)
            if mapped:
                # apply hard filters locally as well
                if _part_matches_constraints(mapped, constraints):
                    results.append(mapped)
        return results

    # fallback: local mock filtering
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


def _map_api_part_to_partir(api_obj: Dict[str, Any]) -> PartIR | None:
    """把 EZ-PLM API 返回的器件对象映射到 PartIR。根据实际返回字段调整映射。"""
    if not isinstance(api_obj, dict):
        return None
    # Common fields mapping with safe access
    try:
        return PartIR.parse_obj({
            "part_number": api_obj.get("partNumber") or api_obj.get("pn") or api_obj.get("part_number") or api_obj.get("id"),
            "manufacturer": api_obj.get("manufacturer") or api_obj.get("mfr"),
            "category": api_obj.get("category"),
            "topology": api_obj.get("topology"),
            "is_domestic": api_obj.get("isDomestic") if api_obj.get("isDomestic") is not None else api_obj.get("is_domestic", False),
            "description": api_obj.get("description") or api_obj.get("summary"),
            "input_voltage_min_v": api_obj.get("inputVoltageMinV") or api_obj.get("input_voltage_min_v"),
            "input_voltage_max_v": api_obj.get("inputVoltageMaxV") or api_obj.get("input_voltage_max_v"),
            "output_current_max_a": api_obj.get("outputCurrentMaxA") or api_obj.get("output_current_max_a") or api_obj.get("iOutMax"),
            "temperature_min_c": api_obj.get("temperatureMinC") or api_obj.get("temperature_min_c"),
            "temperature_max_c": api_obj.get("temperatureMaxC") or api_obj.get("temperature_max_c"),
            "package": api_obj.get("package"),
            "automotive_grade": api_obj.get("automotiveGrade") or api_obj.get("automotive_grade", False),
            "lifecycle_status": api_obj.get("lifecycleStatus") or api_obj.get("lifecycle_status"),
            "stock": api_obj.get("stock") or api_obj.get("inventory") or api_obj.get("qty"),
            "unit_price_cny": api_obj.get("unitPriceCny") or api_obj.get("unit_price") or api_obj.get("price"),
            "datasheet_url": api_obj.get("datasheetUrl") or api_obj.get("datasheet_url") or api_obj.get("datasheet"),
            "replacement_for": api_obj.get("replacementFor") or api_obj.get("replacement_for") or [],
            "source": "ezplm",
        })
    except Exception:
        return None


def _part_matches_constraints(part: PartIR, constraints: RequirementConstraints) -> bool:
    # category/topology
    if constraints.category and part.category != constraints.category:
        return False
    if constraints.topology and part.topology != constraints.topology:
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


