import json
from app.agent_orchestrator import analyze
from pathlib import Path

CASES = Path(__file__).parents[0] / "cases" / "dc_dc_cases.jsonl"


def run():
    out_lines = []
    with open(CASES, "r", encoding="utf-8") as f:
        for ln in f:
            case = json.loads(ln)
            cid = case.get("case_id")
            inp = case.get("input")
            expected = case.get("expected")
            report = analyze(inp)
            passed = True
            # quick checks
            cons = report.constraints
            if expected.get("category") and cons.category != expected.get("category"):
                passed = False
            if expected.get("topology") and cons.topology != expected.get("topology"):
                passed = False
            if expected.get("output_voltage_v") and cons.output_voltage_v != expected.get("output_voltage_v"):
                passed = False
            if expected.get("output_current_a") and cons.output_current_a != expected.get("output_current_a"):
                passed = False
            out_lines.append({"case_id": cid, "passed": passed, "recommended_count": len(report.recommended_parts)})
    # write results
    from pathlib import Path
    out = Path(__file__).parents[1] / "docs" / "eval_results.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(out_lines, f, ensure_ascii=False, indent=2)
    print("Eval finished. Results:")
    print(json.dumps(out_lines, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    run()

