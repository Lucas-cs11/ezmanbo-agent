"""
hybrid_retrieval.py — 混合检索模块（BM25 + 向量检索 + RRF 融合）

融合关键词检索（BM25）和语义检索（向量）的优势：
- BM25：对精确型号匹配（如 "SY8240"）友好
- 向量检索：对功能描述（如 "高效率小封装 Buck"）友好
- RRF：Reciprocal Rank Fusion，通过排名融合避免某一方法的单点失效

用法：
  retriever = HybridRetriever(chroma_collection, documents)
  results = retriever.retrieve(query="12V转5V 3A Buck 芯片", k=5)
"""

from __future__ import annotations

import numpy as np
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi


class HybridRetriever:
    """混合检索器：融合 BM25 关键词匹配和向量相似度。

    Args:
        chroma_collection: ChromaDB collection 对象（已有 embeddings）
        documents: 文档列表，顺序与 collection 中的 IDs 对应
        bm25_weight: BM25 结果权重（0-1），向量权重为 1-bm25_weight
        rrf_k: RRF 融合中的常数项（通常为 60），防止除零
    """

    def __init__(
        self,
        chroma_collection,
        documents: List[str],
        bm25_weight: float = 0.5,
        rrf_k: int = 60,
    ):
        self.chroma = chroma_collection
        self.documents = documents
        self.bm25_weight = bm25_weight
        self.rrf_k = rrf_k

        # 构建 BM25 索引（文档需要分词）
        # 简单按空格和标点分词
        tokenized_docs = [self._tokenize(doc) for doc in documents]
        self.bm25 = BM25Okapi(tokenized_docs)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """简单分词：按空格、中文分隔符、英文标点分割。"""
        import re
        # 按空格、中文标点、英文标点分割
        tokens = re.findall(r'[\w一-鿿]+', text.lower())
        return tokens

    def retrieve(
        self,
        query: str,
        k: int = 5,
        bm25_threshold: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """混合检索：结合 BM25 和向量相似度。

        Args:
            query: 查询文本
            k: 返回的结果数量
            bm25_threshold: BM25 得分阈值（低于阈值的结果会被过滤），None 表示不过滤

        Returns:
            [{doc_id, document, bm25_score, vector_score, hybrid_score}, ...]
            其中 hybrid_score = bm25_weight * bm25_norm + (1 - bm25_weight) * vector_score
        """
        # ── BM25 检索 ────────────────────────────────────────────
        query_tokens = self._tokenize(query)
        bm25_scores = np.array(self.bm25.get_scores(query_tokens), dtype=np.float32)

        # 过滤和标准化 BM25 得分
        if bm25_threshold is not None:
            valid_indices = np.where(bm25_scores >= bm25_threshold)[0]
        else:
            valid_indices = np.arange(len(bm25_scores))

        if len(valid_indices) == 0:
            # BM25 无结果，降级到向量检索
            return self._vector_retrieve_only(query, k)

        bm25_scores_valid = bm25_scores[valid_indices]
        # 标准化到 [0, 1]
        bm25_max = np.max(bm25_scores_valid) if len(bm25_scores_valid) > 0 else 1
        bm25_scores_norm = bm25_scores_valid / (bm25_max + 1e-9)

        # ── 向量检索（仅对 BM25 有效结果进行） ─────────────────
        vector_results = self.chroma.query(
            query_texts=[query],
            n_results=k * 2,  # 多取一些，便于融合
            include=["documents", "metadatas", "distances"],
        )

        # 构建向量检索的得分字典（cosine distance → similarity）
        vector_scores_dict: Dict[int, float] = {}
        if vector_results["ids"] and vector_results["ids"][0]:
            for i, doc_id in enumerate(vector_results["ids"][0]):
                # 从 ChromaDB 的距离转换为相似度 (cosine 距离范围 [0, 2])
                distance = vector_results["distances"][0][i] if vector_results["distances"] else 1.0
                similarity = max(0.0, 1.0 - distance)
                # 尝试从 doc_id 提取索引（假设 id 格式为 "doc_N"）
                try:
                    idx = int(doc_id.split("_")[-1])
                    vector_scores_dict[idx] = similarity
                except (ValueError, IndexError):
                    pass

        # ── RRF 融合 ──────────────────────────────────────────────
        # 为 BM25 的每个有效结果计算 RRF，融合向量得分
        hybrid_results: List[Dict[str, Any]] = []
        for rank_bm25, doc_idx in enumerate(valid_indices):
            bm25_score = bm25_scores_norm[rank_bm25]
            vector_score = vector_scores_dict.get(doc_idx, 0.0)

            # RRF 公式：score = 1 / (k + rank)，rank 从 1 开始
            rrf_bm25 = 1.0 / (self.rrf_k + rank_bm25 + 1)

            # 向量排名：在 vector_scores_dict 中的位置
            vector_rank = sorted(
                [(v, i) for i, v in vector_scores_dict.items()],
                key=lambda x: -x[0]
            )
            vector_rank_idx = next(
                (i for i, (_, idx) in enumerate(vector_rank) if idx == doc_idx),
                len(vector_rank)
            )
            rrf_vector = 1.0 / (self.rrf_k + vector_rank_idx + 1)

            # 加权融合
            hybrid_score = (
                self.bm25_weight * rrf_bm25
                + (1 - self.bm25_weight) * rrf_vector
            )

            hybrid_results.append({
                "doc_idx": doc_idx,
                "document": self.documents[doc_idx] if doc_idx < len(self.documents) else "",
                "bm25_score": round(float(bm25_score), 3),
                "vector_score": round(vector_score, 3),
                "hybrid_score": round(hybrid_score, 4),
            })

        # 按混合得分排序，取 TOP-k
        hybrid_results.sort(key=lambda x: -x["hybrid_score"])
        return hybrid_results[:k]

    def _vector_retrieve_only(self, query: str, k: int) -> List[Dict[str, Any]]:
        """降级方案：仅使用向量检索。"""
        vector_results = self.chroma.query(
            query_texts=[query],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        results: List[Dict[str, Any]] = []
        if vector_results["ids"] and vector_results["ids"][0]:
            for i, doc_text in enumerate(vector_results["documents"][0]):
                distance = vector_results["distances"][0][i] if vector_results["distances"] else 1.0
                similarity = max(0.0, 1.0 - distance)
                results.append({
                    "document": doc_text,
                    "vector_score": round(similarity, 3),
                    "bm25_score": 0.0,
                    "hybrid_score": round(similarity * (1 - self.bm25_weight), 4),
                })

        return results


def integrate_hybrid_retriever_with_chroma(
    chroma_collection,
    documents: List[str],
) -> HybridRetriever:
    """便捷工厂函数：从 ChromaDB collection 和文档列表创建混合检索器。

    Args:
        chroma_collection: RAGStore 的 _collection 对象
        documents: 文档列表

    Returns:
        HybridRetriever 实例
    """
    return HybridRetriever(
        chroma_collection=chroma_collection,
        documents=documents,
        bm25_weight=0.5,
    )
