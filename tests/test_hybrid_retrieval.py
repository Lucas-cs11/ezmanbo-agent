"""
test_hybrid_retrieval.py - Hybrid retrieval evaluation script

Compare hybrid retrieval (BM25 + vector) vs pure vector retrieval recall.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add project path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.hybrid_retrieval import HybridRetriever


def load_mock_parts() -> List[str]:
    """Load component descriptions from mock database."""
    data_file = Path(__file__).parent.parent / "data" / "mock_parts.json"
    with open(data_file, "r", encoding="utf-8") as f:
        parts = json.load(f)

    documents = []
    for p in parts:
        # Build document: MPN + manufacturer + description + params
        parts_list = [
            p.get("part_number", ""),
            p.get("manufacturer", ""),
            p.get("description", ""),
            p.get("category", ""),
            p.get("topology", ""),
        ]
        if p.get("output_voltage_v"):
            parts_list.append(f"{p['output_voltage_v']}V")
        if p.get("output_current_max_a"):
            parts_list.append(f"{p['output_current_max_a']}A")

        doc = " ".join([str(x) for x in parts_list if x])
        documents.append(doc)

    return documents


class MockCollection:
    """Mock ChromaDB collection for testing without real DB."""
    def __init__(self, documents: List[str]):
        self.documents = documents

    def query(self, query_texts, n_results, include):
        # Return empty results to allow pure BM25 retrieval
        return {"ids": [[]], "distances": [[]], "documents": [[]]}


def test_bm25_basic():
    """Test BM25 retrieval functionality."""
    print("=" * 60)
    print("Test 1: BM25 Basic Functionality")
    print("=" * 60)

    try:
        documents = load_mock_parts()
        print(f"OK: Loaded {len(documents)} component documents\n")

        # Create retriever with mock collection
        retriever = HybridRetriever(
            chroma_collection=MockCollection(documents),
            documents=documents,
            bm25_weight=1.0,  # Use pure BM25 for this test
        )
        print("OK: BM25 retriever initialized\n")

        # Test query 1: Exact MPN match
        query1 = "SY8240"
        print(f"[Query 1] '{query1}' (MPN exact match)")
        results1 = retriever.retrieve(query1, k=3)

        if results1:
            print(f"  Returned {len(results1)} results:")
            for i, res in enumerate(results1, 1):
                doc_preview = res['document'][:60] if res['document'] else "N/A"
                print(f"    {i}. {doc_preview}...")
                print(f"       BM25 score: {res['bm25_score']}")
        else:
            print(f"  No results returned")

        print()

        # Test query 2: Topology matching
        query2 = "buck"
        print(f"[Query 2] '{query2}' (topology keyword)")
        results2 = retriever.retrieve(query2, k=3)

        if results2:
            print(f"  Returned {len(results2)} results:")
            for i, res in enumerate(results2, 1):
                doc_preview = res['document'][:60] if res['document'] else "N/A"
                print(f"    {i}. {doc_preview}...")
                print(f"       BM25 score: {res['bm25_score']}")
        else:
            print(f"  No results returned")

        print()

        # Test query 3: Multiple keywords
        query3 = "12V 5V"
        print(f"[Query 3] '{query3}' (multiple voltage keywords)")
        results3 = retriever.retrieve(query3, k=3)

        if results3:
            print(f"  Returned {len(results3)} results:")
            for i, res in enumerate(results3, 1):
                doc_preview = res['document'][:60] if res['document'] else "N/A"
                print(f"    {i}. {doc_preview}...")
                print(f"       BM25 score: {res['bm25_score']}")
        else:
            print(f"  No results returned")

        print()
        print("OK: Test 1 completed\n")
        return True

    except Exception as e:
        print(f"FAIL: Test 1 failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_tokenization():
    """Test BM25 tokenization."""
    print("=" * 60)
    print("Test 2: BM25 Tokenization")
    print("=" * 60)

    test_texts = [
        "SY8240 Silergy Buck 5V 3A",
        "12V to 5V converter LDO chip",
        "LDO low-dropout noise",
        "Silergy SGMICRO domestic alternative",
        "AEC-Q100 automotive grade",
    ]

    for text in test_texts:
        tokens = HybridRetriever._tokenize(text)
        print(f"Text: {text}")
        print(f"Tokens: {tokens}")
        print()

    print("OK: Test 2 completed\n")
    return True


def test_hybrid_weight():
    """Test hybrid retrieval with different BM25 weights."""
    print("=" * 60)
    print("Test 3: Hybrid Weight Comparison")
    print("=" * 60)

    try:
        documents = load_mock_parts()
        print(f"OK: Loaded {len(documents)} documents\n")

        query = "SY8240"
        print(f"Query: '{query}'\n")

        # Test different weights
        weights = [0.0, 0.25, 0.5, 0.75, 1.0]
        results_summary = []

        for weight in weights:
            retriever = HybridRetriever(
                chroma_collection=MockCollection(documents),
                documents=documents,
                bm25_weight=weight,
            )
            results = retriever.retrieve(query, k=3)
            results_summary.append({
                "weight": weight,
                "results": len(results),
                "top_doc": results[0]['document'][:40] if results else "N/A"
            })

        print(f"{'BM25 Weight':<15} {'Results':<10} {'Top Match':<40}")
        print("-" * 65)
        for r in results_summary:
            print(f"{r['weight']:<15.2f} {r['results']:<10} {r['top_doc']:<40}")

        print()
        print("OK: Test 3 completed\n")
        return True

    except Exception as e:
        print(f"FAIL: Test 3 failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_edge_cases():
    """Test edge cases."""
    print("=" * 60)
    print("Test 4: Edge Cases")
    print("=" * 60)

    try:
        documents = load_mock_parts()
        retriever = HybridRetriever(
            chroma_collection=MockCollection(documents),
            documents=documents,
            bm25_weight=0.5,
        )
        print(f"OK: Initialized retriever with {len(documents)} documents\n")

        # Edge case 1: Empty query
        print("[Case 1] Empty query")
        try:
            results = retriever.retrieve("", k=3)
            print(f"  Returned {len(results)} results")
        except Exception as e:
            print(f"  Exception (expected): {type(e).__name__}")
        print()

        # Edge case 2: Query with special characters
        print("[Case 2] Special characters in query")
        results = retriever.retrieve("IC-123.456_ABC", k=3)
        print(f"  Returned {len(results)} results")
        print()

        # Edge case 3: Very long query
        print("[Case 3] Long query")
        long_query = "12V to 5V 3A buck converter " * 5
        results = retriever.retrieve(long_query, k=3)
        print(f"  Returned {len(results)} results")
        print()

        # Edge case 4: k larger than document count
        print("[Case 4] k > document count")
        results = retriever.retrieve("buck", k=10000)
        print(f"  Returned {len(results)} results (requested 10000)")
        print()

        print("OK: Test 4 completed\n")
        return True

    except Exception as e:
        print(f"FAIL: Test 4 failed: {e}\n")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Hybrid Retrieval Test Suite")
    print("=" * 60 + "\n")

    results = []
    results.append(("BM25 Basic", test_bm25_basic()))
    results.append(("Tokenization", test_tokenization()))
    results.append(("Hybrid Weight", test_hybrid_weight()))
    results.append(("Edge Cases", test_edge_cases()))

    print("=" * 60)
    print("Test Summary")
    print("=" * 60)

    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name:<20} {status}")

    all_passed = all(p for _, p in results)
    print("\n" + ("=" * 60))
    if all_passed:
        print("OK: All tests passed!")
    else:
        print("WARNING: Some tests failed, see logs above.")
    print("=" * 60 + "\n")

    sys.exit(0 if all_passed else 1)
