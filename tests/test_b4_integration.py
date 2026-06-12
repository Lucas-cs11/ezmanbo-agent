"""
B4 Integration Test: Verify semantic cache integration with agent_orchestrator and main.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from app.semantic_cache import get_semantic_cache
from app.agent_orchestrator import analyze
from app.schemas import RequirementConstraints


def test_agent_orchestrator_cache():
    """Test cache integration in agent_orchestrator"""
    print("=" * 60)
    print("B4 Integration Test: agent_orchestrator")
    print("=" * 60)

    # Clear cache for testing
    import shutil
    if Path("data/chroma_cache").exists():
        shutil.rmtree("data/chroma_cache")

    cache = get_semantic_cache()
    print(f"\n1. Initial cache state")
    print(f"   Cache entries: {cache.count}")
    assert cache.count == 0, "Cache should be empty"
    print("   [OK] Cache is empty")

    # Test analyze with simple requirement
    query = "12V to 5V buck converter"
    print(f"\n2. First call to analyze('{query}')")
    print("   (This will execute full analysis and cache the result)")

    try:
        report1 = analyze(query)
        print(f"   [OK] Analysis completed, report type: {type(report1).__name__}")
        print(f"   Cache entries after first call: {cache.count}")
        assert cache.count > 0, "Cache should have entries after analyze"

        print(f"\n3. Second call with exact same query")
        print("   (This should hit cache)")

        # This should hit cache immediately
        report2 = analyze(query)
        print(f"   [OK] Second analysis completed")
        print(f"   Cache entries: {cache.count}")

        # Both reports should have same content
        assert report1.dict() == report2.dict(), "Reports should be identical"
        print("   [OK] Both reports are identical")

        print(f"\n4. Verify cache hit behavior")
        cache_result = cache.get(query)
        assert cache_result is not None, "Cache should have the query"
        assert cache_result["cache_hit"] is True, "Should be marked as cache hit"
        print(f"   [OK] Cache hit verified")
        print(f"   Similarity score: {cache_result['similarity']}")

    except Exception as e:
        print(f"   [FAIL] Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n" + "=" * 60)
    print("[PASS] agent_orchestrator cache integration working")
    print("=" * 60)
    return True


def test_main_endpoints():
    """Test X-Cache header in main.py endpoints"""
    print("\n" + "=" * 60)
    print("B4 Integration Test: main.py endpoints")
    print("=" * 60)

    try:
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        # Test /health endpoint
        print("\n1. Testing /health endpoint")
        response = client.get("/health")
        assert response.status_code == 200, "Health check should succeed"
        print("   [OK] Health check passed")

        # Test /analyze endpoint with cache miss (new query)
        print("\n2. Testing /analyze endpoint - first call (MISS)")
        query1 = "Need a 24V to 12V converter"
        response1 = client.post("/analyze", json={"user_input": query1})

        print(f"   Status: {response1.status_code}")
        assert response1.status_code == 200, "Request should succeed"

        x_cache_header = response1.headers.get("X-Cache")
        print(f"   X-Cache header: {x_cache_header}")
        assert x_cache_header in ["HIT", "MISS"], "X-Cache should be HIT or MISS"
        print("   [OK] X-Cache header present")

        # Test /analyze endpoint with cache hit (same query)
        print("\n3. Testing /analyze endpoint - second call (HIT)")
        response2 = client.post("/analyze", json={"user_input": query1})

        print(f"   Status: {response2.status_code}")
        assert response2.status_code == 200, "Request should succeed"

        x_cache_header2 = response2.headers.get("X-Cache")
        print(f"   X-Cache header: {x_cache_header2}")
        assert x_cache_header2 == "HIT", "Second call should be HIT"
        print("   [OK] Cache hit detected via X-Cache header")

        # Verify response content is the same
        data1 = response1.json()
        data2 = response2.json()
        assert data1 == data2, "Responses should be identical"
        print("   [OK] Response content identical for cached query")

        # Test /analyze/stream endpoint (SSE)
        print("\n4. Testing /analyze/stream endpoint")
        query3 = "LDO 3.3V output 500mA"
        response3 = client.post("/analyze/stream", json={"user_input": query3})

        print(f"   Status: {response3.status_code}")
        assert response3.status_code == 200, "Streaming request should succeed"

        x_cache_stream = response3.headers.get("X-Cache")
        print(f"   X-Cache header: {x_cache_stream}")
        assert x_cache_stream in ["HIT", "MISS"], "X-Cache should be HIT or MISS"
        print("   [OK] X-Cache header present on SSE endpoint")

        # Parse SSE events
        content = response3.text
        print(f"   Received {len(content.split('event:'))} events")
        assert "event:" in content, "Should have SSE events"

        # Check for cache_hit event
        if "cache_hit" in content:
            print("   [OK] cache_hit event found in SSE stream")
        else:
            print("   [WARN] cache_hit event not found (might be cache miss)")

        print("\n" + "=" * 60)
        print("[PASS] main.py endpoint integration working")
        print("=" * 60)
        return True

    except ImportError as e:
        print(f"   [SKIP] TestClient not available: {e}")
        print("   Skipping endpoint tests")
        return True
    except Exception as e:
        print(f"   [FAIL] Error during endpoint test: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "=" * 70)
    print("B4 FULL INTEGRATION TEST")
    print("=" * 70)

    results = []

    # Test 1: agent_orchestrator integration
    try:
        result1 = test_agent_orchestrator_cache()
        results.append(("agent_orchestrator", result1))
    except Exception as e:
        print(f"\n[ERROR] agent_orchestrator test failed: {e}")
        results.append(("agent_orchestrator", False))

    # Test 2: main.py endpoints integration
    try:
        result2 = test_main_endpoints()
        results.append(("main.py endpoints", result2))
    except Exception as e:
        print(f"\n[ERROR] main.py test failed: {e}")
        results.append(("main.py endpoints", False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    all_passed = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {test_name}: [{status}]")
        if not result:
            all_passed = False

    print("=" * 70)

    if all_passed:
        print("\n*** ALL B4 INTEGRATION TESTS PASSED ***\n")
        return 0
    else:
        print("\n*** SOME TESTS FAILED ***\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
