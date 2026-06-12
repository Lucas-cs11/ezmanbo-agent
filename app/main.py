from typing import Optional, Dict, Any, AsyncGenerator
from fastapi import FastAPI, Request, Body
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import time
import traceback
from .agent_orchestrator import analyze, replacement_report

app = FastAPI()

# ── CORS 配置，允许 Next.js dev server ──────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


# ── SSE 流式输出端点（B1 任务）──────────────────────────────────────

async def _stream_analyze(req: AnalyzeRequest) -> AsyncGenerator[str, None]:
    """异步生成器：按阶段推送 SSE 事件"""
    start_time = time.time()
    try:
        # Step 1: 解析需求
        from .requirement_parser import parse_requirement
        from .ezplm_client import search_parts
        from .scoring import score_candidates
        from .evidence import build_evidence
        from .report_generator import build_report

        requirement = parse_requirement(req.user_input)
        yield f"event: parse_done\ndata: {json.dumps({'status': '需求解析完成', 'constraint': requirement.dict()})}\n\n"

        # Step 2: 搜索器件候选
        candidates = search_parts(requirement)
        yield f"event: search_done\ndata: {json.dumps({'status': '搜索完成', 'candidate_count': len(candidates)})}\n\n"

        # Step 3: 评分（可以逐个器件推送）
        scored = score_candidates(requirement, candidates)
        for idx, part in enumerate(scored):
            part_data = {
                'status': f'评分完成: {part.part.part_number}',
                'index': idx,
                'total': len(scored),
                'part_number': part.part.part_number,
                'score': part.score.total_score,
            }
            yield f"event: score_update\ndata: {json.dumps(part_data)}\n\n"

        # Step 4: 构建证据和风险评估
        evidence = build_evidence(scored, requirement)
        yield f"event: evidence_done\ndata: {json.dumps({'status': '证据链构建完成', 'evidence_count': len(evidence)})}\n\n"

        # Step 5: 生成报告
        report = build_report(requirement, scored, evidence)
        risk_data = report.risks.dict() if report.risks else {}
        yield f"event: risk_done\ndata: {json.dumps({'status': '风险评估完成', 'risk': risk_data})}\n\n"

        # Step 6: 逐 token 推送报告文本（模拟流式文本）
        if report.summary_markdown:
            for chunk in report.summary_markdown.split('\n'):
                if chunk.strip():
                    yield f"event: text_delta\ndata: {json.dumps({'text': chunk})}\n\n"

        # Step 7: 推送完整报告和完成信号
        elapsed = time.time() - start_time
        yield f"event: done\ndata: {json.dumps({'status': '分析完成', 'elapsed_seconds': round(elapsed, 2), 'report': report.dict()})}\n\n"

    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        yield f"event: error\ndata: {json.dumps({'status': '错误', 'error': str(e), 'elapsed_seconds': round(elapsed, 2)})}\n\n"


@app.post("/analyze/stream")
async def analyze_stream_endpoint(body: AnalyzeRequest):
    """流式输出端点：SSE 逐段推送选型报告

    示例事件流：
    - parse_done: 需求解析完成
    - search_done: 搜索完成 + 候选数量
    - score_update: 评分完成（多次）
    - evidence_done: 证据链完成
    - risk_done: 风险评估完成 + RiskIR
    - text_delta: 报告文本片段（多次）
    - done: 完成 + 总耗时 + 完整报告
    """
    return StreamingResponse(
        _stream_analyze(body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


# ── 电路图生成端点（B2 任务）────────────────────────────────────────

@app.get("/schematic/{topology}")
async def get_schematic(topology: str, Vin: float, Vout: float, Iout: float):
    """生成参数化应用电路 SVG

    Args:
        topology: 拓扑类型 ('buck', 'boost', 'ldo')
        Vin: 输入电压 (V)
        Vout: 输出电压 (V)
        Iout: 输出电流 (A)

    Returns:
        SVG 格式的电路图
    """
    try:
        from .schematic_generator import generate_schematic
        svg = generate_schematic(topology, Vin, Vout, Iout)
        return Response(content=svg, media_type="image/svg+xml")
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"detail": str(e)},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"电路图生成错误: {str(e)}"},
        )
