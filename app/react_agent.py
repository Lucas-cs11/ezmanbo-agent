"""
react_agent.py — LangChain ReAct Agent 核心

基于 LangChain 1.3 `create_agent` API，编排四个工具完成元器件选型。

工作模式：
- 单轮模式：用户输入需求 → Agent 自主决策工具调用顺序 → 返回结果
- 多轮模式：维护对话历史，支持追问（如"有国产替代吗？"）
"""

from __future__ import annotations

import os
from typing import List, Dict, Any, Optional

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from .agent_tools import AGENT_TOOLS

# ═══════════════════════════════════════════════════════════════════
# 系统提示词
# ═══════════════════════════════════════════════════════════════════

SYSTEM_PROMPT = """你是一名资深电子工程师兼元器件选型专家，拥有以下工具辅助工作：

## 可用工具

1. **search_components** — 搜索元器件数据库。输入自然语言需求（如"12V转5V 3A buck"），返回匹配器件的型号、参数、评分。**对每个需求只调用一次，不要重复搜索相同或相似的查询。**
2. **query_design_knowledge** — 检索工程知识库（设计公式、标准规范）。**仅在需要设计验证时调用1-2次。**
3. **find_alternative_parts** — 为指定型号查找替代器件（含国产替代）。**仅在用户明确要求替代方案时调用。**
4. **generate_full_report** — 生成完整的 BOM+风险评估+拓扑分析报告。**选型确认后调用一次。**

## 严格的工作流程

1. **搜索一次**：调用 `search_components` 获取候选列表。**只调用一次。**
2. **验证一次**：如需设计知识验证，调用 `query_design_knowledge`。**最多调用一次。**
3. **如果用户追问替代**：调用 `find_alternative_parts`。
4. **总结回复**：直接基于已有工具结果，用简洁中文回复用户。使用表格对比关键参数。

## 绝对规则

- ⛔ **严禁重复调用同一个工具超过2次**。如果搜索结果不理想，直接如实告知用户并给出建议，不要用不同措辞反复搜索。
- ⛔ **每次只调用一个工具**，观察结果后立即决定下一步（回复用户或调用另一个工具）。
- ⛔ **总工具调用次数不超过5次**。超过后必须回复用户。
- ⛔ 不要编造任何器件型号或参数，只使用工具返回的真实数据。
- ✅ 多轮对话时记住之前推荐过的器件型号，用户追问时直接引用。
- ✅ 回复简洁专业，用中文，关键数据用表格呈现。
"""


# ═══════════════════════════════════════════════════════════════════
# Agent 工厂
# ═══════════════════════════════════════════════════════════════════

def _build_llm() -> ChatOpenAI:
    """构建 LLM 客户端（DeepSeek via OpenAI-compatible API）。"""
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com").strip()
    model = os.getenv("OPENAI_MODEL", "deepseek-chat").strip()

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY 未设置。请在 .env 文件中配置 DeepSeek API Key。"
        )

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.0,
        max_tokens=2000,
    )


def create_component_agent():
    """创建元器件选型 ReAct Agent。

    Returns:
        一个可调用的 Agent（CompiledStateGraph），
        使用 .invoke({"messages": [...]}) 调用。
    """
    llm = _build_llm()
    return create_agent(
        model=llm,
        tools=AGENT_TOOLS,
        system_prompt=SYSTEM_PROMPT,
    )


# ═══════════════════════════════════════════════════════════════════
# 会话管理（多轮对话支持）
# ═══════════════════════════════════════════════════════════════════

# 简单内存会话存储
_sessions: Dict[str, List[Any]] = {}


def get_or_create_session(session_id: str) -> List[Any]:
    """获取或创建会话历史。"""
    if session_id not in _sessions:
        _sessions[session_id] = []
    return _sessions[session_id]


def run_agent(
    user_input: str,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """运行 Agent 处理用户输入。

    Args:
        user_input: 用户输入的自然语言需求或追问
        session_id: 会话 ID。为 None 时创建新会话（单轮模式）；
                    提供时使用已有会话历史（多轮模式）

    Returns:
        {
            "response": str,          # Agent 最终回复文本
            "messages": list,         # 完整消息历史
            "tool_calls": list,       # 工具调用记录 [{tool, args, result}, ...]
            "session_id": str,        # 会话 ID
        }
    """
    agent = create_component_agent()

    sid = session_id or os.urandom(8).hex()
    history = get_or_create_session(sid)

    # 构建消息列表
    messages = list(history) + [HumanMessage(content=user_input)]

    # 调用 Agent（限制最大递归步数）
    result = agent.invoke(
        {"messages": messages},
        config={"recursion_limit": 8},
    )

    # 提取结果
    result_messages = result.get("messages", [])
    tool_calls = []
    final_response = ""

    for msg in result_messages:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({
                    "tool": tc.get("name", "unknown"),
                    "args": tc.get("args", {}),
                    "id": tc.get("id", ""),
                })
        elif isinstance(msg, AIMessage) and msg.content and not hasattr(msg, "tool_calls"):
            final_response = msg.content
        elif isinstance(msg, AIMessage) and not msg.content and hasattr(msg, "tool_calls"):
            # AI 决定调用工具但还没得到结果
            pass

    # 找最后一个 AIMessage 的内容作为回复
    for msg in reversed(result_messages):
        if isinstance(msg, AIMessage) and msg.content and not (
            hasattr(msg, "tool_calls") and msg.tool_calls
        ):
            final_response = msg.content
            break

    # 工具调用的实际结果
    for msg in result_messages:
        if hasattr(msg, "name") and hasattr(msg, "content"):
            # ToolMessage
            for tc in tool_calls:
                if tc.get("id") == getattr(msg, "tool_call_id", None):
                    tc["result"] = str(msg.content)[:500]  # 截断过长结果

    # 更新会话历史
    new_history = list(history) + [
        HumanMessage(content=user_input),
    ]
    new_history.extend(result_messages)
    _sessions[sid] = new_history

    return {
        "response": final_response or "Agent 处理完成，请查看工具调用结果。",
        "messages": [str(m) for m in result_messages],
        "tool_calls": tool_calls,
        "session_id": sid,
    }
