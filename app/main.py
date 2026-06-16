from typing import Optional, Dict, Any, AsyncGenerator
from fastapi import FastAPI, Request, Body
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, StreamingResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import time
import asyncio
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
    """Pipeline 模式：单次调用，返回完整 SelectionReport JSON。

    ── B4：语义缓存支持 ──
    - 响应头 X-Cache: HIT 表示命中缓存
    - 响应头 X-Cache: MISS 表示未命中缓存
    """
    try:
        # ── B4：检查语义缓存 ──────────────────────────────────────
        from .semantic_cache import get_semantic_cache
        cache = get_semantic_cache()
        cache_result = cache.get(body.user_input)
        cache_header = "HIT" if cache_result is not None else "MISS"

        report = analyze(body.user_input)
        return JSONResponse(
            content=report.dict(),
            headers={"X-Cache": cache_header}
        )
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

def _safe_serialize(obj):
    """安全序列化 Pydantic/dataclass 对象为 JSON 兼容 dict。"""
    if hasattr(obj, 'dict'):
        return _safe_serialize(obj.dict())
    if hasattr(obj, 'model_dump'):
        return _safe_serialize(obj.model_dump())
    if isinstance(obj, dict):
        return {k: _safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_safe_serialize(v) for v in obj]
    return obj


