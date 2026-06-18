"""
eZmanbo CLI 颜色主题 — 对齐 Claude Code 2.7.1 主题系统

参考: packages/@ant/ink/src/theme/theme-types.ts
设计原则:
  - 暗底优先（follow terminal bg），亮底可读
  - 品牌色: 蓝紫渐变（eZmanbo icon 主色调）
  - 语义色: success/error/warning 与标准终端一致
  - 支持 True Color (24-bit RGB) 和 ANSI 16 色回退
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Theme:
    """完整终端主题定义 — 约 40 个颜色键。"""

    # ── 品牌色 ──
    brand: str           # 主品牌蓝
    brand_bright: str    # 亮品牌蓝（shimmer 效果）
    brand_dim: str       # 暗品牌蓝（subtle 态）
    accent: str          # 强调色（暖橙，对齐 Claude Code 的 claude 橙）
    accent_shimmer: str  # 亮强调色

    # ── 终端基础色 ──
    text: str
    inverse_text: str
    inactive: str        # 非活跃/灰色态
    subtle: str          # 次级文字
    dim: str             # 更淡的文字
    background: str

    # ── 语义色 ──
    success: str
    error: str
    warning: str
    info: str            # 信息色

    # ── 组件色 ──
    prompt_border: str       # 输入区边框色
    prompt_border_shimmer: str
    panel_border: str        # 面板边框色
    user_message_bg: str     # 用户消息背景
    bash_border: str         # shell 执行区块边框
    memory_bg: str           # 记忆区块背景

    # ── Diff 色 ──
    diff_added: str
    diff_removed: str
    diff_added_dim: str
    diff_removed_dim: str

    # ── 限速/容量色 ──
    rate_limit_fill: str
    rate_limit_empty: str

    # ── 子代理色（多 Agent 区分） ──
    agent_red: str
    agent_blue: str
    agent_green: str
    agent_yellow: str
    agent_purple: str

    # ── Logo 色 ──
    logo_body: str      # icon 主体色（蓝紫渐变主色）
    logo_accent: str    # icon 强调细节
    logo_pin: str       # 芯片引脚色


# ══════════════════════════════════════════════════════════════════
# Dark Theme（默认暗底主题）
# ══════════════════════════════════════════════════════════════════

DARK_THEME = Theme(
    # 品牌色 — eZmanbo 蓝紫渐变
    brand='rgb(79,112,221)',          # #4F70DD 主品牌蓝
    brand_bright='rgb(120,148,240)',  # 亮蓝 shimmer
    brand_dim='rgb(55,80,160)',       # 暗蓝 subtle
    accent='rgb(215,119,87)',         # Claude 暖橙
    accent_shimmer='rgb(235,150,120)',

    # 基础
    text='rgb(228,228,228)',          # 亮灰白
    inverse_text='rgb(30,30,30)',
    inactive='rgb(136,136,136)',       # 非活跃灰
    subtle='rgb(102,102,102)',
    dim='rgb(80,80,80)',
    background='rgb(30,30,30)',

    # 语义
    success='rgb(126,192,102)',        # 终端绿
    error='rgb(235,87,87)',            # 终端红
    warning='rgb(227,180,65)',         # 终端黄
    info='rgb(100,166,227)',           # 信息蓝

    # 组件
    prompt_border='rgb(79,112,221)',
    prompt_border_shimmer='rgb(120,148,240)',
    panel_border='rgb(79,112,221)',
    user_message_bg='rgb(45,45,55)',
    bash_border='rgb(70,70,80)',
    memory_bg='rgb(40,40,50)',

    # Diff
    diff_added='rgb(126,192,102)',
    diff_removed='rgb(235,87,87)',
    diff_added_dim='rgb(80,130,65)',
    diff_removed_dim='rgb(150,50,50)',

    # 限速
    rate_limit_fill='rgb(79,112,221)',
    rate_limit_empty='rgb(60,60,60)',

    # 子代理
    agent_red='rgb(235,87,87)',
    agent_blue='rgb(100,166,227)',
    agent_green='rgb(126,192,102)',
    agent_yellow='rgb(227,180,65)',
    agent_purple='rgb(181,121,232)',

    # Logo
    logo_body='rgb(79,112,221)',      # 蓝紫主色
    logo_accent='rgb(136,82,210)',     # 偏紫强调
    logo_pin='rgb(165,67,203)',        # 引脚紫色
)


# ══════════════════════════════════════════════════════════════════
# Light Theme（亮底主题）
# ══════════════════════════════════════════════════════════════════

LIGHT_THEME = Theme(
    brand='rgb(60,85,175)',
    brand_bright='rgb(80,110,210)',
    brand_dim='rgb(100,125,215)',
    accent='rgb(185,80,55)',
    accent_shimmer='rgb(210,110,85)',

    text='rgb(30,30,30)',
    inverse_text='rgb(228,228,228)',
    inactive='rgb(120,120,120)',
    subtle='rgb(140,140,140)',
    dim='rgb(170,170,170)',
    background='rgb(245,245,245)',

    success='rgb(80,155,60)',
    error='rgb(200,50,50)',
    warning='rgb(185,140,30)',
    info='rgb(60,120,195)',

    prompt_border='rgb(60,85,175)',
    prompt_border_shimmer='rgb(80,110,210)',
    panel_border='rgb(60,85,175)',
    user_message_bg='rgb(235,235,240)',
    bash_border='rgb(210,210,210)',
    memory_bg='rgb(235,235,245)',

    diff_added='rgb(80,155,60)',
    diff_removed='rgb(200,50,50)',
    diff_added_dim='rgb(140,200,120)',
    diff_removed_dim='rgb(220,120,120)',

    rate_limit_fill='rgb(60,85,175)',
    rate_limit_empty='rgb(220,220,220)',

    agent_red='rgb(200,50,50)',
    agent_blue='rgb(60,120,195)',
    agent_green='rgb(80,155,60)',
    agent_yellow='rgb(185,140,30)',
    agent_purple='rgb(140,80,195)',

    logo_body='rgb(60,85,175)',
    logo_accent='rgb(100,60,170)',
    logo_pin='rgb(130,50,165)',
)


def get_theme(is_dark: bool = True) -> Theme:
    """获取当前主题。后续可扩展为自动检测终端明暗模式。"""
    return DARK_THEME if is_dark else LIGHT_THEME


# 默认导出实例供全局使用
THEME = get_theme(is_dark=True)
