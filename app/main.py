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
    report = analyze(body.user_input)
    return report.dict()

class ReplacementRequest(BaseModel):
    original_part_number: str

@app.post("/replacement")
async def replacement_endpoint(body: ReplacementRequest):
    return replacement_report(body.original_part_number)

