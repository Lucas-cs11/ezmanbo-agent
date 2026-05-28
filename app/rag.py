"""
rag.py — 工程知识 RAG 检索模块（最小可行版）

基于 ChromaDB + sentence-transformers，存储和检索电子工程设计知识。
知识来源：设计公式、选型规范、应用笔记、标准要求等。

用法：
  store = RAGStore(persist_dir="data/chroma_db")
  store.ingest_documents([{"content": "...", "metadata": {...}}, ...])
  results = store.query("12V转5V buck 电感选型", top_k=3)
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

# 懒加载 embedding 模型（首次调用时下载，约 80MB）
_embedding_model = None


def _get_embedding_model():
    """懒加载 sentence-transformers 模型（all-MiniLM-L6-v2，轻量）。"""
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embedding_model


class RAGStore:
    """工程知识向量存储与检索。

    每个文档 = {content: str, metadata: dict}。
    内部自动分块（按段落）并生成 embedding。
    """

    def __init__(self, persist_dir: str = "data/chroma_db"):
        self._persist_dir = Path(persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(
            path=str(self._persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        self._collection = self._client.get_or_create_collection(
            name="engineering_knowledge",
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def count(self) -> int:
        return self._collection.count()

    def ingest_documents(self, documents: List[Dict[str, Any]], batch_size: int = 32):
        """批量摄入文档。每个文档含 content 和 metadata 字段。"""
        model = _get_embedding_model()

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            texts = [doc["content"] for doc in batch]
            ids = [f"doc_{i + j}" for j in range(len(batch))]
            metadatas = [doc.get("metadata", {}) for doc in batch]

            # 生成 embedding 并入库
            embeddings = model.encode(texts, show_progress_bar=False).tolist()
            self._collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
            )

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        category_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """语义检索最相关的工程知识片段。

        Args:
            query_text: 查询文本（如 "12V转5V buck 电感计算公式"）
            top_k: 返回条数
            category_filter: 可选的类别过滤（如 "buck_design", "thermal"）

        Returns:
            [{content, metadata, score}, ...]
        """
        model = _get_embedding_model()
        query_embedding = model.encode([query_text], show_progress_bar=False).tolist()

        where_filter = None
        if category_filter:
            where_filter = {"category": category_filter}

        results = self._collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        output = []
        if results["ids"] and results["ids"][0]:
            for j in range(len(results["ids"][0])):
                distance = results["distances"][0][j] if results["distances"] else 1.0
                # cosine distance → similarity score (0-1)
                score = max(0.0, 1.0 - distance)
                output.append({
                    "content": results["documents"][0][j],
                    "metadata": results["metadatas"][0][j] if results["metadatas"] else {},
                    "score": round(score, 3),
                })
        return output

    def clear(self):
        """清空知识库（用于重建）。"""
        self._client.delete_collection("engineering_knowledge")
        self._collection = self._client.get_or_create_collection(
            name="engineering_knowledge",
            metadata={"hnsw:space": "cosine"},
        )


def build_context_from_results(results: List[Dict[str, Any]], max_chars: int = 1500) -> str:
    """将 RAG 检索结果拼接为 LLM 上下文文本。

    Args:
        results: RAGStore.query() 的返回结果
        max_chars: 拼接后最大字符数（避免超出 LLM context 限制）

    Returns:
        格式化的参考知识文本
    """
    if not results:
        return "（未检索到相关工程知识）"

    lines = []
    total = 0
    for i, r in enumerate(results, 1):
        title = r["metadata"].get("title", f"参考条目 {i}")
        content = r["content"]
        entry = f"【{title}】（相关度: {r['score']:.2f}）\n{content}"
        if total + len(entry) > max_chars:
            entry = entry[:max_chars - total] + "..."
            lines.append(entry)
            break
        lines.append(entry)
        total += len(entry) + 2

    return "\n\n".join(lines)


# ── 全局单例 ──────────────────────────────────────────────────────
_rag_store: Optional[RAGStore] = None


def get_rag_store(persist_dir: str = "data/chroma_db") -> RAGStore:
    """获取全局 RAGStore 单例。"""
    global _rag_store
    if _rag_store is None:
        _rag_store = RAGStore(persist_dir=persist_dir)
    return _rag_store
