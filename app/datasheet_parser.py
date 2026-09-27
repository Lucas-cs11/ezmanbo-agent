"""
datasheet_parser.py — 数据手册 PDF 解析与智能分块

基于 pymupdf (fitz) 提取文本 → 检测章节边界 → 按语义块切分 →
标注 field_type → 输出标准化 chunk 列表，可直接喂入 ChromaDB RAGStore。

核心能力：
  1. 章节检测：字号变化 + 关键词匹配
  2. 表格识别：pymupdf table detection + 正则降级方案
  3. 字段分类：overview | pinout | absolute_maximum | electrical_characteristics
                | typical_performance | application_info | thermal | layout | package
  4. 重叠分块：~600 chars/chunk，~100 chars overlap
"""

from __future__ import annotations

import re
import math
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field

import fitz  # pymupdf


# ── 章节标题关键词 ──────────────────────────────────────────────────
# (正则模式, field_type 标签)
_SECTION_PATTERNS: List[Tuple[str, str]] = [
    # ── 概览 / 特性 ──
    (r"^\s*(FEATURES?|特[点性徵]|概要|概述)\s*$", "overview"),
    (r"^\s*(DESCRIPTION|GENERAL\s*DESCRIPTION|概述|器件描述)\s*$", "overview"),
    (r"^\s*(APPLICATIONS?|典型应用|应用领域)\s*$", "overview"),
    (r"^\s*(BENEFITS|优势|特点)\s*$", "overview"),
    (r"^\s*(DEVICE\s*INFORMATION|器件信息|PRODUCT\s*SUMMARY)\s*$", "overview"),
    (r"^\s*(SIMPLIFIED\s*SCHEMATIC|BLOCK\s*DIAGRAM)\s*$", "overview"),

    # ── 引脚 ──
    (r"^\s*(PIN\s*(CONFIGURATION|FUNCTIONS?|DESCRIPTION|ASSIGNMENT)|引脚[配置功能描述图])", "pinout"),
    (r"^\s*(TERMINAL\s*FUNCTIONS?|BALL\s*ASSIGNMENT)", "pinout"),
    (r"^\s*PIN\s*FUNCTIONS?", "pinout"),

    # ── 极限参数 ──
    (r"^\s*(ABSOLUTE\s*MAXIMUM\s*RATINGS?|极限[参额定]值|最大额定值)", "absolute_maximum"),
    (r"^\s*(MAXIMUM\s*RATINGS?)", "absolute_maximum"),
    (r"^\s*(ESD\s*RATINGS?|ESD\s*CAUTION)", "absolute_maximum"),
    (r"^\s*HANDLING\s*RATINGS?", "absolute_maximum"),

    # ── 电气特性 ──
    (r"^\s*(SPECIFICATIONS?)\s*$", "electrical_characteristics"),
    (r"^\s*(ELECTRICAL\s*CHARACTERISTICS?|电气特[性征]|电气参数)", "electrical_characteristics"),
    (r"^\s*(RECOMMENDED\s*OPERATING\s*CONDITIONS?|推荐工作条件)", "electrical_characteristics"),
    (r"^\s*(DC\s*CHARACTERISTICS?|AC\s*CHARACTERISTICS?)", "electrical_characteristics"),
    (r"^\s*(SWITCHING\s*CHARACTERISTICS?|开关特性)", "electrical_characteristics"),
    (r"^\s*(TIMING\s*(REQUIREMENTS?|CHARACTERISTICS?|DIAGRAM))", "electrical_characteristics"),
    (r"^\s*(SUPPLY\s*CURRENT\s*CHARACTERISTICS?)", "electrical_characteristics"),
    (r"^\s*(DISSIPATION\s*RATINGS?)", "electrical_characteristics"),
    (r"^\s*(OPERATING\s*CONDITIONS?)", "electrical_characteristics"),

    # ── 典型性能 ──
    (r"^\s*(TYPICAL\s*(PERFORMANCE|CHARACTERISTICS?)|典型[性能特性])", "typical_performance"),
    (r"^\s*(PERFORMANCE\s*CURVES?|特性曲线)", "typical_performance"),
    (r"^\s*(EFFICIENCY\s*(CURVES?|CHARACTERISTICS?))", "typical_performance"),

    # ── 应用信息（TI: Application Information, ADI: Applications Information）──
    (r"^\s*(APPLICATIONS?\s*INFORMATION|APPLICATIONS?\s*SECTION)", "application_info"),
    (r"^\s*(TYPICAL\s*APPLICATIONS?|典型应用电路|参考设计)", "application_info"),
    (r"^\s*(DESIGN\s*EXAMPLE|设计实例|设计示例)", "application_info"),
    (r"^\s*(DETAILED\s*DESCRIPTION|详细说明|功能描述)", "application_info"),
    (r"^\s*(FUNCTIONAL\s*BLOCK\s*DIAGRAM|功能框图)", "application_info"),
    (r"^\s*(DEVICE\s*FUNCTIONAL\s*MODES?|工作模式)", "application_info"),
    (r"^\s*(POWER\s*GOOD|PG\s*THRESHOLD)", "application_info"),
    (r"^\s*(ENABLE\s*(AND|/)\s*UVLO|ENABLE\s*THRESHOLD)", "application_info"),
    (r"^\s*(SOFT[-\s]?START|SS\s*THRESHOLD|软启动)", "application_info"),
    (r"^\s*(UNDERVOLTAGE\s*LOCK\s*OUT|UVLO\s*THRESHOLD)", "application_info"),
    (r"^\s*(DETAILED\s*DESCRIPTION|Functional\s*Block\s*Diagram)", "application_info"),
    (r"^\s*(APPLICATION\s*(AND|&)\s*IMPLEMENTATION)", "application_info"),
    (r"^\s*(POWER\s*SUPPLY\s*RECOMMENDATIONS?)", "application_info"),
    (r"^\s*(OVER\s*(CURRENT|VOLTAGE|TEMPERATURE)\s*PROTECTION)", "application_info"),
    (r"^\s*(LOOP\s*COMPENSATION|环路补偿|FEEDBACK)", "application_info"),
    (r"^\s*(INDUCTOR\s*SELECTION|电感选型|OUTPUT\s*CAPACITOR)", "application_info"),
    (r"^\s*(INPUT\s*CAPACITOR|EXTERNAL\s*COMPONENT)", "application_info"),
    (r"^\s*(POWER\s*SUPPLY\s*RECOMMENDATIONS?)", "application_info"),

    # ── 热性能 ──
    (r"^\s*(THERMAL\s*(INFORMATION|CHARACTERISTICS|RESISTANCE|SHUTDOWN|CONSIDERATIONS?|PERFORMANCE|PROTECTION|PAD))", "thermal"),
    (r"^\s*(热[阻特性关断]|温度保护|结温|功耗)", "thermal"),
    (r"^\s*(POWER\s*DISSIPATION|功耗[估算计]|DISSIPATION\s*RATING)", "thermal"),
    (r"^\s*(JUNCTION\s*TEMPERATURE|TJ\s*MAX|TJ\s*CALCULATION)", "thermal"),
    (r"^\s*(θJA|θJC|THETA|RθJA|RθJC)", "thermal"),

    # ── Layout / PCB ──
    (r"^\s*(LAYOUT\s*(GUIDELINES?|RECOMMENDATIONS?|CONSIDERATIONS?|EXAMPLE))", "layout"),
    (r"^\s*(PCB\s*(LAYOUT|DESIGN|GUIDELINE))", "layout"),
    (r"^\s*(布线|布局[指南建议规则])", "layout"),
    (r"^\s*(BOARD\s*LAYOUT|PRINTED.CIRCUIT.BOARD)", "layout"),
    (r"^\s*(GROUND\s*PLANE|接[地平面])", "layout"),

    # ── 封装 / 订购 ──
    (r"^\s*(PACKAGE\s*(INFORMATION|DIMENSIONS?|OUTLINE|OPTIONS?|DRAWING))", "package"),
    (r"^\s*(MECHANICAL\s*(DATA|INFORMATION|DRAWING))", "package"),
    (r"^\s*(封装[信息尺寸]|外形[尺寸图])", "package"),
    (r"^\s*(ORDERING\s*INFORMATION|订购信息|选型指南)", "package"),
    (r"^\s*(TAPE\s*AND\s*REEL|REEL\s*INFORMATION|编带)", "package"),
    (r"^\s*(MARKING\s*INFORMATION|丝印|标识)", "package"),
    (r"^\s*(SOLDERING\s*(INFORMATION|PROFILE)|焊接)", "package"),
    (r"^\s*(STORAGE\s*CONDITIONS?|存储条件|MSL)", "package"),
    (r"^\s*(REVISION\s*HISTORY|IMPORTANT\s*NOTICE)", "package"),
]


