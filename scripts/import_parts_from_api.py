#!/usr/bin/env python3
"""从EZ-PLM API查询LDO和Boost器件，导入到mock_parts.json"""

import base64
import hashlib
import hmac
import json
import sys
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Tuple

API_KEY = "epk_db0a679877e6665dc81fd224cd56ebdbe2e43e9094c95d4cf160e6a771e4c85e"
BASE_URL = "https://www.ezplm.cn"
KEYWORDS = [
    "LDO", "低压降",
    "Boost", "升压转换器",
    "MP2307", "TL431", "RT8059",  # Common LDO/Boost families
    "PMIC", "电源IC", "voltage regulator"
]
PAGE_SIZE = "50"

MOCK_PARTS_FILE = Path(__file__).parents[1] / "data" / "mock_parts.json"


def canonical_query(params: Dict[str, Any]) -> str:
    items: List[Tuple[str, str]] = []
    for key, value in params.items():
        if value is None or value == "":
            continue
        items.append((str(key), str(value)))
    items.sort(key=lambda item: (item[0], item[1]))
    return "&".join(
        f"{urllib.parse.quote(key, safe='')}={urllib.parse.quote(value, safe='')}"
        for key, value in items
    )


def build_signature(
    api_key: str,
    method: str,
    path: str,
    params: Dict[str, Any],
    timestamp: str,
    nonce: str,
) -> str:
    canonical = "\n".join(
        [method.upper(), path, canonical_query(params), timestamp, nonce]
    )
    digest = hmac.new(
        api_key.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.urlsafe_b64encode(digest).decode("utf-8").rstrip("=")


def request_json(
    base_url: str,
    api_key: str,
    path: str,
    params: Dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    timestamp = str(int(time.time()))
    nonce = str(uuid.uuid4())
    signature = build_signature(api_key, "GET", path, params, timestamp, nonce)
    query = canonical_query(params)
    url = f"{base_url}{path}"
    if query:
        url = f"{url}?{query}"

    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "X-API-Key": api_key,
            "X-Timestamp": timestamp,
            "X-Nonce": nonce,
            "X-Signature": signature,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except json.JSONDecodeError:
            parsed = {"raw": body}
        return exc.code, parsed
    except Exception as e:
        return 0, {"error": str(e)}


def parse_attributes(attrs: list) -> Dict[str, Any]:
    """从EZ-PLM attributes数组中提取电气参数"""
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
                import re
                m = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:to|~|至|～)\s*(-?\d+(?:\.\d+)?)", val)
                if m:
                    result["temperature_min_c"] = float(m.group(1))
                    result["temperature_max_c"] = float(m.group(2))
            elif "封装" in name or "package" in name.lower():
                result["package"] = val
        except (ValueError, TypeError):
            pass
    return result


def map_api_part(api_obj: Dict[str, Any]) -> Dict[str, Any] | None:
    """把EZ-PLM API返回格式映射到mock part格式"""
    if not isinstance(api_obj, dict):
        return None

    try:
        part_number = (
            api_obj.get("mpn") or api_obj.get("partNumber")
            or api_obj.get("pn") or api_obj.get("part_number")
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

        # Infer category and topology from part name and category
        part_name_lower = part_number.lower()
        cat_name_lower = cat_name.lower()

        topology = "buck"
        category = "dc_dc_converter"

        if "ldo" in cat_name_lower or "ldo" in part_name_lower or "低压降" in cat_name:
            topology = "ldo"
            category = "ldo"
        elif "boost" in cat_name_lower or "boost" in part_name_lower or "升压" in cat_name:
            topology = "boost"
            category = "boost"

        # is_domestic: check manufacturer name against known domestic list
        domestic_manufacturers = {
            "立锜", "圣邦", "南芯", "华润", "矽力杰", "思瑞浦", "芯朋", "英集芯",
            "纳芯微", "杰华特", "芯源系统", "美芯晟", "晶丰明源", "上海贝岭",
        }
        is_domestic = False
        if manufacturer:
            is_domestic = any(d in manufacturer for d in domestic_manufacturers)

        # datasheet url
        pdf_raw = api_obj.get("pdf") or {}
        datasheet_url = (
            pdf_raw.get("url") if isinstance(pdf_raw, dict)
            else api_obj.get("datasheetUrl") or api_obj.get("datasheet_url")
        )

        # parse attributes
        attrs = parse_attributes(api_obj.get("attributes") or [])

        # Provide reasonable defaults if electrical specs are missing
        input_min = attrs.get("input_voltage_min_v") or (2.5 if topology == "ldo" else 5.0)
        input_max = attrs.get("input_voltage_max_v") or (36.0 if topology in ["buck", "boost"] else 5.5)
        output_current = attrs.get("output_current_max_a") or (1.5 if topology == "ldo" else 3.0)
        temp_min = attrs.get("temperature_min_c") or -40
        temp_max = attrs.get("temperature_max_c") or 125

        return {
            "part_number": part_number,
            "manufacturer": manufacturer or "Unknown",
            "category": category,
            "topology": topology,
            "is_domestic": is_domestic,
            "input_voltage_min_v": input_min,
            "input_voltage_max_v": input_max,
            "output_current_max_a": output_current,
            "temperature_min_c": temp_min,
            "temperature_max_c": temp_max,
            "package": attrs.get("package") or api_obj.get("package") or "QFN",
            "automotive_grade": False,
            "stock": api_obj.get("stock") or 5000,
            "unit_price_cny": api_obj.get("unitPriceCny") or api_obj.get("unit_price") or 5.0,
            "lifecycle_status": api_obj.get("lifecycleStatus") or api_obj.get("lifecycle_status") or "active",
            "datasheet_url": datasheet_url or f"https://www.ezplm.cn/part/{part_number}",
            "replacement_for": api_obj.get("replacementFor") or api_obj.get("replacement_for") or [],
        }
    except Exception as e:
        print(f"Error mapping part: {e}", file=sys.stderr)
        return None


def main() -> int:
    print("开始从EZ-PLM API导入LDO和Boost器件...")

    # Load existing parts
    existing_parts = []
    existing_part_numbers = set()

    try:
        with open(MOCK_PARTS_FILE, "r", encoding="utf-8") as f:
            existing_parts = json.load(f)
            existing_part_numbers = {p.get("part_number") for p in existing_parts}
        print(f"已加载{len(existing_parts)}条现有器件数据")
    except FileNotFoundError:
        print("警告：mock_parts.json不存在，将创建新文件")

    new_parts = []

    # Query each keyword
    for keyword in KEYWORDS:
        print(f"\n查询关键词: {keyword}")
        status, body = request_json(
            BASE_URL,
            API_KEY,
            "/api/v1/api-key/parts",
            {"keyword": keyword, "pageSize": PAGE_SIZE},
        )

        if status != 200:
            print(f"错误：HTTP {status}")
            print(f"响应: {json.dumps(body, ensure_ascii=False, indent=2)}")
            continue

        items = body.get("data", [])
        print(f"找到{len(items)}条{keyword}相关器件")

        for item in items:
            mapped = map_api_part(item)
            if mapped:
                part_num = mapped.get("part_number")
                if part_num and part_num not in existing_part_numbers:
                    new_parts.append(mapped)
                    existing_part_numbers.add(part_num)
                    print(f"  [OK] {part_num} ({mapped.get('manufacturer')})")
                elif part_num:
                    print(f"  [SKIP] {part_num} (already exists)")

    # Merge and save
    all_parts = existing_parts + new_parts

    print(f"\n总计：{len(new_parts)}条新器件，现在共有{len(all_parts)}条器件")

    MOCK_PARTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MOCK_PARTS_FILE, "w", encoding="utf-8") as f:
        json.dump(all_parts, f, ensure_ascii=False, indent=2)

    print(f"[OK] Saved to {MOCK_PARTS_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
