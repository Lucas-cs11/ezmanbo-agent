"""
tool_schema.py — 标准化工具接口（参照 Claude Code Tool 接口）

每个工具定义统一包含：
  name        — 工具标识符
  description — 自然语言描述（给 LLM 阅读）
  pool        — 工具所属池：selection / replacement / common
  call()      — 执行入口
"""

from __future__ import annotations

from typing import Protocol, List, Dict, Any, Optional, Literal
from dataclasses import dataclass, field

ToolPool = Literal["selection", "replacement", "common"]


class ToolLike(Protocol):
    """工具最小接口 — 兼容 LangChain @tool 装饰器。"""
    name: str
    description: str

    def __call__(self, *args: Any, **kwargs: Any) -> str: ...


@dataclass
class ToolMeta:
    """工具元数据 — 注册时自动提取。"""
    name: str
    description: str
    pool: ToolPool = "common"
    tool_obj: Optional[ToolLike] = None


# ── 工具注册表 ────────────────────────────────────────────────

_tool_registry: List[ToolMeta] = []


def register_tool(tool: ToolLike, pool: ToolPool = "common") -> ToolMeta:
    """注册工具到全局注册表。"""
    meta = ToolMeta(
        name=tool.name,
        description=tool.description or "",
        pool=pool,
        tool_obj=tool,
    )
    _tool_registry.append(meta)
    return meta


def get_tools_by_pool(pool: ToolPool) -> List[ToolLike]:
    """获取指定池的工具列表。"""
    return [m.tool_obj for m in _tool_registry if m.pool in (pool, "common") and m.tool_obj is not None]


def get_all_tools() -> List[ToolLike]:
    """获取所有已注册工具。"""
    return [m.tool_obj for m in _tool_registry if m.tool_obj is not None]


def get_tool_names_by_pool(pool: ToolPool) -> List[str]:
    """获取指定池的工具名列表。"""
    return [m.name for m in _tool_registry if m.pool in (pool, "common")]


def get_tool_registry() -> List[ToolMeta]:
    """获取完整注册表（用于调试和文档）。"""
    return list(_tool_registry)


# ── 子Agent配置 ───────────────────────────────────────────────

@dataclass
class SubAgentConfig:
    """子Agent配置 — 工具池 + 系统提示词前缀。"""
    name: str
    pool: ToolPool
    system_prefix: str
    max_tool_calls: int = 5

SELECTION_AGENT = SubAgentConfig(
    name="selection",
    pool="selection",
    system_prefix="你是 eZmanbo 选型子Agent，专注于元器件的搜索、评估与推荐。",
    max_tool_calls=5,
)

REPLACEMENT_AGENT = SubAgentConfig(
    name="replacement",
    pool="replacement",
    system_prefix="你是 eZmanbo 替代查找子Agent，专注于为已有器件查找兼容替代方案。",
    max_tool_calls=4,
)

CHAT_AGENT = SubAgentConfig(
    name="chat",
    pool="common",
    system_prefix="你是 eZmanbo 对话Agent，处理一般性咨询与领域外问答。不主动触发选型。",
    max_tool_calls=2,
)

SUB_AGENTS = {
    "selection": SELECTION_AGENT,
    "replacement": REPLACEMENT_AGENT,
    "chat": CHAT_AGENT,
}
