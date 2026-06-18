"""
eZmanbo CLI UI — Claude Code 风格终端界面

迁移自 Claude Code 2.7.1 的核心 UI 设计模式：
  - LogoV2 风格欢迎屏幕（compact / horizontal 自适应）
  - BuiltinStatusLine 风格底部状态栏
  - Spinner 动画框架
  - 完整颜色主题系统
  - Unicode 符号常量体系
"""

from ezmanbo_cli.theme import THEME, Theme
from ezmanbo_cli.figures import (
    BLACK_CIRCLE, BULLET_OPERATOR, UP_ARROW, DOWN_ARROW,
    LIGHTNING_BOLT, PLAY_ICON, PAUSE_ICON, REFRESH_ARROW,
    DIAMOND_OPEN, DIAMOND_FILLED, BLOCKQUOTE_BAR, FLAG_ICON,
)
from ezmanbo_cli.logo import Logo, get_logo_text
from ezmanbo_cli.header import print_welcome, print_condensed_header
from ezmanbo_cli.statusline import render_status_line, StatusInfo

__all__ = [
    "THEME", "Theme",
    "BLACK_CIRCLE", "BULLET_OPERATOR", "UP_ARROW", "DOWN_ARROW",
    "LIGHTNING_BOLT", "PLAY_ICON", "PAUSE_ICON", "REFRESH_ARROW",
    "DIAMOND_OPEN", "DIAMOND_FILLED", "BLOCKQUOTE_BAR", "FLAG_ICON",
    "Logo", "get_logo_text",
    "print_welcome", "print_condensed_header",
    "render_status_line", "StatusInfo",
]
