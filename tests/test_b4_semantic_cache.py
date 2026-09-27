"""
Test B4: Semantic Cache Layer Verification
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import tempfile
from app.semantic_cache import SemanticCache


def test_semantic_cache():
    """Test semantic cache basic functionality"""

    # 用临时目录，且同一用例内两个实例共用它（测持久化）。
    # 曾经写的是相对路径 "test_cache"——既会污染仓库目录，又因为不清理而
    # 让这个用例在非首次运行时必然失败（缓存里已有条目）。
    cache_dir = tempfile.mkdtemp(prefix="b4-semantic-cache-")
    cache = SemanticCache(persist_dir=cache_dir)

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
    # 刻意**不**断言「一定命中/一定不命中」——那取决于嵌入模型的相似度分布，
    # 换模型版本就会变，写死了只是个脆弱断言。但返回值的**契约**必须成立：
    # 要么 None，要么是结构完整、自洽的命中结果。（原先这里两个分支都只有 print，
    # 没有任何断言 —— 正是本模块要根除的假绿写法。）
    print("\n[Test 4] Semantically similar query")
    query4 = "Need to step down 12 volts to 5 volts buck topology"
    result4 = cache.get(query4)
    if result4 is None:
        print("[OK] Cache miss（相似度未过默认阈值，属正常范围）")
    else:
        assert result4["cache_hit"] is True, "非 None 的结果必须是命中"
        assert 0.0 <= result4["similarity"] <= 1.0, (
            f"相似度必须落在 [0,1]，实际 {result4['similarity']}"
        )
        assert "cached_result" in result4, "命中结果必须带回原始缓存内容"
        print("[OK] Cache hit, similarity: %.4f" % result4['similarity'])

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
    # 同理不断言命中与否（阈值边界本身就是模型相关的），但**若返回了结果，
    # 它的相似度必须真的过了阈值、且内容必须是当初存进去的那一份** ——
    # 这是「阈值生效」与「不会串条目」两个真正的正确性属性。
    print("\n[Test 7] Similarity threshold test - use threshold=0.8")
    query7 = "12 to 5 step down"
    result7 = cache.get(query7, threshold=0.8)
    if result7 is None:
        print("[OK] Miss with threshold=0.8")
    else:
        assert result7["similarity"] >= 0.8, (
            f"低于阈值的结果不该被返回：similarity={result7['similarity']} < 0.8"
        )
        assert result7["cached_result"] == test_result, (
            "命中的内容不是 query1 当初存进去的那一份，缓存串了条目"
        )
        print("[OK] Hit with threshold=0.8, similarity: %.4f" % result7['similarity'])

    # Test 8: Cache persistence
    print("\n[Test 8] Cache persistence - create new instance")
    cache2 = SemanticCache(persist_dir=cache_dir)
    result_persist = cache2.get(query1)
    assert result_persist is not None, "New instance should access same cache"
    assert result_persist["cache_hit"] is True
    print("[OK] Cache persists across instances, count: %d" % cache2.count)

    print("\n" + "=" * 60)
    print("[PASS] All assertions passed — B4 semantic cache working correctly")
    print("=" * 60)
    # 这里原先有一句 `return True`。pytest **不检查返回值**，所以它既不会让用例更严格，
    # 也不会在失败时起作用——纯属假绿时代的残留写法，已删除。真正的判定全部由上面的
    # assert 承担。


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

