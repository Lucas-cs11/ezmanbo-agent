"""Streamlit frontend for eZ-PLM Component Risk Agent.

Displays tool-call step cards, intermediate result collapsible panels,
score dashboards with component images, evidence chains, risk assessments,
and a three-report preview panel after selecting a solution.
"""

import base64
from collections import defaultdict
from io import BytesIO
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

# ---------- Page Config ----------
st.set_page_config(
    page_title="eZ-PLM Component Risk Agent",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = st.secrets.get("api_url", "http://localhost:8001")

# ---------- Neutral / Professional CSS ----------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: #1e293b;
        background: #f8fafc;
    }
    .main-header {
        font-size: 1.65rem;
        font-weight: 600;
        color: #0f172a;
        letter-spacing: -0.02em;
        margin-bottom: 0.15rem;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 0.5rem;
    }
    .sub-header {
        color: #64748b;
        font-size: 0.88rem;
        margin-bottom: 1.5rem;
        font-weight: 400;
    }
    .section-header {
        font-size: 1.05rem;
        font-weight: 600;
        color: #334155;
        margin: 1.2rem 0 0.4rem 0;
        border-left: 3px solid #64748b;
        padding-left: 0.65rem;
    }
    .section-caption {
        color: #94a3b8;
        font-size: 0.78rem;
        margin-bottom: 0.75rem;
    }

    /* Tool Step Cards */
    .tool-step-card {
        border-radius: 4px;
        padding: 0.8rem 0.95rem;
        margin: 0.45rem 0;
        border: 1px solid #e2e8f0;
        background: #ffffff;
        transition: border-color 0.15s;
    }
    .tool-step-card:hover { border-color: #94a3b8; }
    .tool-step-card.success { border-left: 3px solid #16a34a; }
    .tool-step-card.error { border-left: 3px solid #dc2626; }
    .tool-step-card.running {
        border-left: 3px solid #ca8a04;
        animation: pulse-neutral 1.8s infinite;
    }
    @keyframes pulse-neutral { 0%,100%{opacity:1;} 50%{opacity:0.65;} }
    .tool-step-header {
        display: flex; align-items: center; gap: 0.45rem; margin-bottom: 0.35rem;
    }
    .tool-step-icon {
        font-size: 1.1rem; width: 28px; height: 28px;
        display: flex; align-items: center; justify-content: center;
        border-radius: 3px; background: #f1f5f9; color: #475569;
    }
    .tool-step-title {
        font-weight: 600; font-size: 0.9rem; color: #1e293b; flex: 1;
    }
    .tool-step-status {
        font-size: 0.68rem; font-weight: 600; padding: 0.08rem 0.45rem;
        border-radius: 3px; text-transform: uppercase; letter-spacing: 0.03em;
    }
    .status-success { background: #dcfce7; color: #166534; }
    .status-error { background: #fee2e2; color: #991b1b; }
    .status-running { background: #fef9c3; color: #854d0e; }
    .tool-step-duration { font-size: 0.66rem; color: #94a3b8; margin-left: 0.25rem; }
    .tool-step-row {
        display: flex; gap: 0.35rem; margin: 0.18rem 0;
        font-size: 0.76rem; line-height: 1.4;
    }
    .tool-step-label { color: #64748b; white-space: nowrap; font-weight: 500; min-width: 52px; }
    .tool-step-value { color: #334155; word-break: break-all; }
    .tool-step-error {
        color: #dc2626; font-size: 0.76rem; background: #fef2f2;
        border-radius: 3px; padding: 0.3rem 0.5rem; margin-top: 0.3rem;
        border: 1px solid #fecaca;
    }

    /* Score Cards */
    .score-card {
        border-radius: 4px; padding: 0.9rem 1.1rem; margin: 0.45rem 0;
        border: 1px solid #e2e8f0; background: #ffffff; transition: box-shadow 0.15s;
    }
    .score-card:hover { box-shadow: 0 1px 6px rgba(0,0,0,0.05); }
    .score-card.recommended { border-left: 3px solid #16a34a; }
    .score-card.backup { border-left: 3px solid #ca8a04; }
    .score-card.not-recommended { border-left: 3px solid #dc2626; }
    .part-name {
        font-size: 0.95rem; font-weight: 600; color: #0f172a;
    }
    .part-meta { color: #64748b; font-size: 0.8rem; }
    .badge {
        display: inline-block; padding: 0.08rem 0.45rem;
        border-radius: 3px; font-size: 0.66rem; font-weight: 600;
        margin-right: 0.3rem; text-transform: uppercase; letter-spacing: 0.02em;
    }
    .badge-domestic { background: #dcfce7; color: #166534; }
    .badge-import { background: #f1f5f9; color: #475569; }
    .badge-auto { background: #e0f2fe; color: #075985; }
    .badge-active { background: #dcfce7; color: #166534; }
    .badge-obsolete { background: #fee2e2; color: #991b1b; }
    .badge-discontinued { background: #fef3c7; color: #92400e; }
    .score-bar-bg {
        background: #e2e8f0; border-radius: 3px; height: 6px;
        margin: 0.3rem 0; overflow: hidden;
    }
    .score-bar-fill { height: 6px; border-radius: 3px; transition: width 0.5s ease; }
    .evidence-block {
        background: #f8fafc; border-radius: 3px; padding: 0.6rem 0.8rem;
        margin: 0.22rem 0; border: 1px solid #e2e8f0; font-size: 0.8rem;
    }
    .evidence-type {
        display: inline-block; padding: 0.06rem 0.38rem;
        border-radius: 3px; font-size: 0.64rem; font-weight: 600;
        background: #e2e8f0; color: #475569; margin-right: 0.3rem;
        text-transform: uppercase; letter-spacing: 0.02em;
    }
    .risk-high { color: #dc2626; font-weight: 600; }
    .risk-medium { color: #ca8a04; font-weight: 600; }
    .risk-low { color: #16a34a; font-weight: 600; }
    .flow-arrow { text-align: center; color: #cbd5e1; font-size: 0.85rem; margin: -0.15rem 0; }
    .reason-tag {
        display: inline-block; background: #f1f5f9; border-radius: 3px;
        padding: 0.12rem 0.4rem; margin: 0.1rem 0.18rem 0.1rem 0;
        font-size: 0.7rem; color: #475569;
    }
    .metric-row {
        display: flex; justify-content: space-between; align-items: center;
        margin: 0.16rem 0; font-size: 0.76rem;
    }
    .metric-label { color: #64748b; }
    .metric-value { font-weight: 600; color: #1e293b; }

    /* Part Image */
    .part-image-wrap {
        text-align: center; margin: 0;
        border: 1px solid #e2e8f0; border-radius: 3px;
        overflow: hidden; background: #f8fafc;
    }
    .part-image-wrap img {
        width: 100%; height: auto; object-fit: contain; max-height: 160px;
    }
    .part-image-caption {
        font-size: 0.68rem; color: #94a3b8; padding: 0.2rem 0;
        text-align: center;
    }

    /* Report Preview Panel */
    .report-preview-header {
        font-size: 0.9rem; font-weight: 600; color: #0f172a;
        margin: 0 0 0.5rem 0;
    }
    .report-preview-subtitle {
        font-size: 0.75rem; color: #64748b; margin-bottom: 0.6rem;
    }
    .report-html-frame {
        border: 1px solid #e2e8f0; border-radius: 4px;
        padding: 1rem; background: #ffffff; max-height: 320px; overflow-y: auto;
        font-size: 0.82rem;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background: #ffffff; border-right: 1px solid #e2e8f0;
    }
    section[data-testid="stSidebar"] .stMarkdown h3,
    section[data-testid="stSidebar"] .stMarkdown h4 {
        color: #334155; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)


def _generate_report_html(
    report_type: str,
    candidates: List[Dict[str, Any]],
    constraints: Dict[str, Any],
    request_id: str,
) -> str:
    """Generate a self-contained HTML report string."""
    rec_list = [c for c in candidates if c.get("recommendation_level") == "recommended"]
    backup_list = [c for c in candidates if c.get("recommendation_level") == "backup"]
    notrec_list = [c for c in candidates if c.get("recommendation_level") == "not_recommended"]

    vin = constraints.get("input_voltage_nominal_v", "N/A")
    vout = constraints.get("output_voltage_v", "N/A")
    iout = constraints.get("output_current_a", "N/A")
    grade = constraints.get("grade", "N/A").upper()

    rows: List[str] = []
    rows.append(f"<h3>eZ-PLM Component Risk Agent — {request_id}</h3>")

    if report_type == "executive":
        rows.append(f"<p style='font-size:0.85rem;color:#64748b;'>Request: {request_id}</p>")
        rows.append("<hr>")
        rows.append("<h3>Executive Summary</h3>")
        rows.append(f"<p><strong>Requirement:</strong> Vin={vin}V, Vout={vout}V, Iout={iout}A, Grade={grade}</p>")
        rows.append(f"<p><strong>Total Candidates:</strong> {len(candidates)} | "
                     f"Recommended: {len(rec_list)} | Backup: {len(backup_list)} | "
                     f"Not Recommended: {len(notrec_list)}</p>")
        if rec_list:
            top = rec_list[0]
            p = top.get("part", {})
            s = top.get("score", {})
            rows.append("<h4>Top Recommendation</h4>")
            rows.append(f"<p><strong>{p.get('part_number','N/A')}</strong> by {p.get('manufacturer','N/A')}</p>")
            rows.append(f"<p>Score: {s.get('total_score',0):.0f}/100 | "
                         f"Stock: {p.get('stock','?')} | Price: ¥{p.get('unit_price_cny','?')}</p>")
    elif report_type == "technical":
        rows.append(f"<p style='font-size:0.85rem;color:#64748b;'>Request: {request_id}</p>")
        rows.append("<hr>")
        rows.append("<h3>Technical Selection Details</h3>")
        for c in candidates:
            p = c.get("part", {})
            s = c.get("score", {})
            level = c.get("recommendation_level", "")
            rows.append(f"<h4>{c.get('rank','-')}. {p.get('part_number','N/A')} — "
                         f"{s.get('total_score',0):.0f}/100 ({level.replace('_',' ').title()})</h4>")
            rows.append(f"<p>{p.get('manufacturer','N/A')} | "
                         f"Vin: {p.get('input_voltage_min_v','?')}–{p.get('input_voltage_max_v','?')}V | "
                         f"Iout: {p.get('output_current_max_a','?')}A | "
                         f"Temp: {p.get('temperature_min_c','?')}–{p.get('temperature_max_c','?')}°C | "
                         f"Package: {p.get('package','?')}</p>")
            rows.append("<hr>")
    elif report_type == "risk":
        rows.append(f"<p style='font-size:0.85rem;color:#64748b;'>Request: {request_id}</p>")
        rows.append("<hr>")
        rows.append("<h3>Risk Assessment</h3>")
        rows.append(f"<p><strong>Distribution:</strong> {len(rec_list)} Recommended | "
                     f"{len(backup_list)} Backup | {len(notrec_list)} Not Recommended</p>")
        obsolete = [c for c in candidates if c.get("part", {}).get("lifecycle_status") in ("obsolete", "discontinued")]
        low_stock = [c for c in candidates if c.get("part", {}).get("stock", 0) < 500]
        if obsolete:
            rows.append(f"<p style='color:#dc2626;'>Warning: {len(obsolete)} candidates are obsolete/discontinued.</p>")
        if low_stock:
            rows.append(f"<p style='color:#dc2626;'>Warning: {len(low_stock)} candidates have low stock (<500).</p>")

    css = """
        body{font-family:'Inter',-apple-system,sans-serif;color:#1e293b;background:#fff;padding:1rem;}
        h2{font-size:1.15rem;color:#0f172a;border-bottom:2px solid #e2e8f0;padding-bottom:0.25rem;}
        h3{font-size:1rem;color:#334155;margin:0.5rem 0 0.15rem;}
        h4{font-size:0.9rem;color:#475569;margin:0.4rem 0 0.1rem;}
        p{font-size:0.82rem;color:#475569;margin:0.15rem 0;line-height:1.5;}
        hr{border:0;border-top:1px solid #e2e8f0;margin:0.3rem 0;}
    """
    return f"<html><head><meta charset='utf-8'>{css}</head><body>{''.join(rows)}</body></html>"


# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("### ◈ eZ-PLM Agent")
    st.caption("Intelligent DC-DC Converter Selection")
    st.markdown("---")
    api_url_input = st.text_input(
        "Backend API URL", value=API_URL, key="api_url_input", label_visibility="visible"
    )
    st.markdown("---")
    st.markdown("#### Preset Examples")
    presets = {
        "车规级 12V→5V 3A 国产": "我需要一个 12V 转 5V、3A 的车规级降压方案，工作温度 -40°C 到 125°C，优先考虑国产替代。",
        "工业 24V→12V 2A": "需要 24V 转 12V、2A 的降压方案，工作温度 -40°C 到 85°C。",
        "大功率 24V→5V 10A": "输入 24V，输出 5V，电流 10A，高功率场景。",
        "低压 5V→3.3V 1A": "请给我一个 5V 到 3.3V 的降压芯片，输出 1A。",
        "车规 36V→5V 8A 国产": "36V 输入，输出 5V、8A，车规级，工作温度 -40°C 到 125°C，必须国产，低供应风险。",
        "性价比 12V→5V 1.2A": "12V 转 5V、1.2A 降压，室温使用，要求成本最低。",
    }
    selected_preset = st.selectbox("Quick load", list(presets.keys()), label_visibility="collapsed")
    st.markdown("---")
    st.caption("eZ-PLM Component Risk Agent v0.3")

# ---------- Main Layout ----------
st.markdown('<p class="main-header">◈ eZ-PLM Component Risk Agent</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">'
    'Intelligent DC-DC converter selection with multi-dimensional scoring & evidence traceability'
    '</p>',
    unsafe_allow_html=True,
)

col1, col2 = st.columns([3, 1])
with col1:
    user_input = st.text_area(
        "Requirement Description",
        value=presets[selected_preset],
        height=100,
        placeholder="Describe your DC-DC converter requirement in natural language...",
        label_visibility="visible",
    )
with col2:
    st.markdown("#### Guidance")
    st.caption(
        "• Specify input/output voltage & current\n"
        "• Define temperature range\n"
        "• Indicate automotive/industrial grade\n"
        "• Prefer domestic or low supply risk"
    )
    analyze_btn = st.button("Run Analysis", type="primary", use_container_width=True)
    clear_btn = st.button("Clear", use_container_width=True)

if clear_btn:
    st.rerun()

# ---------- Analysis Pipeline ----------
if analyze_btn and user_input.strip():
    effective_api = api_url_input.strip() or API_URL
    with st.spinner(
        "Running agent pipeline — parsing requirements, searching parts, "
        "scoring, generating evidence, assessing risks..."
    ):
        try:
            resp = requests.post(
                f"{effective_api}/analyze",
                json={"user_input": user_input.strip()},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.ConnectionError:
            st.error(
                "Cannot connect to backend. Start it with: "
                "`uvicorn app.main:app --port 8001 --reload`"
            )
            st.stop()
        except requests.Timeout:
            st.error("Backend request timed out (60s).")
            st.stop()
        except Exception as e:
            st.error(f"Backend error: {e}")
            st.stop()

    st.session_state._analysis_data = data
    candidates = data.get("candidates", []) or []
    constraints = data.get("constraints", {})
    tool_steps = data.get("tool_steps", []) or []
    request_id = data.get("request_id", "N/A")

    # ================================================================
    #  1. Agent Tool-Call Steps
    # ================================================================
    if tool_steps:
        st.markdown("---")
        st.markdown('<p class="section-header">Agent Inference Pipeline</p>', unsafe_allow_html=True)
        st.markdown('<p class="section-caption">Each card represents one tool call in the agent pipeline.</p>', unsafe_allow_html=True)

        cols_per_row = 3
        for row_start in range(0, len(tool_steps), cols_per_row):
            row_steps = tool_steps[row_start : row_start + cols_per_row]
            cols = st.columns(len(row_steps))
            for col, ts in zip(cols, row_steps):
                with col:
                    status = ts.get("status", "running")
                    icon = ts.get("tool_icon", "◇")
                    label = ts.get("tool_label", ts.get("tool_name", "Unknown"))
                    duration = ts.get("duration_ms", 0)
                    input_summary = ts.get("input_summary", "")
                    output_summary = ts.get("output_summary", "")
                    err_msg = ts.get("error_message", "")
                    intermediate = ts.get("intermediate_result", None)
                    step_idx = ts.get("step_index", 0)

                    st.markdown(f'<div class="tool-step-card {status}">', unsafe_allow_html=True)
                    st.markdown(
                        f'<div class="tool-step-header">'
                        f'<span class="tool-step-icon">{icon}</span>'
                        f'<span class="tool-step-title">#{step_idx} {label}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                    status_class = f"status-{status}"
                    status_text = {"success": "OK", "error": "FAIL", "running": "BUSY"}.get(
                        status, status.upper()
                    )
                    st.markdown(
                        f'<span class="tool-step-status {status_class}">{status_text}</span>'
                        f'<span class="tool-step-duration">{duration:.0f}ms</span>',
                        unsafe_allow_html=True,
                    )

                    if input_summary:
                        st.markdown(
                            f'<div class="tool-step-row">'
                            f'<span class="tool-step-label">Input:</span>'
                            f'<span class="tool-step-value">{input_summary}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    if output_summary:
                        st.markdown(
                            f'<div class="tool-step-row">'
                            f'<span class="tool-step-label">Output:</span>'
                            f'<span class="tool-step-value">{output_summary}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    if err_msg:
                        st.markdown(
                            f'<div class="tool-step-error">{err_msg}</div>',
                            unsafe_allow_html=True,
                        )

                    if intermediate is not None:
                        with st.expander(f"Intermediate — Step #{step_idx}", expanded=False):
                            st.json(intermediate)

                    st.markdown("</div>", unsafe_allow_html=True)

            if row_start + cols_per_row < len(tool_steps):
                st.markdown('<div class="flow-arrow">|</div>', unsafe_allow_html=True)

        # Pipeline summary metrics
        success_count = sum(1 for ts in tool_steps if ts.get("status") == "success")
        error_count = sum(1 for ts in tool_steps if ts.get("status") == "error")
        total_duration = sum(ts.get("duration_ms", 0) for ts in tool_steps)
        sm_cols = st.columns(4)
        with sm_cols[0]:
            st.metric("Total Steps", len(tool_steps))
        with sm_cols[1]:
            st.metric("Successful", success_count)
        with sm_cols[2]:
            st.metric("Failed", error_count, delta=f"-{error_count}" if error_count > 0 else "0")
        with sm_cols[3]:
            st.metric("Total Duration", f"{total_duration:.0f}ms")

    # ================================================================
    #  2. Parsed Constraints
    # ================================================================
    if constraints:
        st.markdown("---")
        st.markdown('<p class="section-header">Parsed Requirement Constraints</p>', unsafe_allow_html=True)
        with st.expander("View constraints", expanded=False):
            cs = constraints
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Category", cs.get("category") or "N/A")
                st.metric("Topology", cs.get("topology") or "N/A")
                st.metric("Application", cs.get("application") or "N/A")
                st.metric("Grade", cs.get("grade") or "N/A")
            with c2:
                st.metric(
                    "Input Voltage (nom)",
                    f"{cs.get('input_voltage_nominal_v')}V"
                    if cs.get("input_voltage_nominal_v")
                    else "N/A",
                )
                st.metric(
                    "Output Voltage",
                    f"{cs.get('output_voltage_v')}V"
                    if cs.get("output_voltage_v")
                    else "N/A",
                )
                st.metric(
                    "Output Current",
                    f"{cs.get('output_current_a')}A"
                    if cs.get("output_current_a")
                    else "N/A",
                )
            with c3:
                tmin = cs.get("temperature_min_c")
                tmax = cs.get("temperature_max_c")
                st.metric(
                    "Temp Range",
                    f"{tmin} ~ {tmax}°C"
                    if tmin is not None and tmax is not None
                    else "N/A",
                )
                prefs = cs.get("preferences", [])
                st.metric("Preferences", ", ".join(prefs) if prefs else "None")

    # ================================================================
    #  3. Score Summary Dashboard
    # ================================================================
    if candidates:
        st.markdown("---")
        st.markdown('<p class="section-header">Score Summary Dashboard</p>', unsafe_allow_html=True)
        rec_count = sum(1 for c in candidates if c.get("recommendation_level") == "recommended")
        backup_count = sum(1 for c in candidates if c.get("recommendation_level") == "backup")
        not_rec_count = sum(1 for c in candidates if c.get("recommendation_level") == "not_recommended")
        dash_cols = st.columns(4)
        with dash_cols[0]:
            st.metric("Total Candidates", len(candidates))
        with dash_cols[1]:
            st.metric("Recommended", rec_count)
        with dash_cols[2]:
            st.metric("Backup", backup_count)
        with dash_cols[3]:
            st.metric("Not Recommended", not_rec_count)

    # ================================================================
    #  4. Ranking & Score Breakdown (with part images)
    # ================================================================
    if candidates:
        st.markdown("---")
        st.markdown('<p class="section-header">Ranking & Score Breakdown</p>', unsafe_allow_html=True)

        level_emoji_map = {
            "recommended": "◆",
            "backup": "◇",
            "not_recommended": "○",
        }
        level_label_map = {
            "recommended": "Recommended",
            "backup": "Backup",
            "not_recommended": "Not Recommended",
        }

        for idx, sp in enumerate(candidates):
            part = sp.get("part", {})
            score = sp.get("score", {})
            rank = sp.get("rank", idx + 1)
            level = sp.get("recommendation_level", "not_recommended")
            card_class = f"score-card {level}"

            with st.container():
                st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

                # Row: image | info
                img_col, info_col = st.columns([1, 5])

                with img_col:
                    image_url = part.get("image_url", "")
                    if image_url:
                        st.markdown(
                            f'<div class="part-image-wrap">'
                            f'<img src="{image_url}" alt="{part.get("part_number","")}">'
                            f'</div>'
                            f'<div class="part-image-caption">{part.get("package","")}</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            '<div class="part-image-wrap" style="height:100px;display:flex;'
                            'align-items:center;justify-content:center;color:#94a3b8;font-size:0.7rem;">'
                            'No Image</div>',
                            unsafe_allow_html=True,
                        )

                with info_col:
                    # Row 1: rank + part info + recommendation level
                    ri1, ri2, ri3 = st.columns([0.4, 4.5, 2])
                    with ri1:
                        st.markdown(
                            f"<h2 style='margin:0;color:#475569;font-weight:700;'>{rank}</h2>",
                            unsafe_allow_html=True,
                        )
                    with ri2:
                        pn = part.get("part_number", "N/A")
                        mfr = part.get("manufacturer", "Unknown")
                        domestic = part.get("is_domestic", False)
                        auto = part.get("automotive_grade", False)
                        lifecycle = part.get("lifecycle_status", "N/A")
                        badges_html = ""
                        badges_html += (
                            '<span class="badge badge-domestic">Domestic</span>'
                            if domestic
                            else '<span class="badge badge-import">Import</span>'
                        )
                        if auto:
                            badges_html += '<span class="badge badge-auto">AUTO</span>'
                        lc_class = (
                            "badge-active"
                            if lifecycle == "active"
                            else "badge-obsolete"
                            if lifecycle == "obsolete"
                            else "badge-discontinued"
                        )
                        badges_html += f'<span class="badge {lc_class}">{lifecycle}</span>'
                        st.markdown(
                            f'<p class="part-name">{pn}&nbsp;&nbsp;'
                            f'<span class="part-meta">by {mfr}</span></p>{badges_html}',
                            unsafe_allow_html=True,
                        )
                    with ri3:
                        st.markdown(
                            f"<p style='text-align:right;font-weight:600;font-size:0.9rem;color:#475569;'>"
                            f"{level_emoji_map.get(level, '')} {level_label_map.get(level, level)}"
                            f"</p>",
                            unsafe_allow_html=True,
                        )

                    # Row 2: total score bar
                    total = score.get("total_score", 0)
                    if total >= 75:
                        bar_color = "#16a34a"
                    elif total >= 50:
                        bar_color = "#ca8a04"
                    else:
                        bar_color = "#dc2626"
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:0.4rem;margin:0.25rem 0;">'
                        f'<span style="font-weight:600;font-size:1.05rem;color:{bar_color};">{total:.0f}</span>'
                        f'<span style="font-size:0.73rem;color:#94a3b8;">/ 100</span>'
                        f'<div class="score-bar-bg" style="flex:1;">'
                        f'<div class="score-bar-fill" style="width:{total}%;background:{bar_color};"></div>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )

                    # Row 3: dimension sub-scores
                    dims = [
                        ("Param", score.get("parameter_match_score", 0)),
                        ("Supply", score.get("supply_risk_score", 0)),
                        ("Cost", score.get("cost_score", 0)),
                        ("Domestic", score.get("domestic_score", 0)),
                        ("Evidence", score.get("evidence_score", 0)),
                    ]
                    dim_cols = st.columns(len(dims))
                    for di, (dim_label, dim_val) in enumerate(dims):
                        if dim_val >= 80:
                            dc = "#16a34a"
                        elif dim_val >= 50:
                            dc = "#ca8a04"
                        else:
                            dc = "#dc2626"
                        with dim_cols[di]:
                            st.markdown(
                                f'<div class="metric-row">'
                                f'<span class="metric-label">{dim_label}</span>'
                                f'<span class="metric-value" style="color:{dc};">{dim_val:.0f}</span>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )

                    # Row 4: specs
                    specs = (
                        f"Vin: {part.get('input_voltage_min_v','?')}–{part.get('input_voltage_max_v','?')}V | "
                        f"Iout: {part.get('output_current_max_a','?')}A | "
                        f"Temp: {part.get('temperature_min_c','?')}–{part.get('temperature_max_c','?')}°C | "
                        f"Stock: {part.get('stock','?')} | "
                        f"Price: ¥{part.get('unit_price_cny','?')}"
                    )
                    st.caption(specs)

                    # Row 5: reasons
                    reasons = score.get("reasons", [])
                    if reasons:
                        tags_html = " ".join(
                            f'<span class="reason-tag">{r}</span>' for r in reasons
                        )
                        st.markdown(
                            f'<div style="margin-top:0.2rem;">{tags_html}</div>',
                            unsafe_allow_html=True,
                        )

                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No candidate parts matched your requirements.")

    # ================================================================
    #  5. Three-Report Preview (after selecting a solution)
    # ================================================================
    if candidates:
        st.markdown("---")
        st.markdown('<p class="section-header">Selection Reports</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="section-caption">'
            'Select a recommended solution below to preview all three analysis reports.'
            '</p>',
            unsafe_allow_html=True,
        )

        # Build candidate options for selection
        candidate_opts = [
            f"#{sp.get('rank',i+1)} {sp.get('part',{}).get('part_number','N/A')} "
            f"({sp.get('score',{}).get('total_score',0):.0f}/100) "
            f"— {sp.get('recommendation_level','').replace('_',' ').title()}"
            for i, sp in enumerate(candidates)
        ]

        selected_candidate_label = st.selectbox(
            "Choose a solution to generate reports:",
            candidate_opts,
            key="report_selector",
            label_visibility="visible",
        )

        if selected_candidate_label:
            # Extract the index
            selected_idx = candidate_opts.index(selected_candidate_label)
            selected_sp = candidates[selected_idx]
            selected_part = selected_sp.get("part", {})

            report_tab1, report_tab2, report_tab3 = st.tabs([
                "Executive Summary",
                "Technical Report",
                "Risk Assessment",
            ])

            # Generate reports for the selected solution only
            single_list = [selected_sp]

            with report_tab1:
                st.markdown(
                    '<p class="report-preview-header">Executive Summary</p>',
                    unsafe_allow_html=True,
                )
                html_exec = _generate_report_html(
                    "executive", single_list, constraints, request_id
                )
                st.markdown(
                    f'<div class="report-html-frame">{html_exec}</div>',
                    unsafe_allow_html=True,
                )
                # Download button
                b64 = base64.b64encode(html_exec.encode("utf-8")).decode()
                st.download_button(
                    label="Download Executive Summary (HTML)",
                    data=html_exec,
                    file_name=f"executive_summary_{request_id}.html",
                    mime="text/html",
                    key=f"dl_exec_{request_id}",
                )

            with report_tab2:
                st.markdown(
                    '<p class="report-preview-header">Technical Selection Report</p>',
                    unsafe_allow_html=True,
                )
                html_tech = _generate_report_html(
                    "technical", single_list, constraints, request_id
                )
                st.markdown(
                    f'<div class="report-html-frame">{html_tech}</div>',
                    unsafe_allow_html=True,
                )
                st.download_button(
                    label="Download Technical Report (HTML)",
                    data=html_tech,
                    file_name=f"technical_report_{request_id}.html",
                    mime="text/html",
                    key=f"dl_tech_{request_id}",
                )

            with report_tab3:
                st.markdown(
                    '<p class="report-preview-header">Risk Assessment Report</p>',
                    unsafe_allow_html=True,
                )
                html_risk = _generate_report_html(
                    "risk", single_list, constraints, request_id
                )
                st.markdown(
                    f'<div class="report-html-frame">{html_risk}</div>',
                    unsafe_allow_html=True,
                )
                st.download_button(
                    label="Download Risk Report (HTML)",
                    data=html_risk,
                    file_name=f"risk_assessment_{request_id}.html",
                    mime="text/html",
                    key=f"dl_risk_{request_id}",
                )

    # ================================================================
    #  6. Evidence Chain
    # ================================================================
    evidence = data.get("evidence", []) or []
    if evidence:
        st.markdown("---")
        st.markdown('<p class="section-header">Evidence Chain</p>', unsafe_allow_html=True)
        ev_by_part = defaultdict(list)
        for ev in evidence:
            ev_by_part[ev.get("part_number", "Unknown")].append(ev)

        tab_labels = list(ev_by_part.keys())
        if len(tab_labels) > 1:
            tabs = st.tabs(tab_labels)
            for tab, pn in zip(tabs, tab_labels):
                with tab:
                    for ev in ev_by_part[pn]:
                        conf = ev.get("confidence", 0)
                        if conf >= 0.9:
                            conf_color = "#16a34a"
                        elif conf >= 0.7:
                            conf_color = "#ca8a04"
                        else:
                            conf_color = "#dc2626"
                        st.markdown(
                            f'<div class="evidence-block">'
                            f'<span class="evidence-type">{ev.get("evidence_type","N/A")}</span>'
                            f'<strong>{ev.get("claim","N/A")}</strong>'
                            f'<span style="font-size:0.72rem;color:#94a3b8;margin-left:0.4rem;">'
                            f'source: {ev.get("source","N/A")}::{ev.get("source_field","")}'
                            f'</span>'
                            f'<span style="float:right;font-weight:600;color:{conf_color};">'
                            f'{conf:.0%}'
                            f'</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
        else:
            for ev in evidence:
                conf = ev.get("confidence", 0)
                if conf >= 0.9:
                    conf_color = "#16a34a"
                elif conf >= 0.7:
                    conf_color = "#ca8a04"
                else:
                    conf_color = "#dc2626"
                st.markdown(
                    f'<div class="evidence-block">'
                    f'<span class="evidence-type">{ev.get("evidence_type","N/A")}</span>'
                    f'<strong>{ev.get("claim","N/A")}</strong>'
                    f'<span style="font-size:0.72rem;color:#94a3b8;margin-left:0.4rem;">'
                    f'source: {ev.get("source","N/A")}::{ev.get("source_field","")}'
                    f'</span>'
                    f'<span style="float:right;font-weight:600;color:{conf_color};">'
                    f'{conf:.0%}'
                    f'</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    else:
        if candidates:
            st.markdown("---")
            st.info("No evidence records available.")

    # ================================================================
    #  7. Risk Assessment
    # ================================================================
    risks = data.get("risks")
    if risks:
        st.markdown("---")
        st.markdown('<p class="section-header">Risk Assessment</p>', unsafe_allow_html=True)
        overall = risks.get("overall_risk_level", "N/A")
        if "low" in str(overall).lower():
            risk_class = "risk-low"
        elif "medium" in str(overall).lower():
            risk_class = "risk-medium"
        else:
            risk_class = "risk-high"
        st.markdown(
            f"**Overall Risk:** <span class='{risk_class}'>{str(overall).upper()}</span>",
            unsafe_allow_html=True,
        )
        for ri in risks.get("risk_items", []):
            sev = ri.get("severity", "N/A")
            if "low" in str(sev).lower():
                sev_class = "risk-low"
            elif "medium" in str(sev).lower():
                sev_class = "risk-medium"
            else:
                sev_class = "risk-high"
            mitigation = f" — Mitigation: {ri.get('mitigation')}" if ri.get("mitigation") else ""
            st.markdown(
                f"- <span class='{sev_class}'>{str(sev).upper()}</span> "
                f"{ri.get('description','')}{mitigation}",
                unsafe_allow_html=True,
            )

    # ---------- Footer ----------
    st.markdown("---")
    st.caption(
        f"Agent v{data.get('ir_version', '0.3')} | "
        f"Request ID: {request_id} | "
        f"Tool Steps: {len(tool_steps)}"
    )