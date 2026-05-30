import os
import requests
from typing import List, Dict, Any, Optional

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")


def call_openai_chat(messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.0) -> str:
    """Call OpenAI-compatible /v1/chat/completions endpoint and return assistant text.

    Requires OPENAI_API_KEY in env. Base URL can be overridden via OPENAI_BASE_URL.
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set in environment")
    model = model or OPENAI_MODEL
    url = OPENAI_BASE_URL.rstrip("/") + "/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 800,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # support both choices[0].message.content and choices[0].text
    if "choices" in data and len(data["choices"]) > 0:
        choice = data["choices"][0]
        if "message" in choice and "content" in choice["message"]:
            return choice["message"]["content"]
        if "text" in choice:
            return choice["text"]
    return ""


def score_part_with_llm(
    requirement_text: str,
    part_info: Dict[str, Any],
    reference_designs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """用 LLM 对器件进行应用场景适配度和设计成熟度评分。

    Args:
        requirement_text: 用户原始需求文本
        part_info: 器件关键参数字典（part_number, manufacturer, description, Vin, Iout, temp）
        reference_designs: EZ-PLM reference-designs API 返回的设计列表

    Returns:
        {"application_score": 0-100, "design_risk_score": 0-100, "reasoning": "..."}
        失败时返回空 dict（调用方应回退到规则评分）
    """
    import json as _json

    # 构建器件信息段
    pn = part_info.get("part_number", "未知")
    mfr = part_info.get("manufacturer") or "-"
    desc = part_info.get("description") or "-"
    vin = f"{part_info.get('vin_min', '?')}–{part_info.get('vin_max', '?')}V"
    iout = f"{part_info.get('iout_max', '?')}A"
    temp = f"{part_info.get('temp_min', '?')}–{part_info.get('temp_max', '?')}°C"

    # 构建参考设计段（最多 3 条，description 截取前 300 字）
    rd_lines = []
    for i, rd in enumerate(reference_designs[:3], 1):
        name = rd.get("name", "")
        desc_rd = (rd.get("description") or "").strip()[:300]
        rd_lines.append(f"{i}. 【{name}】{desc_rd}")
    rd_text = "\n".join(rd_lines) if rd_lines else "（无参考设计数据）"

    system = (
        "你是一名资深电子工程师，专注于模拟/电源电路元器件选型评估。"
        "你的回答必须严格基于提供的参考设计内容，不得凭空捏造。"
        "只返回 JSON，不要任何额外文字。"
    )
    user = (
        f"## 选型需求\n{requirement_text}\n\n"
        f"## 待评估器件\n"
        f"型号：{pn}（{mfr}）\n"
        f"描述：{desc}\n"
        f"电气参数：输入 {vin}，输出电流 {iout}，温度范围 {temp}\n\n"
        f"## 参考设计案例\n{rd_text}\n\n"
        "## 评分要求\n"
        "从以下两个维度打分（0-100整数）：\n"
        "1. application_score：该器件在参考设计中体现的应用场景与当前选型需求的匹配程度\n"
        "2. design_risk_score：参考设计体现的器件可靠性与工程成熟度（100=非常成熟可靠）\n\n"
        "只返回 JSON（不要 markdown 代码块）：\n"
        '{"application_score": 85, "design_risk_score": 78, "reasoning": "一句话说明"}'
    )
    try:
        content = call_openai_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.0,
        )
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            result = _json.loads(content[start:end + 1])
            # 强制 clamp 到 [0, 100]
            for key in ("application_score", "design_risk_score"):
                if key in result:
                    result[key] = max(0.0, min(100.0, float(result[key])))
            return result
    except Exception as e:
        from .log_util import warn_swallow; warn_swallow("llm_client", e, "score_part")
    return {}


def parse_requirement_with_llm(text: str) -> Dict[str, Any]:
    """Ask the LLM to parse a natural language requirement into RequirementConstraints-like JSON.

    Returns a dict with keys matching RequirementConstraints where available.
    """
    system = (
        "你是一个结构化信息提取助手。接收电子工程师的元器件选型需求，输出 JSON 格式的字段。\n"
        "请只输出 JSON，不要额外说明。字段示例：application, category, topology, input_voltage_nominal_v, output_voltage_v, output_current_a, temperature_min_c, temperature_max_c, grade, preferences (list)。"
    )
    user = f"解析以下需求为 JSON：\n{str(text)}\n要求返回满足字段示例，只返回 JSON。"
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    content = call_openai_chat(messages)
    # attempt to find JSON in content
    import json

    try:
        # strip surrounding text
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            jtxt = content[start : end + 1]
            return json.loads(jtxt)
        # fallback parse whole
        return json.loads(content)
    except Exception:
        return {"raw_llm": content}

