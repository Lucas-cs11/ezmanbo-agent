#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 eZ-PLM API 获取 output_voltage_v，补充到 mock_parts.json
只补充输出电压，不改动其他字段
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

def query_and_build_map() -> dict:
    """查询 API 并构建 MPN -> output_voltage 的映射"""
    print("[*] Querying eZ-PLM API for output voltage data...")

    keywords = [
        # Buck
        "TPS54", "TPS62", "LM2596", "LM2576", "ADP23", "LTC388",
        # Boost
        "TPS61", "TPS63",
        # LDO
        "TPS79", "TPS72", "MCP1703", "LM317", "TL431", "ST", "STPMIC"
    ]

    mpn_to_vout = {}
    total_queried = 0
    success_count = 0

    for kw in keywords:
        print(f"  Querying {kw}...", end=" ", flush=True)

        status, body = _request_json(
            API_BASE, API_KEY,
            "/api/v1/api-key/parts",
            {"keyword": kw, "pageSize": "50"}
        )

        if status != 200:
            print(f"[FAIL]")
            continue

        data = body.get("data", [])
        print(f"[OK {len(data)}]")

        for api_part in data:
            mpn = api_part.get('mpn')
            if not mpn:
                continue

            total_queried += 1
            vout = extract_output_voltage(api_part)

            if vout:
                # 保存完整 MPN 和前缀
                mpn_to_vout[mpn] = vout
                # 也保存前缀版本（用于模糊匹配）
                prefix = ''.join(c for c in mpn.split('-')[0] if not c.isdigit() or mpn.index(c) < 6)
                if prefix and prefix not in mpn_to_vout:
                    mpn_to_vout[prefix] = vout
                success_count += 1

        time.sleep(0.2)

    print(f"\n[+] Collected {success_count}/{total_queried} parts with output voltage")
    return mpn_to_vout

def main():
    print("=" * 70)
    print("[*] Enriching mock_parts.json with output_voltage_v")
    print("=" * 70)

    # 加载原始 mock 数据
    print("\n[*] Loading mock_parts.json...")
    with open('data/mock_parts.json', 'r', encoding='utf-8') as f:
        parts = json.load(f)

    print(f"[+] Loaded {len(parts)} parts")

    # 查询 API 获取 output_voltage_v 映射
    mpn_to_vout = query_and_build_map()

    # 补充 output_voltage_v 字段
    print(f"\n[*] Enriching parts with output voltage...")
    enriched_count = 0

    for part in parts:
        mpn = part.get('part_number')
        if mpn in mpn_to_vout:
            part['output_voltage_v'] = mpn_to_vout[mpn]
            enriched_count += 1

    print(f"[+] Enriched {enriched_count}/{len(parts)} parts")

    # 保存备份
    print(f"\n[*] Saving backup...")
    with open('data/mock_parts.json.backup', 'w', encoding='utf-8') as f:
        json.dump(parts, f, ensure_ascii=False, indent=2)
    print(f"[OK] Backup: data/mock_parts.json.backup")

    # 保存更新后的数据
    print(f"\n[*] Saving updated mock_parts.json...")
    with open('data/mock_parts.json', 'w', encoding='utf-8') as f:
        json.dump(parts, f, ensure_ascii=False, indent=2)
    print(f"[OK] Updated data/mock_parts.json")

    # 验证
    print(f"\n[*] Verification...")
    with open('data/mock_parts.json', 'r', encoding='utf-8') as f:
        saved = json.load(f)

    with_vout = sum(1 for p in saved if 'output_voltage_v' in p and p.get('output_voltage_v') is not None)
    print(f"[OK] Parts with output_voltage_v: {with_vout}/{len(saved)}")

    # 统计常见输出电压
    vouts = {}
    for p in saved:
        if 'output_voltage_v' in p and p.get('output_voltage_v'):
            v = p['output_voltage_v']
            vouts[v] = vouts.get(v, 0) + 1

    print(f"\n[+] Unique output voltages: {len(vouts)}")
    print(f"    Common: {sorted(list(vouts.keys()))[:10]}")

    # 检查 5V 器件
    buck_5v = [p for p in saved if p.get('topology') == 'buck' and p.get('output_voltage_v') == 5.0]
    print(f"\n[CRITICAL] 5V Buck parts (for dc_dc_001/008): {len(buck_5v)}")
    if buck_5v:
        print(f"  Sample: {buck_5v[0]['part_number']}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
