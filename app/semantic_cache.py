"""
semantic_cache.py — 语义缓存层（B4 任务）

基于 ChromaDB，实现语义相似度缓存。
当新查询与缓存中的历史查询相似度 > 0.95 时，直接返回缓存结果，跳过 LLM 调用。

用法：
  cache = SemanticCache(persist_dir="data/chroma_cache")
  result = cache.get(query)  # 查询缓存
  if result is None:
      result = expensive_llm_call(query)
      cache.set(query, result)  # 存入缓存
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings


class SemanticCache:
    """语义缓存层：利用向量相似度缓存 LLM 调用结果。

    基于 cosine 距离，当相似度 > 0.95 时视为命中。
    """

    def __init__(self, persist_dir: str = "data/chroma_cache"):
        self._persist_dir = Path(persist_dir)
        self._persist_dir.mkdir(parents=True, exist_ok=True)

        # 初始化 ChromaDB 持久化客户端
        self._client = chromadb.PersistentClient(
            path=str(self._persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # 获取或创建缓存集合（使用 cosine 距离）
        self._collection = self._client.get_or_create_collection(
            name="semantic_cache",
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def count(self) -> int:
        """返回缓存中的条目数。"""
        return self._collection.count()

    def get(self, query: str, threshold: float = 0.95) -> Optional[Dict[str, Any]]:
        """查询缓存，若相似度 > threshold 则返回缓存结果。

        Args:
            query: 查询文本（通常是用户的自然语言输入）
            threshold: 相似度阈值，默认 0.95

        Returns:
            缓存的结果字典，或 None（未命中）

        格式：
            {
                "cached_result": {...},  # 原始 LLM 结果
                "similarity": 0.97,      # 实际相似度
                "cache_hit": True
            }
        """
        if self._collection.count() == 0:
            return None

        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")

            # 编码查询文本
            query_embedding = model.encode([query], show_progress_bar=False).tolist()

            # 查询最相似的结果（只返回 top 1）
            results = self._collection.query(
                query_embeddings=query_embedding,
                n_results=1,
            )

            if not results or not results.get("ids") or not results["ids"][0]:
                return None

            # 提取相似度（ChromaDB 返回的距离，cosine 距离 0-2）
            # 相似度 = 1 - cosine_distance
            distances = results.get("distances", [[]])[0]
            if not distances:
                return None

            distance = distances[0]
            similarity = 1 - distance  # cosine 相似度转换

            # 检查是否超过阈值
            if similarity < threshold:
                return None

            # 命中：从元数据中获取缓存的结果
            metadatas = results.get("metadatas", [[]])[0]
            if not metadatas or not isinstance(metadatas, list) or len(metadatas) == 0:
                return None

            # metadatas 是一个列表，取第一个元素（字典）
            metadata_dict = metadatas[0]
            if "cached_result" not in metadata_dict:
                return None

            cached_result_json = metadata_dict["cached_result"]
            cached_result = json.loads(cached_result_json)

            return {
                "cached_result": cached_result,
                "similarity": round(similarity, 4),
                "cache_hit": True,
            }

        except Exception as e:
            from .log_util import warn_swallow
            warn_swallow("semantic_cache", e, "cache get")
            return None

    def set(self, query: str, result: Dict[str, Any]) -> bool:
        """存入缓存：将查询和结果存储到向量库。

        Args:
            query: 查询文本
            result: 要缓存的结果（通常是 LLM 的返回值）

        Returns:
            True（成功）或 False（失败）
        """
        try:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer("all-MiniLM-L6-v2")

            # 编码查询文本
            query_embedding = model.encode([query], show_progress_bar=False).tolist()

            # 生成唯一 ID（基于查询内容的哈希）
            import hashlib
            doc_id = f"cache_{hashlib.md5(query.encode()).hexdigest()[:8]}"

            # 序列化结果为 JSON（存入元数据）
            cached_result_json = json.dumps(result, ensure_ascii=False)

            # 添加到集合
            self._collection.add(
                ids=[doc_id],
                embeddings=query_embedding,
                documents=[query],
                metadatas=[{
                    "cached_result": cached_result_json,
                    "query_length": len(query),
                }],
            )

            return True

        except Exception as e:
            from .log_util import warn_swallow
            warn_swallow("semantic_cache", e, "cache set")
            return False


# 全局缓存实例
_semantic_cache: Optional[SemanticCache] = None


def get_semantic_cache() -> SemanticCache:
    """获取全局语义缓存实例（懒加载）。"""
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    return _semantic_cache
