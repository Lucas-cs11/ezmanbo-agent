#!/usr/bin/env python3
"""
build_knowledge_base.py — 工程知识库构建脚本

将 data/knowledge/ 下的知识条目摄入 ChromaDB。
首次运行需下载 sentence-transformers 模型（约 80MB）。

用法：
  PYTHONPATH=. python3 scripts/build_knowledge_base.py            # 默认构建
  PYTHONPATH=. python3 scripts/build_knowledge_base.py --rebuild  # 清空重建
  PYTHONPATH=. python3 scripts/build_knowledge_base.py --query "12V转5V buck 电感选型"  # 检索测试
"""

import sys
import os
import json
from pathlib import Path

# 强制项目根目录在 PYTHONPATH
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def build(persist_dir: str = "data/chroma_db", rebuild: bool = False):
    """构建知识库。"""
    from app.rag import RAGStore

    store = RAGStore(persist_dir=persist_dir)

    if rebuild:
        print("清空已有知识库...")
        store.clear()
        store = RAGStore(persist_dir=persist_dir)

    if store.count > 0:
        print(f"知识库已有 {store.count} 条记录，跳过构建（使用 --rebuild 强制重建）。")
        return store.count

    # 加载知识条目
    kb_file = PROJECT_ROOT / "data" / "knowledge" / "engineering_knowledge.json"
    if not kb_file.exists():
        print(f"错误：知识库文件不存在: {kb_file}")
        return 0

    with open(kb_file, "r", encoding="utf-8") as f:
        entries = json.load(f)

    print(f"加载 {len(entries)} 条知识条目...")

    # 转换为 RAG 文档格式
    documents = []
    for entry in entries:
        metadata = {
            "title": entry.get("title", ""),
            "category": entry.get("category", ""),
            "source": entry.get("source", ""),
            "tags": ",".join(entry.get("tags", [])),
        }
        documents.append({
            "content": entry["content"],
            "metadata": metadata,
        })

    # 摄入
    store.ingest_documents(documents)
    print(f"摄入完成！知识库共 {store.count} 条记录。")
    return store.count


def query_test(query_text: str, top_k: int = 3):
    """快速检索测试。"""
    from app.rag import RAGStore

    store = RAGStore(persist_dir="data/chroma_db")
    if store.count == 0:
        print("知识库为空，请先运行构建: PYTHONPATH=. python3 scripts/build_knowledge_base.py")
        return

    results = store.query(query_text, top_k=top_k)
    print(f"\n查询: \"{query_text}\"\n")
    for i, r in enumerate(results, 1):
        title = r["metadata"].get("title", f"结果 {i}")
        print(f"{i}. 【{title}】（相关度: {r['score']:.3f}）")
        print(f"   {r['content'][:120]}...")
        print()


if __name__ == "__main__":
    if "--rebuild" in sys.argv:
        build(rebuild=True)
    elif "--query" in sys.argv:
        idx = sys.argv.index("--query")
        query_str = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "buck 电感选型"
        query_test(query_str)
    else:
        build()
