"""
semantic_cache.py — 语义缓存层（B4 任务）

基于 ChromaDB，实现语义相似度缓存。
当新查询与缓存中的历史查询相似度 > 0.95 时，直接返回缓存结果，跳过 LLM 调用。

关键优化：
  - SentenceTransformer 模型单例加载（避免每次 get/set 重新下载）
  - 模型下载失败时优雅降级（禁用缓存，不影响主流程）
  - HuggingFace 超时 10s 快速失败

用法:
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

# ── 模型单例 ────────────────────────────────────────────────────
_embedding_model = None
_embedding_model_error = None

MODEL_NAME = "all-MiniLM-L6-v2"


def _get_embedding_model():
    """获取 SentenceTransformer 模型（单例，带超时保护）。

    首次调用时下载模型（~80MB），后续调用复用。
    下载失败时缓存错误，避免重复尝试。
    """
    global _embedding_model, _embedding_model_error

    if _embedding_model is not None:
        return _embedding_model

    if _embedding_model_error is not None:
        raise _embedding_model_error

    # 设置 HuggingFace 镜像 + 下载超时
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")
    os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "30")

    try:
        from sentence_transformers import SentenceTransformer
        # 优先使用本地缓存，避免每次联网验证
        _embedding_model = SentenceTransformer(MODEL_NAME, local_files_only=False)
        return _embedding_model

    except Exception as e:
        _embedding_model_error = RuntimeError(
            f"Failed to load embedding model '{MODEL_NAME}': {e}. "
            f"Semantic cache disabled. Pre-download: "
            f"HF_ENDPOINT=https://hf-mirror.com python -c "
            f"\"from sentence_transformers import SentenceTransformer; SentenceTransformer('{MODEL_NAME}')\""
        )
        raise _embedding_model_error


class SemanticCache:
    """语义缓存层：利用向量相似度缓存 LLM 调用结果。

    基于 cosine 距离，当相似度 > 0.95 时视为命中。
    模型加载失败时自动降级（get/set 均返回未命中/失败）。
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

        # 延迟加载嵌入模型（首次 get/set 时触发下载）
        # 不在 __init__ 中加载，避免阻塞服务启动
        self._model_available = True  # 乐观标记，首次使用时验证

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
        """
        if self._collection.count() == 0:
            return None

        if not self._model_available:
            return None

        try:
            model = _get_embedding_model()
            query_embedding = model.encode([query], show_progress_bar=False).tolist()

            results = self._collection.query(
                query_embeddings=query_embedding,
                n_results=1,
            )

            if not results or not results.get("ids") or not results["ids"][0]:
                return None

            distances = results.get("distances", [[]])[0]
            if not distances:
                return None

            distance = distances[0]
            similarity = 1 - distance

            if similarity < threshold:
                return None

            metadatas = results.get("metadatas", [[]])[0]
            if not metadatas or not isinstance(metadatas, list) or len(metadatas) == 0:
                return None

            metadata_dict = metadatas[0]
            if "cached_result" not in metadata_dict:
                return None

            cached_result = json.loads(metadata_dict["cached_result"])
            return {
                "cached_result": cached_result,
                "similarity": round(similarity, 4),
                "cache_hit": True,
            }

        except Exception:
            return None

    def set(self, query: str, result: Dict[str, Any]) -> bool:
        """存入缓存：将查询和结果存储到向量库。"""
        if not self._model_available:
            return False

        try:
            model = _get_embedding_model()
            query_embedding = model.encode([query], show_progress_bar=False).tolist()

            import hashlib
            doc_id = f"cache_{hashlib.md5(query.encode()).hexdigest()[:8]}"
            cached_result_json = json.dumps(result, ensure_ascii=False)

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

        except Exception:
            return False


# 全局缓存实例
_semantic_cache: Optional[SemanticCache] = None


def get_semantic_cache() -> SemanticCache:
    """获取全局语义缓存实例（懒加载）。"""
    global _semantic_cache
    if _semantic_cache is None:
        _semantic_cache = SemanticCache()
    return _semantic_cache
