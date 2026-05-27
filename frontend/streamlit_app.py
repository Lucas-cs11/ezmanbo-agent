import streamlit as st
import requests
import pandas as pd

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
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #6b7280;
        font-size: 0.95rem;
        margin-bottom: 1.5rem;
    }
    .score-card {
        background: linear-gradient(135deg, #f0f4ff 0%, #faf5ff 100%);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin: 0.6rem 0;
        border-left: 4px solid #667eea;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
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
    .reason-tag {
        display: inline-block;
        background: #f3f4f6;
        border-radius: 6px;
        padding: 0.2rem 0.5rem;
        margin: 0.15rem 0.25rem 0.15rem 0;
        font-size: 0.78rem;
        color: #374151;
    }
    .summary-box {
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin: 1rem 0;
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
    st.caption("eZ-PLM Component Risk Agent v0.1")

# ---------- Main Layout ----------
st.markdown('<p class="main-header">🔬 eZ-PLM Component Risk Agent</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Intelligent DC-DC converter selection with multi-dimensional scoring & evidence traceability</p>', unsafe_allow_html=True)

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
    st.caption("• 指定输入/输出电压与电流\n• 标注温度范围\n• 说明车规/工业等级需求\n• 偏好国产或低供应风险")
    analyze_btn = st.button("🚀 Analyze", type="primary", use_container_width=True)
    clear_btn = st.button("🔄 Clear", use_container_width=True)

if clear_btn:
    st.rerun()

# ---------- Analysis Logic ----------
if analyze_btn and user_input.strip():
    effective_api = api_url_input.strip() or API_URL
    with st.spinner("🔍 Analyzing your requirement with agent pipeline..."):
        try:
            resp = requests.post(f"{effective_api}/analyze", json={"user_input": user_input.strip()}, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.ConnectionError:
            st.error("❌ Cannot connect to backend. Make sure `uvicorn app.main:app --port 8001` is running.")
            st.stop()
        except Exception as e:
            st.error(f"❌ Backend error: {e}")
            st.stop()

    # ---------- Parsed Constraints ----------
    constraints = data.get("constraints", {})
    st.markdown("### 📋 Parsed Requirement Constraints")
    with st.expander("Expand to view parsed constraints", expanded=False):
        if constraints:
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
                st.metric("Temp Range", f"{cs.get('temperature_min_c')} ~ {cs.get('temperature_max_c')}°C" if cs.get('temperature_min_c') is not None else "N/A")
                prefs = cs.get("preferences", [])
                st.metric("Preferences", ", ".join(prefs) if prefs else "None")

    # ---------- Score Summary Dashboard ----------
    recommended = data.get("recommended_parts", []) or []
    candidates = data.get("candidates", []) or []
    st.markdown("### 📊 Score Summary Dashboard")
    if candidates:
        dash_cols = st.columns(4)
        rec_list = [c for c in candidates if c.get("recommendation_level") == "recommended"]
        backup_list = [c for c in candidates if c.get("recommendation_level") == "backup"]
        not_rec_list = [c for c in candidates if c.get("recommendation_level") == "not_recommended"]
        with dash_cols[0]:
            st.metric("Total Candidates", len(candidates))
        with dash_cols[1]:
            st.metric("⭐ Recommended", len(rec_list), delta=f"{len(rec_list)} parts")
        with dash_cols[2]:
            st.metric("🟡 Backup", len(backup_list), delta=f"{len(backup_list)} parts")
        with dash_cols[3]:
            st.metric("🔴 Not Recommended", len(not_rec_list))
    else:
        st.info("No candidate parts found matching your requirements.")

    # ---------- Recommended Parts ----------
    st.markdown("---")
    st.markdown("### 🏆 Ranking & Score Breakdown")

    if not candidates:
        st.warning("No scored parts available.")
    else:
        for idx, sp in enumerate(candidates):
            part = sp.get("part", {})
            score = sp.get("score", {})
            rank = sp.get("rank", idx + 1)
            level = sp.get("recommendation_level", "not_recommended")
            level_label = {"recommended": "⭐ Recommended", "backup": "🟡 Backup", "not_recommended": "🔴 Not Recommended"}
            level_emoji = {"recommended": "⭐", "backup": "🟡", "not_recommended": "🔴"}

            card_class = f"score-card {level}"
            with st.container():
                st.markdown(f'<div class="{card_class}">', unsafe_allow_html=True)

                # Row 1: rank + part info + recommendation level
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
                    lc_class = "badge-active" if lifecycle == "active" else ("badge-obsolete" if lifecycle in ("obsolete",) else "badge-discontinued")
                    badges_html += f'<span class="badge {lc_class}">{lifecycle}</span>'
                    st.markdown(f'<p class="part-name">{pn}&nbsp;&nbsp;<span class="part-meta">by {mfr}</span></p>{badges_html}', unsafe_allow_html=True)
                with r1_col3:
                    st.markdown(f"<p style='text-align:right;font-weight:700;font-size:1rem;'>{level_emoji.get(level,'')} {level_label.get(level, level)}</p>", unsafe_allow_html=True)

                # Row 2: total score bar
                total = score.get("total_score", 0)
                bar_color = "#10b981" if total >= 75 else ("#f59e0b" if total >= 50 else "#ef4444")
                st.markdown(f"""
                <div style="display:flex;align-items:center;gap:0.5rem;margin:0.3rem 0;">
                    <span style="font-weight:700;font-size:1.1rem;color:{bar_color};">{total:.0f}</span>
                    <span style="font-size:0.78rem;color:#6b7280;">/ 100</span>
                    <div class="score-bar-bg" style="flex:1;">
                        <div class="score-bar-fill" style="width:{total}%;background:{bar_color};"></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Row 3: dimension sub-scores
                dims = [
                    ("Parameter Match", score.get("parameter_match_score", 0), "📐"),
                    ("Supply Risk", score.get("supply_risk_score", 0), "📦"),
                    ("Cost", score.get("cost_score", 0), "💰"),
                    ("Domestic", score.get("domestic_score", 0), "🇨🇳"),
                    ("Evidence", score.get("evidence_score", 0), "📄"),
                ]
                dim_cols = st.columns(len(dims))
                for di, (label, val, icon) in enumerate(dims):
                    dc = "#10b981" if val >= 80 else ("#f59e0b" if val >= 50 else "#ef4444")
                    with dim_cols[di]:
                        st.markdown(f'<div class="metric-row"><span class="metric-label">{icon} {label}</span><span class="metric-value" style="color:{dc};">{val:.0f}</span></div>', unsafe_allow_html=True)

                # Row 4: part quick specs
                specs_row = f"📐 {part.get('input_voltage_min_v','?')}–{part.get('input_voltage_max_v','?')}V in | ⚡ {part.get('output_current_max_a','?')}A out | 🌡️ {part.get('temperature_min_c','?')}–{part.get('temperature_max_c','?')}°C | 📦 Stock: {part.get('stock','?')} | 💰 ¥{part.get('unit_price_cny','?')}"
                st.caption(specs_row)

                # Row 5: reasons as tags
                reasons = score.get("reasons", [])
                if reasons:
                    tags_html = " ".join([f'<span class="reason-tag">{r}</span>' for r in reasons])
                    st.markdown(f'<div style="margin-top:0.3rem;">{tags_html}</div>', unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

    # ---------- Evidence Chain ----------
    evidence = data.get("evidence", []) or []
    st.markdown("---")
    st.markdown("### 🔗 Evidence Chain")
    if not evidence:
        st.info("No evidence records available.")
    else:
        # Group evidence by part
        from collections import defaultdict
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
                        st.markdown(f"""
                        <div class="evidence-block">
                            <span class="evidence-type">{ev.get('evidence_type','N/A')}</span>
                            <strong>{ev.get('claim','N/A')}</strong>
                            <span style="font-size:0.75rem;color:#6b7280;margin-left:0.5rem;">source: {ev.get('source','N/A')}::{ev.get('source_field','')}</span>
                            <span style="float:right;font-weight:600;color:{conf_color};">conf: {conf:.0%}</span>
                        </div>
                        """, unsafe_allow_html=True)
        else:
            # single part – no tabs
            for ev in evidence:
                conf = ev.get("confidence", 0)
                conf_color = "#10b981" if conf >= 0.9 else ("#f59e0b" if conf >= 0.7 else "#ef4444")
                st.markdown(f"""
                <div class="evidence-block">
                    <span class="evidence-type">{ev.get('evidence_type','N/A')}</span>
                    <strong>{ev.get('claim','N/A')}</strong>
                    <span style="font-size:0.75rem;color:#6b7280;margin-left:0.5rem;">source: {ev.get('source','N/A')}::{ev.get('source_field','')}</span>
                    <span style="float:right;font-weight:600;color:{conf_color};">conf: {conf:.0%}</span>
                </div>
                """, unsafe_allow_html=True)

    # ---------- Risk Summary ----------
    risks = data.get("risks")
    if risks:
        st.markdown("---")
        st.markdown("### ⚠️ Risk Assessment")
        overall = risks.get("overall_risk_level", "N/A")
        risk_color_class = "risk-low" if "low" in str(overall).lower() else ("risk-medium" if "medium" in str(overall).lower() else "risk-high")
        st.markdown(f"**Overall Risk:** <span class='{risk_color_class}'>{overall.upper()}</span>", unsafe_allow_html=True)
        risk_items = risks.get("risk_items", [])
        for ri in risk_items:
            sev = ri.get("severity", "N/A")
            sev_color = "risk-low" if "low" in str(sev).lower() else ("risk-medium" if "medium" in str(sev).lower() else "risk-high")
            st.markdown(f"- <span class='{sev_color}'>{sev.upper()}</span> — {ri.get('description','')}" + (f" (Mitigation: {ri.get('mitigation')})" if ri.get('mitigation') else ""), unsafe_allow_html=True)

    # ---------- Footer ----------
    st.markdown("---")
    st.caption(f"IR version: {data.get('ir_version', '0.1')} | Request ID: {data.get('request_id', 'N/A')}")