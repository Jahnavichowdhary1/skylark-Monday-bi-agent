"""
Unit tests for DataNormalizer and DataQualityReport.
"""

import math
import pandas as pd
import numpy as np
from src.core.data_normalizer import DataNormalizer, DataQualityReport


def test_parse_numeric():
    # Regular floats and ints
    assert DataNormalizer.parse_numeric(100) == 100.0
    assert DataNormalizer.parse_numeric(25000.50) == 25000.50

    # Currency strings
    assert DataNormalizer.parse_numeric("₹ 1,54,150") == 154150.0
    assert DataNormalizer.parse_numeric("$2,64,398.08") == 264398.08

    # Lakhs and Crores
    assert DataNormalizer.parse_numeric("2.5 Lakhs") == 250000.0
    assert DataNormalizer.parse_numeric("1.2 Cr") == 12000000.0

    # None and invalid
    assert DataNormalizer.parse_numeric(None) is None
    assert DataNormalizer.parse_numeric("NaN") is None
    assert DataNormalizer.parse_numeric("-") is None


def test_parse_date():
    d1 = DataNormalizer.parse_date("2025-12-26")
    assert d1.year == 2025 and d1.month == 12 and d1.day == 26

    # Indian format DD/MM/YYYY
    d2 = DataNormalizer.parse_date("26/12/2025")
    assert d2.year == 2025 and d2.month == 12 and d2.day == 26

    # Header repeats or invalid
    assert DataNormalizer.parse_date("Created Date") is None
    assert DataNormalizer.parse_date("None") is None


def test_normalize_sector():
    assert DataNormalizer.normalize_sector("solar") == "Renewables"
    assert DataNormalizer.normalize_sector("Renewables") == "Renewables"
    assert DataNormalizer.normalize_sector("powerline") == "Powerline"
    assert DataNormalizer.normalize_sector("mining") == "Mining"
    assert DataNormalizer.normalize_sector("railways") == "Railways"
    assert DataNormalizer.normalize_sector("construction") == "Construction"
    assert DataNormalizer.normalize_sector(None) == "Unassigned"


def test_normalize_deal_status():
    assert DataNormalizer.normalize_deal_status("Won") == "Won"
    assert DataNormalizer.normalize_deal_status("Dead") == "Lost"
    assert DataNormalizer.normalize_deal_status("On Hold") == "On Hold"
    assert DataNormalizer.normalize_deal_status("Open") == "Open"
    assert DataNormalizer.normalize_deal_status(None, "G. Project Won") == "Won"


def test_clean_deals_and_wo():
    dummy_deals = pd.DataFrame([
        {"Deal Name": "Deal Name", "Masked Deal value": "Masked Deal value"},  # Header repeat
        {"Deal Name": "Deal Alpha", "Owner code": "OWNER_001", "Deal Status": "Won", "Masked Deal value": "₹ 5,00,000", "Sector/service": "solar"},
        {"Deal Name": "Deal Beta", "Owner code": "OWNER_002", "Deal Status": "Open", "Masked Deal value": "2.5 Lakhs", "Sector/service": "mining"},
    ])

    clean_deals, caveats = DataNormalizer.clean_deals(dummy_deals)
    assert len(clean_deals) == 2
    assert clean_deals.iloc[0]["deal_value"] == 500000.0
    assert clean_deals.iloc[0]["sector"] == "Renewables"
    assert clean_deals.iloc[1]["deal_value"] == 250000.0
    assert clean_deals.iloc[1]["sector"] == "Mining"
