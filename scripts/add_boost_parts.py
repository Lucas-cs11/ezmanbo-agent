#!/usr/bin/env python3
"""为mock数据添加常见的Boost转换器"""

import json
from pathlib import Path

MOCK_PARTS_FILE = Path(__file__).parents[1] / "data" / "mock_parts.json"

# Common Boost converter parts with realistic specs
BOOST_PARTS = [
    {
        "part_number": "TPS61030DSG",
        "manufacturer": "Texas Instruments",
        "category": "boost",
        "topology": "boost",
        "is_domestic": False,
        "input_voltage_min_v": 0.7,
        "input_voltage_max_v": 5.5,
        "output_current_max_a": 1.0,
        "temperature_min_c": -40,
        "temperature_max_c": 125,
        "package": "MSOP-8",
        "automotive_grade": False,
        "stock": 3000,
        "unit_price_cny": 12.5,
        "lifecycle_status": "active",
        "datasheet_url": "https://www.ti.com/product/TPS61030",
        "replacement_for": []
    },
    {
        "part_number": "MT3608",
        "manufacturer": "Micropower",
        "category": "boost",
        "topology": "boost",
        "is_domestic": False,
        "input_voltage_min_v": 2.0,
        "input_voltage_max_v": 24.0,
        "output_current_max_a": 2.0,
        "temperature_min_c": -40,
        "temperature_max_c": 125,
        "package": "SOP-8",
        "automotive_grade": False,
        "stock": 5000,
        "unit_price_cny": 3.2,
        "lifecycle_status": "active",
        "datasheet_url": "https://www.micropower.com/MT3608",
        "replacement_for": []
    },
    {
        "part_number": "XL6009",
        "manufacturer": "Xlsemi",
        "category": "boost",
        "topology": "boost",
        "is_domestic": False,
        "input_voltage_min_v": 3.0,
        "input_voltage_max_v": 32.0,
        "output_current_max_a": 4.0,
        "temperature_min_c": -40,
        "temperature_max_c": 125,
        "package": "SSOP-16",
        "automotive_grade": False,
        "stock": 2500,
        "unit_price_cny": 8.8,
        "lifecycle_status": "active",
        "datasheet_url": "https://www.xlsemi.com/XL6009",
        "replacement_for": []
    },
    {
        "part_number": "SX1308",
        "manufacturer": "Semtech",
        "category": "boost",
        "topology": "boost",
        "is_domestic": False,
        "input_voltage_min_v": 0.9,
        "input_voltage_max_v": 5.0,
        "output_current_max_a": 1.5,
        "temperature_min_c": -40,
        "temperature_max_c": 125,
        "package": "SOT-23-5",
        "automotive_grade": False,
        "stock": 8000,
        "unit_price_cny": 5.5,
        "lifecycle_status": "active",
        "datasheet_url": "https://www.semtech.com/SX1308",
        "replacement_for": []
    },
    {
        "part_number": "BOOST-国产-001",
        "manufacturer": "南芯科技",
        "category": "boost",
        "topology": "boost",
        "is_domestic": True,
        "input_voltage_min_v": 2.5,
        "input_voltage_max_v": 28.0,
        "output_current_max_a": 3.0,
        "temperature_min_c": -40,
        "temperature_max_c": 125,
        "package": "LQFP-48",
        "automotive_grade": True,
        "stock": 1500,
        "unit_price_cny": 15.8,
        "lifecycle_status": "active",
        "datasheet_url": "https://www.nanxin.com/boost",
        "replacement_for": []
    },
    {
        "part_number": "BOOST-国产-002",
        "manufacturer": "圣邦微电子",
        "category": "boost",
        "topology": "boost",
        "is_domestic": True,
        "input_voltage_min_v": 3.0,
        "input_voltage_max_v": 36.0,
        "output_current_max_a": 2.5,
        "temperature_min_c": -40,
        "temperature_max_c": 125,
        "package": "QFN-32",
        "automotive_grade": True,
        "stock": 2000,
        "unit_price_cny": 14.2,
        "lifecycle_status": "active",
        "datasheet_url": "https://www.shengbang.com/boost",
        "replacement_for": []
    }
]

def main():
    # Load existing parts
    with open(MOCK_PARTS_FILE, 'r', encoding='utf-8') as f:
        parts = json.load(f)

    existing_part_numbers = {p.get('part_number') for p in parts}
    added_count = 0

    for part in BOOST_PARTS:
        part_num = part.get('part_number')
        if part_num not in existing_part_numbers:
            parts.append(part)
            existing_part_numbers.add(part_num)
            added_count += 1
            print(f"Added: {part_num} ({part.get('manufacturer')})")

    # Save
    with open(MOCK_PARTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(parts, f, ensure_ascii=False, indent=2)

    print(f"\nAdded {added_count} Boost parts")
    print(f"Total parts now: {len(parts)}")

if __name__ == "__main__":
    main()
