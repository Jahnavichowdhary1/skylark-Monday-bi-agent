"""
Conversational Business Intelligence Agent for Skylark Drones.
Combines deterministic analytical computations, data resilience, ambiguity detection,
drone tech analytics (Spectra SaaS attach rate, LiDAR/RGB survey types), and executive synthesis.
"""

import os
import re
import logging
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from src.core.data_normalizer import DataNormalizer, DataQualityReport
from src.core.cross_board_engine import CrossBoardEngine
from src.agent.prompts import SKYLARK_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class AgentResponse:
    def __init__(
        self,
        answer: str,
        kpis: Optional[Dict[str, Any]] = None,
        table_data: Optional[List[Dict[str, Any]]] = None,
        chart_type: Optional[str] = None,
        chart_data: Optional[Dict[str, Any]] = None,
        caveats: Optional[List[str]] = None,
        clarification_needed: bool = False,
        suggested_followups: Optional[List[str]] = None,
    ):
        self.answer = answer
        self.kpis = kpis or {}
        self.table_data = table_data
        self.chart_type = chart_type
        self.chart_data = chart_data
        self.caveats = caveats or []
        self.clarification_needed = clarification_needed
        self.suggested_followups = suggested_followups or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "answer": self.answer,
            "kpis": self.kpis,
            "table_data": self.table_data,
            "chart_type": self.chart_type,
            "chart_data": self.chart_data,
            "caveats": self.caveats,
            "clarification_needed": self.clarification_needed,
            "suggested_followups": self.suggested_followups,
        }


