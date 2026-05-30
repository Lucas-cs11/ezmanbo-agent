"""
eval_for_paper.py  --  Run all test cases and generate LaTeX tables + matplotlib figures.

Usage:
    PYTHONPATH=. python3 scripts/eval_for_paper.py

Outputs:
    latex-paper/tables/*.tex   -- LaTeX table fragments
    latex-paper/figures/*.pdf  -- Charts for the paper
"""

import json, os, sys, time, statistics
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime

# ── Ensure project root importable ──
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.agent_orchestrator import analyze
from app.schemas import SelectionReport

# ── Paths ──
CASES_DIR  = ROOT / "tests" / "cases"
TABLE_DIR  = ROOT / "latex-paper" / "tables"
FIG_DIR    = ROOT / "latex-paper" / "figures"
TABLE_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

# ── Matplotlib config (non-interactive, CJK support) ──
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
try:
    plt.rcParams["font.sans-serif"] = ["PingFang SC", "Heiti SC", "SimHei", "DejaVu Sans"]
except Exception:
    pass
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 150


# =====================================================================
#  1. Load & Run
# =====================================================================

def load_cases():
    """Load all JSONL test case files."""
    cases = []
    for p in sorted(CASES_DIR.glob("*.jsonl")):
        with open(p, "r", encoding="utf-8") as f:
            for ln in f:
                if ln.strip():
                    cases.append(json.loads(ln))
    return cases


def check_pass(report: SelectionReport, expected: dict):
    cons = report.constraints
    failures = []
    checks = {
        "category":          (cons.category,          expected.get("category")),
        "topology":          (cons.topology,          expected.get("topology")),
        "output_voltage_v":  (cons.output_voltage_v,  expected.get("output_voltage_v")),
        "output_current_a":  (cons.output_current_a,  expected.get("output_current_a")),
        "temperature_min_c": (cons.temperature_min_c, expected.get("temperature_min_c")),
        "temperature_max_c": (cons.temperature_max_c, expected.get("temperature_max_c")),
        "grade":             (cons.grade,             expected.get("grade")),
    }
    for field, (actual, exp) in checks.items():
        if exp is not None and actual != exp:
            failures.append(field)
    exp_prefs = expected.get("preferences", [])
    for p in exp_prefs:
        if p not in cons.preferences:
            failures.append(f"pref:{p}")
    return failures


def run_all():
    cases = load_cases()
    results = []
    for c in cases:
        cid = c["case_id"]
        inp = c["input"]
        expected = c.get("expected", {})
        t0 = time.perf_counter()
        try:
            report = analyze(inp)
            elapsed = time.perf_counter() - t0
            failures = check_pass(report, expected)
        except Exception as e:
            elapsed = time.perf_counter() - t0
            report = None
            failures = [str(e)]
        results.append({
            "case_id":    cid,
            "input":      inp,
            "expected":   expected,
            "report":     report,
            "failures":   failures,
            "passed":     len(failures) == 0,
            "elapsed_s":  elapsed,
        })
        status = "PASS" if len(failures) == 0 else f"FAIL({','.join(failures)})"
        print(f"  [{status}] {cid} ({elapsed:.3f}s)")
    return results


# =====================================================================
#  2. Metrics Extraction
# =====================================================================

