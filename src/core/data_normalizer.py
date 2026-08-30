"""
Data Normalization & Resilience Engine for Skylark Drones BI Agent.
Handles dirty real-world spreadsheets/Monday boards: mixed date formats, currency strings,
repeated headers, fuzzy sector/client mapping, drone work types, Spectra platform attach rates,
and produces data quality audit scores & caveats.
"""

import re
import math
import warnings
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import numpy as np


class DataQualityReport:
    def __init__(self):
        self.total_deals = 0
        self.clean_deals = 0
        self.total_work_orders = 0
        self.clean_work_orders = 0
        self.deals_missing_value_pct = 0.0
        self.deals_missing_date_pct = 0.0
        self.wo_missing_value_pct = 0.0
        self.wo_unlinked_pct = 0.0
        self.quality_score = 100.0
        self.caveats: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_deals": self.total_deals,
            "clean_deals": self.clean_deals,
            "total_work_orders": self.total_work_orders,
            "clean_work_orders": self.clean_work_orders,
            "deals_missing_value_pct": round(self.deals_missing_value_pct, 1),
            "deals_missing_date_pct": round(self.deals_missing_date_pct, 1),
            "wo_missing_value_pct": round(self.wo_missing_value_pct, 1),
            "wo_unlinked_pct": round(self.wo_unlinked_pct, 1),
            "quality_score": round(self.quality_score, 1),
            "caveats": self.caveats,
        }


