#!/usr/bin/env python3
"""
从 eZ-PLM API 补充 mock_parts.json 的缺失数据。
主要补充: output_voltage_v, output_current_max_a, 以及其他电气参数。
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ezplm_client import _request_json, _map_api_part_to_partir, _infer_output_voltage_from_mpn

# API 配置
API_KEY = "epk_db0a679877e6665dc81fd224cd56ebdbe2e43e9094c95d4cf160e6a771e4c85e"
BASE_URL = "https://www.ezplm.cn"
MOCK_FILE = Path(__file__).parent.parent / "data" / "mock_parts.json"

# 查询关键字（优先级顺序）
SEARCH_KEYWORDS = [
    # Buck converters
    "TPS54", "TPS62", "LM2596", "LM2576", "ADP23", "LTC388", "LTC365", "ST1S", "L5970",
    # Boost converters
    "TPS61", "TPS63", "LTC370", "LTC358", "MCP1640",
    # LDO
    "TPS79", "TPS72", "MCP1703", "MCP1700", "ADP312", "LT1763", "MCP1501",
]

def query_part_from_api(part_number: str) -> Optional[Dict[str, Any]]:
    """通过 API 查询单个零件。"""
    # Try exact MPN search
    status, data = _request_json(
        BASE_URL,
        API_KEY,
        "/api/v1/api-key/parts",
        {"keyword": part_number, "pageSize": "10"}
    )

    if status != 200:
        return None

    parts = data.get("data", [])
    if not parts:
        return None

    # Find exact match or first match
    for p in parts:
        if p.get("mpn") == part_number:
            return p

    return parts[0] if parts else None


def enrich_part(part: Dict[str, Any]) -> Dict[str, Any]:
    """用 API 数据补充单个器件的缺失字段。"""
    original_part = part.copy()
    pn = part.get("part_number")

    if not pn:
        return part

    # 如果已有关键参数，尝试从 MPN 推断
    if part.get("output_voltage_v") is None:
        inferred = _infer_output_voltage_from_mpn(pn)
        if inferred:
            part["output_voltage_v"] = inferred
            print(f"  [MPN INFER] {pn}: output_voltage_v = {inferred}V")

    # 如果仍缺少关键参数，查询 API
    needs_api = (
        part.get("output_voltage_v") is None or
        part.get("output_current_max_a") is None
    )

    if needs_api:
        print(f"  [API QUERY] {pn}...", end=" ", flush=True)
        api_part = query_part_from_api(pn)

        if api_part:
            mapped = _map_api_part_to_partir(api_part)
            if mapped:
                # 合并 API 数据
                if part.get("output_voltage_v") is None and mapped.output_voltage_v:
                    part["output_voltage_v"] = mapped.output_voltage_v
                    print(f"output_voltage_v={mapped.output_voltage_v}V", end=" ", flush=True)

                if part.get("output_current_max_a") is None and mapped.output_current_max_a:
                    part["output_current_max_a"] = mapped.output_current_max_a
                    print(f"output_current_max_a={mapped.output_current_max_a}A", end=" ", flush=True)

                if part.get("temperature_min_c") is None and mapped.temperature_min_c:
                    part["temperature_min_c"] = mapped.temperature_min_c
                    part["temperature_max_c"] = mapped.temperature_max_c
                    print(f"temp={mapped.temperature_min_c}~{mapped.temperature_max_c}C", end=" ", flush=True)

                if part.get("topology") is None and mapped.topology:
                    part["topology"] = mapped.topology

                print("[OK]")
            else:
                print("[PARSE FAILED]")
        else:
            print("[NOT FOUND]")

        # 间隔以避免 API 限流
        time.sleep(0.1)

    return part


def main():
    print(f"Loading mock_parts.json...")
    with open(MOCK_FILE, "r", encoding="utf-8") as f:
        parts = json.load(f)

    total = len(parts)
    print(f"Total parts: {total}")
    print()

    # 统计缺失情况
    missing_voltage = sum(1 for p in parts if p.get("output_voltage_v") is None)
    missing_current = sum(1 for p in parts if p.get("output_current_max_a") is None)

    print(f"Parts missing output_voltage_v: {missing_voltage}/{total}")
    print(f"Parts missing output_current_max_a: {missing_current}/{total}")
    print()

    # 补充数据
    print("Enriching parts from API...")
    enriched_count = 0
    for i, part in enumerate(parts, 1):
        if i % 50 == 0:
            print(f"\n[{i}/{total}] Progress...")

        original = part.copy()
        part = enrich_part(part)

        # 检查是否有更新
        if part != original:
            enriched_count += 1

    print()
    print(f"Enriched {enriched_count} parts")

    # 统计更新后的情况
    now_missing_voltage = sum(1 for p in parts if p.get("output_voltage_v") is None)
    now_missing_current = sum(1 for p in parts if p.get("output_current_max_a") is None)

    print(f"\nAfter enrichment:")
    print(f"  Parts with output_voltage_v: {total - now_missing_voltage}/{total}")
    print(f"  Parts with output_current_max_a: {total - now_missing_current}/{total}")

    # 有推荐值的器件
    has_recommendations = sum(
        1 for p in parts
        if p.get("output_voltage_v") is not None and p.get("output_current_max_a") is not None
    )
    print(f"  Parts with BOTH params (可推荐): {has_recommendations}/{total}")

    # 保存备份
    backup_file = MOCK_FILE.with_suffix(".json.backup_pre_enrich")
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(json.load(open(MOCK_FILE, "r", encoding="utf-8")), f, ensure_ascii=False, indent=2)
    print(f"\nBackup saved: {backup_file}")

    # 保存更新
    with open(MOCK_FILE, "w", encoding="utf-8") as f:
        json.dump(parts, f, ensure_ascii=False, indent=2)

    print(f"Updated: {MOCK_FILE}")
    print("\nDone!")

if __name__ == "__main__":
    main()
