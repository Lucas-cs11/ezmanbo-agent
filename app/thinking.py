"""
thinking.py — 思考深度控制模块

四档思考深度对应不同的 LLM 提示策略：

  off           — 最小化指令，快速直接回复
  default       — 基础分步推理（默认）
  contemplation — 详细链式推理 + 多角度验证
  exhaustive    — 穷尽分析 + 自检修正

前端通过 thinking_depth 参数传入，后端据此调整 system prompt 和 temperature。
"""

from typing import Tuple

# ── 思考深度配置 ────────────────────────────────────────────

THINKING_CONFIGS = {
    "off": {
        "label": "关闭",
        "temperature": 0.0,
        "system_instruction": (
            "直接、简洁地回答问题。不要展开推理过程，只给出结论。"
        ),
    },
    "default": {
        "label": "默认",
        "temperature": 0.0,
        "system_instruction": (
            "逐步分析问题并给出答案。先理解需求，再检索信息，最后给出结论。"
        ),
    },
    "contemplation": {
        "label": "沉思",
        "temperature": 0.3,
        "system_instruction": (
            "请进行深度推理分析：\n"
            "1. 首先明确问题的关键要素和约束条件\n"
            "2. 从多个角度（电气性能、供应链、成本、合规）展开分析\n"
            "3. 对每个候选方案列出优缺点\n"
            "4. 给出有充分依据的推荐结论\n"
            "5. 标注任何需要人工确认的不确定因素"
        ),
    },
    "exhaustive": {
        "label": "穷究",
        "temperature": 0.5,
        "system_instruction": (
            "请进行最彻底的穷尽分析：\n"
            "1. 完整解析需求中的所有显式和隐含约束\n"
            "2. 从电气参数、供应链、成本、合规、可靠性、热管理、EMC 七个维度逐一评估\n"
            "3. 对每个候选方案进行量化对比（表格形式）\n"
            "4. 识别并标记最佳方案、次优方案和最差方案\n"
            "5. 对推荐方案进行自检：是否存在参数矛盾？是否满足所有硬约束？\n"
            "6. 列出需要实验验证的关键假设\n"
            "7. 给出最终推荐及理由，并标注置信度\n\n"
            "完成以上分析后，在执行任何操作前先做一次自我审查：检查结论是否存在逻辑漏洞、"
            "参数覆盖是否有遗漏、推荐排序是否合理。确认无误后再输出结论。"
        ),
    },
}


def get_thinking_config(depth: str) -> dict:
    """获取思考深度配置，无效值回退到 default。"""
    return THINKING_CONFIGS.get(depth, THINKING_CONFIGS["default"])


def build_thinking_prompt(base_prompt: str, depth: str) -> Tuple[str, float]:
    """在基础 prompt 上附加思考深度指令，返回 (完整prompt, temperature)。"""
    config = get_thinking_config(depth)
    instruction = config["system_instruction"]

    if depth == "off":
        # 最小化模式：只保留核心指令
        enhanced = base_prompt + "\n\n" + instruction
    else:
        # 标准/深度模式：将思考指令插入到 prompt 开头
        enhanced = instruction + "\n\n" + base_prompt

    return enhanced, config["temperature"]
