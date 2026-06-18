"""
eZmanbo CLI 符号常量 — 对齐 Claude Code src/constants/figures.ts

Unicode 特殊字符统一管理。macOS 使用 ⏺ 替代 ● 以获得更好的垂直对齐。
"""

import sys

# ── 基础符号 ──
BLACK_CIRCLE: str = '\u23fa' if sys.platform == 'darwin' else '\u25cf'   # ⏺ / ●
BULLET_OPERATOR: str = '\u2219'   # ∙
UP_ARROW: str = '\u2191'          # ↑ — 滚动提示 / 升级通知
DOWN_ARROW: str = '\u2193'        # ↓ — 滚动提示
LIGHTNING_BOLT: str = '\u21af'    # ↯ — 快速模式指示
TEARDROP_ASTERISK: str = '\u273b' # ✻ — 装饰用星标

# ── 努力/强度级别 ──
EFFORT_LOW: str = '\u25cb'        # ○
EFFORT_MEDIUM: str = '\u25d0'     # ◐
EFFORT_HIGH: str = '\u25cf'       # ●
EFFORT_XHIGH: str = '\u29bf'      # ⦿
EFFORT_MAX: str = '\u25c9'        # ◉

# ── 媒体/触发状态 ──
PLAY_ICON: str = '\u25b6'         # ▶
PAUSE_ICON: str = '\u23f8'        # ⏸

# ── MCP 订阅指示 ──
REFRESH_ARROW: str = '\u21bb'     # ↻ — 资源更新
CHANNEL_ARROW: str = '\u2190'     # ← — 入站消息
INJECTED_ARROW: str = '\u2192'    # → — 跨会话注入

# ── Review 状态 ──
DIAMOND_OPEN: str = '\u25c7'      # ◇ — 运行中
DIAMOND_FILLED: str = '\u25c6'    # ◆ — 完成/失败

# ── 标志/标记 ──
FLAG_ICON: str = '\u2691'         # ⚑ — 问题标记
REFERENCE_MARK: str = '\u203b'    # ※ — 摘要回顾标记

# ── 文本装饰 ──
BLOCKQUOTE_BAR: str = '\u258e'    # ▎ — 左四分之一块，引用前缀
HEAVY_HORIZONTAL: str = '\u2501'  # ━ — 粗水平框线

# ── Box-drawing（圆角边框集） ──
BOX_ROUND_TL: str = '\u256d'      # ╭ 左上
BOX_ROUND_TR: str = '\u256e'      # ╮ 右上
BOX_ROUND_BL: str = '\u2570'      # ╰ 左下
BOX_ROUND_BR: str = '\u256f'      # ╯ 右下
BOX_VERTICAL: str = '\u2502'      # │ 竖线
BOX_HORIZONTAL: str = '\u2500'    # ─ 横线
BOX_SEPARATOR: str = '\u2502'     # │ 分隔符（同竖线）

# ── Block elements（用于 Logo 构造） ──
FULL_BLOCK: str = '\u2588'        # █
UPPER_HALF: str = '\u2580'        # ▀
LOWER_HALF: str = '\u2584'        # ▄
LEFT_HALF: str = '\u258c'         # ▌
RIGHT_HALF: str = '\u2590'        # ▐
LEFT_78: str = '\u258e'           # ▎
RIGHT_78: str = '\u2595'          # ▕

# ── 几何形状 ──
LOWER_RIGHT_QUAD: str = '\u2597'  # ▗
LOWER_LEFT_QUAD: str = '\u2596'   # ▖
UPPER_LEFT_QUAD: str = '\u2598'   # ▘
UPPER_RIGHT_QUAD: str = '\u259d'  # ▝
