"""混合检索（BM25 + 向量）的隔离逻辑测试。

这个文件原先 4 个 `test_*` 全是「假绿」：函数 `return True/False` 而**一个 assert
都没有**，pytest 不检查返回值，所以无论成败都算通过。现在全部换成真实断言。

用 MockCollection 顶掉 ChromaDB（返回空向量结果，走纯 BM25 路径），因此完全隔离、
不外呼，留在默认集。

⚠️ 已知缺陷（见文件末尾的 xfail 用例）：`HybridRetriever.retrieve()` 的排序目前
**按文档原序**输出，BM25 相关性没有参与排序。BM25 打分本身是对的，融合那一层有问题。
"""

from typing import List

import pytest

from app.hybrid_retrieval import HybridRetriever

# ── 内联样本数据（用于测试 BM25/Hybrid 逻辑，不依赖外部文件）────────────
_SAMPLE_DOCUMENTS: List[str] = [
    "TPS54360 Texas Instruments buck 36V 3.5A",
    "TPS62130 Texas Instruments buck 17V 3A 5V",
    "LM2596 Texas Instruments buck 40V 3A",
    "TPS7A4501 Texas Instruments ldo 30V 1A",
    "TLV75801 Texas Instruments ldo 5.5V 1A",
    "LTC3633 Analog Devices buck 15V 8A",
    "LT1763 Analog Devices ldo 20V 1.5A",
    "ADP2384 Analog Devices buck 20V 4A 5V",
    "MCP16301 Microchip buck 32V 1.2A",
    "MCP1703 Microchip ldo 16V 0.25A 3.3V",
    "ST1S10 STMicroelectronics buck 18V 3A",
    "LD1117 STMicroelectronics ldo 15V 0.8A 5V",
    "SY8240 Silergy buck 20V 5V 3A domestic",
    "SGM2576 SGMICRO buck 40V 3A automotive AEC-Q100",
]

_RESULT_KEYS = {"doc_idx", "document", "bm25_score", "vector_score", "hybrid_score"}


class MockCollection:
    """Mock ChromaDB collection for testing without real DB."""

    def __init__(self, documents: List[str]):
        self.documents = documents

    def query(self, query_texts, n_results, include):
        # Return empty results to allow pure BM25 retrieval
        return {"ids": [[]], "distances": [[]], "documents": [[]]}


def load_sample_documents() -> List[str]:
    """返回内联样本文档列表（供 HybridRetriever 逻辑测试用）。"""
    return list(_SAMPLE_DOCUMENTS)


def _make_retriever(bm25_weight: float = 1.0) -> HybridRetriever:
    documents = load_sample_documents()
    return HybridRetriever(
        chroma_collection=MockCollection(documents),
        documents=documents,
        bm25_weight=bm25_weight,
    )


def _assert_well_formed(results, k: int, corpus: List[str]):
    """每一条结果的公共约束。"""
    assert isinstance(results, list)
    assert len(results) == k, f"期望 {k} 条结果，实际 {len(results)}"

    for res in results:
        assert _RESULT_KEYS <= set(res), f"结果缺少字段：{_RESULT_KEYS - set(res)}"
        assert isinstance(res["document"], str) and res["document"], "document 不能为空"
        assert res["document"] in corpus, f"返回了语料之外的文档：{res['document']!r}"
        assert 0.0 <= res["bm25_score"] <= 1.0, f"bm25_score 越界：{res['bm25_score']}"
        assert 0.0 <= res["vector_score"] <= 1.0, f"vector_score 越界：{res['vector_score']}"
        assert 0.0 <= res["hybrid_score"] <= 1.0, f"hybrid_score 越界：{res['hybrid_score']}"
        assert 0 <= res["doc_idx"] < len(corpus)

    scores = [res["hybrid_score"] for res in results]
    assert scores == sorted(scores, reverse=True), f"结果没有按 hybrid_score 降序：{scores}"


def test_bm25_basic():
    """BM25 检索：结果结构、取值范围，以及打分本身确实反映了相关性。"""
    documents = load_sample_documents()
    retriever = _make_retriever(bm25_weight=1.0)

    # ── 查询 1：精确 MPN ──
    results1 = retriever.retrieve("SY8240", k=3)
    _assert_well_formed(results1, 3, documents)

    # ── 查询 2：拓扑关键词 ──
    results2 = retriever.retrieve("buck", k=3)
    _assert_well_formed(results2, 3, documents)
    assert any("buck" in res["document"].lower() for res in results2), (
        "查询 'buck' 的前 3 条里一条 buck 文档都没有"
    )

    # ── 查询 3：多关键词 ──
    results3 = retriever.retrieve("12V 5V", k=3)
    _assert_well_formed(results3, 3, documents)

    # ── BM25 打分本身是对的：拿全量结果，精确匹配的那条应当是最高分 ──
    all_results = retriever.retrieve("SY8240", k=len(documents))
    _assert_well_formed(all_results, len(documents), documents)

    hit_docs = [res["document"] for res in all_results if "SY8240" in res["document"]]
    assert len(hit_docs) == 1, "语料里应当恰好有一条 SY8240 文档"

    best = max(all_results, key=lambda res: res["bm25_score"])
    assert best["document"] == hit_docs[0], (
        f"BM25 打分没有把精确匹配的文档排到最高分，最高分给了：{best['document']!r}"
    )
    assert best["bm25_score"] == 1.0, "归一化后精确匹配的 BM25 分数应为 1.0"


