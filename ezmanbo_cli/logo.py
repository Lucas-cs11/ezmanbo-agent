"""
eZmanbo CLI Logo — 蓝紫渐变电路芯片 ASCII Art (Option C)

对齐 Claude Code LogoV2/Clawd.tsx 的设计模式。
Unicode 半块字符拼合 IC 芯片图案。

视觉特征 (来源: icon-svg.png 最左侧 icon):
  - C 形开口轮廓（字母 "C" = Chip/Circuit，左侧开放）
  - 蓝 → 紫渐变（5 行逐行过渡）
  - 内部嵌套小弧（电容符号 ▗▖/▝▘）
  - 芯片体 block 填充
"""

from __future__ import annotations
import os
from typing import Tuple
from dataclasses import dataclass

from rich.text import Text
from rich.console import Console


# ══════════════════════════════════════════════════════════════════
# Logo 片段定义（对齐 Clawd.tsx POSES 结构）
# ══════════════════════════════════════════════════════════════════

@dataclass
class LogoSegments:
    """Logo 每行的字符片段。每行分为: 前缀 + 左块 + 中间 + 右块 + 后缀。"""
    pre: str    # 行首空白
    left: str   # 左侧边框 + 左芯片体
    mid: str    # 中间（内部嵌套弧 / 空腔 / 芯片体）
    right: str  # 右侧边框 + 右芯片体
    post: str   # 行尾


# ── 标准版（>= 50 列） ──
# 结构示意:
#     ▗▄▄▄▄▄▄▄▖
#    ▐███  ███▌
#    ▐██ ▗▖ █▌
#    ▐██ ▝▘ █▌
#    ▐███  ███▌
#     ▝▀▀▀▀▀▀▀▘
STANDARD_SEGMENTS = [
    LogoSegments('  ', '▗', '▄▄▄▄▄▄▄', '', '▖'),
    LogoSegments(' ', '▐', '███  ███', '▌', ''),
    LogoSegments(' ', '▐', '██ ▗▖ █', '▌', ''),
    LogoSegments(' ', '▐', '██ ▝▘ █', '▌', ''),
    LogoSegments(' ', '▐', '███  ███', '▌', ''),
    LogoSegments('  ', '▝', '▀▀▀▀▀▀▀', '', '▘'),
]

# ── 极简版（< 50 列，无内部弧） ──
MINI_SEGMENTS = [
    LogoSegments('  ', '▗', '▄▄▄▄', '', '▖'),
    LogoSegments(' ', '▐', ' ██ ', '▌', ''),
    LogoSegments(' ', '▐', ' ▗▖ ', '▌', ''),
    LogoSegments(' ', '▐', ' ▝▘ ', '▌', ''),
    LogoSegments(' ', '▐', ' ██ ', '▌', ''),
    LogoSegments('  ', '▝', '▀▀▀▀', '', '▘'),
]


# ══════════════════════════════════════════════════════════════════
# 渐变色带（5+1 行，蓝 → 紫）
# ══════════════════════════════════════════════════════════════════

GRADIENT = [
    'rgb(60,100,225)',    # 行1 — 亮蓝
    'rgb(79,112,221)',    # 行2 — 品牌蓝
    'rgb(106,98,216)',    # 行3 — 蓝紫
    'rgb(136,82,210)',    # 行4 — 紫蓝
    'rgb(165,67,203)',    # 行5 — 紫色
    'rgb(165,67,203)',    # 行6 — 底部紫
]


# ══════════════════════════════════════════════════════════════════
# 渲染逻辑
# ══════════════════════════════════════════════════════════════════

def _render_row(seg: LogoSegments, color: str, *, bg: bool = True) -> str:
    """渲染一行 Logo 文本。

    每行 = pre + left + mid(maybe bg) + right + post
    pre/post 用前景色, left/right 用前景色, mid 各字符独立
    """
    pre = Text(seg.pre)
    if seg.pre.strip():
        pre.stylize(color)

    # left
    left = Text(seg.left, style=color)

    # mid — 逐字符处理，区分前景/背景
    mid = Text()
    for ch in seg.mid:
        if ch == ' ':
            mid.append(' ')
        elif bg:
            # block 字符用前景色（用于实心区域）
            mid.append(ch, style=color)
        else:
            mid.append(ch, style=color)

    # right
    right = Text(seg.right, style=color)

    # post
    post = Text(seg.post)
    if seg.post.strip():
        post.stylize(color)

    # 拼合
    row = Text.assemble(pre, left, mid, right, post)
    return row


def build_logo(segments: list[LogoSegments]) -> Text:
    """将段列表组装为完整 Logo Text。"""
    result = Text()
    for i, seg in enumerate(segments):
        color = GRADIENT[min(i, len(GRADIENT) - 1)]
        row = _render_row(seg, color)
        if i > 0:
            result.append('\n')
        result.append(row)
    return result


# ══════════════════════════════════════════════════════════════════
# 公共 API
# ══════════════════════════════════════════════════════════════════

def get_logo_text(width: int | None = None, mode: str = 'standard') -> Text:
    """获取 eZmanbo Logo 的 Rich Text 渲染。

    Args:
        width: 终端宽度（列数），None 时自动检测
        mode: 'standard' | 'mini'

    Returns:
        Rich Text 对象
    """
    if width is None:
        try:
            width = os.get_terminal_size().columns
        except (OSError, ValueError):
            width = 80

    if mode == 'mini' or width < 50:
        segs = MINI_SEGMENTS
    else:
        segs = STANDARD_SEGMENTS

    return build_logo(segs)


class Logo:
    """Logo 组件 — 对齐 Clawd.tsx 模式。

    用法:
        logo = Logo(width=80)
        console.print(logo.render())
    """

    def __init__(self, width: int | None = None):
        self._width = width

    def render(self) -> Text:
        return get_logo_text(width=self._width)

    @property
    def height(self) -> int:
        return 6

    @property
    def cols(self) -> int:
        return 14


# ── 测试入口 ──
if __name__ == '__main__':
    console = Console()
    console.print()
    console.print(get_logo_text(mode='standard'))
    console.print()
    console.print('  eZmanbo', style='bold rgb(79,112,221)', end='')
    console.print(' — 元器件智能选型', style='dim')
