from fastapi import FastAPI, Request, Body
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError, Field
import json
from typing import Dict, Any
from .agent_orchestrator import analyze, replacement_report

app = FastAPI()

class AnalyzeRequest(BaseModel):
    user_input: str

class ReplacementRequest(BaseModel):
    original_part_number: str

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理请求验证错误"""
    try:
        body = await request.body()
        body_str = body.decode('utf-8', errors='replace')
    except:
        body_str = "[无法解析请求体]"

    return JSONResponse(
        status_code=422,
        content={
            "detail": "请求体格式错误",
            "errors": exc.errors()
        }
    )

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/analyze")
async def analyze_endpoint(body: Dict[str, Any] = Body(...)):
    """处理分析请求，支持 UTF-8 中文"""
    try:
        if "user_input" not in body:
            return JSONResponse(
                status_code=422,
                content={"detail": "缺少必需字段: user_input"}
            )

        user_input = str(body["user_input"])
        report = analyze(user_input)
        return report.dict()

    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"detail": f"处理错误: {str(e)}"}
        )

@app.post("/replacement")
async def replacement_endpoint(body: Dict[str, Any] = Body(...)):
    """处理替代品查询请求，支持 UTF-8 中文"""
    try:
        if "original_part_number" not in body:
            return JSONResponse(
                status_code=422,
                content={"detail": "缺少必需字段: original_part_number"}
            )

        original_part_number = str(body["original_part_number"])
        return replacement_report(original_part_number)

    except Exception as e:
        import traceback
        return JSONResponse(
            status_code=500,
            content={"detail": f"处理错误: {str(e)}"}
        )

