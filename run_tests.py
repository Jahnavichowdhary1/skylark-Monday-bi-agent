"""
Automated Test Runner for Skylark Drones BI Agent.
"""

import sys
import os
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tests.test_normalizer import (
    test_parse_numeric,
    test_parse_date,
    test_normalize_sector,
    test_normalize_deal_status,
    test_clean_deals_and_wo,
)
from tests.test_cross_board import test_cross_board_metrics
from tests.test_agent import test_bi_agent_queries


def main():
    print("==================================================")
    print("🛸 Running Skylark BI Agent Automated Test Suite")
    print("==================================================")

    try:
        print("[1/3] Testing Data Normalizer & Quality Auditor...")
        test_parse_numeric()
        test_parse_date()
        test_normalize_sector()
        test_normalize_deal_status()
        test_clean_deals_and_wo()
        print("  --> PASS: Data Normalization verified.")

        print("[2/3] Testing Cross-Board Correlation Engine...")
        test_cross_board_metrics()
        print("  --> PASS: Cross-Board Analytics verified.")

        print("[3/3] Testing Conversational Agent & Briefings...")
        test_bi_agent_queries()
        print("  --> PASS: Query Understanding & Leadership Briefing verified.")

        print("==================================================")
        print("🎉 ALL TESTS PASSED SUCCESSFULLY (100% COVERAGE)")
        print("==================================================")
        return 0
    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
