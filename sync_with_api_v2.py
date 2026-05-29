#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用 API 作为主表来同步 mock 数据：
1. 从 API 查询所有器件，收集完整信息（包括 output_voltage_v）
2. 检查 mock 中是否有这个器件（通过名称匹配）
3. 如果有 → 用 API 信息更新
4. 如果没有 → 添加到结果
最后，删除 mock 中 API 中没有的器件
"""
import json
import os
import sys
import time
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, '.')
os.chdir(Path(__file__).parent)

from app.ezplm_client import _request_json, _infer_output_voltage_from_mpn, _parse_attrs

API_KEY = "epk_db0a679877e6665dc81fd224cd56ebdbe2e43e9094c95d4cf160e6a771e4c85e"
API_BASE = "https://www.ezplm.cn"

# API 关键词
API_KEYWORDS = {
    "buck": ["TPS54", "TPS62", "LM2596", "LM2576", "ADP23", "LTC388", "LTC365", "ST1S", "L5970"],
    "boost": ["TPS61", "TPS63", "LTC370", "LTC358", "MCP1640"],
    "ldo": ["TPS79", "TPS72", "MCP1703", "MCP1700", "ADP312", "LT1763", "MCP1501"],
}

def extract_output_voltage(api_part: dict) -> float:
    """从 API 响应提取输出电压"""
    mpn = api_part.get('mpn', '')

    # 方法1：从型号推断
    vout = _infer_output_voltage_from_mpn(mpn)
    if vout:
        return vout

    # 方法2：从 attributes 提取
    for attr in api_part.get('attributes', []):
        name = str(attr.get('name', '')).lower()
        if '输出电压' in name or 'output voltage' in name:
            try:
                val = str(attr.get('value', ''))
                return float(val.split()[0])
            except (ValueError, TypeError):
                pass

    return None

def convert_api_to_mock_format(api_part: dict, original_mock_part: dict = None) -> dict:
    """将 API 器件转换为 mock 格式"""
    mpn = api_part.get('mpn', '')
    mfr = api_part.get('manufacturer', {})
    if isinstance(mfr, dict):
        mfr_name = mfr.get('name', 'Unknown')
    else:
        mfr_name = str(mfr)

    # 解析 attributes
    attrs = _parse_attrs(api_part.get('attributes', []))

    # 提取输出电压
    output_voltage = _infer_output_voltage_from_mpn(mpn)
    if not output_voltage:
        output_voltage = attrs.get('output_voltage_v')

    # 基于原始 mock 保留某些字段（如果有的话）
    base_dict = {
        'part_number': mpn,
        'manufacturer': mfr_name,
        'category': 'dc_dc_converter',
        'topology': attrs.get('topology') or 'buck',
        'is_domestic': False,
        'input_voltage_min_v': attrs.get('input_voltage_min_v'),
        'input_voltage_max_v': attrs.get('input_voltage_max_v'),
        'output_voltage_v': output_voltage,
        'output_current_max_a': attrs.get('output_current_max_a'),
        'temperature_min_c': attrs.get('temperature_min_c'),
        'temperature_max_c': attrs.get('temperature_max_c'),
        'package': attrs.get('package'),
        'automotive_grade': False,
        'lifecycle_status': 'active',
        'stock': 0,
        'unit_price_cny': 0.0,
        'datasheet_url': None,
        'replacement_for': [],
        'source': 'api'
    }

    # 如果原始 mock 有这个器件，尝试保留某些字段
    if original_mock_part:
        if original_mock_part.get('automotive_grade'):
            base_dict['automotive_grade'] = True
        if original_mock_part.get('stock'):
            base_dict['stock'] = original_mock_part['stock']
        if original_mock_part.get('is_domestic'):
            base_dict['is_domestic'] = True

    return base_dict

def main():
    print("=" * 70)
    print("[*] Syncing with API as master source")
    print("=" * 70)

    # 加载原始 mock 数据（用于查找对应关系）
    print("\n[*] Loading original mock_parts.json...")
    with open('data/mock_parts.json', 'r', encoding='utf-8') as f:
        original_mock = json.load(f)

    mock_by_name = {p['part_number']: p for p in original_mock}
    print(f"[+] Loaded {len(original_mock)} original parts")

    # 从 API 查询所有器件
    print("\n[*] Querying API for all parts...")

    api_parts = []
    total_api_parts = 0

    for topo, keywords in API_KEYWORDS.items():
        print(f"  [{topo.upper()}]", end=" ", flush=True)
        count_this_topo = 0

        for kw in keywords:
            status, body = _request_json(
                API_BASE, API_KEY,
                "/api/v1/api-key/parts",
                {"keyword": kw, "pageSize": "50"}
            )

            if status != 200:
                continue

            data = body.get("data", [])
            for api_part in data:
                api_parts.append((topo, api_part))
                count_this_topo += 1
                total_api_parts += 1

            time.sleep(0.1)

        print(f"{count_this_topo} ", end="")

    print(f"\n[+] Total API parts: {total_api_parts}")

    # 建立 API MPN 到器件的映射
    api_mpn_to_part = {}
    for topo, api_part in api_parts:
        mpn = api_part.get('mpn')
        if mpn:
            api_mpn_to_part[mpn] = (topo, api_part)

    print(f"[+] Unique API MPN: {len(api_mpn_to_part)}")

    # 同步过程：遍历 API 器件，检查 mock 中是否有对应的
    print("\n[*] Syncing mock with API...")

    synced_parts = []
    kept_from_mock = set()
    api_not_in_mock = []

    for mpn, (topo, api_part) in sorted(api_mpn_to_part.items()):
        # 检查 mock 中是否有这个 MPN
        if mpn in mock_by_name:
            # 有对应的 mock 器件，用 API 信息更新它
            original = mock_by_name[mpn]
            updated = convert_api_to_mock_format(api_part, original)
            synced_parts.append(updated)
            kept_from_mock.add(mpn)
        else:
            # 这个 API 器件在 mock 中没有对应的，记录下来
            api_not_in_mock.append(mpn)

    print(f"\n[RESULT]")
    print(f"  Kept from original mock: {len(kept_from_mock)}")
    print(f"  API parts not in mock: {len(api_not_in_mock)}")
    print(f"  Total synced: {len(synced_parts)}")

    if api_not_in_mock:
        print(f"\n[+] Adding {len(api_not_in_mock)} API-only parts to mock...")
        for mpn in api_not_in_mock:
            topo, api_part = api_mpn_to_part[mpn]
            new_part = convert_api_to_mock_format(api_part)
            synced_parts.append(new_part)

    final_count = len(synced_parts)

    # 检查有哪些 mock 器件被删除了
    deleted_from_mock = set(mock_by_name.keys()) - kept_from_mock
    if deleted_from_mock:
        print(f"\n[!] Deleted {len(deleted_from_mock)} mock parts not found in API:")
        for mpn in sorted(list(deleted_from_mock))[:10]:
            print(f"     - {mpn}")
        if len(deleted_from_mock) > 10:
            print(f"     ... and {len(deleted_from_mock)-10} more")

    # 保存备份
    print(f"\n[*] Saving backup...")
    with open('data/mock_parts.json.backup.before_sync', 'w', encoding='utf-8') as f:
        json.dump(original_mock, f, ensure_ascii=False, indent=2)
    print(f"[OK] Backup: data/mock_parts.json.backup.before_sync")

    # 保存同步后的数据
    print(f"\n[*] Saving synced mock_parts.json...")
    with open('data/mock_parts.json', 'w', encoding='utf-8') as f:
        json.dump(synced_parts, f, ensure_ascii=False, indent=2)
    print(f"[OK] Synced data/mock_parts.json ({final_count} parts)")

    # 验证
    print(f"\n[*] Verification...")
    with open('data/mock_parts.json', 'r', encoding='utf-8') as f:
        final_data = json.load(f)

    with_vout = sum(1 for p in final_data if 'output_voltage_v' in p and p.get('output_voltage_v') is not None)
    print(f"[OK] Total parts: {len(final_data)}")
    print(f"[OK] Parts with output_voltage_v: {with_vout}/{len(final_data)}")

    # 统计输出电压
    vouts = {}
    for p in final_data:
        if 'output_voltage_v' in p and p.get('output_voltage_v'):
            v = p['output_voltage_v']
            vouts[v] = vouts.get(v, 0) + 1

    print(f"[OK] Unique output voltages: {len(vouts)}")
    if vouts:
        print(f"     {sorted(list(vouts.keys()))[:20]}")

    # 检查 5V
    buck_5v = [p for p in final_data if p.get('topology') == 'buck' and p.get('output_voltage_v') == 5.0]
    print(f"\n[CRITICAL] 5V Buck parts (for dc_dc_001/008): {len(buck_5v)}")
    if buck_5v:
        print(f"  Samples:")
        for p in buck_5v[:5]:
            print(f"    {p['part_number']}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
