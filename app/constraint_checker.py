"""
constraint_checker.py — 选型约束完整性检查与渐进式追问

硬约束分级：
  P0 (MUST)：Vin, Vout, Iout — 缺失时禁止触发选型
  P1 (SHOULD)：温度范围, 等级 — 缺失时追问
  P2 (NICE)：封装, 应用场景, 偏好 — 缺失时不追问

流程：
  1. 解析用户输入 → 提取约束参数
  2. 合并到会话累积约束上下文
  3. 检查完整性 → 完整则触发选型 / 不完整则生成追问
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import re


# ═══════════════════════════════════════════════════════════════
# 约束定义
# ═══════════════════════════════════════════════════════════════

P0_FIELDS = ["input_voltage_nominal_v", "output_voltage_v", "output_current_a"]
P1_FIELDS = ["temperature_min_c", "temperature_max_c", "grade"]
P2_FIELDS = ["package_preference", "application"]

FIELD_LABELS: Dict[str, str] = {
    "input_voltage_nominal_v": "输入电压 (Vin)",
    "output_voltage_v": "输出电压 (Vout)",
    "output_current_a": "输出电流 (Iout)",
    "temperature_min_c": "最低工作温度",
    "temperature_max_c": "最高工作温度",
    "grade": "应用等级",
    "package_preference": "封装偏好",
    "application": "应用场景",
}

FIELD_EXAMPLES: Dict[str, str] = {
    "input_voltage_nominal_v": "如 12V",
    "output_voltage_v": "如 5V 或 3.3V",
    "output_current_a": "如 3A 或 500mA",
    "temperature_min_c": "如 -40°C",
    "temperature_max_c": "如 85°C 或 125°C",
    "grade": "automotive(车规) / industrial(工业级) / commercial(商业级)",
    "package_preference": "如 SOT-23、QFN、TO-220",
    "application": "如 车载电源、通信设备、工业控制",
}

P0_QUESTIONS: Dict[str, str] = {
    "input_voltage_nominal_v": "系统的输入电压是多少？（如 12V、24V、5V 等）",
    "output_voltage_v": "需要的输出电压是多少？（如 5V、3.3V 等）",
    "output_current_a": "输出端需要多大电流？（如 3A、500mA 等）",
}

P1_QUESTIONS: Dict[str, str] = {
    "temperature_min_c,temperature_max_c": "工作温度范围是多少？（如 -40~85°C 工业级，或 -40~125°C 车规级）",
    "grade": "需要满足什么等级标准？车规 (AEC-Q100)、工业级还是商业级？",
}

# P0 字段是否可从其他字段推断
_VOLTAGE_INFER = re.compile(
    r"(\d+\.?\d*)\s*[Vv伏][\s\S]{0,8}?(?:转|→|->|to|输?出|降到|升到)[\s]*(\d+\.?\d*)\s*[Vv伏]"
    r"|(\d+\.?\d*)\s*[Vv伏]\s*[-–—]\s*(\d+\.?\d*)\s*[Vv伏]"  # 范围: 6V–36V
)
_CURRENT_INFER = re.compile(r"(\d+\.?\d*)\s*(?:A|a|安|\s*毫安|mA|ｍＡ)")
_MA_INFER = re.compile(r"(\d+)\s*(?:mA|毫安|ｍＡ)")


def extract_constraints(text: str) -> dict:
    """从用户输入文本中提取约束参数（规则层快速提取）。"""
    result: dict = {}

    # 电压：X V 转 Y V 或 X V – Y V 范围
    vm = _VOLTAGE_INFER.search(text)
    if vm:
        if vm.group(1) and vm.group(2):
            # "12V转5V" 模式
            result["input_voltage_nominal_v"] = float(vm.group(1))
            result["output_voltage_v"] = float(vm.group(2))
        elif vm.group(3) and vm.group(4):
            # "6V–36V" 范围模式 — 提取为 Vin 范围
            result["input_voltage_min_v"] = float(vm.group(3))
            result["input_voltage_max_v"] = float(vm.group(4))
            # 从文本上下文中提取输出电压
            vout_m = re.search(r"(\d+)V\s*(?:输?出|转|→|->)", text)
            if vout_m:
                result["output_voltage_v"] = float(vout_m.group(1))
        else:
            # 单电压数值
            single_v = vm.group(1) or vm.group(3)
            if single_v:
                result["input_voltage_nominal_v"] = float(single_v)

    # 电流：优先匹配毫安
    ma = _MA_INFER.search(text)
    if ma:
        result["output_current_a"] = float(ma.group(1)) / 1000.0
    else:
        cm = _CURRENT_INFER.search(text)
        if cm:
            result["output_current_a"] = float(cm.group(1))

    # 温度
    tm = re.search(r"(-?\d+)\s*(?:~|到|至|-)\s*(-?\d+)\s*(?:°|°C|C|度)", text)
    if tm:
        result["temperature_min_c"] = float(tm.group(1))
        result["temperature_max_c"] = float(tm.group(2))

    # 等级
    if re.search(r"车规|automotive|AEC", text, re.I):
        result["grade"] = "automotive"
    elif re.search(r"工业|industrial", text, re.I):
        result["grade"] = "industrial"
    elif re.search(r"商业|commercial", text, re.I):
        result["grade"] = "commercial"
    elif re.search(r"非车规|不要车规|不是车规", text, re.I):
        result["grade"] = "industrial"

    # 封装
    pkg_m = re.search(r"(SOT-\d+|QFN\d*|TO-\d+|SOIC-\d+|TSSOP-\d+|DFN\d*)", text, re.I)
    if pkg_m:
        result["package_preference"] = pkg_m.group(1).upper()

    # 拓扑
    if re.search(r"降压|buck|降到|step.down", text, re.I):
        result["topology"] = "buck"
    elif re.search(r"升压|boost|升到|step.up", text, re.I):
        result["topology"] = "boost"
    elif re.search(r"ldo|线性|LDO", text, re.I):
        result["topology"] = "ldo"

    return result


def merge_constraints(accumulated: dict, new_extracted: dict) -> dict:
    """合并新提取的约束到累积约束中（新值优先覆盖旧值）。"""
    merged = dict(accumulated)
    for k, v in new_extracted.items():
        if v is not None and v != "":
            merged[k] = v
    return merged


def check_completeness(constraints: dict) -> Tuple[bool, List[str], List[str]]:
    """检查约束完整性。"""
    missing_p0 = []
    missing_p1 = []

    # input_voltage_nominal_v 可以由 input_voltage_min/max 替代
    has_vin = (constraints.get("input_voltage_nominal_v") is not None or
               (constraints.get("input_voltage_min_v") is not None and
                constraints.get("input_voltage_max_v") is not None))

    for f in P0_FIELDS:
        if f == "input_voltage_nominal_v":
            if not has_vin:
                missing_p0.append(f)
        elif constraints.get(f) is None:
            missing_p0.append(f)

    for f in P1_FIELDS:
        if constraints.get(f) is None:
            missing_p1.append(f)

    # 温度特殊处理 — 两个都缺失才算
    if "temperature_min_c" in missing_p1 and "temperature_max_c" in missing_p1:
        pass  # 都缺失，保留在列表中
    elif "temperature_min_c" in missing_p1 or "temperature_max_c" in missing_p1:
        missing_p1 = [m for m in missing_p1 if m not in ("temperature_min_c", "temperature_max_c")]
        missing_p1.append("temperature_range")

    return (len(missing_p0) == 0, missing_p0, missing_p1)


def generate_clarification_questions(missing_p0: List[str], missing_p1: List[str]) -> List[str]:
    """根据缺失字段生成自然语言追问列表。"""
    questions = []

    # P0 问题 — 必须问
    for f in missing_p0:
        if f in P0_QUESTIONS:
            questions.append(P0_QUESTIONS[f])

    # P1 问题 — 选最重要的 1-2 个
    p1_asked = 0
    if "temperature_min_c,temperature_max_c" in P1_QUESTIONS:
        for mp1 in missing_p1:
            if mp1 in ("temperature_min_c", "temperature_max_c", "temperature_range"):
                questions.append(P1_QUESTIONS["temperature_min_c,temperature_max_c"])
                p1_asked += 1
                break
    for f in missing_p1:
        if f in P1_QUESTIONS and p1_asked < 2:
            questions.append(P1_QUESTIONS[f])
            p1_asked += 1

    return questions


def build_clarification_response(
    user_input: str,
    accumulated: dict,
    agent_name: str = "eZmanbo",
) -> str:
    """构建完整的追问回复。

    1. 确认已理解的信息
    2. 指出缺失的关键参数
    3. 给出明确的问题
    """
    constraints = merge_constraints(accumulated, extract_constraints(user_input))
    is_complete, missing_p0, missing_p1 = check_completeness(constraints)

    if is_complete:
        return ""  # 完整则不需要追问

    lines = []

    # 已确认的信息
    confirmed = []
    if constraints.get("input_voltage_nominal_v"):
        confirmed.append(f"输入电压 {constraints['input_voltage_nominal_v']}V")
    if constraints.get("output_voltage_v"):
        confirmed.append(f"输出电压 {constraints['output_voltage_v']}V")
    if constraints.get("output_current_a"):
        confirmed.append(f"输出电流 {constraints['output_current_a']}A")
    if constraints.get("topology"):
        topo_cn = {"buck": "降压(Buck)", "boost": "升压(Boost)", "ldo": "LDO"}.get(constraints["topology"], constraints["topology"])
        confirmed.append(f"拓扑 {topo_cn}")
    if constraints.get("grade"):
        grade_cn = {"automotive": "车规级", "industrial": "工业级", "commercial": "商业级"}.get(constraints["grade"], constraints["grade"])
        confirmed.append(f"等级 {grade_cn}")

    if confirmed:
        lines.append(f"已理解您的需求：{'，'.join(confirmed)}。")
        lines.append("")

    # 追问
    questions = generate_clarification_questions(missing_p0, missing_p1)
    if questions:
        lines.append("为了给出精准的选型推荐，还需要确认以下关键参数：")
        lines.append("")
        for i, q in enumerate(questions, 1):
            lines.append(f"{i}. {q}")

    return "\n".join(lines)