def test_tokenization():
    """分词：小写化、按标点切分、中文保留成词。"""
    assert HybridRetriever._tokenize("SY8240 Silergy Buck 5V 3A") == [
        "sy8240", "silergy", "buck", "5v", "3a"
    ]

    assert HybridRetriever._tokenize("12V to 5V converter LDO chip") == [
        "12v", "to", "5v", "converter", "ldo", "chip"
    ]

    # 连字符 / 点号是分隔符
    assert HybridRetriever._tokenize("IC-123.456_ABC") == ["ic", "123", "456_abc"]
    assert HybridRetriever._tokenize("AEC-Q100 automotive grade") == [
        "aec", "q100", "automotive", "grade"
    ]

    # 中文按空格成词，不被拆散
    assert HybridRetriever._tokenize("车规 降压 芯片") == ["车规", "降压", "芯片"]

    # 空输入 / 纯标点 → 空 token 列表
    for empty in ("", "   ", "!@#$%"):
        assert HybridRetriever._tokenize(empty) == []

    # 所有 token 都是小写且非空
    tokens = HybridRetriever._tokenize("TPS54360 Texas Instruments buck")
    assert tokens == [t.lower() for t in tokens]
    assert all(tokens)


def test_hybrid_weight():
    """不同 BM25 权重下都必须返回结构良好的 TOP-k。"""
    documents = load_sample_documents()
    query = "SY8240"

    summary = []
    for weight in (0.0, 0.25, 0.5, 0.75, 1.0):
        retriever = HybridRetriever(
            chroma_collection=MockCollection(documents),
            documents=documents,
            bm25_weight=weight,
        )
        results = retriever.retrieve(query, k=3)
        _assert_well_formed(results, 3, documents)

        summary.append({
            "weight": weight,
            "results": len(results),
            "top_doc": results[0]["document"][:40],
        })

    assert len(summary) == 5
    assert all(row["results"] == 3 for row in summary)


def test_edge_cases():
    """边界输入不能把检索炸掉，也不能返回结构错乱的结果。"""
    documents = load_sample_documents()
    retriever = _make_retriever(bm25_weight=0.5)

    # 1. 空查询
    empty_results = retriever.retrieve("", k=3)
    assert isinstance(empty_results, list)
    assert len(empty_results) == 3

    # 2. 特殊字符
    special_results = retriever.retrieve("IC-123.456_ABC", k=3)
    _assert_well_formed(special_results, 3, documents)

    # 3. 超长查询
    long_query = "12V to 5V 3A buck converter " * 5
    long_results = retriever.retrieve(long_query, k=3)
    _assert_well_formed(long_results, 3, documents)

    # 4. k 大于语料规模 → 最多返回全部文档
    overflow_results = retriever.retrieve("buck", k=10000)
    assert len(overflow_results) == len(documents), (
        f"k 超过语料规模时应返回全部 {len(documents)} 条，实际 {len(overflow_results)}"
    )
    _assert_well_formed(overflow_results, len(documents), documents)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "已知缺陷：HybridRetriever.retrieve() 的 RRF 融合用的是文档枚举下标而不是 BM25 "
        "排名，导致结果按文档原序返回、相关性不参与排序。见 app/hybrid_retrieval.py "
        "的 `for rank_bm25, doc_idx in enumerate(valid_indices)`。"
        "修好之后本用例会 XPASS（strict 模式下即失败），请把 xfail 去掉并转成正式断言。"
    ),
)
def test_exact_mpn_query_ranks_that_part_first():
    """精确 MPN 查询应当把该 MPN 的文档排到第一位。"""
    retriever = _make_retriever(bm25_weight=1.0)

    results = retriever.retrieve("SY8240", k=3)

    assert results, "查询精确 MPN 竟然一条都没返回"
    assert "SY8240" in results[0]["document"], (
        f"精确 MPN 查询的第一条不是该器件，而是：{results[0]['document']!r}"
    )