class DataNormalizer:
    """Resilient cleaning and normalization engine."""

    SECTOR_MAPPING = {
        "renewables": "Renewables",
        "renewable": "Renewables",
        "solar": "Renewables",
        "energy": "Renewables",
        "green energy": "Renewables",
        "wind": "Renewables",
        "clean energy": "Renewables",
        "mining": "Mining",
        "mines": "Mining",
        "coal": "Mining",
        "iron ore": "Mining",
        "powerline": "Powerline",
        "power line": "Powerline",
        "power": "Powerline",
        "utilities": "Powerline",
        "transmission": "Powerline",
        "grid": "Powerline",
        "railways": "Railways",
        "railway": "Railways",
        "rail": "Railways",
        "construction": "Construction",
        "infra": "Construction",
        "infrastructure": "Construction",
        "highways": "Construction",
        "roads": "Construction",
        "dsp": "DSP",
        "tender": "Tender",
        "manufacturing": "Manufacturing",
        "security and surveillance": "Security and Surveillance",
        "security": "Security and Surveillance",
        "surveillance": "Security and Surveillance",
        "aviation": "Aviation",
        "others": "Others",
        "other": "Others",
    }

    STAGE_FUNNEL_ORDER = [
        "A. Lead Generated",
        "B. Sales Qualified Leads",
        "C. Demo Done",
        "D. Feasibility",
        "I. POC",
        "E. Proposal/Commercials Sent",
        "F. Negotiations",
        "G. Project Won",
        "H. Work Order Received",
        "J. Invoice sent",
        "K. Amount Accrued",
        "Project Completed",
        "L. Project Lost",
        "M. Projects On Hold",
        "N. Not relevant at the moment",
        "O. Not Relevant at all",
    ]

    @staticmethod
    def parse_numeric(val: Any) -> Optional[float]:
        """Parses numeric values from messy strings, floats, ints, currency symbols, lakhs/crores."""

        if val is None or (isinstance(val, float) and math.isnan(val)):
            return None

        if isinstance(val, (int, float)):
            return float(val)

        val_str = str(val).strip()

        if not val_str or val_str.lower() in (
            "nan",
            "none",
            "null",
            "-",
            "n/a",
            "",
        ):
            return None

        clean = re.sub(r"[₹$,\s]", "", val_str)

        lakh_match = re.search(
            r"([\d\.]+)\s*(?:lakh|lakhs|l)",
            clean,
            re.IGNORECASE,
        )

        if lakh_match:
            try:
                return float(lakh_match.group(1)) * 100000.0
            except ValueError:
                pass

        cr_match = re.search(
            r"([\d\.]+)\s*(?:cr|crore|crores)",
            clean,
            re.IGNORECASE,
        )

        if cr_match:
            try:
                return float(cr_match.group(1)) * 10000000.0
            except ValueError:
                pass

        try:
            return float(clean)
        except ValueError:
            match = re.search(r"[-+]?\d*\.?\d+", clean)

            if match:
                try:
                    return float(match.group())
                except ValueError:
                    return None

            return None

    @staticmethod
    def parse_date(val: Any) -> Optional[pd.Timestamp]:
        """Robustly parses date from mixed types."""

        if val is None or (isinstance(val, float) and math.isnan(val)):
            return None

        if isinstance(val, pd.Timestamp):
            return val

        if hasattr(val, "year") and hasattr(val, "month") and hasattr(val, "day"):
            try:
                return pd.Timestamp(val)
            except Exception:
                return None

        val_str = str(val).strip()

        if not val_str or val_str.lower() in (
            "nan",
            "none",
            "null",
            "-",
            "n/a",
            "created date",
            "close date (a)",
            "tentative close date",
            "date of po/loi",
        ):
            return None

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")

            try:
                res = pd.to_datetime(
                    val_str,
                    errors="coerce",
                    format="mixed",
                )

                if pd.notna(res):
                    return res

                return pd.to_datetime(
                    val_str,
                    errors="coerce",
                    dayfirst=True,
                )

            except Exception:
                return None

    @classmethod
    def normalize_sector(cls, sector_raw: Any) -> str:
        """Normalizes sector/vertical names."""

        if not sector_raw or pd.isna(sector_raw):
            return "Unassigned"

        s = str(sector_raw).strip().lower()

        if s in ("sector/service", "sector", "nan", "none", ""):
            return "Unassigned"

        return cls.SECTOR_MAPPING.get(
            s,
            str(sector_raw).strip().title(),
        )

    @classmethod
    def normalize_deal_status(
        cls,
        status_raw: Any,
        stage_raw: Any = None,
    ) -> str:
        """Normalizes deal status to Won, Open, Lost, or On Hold."""

        if not status_raw or pd.isna(status_raw):

            if stage_raw:
                stg = str(stage_raw).strip().lower()

                if any(
                    w in stg
                    for w in [
                        "won",
                        "work order received",
                        "invoice sent",
                        "completed",
                        "accrued",
                    ]
                ):
                    return "Won"

                if any(
                    l in stg
                    for l in [
                        "lost",
                        "not relevant",
                    ]
                ):
                    return "Lost"

                if "on hold" in stg:
                    return "On Hold"

            return "Open"

        s = str(status_raw).strip().lower()

        if s == "won":
            return "Won"

        if s in ("dead", "lost", "project lost"):
            return "Lost"

        if s in ("on hold", "hold"):
            return "On Hold"

        if s in ("open", "active", "in progress"):
            return "Open"

        return "Open"

    @classmethod
    def normalize_wo_status(cls, status_raw: Any) -> str:
        """Normalizes work order execution status."""

        if not status_raw or pd.isna(status_raw):
            return "Pending Triage"

        s = str(status_raw).strip()

        if s.lower() in ("completed", "done"):
            return "Completed"

        if s.lower() in ("ongoing", "in progress"):
            return "Ongoing"

        if s.lower() in (
            "executed until current month",
            "executed till date",
        ):
            return "Executed until current month"

        if s.lower() in ("not started", "unstarted"):
            return "Not Started"

        if any(
            p in s.lower()
            for p in [
                "pause",
                "struck",
                "pending from client",
                "blocked",
            ]
        ):
            return "Paused / Blocked"

        if "partial" in s.lower():
            return "Partial Completed"

        return s

    @classmethod
    def normalize_software_platform(cls, val: Any) -> str:
        """Normalizes Spectra SaaS platform attach rate."""

        if not val or pd.isna(val):
            return "None (Service Only)"

        s = str(val).strip().upper()

        if "SPECTRA" in s and "DMO" in s:
            return "Spectra + DMO"

        if "SPECTRA" in s:
            return "Spectra Platform"

        if "DMO" in s:
            return "DMO Platform"

        if s in ("NONE", "NO", "FALSE", "0"):
            return "None (Service Only)"

        return str(val).strip()

    @classmethod
    def clean_deals(
        cls,
        df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Cleans and standardizes the Deals dataframe."""

        caveats = []

        if df.empty:
            return df, ["Deals dataset is empty."]

        clean = df.copy()

        clean.columns = [
            str(c).strip()
            for c in clean.columns
        ]

        # IMPORTANT:
        # Monday.com returns the item name as "name".
        # Therefore both "Deal Name" and "name" are supported.
        col_map = {
            "Deal Name": "deal_name",
            "name": "deal_name",

            "Owner code": "owner_code",
            "Client Code": "client_code",
            "Deal Status": "deal_status",
            "Close Date (A)": "actual_close_date",
            "Closure Probability": "closure_probability",
            "Masked Deal value": "deal_value",
            "Tentative Close Date": "tentative_close_date",
            "Deal Stage": "deal_stage",
            "Product deal": "product_type",
            "Sector/service": "sector",
            "Created Date": "created_date",
        }

        for orig, target in col_map.items():

            for c in clean.columns:

                if (
                    c.lower() == orig.lower()
                    or c.lower().replace(" ", "_") == target
                ):
                    clean.rename(
                        columns={c: target},
                        inplace=True,
                    )
                    break

        # Safety fallback for Monday.com.
        # If Monday sends "name", make sure deal_name exists.
        if "deal_name" not in clean.columns and "name" in clean.columns:
            clean.rename(
                columns={"name": "deal_name"},
                inplace=True,
            )

        if "deal_name" in clean.columns:

            clean = clean[
                clean["deal_name"]
                .astype(str)
                .str.strip()
                .str.lower()
                != "deal name"
            ]

            clean = clean.dropna(
                subset=["deal_name"]
            )

            clean = clean[
                clean["deal_name"]
                .astype(str)
                .str.strip()
                != ""
            ]

        else:
            # Prevent downstream KeyError.
            clean["deal_name"] = "Unnamed Deal"

            caveats.append(
                "Deal name column was missing from deals board."
            )

        if "deal_value" in clean.columns:

            clean["deal_value"] = clean[
                "deal_value"
            ].apply(cls.parse_numeric)

            missing_val_cnt = clean[
                "deal_value"
            ].isna().sum()

            if missing_val_cnt > 0:

                pct = (
                    missing_val_cnt
                    / max(len(clean), 1)
                ) * 100

                caveats.append(
                    f"{missing_val_cnt} deals "
                    f"({pct:.1f}%) have unrecorded / "
                    f"missing deal values."
                )

        else:

            clean["deal_value"] = None

            caveats.append(
                "Deal value column missing from deals board."
            )

        for dcol in [
            "created_date",
            "actual_close_date",
            "tentative_close_date",
        ]:

            if dcol in clean.columns:
                clean[dcol] = clean[dcol].apply(
                    cls.parse_date
                )
            else:
                clean[dcol] = pd.NaT

        if "sector" in clean.columns:

            clean["sector"] = clean[
                "sector"
            ].apply(cls.normalize_sector)

        else:

            clean["sector"] = "Unassigned"

        if "deal_status" in clean.columns:

            stage_series = (
                clean["deal_stage"]
                if "deal_stage" in clean.columns
                else None
            )

            clean["deal_status"] = [
                cls.normalize_deal_status(
                    s,
                    stage,
                )
                for s, stage in zip(
                    clean["deal_status"],
                    (
                        stage_series
                        if stage_series is not None
                        else [None] * len(clean)
                    ),
                )
            ]

        else:

            clean["deal_status"] = "Open"

        if "closure_probability" in clean.columns:

            clean["closure_probability"] = (
                clean["closure_probability"]
                .astype(str)
                .str.strip()
                .replace(
                    {
                        "nan": None,
                        "None": None,
                    }
                )
            )

        else:

            clean["closure_probability"] = None

        if "product_type" in clean.columns:

            clean["product_type"] = (
                clean["product_type"]
                .astype(str)
                .str.strip()
                .replace(
                    {
                        "nan": "Unspecified",
                        "None": "Unspecified",
                    }
                )
            )

        else:

            clean["product_type"] = "Unspecified"

        clean["created_year"] = (
            clean["created_date"].dt.year
        )

        clean["created_quarter"] = clean[
            "created_date"
        ].apply(
            lambda d:
            f"Q{d.quarter} {d.year}"
            if pd.notna(d)
            else "Unknown"
        )

        clean["close_quarter"] = clean[
            "actual_close_date"
        ].apply(
            lambda d:
            f"Q{d.quarter} {d.year}"
            if pd.notna(d)
            else None
        )

        clean["tentative_quarter"] = clean[
            "tentative_close_date"
        ].apply(
            lambda d:
            f"Q{d.quarter} {d.year}"
            if pd.notna(d)
            else None
        )

        clean.reset_index(
            drop=True,
            inplace=True,
        )

        return clean, caveats

    @classmethod
    def clean_work_orders(
        cls,
        df: pd.DataFrame,
    ) -> Tuple[pd.DataFrame, List[str]]:
        """Cleans and standardizes the Work Orders dataframe."""

        caveats = []

        if df.empty:
            return df, ["Work Orders dataset is empty."]

        clean = df.copy()

        first_row = [
            str(x).strip().lower()
            for x in clean.iloc[0].values
        ]

        if any(
            "deal name" in x
            or "serial #" in x
            or "execution status" in x
            for x in first_row
        ):

            clean.columns = [
                str(x).strip()
                for x in clean.iloc[0].values
            ]

            clean = clean.iloc[1:].copy()

        clean.columns = [
            str(c).strip()
            for c in clean.columns
        ]

        # IMPORTANT:
        # Monday.com item names are returned as "name".
        col_map = {
            "Deal name masked": "deal_name",
            "name": "deal_name",

            "Customer Name Code": "client_code",
            "Serial #": "wo_serial_id",
            "Nature of Work": "nature_of_work",
            "Execution Status": "execution_status",
            "Data Delivery Date": "delivery_date",
            "Date of PO/LOI": "po_date",
            "Document Type": "document_type",
            "Probable Start Date": "start_date",
            "Probable End Date": "end_date",
            "BD/KAM Personnel code": "owner_code",
            "Sector": "sector",
            "Type of Work": "work_type",
            "Is any Skylark software platform part of the client deliverables in this deal?": "software_platform",
            "Amount in Rupees (Excl of GST) (Masked)": "amount_excl_gst",
            "Amount in Rupees (Incl of GST) (Masked)": "amount_incl_gst",
            "Billed Value in Rupees (Excl of GST.) (Masked)": "billed_excl_gst",
            "Billed Value in Rupees (Incl of GST.) (Masked)": "billed_incl_gst",
            "Collected Amount in Rupees (Incl of GST.) (Masked)": "collected_incl_gst",
            "Amount to be billed in Rs. (Exl. of GST) (Masked)": "unbilled_excl_gst",
            "Amount to be billed in Rs. (Incl. of GST) (Masked)": "unbilled_incl_gst",
            "Amount Receivable (Masked)": "receivable_amount",
            "Quantities as per PO": "quantities_po",
            "Billing Status": "billing_status",
            "WO Status (billed)": "wo_billed_status",
        }

        for orig, target in col_map.items():

            for c in clean.columns:

                if (
                    c.lower() == orig.lower()
                    or c.lower().replace(" ", "_") == target
                ):
                    clean.rename(
                        columns={c: target},
                        inplace=True,
                    )
                    break

        # Safety fallback for Monday.com.
        if "deal_name" not in clean.columns and "name" in clean.columns:

            clean.rename(
                columns={"name": "deal_name"},
                inplace=True,
            )

        if "deal_name" in clean.columns:

            clean = clean[
                clean["deal_name"]
                .astype(str)
                .str.strip()
                .str.lower()
                != "deal name masked"
            ]

            clean = clean.dropna(
                subset=["deal_name"]
            )

            clean = clean[
                clean["deal_name"]
                .astype(str)
                .str.strip()
                != ""
            ]

        else:

            clean["deal_name"] = "Unnamed Work Order"

            caveats.append(
                "Deal name column was missing from work orders board."
            )

        financial_cols = [
            "amount_excl_gst",
            "amount_incl_gst",
            "billed_excl_gst",
            "billed_incl_gst",
            "collected_incl_gst",
            "unbilled_excl_gst",
            "unbilled_incl_gst",
            "receivable_amount",
        ]

        for fcol in financial_cols:

            if fcol in clean.columns:
