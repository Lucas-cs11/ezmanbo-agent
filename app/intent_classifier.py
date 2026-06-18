"""
intent_classifier.py — 规则快筛 + LLM 终判 混合意图分类器

架构：
  1. 规则快筛（毫秒级）：最明显的 case（问候/空输入/明确的电压转换模式）
  2. LLM 终判（~1s）：规则无法确定的 case，交给 LLM 理解领域、判断意图

输出：
  Intent = "selection" | "chat" | "adjustment" | "clarify"

核心理念：规则只做"肯定对"的快速路径，其余交给 LLM 理解上下文。
"""

from __future__ import annotations

import json
import re
from typing import Literal, Optional

Intent = Literal["selection", "chat", "adjustment", "clarify"]


# ══════════════════════════════════════════════════════════════════
# 规则快筛 — 只做最明显的判断（不会误判的 case）
# ══════════════════════════════════════════════════════════════════

# 明确的电压转换模式: "12V转5V", "5V step-down to 3.3V"
_VOLTAGE_CONVERSION = re.compile(
    r"(\d+\.?\d*)\s*[vV]\s*(?:转|→|->|to|转换成|转换到|降[压到]|升[压到])\s*(\d+\.?\d*)\s*[vV]"
)

# DC-DC 拓扑关键词（用于快速确认选型意图）
_DCDC_TOPOLOGY = [
    "buck", "boost", "ldo", "dc-dc", "dc_dc", "dcdc",
    "降压", "升压", "稳压", "电源芯片", "电源模块", "转换器",
    "converter", "regulator",
]

# 明确非选型信号
_CHAT_SIGNALS = [
    "你好", "hello", "hi", "谢谢", "好的", "ok", "明白了",
    "什么是", "怎么", "如何", "为什么",
    "帮助", "help", "功能", "能做什么",
]

# 选型调整信号
_ADJUSTMENT_SIGNALS = [
    "换个", "换成", "替代", "代替", "改一下", "改成",
    "调整", "修改", "国产替代", "有没有其他",
]


def _is_fast_chat(text: str) -> bool:
    """最明显的纯对话：问候、超短、纯问句。"""
    t = text.strip().lower()
    if len(t) <= 3:
        return True
    for s in _CHAT_SIGNALS:
        if s in t:
            return True
    if t.endswith("?") or t.endswith("？"):
        return True
    return False


def _is_fast_selection(text: str) -> bool:
    """最明确的选型信号：含电压转换 + DC-DC 拓扑关键词。"""
    t = text.lower()
    has_conversion = bool(_VOLTAGE_CONVERSION.search(text))
    has_topology = any(kw in t for kw in _DCDC_TOPOLOGY)
    return has_conversion and has_topology


def _is_fast_adjustment(text: str) -> bool:
    """明显的调整信号。"""
    t = text.lower()
    return any(s in t for s in _ADJUSTMENT_SIGNALS)


# ══════════════════════════════════════════════════════════════════
# LLM 终判 — 规则无法确定时调用
# ══════════════════════════════════════════════════════════════════

_CLASSIFY_PROMPT = """你是电子元器件选型系统的意图分类器。

本系统对接 eZ-PLM 元器件数据库，支持多种电子元器件的搜索与选型。

请将用户输入分类为：
- selection: 用户要进行元器件选型（含具体参数需求，如电压/电流/封装等）
- adjustment: 用户要修改已有选型结果
- chat: 普通对话、技术问答、问候、闲聊

返回纯 JSON（不要 markdown 代码块）：
{
  "intent": "selection|adjustment|chat",
  "reasoning": "简短判断理由（10字以内）",
  "device_category": "用户询问的器件类型（如 buck/ldo/mosfet/op_amp/current_sense 等）"
}

示例：
输入: "为一款电机驱动器选择高边电流检测放大器。母线电压最高48V，采样电流0-30A"
输出: {"intent": "selection", "reasoning": "电流检测放大器选型需求", "device_category": "current_sense_amplifier"}

输入: "需要5V转3.3V的LDO 输出500mA"
输出: {"intent": "selection", "reasoning": "明确的LDO选型需求", "device_category": "ldo"}

输入: "Buck转换器用在哪里比较好"
输出: {"intent": "chat", "reasoning": "技术问答", "device_category": "buck"}

输入: "你好"
输出: {"intent": "chat", "reasoning": "问候", "device_category": "none"}"""