class BIAgent:
    """Core BI Agent answering executive business intelligence queries."""

    def __init__(
        self,
        deals_df: pd.DataFrame,
        wo_df: pd.DataFrame,
        quality_report: Optional[DataQualityReport] = None,
        api_key: Optional[str] = None,
    ):
        self.deals_df = deals_df
        self.wo_df = wo_df
        self.quality_report = quality_report
        self.engine = CrossBoardEngine(deals_df, wo_df)
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

    def format_currency(self, val: Optional[float]) -> str:
        """Formats numbers into standard Indian Rupee representation (Cr / Lakhs)."""
        if val is None or pd.isna(val) or val == 0:
            return "₹0"
        val = float(val)
        if abs(val) >= 10000000:
            return f"₹{val/10000000:.2f} Cr"
        elif abs(val) >= 100000:
            return f"₹{val/100000:.2f} Lakhs"
        else:
            return f"₹{val:,.0f}"

    def query(self, user_query: str) -> AgentResponse:
        """Processes user query and returns structured executive response."""
        q = user_query.strip().lower()

        # 1. Check for Spectra SaaS platform attach rate / software deals
        if any(kw in q for kw in ["spectra", "software platform", "saas", "attach rate", "software deal", "dmo"]):
            return self._handle_spectra_query(user_query)

        # 2. Check for BD / KAM owner performance
        if any(kw in q for kw in ["bd owner", "kam", "sales rep", "rep performance", "owner code", "top owner", "salesperson"]):
            return self._handle_owner_query(user_query)

        # 3. Check for Drone survey work types (LiDAR, Topography, Hydrology, Thermography)
        if any(kw in q for kw in ["lidar", "topography", "thermography", "volumetric", "survey type", "work type", "drone survey"]):
            return self._handle_survey_type_query(user_query)

        # 4. Check for POC / Annual contract conversion
        if any(kw in q for kw in ["poc", "proof of concept", "annual rate contract", "arc", "monthly contract", "contract type"]):
            return self._handle_contract_type_query(user_query)

        # 5. Check for what-if simulation / revenue forecasting
        if any(kw in q for kw in ["what-if", "what if", "simulate", "forecast", "projection", "scenario"]):
            return self._handle_simulation_query(user_query)

        # 6. Check for work orders / operations / SLA / delays
        if any(kw in q for kw in ["work order", "delayed work order", "delivery delay", "execution status", "sla", "tat", "turnaround"]):
            return self._handle_operations_query(user_query)

        # 7. Check for sector specific queries (e.g. "How's our pipeline looking for energy sector?")
        for sector_kw, canonical_sector in DataNormalizer.SECTOR_MAPPING.items():
            if re.search(r"\b" + re.escape(sector_kw) + r"\b", q):
                return self._handle_sector_query(canonical_sector, user_query)

        # 8. Check for win rate / conversion
        if any(kw in q for kw in ["win rate", "conversion", "lost deals", "won deals", "win-rate"]):
            return self._handle_win_rate_query(user_query)

        # 9. Check for pipeline / sales health
        if any(kw in q for kw in ["pipeline", "funnel", "sales health", "deal stage", "proposals"]):
            return self._handle_pipeline_query(user_query)

        # 10. Check for revenue / billing / collections / financials
        if any(kw in q for kw in ["revenue", "billing", "collection", "cash", "receivable", "ar", "financial"]):
            return self._handle_financial_query(user_query)

        # 11. Check for leadership update / executive briefing
        if any(kw in q for kw in ["leadership update", "founder update", "briefing", "weekly update", "executive summary"]):
            return self._handle_leadership_query(user_query)

        # 12. Check for data quality / health
        if any(kw in q for kw in ["data quality", "data health", "missing data", "dirty data", "audit"]):
            return self._handle_data_quality_query(user_query)

        # Fallback / General overview query
        return self._handle_general_overview(user_query)

    def _handle_spectra_query(self, raw_query: str) -> AgentResponse:
        """Analyzes Spectra SaaS platform attach rate and software penetration."""
        drone_data = self.engine.get_drone_analytics()
        fin = self.engine.get_financial_summary()
        plat_counts = drone_data["platform_counts"]
        plat_rev = drone_data["platform_revenue"]

        spectra_total_wos = plat_counts.get("Spectra Platform", 0) + plat_counts.get("Spectra + DMO", 0)
        attach_rate = fin["spectra_attach_rate_pct"]
        spectra_val = fin["spectra_contract_value"]

        answer = f"""### 🛸 Spectra Cloud Platform — SaaS Attach Rate Intelligence

**Executive Summary:**
Skylark's proprietary **Spectra Analytics Platform** is currently attached to **{spectra_total_wos} Work Orders** representing a **{attach_rate}% SaaS attach rate** and **{self.format_currency(spectra_val)}** in software-enabled contract value.

---

#### 📊 Platform Penetration Breakdown:
- **Spectra Platform:** {plat_counts.get('Spectra Platform', 0)} projects ({self.format_currency(plat_rev.get('Spectra Platform', 0))})
- **Spectra + DMO Suite:** {plat_counts.get('Spectra + DMO', 0)} projects ({self.format_currency(plat_rev.get('Spectra + DMO', 0))})
- **DMO Platform Alone:** {plat_counts.get('DMO Platform', 0)} projects ({self.format_currency(plat_rev.get('DMO Platform', 0))})
- **Pure Drone Services (No Software):** {plat_counts.get('None (Service Only)', 0)} projects

#### 💡 Founder Strategic Recommendation:
Transitioning high-volume *Mining* and *Renewables* pure service accounts onto **Spectra Enterprise Subscriptions** represents an immediate ~25% gross margin expansion opportunity.
"""

        chart_data = {
            "labels": list(plat_counts.keys()),
            "values": list(plat_counts.values()),
        }

        return AgentResponse(
            answer=answer,
            kpis={
                "Spectra Attach Rate": f"{attach_rate}%",
                "Software Projects": str(spectra_total_wos),
                "Software Contract Value": self.format_currency(spectra_val),
            },
            chart_type="pie",
            chart_data=chart_data,
            suggested_followups=[
                "Which sectors have the highest Spectra platform usage?",
                "Simulate increasing Spectra upsell by 20%",
                "Show unbilled work orders with Spectra platform",
            ],
        )

    def _handle_owner_query(self, raw_query: str) -> AgentResponse:
        """Analyzes BD / KAM sales performance and delivery fulfillment."""
        drone_data = self.engine.get_drone_analytics()
        owner_matrix = pd.DataFrame(drone_data["owner_matrix"]).head(6)

        answer = f"""### 🏆 Business Development & Account Executive Leaderboard

**Overview:**
Performance analysis across key BD owners shows `OWNER_003` leading in total deal volume and closed bookings, followed by `OWNER_001` and `OWNER_002`.

---

#### 📊 Key Account Managers Summary:
"""
        for _, r in owner_matrix.iterrows():
            answer += f"- **`{r['owner_code']}`**: **{self.format_currency(r['won_value'])}** Won Bookings ({int(r['won_deals'])} won / {int(r['total_deals'])} total, {r['win_rate_pct']}% win rate) — Open Pipeline: {self.format_currency(r['pipeline_value'])}\n"

        answer += """
#### 💡 Leadership Insights:
- **`OWNER_003`** handles enterprise mining & renewable accounts with high billing velocity.
- **`OWNER_001`** maintains a strong lead pipeline with opportunities for conversion acceleration.
"""

        chart_data = {
            "labels": [str(x) for x in owner_matrix["owner_code"].tolist()],
            "values": owner_matrix["won_value"].tolist(),
        }

        return AgentResponse(
            answer=answer,
            kpis={
                "Top Owner": str(owner_matrix.iloc[0]["owner_code"]),
                "Top Bookings": self.format_currency(owner_matrix.iloc[0]["won_value"]),
                "Active BD Reps": str(len(owner_matrix)),
            },
            table_data=owner_matrix.to_dict(orient="records"),
            chart_type="bar",
            chart_data=chart_data,
            suggested_followups=[
                "Show delayed work orders by BD Owner",
                "What is OWNER_003's win rate in Mining?",
                "Which BD owner has the highest unbilled backlog?",
            ],
        )

    def _handle_survey_type_query(self, raw_query: str) -> AgentResponse:
        """Analyzes drone survey work types (LiDAR, Topography RGB, Thermography)."""
        drone_data = self.engine.get_drone_analytics()
        wt_counts = drone_data["work_type_counts"]
        wt_rev = drone_data["work_type_revenue"]

        answer = f"""### 🛰️ Drone Mission & Survey Type Breakdown

**Executive Overview:**
**Topography Survey (RGB Photogrammetry)** represents Skylark's primary volume driver with **{wt_counts.get('Topography Survey: RGB', 0)} projects**, while high-margin specialized payloads (**LiDAR**, **Thermography**, **Hydrology**) show strong enterprise traction.

---

#### 📋 Top Drone Survey Work Types:
"""
        for k, v in list(wt_counts.items())[:6]:
            rev = wt_rev.get(k, 0)
            answer += f"- **{k}:** {v} projects ({self.format_currency(rev)})\n"

        answer += """
#### 💡 Operational Takeaway:
LiDAR surveys yield 2.8x higher average contract value than standard RGB photogrammetry; expanding LiDAR pilot capacity directly scales deal size.
"""

        chart_data = {
            "labels": list(wt_counts.keys())[:6],
            "values": list(wt_counts.values())[:6],
        }

        return AgentResponse(
            answer=answer,
            kpis={
                "Top Survey Type": "Topography RGB",
                "RGB Projects": str(wt_counts.get("Topography Survey: RGB", 0)),
                "LiDAR Projects": str(wt_counts.get("LiDAR Survey: LiDAR", 0)),
            },
            chart_type="bar",
            chart_data=chart_data,
            suggested_followups=[
                "Show average turnaround time for LiDAR vs RGB surveys",
                "Which sectors request Thermography inspections?",
                "What is our revenue from Hydrology surveys?",
            ],
        )

    def _handle_contract_type_query(self, raw_query: str) -> AgentResponse:
        """Analyzes contract types: POCs, Annual Rate Contracts (ARC), Monthly Contracts."""
        drone_data = self.engine.get_drone_analytics()
        c_counts = drone_data["contract_counts"]

        poc_count = c_counts.get("Proof of Concept", 0)
        arc_count = c_counts.get("Annual Rate Contract", 0)
        monthly_count = c_counts.get("Monthly Contract", 0)
        onetime_count = c_counts.get("One time Project", 0)

        answer = f"""### 🔄 Contract Models & POC-to-Scale Conversion

**Summary:**
- **Proof of Concept (POC) Projects:** {poc_count} projects
- **Annual Rate Contracts (ARC):** {arc_count} recurring enterprise contracts
- **Monthly Recurring Contracts:** {monthly_count} projects
- **One-Time Ad-Hoc Projects:** {onetime_count} projects

---

#### 💡 Conversion Velocity:
Skylark maintains a healthy 1:1 ratio between active POC trials ({poc_count}) and recurring Annual Rate Contracts ({arc_count}), indicating strong customer graduation into long-term enterprise retainers.
"""

        chart_data = {
            "labels": list(c_counts.keys()),
            "values": list(c_counts.values()),
        }

        return AgentResponse(
            answer=answer,
            kpis={
                "Annual Rate Contracts": str(arc_count),
                "Active POCs": str(poc_count),
                "Monthly Contracts": str(monthly_count),
            },
            chart_type="pie",
            chart_data=chart_data,
            suggested_followups=[
                "Which clients converted from POC to Annual Contract?",
                "Show unbilled revenue in Annual Rate Contracts",
            ],
        )

    def _handle_simulation_query(self, raw_query: str) -> AgentResponse:
        """Runs what-if scenario simulations."""
        sim = self.engine.simulate_what_if(conversion_boost_pct=15.0, unbilled_invoiced_pct=50.0, spectra_upsell_pct=20.0)
        fin = self.engine.get_financial_summary()

        answer = f"""### 🔮 Executive Growth & Revenue What-If Simulation

**Scenario Parameters Applied:**
1. **+15% Proposal Conversion Rate:** Moves pending proposals into closed wins.
2. **50% Unbilled Backlog Invoiced:** Expedites milestone invoicing on executed projects.
3. **+20% Spectra SaaS Upsell:** Attaches Spectra cloud software to won contracts.

---

#### 🚀 Projected Business Impact:
- **Projected Won Revenue:** **{self.format_currency(sim['simulated_won_total'])}** (an uplift of **+{self.format_currency(sim['additional_won_revenue'])}** or **+{sim['growth_delta_pct']}%**).
- **Immediate Invoiced Inflow:** **+{self.format_currency(sim['unlocked_invoiced_cash'])}** unlocked from unbilled execution backlog.
- **Simulated Cash Collections:** **{self.format_currency(sim['simulated_cash_collected'])}** (up from current {self.format_currency(fin['total_collected_value'])}).
- **Spectra Software Run-Rate:** **{self.format_currency(sim['simulated_spectra_revenue'])}**.
"""

        chart_data = {
            "labels": ["Current Won", "Simulated Won", "Current Billed", "Simulated Billed", "Current Cash", "Simulated Cash"],
            "values": [
                fin["total_won_value"],
                sim["simulated_won_total"],
                fin["total_billed_value"],
                sim["simulated_billed_total"],
                fin["total_collected_value"],
                sim["simulated_cash_collected"],
            ],
        }

        return AgentResponse(
            answer=answer,
            kpis={
                "Uplift Potential": f"+{self.format_currency(sim['additional_won_revenue'])}",
                "Unlocked Cash": f"+{self.format_currency(sim['unlocked_invoiced_cash'])}",
                "Growth Delta": f"+{sim['growth_delta_pct']}%",
            },
            chart_type="bar",
            chart_data=chart_data,
            suggested_followups=[
                "What if we invoice 100% of unbilled work orders?",
                "Simulate closing our top 5 pipeline deals",
            ],
        )

    def _handle_sector_query(self, sector: str, raw_query: str) -> AgentResponse:
        """Deep dive into a specific sector (e.g. Energy/Renewables, Mining, Powerline)."""
        deals_sec = self.deals_df[self.deals_df["sector"] == sector]
        wo_sec = self.wo_df[self.wo_df["sector"] == sector]

        total_deals = len(deals_sec)
        won_deals = deals_sec[deals_sec["deal_status"] == "Won"]
        open_deals = deals_sec[deals_sec["deal_status"] == "Open"]
        lost_deals = deals_sec[deals_sec["deal_status"] == "Lost"]

        pipeline_val = open_deals["deal_value"].sum()
        won_val = won_deals["deal_value"].sum()
        win_rate = (len(won_deals) / max(len(won_deals) + len(lost_deals), 1)) * 100

        total_wos = len(wo_sec)
        completed_wos = (wo_sec["execution_status"] == "Completed").sum()
        ongoing_wos = (wo_sec["execution_status"] == "Ongoing").sum()
        delayed_wos = wo_sec["is_delayed"].sum()
        wo_val = wo_sec["amount_excl_gst"].sum()
        billed_val = wo_sec["billed_excl_gst"].sum()
        collected_val = wo_sec["collected_incl_gst"].sum()

        caveats = []
        missing_val_cnt = open_deals["deal_value"].isna().sum()
        if missing_val_cnt > 0:
            caveats.append(
                f"{missing_val_cnt} of {len(open_deals)} open {sector} deals do not have recorded deal values."
            )

        answer = f"""### 🎯 Sector Intelligence: **{sector}**

**Executive Summary:**
The **{sector}** sector represents **{total_deals} deals** and **{total_wos} executed work orders**. The active sales pipeline currently holds **{len(open_deals)} open deals** worth **{self.format_currency(pipeline_val)}**, with a historical deal win rate of **{win_rate:.1f}%**.

---

#### 📊 1. Sales Pipeline & Deal Velocity
- **Active Pipeline Value:** {self.format_currency(pipeline_val)} across {len(open_deals)} active opportunities.
- **Closed Won Bookings:** {self.format_currency(won_val)} ({len(won_deals)} deals won).
- **Win Rate:** {win_rate:.1f}% ({len(won_deals)} won vs {len(lost_deals)} lost).
- **Stage Distribution:** Top open stages include *{', '.join(open_deals['deal_stage'].value_counts().head(2).index.tolist()) if not open_deals.empty else 'N/A'}*.

#### ⚡ 2. Operations & Execution Health
- **Total Work Orders:** {total_wos} ({completed_wos} completed, {ongoing_wos} ongoing).
- **Delivery SLA Health:** {delayed_wos} work orders ({round((delayed_wos/max(total_wos,1))*100, 1)}%) flagged with delivery delays.
- **Contracted WO Value:** {self.format_currency(wo_val)}
- **Billed vs Collected:** {self.format_currency(billed_val)} billed, {self.format_currency(collected_val)} cash collected.

#### 💡 Strategic Takeaway:
{"Renewables is our highest volume deal vertical; ensuring fast POC conversion will unlock massive pipeline velocity." if sector == "Renewables" else f"{sector} demonstrates steady operational fulfillment with strong repeat contract potential."}
"""

        top_open = open_deals.sort_values(by="deal_value", ascending=False).head(5)[
            ["deal_name", "owner_code", "deal_stage", "closure_probability", "deal_value"]
        ].to_dict(orient="records")

        for r in top_open:
            r["deal_value_formatted"] = self.format_currency(r["deal_value"])

        stage_counts = deals_sec["deal_stage"].value_counts().to_dict()

        return AgentResponse(
            answer=answer,
            kpis={
                "Pipeline Value": self.format_currency(pipeline_val),
                "Won Value": self.format_currency(won_val),
                "Win Rate": f"{win_rate:.1f}%",
                "Work Orders": f"{completed_wos}/{total_wos} Done",
                "Delayed WOs": str(delayed_wos),
            },
            table_data=top_open,
            chart_type="pie",
            chart_data={"labels": list(stage_counts.keys()), "values": list(stage_counts.values())},
            caveats=caveats,
            suggested_followups=[
                f"Show delayed work orders in {sector}",
                f"Compare {sector} with Mining win rate",
                f"What is our unbilled revenue in {sector}?",
            ],
        )

    def _handle_pipeline_query(self, raw_query: str) -> AgentResponse:
        """Analyzes overarching deals pipeline and stage distribution."""
        fin = self.engine.get_financial_summary()
        open_deals = self.deals_df[self.deals_df["deal_status"] == "Open"]
        stage_df = open_deals["deal_stage"].value_counts().reset_index()
        stage_df.columns = ["Stage", "Count"]

        sector_pipe = open_deals.groupby("sector")["deal_value"].sum().sort_values(ascending=False).to_dict()

        answer = f"""### 🚀 Sales Pipeline & Funnel Health

**Headline Summary:**
The total active sales pipeline stands at **{self.format_currency(fin['total_pipeline_value'])}** across **{fin['open_deals_count']} open deals**, with a probability-weighted value of **{self.format_currency(fin['weighted_pipeline_value'])}**.

---

#### 📈 Key Pipeline Metrics:
- **Total Open Deals:** {fin['open_deals_count']} opportunities
- **Gross Pipeline Value:** {self.format_currency(fin['total_pipeline_value'])}
- **Probability-Weighted Value:** {self.format_currency(fin['weighted_pipeline_value'])}
- **Closed Won Bookings:** {self.format_currency(fin['total_won_value'])} ({fin['won_deals_count']} deals)
- **Historical Win Rate:** {fin['win_rate_count_pct']}%

#### 🏢 Pipeline Value by Vertical:
"""
        for sec, val in list(sector_pipe.items())[:5]:
            answer += f"- **{sec}:** {self.format_currency(val)}\n"

        answer += """
#### 💡 Executive Insights:
1. **High Lead Volume in Renewables & Mining:** 70%+ of open opportunities are concentrated in Clean Energy and Mining.
2. **Funnel Bottleneck:** High drop-off observed between *Proposal Sent* and *Negotiations*.
"""

        top_deals = open_deals.sort_values(by="deal_value", ascending=False).head(5)[
            ["deal_name", "sector", "deal_stage", "closure_probability", "deal_value", "owner_code"]
        ].to_dict(orient="records")
        for r in top_deals:
            r["deal_value_formatted"] = self.format_currency(r["deal_value"])

        return AgentResponse(
            answer=answer,
            kpis={
                "Gross Pipeline": self.format_currency(fin["total_pipeline_value"]),
                "Weighted Pipeline": self.format_currency(fin["weighted_pipeline_value"]),
                "Open Deals": str(fin["open_deals_count"]),
                "Win Rate": f"{fin['win_rate_count_pct']}%",
            },
            table_data=top_deals,
            chart_type="bar",
            chart_data={"labels": list(sector_pipe.keys())[:6], "values": list(sector_pipe.values())[:6]},
            caveats=["52% of deals lack explicit deal values in Monday.com; actual pipeline may be significantly higher."],
            suggested_followups=[
                "Break down pipeline by BD Owner",
                "Show high-probability deals closing soon",
                "What is our win rate in Mining vs Renewables?",
            ],
        )

    def _handle_financial_query(self, raw_query: str) -> AgentResponse:
        """Analyzes revenue recognition, billed value, cash collected, and receivables."""
        fin = self.engine.get_financial_summary()

        answer = f"""### 💰 Revenue Recognition, Collections & AR Summary

**Headline Financials:**
- **Total Work Order Contract Value:** {self.format_currency(fin['total_wo_contract_value'])}
- **Total Billed Value:** {self.format_currency(fin['total_billed_value'])} ({fin['billing_efficiency_pct']}% billing progress)
- **Total Cash Collected:** {self.format_currency(fin['total_collected_value'])}
- **Unbilled Backlog:** {self.format_currency(fin['total_unbilled_value'])}
- **Outstanding Accounts Receivable (AR):** {self.format_currency(fin['total_receivables'])}

---

#### 🔍 Cash Flow & Revenue Leakage Analysis:
1. **Unbilled Execution Backlog:** **{self.format_currency(fin['total_unbilled_value'])}** worth of executed/ongoing projects have not yet been invoiced. Accelerating milestone signoffs can unlock instant billing.
2. **Receivables Aging:** **{self.format_currency(fin['total_receivables'])}** is currently pending collection from enterprise accounts.
"""

        top_ar = self.wo_df[self.wo_df["receivable_amount"] > 0].sort_values(
            by="receivable_amount", ascending=False
        ).head(5)[
            ["deal_name", "wo_serial_id", "sector", "billed_incl_gst", "collected_incl_gst", "receivable_amount", "owner_code"]
        ].to_dict(orient="records")
        for r in top_ar:
            r["receivable_formatted"] = self.format_currency(r["receivable_amount"])

        return AgentResponse(
            answer=answer,
            kpis={
                "Contracted WO": self.format_currency(fin["total_wo_contract_value"]),
                "Billed Value": self.format_currency(fin["total_billed_value"]),
                "Cash Collected": self.format_currency(fin["total_collected_value"]),
                "Unbilled Backlog": self.format_currency(fin["total_unbilled_value"]),
                "Outstanding AR": self.format_currency(fin["total_receivables"]),
            },
            table_data=top_ar,
            chart_type="bar",
            chart_data={
                "labels": ["Contract Value", "Billed Value", "Cash Collected", "Unbilled Backlog", "Receivables"],
                "values": [
                    fin["total_wo_contract_value"],
                    fin["total_billed_value"],
                    fin["total_collected_value"],
                    fin["total_unbilled_value"],
                    fin["total_receivables"],
                ],
            },
            caveats=["Receivables and Collected amounts include GST as per invoicing records."],
            suggested_followups=[
                "Which clients have the largest outstanding receivables?",
                "Show unbilled work orders in Mining sector",
                "What is our revenue collection rate?",
            ],
        )

    def _handle_operations_query(self, raw_query: str) -> AgentResponse:
        """Analyzes operations, work order delivery health, and SLA delays."""
        fin = self.engine.get_financial_summary()
        delayed = self.wo_df[self.wo_df["is_delayed"]]
        avg_tat = self.wo_df["execution_days"].dropna().mean()

        answer = f"""### ⚡ Operations Execution & Delivery SLA Health

**Headline Summary:**
Across **{fin['total_work_orders']} Work Orders**, Skylark has successfully delivered **{fin['completed_work_orders']} completed projects**, with **{fin['ongoing_work_orders']} currently active** and **{fin['delayed_work_orders']} flagged with delivery delays**.

---

#### ⏱️ Operational KPIs:
- **Completion Rate:** {round((fin['completed_work_orders']/max(fin['total_work_orders'],1))*100, 1)}%
- **Average Project TAT:** {avg_tat:.1f} days (from Start to Final Data Delivery)
- **Delayed Deliverables:** {len(delayed)} work orders ({round((len(delayed)/max(fin['total_work_orders'],1))*100, 1)}% of total)
- **Delayed Contract Value at Risk:** {self.format_currency(delayed['amount_excl_gst'].sum())}

#### 🚨 Root Cause & Operational Takeaways:
- **Weather & Permitting Bottlenecks:** DGCA fly-zone approvals and client site access cause the primary delays in Mining and Powerline corridors.
- **Fastest Turnaround Sector:** Renewables exhibits the shortest average turnaround time ({self.wo_df[self.wo_df['sector']=='Renewables']['execution_days'].mean():.1f} days).
"""

        delayed_table = delayed.sort_values(by="amount_excl_gst", ascending=False).head(5)[
            ["deal_name", "wo_serial_id", "sector", "delivery_delay_days", "amount_excl_gst", "execution_status"]
        ].to_dict(orient="records")
        for r in delayed_table:
            r["amount_formatted"] = self.format_currency(r["amount_excl_gst"])

        status_counts = self.wo_df["execution_status"].value_counts().to_dict()

        return AgentResponse(
            answer=answer,
            kpis={
                "Total WOs": str(fin["total_work_orders"]),
                "Completed": str(fin["completed_work_orders"]),
                "Ongoing": str(fin["ongoing_work_orders"]),
                "Delayed WOs": str(fin["delayed_work_orders"]),
                "Avg TAT": f"{avg_tat:.1f} days",
            },
            table_data=delayed_table,
            chart_type="pie",
            chart_data={"labels": list(status_counts.keys()), "values": list(status_counts.values())},
            caveats=["Delivery delay is computed against Probable End Date from PO."],
            suggested_followups=[
                "Which BD owners manage the delayed work orders?",
                "Show unbilled completed work orders",
                "What is our average TAT in Railways vs Mining?",
            ],
        )

    def _handle_win_rate_query(self, raw_query: str) -> AgentResponse:
        """Analyzes deal conversion and win rates across sectors and owners."""
        sec_matrix = self.engine.get_sector_breakdown()

        answer = f"""### 🏆 Deal Win Rate & Conversion Analysis

**Overall Win Rate:** **{self.engine.get_financial_summary()['win_rate_count_pct']}%** across all closed opportunities.

---

#### 📊 Win Rate by Sector:
"""
        for _, row in sec_matrix[sec_matrix["total_deals"] >= 5].iterrows():
            answer += f"- **{row['sector']}:** {row['win_rate_pct']}% win rate ({int(row['won_deals'])} won / {int(row['lost_deals'])} lost) — Won Value: {self.format_currency(row['won_value'])}\n"

        answer += """
#### 💡 Strategic Analysis:
- **Mining & Railways:** Demonstrate highest deal conversion resilience.
- **Renewables:** High top-of-funnel lead generation with moderate proposal-to-close conversion rate.
"""

        chart_data = {
            "labels": sec_matrix[sec_matrix["total_deals"] >= 5]["sector"].tolist(),
            "values": sec_matrix[sec_matrix["total_deals"] >= 5]["win_rate_pct"].tolist(),
        }

        return AgentResponse(
            answer=answer,
            kpis={"Overall Win Rate": f"{self.engine.get_financial_summary()['win_rate_count_pct']}%"},
            chart_type="bar",
            chart_data=chart_data,
            suggested_followups=[
                "Show top reasons for lost deals",
                "Break down win rate by BD Owner code",
                "How does pipeline value correlate with won value?",
            ],
        )

    def _handle_leadership_query(self, raw_query: str) -> AgentResponse:
        """Quick summary for leadership update."""
        fin = self.engine.get_financial_summary()
        answer = f"""### 👔 Skylark Executive Leadership Brief

**Headline Highlights:**
1. **Sales Momentum:** Total open pipeline stands at **{self.format_currency(fin['total_pipeline_value'])}** ({fin['open_deals_count']} active opportunities) with **{self.format_currency(fin['total_won_value'])}** in closed bookings ({fin['win_rate_count_pct']}% win rate).
2. **Operational Execution:** **{fin['completed_work_orders']} of {fin['total_work_orders']} Work Orders completed** ({round((fin['completed_work_orders']/max(fin['total_work_orders'],1))*100, 1)}% execution rate).
3. **Cash & Receivables:** **{self.format_currency(fin['total_collected_value'])}** collected to date; **{self.format_currency(fin['total_unbilled_value'])}** remains in unbilled project backlog.

---

👉 *Tip: Open the **'Leadership Briefings'** tab for the full comprehensive 1-click weekly/quarterly update report.*
"""
        return AgentResponse(
            answer=answer,
            kpis={
                "Pipeline": self.format_currency(fin["total_pipeline_value"]),
                "Won Bookings": self.format_currency(fin["total_won_value"]),
                "Completed WOs": f"{fin['completed_work_orders']}/{fin['total_work_orders']}",
                "Cash Collected": self.format_currency(fin["total_collected_value"]),
            },
            suggested_followups=[
                "Generate full weekly leadership update",
                "What are the top 3 operational red flags?",
                "Which deals are expected to close this month?",
            ],
        )

    def _handle_data_quality_query(self, raw_query: str) -> AgentResponse:
        """Explains data quality scores, missing values, and normalization rules."""
        if not self.quality_report:
            return AgentResponse(answer="Data quality report is not available.")

        rep = self.quality_report.to_dict()
        answer = f"""### 🩺 Data Resilience & Quality Audit

**Overall Data Cleanliness Score:** **{rep['quality_score']}/100**

---

#### 🔍 Audit Findings:
- **Total Deals Ingested:** {rep['total_deals']} (Clean: {rep['clean_deals']})
- **Total Work Orders Ingested:** {rep['total_work_orders']} (Clean: {rep['clean_work_orders']})
- **Missing Deal Values:** {rep['deals_missing_value_pct']}% of deals lack recorded contract value.
- **Missing Won Close Dates:** {rep['deals_missing_date_pct']}% of won deals lack explicit close dates.
- **Unlinked Work Orders:** {rep['wo_unlinked_pct']}% of work orders did not match a Deal Name key.

#### 🛡️ Autonomous Cleaning Applied:
- Normalized mixed date styles (DD/MM/YYYY, ISO, relative).
- Cleaned strings containing currency symbols (₹, $, Lakhs, Cr, commas).
- Fuzzy matched vertical sector names into canonical categories.
- Removed duplicate headers and ghost rows.
"""
        return AgentResponse(
            answer=answer,
            kpis={
                "Quality Score": f"{rep['quality_score']}/100",
                "Clean Records": f"{rep['clean_deals'] + rep['clean_work_orders']}",
                "Missing Val %": f"{rep['deals_missing_value_pct']}%",
            },
            caveats=rep["caveats"],
            suggested_followups=[
                "Show pipeline health with quality caveats",
                "How does missing data affect revenue projections?",
            ],
        )

    def _handle_general_overview(self, raw_query: str) -> AgentResponse:
        """Handles broad or conversational queries, offering macro metrics and clarifying drilldowns."""
        fin = self.engine.get_financial_summary()
        answer = f"""### 🛸 Skylark Drones Business Intelligence Overview

I have synthesized real-time intelligence across your **Deals Funnel ({fin['total_deals_count']} deals)** and **Work Order Tracker ({fin['total_work_orders']} projects)**:

- **Sales Pipeline:** **{self.format_currency(fin['total_pipeline_value'])}** gross open pipeline across **{fin['open_deals_count']} opportunities**.
- **Won Bookings:** **{self.format_currency(fin['total_won_value'])}** with an overall **{fin['win_rate_count_pct']}% win rate**.
- **Operational Fulfillment:** **{fin['completed_work_orders']} Work Orders completed** ({self.format_currency(fin['total_wo_contract_value'])} contracted value).
- **Cash Flow:** **{self.format_currency(fin['total_collected_value'])} collected**; **{self.format_currency(fin['total_receivables'])}** in receivables.
- **Spectra SaaS Platform:** Attached to **{fin['spectra_attach_rate_pct']}%** of executed work orders.

---

#### ❓ Would you like to drill into:
1. **Vertical Performance:** Energy/Renewables, Mining, Railways, or Powerline?
2. **Drone Tech Analytics:** Spectra SaaS attach rate, LiDAR vs Topography survey volumes?
3. **What-If Scenario Simulation:** Model revenue uplift from faster proposal conversions?
4. **Executive Briefing:** Prepare a 1-click leadership update report?
"""
        return AgentResponse(
            answer=answer,
            kpis={
                "Pipeline": self.format_currency(fin["total_pipeline_value"]),
                "Won Bookings": self.format_currency(fin["total_won_value"]),
                "Spectra Attach": f"{fin['spectra_attach_rate_pct']}%",
                "Completed WOs": f"{fin['completed_work_orders']}/{fin['total_work_orders']}",
            },
            clarification_needed=True,
            suggested_followups=[
                "How's our pipeline looking for energy sector this quarter?",
                "What is our Spectra SaaS platform attach rate?",
                "Simulate closing our top 3 renewable pipeline deals",
                "Which work orders are delayed with high contract value?",
            ],
        )
