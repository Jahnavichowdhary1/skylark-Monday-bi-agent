"""
Unit tests for CrossBoardEngine and financial analytics.
"""

import os
import pandas as pd
from src.core.data_normalizer import DataNormalizer
from src.core.cross_board_engine import CrossBoardEngine


def test_cross_board_metrics():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    deals_file = os.path.join(base_dir, "data", "deals_raw.xlsx")
    wo_file = os.path.join(base_dir, "data", "work_orders_raw.xlsx")

    deals_raw = pd.read_excel(deals_file)
    wo_raw = pd.read_excel(wo_file)

    clean_deals, _ = DataNormalizer.clean_deals(deals_raw)
    clean_wo, _ = DataNormalizer.clean_work_orders(wo_raw)

    engine = CrossBoardEngine(clean_deals, clean_wo)
    summary = engine.get_financial_summary()

    # Check key figures
    assert summary["total_deals_count"] > 300
    assert summary["won_deals_count"] > 150
    assert summary["open_deals_count"] > 40
    assert summary["total_pipeline_value"] > 500000000.0  # > 50 Cr
    assert summary["total_won_value"] > 80000000.0  # > 8 Cr
    assert summary["total_work_orders"] > 150
    assert summary["completed_work_orders"] > 100
    assert summary["total_wo_contract_value"] > 150000000.0  # > 15 Cr

    # Check sector breakdown
    sec_df = engine.get_sector_breakdown()
    assert not sec_df.empty
    assert "Renewables" in sec_df["sector"].values
    assert "Mining" in sec_df["sector"].values

    # Check risks
    risks = engine.get_risk_anomalies()
    assert "delayed_work_orders" in risks
    assert "large_receivables" in risks
