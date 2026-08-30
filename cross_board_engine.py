"""
Cross-Board Correlation & Business Intelligence Engine.
Correlates Sales Pipeline (Deals) with Operations Execution (Work Orders)
to analyze conversion velocity, revenue recognition gaps, sectoral performance,
Spectra SaaS attach rate, drone survey analytics, and what-if financial simulations.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np


class CrossBoardEngine:
    """Computes cross-board aggregations, drone domain metrics, and what-if simulations."""

    def __init__(self, deals_df: pd.DataFrame, wo_df: pd.DataFrame):
        self.deals_df = deals_df.copy()
        self.wo_df = wo_df.copy()

    def get_financial_summary(self) -> Dict[str, Any]:
        """Calculates overarching executive financial KPIs across both boards."""
        total_deals = len(self.deals_df)
        won_deals = self.deals_df[self.deals_df["deal_status"] == "Won"]
        open_deals = self.deals_df[self.deals_df["deal_status"] == "Open"]
        lost_deals = self.deals_df[self.deals_df["deal_status"] == "Lost"]

        total_pipeline_val = open_deals["deal_value"].sum()
        total_won_val = won_deals["deal_value"].sum()

        win_rate_count = (len(won_deals) / max(len(won_deals) + len(lost_deals), 1)) * 100
        won_val_denom = total_won_val + lost_deals["deal_value"].sum()
        win_rate_value = (total_won_val / max(won_val_denom, 1.0)) * 100 if won_val_denom > 0 else 0.0

        total_wos = len(self.wo_df)
        completed_wos = (self.wo_df["execution_status"] == "Completed").sum()
        ongoing_wos = (self.wo_df["execution_status"] == "Ongoing").sum()
        delayed_wos = self.wo_df["is_delayed"].sum()

        total_wo_contract_val = self.wo_df["amount_excl_gst"].sum()
        total_wo_billed_val = self.wo_df["billed_excl_gst"].sum()
        total_wo_collected_val = self.wo_df["collected_incl_gst"].sum()
        total_unbilled_val = self.wo_df["unbilled_excl_gst"].sum()
        total_receivable_val = self.wo_df["receivable_amount"].sum()

        prob_map = {"High": 0.8, "Medium": 0.5, "Low": 0.2}
        open_deals_calc = open_deals.copy()
        open_deals_calc["weight"] = open_deals_calc["closure_probability"].map(prob_map).fillna(0.3)
        weighted_pipeline_val = (open_deals_calc["deal_value"].fillna(0) * open_deals_calc["weight"]).sum()

        # Spectra SaaS platform metrics
        spectra_wos = self.wo_df[self.wo_df["software_platform"].str.contains("Spectra", case=False, na=False)]
        spectra_attach_rate = (len(spectra_wos) / max(total_wos, 1)) * 100
        spectra_contract_val = spectra_wos["amount_excl_gst"].sum()

        return {
            "total_deals_count": total_deals,
            "won_deals_count": len(won_deals),
            "open_deals_count": len(open_deals),
            "lost_deals_count": len(lost_deals),
            "total_pipeline_value": total_pipeline_val,
            "weighted_pipeline_value": weighted_pipeline_val,
            "total_won_value": total_won_val,
            "win_rate_count_pct": round(win_rate_count, 1),
            "win_rate_value_pct": round(win_rate_value, 1),
            "total_work_orders": total_wos,
            "completed_work_orders": int(completed_wos),
            "ongoing_work_orders": int(ongoing_wos),
            "delayed_work_orders": int(delayed_wos),
            "total_wo_contract_value": total_wo_contract_val,
            "total_billed_value": total_wo_billed_val,
            "total_collected_value": total_wo_collected_val,
            "total_unbilled_value": total_unbilled_val,
            "total_receivables": total_receivable_val,
            "billing_efficiency_pct": round((total_wo_billed_val / max(total_wo_contract_val, 1)) * 100, 1),
            "spectra_attach_rate_pct": round(spectra_attach_rate, 1),
            "spectra_contract_value": spectra_contract_val,
        }

    def get_drone_analytics(self) -> Dict[str, Any]:
        """Calculates deep domain drone surveying and platform metrics."""
        # 1. Spectra Platform Attach Rate Breakdown
        platform_counts = self.wo_df["software_platform"].value_counts().to_dict()
        platform_revenue = self.wo_df.groupby("software_platform")["amount_excl_gst"].sum().to_dict()

        # 2. Survey Work Type Breakdown (Topography RGB, LiDAR, Hydrology, Thermography, Volumetric)
        work_type_counts = self.wo_df["work_type"].value_counts().head(8).to_dict()
        work_type_rev = self.wo_df.groupby("work_type")["amount_excl_gst"].sum().sort_values(ascending=False).head(8).to_dict()

        # 3. Nature of Contract (POC vs ARC vs One-Time vs Monthly)
        contract_counts = self.wo_df["nature_of_work"].value_counts().to_dict()

        # 4. BD / KAM Owner Leaderboard
        owner_deals = self.deals_df.groupby("owner_code").agg(
            total_deals=("deal_name", "count"),
            won_deals=("deal_status", lambda s: (s == "Won").sum()),
            open_deals=("deal_status", lambda s: (s == "Open").sum()),
            won_value=("deal_value", lambda v: self.deals_df.loc[v.index][self.deals_df.loc[v.index, "deal_status"] == "Won"]["deal_value"].sum()),
            pipeline_value=("deal_value", lambda v: self.deals_df.loc[v.index][self.deals_df.loc[v.index, "deal_status"] == "Open"]["deal_value"].sum()),
        ).reset_index()

        owner_wo = self.wo_df.groupby("owner_code").agg(
            total_wos=("wo_serial_id", "count"),
            delayed_wos=("is_delayed", "sum"),
            wo_billed=("billed_excl_gst", "sum"),
            wo_unbilled=("unbilled_excl_gst", "sum"),
        ).reset_index()

        owner_matrix = pd.merge(owner_deals, owner_wo, on="owner_code", how="outer").fillna(0)
        owner_matrix["win_rate_pct"] = (
            owner_matrix["won_deals"] / (owner_matrix["won_deals"] + owner_matrix["total_deals"] - owner_matrix["won_deals"] - owner_matrix["open_deals"]).replace(0, 1)
        ) * 100
        owner_matrix["win_rate_pct"] = owner_matrix["win_rate_pct"].round(1)
        owner_matrix.sort_values(by="won_value", ascending=False, inplace=True)

        return {
            "platform_counts": platform_counts,
            "platform_revenue": platform_revenue,
            "work_type_counts": work_type_counts,
            "work_type_revenue": work_type_rev,
            "contract_counts": contract_counts,
            "owner_matrix": owner_matrix.to_dict(orient="records"),
        }

    def simulate_what_if(
        self,
        conversion_boost_pct: float = 10.0,
        unbilled_invoiced_pct: float = 50.0,
        spectra_upsell_pct: float = 15.0,
    ) -> Dict[str, Any]:
        """Simulates revenue, cash flow, and ARR uplift under leadership growth initiatives."""
        fin = self.get_financial_summary()

        # 1. Pipeline conversion uplift
        current_pipeline = fin["total_pipeline_value"]
        additional_won = current_pipeline * (conversion_boost_pct / 100.0)
        sim_won_total = fin["total_won_value"] + additional_won

        # 2. Invoicing acceleration
        current_unbilled = fin["total_unbilled_value"]
        unlocked_cash = current_unbilled * (unbilled_invoiced_pct / 100.0)
        sim_billed_total = fin["total_billed_value"] + unlocked_cash
        sim_collected_total = fin["total_collected_value"] + (unlocked_cash * 0.85)

        # 3. Spectra SaaS platform expansion
        sim_spectra_rev = fin["spectra_contract_value"] * (1.0 + (spectra_upsell_pct / 100.0))

        return {
            "additional_won_revenue": additional_won,
            "simulated_won_total": sim_won_total,
            "unlocked_invoiced_cash": unlocked_cash,
            "simulated_billed_total": sim_billed_total,
            "simulated_cash_collected": sim_collected_total,
            "simulated_spectra_revenue": sim_spectra_rev,
            "growth_delta_pct": round((additional_won / max(fin["total_won_value"], 1)) * 100, 1),
        }

    def get_sector_breakdown(self) -> pd.DataFrame:
        """Generates comprehensive sector comparison matrix."""
        deals_grp = self.deals_df.groupby("sector").agg(
            total_deals=("deal_name", "count"),
            won_deals=("deal_status", lambda s: (s == "Won").sum()),
            open_deals=("deal_status", lambda s: (s == "Open").sum()),
            lost_deals=("deal_status", lambda s: (s == "Lost").sum()),
            pipeline_value=("deal_value", lambda v: self.deals_df.loc[v.index][self.deals_df.loc[v.index, "deal_status"] == "Open"]["deal_value"].sum()),
            won_value=("deal_value", lambda v: self.deals_df.loc[v.index][self.deals_df.loc[v.index, "deal_status"] == "Won"]["deal_value"].sum()),
        ).reset_index()

        deals_grp["win_rate_pct"] = (
            deals_grp["won_deals"] / (deals_grp["won_deals"] + deals_grp["lost_deals"]).replace(0, 1)
        ) * 100
        deals_grp["win_rate_pct"] = deals_grp["win_rate_pct"].round(1)

        wo_grp = self.wo_df.groupby("sector").agg(
            total_wos=("wo_serial_id", "count"),
            completed_wos=("execution_status", lambda s: (s == "Completed").sum()),
            ongoing_wos=("execution_status", lambda s: (s == "Ongoing").sum()),
            delayed_wos=("is_delayed", "sum"),
            wo_contract_val=("amount_excl_gst", "sum"),
            wo_billed_val=("billed_excl_gst", "sum"),
            wo_collected_val=("collected_incl_gst", "sum"),
            avg_execution_days=("execution_days", "mean"),
        ).reset_index()

        merged = pd.merge(deals_grp, wo_grp, on="sector", how="outer").fillna(0)
        merged["avg_execution_days"] = merged["avg_execution_days"].round(1)
        merged.sort_values(by="won_value", ascending=False, inplace=True)
        return merged

    def get_risk_anomalies(self) -> Dict[str, Any]:
        """Identifies critical operational and revenue risks across both boards."""
        delayed_wos = self.wo_df[self.wo_df["is_delayed"]].sort_values(
            by="amount_excl_gst", ascending=False
        )[
            [
                "deal_name",
                "wo_serial_id",
                "sector",
                "amount_excl_gst",
                "delivery_delay_days",
                "execution_status",
                "owner_code",
            ]
        ].head(10).to_dict(orient="records")

        won_deals = self.deals_df[self.deals_df["deal_status"] == "Won"]
        wo_deal_names = set(self.wo_df["deal_name"].dropna().astype(str).str.strip().str.lower())
        unfulfilled_deals = won_deals[
            ~won_deals["deal_name"].astype(str).str.strip().str.lower().isin(wo_deal_names)
        ].sort_values(by="deal_value", ascending=False)[
            ["deal_name", "sector", "deal_value", "owner_code", "actual_close_date", "deal_stage"]
        ].head(10).to_dict(orient="records")

        completed_unbilled = self.wo_df[
            (self.wo_df["execution_status"] == "Completed") & (self.wo_df["unbilled_excl_gst"] > 0)
        ].sort_values(by="unbilled_excl_gst", ascending=False)[
            ["deal_name", "wo_serial_id", "sector", "amount_excl_gst", "unbilled_excl_gst", "owner_code"]
        ].head(10).to_dict(orient="records")

        large_receivables = self.wo_df[self.wo_df["receivable_amount"] > 0].sort_values(
            by="receivable_amount", ascending=False
        )[
            ["deal_name", "wo_serial_id", "sector", "billed_incl_gst", "collected_incl_gst", "receivable_amount", "owner_code"]
        ].head(10).to_dict(orient="records")

        return {
            "delayed_work_orders": delayed_wos,
            "unfulfilled_won_deals": unfulfilled_deals,
            "completed_unbilled_wos": completed_unbilled,
            "large_receivables": large_receivables,
        }
