import os
import json as _json
import requests
from typing import List, Dict, Any, Optional

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# ── Function Calling Tool Schema（P2：结构化需求提取）───────────

REQUIREMENT_TOOLS = [{
    "type": "function",
    "function": {
        "name": "extract_requirement",
        "description": "从自然语言中提取电子元器件选型的结构化需求参数",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["dc_dc_converter", "ldo", "mosfet", "op_amp", "interface_ic", "other"],
                    "description": "器件类别"
                },
                "topology": {
                    "type": "string",
                    "enum": ["buck", "boost", "buck_boost", "ldo", "other"],
                    "description": "电路拓扑，DC-DC 必填，LDO 填 ldo"
                },
                "application": {
                    "type": "string",
                    "description": "应用场景描述，如'车载电源''通信设备'"
                },
                "input_voltage_nominal_v": {
                    "type": "number",
                    "description": "标称输入电压 (V)"
                },
                "input_voltage_min_v": {
                    "type": "number",
                    "description": "最小输入电压 (V)"
                },
                "input_voltage_max_v": {
                    "type": "number",
                    "description": "最大输入电压 (V)"
                },
                "output_voltage_v": {
                    "type": "number",
                    "description": "输出电压 (V)"
                },
                "output_current_a": {
                    "type": "number",
                    "description": "输出电流 (A)，注意 mA 需转换为 A"
                },
                "temperature_min_c": {
                    "type": "number",
                    "description": "最低工作温度 (°C)"
                },
                "temperature_max_c": {
                    "type": "number",
                    "description": "最高工作温度 (°C)"
                },
                "grade": {
                    "type": "string",
                    "enum": ["automotive", "industrial", "commercial", "military"],
                    "description": "器件等级，注意'非车规''不要车规'意味着 industrial"
                },
                "package_preference": {
                    "type": "string",
                    "description": "封装偏好，如'SOT-23''QFN'"
                },
                "preferences": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "偏好列表，如 domestic_alternative, low_cost, high_efficiency, small_package"
                }
            },
            "required": ["category", "topology", "output_voltage_v", "output_current_a"]
        }
    }
}]


def call_openai_chat(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.0,
    tools: Optional[List[dict]] = None,
    tool_choice: Optional[str] = None,
) -> dict:
    """Call OpenAI-compatible /v1/chat/completions endpoint.

    Returns: {"content": str, "tool_calls": list} — content 可能为空（tool call 模式）。
    """
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY not set in environment")
    model = model or OPENAI_MODEL
    url = OPENAI_BASE_URL.rstrip("/") + "/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload: dict = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 800,
    }
    if tools:
        payload["tools"] = tools
    if tool_choice:
        payload["tool_choice"] = tool_choice

    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    result: dict = {"content": "", "tool_calls": []}
    if "choices" in data and len(data["choices"]) > 0:
        choice = data["choices"][0]
        msg = choice.get("message", {})
        result["content"] = msg.get("content", "") or ""
        result["tool_calls"] = msg.get("tool_calls", [])
    return result


def call_openai_chat_text(messages: List[Dict[str, str]], model: Optional[str] = None, temperature: float = 0.0) -> str:
    """向后兼容：返回纯文本。"""
    return call_openai_chat(messages, model, temperature)["content"]


def score_part_with_llm(
    requirement_text: str,
    part_info: Dict[str, Any],
    reference_designs: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """用 LLM 对器件进行应用场景适配度和设计成熟度评分。"""
    pn = part_info.get("part_number", "Unknown")
    mfr = part_info.get("manufacturer") or "-"
    desc = part_info.get("description") or "-"
    vin = f"{part_info.get('vin_min', '?')}-{part_info.get('vin_max', '?')}V"
    iout = f"{part_info.get('iout_max', '?')}A"
    temp = f"{part_info.get('temp_min', '?')}-{part_info.get('temp_max', '?')}C"

    rd_lines = []
    for i, rd in enumerate(reference_designs[:3], 1):
        name = rd.get("name", "")
        desc_rd = (rd.get("description") or "").strip()[:300]
        rd_lines.append(f"{i}. [{name}] {desc_rd}")
    rd_text = "\n".join(rd_lines) if rd_lines else "(no reference designs)"

    system = (
        "You are a senior electronic engineer specializing in power IC component evaluation. "
        "Respond with JSON only, no extra text."
    )
    user = (
        f"## Requirement\n{requirement_text}\n\n"
        f"## Part\n"
        f"MPN: {pn} ({mfr})\n"
        f"Desc: {desc}\n"
        f"Params: Vin {vin}, Iout {iout}, Temp {temp}\n\n"
        f"## Reference Designs\n{rd_text}\n\n"
        "Score 0-100 for:\n"
        "1. application_score: design scenario match\n"
        "2. design_risk_score: reliability & maturity\n"
        'Return: {"application_score": 85, "design_risk_score": 78, "reasoning": "..."}'
    )
    try:
        resp = call_openai_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=0.0,
        )
        content = resp["content"]
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            result = _json.loads(content[start:end + 1])
            for key in ("application_score", "design_risk_score"):
                if key in result:
                    result[key] = max(0.0, min(100.0, float(result[key])))
            return result
    except Exception as e:
        from .log_util import warn_swallow; warn_swallow("llm_client", e, "score_part")
    return {}


def parse_requirement_with_fc(text: str) -> Dict[str, Any]:
    """P2: 使用 DeepSeek Function Calling 进行结构化需求提取。

    替代原来的 JSON 字符串解析，强制 LLM 按 Tool Schema 输出结构化字段。
    减少解析错误（格式异常、字段遗漏、类型错误）。

    Returns:
        dict with keys matching RequirementConstraints fields.
    """
    try:
        resp = call_openai_chat(
            messages=[{
                "role": "system",
                "content": "你是一个电子元器件选型需求解析器。从用户输入中提取结构化参数。注意：mA 必须转为 A（除以1000），'非车规'意味着 industrial 等级。"
            }, {
                "role": "user",
                "content": text,
            }],
            tools=REQUIREMENT_TOOLS,
            tool_choice="required",
            temperature=0.0,
        )

        tool_calls = resp.get("tool_calls", [])
        if tool_calls:
            args = _json.loads(tool_calls[0]["function"]["arguments"])
            # 清理 null 值
            return {k: v for k, v in args.items() if v is not None}

        # Fallback: 尝试从 content 解析
        content = resp.get("content", "")
        if content:
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                return _json.loads(content[start:end + 1])

    except Exception as e:
        from .log_util import warn_swallow; warn_swallow("llm_client", e, "parse_fc")

    return {}


def parse_requirement_with_llm(text: str) -> Dict[str, Any]:
    """旧版 JSON 字符串解析（保留作为 fallback）。"""
    system = (
        "你是一个结构化信息提取助手。接收电子工程师的元器件选型需求，输出 JSON 格式的字段。\n"
        "请只输出 JSON，不要额外说明。字段示例：application, category, topology, input_voltage_nominal_v, output_voltage_v, output_current_a, temperature_min_c, temperature_max_c, grade, preferences (list)。"
    )
    user = f"解析以下需求为 JSON：\n{text}\n要求返回满足字段示例，只返回 JSON。"
    try:
        resp = call_openai_chat(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
        )
        content = resp["content"]
        start = content.find("{")
        end = content.rfind("}")
        if start != -1 and end != -1:
            return _json.loads(content[start:end + 1])
        return _json.loads(content)
    except Exception:
        return {"raw_llm": resp.get("content", "") if 'resp' in dir() else ""}

