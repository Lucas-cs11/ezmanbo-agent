"""
eZmanbo CLI 底部状态栏 — 对齐 Claude Code StatusLine + BuiltinStatusLine

参考:
  - src/components/StatusLine.tsx（主状态栏容器 + CachePill）
  - src/components/BuiltinStatusLine.tsx（内置状态数据行）

结构（双行，与 Claude Code 一致）：
  上行: [模型名] │ Context N% (Nk/NM) │ Session N% HH:MM │ $0.0012
  下行: 用户自定义状态（通过 /status 命令配置，预留）

设计模式对齐：
  - 内置行仅在 statusLineEnabled=True 时显示
  - 分隔符使用 U+2502 │
  - 窄终端（< 60 列）隐藏 token 精确计数
  - 限速倒计时自动刷新
"""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from rich.text import Text
from rich.console import Console

from ezmanbo_cli.theme import Theme, get_theme


# ══════════════════════════════════════════════════════════════════
# StatusInfo — 状态栏数据容器（对齐 buildStatusLineCommandInput）
# ══════════════════════════════════════════════════════════════════

@dataclass
class StatusInfo:
    """状态栏需要展示的所有数据。

    对齐 Claude Code 的 StatusLineCommandInput 结构。
    """
    # 模型
    model_id: str = "deepseek-v3"
    model_display: str = "DeepSeek-V3"

    # Context 窗口
    used_tokens: int = 0
    context_window_size: int = 0
    context_used_pct: float = 0.0

    # 费率
    total_cost_usd: float = 0.0

    # 会话限速（5小时滚动窗口）
    session_utilization: float = 0.0
    session_resets_at: float = 0.0  # epoch seconds

    # 周限速
    weekly_utilization: float = 0.0
    weekly_resets_at: float = 0.0  # epoch seconds

    # 缓存
    cache_hit_rate: Optional[float] = None
    cache_ttl_remaining: Optional[float] = None  # seconds

    # 会话
    session_name: str = ""

    # 工作区
    cwd: str = ""
    project_dir: str = ""

    # 额外
    extra_fields: Dict[str, str] = field(default_factory=dict)


# ══════════════════════════════════════════════════════════════════
# 格式化辅助（对齐 BuiltinStatusLine 的 formatCountdown / formatTokens）
# ══════════════════════════════════════════════════════════════════

def _format_tokens(n: int) -> str:
    """Token 计数格式化: 50000 → '50k', 1000000 → '1M'。"""
    if n >= 1_000_000:
        return f'{n / 1_000_000:.1f}M'
    if n >= 1_000:
        return f'{n / 1_000:.0f}k'
    return str(n)


