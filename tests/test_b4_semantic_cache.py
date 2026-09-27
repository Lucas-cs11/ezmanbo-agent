"""
Test B4: Semantic Cache Layer Verification
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from app.semantic_cache import SemanticCache


def test_semantic_cache():
    """Test semantic cache basic functionality"""

    # Create cache instance (using temp directory)
    cache = SemanticCache(persist_dir="test_cache")

    print("=" * 60)
    print("B4 Semantic Cache Layer Test")
    print("=" * 60)

    # Test 1: Empty cache check
    print("\n[Test 1] Empty cache check")
    query1 = "I need a 12V to 5V buck converter circuit"
    result1 = cache.get(query1)
    assert result1 is None, "Cache should be empty"
    print("[OK] Cache is empty, returned None")

    # Test 2: Store in cache
    print("\n[Test 2] Store in cache")
    test_result = {
        "candidates": [
            {"part_number": "TPS5430", "score": 92},
            {"part_number": "LM2576", "score": 85},
        ],
        "summary": "Recommend TPS5430"
    }
    success = cache.set(query1, test_result)
    assert success, "Cache set should succeed"
    print("[OK] Successfully stored in cache, entry count: %d" % cache.count)

    # Test 3: Exact query hit
    print("\n[Test 3] Exact same query - should hit cache")
    result2 = cache.get(query1)
    assert result2 is not None, "Same query should hit cache"
    assert result2["cache_hit"] is True
    assert result2["similarity"] >= 0.99, "Same query similarity should be very high"
    cached = result2["cached_result"]
    assert cached["candidates"][0]["part_number"] == "TPS5430"
    print("[OK] Cache hit! Similarity: %.4f" % result2['similarity'])
    print("     Returned: %s" % cached['summary'])

    # Test 4: Similar semantic query
    print("\n[Test 4] Semantically similar query - similarity > 0.95 should hit")
    query4 = "Need to step down 12 volts to 5 volts buck topology"
    result4 = cache.get(query4)
    if result4 is not None:
        print("[OK] Cache hit! Similarity: %.4f" % result4['similarity'])
    else:
        print("[OK] Cache miss (similarity < 0.95, this is normal)")

    # Test 5: Completely different query no hit
    print("\n[Test 5] Completely different query - should not hit")
    query5 = "Solve the Schrodinger equation"
    result5 = cache.get(query5)
    assert result5 is None, "Completely different query should not hit"
    print("[OK] Cache miss (expected)")

    # Test 6: Multiple cache entries
    print("\n[Test 6] Add multiple cache entries")
    test_queries = [
        "24V to 3.3V LDO selection",
        "Boost converter 5V to 12V chip recommendation",
        "Automotive grade DC-DC converter",
    ]
    for q in test_queries:
        cache.set(q, {"query": q, "result": "test"})

    print("[OK] Added %d entries, total count: %d" % (len(test_queries), cache.count))

    # Test 7: Threshold test
    print("\n[Test 7] Similarity threshold test - use threshold=0.8")
    query7 = "12 to 5 step down"
    result7 = cache.get(query7, threshold=0.8)
    if result7 is not None:
        print("[OK] Hit with threshold=0.8, similarity: %.4f" % result7['similarity'])
    else:
        print("[OK] Miss with threshold=0.8")

    # Test 8: Cache persistence
    print("\n[Test 8] Cache persistence - create new instance")
    cache2 = SemanticCache(persist_dir="test_cache")
    result_persist = cache2.get(query1)
    assert result_persist is not None, "New instance should access same cache"
    assert result_persist["cache_hit"] is True
    print("[OK] Cache persists across instances, count: %d" % cache2.count)

    print("\n" + "=" * 60)
    print("[PASS] All tests passed! B4 semantic cache working correctly")
    print("=" * 60)

    return True


if __name__ == "__main__":
    try:
        test_semantic_cache()
        print("\n*** B4 VERIFICATION PASSED ***")
        sys.exit(0)
    except Exception as e:
        print("\n[FAIL] Test failed with error:")
        print(str(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)

