"""
eZmanbo CLI 欢迎屏幕 — 对齐 Claude Code LogoV2 设计

参考: src/components/LogoV2/LogoV2.tsx

布局模式：
  - horizontal（终端宽度 >= 70 列）: 左栏 Logo+信息 | 右栏 快捷命令
  - compact（50 <= 列 < 70）: 居中单栏圆角边框
  - condensed（列 < 50）: 极简单行 Logo + 信息
"""

from __future__ import annotations
import os
from rich.console import Console
from rich.text import Text
from rich.panel import Panel
from rich.table import Table
from rich import box

from ezmanbo_cli.theme import get_theme
from ezmanbo_cli.figures import BLACK_CIRCLE
from ezmanbo_cli.logo import get_logo_text

LAYOUT_THRESHOLD = 70
COMPACT_THRESHOLD = 50
LEFT_MAX_WIDTH = 50
MAX_USERNAME = 20

BRAND = "eZmanbo"
VERSION = "0.1.0"


# ══════════════════════════════════════════════════════════════════
# 辅助函数
# ══════════════════════════════════════════════════════════════════

def _tw() -> int:
    try:
        return os.get_terminal_size().columns
    except (OSError, ValueError):
        return 80


def _trunc_path(p: str, n: int) -> str:
    if len(p) <= n:
        return p
    if '/' not in p and '\\' not in p:
        return p[:n - 1] + '…'
    sep = '/'
    parts = p.split(sep)
    first, last = parts[0] or '', parts[-1] or ''
    # path too long → truncate middle
    avail = n - len(last) - 3
    if avail < 3:
        return sep + last[:n - 1]
    if first == '':
        result = ''
        for part in parts[1:]:
            if len(result) + len(sep) + len(part) + 3 <= n:
                result += sep + part
            else:
                result += sep + '…' + sep + last
                break
        return result
    result = first
    for part in parts[1:]:
        if len(result) + len(sep) + len(part) + (3 if part != last else 0) <= n:
            result += sep + part
        else:
            result += sep + '…' + sep + last
            break
    return result


def _welcome(name: str | None) -> str:
    if name and len(name) <= MAX_USERNAME:
        return f'Welcome back, {name}!'
    return 'Welcome to eZmanbo!'


# ══════════════════════════════════════════════════════════════════
# Condensed 模式
# ══════════════════════════════════════════════════════════════════

def print_condensed_header(
    console: Console,
    cwd: str = ".",
    model_name: str = "DeepSeek-V3",
    agent_name: str = "",
) -> None:
    theme = get_theme()
    w = _tw()

    console.print()
    logo = get_logo_text(width=w, mode='mini')
    console.print(logo)

    info = Text.assemble(
        (f'{BRAND}', f'bold {theme.brand}'),
        (f' v{VERSION}', 'dim'),
        (f'  {BLACK_CIRCLE} {model_name}', 'dim'),
    )
    console.print(info)

    if agent_name:
        console.print(Text(f'  @{agent_name}', style='dim'))
    console.print(Text(f'  {_trunc_path(cwd, w - 4)}', style='dim'))
    console.print()


# ══════════════════════════════════════════════════════════════════
# Compact 模式
# ══════════════════════════════════════════════════════════════════

def _render_compact(
    console: Console,
    welcome: str, cwd: str, model_name: str, billing: str,
    agent_name: str, username: str,
) -> None:
    theme = get_theme()
    w = _tw()

    cwd_prefix = f'@{agent_name} · ' if agent_name else ''
    cwd_display = cwd_prefix + _trunc_path(cwd, w - 12)

    inner = Table.grid(padding=(0, 1))
    inner.add_column(justify='center')
    inner.add_row(Text(welcome, style='bold'))
    inner.add_row(Text())
    inner.add_row(get_logo_text(width=w))
    inner.add_row(Text())
    inner.add_row(Text(f'{model_name} · {billing}', style='dim'))
    inner.add_row(Text(cwd_display, style='dim'))

    title = Text.assemble(
        (' ', ''),
        (BRAND, f'bold {theme.brand}'),
        (' ', ''),
    )

    panel = Panel(inner, box=box.ROUNDED, border_style=theme.brand,
                  title=title, title_align='left', padding=(1, 1))
    console.print()
    console.print(panel)
    console.print()


