#!/usr/bin/env python3
"""
Test script for B2: schemdraw 参数化电路图生成

Tests:
- Buck converter: 12V -> 5V @ 3A
- Boost converter: 5V -> 12V @ 2A
- LDO regulator: 12V -> 3.3V @ 1A
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.schematic_generator import generate_schematic


def test_topologies():
    """Test all three topology implementations."""
    test_cases = [
        ('buck', 12, 5, 3, 'Buck 12V->5V @ 3A'),
        ('boost', 5, 12, 2, 'Boost 5V->12V @ 2A'),
        ('ldo', 12, 3.3, 1, 'LDO 12V->3.3V @ 1A'),
    ]

    print("Testing schematic generation for all topologies:")
    print("-" * 60)

    for topology, vin, vout, iout, desc in test_cases:
        try:
            svg = generate_schematic(topology, vin, vout, iout)

            # Verify SVG output
            assert isinstance(svg, str), f"Expected string, got {type(svg)}"
            assert '<svg' in svg, "SVG tag missing"
            assert len(svg) > 1000, f"SVG too small: {len(svg)} chars"

            # Check for calculated component values in labels
            if topology == 'buck':
                assert 'uH' in svg, "Inductance not in SVG"
                assert 'uF' in svg, "Capacitance not in SVG"

            print(f"[PASS] {desc:30s} | {len(svg):6d} bytes")

        except Exception as e:
            print(f"[FAIL] {desc:30s} | {str(e)}")
            raise

    print("-" * 60)
    print(f"\nAll {len(test_cases)} tests passed!")


def test_error_handling():
    """Test error handling for invalid topologies."""
    print("\nTesting error handling:")
    print("-" * 60)

    try:
        generate_schematic('invalid', 12, 5, 3)
        print("[FAIL] Should have raised ValueError for invalid topology")
    except ValueError as e:
        print(f"[PASS] Correctly raised ValueError: {str(e)}")

    print("-" * 60)


if __name__ == '__main__':
    test_topologies()
    test_error_handling()
    print("\nAll B2 tests passed!")