async def _stream_analyze(req: AnalyzeRequest) -> AsyncGenerator[str, None]:
    """异步生成器：按阶段推送 SSE 事件（含 B4 语义缓存集成）"""
    t_start = time.time()
    loop = asyncio.get_running_loop()

    def _yield(event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(_safe_serialize(data), ensure_ascii=False)}\n\n"

    try:
        # ── B4：语义缓存层检查 ──────────────────────────────────
        from .semantic_cache import get_semantic_cache
        cache = get_semantic_cache()
        cache_result = cache.get(req.user_input)

        if cache_result is not None:
            elapsed = round(time.time() - t_start, 2)
            yield _yield("cache_hit", {"hit": True, "similarity": cache_result.get("similarity", 0)})
            yield _yield("done", {
                "status": "分析完成（语义缓存命中）",
                "elapsed_s": elapsed,
                "cache_hit": True,
            })
            return

        yield _yield("cache_hit", {"hit": False})

        # ── Stage 1：需求解析 ──────────────────────────────────
        yield _yield("stage", {"stage": "parse", "status": "started"})
        from .requirement_parser import parse_requirement
        requirement = await loop.run_in_executor(None, parse_requirement, req.user_input)
        yield _yield("parse_done", {
            "status": "需求解析完成",
            "constraints": _safe_serialize(requirement),
            "fields_parsed": sum(1 for v in [
                requirement.category, requirement.topology,
                requirement.input_voltage_nominal_v, requirement.output_voltage_v,
                requirement.output_current_a, requirement.temperature_min_c,
                requirement.temperature_max_c, requirement.grade,
            ] if v is not None),
        })

        # ── Stage 2：器件搜索 ──────────────────────────────────
        yield _yield("stage", {"stage": "search", "status": "started"})
        from .ezplm_client import search_parts
        candidates = await loop.run_in_executor(None, search_parts, requirement)
        yield _yield("search_done", {
            "status": "搜索完成",
            "candidate_count": len(candidates),
            "sources": list(set(getattr(c, "source", "mock") for c in candidates)),
        })

        if not candidates:
            yield _yield("warning", {"message": "未找到匹配器件，请检查需求或扩充数据源"})

        # ── Stage 3：评分计算 ──────────────────────────────────
        yield _yield("stage", {"stage": "score", "status": "started", "total": len(candidates)})
        from .scoring import score_candidates
        scored = await loop.run_in_executor(None, score_candidates, requirement, candidates)
        for i, s in enumerate(scored):
            yield _yield("score_update", {
                "status": f"评分完成: {s.part.part_number}",
                "index": i + 1,
                "total": len(scored),
                "part_number": s.part.part_number,
                "manufacturer": s.part.manufacturer,
                "total_score": s.score.total_score,
                "parameter_match_score": s.score.parameter_match_score,
                "recommendation_level": s.recommendation_level,
                "scoring_mode": s.score.scoring_mode,
            })

        # ── Stage 4：证据构建 ──────────────────────────────────
        yield _yield("stage", {"stage": "evidence", "status": "started"})
        from .evidence import build_evidence
        evidence = await loop.run_in_executor(None, build_evidence, scored, requirement)
        avg_conf = round(sum(e.confidence for e in evidence) / len(evidence), 3) if evidence else 0.0
        yield _yield("evidence_done", {
            "status": "证据链构建完成",
            "evidence_count": len(evidence),
            "avg_confidence": avg_conf,
        })

        # ── Stage 5：风险评估 ──────────────────────────────────
        yield _yield("stage", {"stage": "risk", "status": "started"})
        from .report_generator import build_report, _assess_risks
        risks = await loop.run_in_executor(None, _assess_risks, requirement, scored)
        yield _yield("risk_done", {
            "status": "风险评估完成",
            "overall_risk_level": risks.overall_risk_level,
            "risk_count": len(risks.risk_items),
            "high": sum(1 for r in risks.risk_items if r.severity == "high"),
            "medium": sum(1 for r in risks.risk_items if r.severity == "medium"),
            "low": sum(1 for r in risks.risk_items if r.severity == "low"),
            "supply_summary": risks.supply_risk_summary,
            "engineering_summary": risks.engineering_risk_summary,
        })

        # ── Stage 6：报告生成与流式输出 ─────────────────────────
        yield _yield("stage", {"stage": "report", "status": "started"})
        report = await loop.run_in_executor(None, build_report, requirement, scored, evidence)
        if report.summary_markdown:
            for line in report.summary_markdown.split('\n'):
                if line.strip():
                    yield _yield("text_delta", {"text": line})

        # ── Stage 7：完成 ──────────────────────────────────────
        elapsed = round(time.time() - t_start, 2)
        yield _yield("done", {
            "status": "分析完成",
            "elapsed_s": elapsed,
            "request_id": report.request_id,
            "recommended_count": len(report.recommended_parts),
            "candidate_count": len(report.candidates),
            "overall_risk": risks.overall_risk_level,
        })

        # ── B4：将结果存入语义缓存 ────────────────────────────
        try:
            from .semantic_cache import get_semantic_cache
            get_semantic_cache().set(req.user_input, report.dict())
        except Exception:
            pass

    except Exception as exc:
        elapsed = round(time.time() - t_start, 2)
        yield _yield("error", {
            "status": "错误",
            "message": str(exc),
            "elapsed_s": elapsed,
            "traceback": traceback.format_exc()[:500],
        })


@app.post("/analyze/stream")
async def analyze_stream_endpoint(body: AnalyzeRequest):
    """流式输出端点：SSE 逐段推送选型报告

    ── B4：语义缓存支持 ──
    - 响应头 X-Cache: HIT 表示命中缓存
    - 响应头 X-Cache: MISS 表示未命中缓存

    示例事件流：
    - cache_hit: 缓存命中状态（HIT/MISS）
    - parse_done: 需求解析完成
    - search_done: 搜索完成 + 候选数量
    - score_update: 评分完成（多次）
    - evidence_done: 证据链完成
    - risk_done: 风险评估完成 + RiskIR
    - text_delta: 报告文本片段（多次）
    - done: 完成 + 总耗时 + 完整报告
    """
    # ── B4：检查语义缓存 ──────────────────────────────────────
    from .semantic_cache import get_semantic_cache
    cache = get_semantic_cache()
    cache_result = cache.get(body.user_input)

    # 根据缓存状态设置响应头
    cache_header = "HIT" if cache_result is not None else "MISS"

    return StreamingResponse(
        _stream_analyze(body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "X-Cache": cache_header,
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