def _llm_classify(user_input: str) -> dict:
    """调用 LLM 进行意图分类，返回结构化 JSON。"""
    import os
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
    model = os.getenv("OPENAI_MODEL", "deepseek-chat")

    if not api_key:
        return {"intent": "chat", "reasoning": "no LLM config", "device_category": "unknown", "is_in_scope": True}

    import urllib.request, urllib.error

    url = base_url.rstrip("/") + "/v1/chat/completions"
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": _CLASSIFY_PROMPT},
            {"role": "user", "content": user_input},
        ],
        "temperature": 0.0,
        "max_tokens": 200,
    }).encode()

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        content = data["choices"][0]["message"]["content"].strip()

        # 清理可能的 markdown 代码块包裹
        if content.startswith("```"):
            content = re.sub(r"^```(?:json)?\s*\n?", "", content)
            content = re.sub(r"\n?```\s*$", "", content)

        result = json.loads(content)
        return {
            "intent": result.get("intent", "chat"),
            "reasoning": result.get("reasoning", ""),
            "device_category": result.get("device_category", "unknown"),
        }
    except Exception:
        return {"intent": "chat", "reasoning": "LLM error", "device_category": "unknown"}


# ── 最后一次 LLM 分类详情，供调用方获取附加信息 ──────────────
_last_classification: dict = {}


def get_last_classification() -> dict:
    """获取最近一次 LLM 分类的详细信息。"""
    return _last_classification.copy()


# ══════════════════════════════════════════════════════════════════
# 主分类函数
# ══════════════════════════════════════════════════════════════════

def classify(
    user_input: str,
    has_active_selection: bool = False,
    accumulated_input: str = "",
) -> Intent:
    """混合意图分类：规则快筛 → LLM 终判。

    Args:
        user_input: 用户输入文本
        has_active_selection: 当前会话是否已有选型结果
        accumulated_input: 跨轮累积的约束文本

    Returns:
        "selection" | "chat" | "adjustment" | "clarify"
    """
    text = user_input.strip()
    merged = (accumulated_input + "; " + text) if accumulated_input else text

    # ── Step 1: 规则快筛（毫秒级，只做不会误判的 case） ──
    if _is_fast_chat(text):
        return "chat"

    if _is_fast_selection(merged):
        # 明确的 DC-DC 选型模式 → 检查约束完整性
        from .constraint_checker import extract_constraints, check_completeness
        constraints = extract_constraints(merged)
        is_complete, missing_p0, _ = check_completeness(constraints)
        if not is_complete:
            return "clarify"
        return "selection"

    if has_active_selection and _is_fast_adjustment(text):
        return "adjustment"

    # ── Step 2: LLM 终判（~1s，处理规则无法确定的 case） ──
    result = _llm_classify(merged if accumulated_input else text)
    global _last_classification
    _last_classification = result

    llm_intent = result.get("intent", "chat")

    # 选型意图 → 检查约束完整性
    if llm_intent == "selection":
        from .constraint_checker import extract_constraints, check_completeness
        constraints = extract_constraints(merged)
        is_complete, missing_p0, _ = check_completeness(constraints)
        if not is_complete:
            return "clarify"
        return "selection"

    return llm_intent  # chat 或 adjustment


# ══════════════════════════════════════════════════════════════════
# 兼容旧接口
# ══════════════════════════════════════════════════════════════════

def classify_with_llm(user_input: str, has_active_selection: bool = False) -> Intent:
    """旧接口兼容 — 直接走 LLM 分类。"""
    result = _llm_classify(user_input)
    return result.get("intent", "chat")  # type: ignore[return-value]


def extract_adjustment(user_input: str, current_constraints: Optional[dict] = None) -> dict:
    """从调整语句中提取需要修改的约束参数。"""
    changes: dict = {}

    if re.search(r"车规|automotive", user_input, re.I):
        changes["grade"] = "automotive"
    elif re.search(r"非车规|工业级|industrial|不要车规", user_input, re.I):
        changes["grade"] = "industrial"

    if re.search(r"国产|国产化|domestic|矽力杰|圣邦微|南芯", user_input, re.I):
        changes["preferences"] = ["domestic_alternative"]

    m = re.search(r"(\d+\.?\d*)\s*[aA]\b", user_input)
    if m:
        changes["output_current_a"] = float(m.group(1))

    m = re.search(r"(\d+)\s*[vV]\s*(?:转|→|->|to|输出)", user_input)
    if m:
        changes["output_voltage_v"] = float(m.group(1))

    m = re.search(r"(-?\d+)\s*[~\-到至]\s*(-?\d+)\s*[°℃C]", user_input)
    if m:
        changes["temperature_min_c"] = float(m.group(1))
        changes["temperature_max_c"] = float(m.group(2))

    return changes
