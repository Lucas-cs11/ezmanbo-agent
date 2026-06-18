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

from .agent_tools import AGENT_TOOLS, SELECTION_TOOLS, REPLACEMENT_TOOLS, CHAT_TOOLS

# ═══════════════════════════════════════════════════════════════════
# 系统提示词（动态构建，包含 Soul + Memory）
# ═══════════════════════════════════════════════════════════════════

def _build_system_prompt(thinking_depth: str = "default", is_first_turn: bool = True) -> str:
    """构建包含 Soul 身份 + 用户记忆 + 思考深度的动态系统提示词。

    is_first_turn=True 时注入完整身份和项目回顾。
    is_first_turn=False 时仅保留名字，避免每轮重复自我介绍。
    """
    from .memory import get_soul_summary, get_user_context
    from .thinking import build_thinking_prompt

    user = get_user_context()

    if is_first_turn:
        soul = get_soul_summary()
        identity_block = f"""{soul}

{user}"""
    else:
        # 后续轮次：仅保留核心身份标识，不重复完整介绍
        identity_block = f"""你是 eZmanbo，智能电子元器件选型助理。

**重要**：这不是首次对话。不要再次自我介绍或复述自己的名字和职能。直接回应用户问题。
不要重复提及用户的项目历史，除非用户的问题直接涉及。

{user[:200] if '尚未' not in user else ''}"""

    base = f"""{identity_block}

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

- **搜索空结果 = 数据库无此器件**。看到搜索返回"未找到"/"搜索结果为空"时，必须立即停止，直接回复用户"当前数据库暂不支持该类型器件"。严禁用近义词重新搜索。
- 对同一需求最多搜索 1 次。如果搜索有结果（>0个候选），可以直接回复用户不必再搜。
- 总工具调用次数不超过 3 次。超过后必须回复用户。
- 不要编造任何器件型号或参数，只使用工具返回的真实数据。
- 多轮对话时记住之前推荐过的器件型号，用户追问时直接引用。
- 回复简洁专业，用中文，关键数据用表格呈现。
- **只在首次对话时介绍自己（名字与职能），后续轮次绝不重复自我介绍。**
- **只在首次对话或用户明确询问时提及项目历史，不要每轮都回顾。**
- 回复中不使用 emoji 表情符号，保持专业风格。
- 如果用户的需求暂时没有匹配的器件，如实告知并建议调整参数或联系管理员扩充数据库。
"""

    # 应用思考深度
    enhanced, _ = build_thinking_prompt(base, thinking_depth)
    return enhanced


# ═══════════════════════════════════════════════════════════════════
# Agent 工厂
# ═══════════════════════════════════════════════════════════════════

def _build_llm(thinking_depth: str = "default") -> ChatOpenAI:
    """构建 LLM 客户端，temperature 由思考深度控制。"""
    from .thinking import get_thinking_config

    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com").strip()
    model = os.getenv("OPENAI_MODEL", "deepseek-chat").strip()

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY 未设置。请在 .env 文件中配置 DeepSeek API Key。"
        )

    config = get_thinking_config(thinking_depth)
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=config["temperature"],
        max_tokens={"off": 1024, "default": 2048, "contemplation": 3072, "exhaustive": 4096}.get(thinking_depth, 2048),
    )



