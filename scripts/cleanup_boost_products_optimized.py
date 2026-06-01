#!/usr/bin/env python3
"""Clean up Boost products - keep only those with verified manufacturer datasheets
Optimized version: only add datasheet fields to products that have them
"""

import json
from pathlib import Path

# Define which Boost products have verified datasheets
VERIFIED_BOOST_PRODUCTS = {
    'TPS61030DSG',  # Texas Instruments - official datasheet verified
}

# Products to remove (no manufacturer datasheet available)
PRODUCTS_TO_REMOVE = {
    'MT3608',           # Micropower - no verified source
    'XL6009',           # Xlsemi - no datasheet found
    'SX1308',           # Semtech - no datasheet found
    'BOOST-国产-001',   # Nanxin - no datasheet source
    'BOOST-国产-002',   # Shengbang - no datasheet source
}

def main():
    project_root = Path(__file__).parent.parent
    mock_parts_file = project_root / "data" / "mock_parts.json"

    # Load current parts
    with open(mock_parts_file, 'r', encoding='utf-8') as f:
        parts = json.load(f)

    print("=" * 70)
    print("Boost Product Quality Control - Optimized (Only tag parts with datasheets)")
    print("=" * 70)
    print()

    # Identify parts to keep and remove
    boost_parts_before = [p for p in parts if p.get('topology') == 'boost']
    print(f"Before: {len(boost_parts_before)} Boost products")
    for p in boost_parts_before:
        print(f"  - {p.get('part_number'):25s} ({p.get('manufacturer')})")
    print()

    # Remove products without verified datasheets
    filtered_parts = []
    removed_count = 0

    for part in parts:
        part_number = part.get('part_number')

        if part_number in PRODUCTS_TO_REMOVE:
            print(f"[REMOVE] {part_number:25s} - No verified datasheet")
            removed_count += 1
        else:
            # Only add datasheet fields to products that have them
            if part_number in VERIFIED_BOOST_PRODUCTS:
                part['has_datasheet'] = True
                part['datasheet_local_path'] = f"docs/datasheets/{part['part_number']}.pdf"
                part['datasheet_verification'] = 'Verified - Official datasheet'
            # For products without datasheets, don't add the field at all
            # This is more efficient than adding 'has_datasheet': false to every part

            filtered_parts.append(part)

    print()
    print("=" * 70)

    # Calculate statistics
    boost_parts_after = [p for p in filtered_parts if p.get('topology') == 'boost']
    print(f"\nAfter: {len(boost_parts_after)} Boost products (verified with datasheets)")
    for p in boost_parts_after:
        print(f"  + {p.get('part_number'):25s} ({p.get('manufacturer')})")

    # Save filtered parts
    with open(mock_parts_file, 'w', encoding='utf-8') as f:
        json.dump(filtered_parts, f, ensure_ascii=False, indent=2)

    print()
    print(f"Total parts: {len(parts)} -> {len(filtered_parts)} (removed {removed_count})")

    # Count parts with datasheet field
    parts_with_ds = len([p for p in filtered_parts if 'has_datasheet' in p])
    print(f"Parts with datasheet field: {parts_with_ds} / {len(filtered_parts)}")
    print()
    print("Cleaned data saved to data/mock_parts.json (optimized)")

if __name__ == '__main__':
    main()
