"""FastAPI backend serving the Agent analysis endpoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent import run_agent
from app.models import AnalyzeRequest, AnalyzeResponse

app = FastAPI(
    title="eZ-PLM Component Risk Agent",
    description="Intelligent DC-DC component selection with multi-dimensional scoring & evidence traceability",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "version": "0.2.0"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze_endpoint(req: AnalyzeRequest):
    """Run the full Agent pipeline and return scored candidates with tool steps."""
    return run_agent(req)