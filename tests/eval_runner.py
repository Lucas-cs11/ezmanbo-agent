"""
eval_runner.py — 端到端评测脚本

用法：
  # 纯规则模式（不需要 LLM key）
  PYTHONPATH=. python3 tests/eval_runner.py

  # LLM 增强模式（需要 .env 中配置 OPENAI_API_KEY）
  PYTHONPATH=. python3 tests/eval_runner.py --llm

  # 对比模式（同时跑纯规则和 LLM，输出差异）
  PYTHONPATH=. python3 tests/eval_runner.py --compare
"""

# ── load_dotenv 必须在 app.* 导入之前执行 ────────────────────────
# llm_client.py 在模块级别读取 OPENAI_API_KEY，若先 import 再 dotenv 则无效
import sys
import os

_dotenv_loaded = False
try:
    from dotenv import load_dotenv
    _dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if load_dotenv(_dotenv_path):
        _dotenv_loaded = True
except ImportError:
    pass

# ── 正常导入 ─────────────────────────────────────────────────────
import json
import time
from pathlib import Path
from app.agent_orchestrator import analyze

CASES = Path(__file__).parent / "cases" / "dc_dc_cases.jsonl"
OUT_DIR = Path(__file__).parents[1] / "docs"


def _check_case(case: dict, report) -> dict:
    """对单个 case 做字段级校验，返回详细结果。"""
    expected = case.get("expected", {})
    cons = report.constraints
    failures = []

    for field in ("category", "topology", "output_voltage_v", "output_current_a"):
        exp_val = expected.get(field)
        if exp_val is None:
            continue
        got_val = getattr(cons, field, None)
        if got_val != exp_val:
            failures.append(f"{field}: 期望={exp_val!r} 实际={got_val!r}")

    return {
        "case_id": case.get("case_id"),
        "input": case.get("input"),
        "passed": len(failures) == 0,
        "failures": failures,
        "recommended_count": len(report.recommended_parts),
        "risk_level": report.risks.overall_risk_level if report.risks else "n/a",
        "top1": (
            report.recommended_parts[0].part.part_number
            if report.recommended_parts else None
        ),
        "top1_score": (
            report.recommended_parts[0].score.total_score
            if report.recommended_parts else None
        ),
    }


def run_mode(label: str, use_llm: bool) -> list:
    """运行评测，返回结果列表。use_llm 控制是否激活 LLM key。"""
    original_key = os.environ.get("OPENAI_API_KEY", "")

    if not use_llm:
        # 临时屏蔽 key，强制纯规则
        os.environ["OPENAI_API_KEY"] = ""

    results = []
    with open(CASES, "r", encoding="utf-8") as f:
        for ln in f:
            if not ln.strip():
                continue
            case = json.loads(ln)
            t0 = time.time()
            report = analyze(case.get("input", ""))
            elapsed = round(time.time() - t0, 2)
            res = _check_case(case, report)
            res["elapsed_s"] = elapsed
            res["mode"] = label
            results.append(res)

    if not use_llm:
        # 恢复 key
        os.environ["OPENAI_API_KEY"] = original_key

    return results


def print_results(results: list, label: str):
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print(f"\n{'=' * 60}")
    print(f"模式: {label}  通过率: {passed}/{total}")
    print(f"{'=' * 60}")
    for r in results:
        status = "✅" if r["passed"] else "❌"
        rec = r["recommended_count"]
        top = f"TOP1={r['top1']}({r['top1_score']})" if r["top1"] else "无推荐"
        risk = r["risk_level"].upper()
        print(f"  {status} {r['case_id']:12s} | 推荐={rec:2d} | {top:35s} | 风险={risk}")
        for fail in r.get("failures", []):
            print(f"       ↳ FAIL: {fail}")


def compare_results(rule_results: list, llm_results: list):
    print(f"\n{'=' * 60}")
    print("对比：LLM 增强 vs 纯规则")
    print(f"{'=' * 60}")
    by_id = {r["case_id"]: r for r in rule_results}
    for lr in llm_results:
        cid = lr["case_id"]
        rr = by_id.get(cid, {})
        r_pass = "✅" if rr.get("passed") else "❌"
        l_pass = "✅" if lr["passed"] else "❌"
        r_rec = rr.get("recommended_count", "-")
        l_rec = lr["recommended_count"]
        diff = "  " if r_rec == l_rec else f" ↑{l_rec - r_rec:+d}"
        print(f"  {cid:12s} | 规则={r_pass}{r_rec:2d} | LLM={l_pass}{l_rec:2d}{diff}")


def save_results(results: list, suffix: str = ""):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUT_DIR / f"eval_results{suffix}.md"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n结果已写入: {out_path}")


def run():
    mode_compare = "--compare" in sys.argv
    mode_llm = "--llm" in sys.argv or mode_compare

    has_key = bool(os.environ.get("OPENAI_API_KEY", "").strip())
    if mode_llm and not has_key:
        print("⚠️  未检测到 OPENAI_API_KEY，LLM 路径将 fallback 到纯规则")

    # 纯规则评测（始终执行）
    rule_results = run_mode("rule-only", use_llm=False)
    print_results(rule_results, "纯规则模式")
    save_results(rule_results)

    # LLM 增强评测（按需）
    if mode_llm and has_key:
        llm_results = run_mode("llm-enhanced", use_llm=True)
        print_results(llm_results, "LLM 增强模式")
        save_results(llm_results, "_llm")
        if mode_compare:
            compare_results(rule_results, llm_results)


if __name__ == "__main__":
    run()