def create_component_agent(
    thinking_depth: str = "default",
    is_first_turn: bool = True,
    sub_agent: str = "selection",
):
    """创建元器件选型 ReAct Agent。

    sub_agent: "selection" | "replacement" | "chat" — 决定工具池
    """
    tool_pool = {
        "selection": SELECTION_TOOLS,
        "replacement": REPLACEMENT_TOOLS,
        "chat": CHAT_TOOLS,
    }.get(sub_agent, AGENT_TOOLS)

    llm = _build_llm(thinking_depth)
    return create_agent(
        model=llm,
        tools=tool_pool,
        system_prompt=_build_system_prompt(thinking_depth, is_first_turn),
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


# ── 幻觉检测工具 ─────────────────────────────────────────────────
import re as _re_hallu

# 常见制造商前缀模式
_MPN_PATTERN = _re_hallu.compile(
    r'\b([A-Z]{2,5}\d{2,6}[A-Z]?[-]?\d*[A-Za-z0-9]*(?:/[-A-Za-z0-9]+)?)\b'
)

# 已知厂商前缀白名单（这些厂商的型号大概率是真实的，不标记为幻觉）
_KNOWN_MFR_PREFIXES = [
    "TI", "TPS", "TL", "LM", "LMR", "INA", "OPA", "ADS", "DAC", "REF",  # TI
    "ADP", "AD", "LTC", "LT", "ADA", "ADM", "ADG",                       # ADI/LTC
    "STM", "ST1", "ST2", "LD", "TS", "L6", "L78", "L79",                 # ST（精确前缀）
    "MCP", "MIC", "PIC", "DSPIC", "KSZ",                                  # Microchip
    "IR", "IRF", "AU",                                                     # Infineon/IR
    "MAX", "DS",                                                            # Maxim
    "NCP", "NCV", "NCS",                                                   # onsemi
    "ISL", "ICL",                                                          # Renesas/Intersil
    "MP", "MPQ", "NB",                                                     # MPS
    "RT", "RTQ",                                                           # Richtek
    "XL",                                                                  # XLSemi
    "SY", "RY",                                                            # Silergy
    "SGM", "SG",                                                           # SGMICRO
]


def _validate_part_numbers_in_response(response: str) -> str:
    """扫描 Agent 回复中的型号，校验是否存在于数据库中。

    对不在已知厂商白名单也不在数据库中的疑似编造型号追加警告。
    """
    try:
        from .ezplm_client import _load_parts
        known_parts = _load_parts()
        known_mpns = {p.get("part_number", "").upper() for p in known_parts}
    except Exception:
        return response

    # 常见非型号缩写
    _noise = {"API", "JSON", "HTTP", "UUID", "URL", "HTML", "CSS",
              "BOM", "EMI", "PCB", "LDO", "PMIC", "MOSFET", "ESR",
              "MTBF", "FMEA", "RPN", "PPAP", "PCN", "EOL", "LTB",
              "AVL", "PDN", "GAN", "FET", "PWM", "PFM", "PLL", "ADC"}

    found_mpns = set()
    for m in _MPN_PATTERN.finditer(response):
        mpn = m.group(1).upper()
        if mpn in _noise or len(mpn) < 5:
            continue
        # 已知厂商前缀 → 信任，不检查
        is_known_mfr = any(mpn.startswith(p.upper().replace(" ", ""))
                           for p in _KNOWN_MFR_PREFIXES)
        if is_known_mfr:
            continue
        # eZ-PLM 缓存中的已知型号 → 信任
        if mpn in known_mpns:
            continue
        # 剩余 → 疑似幻觉
        found_mpns.add(m.group(1))

    if found_mpns:
        warning = (
            "\n\n---\n"
            "> ⚠ **数据验证提示**：以下型号在当前数据库中未检索到匹配记录，"
            "可能为 LLM 推测生成，请通过实际数据源确认后再采纳：\n"
        )
        for mpn in sorted(found_mpns):
            warning += f"> - `{mpn}`\n"
        response += warning

    return response


def run_agent(
    user_input: str,
    session_id: Optional[str] = None,
    thinking_depth: str = "default",
) -> Dict[str, Any]:
    """运行 Agent 处理用户输入。

    """
    sid = session_id or os.urandom(8).hex()
    history = get_or_create_session(sid)

    # 检测是否首次对话（空历史 = 首次）
    is_first_turn = len(history) == 0
    agent = create_component_agent(thinking_depth, is_first_turn)

    # 构建消息列表
    messages = list(history) + [HumanMessage(content=user_input)]

    # 调用 Agent（限制最大递归步数，每轮 think+tool+observe 约 3 步）
    result = agent.invoke(
        {"messages": messages},
        config={"recursion_limit": 25},
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

    # ── 幻觉检测：校验回复中的器件型号是否存在于数据库 ─────────
    if final_response:
        final_response = _validate_part_numbers_in_response(final_response)

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
