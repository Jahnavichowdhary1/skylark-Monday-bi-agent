"""
Integration tests for BIAgent query understanding and executive briefing generation.
"""

import os
import pandas as pd
from src.core.data_normalizer import DataNormalizer
from src.agent.bi_agent import BIAgent
from src.agent.executive_briefing import ExecutiveBriefingGenerator


def test_bi_agent_queries():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    deals_file = os.path.join(base_dir, "data", "deals_raw.xlsx")
    wo_file = os.path.join(base_dir, "data", "work_orders_raw.xlsx")

    deals_raw = pd.read_excel(deals_file)
    wo_raw = pd.read_excel(wo_file)

    clean_deals, deals_cav = DataNormalizer.clean_deals(deals_raw)
    clean_wo, wo_cav = DataNormalizer.clean_work_orders(wo_raw)
    report = DataNormalizer.audit_quality(clean_deals, clean_wo, deals_cav, wo_cav)

    agent = BIAgent(clean_deals, clean_wo, report)

    # 1. Test Energy / Renewables query
    res_energy = agent.query("How is our pipeline looking for energy sector this quarter?")
    assert "Renewables" in res_energy.answer
    assert "Pipeline Value" in res_energy.kpis
    assert len(res_energy.caveats) >= 1

    # 2. Test Delayed Work Orders query
    res_wo = agent.query("Which work orders are delayed and what revenue is at risk?")
    assert "Operations Execution" in res_wo.answer
    assert "Delayed WOs" in res_wo.kpis

    # 3. Test Win rate query
    res_win = agent.query("What is our win rate across Mining vs Renewables?")
    assert "Win Rate" in res_win.answer

    # 4. Test Revenue & AR query
    res_fin = agent.query("Summarize our revenue, billed value, and outstanding collections.")
    assert "Revenue Recognition" in res_fin.answer

    # 5. Test Leadership Briefing Generator
    gen = ExecutiveBriefingGenerator(clean_deals, clean_wo, report)
    brief = gen.generate_briefing("Weekly Founder Sync")
    assert "Skylark Drones - Executive Leadership Briefing" in brief["markdown"]
    assert "Executive Scorecard" in brief["markdown"]
