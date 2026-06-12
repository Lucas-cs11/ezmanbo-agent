"""
example_hybrid_search.py - Example: Using hybrid retrieval in agent workflow

This example demonstrates how to integrate hybrid retrieval into the
SearchNode of the LangGraph-based agent.
"""

import json
from pathlib import Path
from app.requirement_parser import parse_requirement
from app.ezplm_client import search_parts
from app.schemas import RequirementConstraints


def example_1_pure_filtering():
    """Example 1: Traditional search with pure filtering (baseline)."""
    print("=" * 70)
    print("Example 1: Traditional Search (Pure Filtering)")
    print("=" * 70)

    query = "12V转5V 3A Buck 降压芯片"
    print(f"\nQuery: {query}\n")

    # Parse user requirement
    constraints = parse_requirement(query)
    print(f"Parsed constraints:")
    print(f"  Category: {constraints.category}")
    print(f"  Topology: {constraints.topology}")
    print(f"  Input Voltage: {constraints.input_voltage_nominal_v}V")
    print(f"  Output Voltage: {constraints.output_voltage_v}V")
    print(f"  Output Current: {constraints.output_current_a}A")

    # Search without hybrid retrieval
    candidates = search_parts(constraints, use_hybrid_retrieval=False)

    print(f"\nResults: {len(candidates)} candidates found")
    for i, part in enumerate(candidates[:3], 1):
        print(f"\n  {i}. {part.part_number}")
        print(f"     Manufacturer: {part.manufacturer}")
        print(f"     Topology: {part.topology}")
        print(f"     Vin: {part.input_voltage_min_v}-{part.input_voltage_max_v}V")
        print(f"     Vout: {part.output_voltage_v}V")
        print(f"     Iout: {part.output_current_max_a}A")


def example_2_hybrid_search():
    """Example 2: Search with hybrid retrieval (new feature)."""
    print("\n" + "=" * 70)
    print("Example 2: Hybrid Search (BM25 + Vector)")
    print("=" * 70)

    query = "12V转5V 3A Buck 降压芯片"
    print(f"\nQuery: {query}\n")

    # Parse user requirement
    constraints = parse_requirement(query)

    # Search WITH hybrid retrieval
    candidates = search_parts(constraints, use_hybrid_retrieval=True)

    print(f"Results: {len(candidates)} candidates found")
    for i, part in enumerate(candidates[:3], 1):
        print(f"\n  {i}. {part.part_number}")
        print(f"     Manufacturer: {part.manufacturer}")
        print(f"     Topology: {part.topology}")
        print(f"     Vin: {part.input_voltage_min_v}-{part.input_voltage_max_v}V")
        print(f"     Vout: {part.output_voltage_v}V")
        print(f"     Iout: {part.output_current_max_a}A")


def example_3_mpn_exact_match():
    """Example 3: Exact MPN matching (hybrid retrieval advantage)."""
    print("\n" + "=" * 70)
    print("Example 3: Exact MPN Matching")
    print("=" * 70)

    # Query with specific MPN
    query = "SY8240 Silergy"
    print(f"\nQuery: {query}\n")

    constraints = parse_requirement(query)
    print(f"Parsed constraints:")
    print(f"  Raw input: {constraints.raw_input}")
    print(f"  Category: {constraints.category}")

    # Pure filtering (may miss exact matches)
    pure_results = search_parts(constraints, use_hybrid_retrieval=False)
    print(f"\nPure filtering: {len(pure_results)} results")

    # Hybrid (should prioritize exact MPN match)
    hybrid_results = search_parts(constraints, use_hybrid_retrieval=True)
    print(f"Hybrid retrieval: {len(hybrid_results)} results")

    if hybrid_results:
        print(f"\nTop match (hybrid):")
        top = hybrid_results[0]
        print(f"  {top.part_number} ({top.manufacturer})")
        if "SY8240" in top.part_number or top.manufacturer == "Silergy":
            print(f"  ✓ Correctly prioritized exact match")


def example_4_mixed_query():
    """Example 4: Mixed functional + parameter query."""
    print("\n" + "=" * 70)
    print("Example 4: Mixed Functional Query")
    print("=" * 70)

    query = "高效率小封装低噪声LDO 3.3V 1A"
    print(f"\nQuery: {query}\n")

    constraints = parse_requirement(query)
    print(f"Parsed constraints:")
    print(f"  Category: {constraints.category}")
    print(f"  Topology: {constraints.topology}")
    print(f"  Output Voltage: {constraints.output_voltage_v}V")
    print(f"  Output Current: {constraints.output_current_a}A")

    # Hybrid retrieval should handle semantic "高效率" and "小封装"
    candidates = search_parts(constraints, use_hybrid_retrieval=True)

    print(f"\nResults: {len(candidates)} candidates")
    if candidates:
        for i, part in enumerate(candidates[:2], 1):
            print(f"\n  {i}. {part.part_number}")
            print(f"     Manufacturer: {part.manufacturer}")
            print(f"     Package: {part.package}")


def example_5_compare_results():
    """Example 5: Side-by-side comparison of pure vs hybrid."""
    print("\n" + "=" * 70)
    print("Example 5: Pure vs Hybrid Comparison")
    print("=" * 70)

    queries = [
        ("型号精确查询", "LM2596 降压"),
        ("功能语义查询", "高效率 小封装 LDO"),
        ("混合查询", "12V转3.3V 1A LDO 低压差"),
    ]

    for query_type, query in queries:
        print(f"\n{query_type}: '{query}'")
        constraints = parse_requirement(query)

        pure = search_parts(constraints, use_hybrid_retrieval=False)
        hybrid = search_parts(constraints, use_hybrid_retrieval=True)

        print(f"  Pure filtering: {len(pure)} results")
        print(f"  Hybrid retrieval: {len(hybrid)} results")

        if pure and hybrid:
            # Check if top results differ
            pure_top = pure[0].part_number
            hybrid_top = hybrid[0].part_number
            if pure_top != hybrid_top:
                print(f"  ✓ Different ranking: pure={pure_top}, hybrid={hybrid_top}")
            else:
                print(f"  ✓ Same top result: {pure_top}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("B3 Hybrid Retrieval Integration Examples")
    print("=" * 70)

    try:
        example_1_pure_filtering()
    except Exception as e:
        print(f"Example 1 error: {e}")

    try:
        example_2_hybrid_search()
    except Exception as e:
        print(f"Example 2 error: {e}")

    try:
        example_3_mpn_exact_match()
    except Exception as e:
        print(f"Example 3 error: {e}")

    try:
        example_4_mixed_query()
    except Exception as e:
        print(f"Example 4 error: {e}")

    try:
        example_5_compare_results()
    except Exception as e:
        print(f"Example 5 error: {e}")

    print("\n" + "=" * 70)
    print("Examples completed")
    print("=" * 70 + "\n")