# ══════════════════════════════════════════════════════════════════
# Horizontal 模式
# ══════════════════════════════════════════════════════════════════

def _render_horizontal(
    console: Console,
    welcome: str, cwd: str, model_name: str, billing: str,
    agent_name: str, username: str,
) -> None:
    theme = get_theme()
    w = _tw()

    title = Text.assemble(
        ('  ', ''),
        (BRAND, f'bold {theme.brand}'),
        ('  ', 'dim'), (f'v{VERSION}', 'dim'),
        ('  ', ''),
    )

    cwd_prefix = f'@{agent_name} · ' if agent_name else ''
    cwd_display = cwd_prefix + _trunc_path(cwd, LEFT_MAX_WIDTH - 10)
    model_line = f'{model_name} · {billing}'

    # 左栏
    left = Table.grid(padding=(0, 1))
    left.add_column(justify='center')
    left.add_row(Text(welcome, style='bold'))
    left.add_row(Text())
    left.add_row(get_logo_text(width=w))
    left.add_row(Text())
    left.add_row(Text(model_line, style='dim'))
    left.add_row(Text(cwd_display, style='dim'))

    # 右栏 — 快捷命令
    right = Table.grid(padding=(0, 2))
    right.add_column(width=12, style=f'bold {theme.brand}')
    right.add_column(style='dim', min_width=25)
    right.add_row(Text('Quick Start', style=f'bold {theme.accent}'), Text(''))
    right.add_row('/help', 'Show all commands')
    right.add_row('/status', 'Check backend')
    right.add_row('/clear', 'New session')
    right.add_row('/export', 'Download BOM')
    right.add_row(Text(''), Text(''))
    right.add_row(Text('Tips', style=f'bold {theme.accent}'), Text(''))
    right.add_row(f'{BLACK_CIRCLE} 选型', 'Describe component needs')
    right.add_row(f'{BLACK_CIRCLE} 问答', 'Ask about datasheets')
    right.add_row(f'{BLACK_CIRCLE} 调整', 'Refine specifications')

    grid = Table.grid()
    grid.add_row(left, right)
    panel = Panel(grid, box=box.ROUNDED, border_style=theme.brand,
                  title=title, title_align='left', padding=(1, 2))

    console.print()
    console.print(panel)
    console.print()


# ══════════════════════════════════════════════════════════════════
# 公共 API
# ══════════════════════════════════════════════════════════════════

def print_welcome(
    console: Console | None = None,
    *,
    cwd: str = "",
    model_name: str = "DeepSeek-V3",
    billing: str = "API",
    agent_name: str = "",
    username: str = "",
    force_mode: str = "",
) -> None:
    if console is None:
        console = Console()

    w = _tw()
    welcome = _welcome(username or None)

    if force_mode:
        mode = force_mode
    elif w < COMPACT_THRESHOLD:
        mode = 'condensed'
    elif w < LAYOUT_THRESHOLD:
        mode = 'compact'
    else:
        mode = 'horizontal'

    _cwd = cwd or os.getcwd()

    if mode == 'condensed':
        print_condensed_header(console, _cwd, model_name, agent_name)
    elif mode == 'compact':
        _render_compact(console, welcome, _cwd, model_name, billing, agent_name, username)
    else:
        _render_horizontal(console, welcome, _cwd, model_name, billing, agent_name, username)


if __name__ == '__main__':
    console = Console()
    print_welcome(console, cwd=os.getcwd(), model_name='DeepSeek-V3',
                  billing='API Usage', username='Engineer')
