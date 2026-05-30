#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
将 mock_parts.json 与 API 同步：
1. 对每个 mock 器件，查询 API 找属性匹配的真实器件
2. 找到了 → 用 API 器件替换（包含正确的 MPN 和 output_voltage_v）
3. 找不到 → 删除
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, '.')
os.chdir(Path(__file__).parent)

from app.ezplm_client import _request_json
from app.schemas import PartIR, RequirementConstraints

API_KEY = "epk_db0a679877e6665dc81fd224cd56ebdbe2e43e9094c95d4cf160e6a771e4c85e"
API_BASE = "https://www.ezplm.cn"

def extract_output_voltage(api_part: dict) -> float:
    """从 API 响应提取输出电压"""
    from app.ezplm_client import _infer_output_voltage_from_mpn

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

def build_query_keywords(part: dict) -> list:
    """根据 mock 器件的属性，构建 API 查询关键词"""
    """返回关键词列表，优先级从高到低"""
    keywords = []

    # 方式1：从 part_number 提取前缀（TPS54、LM2596 等）
    pn = part.get('part_number', '').upper()
    # 提取字母前缀
    prefix = ''.join(c for c in pn.split('-')[0] if c.isalpha())
    if prefix and len(prefix) >= 2:
        keywords.append(prefix[:6])  # 如 "TPS54"

    # 方式2：根据拓扑
    topo = part.get('topology', '')
    if topo == 'buck':
        # Buck 常见厂商/系列
        if 'LM' in pn:
            keywords.extend(['LM2596', 'LM2576'])
        elif 'TPS' in pn:
            keywords.extend(['TPS54', 'TPS62'])
        elif 'ADP' in pn:
            keywords.append('ADP23')

    # 去重，保留有意义的
    keywords = list(dict.fromkeys(keywords))  # 保持顺序并去重
    return keywords[:3]  # 返回前3个

def find_matching_api_part(mock_part: dict) -> dict:
    """在 API 中查找属性匹配的器件"""
    keywords = build_query_keywords(mock_part)

    if not keywords:
        return None

    # 提取 mock 器件的关键属性
    mock_topo = mock_part.get('topology')
    mock_output_current = mock_part.get('output_current_max_a')
    mock_input_min = mock_part.get('input_voltage_min_v')
    mock_input_max = mock_part.get('input_voltage_max_v')

    for kw in keywords:
        # 查询 API
        status, body = _request_json(
            API_BASE, API_KEY,
            "/api/v1/api-key/parts",
            {"keyword": kw, "pageSize": "50"}
        )

        if status != 200:
            continue

        data = body.get("data", [])
        if not data:
            continue

        # 在返回的器件中找最匹配的
        best_match = None
        best_score = -1

        for api_part in data:
            score = 0

            # 检查拓扑
            api_cat = api_part.get('category', {})
            if isinstance(api_cat, dict):
                cat_name = api_cat.get('name', '').lower()
            else:
                cat_name = str(api_cat).lower()

            if 'buck' in cat_name and mock_topo == 'buck':
                score += 100
            elif 'boost' in cat_name and mock_topo == 'boost':
                score += 100
            elif 'ldo' in cat_name and mock_topo == 'ldo':
                score += 100

            # 检查输出电流是否足够
            api_output_curr = None
            for attr in api_part.get('attributes', []):
                name = str(attr.get('name', '')).lower()
                if '输出电流' in name and '最大' in name:
                    try:
                        api_output_curr = float(str(attr.get('value', '').split()[0]))
                    except:
                        pass

            if api_output_curr and mock_output_current:
                if api_output_curr >= mock_output_current * 0.9:  # 允许 10% 偏差
                    score += 50

            # 检查输入电压范围是否匹配
            api_input_min = None
            api_input_max = None
            for attr in api_part.get('attributes', []):
                name = str(attr.get('name', '')).lower()
                if '输入电压' in name and '最小' in name:
                    try:
                        api_input_min = float(str(attr.get('value', '').split()[0]))
                    except:
                        pass
                if '输入电压' in name and '最大' in name:
                    try:
                        api_input_max = float(str(attr.get('value', '').split()[0]))
                    except:
                        pass

            if mock_input_min and mock_input_max and api_input_min and api_input_max:
                if api_input_min <= mock_input_min and api_input_max >= mock_input_max:
                    score += 50  # 完全覆盖

            if score > best_score:
                best_score = score
                best_match = api_part

        if best_match and best_score >= 100:  # 至少要拓扑匹配
            return best_match

    return None