def extract_metrics(results):
    m = {}
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    m["total"] = total
    m["passed"] = passed
    m["pass_rate"] = passed / total if total else 0

    # Per-field parse accuracy
    field_checks = defaultdict(lambda: {"total": 0, "correct": 0})
    for r in results:
        exp = r["expected"]
        if r["report"] is None:
            continue
        cons = r["report"].constraints
        for field in ["category", "topology", "output_voltage_v", "output_current_a",
                      "temperature_min_c", "temperature_max_c", "grade"]:
            exp_val = exp.get(field)
            if exp_val is not None:
                field_checks[field]["total"] += 1
                if getattr(cons, field) == exp_val:
                    field_checks[field]["correct"] += 1
    m["field_accuracy"] = {k: v["correct"]/v["total"] if v["total"] else 0
                           for k, v in field_checks.items()}

    # Scoring stats
    all_scores = []
    param_scores = []
    supply_scores = []
    rec_counts = []
    cand_counts = []
    for r in results:
        if r["report"] is None:
            continue
        rep = r["report"]
        cands = rep.candidates or []
        cand_counts.append(len(cands))
        recs = rep.recommended_parts or []
        rec_counts.append(len(recs))
        for c in cands:
            s = c.score
            all_scores.append(s.total_score)
            param_scores.append(s.parameter_match_score)
            supply_scores.append(s.supply_risk_score)

    m["score_stats"] = {
        "total":  _stats(all_scores),
        "param":  _stats(param_scores),
        "supply": _stats(supply_scores),
    }
    m["rec_count_dist"]  = Counter(rec_counts)
    m["cand_count_dist"] = Counter(cand_counts)

    # Risk level distribution
    risk_levels = []
    risk_type_counts = Counter()
    for r in results:
        if r["report"] is None:
            continue
        risks = r["report"].risks
        if risks:
            risk_levels.append(risks.overall_risk_level)
            for item in (risks.risk_items or []):
                risk_type_counts[item.risk_type] += 1
    m["risk_dist"] = Counter(risk_levels)
    m["risk_type_counts"] = risk_type_counts

    # Evidence stats
    ev_counts = []
    ev_confs = []
    human_review_count = 0
    ev_total = 0
    for r in results:
        if r["report"] is None:
            continue
        evidence = r["report"].evidence or []
        ev_counts.append(len(evidence))
        for ev in evidence:
            ev_confs.append(ev.confidence)
            ev_total += 1
            if ev.need_human_review:
                human_review_count += 1
    m["evidence_stats"] = {
        "per_case": _stats(ev_counts),
        "confidence": _stats(ev_confs),
        "total": ev_total,
        "human_review": human_review_count,
    }

    # Latency
    elapsed_list = [r["elapsed_s"] for r in results]
    m["latency"] = _stats(elapsed_list)

    # Category breakdown
    cat_results = defaultdict(lambda: {"total": 0, "passed": 0})
    for r in results:
        cat = r["case_id"].split("_")[0]  # dc or ldo
        cat_results[cat]["total"] += 1
        if r["passed"]:
            cat_results[cat]["passed"] += 1
    m["cat_results"] = dict(cat_results)

    return m


def _stats(values):
    if not values:
        return {"mean": 0, "median": 0, "std": 0, "min": 0, "max": 0, "count": 0}
    return {
        "mean":   round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "std":    round(statistics.stdev(values), 2) if len(values) > 1 else 0,
        "min":    round(min(values), 2),
        "max":    round(max(values), 2),
        "count":  len(values),
    }


# =====================================================================
#  3. LaTeX Table Generation
# =====================================================================