# ── 字号阈值常数 ──────────────────────────────────────────────────
_HEADING_FONT_RATIO = 1.08   # 字号 > 平均 * 1.08 视为标题候选
_MIN_SECTION_TEXT_LEN = 200  # 至少 200 字符才算一个有效 section


@dataclass
class TextBlock:
    """pymupdf 文本块扩展结构。"""
    text: str
    font_size: float
    bbox: Tuple[float, float, float, float]
    page_num: int
    block_type: str = "text"  # text | table | heading


@dataclass
class ParsedChunk:
    """解析后的语义分块。"""
    content: str
    metadata: Dict[str, str]
    section_title: str = ""
    field_type: str = "general"
    page_range: Tuple[int, int] = (0, 0)
    chunk_index: int = 0


class DatasheetParser:
    """数据手册 PDF 解析器。

    Usage:
        parser = DatasheetParser()
        chunks = parser.parse("TPS54360.pdf", mpn="TPS54360", manufacturer="TI")
        # chunks = [{content, metadata: {mpn, manufacturer, category, field_type, ...}}, ...]
    """

    def __init__(
        self,
        target_chunk_size: int = 600,
        chunk_overlap: int = 100,
        min_chunk_size: int = 80,
    ):
        self.target_chunk_size = target_chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def parse(
        self,
        pdf_path: str | Path,
        mpn: str = "",
        manufacturer: str = "",
        category: str = "",
        topology: str = "",
    ) -> List[ParsedChunk]:
        """解析 PDF 并返回语义分块列表。"""
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        doc = fitz.open(str(pdf_path))
        try:
            # 第一步：提取所有文本块
            all_blocks = self._extract_blocks(doc)

            # 第二步：检测章节边界
            sections = self._detect_sections(all_blocks)

            # 第三步：按章节切块
            chunks = self._chunk_sections(sections)

            # 第四步：注入公共元数据
            base_meta = {
                "mpn": mpn or pdf_path.stem,
                "manufacturer": manufacturer,
                "category": category,
                "topology": topology,
                "source": "datasheet",
                "source_file": pdf_path.name,
            }
            for ch in chunks:
                ch.metadata = {**base_meta, **ch.metadata}

            return chunks
        finally:
            doc.close()

    # ── 文本提取 ──────────────────────────────────────────────────

    def _extract_blocks(self, doc: fitz.Document) -> List[TextBlock]:
        """从 PDF 中提取所有文本块（保留行结构）。"""
        blocks = []

        for page_num, page in enumerate(doc):
            page_blocks = page.get_text("dict")["blocks"]

            for blk in page_blocks:
                if blk["type"] == 0:  # 文本块
                    lines_out = []
                    font_sizes = []
                    has_bold = False
                    all_bold = True  # 是否所有行都含 Bold

                    for line in blk.get("lines", []):
                        line_parts = []
                        line_has_bold = False
                        for span in line.get("spans", []):
                            line_parts.append(span["text"])
                            font_sizes.append(span["size"])
                            if "Bold" in span.get("font", ""):
                                has_bold = True
                                line_has_bold = True
                        line_text = "".join(line_parts).strip()
                        if line_text:
                            lines_out.append(line_text)
                            if not line_has_bold:
                                all_bold = False

                    if not lines_out:
                        continue

                    text = "\n".join(lines_out)
                    if len(text) < 2:
                        continue

                    max_font = max(font_sizes) if font_sizes else 10.0
                    num_lines = len(lines_out)
                    is_short = len(text) < 140
                    is_very_short = len(text) < 60

                    # 判断是否为标题候选
                    is_heading = False

                    # 排除小字号（< 7pt 通常是 PCB 丝印/原理图标签，不是章节标题）
                    if max_font < 7.0:
                        is_heading = False
                    # 1-3 行短文本 + Bold → 标题候选
                    elif num_lines <= 3 and is_short and has_bold:
                        is_heading = True
                    # 单行全大写短文本 → 页眉/表头
                    elif num_lines == 1 and text.isupper() and is_very_short and page_num > 0:
                        is_heading = True
                    # 数字编号开头短文本（如 "8.1 Absolute Maximum Ratings"）
                    elif num_lines <= 2 and is_short and re.match(r"^\d+(\.\d+)*\s+\w", text):
                        is_heading = True

                    blocks.append(TextBlock(
                        text=text,
                        font_size=max_font,
                        bbox=blk["bbox"],
                        page_num=page_num,
                        block_type="heading" if is_heading else "text",
                    ))

                elif blk["type"] == 1:  # 图像块（可能包含表格）
                    # ── C4: 表格提取已移到每页级别，避免重复 ──
                    pass

            # ── C4: 对每页只提取一次表格（在图像块循环外）──
            tables = page.find_tables()
            if tables:
                for table in tables:
                    table_text = self._table_to_text(table)
                    if table_text:
                        blocks.append(TextBlock(
                            text=table_text,
                            font_size=9.0,
                            bbox=table.bbox,
                            page_num=page_num,
                            block_type="table",
                        ))

        return blocks

    def _table_to_text(self, table) -> str:
        """将 pymupdf 表格对象转为结构化文本。"""
        rows = []
        try:
            data = table.extract()
            if not data:
                return ""

            # 表头行
            header = data[0] if data else []
            if header:
                rows.append(" | ".join(str(c) for c in header if c))
                rows.append("-" * 60)

            # 数据行
            for row in data[1:]:
                if row:
                    rows.append(" | ".join(str(c) for c in row if c))
        except Exception:
            return ""

        return "\n".join(rows)

    # ── 章节检测 ──────────────────────────────────────────────────

    def _detect_sections(self, blocks: List[TextBlock]) -> List[Dict]:
        """将文本块分组为章节。

        Returns:
            [{title, field_type, blocks, start_page, end_page, confidence}, ...]
        """
        if not blocks:
            return []

        # 计算全局平均字号用于标题检测
        all_sizes = [b.font_size for b in blocks if b.block_type != "table"]
        avg_font = sum(all_sizes) / len(all_sizes) if all_sizes else 10.0
        heading_threshold = avg_font * _HEADING_FONT_RATIO

        # 检测标题候选
        headings = []
        for i, blk in enumerate(blocks):
            if blk.block_type == "table":
                continue

            is_heading = blk.block_type == "heading"  # 优先信任预处理
            field_type = "general"
            confidence = 0.5

            # 规则1：字号明显大于平均
            if not is_heading and blk.font_size >= heading_threshold:
                is_heading = True
                confidence = 0.6

            # 规则2：文本短且全大写（常见于 TI / ADI 数据手册）
            text_stripped = blk.text.strip()
            text_len = len(text_stripped)
            if not is_heading and text_len < 100:
                if text_stripped.isupper() and text_len > 3:
                    is_heading = True
                    confidence = 0.65

            # 规则3：数字编号开头（如 "1 Overview", "7.3.2 Soft Start"）
            if not is_heading and re.match(r"^\d+(\.\d+)*\s+\w", text_stripped):
                is_heading = True
                confidence = 0.7

            # 规则4：匹配已知章节模式（先剥离 TI 风格数字前缀）
            if is_heading or text_len < 140:
                # 剥离可能的数字前缀 "8.1\n", "8\n", "1.2.3\n" 等
                stripped_for_match = re.sub(
                    r"^\d+(?:\.\d+)*[\s\n]+", "", text_stripped
                )
                flat_stripped = stripped_for_match.replace("\n", " ")
                for pattern, ftype in _SECTION_PATTERNS:
                    if (re.search(pattern, stripped_for_match, re.IGNORECASE) or
                        re.search(pattern, flat_stripped, re.IGNORECASE)):
                        is_heading = True
                        field_type = ftype
                        confidence = 0.9
                        break
                # 如果仍未匹配，尝试原始文本的 flat 版本
                if field_type == "general":
                    flat_text = text_stripped.replace("\n", " ")
                    for pattern, ftype in _SECTION_PATTERNS:
                        if re.search(pattern, flat_text, re.IGNORECASE):
                            is_heading = True
                            field_type = ftype
                            confidence = 0.85
                            break

            if is_heading:
                headings.append({
                    "block_index": i,
                    "title": text_stripped[:120],
                    "field_type": field_type,
                    "confidence": confidence,
                })

        # 构建章节分组
        sections = []
        if not headings:
            # 无标题：整个文档作为一个 general section
            text = "\n".join(b.text for b in blocks)
            sections.append({
                "title": "Full Document",
                "field_type": "general",
                "blocks": blocks,
                "start_page": blocks[0].page_num if blocks else 0,
                "end_page": blocks[-1].page_num if blocks else 0,
                "confidence": 0.3,
            })
        else:
            # 第一个 section：在第一个标题之前的内容
            first_h = headings[0]
            if first_h["block_index"] > 0:
                pre_blocks = blocks[:first_h["block_index"]]
                pre_text = " ".join(b.text for b in pre_blocks[:5])
                # 检测这部分是否本身是标题/摘要信息
                pre_ft = "overview"
                for pat, ft in _SECTION_PATTERNS:
                    if re.search(pat, pre_text, re.IGNORECASE):
                        pre_ft = ft
                        break

                sections.append({
                    "title": "Document Header",
                    "field_type": pre_ft,
                    "blocks": pre_blocks,
                    "start_page": pre_blocks[0].page_num if pre_blocks else 0,
                    "end_page": pre_blocks[-1].page_num if pre_blocks else 0,
                    "confidence": 0.4,
                })

            # 中间 sections
            for i, h in enumerate(headings):
                start_idx = h["block_index"]
                end_idx = (
                    headings[i + 1]["block_index"]
                    if i + 1 < len(headings)
                    else len(blocks)
                )
                section_blocks = blocks[start_idx:end_idx]

                sections.append({
                    "title": h["title"],
                    "field_type": h["field_type"],
                    "blocks": section_blocks,
                    "start_page": section_blocks[0].page_num if section_blocks else 0,
                    "end_page": section_blocks[-1].page_num
                    if section_blocks
                    else 0,
                    "confidence": h["confidence"],
                })

        return sections

    # ── 分块 ──────────────────────────────────────────────────────

    def _chunk_sections(self, sections: List[Dict]) -> List[ParsedChunk]:
        """将章节进一步切分为 RAG 友好的小块。"""
        all_chunks = []
        chunk_idx = 0

        for sec in sections:
            # 合并 section 内所有文本
            texts = [b.text for b in sec["blocks"] if b.text.strip()]
            full_text = "\n".join(texts)

            if len(full_text) < self.min_chunk_size:
                continue

            # 按段落分割
            paragraphs = self._split_paragraphs(full_text)

            # 滑窗分块
            sec_chunks = self._sliding_window(
                paragraphs,
                target_size=self.target_chunk_size,
                overlap=self.chunk_overlap,
            )

            for ch_text in sec_chunks:
                if len(ch_text.strip()) < self.min_chunk_size:
                    continue

                all_chunks.append(ParsedChunk(
                    content=ch_text.strip(),
                    metadata={
                        "field_type": sec["field_type"],
                        "section_title": sec["title"][:100],
                        "page_start": str(sec["start_page"]),
                        "page_end": str(sec["end_page"]),
                    },
                    section_title=sec["title"],
                    field_type=sec["field_type"],
                    page_range=(sec["start_page"], sec["end_page"]),
                    chunk_index=chunk_idx,
                ))
                chunk_idx += 1

        return all_chunks

    def _split_paragraphs(self, text: str) -> List[str]:
        """将文本按段落分割（保留表格结构）。"""
        # 先按双换行分割段落
        raw_paras = re.split(r"\n\s*\n", text)
        paragraphs = []
        for p in raw_paras:
            p = p.strip()
            if not p:
                continue
            # 清理多余空白
            p = re.sub(r"\s+", " ", p)
            paragraphs.append(p)
        return paragraphs

    def _sliding_window(
        self,
        paragraphs: List[str],
        target_size: int = 600,
        overlap: int = 100,
    ) -> List[str]:
        """滑窗分块：累积段落直到达到目标大小，然后开始新块。"""
        if not paragraphs:
            return []

        chunks = []
        current = []
        current_len = 0

        for para in paragraphs:
            para_len = len(para)

            if current_len + para_len > target_size and current:
                # 当前块已满，输出
                chunk_text = "\n\n".join(current)
                chunks.append(chunk_text)

                # 回退 overlap chars 作为新块起点
                # 从最后一个段落中取 overlap 部分
                if overlap > 0 and current:
                    last_para = current[-1]
                    if len(last_para) > overlap:
                        current = [last_para[-overlap:]]
                        current_len = overlap
                    else:
                        current = []
                        current_len = 0
                else:
                    current = []
                    current_len = 0

            current.append(para)
            current_len += para_len

        # 最后一个块
        if current:
            chunk_text = "\n\n".join(current)
            chunks.append(chunk_text)

        return chunks


# ── 便捷函数 ──────────────────────────────────────────────────────

def parse_datasheet(
    pdf_path: str | Path,
    mpn: str = "",
    manufacturer: str = "",
    category: str = "",
    topology: str = "",
) -> List[ParsedChunk]:
    """单文件解析便捷入口。"""
    parser = DatasheetParser()
    return parser.parse(
        pdf_path,
        mpn=mpn,
        manufacturer=manufacturer,
        category=category,
        topology=topology,
    )


def chunks_to_ingest_format(chunks: List[ParsedChunk]) -> List[Dict]:
    """将 ParsedChunk 列表转为 RAGStore.ingest_documents() 格式。"""
    return [
        {
            "content": ch.content,
            "metadata": {
                **ch.metadata,
                "chunk_index": str(ch.chunk_index),
                "field_type": ch.field_type,
            },
        }
        for ch in chunks
    ]
