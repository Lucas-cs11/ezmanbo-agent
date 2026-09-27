#!/usr/bin/env python3
"""
重新构建 mock_parts.json：直接从 eZ-PLM API 获取所有已知关键词的器件。
比 v1 更直接 - 通过 API 关键字前缀批量获取完整数据。
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Set

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ezplm_client import _request_json, _map_api_part_to_partir

API_KEY = "epk_db0a679877e6665dc81fd224cd56ebdbe2e43e9094c95d4cf160e6a771e4c85e"
BASE_URL = "https://www.ezplm.cn"
MOCK_FILE = Path(__file__).parent.parent / "data" / "mock_parts.json"

# 按类别分组的搜索关键字
KEYWORDS_BY_CATEGORY = {
    "buck": [
        "TPS54", "TPS62", "LM2596", "LM2576", "ADP23", "LTC388", "LTC365", "ST1S", "L5970"
    ],
    "boost": [
        "TPS61", "TPS63", "LTC370", "LTC358", "MCP1640"
    ],
    "ldo": [
        "TPS79", "TPS72", "MCP1703", "MCP1700", "ADP312", "LT1763", "MCP1501"
    ],
}

def fetch_all_from_api() -> Dict[str, Dict[str, Any]]:
    """通过 API 按关键字批量获取器件，返回 {part_number: api_obj}。"""
    parts_by_pn: Dict[str, Dict[str, Any]] = {}
    total_fetched = 0

    for category, keywords in KEYWORDS_BY_CATEGORY.items():
        print(f"\n[{category.upper()}] Fetching {len(keywords)} keyword groups...")

        for kw_idx, kw in enumerate(keywords, 1):
            print(f"  [{kw_idx}/{len(keywords)}] {kw}...", end=" ", flush=True)

            status, data = _request_json(
                BASE_URL,
                API_KEY,
                "/api/v1/api-key/parts",
                {"keyword": kw, "pageSize": "100"}  # 增加 pageSize 到 100
            )

            if status == 200:
                api_parts = data.get("data", [])
                new_count = 0
                for ap in api_parts:
                    pn = ap.get("mpn") or ap.get("part_number") or ap.get("id")
                    if pn and pn not in parts_by_pn:
                        parts_by_pn[pn] = ap
                        new_count += 1

                print(f"found {len(api_parts)}, new {new_count}")
                total_fetched += new_count
            else:
                print(f"ERROR {status}")

            time.sleep(0.05)  # 间隔以避免限流

    print(f"\nTotal unique parts from API: {len(parts_by_pn)}")
    return parts_by_pn


def convert_to_mock_format(api_part: Dict[str, Any]) -> Dict[str, Any]:
    """将 API 部件转换为 mock 格式。"""
    mapped = _map_api_part_to_partir(api_part)
    if not mapped:
        return None

    return {
        "part_number": mapped.part_number,
        "manufacturer": mapped.manufacturer,
        "category": mapped.category or "dc_dc_converter",
        "topology": mapped.topology,
        "is_domestic": mapped.is_domestic,
        "description": mapped.description,
        "input_voltage_min_v": mapped.input_voltage_min_v,
        "input_voltage_max_v": mapped.input_voltage_max_v,
        "output_voltage_v": mapped.output_voltage_v,
        "output_current_max_a": mapped.output_current_max_a,
        "temperature_min_c": mapped.temperature_min_c,
        "temperature_max_c": mapped.temperature_max_c,
        "package": mapped.package,
        "automotive_grade": mapped.automotive_grade,
        "lifecycle_status": mapped.lifecycle_status,
        "stock": mapped.stock,
        "unit_price_cny": mapped.unit_price_cny,
        "datasheet_url": mapped.datasheet_url,
        "replacement_for": mapped.replacement_for or [],
        "source": "api",
    }


def main():
    # 加载原始 mock 数据用于参考
    with open(MOCK_FILE, "r", encoding="utf-8") as f:
        original_parts = json.load(f)

    original_pns = {p.get("part_number") for p in original_parts}
    print(f"Original mock_parts.json: {len(original_parts)} parts")
    print(f"Unique part numbers: {len(original_pns)}")

    # 从 API 获取所有数据
    api_parts = fetch_all_from_api()

    # 转换为 mock 格式
    print(f"\nConverting to mock format...")
    converted_parts = []
    successful = 0
    failed = 0

    for pn, api_obj in api_parts.items():
        mock_part = convert_to_mock_format(api_obj)
        if mock_part:
            converted_parts.append(mock_part)
            successful += 1
        else:
            failed += 1

    print(f"  Successful: {successful}")
    print(f"  Failed: {failed}")

    # 排序
    converted_parts.sort(key=lambda p: (p["manufacturer"], p["part_number"]))

    # 统计参数完整性
    print(f"\nParameter completeness:")
    has_vout = sum(1 for p in converted_parts if p.get("output_voltage_v"))
    has_iout = sum(1 for p in converted_parts if p.get("output_current_max_a"))
    has_both = sum(1 for p in converted_parts if p.get("output_voltage_v") and p.get("output_current_max_a"))

    print(f"  With output_voltage_v: {has_vout}/{len(converted_parts)} ({has_vout/len(converted_parts)*100:.1f}%)")
    print(f"  With output_current_max_a: {has_iout}/{len(converted_parts)} ({has_iout/len(converted_parts)*100:.1f}%)")
    print(f"  With BOTH: {has_both}/{len(converted_parts)} ({has_both/len(converted_parts)*100:.1f}%)")

    # 保存备份
    backup = MOCK_FILE.with_suffix(".json.backup_pre_rebuild")
    with open(backup, "w", encoding="utf-8") as f:
        json.dump(original_parts, f, ensure_ascii=False, indent=2)
    print(f"\nBackup: {backup}")

    # 保存新数据
    with open(MOCK_FILE, "w", encoding="utf-8") as f:
        json.dump(converted_parts, f, ensure_ascii=False, indent=2)

    print(f"Updated: {MOCK_FILE}")
    print(f"  Original: {len(original_parts)} parts")
    print(f"  New: {len(converted_parts)} parts")
    print(f"  Change: {len(converted_parts) - len(original_parts):+d}")

    print("\nDone!")


if __name__ == "__main__":
    main()