def gen_tables(results, metrics):
    # ── Table 1: Summary of all test cases ──
    rows = []
    for r in results:
        cid = r["case_id"]
        passed = r["passed"]
        rep = r["report"]
        if rep:
            rec_n = len(rep.recommended_parts or [])
            cand_n = len(rep.candidates or [])
            top_score = rep.candidates[0].score.total_score if rep.candidates else 0
            risk = rep.risks.overall_risk_level if rep.risks else "N/A"
        else:
            rec_n = cand_n = top_score = 0
            risk = "ERR"
        elapsed_ms = int(r["elapsed_s"] * 1000)
        mark = r"$\checkmark$" if passed else r"$\times$"
        risk_str = risk.upper()
        rows.append(f"    {cid} & {mark} & {cand_n} & {rec_n} & {top_score:.1f} & {risk_str} & {elapsed_ms} \\\\")

    total = metrics["total"]
    passed = metrics["passed"]
    rate = metrics["pass_rate"] * 100

    tex = rf"""\begin{{table}}[H]
\centering
\caption{{端到端评测结果汇总（{total}条用例，通过率{rate:.1f}\%）}}
\label{{tab:eval_summary}}
\small
\begin{{tabular}}{{lcccrllr}}
\toprule
\textbf{{用例}} & \textbf{{通过}} & \textbf{{候选}} & \textbf{{推荐}} & \textbf{{首选得分}} & \textbf{{风险}} & \textbf{{耗时/ms}} \\
\midrule
{chr(10).join(rows)}
\bottomrule
\end{{tabular}}
\end{{table}}"""
    _write_tex("eval_summary", tex)

    # ── Table 2: Parse accuracy by field ──
    fa = metrics["field_accuracy"]
    field_names = {
        "category": "类别", "topology": "拓扑", "output_voltage_v": "输出电压",
        "output_current_a": "输出电流", "temperature_min_c": "温度下限",
        "temperature_max_c": "温度上限", "grade": "器件等级",
    }
    fa_rows = []
    for field, cn_name in field_names.items():
        acc = fa.get(field, 0)
        fa_rows.append(f"    {cn_name} & {acc*100:.1f}\\% \\\\")

    tex2 = rf"""\begin{{table}}[H]
\centering
\caption{{需求解析各约束字段准确率}}
\label{{tab:parse_accuracy}}
\small
\begin{{tabular}}{{lr}}
\toprule
\textbf{{约束字段}} & \textbf{{准确率}} \\
\midrule
{chr(10).join(fa_rows)}
\bottomrule
\end{{tabular}}
\end{{table}}"""
    _write_tex("parse_accuracy", tex2)

    # ── Table 3: Scoring statistics ──
    ss = metrics["score_stats"]
    tex3 = rf"""\begin{{table}}[H]
\centering
\caption{{评分统计（全部候选器件）}}
\label{{tab:score_stats}}
\small
\begin{{tabular}}{{lrrrrr}}
\toprule
\textbf{{维度}} & \textbf{{均值}} & \textbf{{中位数}} & \textbf{{标准差}} & \textbf{{最小值}} & \textbf{{最大值}} \\
\midrule
    综合得分 & {ss['total']['mean']:.1f} & {ss['total']['median']:.1f} & {ss['total']['std']:.1f} & {ss['total']['min']:.1f} & {ss['total']['max']:.1f} \\
    参数匹配分 & {ss['param']['mean']:.1f} & {ss['param']['median']:.1f} & {ss['param']['std']:.1f} & {ss['param']['min']:.1f} & {ss['param']['max']:.1f} \\
    供应链分 & {ss['supply']['mean']:.1f} & {ss['supply']['median']:.1f} & {ss['supply']['std']:.1f} & {ss['supply']['min']:.1f} & {ss['supply']['max']:.1f} \\
\bottomrule
\end{{tabular}}
\end{{table}}"""
    _write_tex("score_stats", tex3)

    # ── Table 4: Risk distribution ──
    rd = metrics["risk_dist"]
    tex4 = rf"""\begin{{table}}[H]
\centering
\caption{{风险等级分布}}
\label{{tab:risk_dist}}
\small
\begin{{tabular}}{{lr}}
\toprule
\textbf{{风险等级}} & \textbf{{用例数}} \\
\midrule
    HIGH & {rd.get('high', 0)} \\
    MEDIUM & {rd.get('medium', 0)} \\
    LOW & {rd.get('low', 0)} \\
\bottomrule
\end{{tabular}}
\end{{table}}"""
    _write_tex("risk_dist", tex4)

    # ── Table 5: Evidence statistics ──
    es = metrics["evidence_stats"]
    tex5 = rf"""\begin{{table}}[H]
\centering
\caption{{证据链统计}}
\label{{tab:evidence_stats}}
\small
\begin{{tabular}}{{lr}}
\toprule
\textbf{{指标}} & \textbf{{值}} \\
\midrule
    证据总条数 & {es['total']} \\
    每用例平均条数 & {es['per_case']['mean']:.1f} \\
    平均置信度 & {es['confidence']['mean']:.2f} \\
    需人工复核条数 & {es['human_review']} \\
\bottomrule
\end{{tabular}}
\end{{table}}"""
    _write_tex("evidence_stats", tex5)


def _write_tex(name, content):
    path = TABLE_DIR / f"{name}.tex"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  [TABLE] {path}")


# =====================================================================
#  4. Figure Generation
# =====================================================================

