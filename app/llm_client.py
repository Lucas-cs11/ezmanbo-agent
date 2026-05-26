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