def convert_api_to_mock_format(api_part: dict) -> dict:
    """将 API 器件转换为 mock 格式"""
    from app.ezplm_client import _infer_output_voltage_from_mpn, _parse_attrs

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

    return {
        'part_number': mpn,
        'manufacturer': mfr_name,
        'category': 'dc_dc_converter',
        'topology': attrs.get('topology'),
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

def main():
    print("=" * 70)
    print("[*] Syncing mock_parts.json with eZ-PLM API")
    print("=" * 70)

    # 加载 mock 数据
    print("\n[*] Loading original mock_parts.json...")
    with open('data/mock_parts.json', 'r', encoding='utf-8') as f:
        original_parts = json.load(f)

    print(f"[+] Loaded {len(original_parts)} parts")

    # 处理每条器件
    synced_parts = []
    deleted_parts = []
    kept_parts = []
    matched_parts = []

    print("\n[*] Processing each part...")

    for i, mock_part in enumerate(original_parts, 1):
        pn = mock_part.get('part_number')

        if i % 20 == 0:
            print(f"  [{i}/{len(original_parts)}]", flush=True)

        # 查询 API 找匹配的器件
        api_part = find_matching_api_part(mock_part)

        if api_part:
            # 找到了对应的 API 器件
            new_part = convert_api_to_mock_format(api_part)
            synced_parts.append(new_part)
            matched_parts.append((pn, new_part['part_number']))
        else:
            # 没找到对应的 API 器件，删除
            deleted_parts.append(pn)

        time.sleep(0.05)

    print(f"\n[RESULT]")
    print(f"  Synced (found in API): {len(synced_parts)}")
    print(f"  Deleted (not found): {len(deleted_parts)}")

    if deleted_parts:
        print(f"\n[!] Deleted {len(deleted_parts)} parts:")
        for pn in deleted_parts[:10]:
            print(f"     - {pn}")
        if len(deleted_parts) > 10:
            print(f"     ... and {len(deleted_parts)-10} more")

    if matched_parts:
        print(f"\n[+] Name changes (sample):")
        for old, new in matched_parts[:5]:
            if old != new:
                print(f"     {old} → {new}")

    # 保存备份
    print(f"\n[*] Saving backup...")
    with open('data/mock_parts.json.backup.original', 'w', encoding='utf-8') as f:
        json.dump(original_parts, f, ensure_ascii=False, indent=2)
    print(f"[OK] Backup: data/mock_parts.json.backup.original")

    # 保存新的 mock 数据
    print(f"\n[*] Saving synced mock_parts.json...")
    with open('data/mock_parts.json', 'w', encoding='utf-8') as f:
        json.dump(synced_parts, f, ensure_ascii=False, indent=2)
    print(f"[OK] Synced data/mock_parts.json ({len(synced_parts)} parts)")

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
        print(f"     {sorted(list(vouts.keys()))[:15]}")

    # 检查 5V
    buck_5v = [p for p in final_data if p.get('topology') == 'buck' and p.get('output_voltage_v') == 5.0]
    print(f"\n[CRITICAL] 5V Buck parts (for dc_dc_001/008): {len(buck_5v)}")
    if buck_5v:
        print(f"  Sample: {buck_5v[0]['part_number']}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
