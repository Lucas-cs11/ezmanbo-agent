from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from .agent_orchestrator import analyze, replacement_report

app = FastAPI()

class AnalyzeRequest(BaseModel):
    user_input: str

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/analyze")
async def analyze_endpoint(body: AnalyzeRequest):
    """Pipeline 模式：单次调用，返回完整 SelectionReport JSON。"""
    report = analyze(body.user_input)
    return report.dict()

class ReplacementRequest(BaseModel):
    original_part_number: str

@app.post("/replacement")
async def replacement_endpoint(body: ReplacementRequest):
    return replacement_report(body.original_part_number)


# ── Agent 端点 ──────────────────────────────────────────────────

class AgentRequest(BaseModel):
    user_input: str
    session_id: Optional[str] = None  # 多轮对话用

@app.post("/agent/chat")
async def agent_chat_endpoint(body: AgentRequest):
    """ReAct Agent 模式：支持多轮对话，返回推理过程 + 工具调用记录。"""
    from .react_agent import run_agent
    return run_agent(body.user_input, session_id=body.session_id)

@app.get("/agent/sessions")
async def agent_sessions_endpoint():
    """列出当前活跃的 Agent 会话。"""
    from .react_agent import _sessions
    return {
        "active_sessions": len(_sessions),
        "session_ids": list(_sessions.keys()),
    }

