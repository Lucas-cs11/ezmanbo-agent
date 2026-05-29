from typing import Optional, Dict, Any
from fastapi import FastAPI, Request, Body
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import traceback
from .agent_orchestrator import analyze, replacement_report

app = FastAPI()

class AnalyzeRequest(BaseModel):
    user_input: str

class ReplacementRequest(BaseModel):
    original_part_number: str

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    return JSONResponse(
        status_code=422,
        content={"detail": "请求体格式错误", "errors": exc.errors()},
    )

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/analyze")
async def analyze_endpoint(body: AnalyzeRequest):
    """Pipeline 模式：单次调用，返回完整 SelectionReport JSON。"""
    try:
        report = analyze(body.user_input)
        return report.dict()
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"处理错误: {str(e)}"},
        )

@app.post("/replacement")
async def replacement_endpoint(body: ReplacementRequest):
    """替代器件查找。"""
    try:
        return replacement_report(body.original_part_number)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"处理错误: {str(e)}"},
        )


# ── Agent 端点 ──────────────────────────────────────────────────

class AgentRequest(BaseModel):
    user_input: str
    session_id: Optional[str] = None

@app.post("/agent/chat")
async def agent_chat_endpoint(body: AgentRequest):
    """ReAct Agent 模式：支持多轮对话，返回推理过程 + 工具调用记录。"""
    try:
        from .react_agent import run_agent
        return run_agent(body.user_input, session_id=body.session_id)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Agent 错误: {str(e)}"},
        )

@app.get("/agent/sessions")
async def agent_sessions_endpoint():
    """列出当前活跃的 Agent 会话。"""
    from .react_agent import _sessions
    return {"active_sessions": len(_sessions), "session_ids": list(_sessions.keys())}
