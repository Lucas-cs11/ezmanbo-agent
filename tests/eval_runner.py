import json
import time
from pathlib import Path
from datetime import datetime
from app.agent_orchestrator import analyze

CASES = Path(__file__).parents[0] / "cases" / "dc_dc_cases.jsonl"
OUT_DIR = Path(__file__).parents[1] / "docs" / "eval_results"


def _color(level: str) -> str:
    return {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(level, "⚪")


def _level_emoji(level: str) -> str:
    m = {
        "recommended": "⭐",
        "backup": "🟡",
        "not_recommended": "🔴",
    }
    return m.get(level, "❓")


def _check_pass(report, expected: dict) -> dict:
    cons = report.constraints
    failures = []
    checks = {
        "category": (cons.category, expected.get("category")),
        "topology": (cons.topology, expected.get("topology")),
        "output_voltage_v": (cons.output_voltage_v, expected.get("output_voltage_v")),
        "output_current_a": (cons.output_current_a, expected.get("output_current_a")),
        "temperature_min_c": (cons.temperature_min_c, expected.get("temperature_min_c")),
        "temperature_max_c": (cons.temperature_max_c, expected.get("temperature_max_c")),
        "grade": (cons.grade, expected.get("grade")),
    }
    for field, (actual, exp) in checks.items():
        if exp is not None and actual != exp:
            failures.append(f"{field}: expected={exp}, got={actual}")
    # preferences: check that all expected preferences are present
    exp_prefs = expected.get("preferences", [])
    if exp_prefs:
        for p in exp_prefs:
            if p not in cons.preferences:
                failures.append(f"preference '{p}' missing (got {cons.preferences})")
    return {
        "passed": len(failures) == 0,
        "failures": failures,
        "constraints_parsed": cons.dict(),
    }


def run():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    lines = []

    with open(CASES, "r", encoding="utf-8") as f:
        for ln in f:
            if not ln.strip():
                continue
            case = json.loads(ln)
            cid = case.get("case_id")
            inp = case.get("input")
            expected = case.get("expected", {})

            t0 = time.perf_counter()
            try:
                report = analyze(inp)
                elapsed = time.perf_counter() - t0
                check = _check_pass(report, expected)
            except Exception as e:
                elapsed = time.perf_counter() - t0
                check = {"passed": False, "failures": [str(e)], "constraints_parsed": {}}
                report = None

            lines.append({
                "case_id": cid,
                "input": inp,
                "expected": expected,
                "check": check,
                "report": report.dict() if report else {},
                "elapsed_s": round(elapsed, 3),
            })

    # ---------- Build Markdown report ----------
    total = len(lines)
    passed = sum(1 for l in lines if l["check"]["passed"])
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = []
    md.append(f"# eZ-PLM Component Risk Agent — 评测报告")
    md.append(f"")
    md.append(f"**生成时间**：{now}  ")
    md.append(f"**用例总数**：{total}  ")
    md.append(f"**通过**：{passed} ✅  |  **失败**：{total - passed} ❌  ")
    md.append(f"**通过率**：{passed / total * 100:.1f}%  ")
    md.append(f"**评测模式**：纯规则模式，无 LLM 依赖  ")
    md.append(f"")
    md.append(f"---")
    md.append(f"")

    # Summary table
    md.append(f"## 📊 总览")
    md.append(f"")
    md.append(f"| 用例 ID | 输入摘要 | 解析通过 | 推荐数 | 风险等级 | 耗时(ms) |")
    md.append(f"|---------|----------|----------|--------|----------|----------|")
    for l in lines:
        cid = l["case_id"]
        inp_short = l["input"][:40] + ("..." if len(l["input"]) > 40 else "")
        chk = "✅" if l["check"]["passed"] else "❌"
        rec = len(l["report"].get("recommended_parts", []) or [])
        risk = l["report"].get("risks") or {}
        risk_level = risk.get("overall_risk_level", "N/A") if risk else "N/A"
        elapsed_ms = int(l["elapsed_s"] * 1000)
        md.append(f"| {cid} | {inp_short} | {chk} | {rec} | {_color(risk_level)} {risk_level} | {elapsed_ms}ms |")
    md.append(f"")

    # Detail per case
    md.append(f"---")
    md.append(f"")
    md.append(f"## 📋 逐用例详情")
    md.append(f"")

    for idx, l in enumerate(lines):
        cid = l["case_id"]
        chk = l["check"]
        rep = l["report"]
        elapsed_ms = int(l["elapsed_s"] * 1000)

        md.append(f"### {idx + 1}. {cid} {'✅' if chk['passed'] else '❌'}")
        md.append(f"")
        md.append(f"**输入**：{l['input']}  ")
        md.append(f"**耗时**：{elapsed_ms}ms  ")
        md.append(f"")

        if chk["failures"]:
            md.append(f"**解析失败项**：")
            for f in chk["failures"]:
                md.append(f"- ❌ {f}")
            md.append(f"")

        # Parsed constraints
        cons = chk.get("constraints_parsed", {})
        if cons:
            md.append(f"**解析约束**：")
            md.append(f"")
            md.append(f"| 字段 | 值 |")
            md.append(f"|------|-----|")
            for field in ["category", "topology", "application", "grade",
                          "input_voltage_nominal_v", "output_voltage_v", "output_current_a",
                          "temperature_min_c", "temperature_max_c"]:
                val = cons.get(field)
                if val is not None:
                    md.append(f"| {field} | {val} |")
            prefs = cons.get("preferences", [])
            must = cons.get("must_have", [])
            nice = cons.get("nice_to_have", [])
            if prefs:
                md.append(f"| preferences | {', '.join(prefs)} |")
            if must:
                md.append(f"| must_have | {', '.join(must)} |")
            if nice:
                md.append(f"| nice_to_have | {', '.join(nice)} |")
            md.append(f"")

        # Score breakdown
        candidates = rep.get("candidates", []) or []
        if candidates:
            md.append(f"**候选评分明细**（共 {len(candidates)} 个）：")
            md.append(f"")
            md.append(f"| # | 型号 | 厂商 | 国产 | 车规 | 总分 | 参数 | 供应 | 成本 | 国产 | 证据 | 推荐等级 |")
            md.append(f"|---|------|------|------|------|------|------|------|------|------|------|----------|")
            for sc in candidates:
                part = sc.get("part", {})
                score = sc.get("score", {})
                pn = part.get("part_number", "N/A")
                mfr = part.get("manufacturer", "?")
                dom = "🇨🇳" if part.get("is_domestic") else "🌍"
                auto = "🚗" if part.get("automotive_grade") else "-"
                total_s = score.get("total_score", 0)
                pm = score.get("parameter_match_score", 0)
                sr = score.get("supply_risk_score", 0)
                cs = score.get("cost_score", 0)
                ds = score.get("domestic_score", 0)
                es = score.get("evidence_score", 0)
                rl = sc.get("recommendation_level", "N/A")
                md.append(f"| {sc.get('rank','-')} | {pn} | {mfr} | {dom} | {auto} | **{total_s:.0f}** | {pm:.0f} | {sr:.0f} | {cs:.0f} | {ds:.0f} | {es:.0f} | {_level_emoji(rl)} {rl} |")
            md.append(f"")

            # Top-1 reasons
            top = candidates[0]
            reasons = top.get("score", {}).get("reasons", [])
            if reasons:
                md.append(f"**TOP1 评分原因**：")
                for r in reasons:
                    md.append(f"- {r}")
                md.append(f"")

        # Evidence
        evidence = rep.get("evidence", []) or []
        if evidence:
            md.append(f"**证据链**（共 {len(evidence)} 条）：")
            md.append(f"")
            md.append(f"| 器件 | 证据类型 | 声明 | 置信度 | 需人工 |")
            md.append(f"|------|----------|------|--------|--------|")
            for ev in evidence[:10]:  # limit to 10
                pn = ev.get("part_number", "-")
                et = ev.get("evidence_type", "N/A")
                claim = ev.get("claim", "")[:60]
                conf = ev.get("confidence", 0)
                hr = "⚠️" if ev.get("need_human_review") else ""
                md.append(f"| {pn} | `{et}` | {claim} | {conf:.0%} | {hr} |")
            if len(evidence) > 10:
                md.append(f"| ... | ... | _(共 {len(evidence)} 条，仅展示前 10 条)_ | ... | ... |")
            md.append(f"")

        # Risk
        risk = rep.get("risks")
        if risk:
            md.append(f"**风险评估**：{_color(risk.get('overall_risk_level','N/A'))} {risk.get('overall_risk_level','N/A')}")
            md.append(f"")
            items = risk.get("risk_items", []) or []
            for ri in items:
                sev = ri.get("severity", "N/A")
                desc = ri.get("description", "")
                mit = ri.get("mitigation", "")
                md.append(f"- {_color(sev)} **{sev}** — {desc}" + (f" _(缓解: {mit})_" if mit else ""))
            md.append(f"")

        md.append(f"---")
        md.append(f"")

    # Footer
    md.append(f"")
    md.append(f"*报告由 `tests/eval_runner.py` 自动生成，IR version: {rep.get('ir_version', '0.1') if rep else 'N/A'}*")
    md.append(f"")

    report_path = OUT_DIR / "eval_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md))

    # Also write JSON summary
    json_path = OUT_DIR / "eval_summary.json"
    json_out = []
    for l in lines:
        json_out.append({
            "case_id": l["case_id"],
            "passed": l["check"]["passed"],
            "failures": l["check"]["failures"],
            "recommended_count": len(l["report"].get("recommended_parts", []) or []),
            "candidate_count": len(l["report"].get("candidates", []) or []),
            "risk_level": (l["report"].get("risks") or {}).get("overall_risk_level", "N/A"),
            "elapsed_s": l["elapsed_s"],
        })
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"total": total, "passed": passed, "pass_rate": f"{passed / total * 100:.1f}%", "results": json_out}, f, ensure_ascii=False, indent=2)

    import sys
    # Avoid UnicodeEncodeError on Windows GBK terminals
    if hasattr(sys.stdout, "reconfigure") and sys.stdout.encoding.lower() in ("gbk", "cp936", "gb2312"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    print(f"Eval complete: {passed}/{total} passed ({passed / total * 100:.1f}%)")
    print(f"Markdown report: {report_path}")
    print(f"JSON summary:   {json_path}")


if __name__ == "__main__":
    run()