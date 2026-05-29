#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
第二版：用 mock 中的真实 MPN 直接查询 API，获取 output_voltage_v
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, '.')
os.chdir(Path(__file__).parent)

from app.ezplm_client import _request_json, _infer_output_voltage_from_mpn

API_KEY = "epk_db0a679877e6665dc81fd224cd56ebdbe2e43e9094c95d4cf160e6a771e4c85e"
API_BASE = "https://www.ezplm.cn"

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

def main():
    print("=" * 70)
    print("[*] Enriching with direct MPN query")
    print("=" * 70)

    # 加载 mock 数据
    print("\n[*] Loading mock_parts.json...")
    with open('data/mock_parts.json', 'r', encoding='utf-8') as f:
        parts = json.load(f)

    print(f"[+] Loaded {len(parts)} parts")

    # 找出真实 MPN（包含 TPS、LM、ADP 等）
    real_mpn_patterns = ['TPS', 'LM', 'ADP', 'LTC', 'ST', 'MCP']
    real_parts = []

    for p in parts:
        pn = p['part_number'].upper()
        if any(pat in pn for pat in real_mpn_patterns):
            real_parts.append(p)

    print(f"[+] Found {len(real_parts)} real MPN parts")

    # 直接查询这些 MPN
    print(f"\n[*] Querying API for real MPNs...")
    enriched_count = 0
    success_count = 0

    for i, part in enumerate(real_parts, 1):
        mpn = part['part_number']

        if i % 20 == 0 or i == 1:
            print(f"  [{i}/{len(real_parts)}]...", flush=True)

        # 直接查询这个 MPN
        status, body = _request_json(
            API_BASE, API_KEY,
            "/api/v1/api-key/parts",
            {"keyword": mpn, "pageSize": "5"}
        )

        if status != 200:
            continue

        data = body.get("data", [])
        if data:
            api_part = data[0]  # 取第一个匹配
            vout = extract_output_voltage(api_part)

            if vout:
                part['output_voltage_v'] = vout
                enriched_count += 1
                success_count += 1

                # 打印发现 5V 的情况
                if vout == 5.0:
                    print(f"    [+] Found 5V: {mpn}")

        time.sleep(0.1)

    print(f"\n[+] Successfully enriched: {enriched_count}/{len(real_parts)}")

    # 也处理虚拟器件（基于名称或规则）
    mock_parts = [p for p in parts if 'MOCK' in p['part_number']]
    print(f"\n[*] Processing {len(mock_parts)} mock parts...")

    # 虚拟器件：根据拓扑和数据中的其他信息推断
    for p in mock_parts:
        if 'AEC' in p['part_number']:  # 车规器件通常是 5V
            if p.get('topology') == 'buck':
                p['output_voltage_v'] = 5.0
                enriched_count += 1

    print(f"[+] Total enriched: {enriched_count}/209")

    # 保存
    print(f"\n[*] Saving...")
    with open('data/mock_parts.json', 'w', encoding='utf-8') as f:
        json.dump(parts, f, ensure_ascii=False, indent=2)

    print(f"[OK] Saved")

    # 验证
    with open('data/mock_parts.json', 'r', encoding='utf-8') as f:
        saved = json.load(f)

    with_vout = sum(1 for p in saved if 'output_voltage_v' in p and p.get('output_voltage_v') is not None)
    print(f"\n[VERIFY] Parts with output_voltage_v: {with_vout}/209")

    # 统计 5V
    buck_5v = [p for p in saved if p.get('topology') == 'buck' and p.get('output_voltage_v') == 5.0]
    print(f"[CRITICAL] 5V Buck parts: {len(buck_5v)}")
    if buck_5v:
        for p in buck_5v[:5]:
            print(f"  - {p['part_number']}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