def _format_countdown(epoch_seconds: float) -> str:
    """倒计时格式化: 返回 '3h12m', '45m', 'now'。"""
    diff = epoch_seconds - time.time()
    if diff <= 0:
        return 'now'
    days = int(diff // 86400)
    hours = int((diff % 86400) // 3600)
    minutes = int((diff % 3600) // 60)
    if days >= 1:
        return f'{days}d{hours}h'
    if hours >= 1:
        return f'{hours}h{minutes}m'
    return f'{minutes}m'


def _format_cost(usd: float) -> str:
    """成本格式化: $0.0012, $1.50, $12.34。"""
    if usd < 0.01:
        return f'${usd:.4f}'
    if usd < 1:
        return f'${usd:.3f}'
    return f'${usd:.2f}'


def _format_cache_ttl(remaining_sec: float) -> str:
    """缓存 TTL 格式化: 60:00 → mm:ss。"""
    if remaining_sec <= 0:
        return 'exp'
    m = int(remaining_sec // 60)
    s = int(remaining_sec % 60)
    return f'{m:02d}:{s:02d}'


# ══════════════════════════════════════════════════════════════════
# 渲染函数
# ══════════════════════════════════════════════════════════════════

def _sep() -> Text:
    """分隔符 │（对齐 BuiltinStatusLine.Separator）。"""
    return Text(' \u2502 ', style='dim')


def render_status_line(
    info: StatusInfo,
    width: int = 80,
    show_builtin: bool = True,
    show_cache: bool = True,
) -> Text:
    """渲染底部状态栏上行。

    对齐:
      - BuiltinStatusLine: 模型 | Context | Session | Weekly | Cost
      - CachePill: Cache NN% MM:SS

    Args:
        info: 状态数据
        width: 终端宽度（列数）
        show_builtin: 是否显示内置状态行
        show_cache: 是否显示缓存柱

    Returns:
        Rich Text 对象
    """
    theme = get_theme()
    narrow = width < 60
    result = Text()

    if not show_builtin:
        return result

    # ── 模型名（取前两个词，对齐 BuiltinStatusLine.shortModel） ──
    model_parts = info.model_display.split()
    short_model = ' '.join(model_parts[:2]) if len(model_parts) >= 2 else info.model_display
    result.append(short_model, style='default')

    # ── Context N% (Nk/NM) ──
    result.append(_sep())
    result.append('Context ', style='dim')
    result.append(f'{int(info.context_used_pct)}%', style='default')
    if not narrow and info.used_tokens > 0:
        token_display = f'{_format_tokens(info.used_tokens)}/{_format_tokens(info.context_window_size)}'
        result.append(f' ({token_display})', style='dim')

    # ── Session 限速（5 小时窗口） ──
    if info.session_utilization > 0:
        result.append(_sep())
        result.append('Session ', style='dim')
        pct = int(info.session_utilization * 100)
        color = 'green' if pct < 75 else 'yellow' if pct < 95 else 'red'
        result.append(f'{pct}%', style=color)
        if not narrow and info.session_resets_at > 0:
            result.append(f' {_format_countdown(info.session_resets_at)}', style='dim')

    # ── Weekly 限速 ──
    if info.weekly_utilization > 0:
        result.append(_sep())
        result.append('Weekly ', style='dim')
        pct = int(info.weekly_utilization * 100)
        color = 'green' if pct < 75 else 'yellow' if pct < 95 else 'red'
        result.append(f'{pct}%', style=color)
        if not narrow and info.weekly_resets_at > 0:
            result.append(f' {_format_countdown(info.weekly_resets_at)}', style='dim')

    # ── Cost ──
    if info.total_cost_usd > 0:
        result.append(_sep())
        result.append(_format_cost(info.total_cost_usd), style='default')

    # ── Cache Pill（对齐 StatusLine.CachePill） ──
    if show_cache and info.cache_hit_rate is not None:
        result.append(Text('  Cache ', style='dim'))
        hit_color = 'green' if info.cache_hit_rate >= 50 else 'dim'
        result.append(f'{int(info.cache_hit_rate)}%', style=hit_color)

        if info.cache_ttl_remaining is not None:
            ttl_text = _format_cache_ttl(info.cache_ttl_remaining)
            remaining_min = info.cache_ttl_remaining / 60
            if remaining_min <= 0:
                ttl_color = 'dim'
            elif remaining_min < 20:
                ttl_color = 'green'
            elif remaining_min < 40:
                ttl_color = 'yellow'
            else:
                ttl_color = 'red'
            result.append(f' {ttl_text}', style=ttl_color)

    return result


def print_status_line(
    console: Console,
    info: StatusInfo,
    status_line_cmd_output: str = "",
) -> None:
    """在终端底部打印状态栏。

    对齐 StatusLine 的双行结构:
      行1: render_status_line (内置状态)
      行2: status_line_cmd_output (用户自定义命令输出)
    """
    w = console.width

    # 上行
    builtin = render_status_line(info, width=w, show_builtin=True)
    console.print(builtin)

    # 下行（用户 shell 命令输出，预留）
    if status_line_cmd_output:
        console.print(Text(status_line_cmd_output, style='dim'))


# ── 测试入口 ──
if __name__ == '__main__':
    console = Console()
    info = StatusInfo(
        model_id='deepseek-v3',
        model_display='DeepSeek-V3 0324',
        used_tokens=45000,
        context_window_size=128000,
        context_used_pct=35.0,
        total_cost_usd=0.0042,
        session_utilization=0.42,
        session_resets_at=time.time() + 7200,
        weekly_utilization=0.15,
        weekly_resets_at=time.time() + 86400 * 3,
        cache_hit_rate=68.0,
        cache_ttl_remaining=2400,  # 40 min
        cwd='/home/engineer/project',
    )

    console.print()
    console.print('─' * console.width, style='dim')
    console.print(render_status_line(info, width=console.width))
    console.print('─' * console.width, style='dim')
