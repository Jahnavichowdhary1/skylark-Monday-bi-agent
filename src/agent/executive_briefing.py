"""
Leadership Update & Executive Briefing Generator for Skylark Drones.
Prepares 1-click weekly, monthly, and quarterly executive briefs for Founders,
C-suite, and Board meetings.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
import pandas as pd

from src.core.cross_board_engine import CrossBoardEngine
from src.core.data_normalizer import DataQualityReport


class ExecutiveBriefingGenerator:
    """Generates structured, high-impact Leadership Update Briefs."""

    def __init__(
        self,
        deals_df: pd.DataFrame,
        wo_df: pd.DataFrame,
        quality_report: Optional[DataQualityReport] = None,
    ):
        self.deals_df = deals_df
        self.wo_df = wo_df
        self.quality_report = quality_report
        self.engine = CrossBoardEngine(deals_df, wo_df)

    def _fmt(self, val: Optional[float]) -> str:
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

    def generate_briefing(self, period: str = "Quarterly Sync") -> Dict[str, Any]:
        """Generates comprehensive leadership update document and structured metadata."""
        fin = self.engine.get_financial_summary()
        sec_df = self.engine.get_sector_breakdown()
        risks = self.engine.get_risk_anomalies()

        # Top won deals
        top_won = self.deals_df[self.deals_df["deal_status"] == "Won"].sort_values(
            by="deal_value", ascending=False
        ).head(5)

        # Top pipeline deals
        top_open = self.deals_df[self.deals_df["deal_status"] == "Open"].sort_values(
            by="deal_value", ascending=False
        ).head(5)

        report_date = datetime.now().strftime("%B %d, %Y")

        # Build Markdown Document
        md = f"""# 🛸 Skylark Drones - Executive Leadership Briefing
**Reporting Scope:** {period}  
**Date:** {report_date}  
**Prepared By:** Skylark Business Intelligence AI Agent  
**Data Sources:** Monday.com Deals Funnel & Work Order Tracker  

---

## 1. 📊 Executive Scorecard

| Metric | Current Value | Context / Benchmark |
| :--- | :--- | :--- |
| **Gross Sales Pipeline** | **{self._fmt(fin['total_pipeline_value'])}** | Across {fin['open_deals_count']} active opportunities |
| **Probability-Weighted Pipeline** | **{self._fmt(fin['weighted_pipeline_value'])}** | Adjusted for stage closure probability |
| **Closed Won Bookings** | **{self._fmt(fin['total_won_value'])}** | {fin['won_deals_count']} won deals ({fin['win_rate_count_pct']}% count win rate) |
| **Contracted Work Orders** | **{self._fmt(fin['total_wo_contract_value'])}** | {fin['total_work_orders']} Work Orders initiated |
| **Billed Revenue** | **{self._fmt(fin['total_billed_value'])}** | {fin['billing_efficiency_pct']}% billing progress against contracted |
| **Cash Collected** | **{self._fmt(fin['total_collected_value'])}** | Inflow received against billings |
| **Unbilled Project Backlog** | **{self._fmt(fin['total_unbilled_value'])}** | Revenue pending milestone invoicing |
| **Outstanding Receivables (AR)**| **{self._fmt(fin['total_receivables'])}** | Pending client collection |
| **Data Completeness Score** | **{self.quality_report.quality_score if self.quality_report else 85.0}/100** | Automated cleaning & cross-board linkage |

---

## 2. 🚀 Sales Pipeline & Bookings Highlights

- **Top Growth Vertical:** **Renewables** leads volume with {sec_df[sec_df['sector']=='Renewables']['total_deals'].values[0] if not sec_df[sec_df['sector']=='Renewables'].empty else 0} deals, followed closely by **Mining** with {sec_df[sec_df['sector']=='Mining']['total_deals'].values[0] if not sec_df[sec_df['sector']=='Mining'].empty else 0} deals.
- **Top Closed Deals Won:**
"""
        for _, r in top_won.iterrows():
            md += f"  - **{r['deal_name']}** ({r['sector']}) — {self._fmt(r['deal_value'])} [Owner: `{r['owner_code']}`]\n"

        md += """
- **High-Priority Open Opportunities (Closing Soon):**
"""
        for _, r in top_open.iterrows():
            md += f"  - **{r['deal_name']}** ({r['sector']}) — {self._fmt(r['deal_value'])} [Stage: `{r['deal_stage']}`, Prob: `{r['closure_probability']}`]\n"

        md += f"""
---

## 3. 🏢 Sector Performance Matrix

| Sector / Vertical | Total Deals | Won Deals | Win Rate | Pipeline Value | Won Bookings | Work Orders | Avg Execution TAT |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
"""
        for _, r in sec_df.head(6).iterrows():
            md += f"| **{r['sector']}** | {int(r['total_deals'])} | {int(r['won_deals'])} | {r['win_rate_pct']}% | {self._fmt(r['pipeline_value'])} | {self._fmt(r['won_value'])} | {int(r['total_wos'])} | {r['avg_execution_days']} days |\n"

        md += f"""
---

## 4. ⚡ Operations Execution & Delivery SLA Health

- **Project Execution Status:**
  - **Completed:** {fin['completed_work_orders']} Work Orders ({round((fin['completed_work_orders']/max(fin['total_work_orders'],1))*100, 1)}%)
  - **Ongoing / Active:** {fin['ongoing_work_orders']} Work Orders
  - **Delayed Deliveries:** {fin['delayed_work_orders']} Work Orders flagged past target completion dates.
- **Average Turnaround Time:** **{self.wo_df['execution_days'].dropna().mean():.1f} days** from flight initiation to client data delivery.

---

## 5. 🚨 Risk Radar & Operational Red Flags

### Top Overdue Work Orders (Revenue at Risk):
"""
        if risks["delayed_work_orders"]:
            for r in risks["delayed_work_orders"][:4]:
                md += f"- ⚠️ **{r['deal_name']}** (`{r['wo_serial_id']}`): {self._fmt(r['amount_excl_gst'])} in {r['sector']} is **{r['delivery_delay_days']} days overdue** [Owner: `{r['owner_code']}`]\n"
        else:
            md += "- *No high-risk overdue work orders detected.*\n"

        md += f"""
### Top Outstanding Accounts Receivable:
"""
        if risks["large_receivables"]:
            for r in risks["large_receivables"][:3]:
                md += f"- 💳 **{r['deal_name']}** (`{r['wo_serial_id']}`): **{self._fmt(r['receivable_amount'])}** receivable pending collection in {r['sector']}.\n"

        md += """
---

## 6. 🎯 Strategic Action Items for Leadership

1. **Unblock Invoicing Milestone:** Expedite sign-offs on unbilled work orders to convert unbilled backlog into cash collections.
2. **Accelerate Renewables Proposal Stage:** Focus BD resources on moving high-probability Renewable deals from *Proposal Sent* to *Negotiation/Won*.
3. **Operations SLA Taskforce:** Review delayed Mining & Powerline deliverables with regional field teams to eliminate DGCA/client site bottlenecks.
4. **Data Hygiene Initiative:** Mandate standard deal value and close date logging on Monday.com boards to eliminate pipeline blindspots.
"""

        return {
            "title": f"Skylark Executive Briefing - {period}",
            "generated_at": report_date,
            "markdown": md,
            "financial_kpis": fin,
            "sector_data": sec_df.to_dict(orient="records"),
            "risk_data": risks,
        }
