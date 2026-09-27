"""
langgraph_orchestrator.py — LangGraph 状态机选型流水线 (P1)

替换原有的线性 analyze() 函数，使用 LangGraph StateGraph 实现：
  ParseNode → SearchNode → ScoreNode → EvidenceNode → CriticNode → ReportNode
                     ↑                                              |
                     └── 候选不足时自动放宽约束重搜 ──────────────────┘
                                                          ↑         |
                                                          └─ 不通过 ─┘ (最多1次)

前置依赖：langgraph>=1.0
"""

from __future__ import annotations

import os
from typing import TypedDict, Optional, List, Any
from langgraph.graph import StateGraph, END


# ═══════════════════════════════════════════════════════════════
# State
# ═══════════════════════════════════════════════════════════════

class GraphState(TypedDict):
    user_input: str
    constraints: Any                           # RequirementConstraints
    candidates: List[Any]                       # List[PartIR]
    scored: List[Any]                           # List[ScoredPart]
    evidence: List[Any]                         # List[EvidenceIR]
    risks: Any                                  # RiskIR | None
    report: Any                                 # SelectionReport | None
    retry_count: int
    current_relaxed: bool                       # 是否已放宽过约束
    critic_passed: bool
    error: str


# ═══════════════════════════════════════════════════════════════
# Nodes
# ═══════════════════════════════════════════════════════════════

def parse_node(state: GraphState) -> GraphState:
    """ParseNode: 调用 requirement_parser 解析用户输入。"""
    from .requirement_parser import parse_requirement
    req = parse_requirement(state["user_input"])
    return {**state, "constraints": req, "retry_count": 0, "current_relaxed": False}


def search_node(state: GraphState) -> GraphState:
    """SearchNode: 调用 eZ-PLM API 搜索匹配器件。"""
    from .ezplm_client import search_parts

    req = state["constraints"]

    # 重试时放宽电流约束 20%
    if state.get("current_relaxed") and req.output_current_a:
        req.output_current_a = round(req.output_current_a * 0.8, 2)

    candidates = search_parts(req)
    return {**state, "candidates": candidates}


def score_node(state: GraphState) -> GraphState:
    """ScoreNode: 双模自适应评分。"""
    from .scoring import score_candidates

    scored = score_candidates(state["constraints"], state["candidates"])
    return {**state, "scored": scored}


def evidence_node(state: GraphState) -> GraphState:
    """EvidenceNode: 构建证据链。"""
    from .evidence import build_evidence

    evidence = build_evidence(state["scored"], state["constraints"])
    return {**state, "evidence": evidence}


def critic_node(state: GraphState) -> GraphState:
    """CriticNode (P5): 自省检查 — 拓扑/参数一致性验证。

    仅在 LLM 增强模式下运行。检查项：
    1. 拓扑与电压方向是否一致
    2. 推荐器件是否存在明显的参数矛盾
    失败时触发一次重试。
    """
    constraints = state["constraints"]
    scored = state["scored"]
    retries = state.get("retry_count", 0)

    # 无候选或纯规则模式跳过
    if not scored or retries >= 1:
        return {**state, "critic_passed": True}

    # 规则层自检（无 LLM 调用）
    issues = []

    # 检查 1：拓扑-电压一致性
    topo = getattr(constraints, "topology", None)
    vin = getattr(constraints, "input_voltage_nominal_v", None)
    vout = getattr(constraints, "output_voltage_v", None)
    if topo and vin and vout:
        if topo == "buck" and vin <= vout:
            issues.append(f"Topology mismatch: buck requires Vin({vin}V) > Vout({vout}V)")
        elif topo == "boost" and vin >= vout:
            issues.append(f"Topology mismatch: boost requires Vin({vin}V) < Vout({vout}V)")

    # 检查 2：推荐器件参数覆盖
    recommended = [s for s in scored if getattr(s, "recommendation_level", "") == "recommended"]
    if recommended:
        top = recommended[0]
        iout_req = getattr(constraints, "output_current_a", None)
        iout_rated = getattr(top.part, "output_current_max_a", None) if hasattr(top, "part") else None
        if iout_req and iout_rated and iout_rated < iout_req * 0.8:
            issues.append(f"Current margin low: rated {iout_rated}A vs required {iout_req}A")

    if issues:
        return {
            **state,
            "critic_passed": False,
            "retry_count": retries + 1,
            "error": "; ".join(issues),
        }

    return {**state, "critic_passed": True}


def report_node(state: GraphState) -> GraphState:
    """ReportNode: 生成完整 SelectionReport。"""
    from .report_generator import build_report

    req = state["constraints"]
    scored = state["scored"]
    evidence = state["evidence"]
    report = build_report(req, scored, evidence)
    return {**state, "report": report}


# ═══════════════════════════════════════════════════════════════
# Conditional Edges
# ═══════════════════════════════════════════════════════════════

def should_relax(state: GraphState) -> str:
    """ScoreNode 后判断：候选数 < 3 且未放宽过 → 放宽重搜。"""
    if len(state["candidates"]) < 3 and not state.get("current_relaxed"):
        return "relax_search"
    return "continue"


def should_retry(state: GraphState) -> str:
    """CriticNode 后判断：不通过且未超过重试上限 → 回退到 SearchNode。"""
    if not state.get("critic_passed") and state.get("retry_count", 0) <= 1:
        return "retry"
    return "report"


# ═══════════════════════════════════════════════════════════════
# Graph Builder
# ═══════════════════════════════════════════════════════════════

def build_selection_graph() -> StateGraph:
    """构建 LangGraph 选型流水线。"""
    workflow = StateGraph(GraphState)

    # 添加节点
    workflow.add_node("parse", parse_node)
    workflow.add_node("search", search_node)
    workflow.add_node("score", score_node)
    workflow.add_node("evidence", evidence_node)
    workflow.add_node("critic", critic_node)
    workflow.add_node("report", report_node)

    # 主流程边
    workflow.set_entry_point("parse")
    workflow.add_edge("parse", "search")
    workflow.add_edge("search", "score")

    # Score → 条件边
    workflow.add_conditional_edges(
        "score",
        should_relax,
        {
            "relax_search": "search",   # 放宽 → 重搜
            "continue": "evidence",
        }
    )

    workflow.add_edge("evidence", "critic")

    # Critic → 条件边
    workflow.add_conditional_edges(
        "critic",
        should_retry,
        {
            "retry": "search",          # 自省失败 → 回退重搜
            "report": "report",
        }
    )

    workflow.add_edge("report", END)

    return workflow.compile()


# ═══════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════

_graph = None


def get_graph():
    """获取或创建单例 LangGraph 实例。"""
    global _graph
    if _graph is None:
        _graph = build_selection_graph()
    return _graph


def run_selection_pipeline(user_input: str) -> dict:
    """运行完整选型流水线，返回最终 GraphState。

    兼容旧 analyze() 接口：从返回的 state 中提取 SelectionReport。
    """
    graph = get_graph()
    initial: GraphState = {
        "user_input": user_input,
        "constraints": None,
        "candidates": [],
        "scored": [],
        "evidence": [],
        "risks": None,
        "report": None,
        "retry_count": 0,
        "current_relaxed": False,
        "critic_passed": False,
        "error": "",
    }
    result = graph.invoke(initial)
    return result
