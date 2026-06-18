#!/usr/bin/env python3
"""
download_datasheets.py — 批量下载 eZ-PLM RAG 数据手册

从 数据手册下载清单_eZPLM_RAG.xlsx 读取 URL，下载到 docs/datasheets/。
支持：resume（跳过已有）、重试、进度条、User-Agent 伪装。
"""

from __future__ import annotations

import os
import sys
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple

import requests
from tqdm import tqdm

# ── 项目根目录 ──────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXCEL_PATH = PROJECT_ROOT / "数据手册下载清单_eZPLM_RAG.xlsx"
OUTPUT_DIR = PROJECT_ROOT / "docs" / "datasheets"

# ── 请求头（模拟浏览器，避免某些 CDN 拒 403）───────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept": "application/pdf,application/octet-stream,*/*",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
}

# ── 下载配置 ────────────────────────────────────────────────────────
MAX_RETRIES = 3
RETRY_DELAY = 2.0  # 秒
REQUEST_TIMEOUT = 60  # 秒
CHUNK_SIZE = 8192


def load_parts_from_excel(excel_path: Path) -> List[Dict]:
    """从 Excel 读取完整清单 Sheet，返回器件列表。"""
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


def _sanitise_filename(name: str) -> str:
    """清理文件名中的非法字符。"""
    import re
    # 替换路径分隔符和特殊字符
    name = name.replace("/", "_").replace("\\", "_")
    name = re.sub(r'[<>:"|?*]', "_", name)
    return name


def download_one(
    url: str,
    dest: Path,
    mpn: str,
    retries: int = MAX_RETRIES,
) -> Tuple[bool, str]:
    """下载单个 PDF 文件。

    Returns:
        (success, message)
    """
    # 检查是否已存在（且非空）
    if dest.exists() and dest.stat().st_size > 1000:
        # 验证文件头是否为 PDF
        with open(dest, "rb") as f:
            header = f.read(5)
        if header.startswith(b"%PDF"):
            return True, f"skip: already downloaded ({dest.stat().st_size} bytes)"
        else:
            # 损坏文件，重新下载
            dest.unlink()

    last_error = ""
    for attempt in range(1, retries + 1):
        try:
            resp = requests.get(
                url,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT,
                stream=True,
                allow_redirects=True,
            )
            resp.raise_for_status()

            # 验证 content-type（有些 CDN 可能返回 HTML 错误页）
            ct = resp.headers.get("Content-Type", "")
            if "pdf" not in ct.lower() and "octet-stream" not in ct.lower():
                # TI 有时返回 application/pdf 或 binary/octet-stream
                if "text/html" in ct.lower():
                    return False, f"error: HTML instead of PDF (content-type={ct})"

            # 流式写入
            with open(dest, "wb") as f:
                for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                    f.write(chunk)

            # 验证写入结果
            file_size = dest.stat().st_size
            if file_size < 1000:
                dest.unlink()
                return False, f"error: file too small ({file_size} bytes)"

            with open(dest, "rb") as f:
                header = f.read(5)
            if not header.startswith(b"%PDF"):
                dest.unlink()
                return False, f"error: not a valid PDF (header={header[:10]!r})"

            return True, f"ok: {file_size} bytes"

        except requests.RequestException as e:
            last_error = str(e)
            if attempt < retries:
                time.sleep(RETRY_DELAY * attempt)

    return False, f"error after {retries} attempts: {last_error}"


def main():
    """主入口：读取 Excel → 下载全部 PDF。"""
    if not EXCEL_PATH.exists():
        print(f"[ERROR] Excel 文件不存在: {EXCEL_PATH}")
        sys.exit(1)

    parts = load_parts_from_excel(EXCEL_PATH)
    print(f"[INFO] 从 Excel 读取到 {len(parts)} 个器件")

    # 创建输出目录
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 按优先级排序：P1 先下载
    priority_order = {"P1": 0, "P2": 1, "P3": 2}
    parts.sort(key=lambda p: priority_order.get(p["priority"], 99))

    success_count = 0
    fail_count = 0
    fail_list: List[Dict] = []

    print(f"[INFO] 开始下载到 {OUTPUT_DIR}")
    print(f"[INFO] 将尝试 {len(parts)} 个文件（P1 优先）\n")

    for part in tqdm(parts, desc="下载数据手册", unit="file"):
        mpn = part["mpn"]
        url = part["url"]
        filename = _sanitise_filename(part["filename"])
        dest = OUTPUT_DIR / filename

        if not url:
            fail_count += 1
            fail_list.append({**part, "error": "no URL"})
            continue

        ok, msg = download_one(url, dest, mpn)
        if ok:
            success_count += 1
        else:
            fail_count += 1
            fail_list.append({**part, "error": msg})

        tqdm.write(f"  [{mpn:25s}] {msg}")

    # ── 汇总报告 ──────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"[DONE] 下载完成")
    print(f"  成功: {success_count}/{len(parts)}")
    print(f"  失败: {fail_count}/{len(parts)}")

    if fail_list:
        print(f"\n  失败清单:")
        for f in fail_list:
            print(f"    - {f['mpn']:25s} [{f['priority']}] {f.get('error', 'unknown')}")

        # 写入失败日志
        fail_log = PROJECT_ROOT / "docs" / "datasheets" / "download_failures.json"
        import json
        with open(fail_log, "w", encoding="utf-8") as fh:
            json.dump(fail_list, fh, ensure_ascii=False, indent=2)
        print(f"\n  失败详情已写入: {fail_log}")

    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
