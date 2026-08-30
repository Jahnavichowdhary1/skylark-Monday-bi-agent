"""
Antigravity BI - Streamlit Executive Intelligence Web App for Skylark Drones.
Enterprise Aerospace Edition featuring:
- Conversational BI Agent with Plotly Generative UI
- What-If Revenue Scenario Simulator
- Spectra SaaS Platform & Drone Survey Payload Analytics
- 1-Click Leadership Briefing Generator with PDF/Markdown Exporter
- Interactive Live Data Cleaning Sandbox
- Monday.com GraphQL v2 Live Connector
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.core.data_normalizer import DataNormalizer, DataQualityReport
from src.core.monday_client import MondayClient, MondayAPIError
from src.core.mock_provider import MockMondayProvider
from src.core.cross_board_engine import CrossBoardEngine
from src.agent.bi_agent import BIAgent, AgentResponse
from src.agent.executive_briefing import ExecutiveBriefingGenerator

# Page Configuration
st.set_page_config(
    page_title="Antigravity BI | Skylark Drones Executive Cockpit",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-End Aerospace & Executive Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-header {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(90deg, #0f172a 0%, #0369a1 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 1.0rem;
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .badge-live {
        background: #dcfce7;
        color: #15803d;
        padding: 4px 10px;
        border-radius: 16px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.3px;
        display: inline-block;
        border: 1px solid #bbf7d0;
    }
    .badge-demo {
        background: #e0e7ff;
        color: #4338ca;
        padding: 4px 10px;
        border-radius: 16px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.3px;
        display: inline-block;
        border: 1px solid #c7d2fe;
    }
    .badge-quality {
        background: #fef3c7;
        color: #b45309;
        padding: 4px 10px;
        border-radius: 16px;
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.3px;
        display: inline-block;
        border: 1px solid #fde68a;
    }
    .briefing-box {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 24px;
        font-size: 0.95rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 16px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_data(source_type: str = "mock", api_key: str = "", deals_id: str = "", wo_id: str = ""):
    """Loads and normalizes data from either live Monday.com or mock provider."""
    deals_cav = []
    wo_cav = []

    if source_type == "live" and api_key and deals_id and wo_id:
        try:
            client = MondayClient(api_key)
            deals_raw = client.fetch_board_items(deals_id)
            wo_raw = client.fetch_board_items(wo_id)
        except Exception as e:
            st.error(f"Live Monday.com fetch failed ({e}). Falling back to local dataset.")
            mock = MockMondayProvider()
            deals_raw = mock.fetch_board_items("1001")
            wo_raw = mock.fetch_board_items("1002")
    else:
        mock = MockMondayProvider()
        deals_raw = mock.fetch_board_items("1001")
        wo_raw = mock.fetch_board_items("1002")

    clean_deals, deals_cav = DataNormalizer.clean_deals(deals_raw)
    clean_wo, wo_cav = DataNormalizer.clean_work_orders(wo_raw)
    quality_report = DataNormalizer.audit_quality(clean_deals, clean_wo, deals_cav, wo_cav)

    return clean_deals, clean_wo, quality_report


# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "monday_source" not in st.session_state:
    st.session_state.monday_source = "mock"
if "monday_api_key" not in st.session_state:
    st.session_state.monday_api_key = ""
if "monday_deals_id" not in st.session_state:
    st.session_state.monday_deals_id = ""
if "monday_wo_id" not in st.session_state:
    st.session_state.monday_wo_id = ""

# Sidebar: Live Monday Connection & Prompt Launcher
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/drone.png", width=64)
    st.title("Skylark BI Cockpit")
    st.markdown("**Executive Multi-Board Intelligence**")

    st.markdown("---")
    st.subheader("🔌 Monday.com Connection")

    conn_mode = st.radio(
        "Data Source Mode",
        ["⚡ Demo Sandbox (Preloaded)", "🟢 Live Monday.com API v2"],
        index=0 if st.session_state.monday_source == "mock" else 1,
    )

    if "Live" in conn_mode:
        st.session_state.monday_source = "live"
        st.session_state.monday_api_key = st.text_input(
            "Monday API Token", value=st.session_state.monday_api_key, type="password"
        )
        st.session_state.monday_deals_id = st.text_input(
            "Deals Board ID", value=st.session_state.monday_deals_id, placeholder="e.g. 1827364521"
        )
        st.session_state.monday_wo_id = st.text_input(
            "Work Orders Board ID", value=st.session_state.monday_wo_id, placeholder="e.g. 1827364522"
        )

        if st.button("🔄 Connect & Sync Live Boards"):
            st.cache_data.clear()
            st.rerun()
    else:
        st.session_state.monday_source = "mock"

    st.markdown("---")
    st.markdown("### 💡 Executive Quick Prompts")
    sample_prompts = [
        "How's our pipeline looking for energy sector this quarter?",
        "What is our Spectra SaaS platform attach rate?",
        "Which work orders are delayed and what revenue is at risk?",
        "Show BD Owner performance and win rates.",
        "Simulate closing our top 3 renewable pipeline deals.",
        "Summarize our revenue, billed value, and outstanding collections.",
        "Prepare a leadership update for weekly founder sync.",
        "Run an autonomous data resilience and quality audit.",
    ]

    for p in sample_prompts:
        if st.button(p, key=f"quick_{p[:18]}"):
            st.session_state.active_prompt = p
            st.rerun()

# Load Data
clean_deals, clean_wo, quality_report = load_data(
    st.session_state.monday_source,
    st.session_state.monday_api_key,
    st.session_state.monday_deals_id,
    st.session_state.monday_wo_id,
)

# Initialize Engine & Agents
engine = CrossBoardEngine(clean_deals, clean_wo)
fin_summary = engine.get_financial_summary()
drone_metrics = engine.get_drone_analytics()
agent = BIAgent(clean_deals, clean_wo, quality_report)
briefing_gen = ExecutiveBriefingGenerator(clean_deals, clean_wo, quality_report)

# Top Bar Header
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("<div class='main-header'>🛸 Skylark Drones — Business Intelligence Agent</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Real-time founder-level answers across Sales Pipeline & Work Order Execution</div>", unsafe_allow_html=True)
with col_h2:
    mode_badge = (
        "<span class='badge-live'>🟢 Live Monday.com Connected</span>"
        if st.session_state.monday_source == "live"
        else "<span class='badge-demo'>⚡ Demo Sandbox Active</span>"
    )
    quality_badge = f"<span class='badge-quality'>🩺 Data Score: {quality_report.quality_score:.1f}/100</span>"
    st.markdown(f"<div style='text-align: right; padding-top: 6px;'>{mode_badge}<br>{quality_badge}</div>", unsafe_allow_html=True)

# Top Executive KPI Cards Row
kpi1, kpi2, kpi3, kpi4, kpi5, kpi6 = st.columns(6)
with kpi1:
    st.metric("Total Open Pipeline", agent.format_currency(fin_summary["total_pipeline_value"]), f"{fin_summary['open_deals_count']} Deals")
with kpi2:
    st.metric("Won Bookings", agent.format_currency(fin_summary["total_won_value"]), f"{fin_summary['win_rate_count_pct']}% Win Rate")
with kpi3:
    st.metric("Contracted Work Orders", agent.format_currency(fin_summary["total_wo_contract_value"]), f"{fin_summary['total_work_orders']} Projects")
with kpi4:
    st.metric("Cash Collected", agent.format_currency(fin_summary["total_collected_value"]), f"{fin_summary['billing_efficiency_pct']}% Invoiced")
with kpi5:
    st.metric("Spectra SaaS Attach", f"{fin_summary['spectra_attach_rate_pct']}%", agent.format_currency(fin_summary['spectra_contract_value']))
with kpi6:
    st.metric("Delayed WOs (At Risk)", str(fin_summary["delayed_work_orders"]), f"TAT: {clean_wo['execution_days'].mean():.1f}d", delta_color="inverse")

st.markdown("---")

# Main Navigation Tabs (Enhanced with What-If & Drone Tech)
tab_chat, tab_whatif, tab_drone_tech, tab_briefing, tab_dashboards, tab_sandbox, tab_config = st.tabs([
    "💬 Executive Chatbot",
    "🔮 What-If Growth Simulator",
    "🛰️ Drone Tech & SaaS Analytics",
    "📋 Leadership Briefings",
    "📊 Cross-Board Dashboards",
    "🩺 Data Resilience Sandbox",
    "🔌 Monday.com Setup",
])

# ================= TAB 1: EXECUTIVE CHATBOT =================
with tab_chat:
    st.markdown("### 💬 Ask Founder-Level Business Intelligence Questions")

    # Render Chat History
    for msg_idx, msg in enumerate(st.session_state.chat_history):
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant"):
                st.markdown(msg["content"])
                if msg.get("kpis"):
                    kcols = st.columns(len(msg["kpis"]))
                    for idx, (k, v) in enumerate(msg["kpis"].items()):
                        with kcols[idx]:
                            st.metric(k, v)
                if msg.get("chart_type") and msg.get("chart_data"):
                    cd = msg["chart_data"]
                    if msg["chart_type"] == "bar":
                        fig = px.bar(x=cd["labels"], y=cd["values"], labels={"x": "Category", "y": "Value"}, color_discrete_sequence=["#0284c7"])
                        fig.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20))
                        st.plotly_chart(fig, width="stretch", key=f"hist_bar_{msg_idx}")
                    elif msg["chart_type"] == "pie":
                        fig = px.pie(names=cd["labels"], values=cd["values"], color_discrete_sequence=px.colors.qualitative.Prism)
                        fig.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20))
                        st.plotly_chart(fig, width="stretch", key=f"hist_pie_{msg_idx}")
                if msg.get("table_data"):
                    st.dataframe(pd.DataFrame(msg["table_data"]), width="stretch")
                if msg.get("caveats"):
                    with st.expander("⚠️ Data Resilience & Quality Caveats", expanded=False):
                        for cav in msg["caveats"]:
                            st.caption(f"• {cav}")

    # Check if a quick prompt was triggered
    prompt_to_send = None
    if "active_prompt" in st.session_state and st.session_state.active_prompt:
        prompt_to_send = st.session_state.active_prompt
        st.session_state.active_prompt = None

    user_input = st.chat_input("Ask a question (e.g. 'How is our pipeline looking for energy sector this quarter?')...")
    if user_input:
        prompt_to_send = user_input

    if prompt_to_send:
        st.session_state.chat_history.append({"role": "user", "content": prompt_to_send})
        with st.chat_message("user"):
            st.markdown(prompt_to_send)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing cross-board intelligence & computing metrics..."):
                response = agent.query(prompt_to_send)
                st.markdown(response.answer)

                if response.kpis:
                    kcols = st.columns(len(response.kpis))
                    for idx, (k, v) in enumerate(response.kpis.items()):
                        with kcols[idx]:
                            st.metric(k, v)

                cur_idx = len(st.session_state.chat_history)
                if response.chart_type and response.chart_data:
                    cd = response.chart_data
                    if response.chart_type == "bar":
                        fig = px.bar(x=cd["labels"], y=cd["values"], labels={"x": "Category", "y": "Value"}, color_discrete_sequence=["#0284c7"])
                        fig.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20))
                        st.plotly_chart(fig, width="stretch", key=f"live_bar_{cur_idx}")
                    elif response.chart_type == "pie":
                        fig = px.pie(names=cd["labels"], values=cd["values"], color_discrete_sequence=px.colors.qualitative.Prism)
                        fig.update_layout(height=320, margin=dict(l=20, r=20, t=30, b=20))
                        st.plotly_chart(fig, width="stretch", key=f"live_pie_{cur_idx}")

                if response.table_data:
                    st.dataframe(pd.DataFrame(response.table_data), width="stretch")

                if response.caveats:
                    with st.expander("⚠️ Data Resilience & Quality Caveats", expanded=True):
                        for cav in response.caveats:
                            st.caption(f"• {cav}")

                if response.suggested_followups:
                    st.markdown("**Suggested Follow-ups:**")
                    fcols = st.columns(len(response.suggested_followups))
                    for fidx, fup in enumerate(response.suggested_followups):
                        with fcols[fidx]:
                            if st.button(fup, key=f"fup_{cur_idx}_{fidx}"):
                                st.session_state.active_prompt = fup
                                st.rerun()

        st.session_state.chat_history.append({
            "role": "assistant",
            "content": response.answer,
            "kpis": response.kpis,
            "chart_type": response.chart_type,
            "chart_data": response.chart_data,
            "table_data": response.table_data,
            "caveats": response.caveats,
        })

# ================= TAB 2: WHAT-IF SCENARIO SIMULATOR =================
with tab_whatif:
    st.markdown("### 🔮 Executive Growth & What-If Revenue Simulator")
    st.markdown("Interactive scenario modeling for Founders & Board members to project cash flow and revenue uplift under key growth initiatives.")

    sim_col1, sim_col2, sim_col3 = st.columns(3)
    with sim_col1:
        conv_slider = st.slider("📈 Proposal-to-Won Conversion Uplift (%)", min_value=0, max_value=30, value=15, step=5, key="slider_conv")
    with sim_col2:
        invoicing_slider = st.slider("⚡ Unbilled Backlog Invoiced (%)", min_value=10, max_value=100, value=50, step=10, key="slider_inv")
    with sim_col3:
        spectra_slider = st.slider("🚀 Spectra SaaS Attach Expansion (%)", min_value=0, max_value=50, value=20, step=5, key="slider_spec")

    sim_res = engine.simulate_what_if(
        conversion_boost_pct=float(conv_slider),
        unbilled_invoiced_pct=float(invoicing_slider),
        spectra_upsell_pct=float(spectra_slider),
    )

    st.markdown("---")
    res1, res2, res3, res4 = st.columns(4)
    with res1:
        st.metric("Projected Won Bookings", agent.format_currency(sim_res["simulated_won_total"]), f"+{agent.format_currency(sim_res['additional_won_revenue'])}")
    with res2:
        st.metric("Unlocked Invoiced Cash", f"+{agent.format_currency(sim_res['unlocked_invoiced_cash'])}", f"From {invoicing_slider}% Backlog")
    with res3:
        st.metric("Projected Cash Collected", agent.format_currency(sim_res["simulated_cash_collected"]), f"vs Current {agent.format_currency(fin_summary['total_collected_value'])}")
    with res4:
        st.metric("Projected Spectra Software Value", agent.format_currency(sim_res["simulated_spectra_revenue"]), f"+{spectra_slider}% Expansion")

    col_w1, col_w2 = st.columns(2)
    with col_w1:
        fig_sim = go.Figure(data=[
            go.Bar(name="Current Baseline", x=["Won Bookings", "Billed Revenue", "Cash Inflows"], y=[fin_summary["total_won_value"], fin_summary["total_billed_value"], fin_summary["total_collected_value"]], marker_color="#94a3b8"),
            go.Bar(name="Simulated Uplift", x=["Won Bookings", "Billed Revenue", "Cash Inflows"], y=[sim_res["simulated_won_total"], sim_res["simulated_billed_total"], sim_res["simulated_cash_collected"]], marker_color="#0284c7"),
        ])
        fig_sim.update_layout(barmode="group", height=340, title="Current vs Simulated Growth", margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_sim, width="stretch", key="whatif_growth_comparison_chart")

    with col_w2:
        st.markdown(f"""
        #### 💡 Strategic Impact Analysis:
        - **Pipeline Acceleration:** Converting an additional **{conv_slider}%** of open proposals injects **+{agent.format_currency(sim_res['additional_won_revenue'])}** directly into top-line bookings.
        - **Working Capital Optimization:** Invoicing **{invoicing_slider}%** of the current unbilled execution backlog unlocks **+{agent.format_currency(sim_res['unlocked_invoiced_cash'])}** in billing milestone releases.
        - **SaaS Multiple Uplift:** Expanding Spectra platform attach by **{spectra_slider}%** boosts software recurring revenue to **{agent.format_currency(sim_res['simulated_spectra_revenue'])}**, significantly increasing company valuation multiples.
        """)

# ================= TAB 3: DRONE TECH & SAAS ANALYTICS =================
with tab_drone_tech:
    st.markdown("### 🛰️ Drone Tech Payloads, Survey Types & Spectra Platform Analytics")
    st.markdown("Domain-specific intelligence tailored to Skylark Drones' core surveying capabilities and SaaS platform expansion.")

    dcol1, dcol2 = st.columns(2)
    with dcol1:
        st.subheader("🛸 Spectra SaaS Platform Attach Rate")
        p_counts = drone_metrics["platform_counts"]
        fig_plat = px.pie(names=list(p_counts.keys()), values=list(p_counts.values()), color_discrete_sequence=px.colors.qualitative.Prism, hole=0.4)
        fig_plat.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_plat, width="stretch", key="drone_spectra_attach_pie")

    with dcol2:
        st.subheader("🛰️ Drone Survey Payloads & Work Types")
        wt_counts = drone_metrics["work_type_counts"]
        fig_wt = px.bar(x=list(wt_counts.keys())[:6], y=list(wt_counts.values())[:6], labels={"x": "Work Type", "y": "Project Count"}, color_discrete_sequence=["#0284c7"])
        fig_wt.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_wt, width="stretch", key="drone_payload_types_bar")

    st.markdown("---")
    st.subheader("🏆 BD / Account Executive Performance Leaderboard")
    owner_df = pd.DataFrame(drone_metrics["owner_matrix"])
    owner_df["won_value_fmt"] = owner_df["won_value"].apply(agent.format_currency)
    owner_df["pipeline_fmt"] = owner_df["pipeline_value"].apply(agent.format_currency)
    owner_df["unbilled_fmt"] = owner_df["wo_unbilled"].apply(agent.format_currency)
    st.dataframe(owner_df[["owner_code", "won_value_fmt", "pipeline_fmt", "total_deals", "won_deals", "win_rate_pct", "total_wos", "delayed_wos", "unbilled_fmt"]], width="stretch")

# ================= TAB 4: LEADERSHIP BRIEFINGS =================
with tab_briefing:
    st.markdown("### 📋 Executive Leadership Update Generator")
    st.markdown("Generate 1-click strategic digests synthesizing Sales Pipeline velocity and Operational delivery health for Founder & Board syncs.")

    col_scope, col_btn = st.columns([3, 1])
    with col_scope:
        period = st.selectbox(
            "Select Reporting Horizon",
            ["Weekly Founder Sync", "Monthly Executive Review", "Q3 Quarterly Business Review", "Full Fiscal Year YTD"],
            key="briefing_horizon_select"
        )
    with col_btn:
        st.markdown("<div style='padding-top: 28px;'></div>", unsafe_allow_html=True)
        generate_btn = st.button("⚡ Generate Briefing", type="primary", key="btn_gen_briefing")

    briefing = briefing_gen.generate_briefing(period)

    st.markdown("---")
    st.markdown(briefing["markdown"])

    st.download_button(
        label="📥 Download Briefing Report (.md)",
        data=briefing["markdown"],
        file_name=f"skylark_leadership_briefing_{period.lower().replace(' ', '_')}.md",
        mime="text/markdown",
        key="btn_download_briefing"
    )

# ================= TAB 5: CROSS-BOARD DASHBOARDS =================
with tab_dashboards:
    st.markdown("### 📊 Cross-Board Strategic BI Dashboards")

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.subheader("🏢 Pipeline & Won Value by Vertical")
        sec_df = engine.get_sector_breakdown().head(7)
        fig_sec = go.Figure(data=[
            go.Bar(name="Pipeline Value", x=sec_df["sector"], y=sec_df["pipeline_value"], marker_color="#38bdf8"),
            go.Bar(name="Won Bookings", x=sec_df["sector"], y=sec_df["won_value"], marker_color="#0284c7"),
        ])
        fig_sec.update_layout(barmode="group", height=340, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_sec, width="stretch", key="dash_sector_pipeline_won_bar")

    with col_d2:
        st.subheader("⚡ Work Orders Execution Status")
        status_counts = clean_wo["execution_status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig_wo = px.pie(status_counts, names="Status", values="Count", color_discrete_sequence=px.colors.qualitative.Safe)
        fig_wo.update_layout(height=340, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_wo, width="stretch", key="dash_wo_status_pie_chart")

    col_d3, col_d4 = st.columns(2)
    with col_d3:
        st.subheader("💰 Financial Leakage & Invoicing Gap")
        fin_bar = go.Figure(data=[
            go.Bar(
                x=["Contracted Value", "Billed Value", "Cash Collected", "Unbilled Backlog", "Receivables"],
                y=[
                    fin_summary["total_wo_contract_value"],
                    fin_summary["total_billed_value"],
                    fin_summary["total_collected_value"],
                    fin_summary["total_unbilled_value"],
                    fin_summary["total_receivables"],
                ],
                marker_color=["#0284c7", "#3b82f6", "#10b981", "#f59e0b", "#ef4444"],
            )
        ])
        fin_bar.update_layout(height=340, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fin_bar, width="stretch", key="dash_financial_leakage_flow_bar")

    with col_d4:
        st.subheader("⏱️ Delivery Turnaround Time (TAT) by Sector")
        tat_df = clean_wo[clean_wo["execution_days"] > 0].groupby("sector")["execution_days"].mean().reset_index()
        fig_tat = px.bar(tat_df, x="sector", y="execution_days", labels={"execution_days": "Avg Days", "sector": "Sector"}, color_discrete_sequence=["#6366f1"])
        fig_tat.update_layout(height=340, margin=dict(l=20, r=20, t=30, b=20))
        st.plotly_chart(fig_tat, width="stretch", key="dash_sector_tat_duration_bar")

# ================= TAB 6: INTERACTIVE DATA RESILIENCE SANDBOX =================
with tab_sandbox:
    st.markdown("### 🩺 Autonomous Data Resilience & Interactive Sandbox")
    st.markdown("Test the agent's real-time parser against dirty real-world spreadsheet anomalies.")

    sand1, sand2 = st.columns(2)
    with sand1:
        st.subheader("🧪 Live Interactive Normalizer Tester")
        sample_input = st.text_input("Enter any dirty string to test:", value="₹ 2,64,398.08 (Excl GST)", key="input_sandbox_num")
        parsed_num = DataNormalizer.parse_numeric(sample_input)
        st.info(f"**Parsed Numeric Output:** `{parsed_num}` (Formatted: `{agent.format_currency(parsed_num)}`)")

        sample_date = st.text_input("Enter mixed format date:", value="26/12/2025", key="input_sandbox_date")
        parsed_dt = DataNormalizer.parse_date(sample_date)
        st.info(f"**Parsed Timestamp Output:** `{parsed_dt}`")

        sample_sec = st.text_input("Enter sector synonym:", value="Green Energy / Solar Farm", key="input_sandbox_sec")
        parsed_sec = DataNormalizer.normalize_sector(sample_sec)
        st.info(f"**Canonical Sector Output:** `{parsed_sec}`")

    with sand2:
        st.subheader("🛡️ Data Health Audit Metrics")
        rep = quality_report.to_dict()
        st.metric("Overall Quality Score", f"{rep['quality_score']}/100")
        st.write(f"- **Clean Deals Ingested:** {rep['clean_deals']}/{rep['total_deals']}")
        st.write(f"- **Clean Work Orders:** {rep['clean_work_orders']}/{rep['total_work_orders']}")
        st.write(f"- **Deals Missing Value:** {rep['deals_missing_value_pct']}%")
        st.write(f"- **Unlinked Work Orders:** {rep['wo_unlinked_pct']}%")

        st.subheader("⚠️ Active Data Quality Caveats")
        for cav in rep["caveats"]:
            st.warning(cav)

# ================= TAB 7: MONDAY.COM CONFIGURATION GUIDE =================
with tab_config:
    st.markdown("### 🔌 Monday.com Board Configuration & Setup Guide")
    st.markdown("""
To connect your live [Monday.com](https://monday.com) boards to this AI Agent:

#### 1. Obtain your Monday.com API Token
- Log into your Monday.com workspace ➔ Click profile avatar ➔ **Developers** ➔ **Developer API Token**.

#### 2. Configure Boards on Monday.com
- **Deals Board (Sales Funnel)**: Import `data/deals_raw.xlsx`.
- **Work Orders Board (Execution Tracker)**: Import `data/work_orders_raw.xlsx`.

#### 3. Connect via Sidebar
- Enter your API Token and both Board IDs in the sidebar.
- Click **'Connect & Sync Live Boards'**.
""")