def gen_figures(results, metrics):
    # ── Fig 1: Score distribution histogram ──
    all_scores = []
    for r in results:
        if r["report"] is None:
            continue
        for c in (r["report"].candidates or []):
            all_scores.append(c.score.total_score)

    if all_scores:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.hist(all_scores, bins=20, color="#4A90D9", edgecolor="white", alpha=0.85)
        ax.set_xlabel("Total Score", fontsize=10)
        ax.set_ylabel("Count", fontsize=10)
        ax.set_title("Score Distribution of All Candidates", fontsize=11)
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        fig.savefig(FIG_DIR / "score_distribution.pdf")
        plt.close(fig)
        print(f"  [FIG] {FIG_DIR / 'score_distribution.pdf'}")

    # ── Fig 2: Risk level pie chart ──
    rd = metrics["risk_dist"]
    if rd:
        labels = []
        sizes = []
        colors_map = {"high": "#E74C3C", "medium": "#F39C12", "low": "#27AE60"}
        for level in ["high", "medium", "low"]:
            if rd.get(level, 0) > 0:
                labels.append(level.upper())
                sizes.append(rd[level])
        if sizes:
            fig, ax = plt.subplots(figsize=(4.5, 3.5))
            cs = [colors_map.get(l.lower(), "#999") for l in labels]
            wedges, texts, autotexts = ax.pie(
                sizes, labels=labels, colors=cs, autopct="%1.0f%%",
                startangle=90, textprops={"fontsize": 10})
            ax.set_title("Risk Level Distribution", fontsize=11)
            fig.tight_layout()
            fig.savefig(FIG_DIR / "risk_distribution.pdf")
            plt.close(fig)
            print(f"  [FIG] {FIG_DIR / 'risk_distribution.pdf'}")

    # ── Fig 3: Latency bar chart per case ──
    case_ids = [r["case_id"] for r in results]
    latencies = [r["elapsed_s"] * 1000 for r in results]  # ms
    if case_ids:
        fig, ax = plt.subplots(figsize=(10, 3.5))
        x = range(len(case_ids))
        bars = ax.bar(x, latencies, color="#4A90D9", alpha=0.8, width=0.7)
        ax.set_xticks(x)
        ax.set_xticklabels(case_ids, rotation=60, ha="right", fontsize=6)
        ax.set_ylabel("Latency (ms)", fontsize=10)
        ax.set_title("End-to-End Latency per Test Case", fontsize=11)
        ax.grid(axis="y", alpha=0.3)
        # highlight outliers (>1000ms)
        for i, v in enumerate(latencies):
            if v > 1000:
                bars[i].set_color("#E74C3C")
        fig.tight_layout()
        fig.savefig(FIG_DIR / "latency_per_case.pdf")
        plt.close(fig)
        print(f"  [FIG] {FIG_DIR / 'latency_per_case.pdf'}")

    # ── Fig 4: Parse accuracy bar chart ──
    fa = metrics["field_accuracy"]
    field_names = {
        "category": "Category", "topology": "Topology",
        "output_voltage_v": "Vout", "output_current_a": "Iout",
        "temperature_min_c": "Tmin", "temperature_max_c": "Tmax",
        "grade": "Grade",
    }
    labels_fa = []
    vals_fa = []
    for field, cn in field_names.items():
        if field in fa:
            labels_fa.append(cn)
            vals_fa.append(fa[field] * 100)
    if labels_fa:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        bars = ax.bar(labels_fa, vals_fa, color="#27AE60", alpha=0.85, edgecolor="white")
        ax.set_ylim(0, 105)
        ax.set_ylabel("Accuracy (%)", fontsize=10)
        ax.set_title("Requirement Parsing Accuracy by Field", fontsize=11)
        ax.grid(axis="y", alpha=0.3)
        for bar, v in zip(bars, vals_fa):
            ax.text(bar.get_x() + bar.get_width()/2, v + 1, f"{v:.0f}%",
                    ha="center", va="bottom", fontsize=8)
        fig.tight_layout()
        fig.savefig(FIG_DIR / "parse_accuracy.pdf")
        plt.close(fig)
        print(f"  [FIG] {FIG_DIR / 'parse_accuracy.pdf'}")

    # ── Fig 5: Evidence confidence distribution ──
    ev_confs = []
    for r in results:
        if r["report"] is None:
            continue
        for ev in (r["report"].evidence or []):
            ev_confs.append(ev.confidence)
    if ev_confs:
        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.hist(ev_confs, bins=15, color="#8E44AD", edgecolor="white", alpha=0.85)
        ax.set_xlabel("Confidence", fontsize=10)
        ax.set_ylabel("Count", fontsize=10)
        ax.set_title("Evidence Confidence Distribution", fontsize=11)
        ax.grid(axis="y", alpha=0.3)
        fig.tight_layout()
        fig.savefig(FIG_DIR / "evidence_confidence.pdf")
        plt.close(fig)
        print(f"  [FIG] {FIG_DIR / 'evidence_confidence.pdf'}")


# =====================================================================
#  Main
# =====================================================================

def main():
    print(f"=== eval_for_paper.py === {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"Running all test cases from {CASES_DIR} ...\n")

    results = run_all()

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    print(f"\n--- Results: {passed}/{total} passed ({passed/total*100:.1f}%) ---\n")

    print("Extracting metrics ...")
    metrics = extract_metrics(results)

    print("Generating LaTeX tables ...")
    gen_tables(results, metrics)

    print("Generating figures ...")
    gen_figures(results, metrics)

    # Save raw metrics JSON
    metrics_path = TABLE_DIR / "metrics.json"
    serializable = json.loads(json.dumps(metrics, default=str))
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(serializable, f, ensure_ascii=False, indent=2)
    print(f"\n  [JSON] {metrics_path}")

    print("\nDone!")


if __name__ == "__main__":
    main()
