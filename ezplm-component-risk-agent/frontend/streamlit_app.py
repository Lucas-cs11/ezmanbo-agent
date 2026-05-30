"""Streamlit frontend for eZ-PLM Component Risk Agent.

Displays tool-call step cards, intermediate result collapsible panels,
score dashboards, evidence chains, and risk assessments.
"""

import json
from collections import defaultdict

import requests
import streamlit as st

# ---------- Page Config ----------
st.set_page_config(
    page_title="eZ-PLM Component Risk Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = st.secrets.get("api_url", "http://localhost:8001")

# ---------- Custom CSS ----------
st.markdown("""
<style>
    /* ---------- Layout ---------- */
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #6b7280;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }

    /* ---------- Tool Step Cards ---------- */
    .tool-step-card {
        border-radius: 12px;
        padding: 1rem 1.2rem;
        margin: 0.6rem 0;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        background: #ffffff;
        transition: box-shadow 0.2s;
    }
    .tool-step-card:hover {
        box-shadow: 0 4px 14px rgba(0,0,0,0.08);
    }
    .tool-step-card.success {
        border-left: 5px solid #10b981;
    }
    .tool-step-card.error {
        border-left: 5px solid #ef4444;
    }
    .tool-step-card.running {
        border-left: 5px solid #f59e0b;
        animation: pulse 1.5s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    .tool-step-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-bottom: 0.5rem;
    }
    .tool-step-icon {
        font-size: 1.5rem;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 10px;
        background: #f3f4f6;
    }
    .tool-step-title {
        font-weight: 700;
        font-size: 1rem;
        color: #1f2937;
        flex: 1;
    }
    .tool-step-status {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
    }
    .status-success { background: #d1fae5; color: #065f46; }
    .status-error { background: #fee2e2; color: #991b1b; }
    .status-running { background: #fef3c7; color: #92400e; }
    .tool-step-duration {
        font-size: 0.72rem;
        color: #9ca3af;
        margin-left: 0.4rem;
    }
    .tool-step-row {
        display: flex;
        gap: 0.5rem;
        margin: 0.25rem 0;
        font-size: 0.82rem;
        line-height: 1.5;
    }
    .tool-step-label {
        color: #6b7280;
        white-space: nowrap;
        font-weight: 500;
    }
    .tool-step-value {
        color: #374151;
        word-break: break-all;
    }
    .tool-step-error {
        color: #dc2626;
        font-size: 0.82rem;
        background: #fef2f2;
        border-radius: 6px;
        padding: 0.4rem 0.6rem;
        margin-top: 0.4rem;
        border: 1px solid #fecaca;
    }

    /* ---------- Intermediate Result Panel ---------- */
    .intermediate-toggle {
        font-size: 0.78rem;
        color: #667eea;
        cursor: pointer;
        user-select: none;
        margin-top: 0.3rem;
        display: inline-block;
        font-weight: 500;
    }
    .intermediate-toggle:hover {
        text-decoration: underline;
    }
    .intermediate-json {
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 0.8rem;
        font-size: 0.78rem;
        max-height: 300px;
        overflow-y: auto;
        margin-top: 0.5rem;
        white-space: pre-wrap;
        word-break: break-all;
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        color: #374151;
    }

    /* ---------- Score Cards ---------- */
    .score-card {
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 0.6rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        background: linear-gradient(135deg, #f0f4ff 0%, #faf5ff 100%);
    }
    .score-card.recommended {
        border-left-color: #10b981;
        background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
    }
    .score-card.backup {
        border-left-color: #f59e0b;
        background: linear-gradient(135deg, #fffbeb 0%, #fefce8 100%);
    }
    .score-card.not-recommended {
        border-left-color: #ef4444;
        background: linear-gradient(135deg, #fef2f2 0%, #fff5f5 100%);
    }
    .part-name {
        font-size: 1.1rem;
        font-weight: 700;
        color: #1f2937;
    }
    .part-meta {
        color: #6b7280;
        font-size: 0.85rem;
    }
    .badge {
        display: inline-block;
        padding: 0.15rem 0.55rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-right: 0.4rem;
    }
    .badge-domestic { background: #d1fae5; color: #065f46; }
    .badge-import { background: #fee2e2; color: #991b1b; }
    .badge-auto { background: #dbeafe; color: #1e40af; }
    .badge-active { background: #d1fae5; color: #065f46; }
    .badge-obsolete { background: #fecaca; color: #991b1b; }
    .badge-discontinued { background: #fed7aa; color: #9a3412; }
    .score-bar-bg {
        background: #e5e7eb;
        border-radius: 999px;
        height: 8px;
        margin: 0.4rem 0;
        overflow: hidden;
    }
    .score-bar-fill {
        height: 8px;
        border-radius: 999px;
        transition: width 0.6s ease;
    }
    .evidence-block {
        background: #f9fafb;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        margin: 0.3rem 0;
        border: 1px solid #e5e7eb;
        font-size: 0.85rem;
    }
    .evidence-type {
        display: inline-block;
        padding: 0.1rem 0.45rem;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        background: #ede9fe;
        color: #5b21b6;
        margin-right: 0.4rem;
    }
    .risk-high { color: #dc2626; font-weight: 700; }
    .risk-medium { color: #d97706; font-weight: 700; }
    .risk-low { color: #059669; font-weight: 700; }

    /* Agent Flow Connector */
    .flow-arrow {
        text-align: center;
        color: #c4b5fd;
        font-size: 1.2rem;
        margin: -0.3rem 0;
    }
    .reason-tag {
        display: inline-block;
        background: #f3f4f6;
        border-radius: 6px;
        padding: 0.2rem 0.5rem;
        margin: 0.15rem 0.25rem 0.15rem 0;
        font-size: 0.78rem;
        color: #374151;
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 0.2rem 0;
        font-size: 0.82rem;
    }
    .metric-label { color: #6b7280; }
    .metric-value { font-weight: 600; color: #1f2937; }
</style>
""", unsafe_allow_html=True)

# ---------- Sidebar ----------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/electronics.png", width=72)
    st.markdown("### ⚙️ Settings")
    api_url_input = st.text_input("Backend API URL", value=API_URL, key="api_url_input")
    st.markdown("---")
    st.markdown("### 📋 Preset Examples")
    presets = {
        "车规级 12V→5V 3A 国产": "我需要一个 12V 转 5V、3A 的车规级降压方案，工作温度 -40°C 到 125°C，优先考虑国产替代。",
        "工业 24V→12V 2A": "需要 24V 转 12V、2A 的降压方案，工作温度 -40°C 到 85°C。",
        "大功率 24V→5V 10A": "输入 24V，输出 5V，电流 10A，高功率场景。",
        "低压 5V→3.3V 1A": "请给我一个 5V 到 3.3V 的降压芯片，输出 1A。",
        "车规 36V→5V 8A 国产": "36V 输入，输出 5V、8A，车规级，工作温度 -40°C 到 125°C，必须国产，低供应风险。",
        "性价比 12V→5V 1.2A": "12V 转 5V、1.2A 降压，室温使用，要求成本最低。",
    }
    selected_preset = st.selectbox("Quick load", list(presets.keys()))
    st.markdown("---")
    st.caption("eZ-PLM Component Risk Agent v0.2")

# ---------- Main Layout ----------
st.markdown('<p class="main-header">🔬 eZ-PLM Component Risk Agent</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Intelligent DC-DC converter selection with multi-dimensional scoring & evidence traceability — powered by Agent tool-call pipeline</p>', unsafe_allow_html=True)

col1, col2 = st.columns([3, 1])
with col1:
    user_input = st.text_area(
        "📝 Requirement Description",
        value=presets[selected_preset],
        height=100,
        placeholder="Describe your DC-DC converter requirement in natural language...",
        label_visibility="visible",
    )
with col2:
    st.markdown("### 🎯 Tips")
    st.caption(
        "• 指定输入/输出电压与电流\n"
        "• 标注温度范围\n"
        "• 说明车规/工业等级需求\n"
        "• 偏好国产或低供应风险"
    )
    analyze_btn = st.button("🚀 Analyze", type="primary", use_container_width=True)
    clear_btn = st.button("🔄 Clear", use_container_width=True)

if clear_btn:
    st.rerun()

# ---------- Analysis Logic ----------
if analyze_btn and user_input.strip():
    effective_api = api_url_input.strip() or API_URL
    with st.spinner("🔍 Agent pipeline running — parsing requirement, searching parts, scoring, generating evidence, assessing risks..."):
        try:
            resp = requests.post(
                f"{effective_api}/analyze",
                json={"user_input": user_input.strip()},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.ConnectionError:
            st.error("❌ Cannot connect to backend. Start it with: `uvicorn app.main:app --port 8001 --reload`")
            st.stop()
        except requests.Timeout:
            st.error("❌ Backend request timed out (60s).")
            st.stop()
        except Exception as e:
            st.error(f"❌ Backend error: {e}")
            st.stop()

    # ========================================================================
    #  ⛓️ Agent Tool-Call Steps — visual cards + intermediate result panels
    # ========================================================================
    tool_steps = data.get("tool_steps", []) or []
    if tool_steps:
        st.markdown("---")
        st.markdown("### ⛓️ Agent Inference Pipeline")
        st.caption("Each card represents one tool call in the agent pipeline. Expand to inspect intermediate results.")

        # Use columns for a flow-like layout: max 3 per row
        cols_per_row = 3
        for row_start in range(0, len(tool_steps), cols_per_row):
            row_steps = tool_steps[row_start: row_start + cols_per_row]
            cols = st.columns(len(row_steps))
            for col, ts in zip(cols, row_steps):
                with col:
                    status = ts.get("status", "running")
                    icon = ts.get("tool_icon", "🔧")
                    label = ts.get("tool_label", ts.get("tool_name", "Unknown"))
                    duration = ts.get("duration_ms", 0)
                    input_summary = ts.get("input_summary", "")
                    output_summary = ts.get("output_summary", "")
                    err_msg = ts.get("error_message", "")
                    intermediate = ts.get("intermediate_result", None)
                    step_idx = ts.get("step_index", 0)

                    # Card wrapper
                    st.markdown(f'<div class="tool-step-card {status}">', unsafe_allow_html=True)

                    # Header row
                    st.markdown(
                        f'<div class="tool-step-header">'
                        f'<span class="tool-step-icon">{icon}</span>'
                        f'<span class="tool-step-title">#{step_idx} {label}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                    # Status + duration badge
                    status_class = f"status-{status}"
                    status_text = {"success": "✅ 成功", "error": "❌ 失败", "running": "⏳ 运行中"}.get(status, status)
                    st.markdown(
                        f'<span class="tool-step-status {status_class}">{status_text}</span>'
                        f'<span class="tool-step-duration">⏱ {duration:.0f}ms</span>',
                        unsafe_allow_html=True,
                    )

                    # Input summary
                    if input_summary:
                        st.markdown(
                            f'<div class="tool-step-row">'
                            f'<span class="tool-step-label">📥 Input:</span>'
                            f'<span class="tool-step-value">{input_summary}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                    # Output summary
                    if output_summary:
                        st.markdown(
                            f'<div class="tool-step-row">'
                            f'<span class="tool-step-label">📤 Output:</span>'
                            f'<span class="tool-step-value">{output_summary}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                    # Error message
                    if err_msg:
                        st.markdown(f'<div class="tool-step-error">⚠️ {err_msg}</div>', unsafe_allow_html=True)

                    # ---------- Intermediate Result Collapsible Panel ----------
                    if intermediate is not None:
                        with st.expander(f"📋 Intermediate Result — Step #{step_idx}", expanded=False):
                            st.json(intermediate)

                    st.markdown('</div>', unsafe_allow_html=True)  # close card

            # Flow arrows between rows
            if row_start + cols_per_row < len(tool_steps):
                st.markdown('<div class="flow-arrow">⬇️</div>', unsafe_allow_html=True)

        # Pipeline Summary
        success_count = sum(1 for ts in tool_steps if ts.get("status") == "success")
        error_count = sum(1 for ts in tool_steps if ts.get("status") == "error")
        total_duration = sum(ts.get("duration_ms", 0) for ts in tool_steps)
        summary_cols = st.columns(4)
        with summary_cols[0]:
            st.metric("Total Steps", len(tool_steps))
        with summary_cols[1]:
            st.metric("✅ Successful", success_count)
        with summary_cols[2]:
            st.metric("❌ Failed", error_count, delta=f"-{error_count}" if error_count > 0 else "0")
        with summary_cols[3]:
            st.metric("⏱ Total Duration", f"{total_duration:.0f}ms")

    # ========================================================================
    #  📋 Parsed Constraints
    # ========================================================================
    constraints = data.get("constraints", {})
    if constraints:
        st.markdown("---")
        st.markdown("### 📋 Parsed Requirement Constraints")
        with st.expander("Expand to view parsed constraints", expanded=False):
            cs = constraints
            c_col1, c_col2, c_col3 = st.columns(3)
            with c_col1:
                st.metric("Category", cs.get("category") or "N/A")
                st.metric("Topology", cs.get("topology") or "N/A")
                st.metric("Application", cs.get("application") or "N/A")
                st.metric("Grade", cs.get("grade") or "N/A")
            with c_col2:
                st.metric("Input Voltage (nom)", f"{cs.get('input_voltage_nominal_v')}V" if cs.get('input_voltage_nominal_v') else "N/A")
                st.metric("Output Voltage", f"{cs.get('output_voltage_v')}V" if cs.get('output_voltage_v') else "N/A")
                st.metric("Output Current", f"{cs.get('output_current_a')}A" if cs.get('output_current_a') else "N/A")
            with c_col3:
                tmin = cs.get("temperature_min_c")
                tmax = cs.get("temperature_max_c")
                st.metric("Temp Range", f"{tmin} ~ {tmax}°C" if tmin is not None and tmax is not None else "N/A")
                prefs = cs.get("preferences", [])
                st.metric("Preferences", ", ".join(prefs) if prefs else "None")

    # ========================================================================
    #  📊 Score Summary Dashboard
    # ========================================================================
    candidates = data.get("candidates", []) or []
    if candidates:
        st.markdown("---")
        st.markdown("### 📊 Score Summary Dashboard")
        rec_count = sum(1 for c in candidates if c.get("recommendation_level") == "recommended")
        backup_count = sum(1 for c in candidates if c.get("recommendation_level") == "backup")
        not_rec_count = sum(1 for c in candidates if c.get("recommendation_level") == "not_recommended")
        dash_cols = st.columns(4)
        with dash_cols[0]:
            st.metric("Total Candidates", len(candidates))
        with dash_cols[1]:
            st.metric("⭐ Recommended", rec_count)
        with dash_cols[2]:
            st.metric("🟡 Backup", backup_count)
        with dash_cols[3]:
            st.metric("🔴 Not Recommended", not_rec_count)

    # ========================================================================
    #  🏆 Ranking & Score Breakdown
    # ========================================================================
    if candidates:
        st.markdown("---")
        st.markdown("### 🏆 Ranking & Score Breakdown")
        for idx, sp in enumerate(candidates):
            part = sp.get("part", {})
            score = sp.get("score", {})
            rank = sp.get("rank", idx + 1)
            level = sp.get("recommendation_level", "not_recommended")
            level_label_map = {"recommended": "⭐ Recommended", "backup": "🟡 Backup", "not_recommended": "🔴 Not Recommended"}
            level_emoji_map = {"recommended": "⭐", "backup": "🟡", "not_recommended": "🔴"}
            card_class = f"score-card {level}"
            with st.container():
                st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)
                r1_col1, r1_col2, r1_col3 = st.columns([0.5, 5, 2])
                with r1_col1:
                    st.markdown(f"<h2 style='margin:0;color:#667eea;'>#{rank}</h2>", unsafe_allow_html=True)
                with r1_col2:
                    pn = part.get("part_number", "N/A")
                    mfr = part.get("manufacturer", "Unknown")
                    domestic = part.get("is_domestic", False)
                    auto = part.get("automotive_grade", False)
                    lifecycle = part.get("lifecycle_status", "N/A")
                    badges_html = ""
                    badges_html += '<span class="badge badge-domestic">🇨🇳 国产</span>' if domestic else '<span class="badge badge-import">🌍 进口</span>'
                    if auto:
                        badges_html += '<span class="badge badge-auto">🚗 车规</span>'
                    lc_class = "badge-active" if lifecycle == "active" else ("badge-obsolete" if lifecycle == "obsolete" else "badge-discontinued")
                    badges_html += f'<span class="badge {lc_class}">{lifecycle}</span>'
                    st.markdown(f'<p class="part-name">{pn}&nbsp;&nbsp;<span class="part-meta">by {mfr}</span></p>{badges_html}', unsafe_allow_html=True)
                with r1_col3:
                    st.markdown(f"<p style='text-align:right;font-weight:700;font-size:1rem;'>{level_emoji_map.get(level,'')} {level_label_map.get(level, level)}</p>", unsafe_allow_html=True)
                total = score.get("total_score", 0)
                bar_color = "#10b981" if total >= 75 else ("#f59e0b" if total >= 50 else "#ef4444")
                st.markdown(f"""<div style="display:flex;align-items:center;gap:0.5rem;margin:0.3rem 0;"><span style="font-weight:700;font-size:1.1rem;color:{bar_color};">{total:.0f}</span><span style="font-size:0.78rem;color:#6b7280;">/ 100</span><div class="score-bar-bg" style="flex:1;"><div class="score-bar-fill" style="width:{total}%;background:{bar_color};"></div></div></div>""", unsafe_allow_html=True)
                dims = [("Parameter Match", score.get("parameter_match_score", 0), "📐"), ("Supply Risk", score.get("supply_risk_score", 0), "📦"), ("Cost", score.get("cost_score", 0), "💰"), ("Domestic", score.get("domestic_score", 0), "🇨🇳"), ("Evidence", score.get("evidence_score", 0), "📄")]
                dim_cols = st.columns(len(dims))
                for di, (dim_label, dim_val, dim_icon) in enumerate(dims):
                    dc = "#10b981" if dim_val >= 80 else ("#f59e0b" if dim_val >= 50 else "#ef4444")
                    with dim_cols[di]:
                        st.markdown(f'<div class="metric-row"><span class="metric-label">{dim_icon} {dim_label}</span><span class="metric-value" style="color:{dc};">{dim_val:.0f}</span></div>', unsafe_allow_html=True)
                specs_row = f"📐 {part.get('input_voltage_min_v','?')}–{part.get('input_voltage_max_v','?')}V in | ⚡ {part.get('output_current_max_a','?')}A out | 🌡️ {part.get('temperature_min_c','?')}–{part.get('temperature_max_c','?')}°C | 📦 Stock: {part.get('stock','?')} | 💰 ¥{part.get('unit_price_cny','?')}"
                st.caption(specs_row)
                reasons = score.get("reasons", [])
                if reasons:
                    tags_html = " ".join([f'<span class="reason-tag">{r}</span>' for r in reasons])
                    st.markdown(f'<div style="margin-top:0.3rem;">{tags_html}</div>', unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("No candidate parts matched your requirements.")

    # ========================================================================
    #  🔗 Evidence Chain
    # ========================================================================
    evidence = data.get("evidence", []) or []
    if evidence:
        st.markdown("---")
        st.markdown("### 🔗 Evidence Chain")
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
                        conf_color = "#10b981" if conf >= 0.9 else ("#f59e0b" if conf >= 0.7 else "#ef4444")
                        st.markdown(f"""<div class="evidence-block"><span class="evidence-type">{ev.get('evidence_type','N/A')}</span><strong>{ev.get('claim','N/A')}</strong><span style="font-size:0.75rem;color:#6b7280;margin-left:0.5rem;">source: {ev.get('source','N/A')}::{ev.get('source_field','')}</span><span style="float:right;font-weight:600;color:{conf_color};">conf: {conf:.0%}</span></div>""", unsafe_allow_html=True)
        else:
            for ev in evidence:
                conf = ev.get("confidence", 0)
                conf_color = "#10b981" if conf >= 0.9 else ("#f59e0b" if conf >= 0.7 else "#ef4444")
                st.markdown(f"""<div class="evidence-block"><span class="evidence-type">{ev.get('evidence_type','N/A')}</span><strong>{ev.get('claim','N/A')}</strong><span style="font-size:0.75rem;color:#6b7280;margin-left:0.5rem;">source: {ev.get('source','N/A')}::{ev.get('source_field','')}</span><span style="float:right;font-weight:600;color:{conf_color};">conf: {conf:.0%}</span></div>""", unsafe_allow_html=True)
    else:
        if candidates:
            st.markdown("---")
            st.info("No evidence records available.")

    # ========================================================================
    #  ⚠️ Risk Assessment
    # ========================================================================
    risks = data.get("risks")
    if risks:
        st.markdown("---")
        st.markdown("### ⚠️ Risk Assessment")
        overall = risks.get("overall_risk_level", "N/A")
        risk_color_class = "risk-low" if "low" in str(overall).lower() else ("risk-medium" if "medium" in str(overall).lower() else "risk-high")
        st.markdown(f"**Overall Risk:** <span class='{risk_color_class}'>{str(overall).upper()}</span>", unsafe_allow_html=True)
        risk_items = risks.get("risk_items", [])
        for ri in risk_items:
            sev = ri.get("severity", "N/A")
            sev_color = "risk-low" if "low" in str(sev).lower() else ("risk-medium" if "medium" in str(sev).lower() else "risk-high")
            mitigation_text = f" (Mitigation: {ri.get('mitigation')})" if ri.get("mitigation") else ""
            st.markdown(f"- <span class='{sev_color}'>{str(sev).upper()}</span> — {ri.get('description','')}{mitigation_text}", unsafe_allow_html=True)

    # ---------- Footer ----------
    st.markdown("---")
    st.caption(f"Agent v{data.get('ir_version', '0.2')} | Request ID: {data.get('request_id', 'N/A')} | Tool Steps: {len(tool_steps)}")