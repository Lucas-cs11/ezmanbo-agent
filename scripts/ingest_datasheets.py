#!/usr/bin/env python3
"""
ingest_datasheets.py — 数据手册 RAG 全管线

流程：
  1. 下载：从 Excel 读取 URL → 下载 PDF 到 docs/datasheets/
  2. 解析：pymupdf 提取文本 → 检测章节 → 按字段类型切块
  3. 灌入：将 chunk 嵌入 ChromaDB RAG 知识库

用法：
  python scripts/ingest_datasheets.py              # 全管线（下载 + 解析 + 灌入）
  python scripts/ingest_datasheets.py --skip-dl    # 跳过下载（已有 PDF）
  python scripts/ingest_datasheets.py --dry-run    # 仅解析，不灌入（测试）
  python scripts/ingest_datasheets.py --clear      # 先清空 RAG 再灌入
"""

from __future__ import annotations

import sys
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict

# 确保项目根目录在 sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.datasheet_parser import DatasheetParser, chunks_to_ingest_format
from app.rag import get_rag_store, RAGStore


# ── 路径常量 ──────────────────────────────────────────────────────
EXCEL_PATH = PROJECT_ROOT / "数据手册下载清单_eZPLM_RAG.xlsx"
DATASHEETS_DIR = PROJECT_ROOT / "docs" / "datasheets"
CHROMA_DIR = PROJECT_ROOT / "data" / "chroma_db"
PROGRESS_FILE = DATASHEETS_DIR / "ingestion_progress.json"


def load_excel_registry(excel_path: Path) -> List[Dict]:
    """从 Excel 读取完整器件注册表。"""
    import openpyxl

    wb = openpyxl.load_workbook(str(excel_path))
    ws = wb["完整清单"]

    parts = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if row[0] is None:
            continue
        parts.append({
            "seq": int(row[0]),
            "manufacturer": str(row[1]).strip(),
            "mpn": str(row[2]).strip(),
            "category": str(row[3]).strip(),
            "topology": str(row[4]).strip() if row[4] else "",
            "vin": str(row[5]).strip() if row[5] else "",
            "vout": str(row[6]).strip() if row[6] else "",
            "iout": str(row[7]).strip() if row[7] else "",
            "priority": str(row[8]).strip(),
            "url": str(row[9]).strip() if row[9] else "",
            "filename": str(row[10]).strip(),
            "rag_usage": str(row[11]).strip() if row[11] else "",
        })

    wb.close()
    return parts


def load_progress() -> Dict[str, dict]:
    """加载已处理的文件记录（断点续传）。"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_progress(progress: Dict[str, dict]):
    """保存处理进度。"""
    with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def step1_download(parts: List[Dict]) -> int:
    """步骤1：下载数据手册 PDF。"""
    from scripts.download_datasheets import download_one, _sanitise_filename
    from tqdm import tqdm

    DATASHEETS_DIR.mkdir(parents=True, exist_ok=True)

    # 按优先级排序
    priority_order = {"P1": 0, "P2": 1, "P3": 2}
    parts_sorted = sorted(parts, key=lambda p: priority_order.get(p["priority"], 99))

    success = 0
    fail = 0
    skipped = 0

    print(f"[STEP 1/3] 下载数据手册 ({len(parts_sorted)} 个文件)")
    print(f"[INFO] 输出目录: {DATASHEETS_DIR}\n")

    for part in tqdm(parts_sorted, desc="下载", unit="file"):
        url = part["url"]
        filename = _sanitise_filename(part["filename"])
        dest = DATASHEETS_DIR / filename

        if not url:
            fail += 1
            tqdm.write(f"  [{part['mpn']:25s}] SKIP: no URL")
            continue

        ok, msg = download_one(url, dest, part["mpn"])
        if ok:
            if "skip" in msg:
                skipped += 1
            else:
                success += 1
        else:
            fail += 1
        tqdm.write(f"  [{part['mpn']:25s}] {msg}")

    print(f"\n[RESULT] 下载完成: 新增={success}, 已有={skipped}, 失败={fail}")
    return success + skipped


def step2_parse(parts: List[Dict], dry_run: bool = False) -> Dict[str, list]:
    """步骤2：解析 PDF → 分块。"""
    from tqdm import tqdm

    parser = DatasheetParser(target_chunk_size=600, chunk_overlap=100)

    all_chunks: Dict[str, list] = {}  # mpn → List[{content, metadata}]
    progress = load_progress()
    fail_count = 0
    skip_count = 0

    print(f"\n[STEP 2/3] 解析 PDF 并分块 ({len(parts)} 个器件)")
    print(f"[INFO] 目标块大小: {parser.target_chunk_size} chars, 重叠: {parser.chunk_overlap} chars\n")

    for part in tqdm(parts, desc="解析", unit="file"):
        mpn = part["mpn"]
        filename = DATASHEETS_DIR / part["filename"]

        # 断点续传
        if mpn in progress and not dry_run:
            skip_count += 1
            # 仍然需要加载 chunks 供下一步使用
            if dry_run:
                continue

        if not filename.exists():
            fail_count += 1
            tqdm.write(f"  [{mpn:25s}] NOT FOUND: {filename}")
            continue

        try:
            chunks = parser.parse(
                str(filename),
                mpn=mpn,
                manufacturer=part["manufacturer"],
                category=part["category"],
                topology=part["topology"],
            )

            ingest_chunks = chunks_to_ingest_format(chunks)

            if dry_run:
                # 打印分块统计
                field_types = {}
                for ch in chunks:
                    ft = ch.field_type
                    field_types[ft] = field_types.get(ft, 0) + 1
                type_summary = ", ".join(
                    f"{ft}:{n}" for ft, n in sorted(field_types.items())
                )
                tqdm.write(
                    f"  [{mpn:25s}] {len(chunks):3d} chunks "
                    f"| {len(filename.stat().st_size)/1024:6.1f} KB "
                    f"| {type_summary}"
                )
            else:
                all_chunks[mpn] = ingest_chunks
                total_content_len = sum(len(c["content"]) for c in ingest_chunks)
                tqdm.write(
                    f"  [{mpn:25s}] {len(ingest_chunks):3d} chunks, "
                    f"{total_content_len:6d} chars total"
                )

            # 记录进度
            progress[mpn] = {
                "mpn": mpn,
                "manufacturer": part["manufacturer"],
                "category": part["category"],
                "priority": part["priority"],
                "chunks": len(chunks),
                "total_chars": sum(len(c.content) for c in chunks) if not dry_run else 0,
                "field_types": list(set(c.field_type for c in chunks)),
                "filename": part["filename"],
                "ingested": False,
            }

        except Exception as e:
            fail_count += 1
            tqdm.write(f"  [{mpn:25s}] ERROR: {e}")

    # 保存进度
    if not dry_run:
        save_progress(progress)

    total_chunks = sum(len(v) for v in all_chunks.values())
    print(
        f"\n[RESULT] 解析完成: "
        f"成功={len(all_chunks)}, 跳过={skip_count}, 失败={fail_count}"
    )
    print(f"[RESULT] 总分块数: {total_chunks}")

    return all_chunks


def step3_ingest(
    all_chunks: Dict[str, list],
    rag_store: RAGStore,
    clear_first: bool = False,
):
    """步骤3：将分块灌入 ChromaDB RAG 知识库。"""
    from tqdm import tqdm

    print(f"\n[STEP 3/3] 灌入 ChromaDB RAG 知识库")

    if clear_first:
        print("[INFO] 清空现有知识库...")
        rag_store.clear()
        print("[INFO] 知识库已清空")

    before_count = rag_store.count
    print(f"[INFO] 灌入前知识库条目数: {before_count}")

    # 展平所有 chunks
    all_docs = []
    doc_counter = 0
    for mpn, chunks in all_chunks.items():
        for ch in chunks:
            all_docs.append({
                "content": ch["content"],
                "metadata": {
                    **ch["metadata"],
                    "mpn": mpn,
                    "ingest_batch": "datasheet_v1",
                },
            })
            doc_counter += 1

    if not all_docs:
        print("[WARN] 无数据可灌入")
        return

    print(f"[INFO] 准备灌入 {len(all_docs)} 条 chunk（来自 {len(all_chunks)} 个器件）")

    # 批量灌入（分批避免 OOM，传递递增 id_offset 防止 ID 碰撞）
    BATCH_SIZE = 64
    total_batches = (len(all_docs) + BATCH_SIZE - 1) // BATCH_SIZE

    with tqdm(total=len(all_docs), desc="灌入 ChromaDB", unit="chunk") as pbar:
        for i in range(0, len(all_docs), BATCH_SIZE):
            batch = all_docs[i : i + BATCH_SIZE]
            try:
                rag_store.ingest_documents(batch, id_offset=i)
                pbar.update(len(batch))
            except Exception as e:
                print(f"\n[ERROR] Batch {i//BATCH_SIZE + 1}/{total_batches} failed: {e}")
                # 尝试逐个灌入以定位问题
                for doc in batch:
                    try:
                        rag_store.ingest_documents([doc])
                        pbar.update(1)
                    except Exception as e2:
                        print(f"  [ERROR] Single doc failed: {doc['metadata'].get('mpn', '?')} - {e2}")

    after_count = rag_store.count
    print(f"\n[RESULT] 灌入完成: {before_count} → {after_count} (+{after_count - before_count})")

    # 更新进度标记
    progress = load_progress()
    for mpn in all_chunks:
        if mpn in progress:
            progress[mpn]["ingested"] = True
    save_progress(progress)


def print_statistics():
    """打印 RAG 知识库统计信息。"""
    store = get_rag_store(str(CHROMA_DIR))

    print(f"\n{'='*60}")
    print(f"RAG 知识库统计")
    print(f"{'='*60}")
    print(f"总条目数: {store.count}")
    print(f"存储路径: {CHROMA_DIR}")

    if store.count == 0:
        return

    # 按 field_type 统计
    try:
        collection = store._collection
        all_meta = collection.get(include=["metadatas"])
        if all_meta and all_meta["metadatas"]:
            field_counts = {}
            mfr_counts = {}
            for m in all_meta["metadatas"]:
                ft = m.get("field_type", "unknown")
                field_counts[ft] = field_counts.get(ft, 0) + 1
                mfr = m.get("manufacturer", "unknown")
                mfr_counts[mfr] = mfr_counts.get(mfr, 0) + 1

            print(f"\n按字段类型分布:")
            for ft, n in sorted(field_counts.items(), key=lambda x: -x[1]):
                print(f"  {ft:30s} {n:5d}")

            print(f"\n按厂商分布:")
            for mfr, n in sorted(mfr_counts.items(), key=lambda x: -x[1]):
                print(f"  {mfr:30s} {n:5d}")
    except Exception as e:
        print(f"  (统计查询失败: {e})")


def main():
    parser = argparse.ArgumentParser(
        description="数据手册 RAG 全管线：下载 → 解析 → 灌入 ChromaDB",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                 # 全管线
  %(prog)s --skip-dl       # 跳过下载（PDF 已就绪）
  %(prog)s --dry-run       # 仅解析预览，不灌入
  %(prog)s --clear         # 清空旧库再灌入
        """,
    )
    parser.add_argument(
        "--skip-dl", action="store_true",
        help="跳过下载步骤（假设 PDF 已存在）",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="仅解析并预览分块，不灌入 ChromaDB",
    )
    parser.add_argument(
        "--clear", action="store_true",
        help="灌入前清空现有知识库",
    )

    args = parser.parse_args()

    # ── 加载 Excel 注册表 ────────────────────────────────────────
    if not EXCEL_PATH.exists():
        print(f"[ERROR] Excel 文件不存在: {EXCEL_PATH}")
        sys.exit(1)

    parts = load_excel_registry(EXCEL_PATH)
    print(f"[INFO] 从 Excel 加载 {len(parts)} 个器件\n")
    print(f"[INFO] 模式: {'DRY RUN (预览)' if args.dry_run else 'FULL INGESTION'}")
    if args.clear:
        print(f"[INFO] 将清空现有知识库后重新灌入")

    # ── 步骤1：下载 ──────────────────────────────────────────────
    available_count = len(parts)
    if not args.skip_dl:
        available_count = step1_download(parts)
        if available_count == 0:
            print("\n[ERROR] 没有成功下载的 PDF，中止")
            sys.exit(1)

    # ── 步骤2：解析分块 ──────────────────────────────────────────
    all_chunks = step2_parse(parts, dry_run=args.dry_run)

    if args.dry_run:
        print(f"\n[DRY RUN] 解析完成，共 {sum(len(v) for v in all_chunks.values())} 个分块（未灌入）")
        sys.exit(0)

    # ── 步骤3：灌入 ChromaDB ─────────────────────────────────────
    rag_store = get_rag_store(str(CHROMA_DIR))
    step3_ingest(all_chunks, rag_store, clear_first=args.clear)

    # ── 打印统计 ─────────────────────────────────────────────────
    print_statistics()

    print(f"\n{'='*60}")
    print(f"DONE. RAG 知识库已就绪。")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
