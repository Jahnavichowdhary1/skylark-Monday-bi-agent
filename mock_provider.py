"""
Mock Monday Provider simulating live Monday.com GraphQL API responses
for offline evaluation, testing, and zero-friction demonstrations.
"""

import os
import logging
from typing import Any, Dict, List, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class MockMondayProvider:
    """Simulates dynamic Monday.com GraphQL API data fetching from raw datasets."""

    def __init__(self, data_dir: Optional[str] = None):
        if not data_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            data_dir = os.path.join(base_dir, "data")
        self.data_dir = data_dir
        self.deals_file = os.path.join(data_dir, "deals_raw.xlsx")
        self.wo_file = os.path.join(data_dir, "work_orders_raw.xlsx")

    def list_boards(self) -> List[Dict[str, Any]]:
        """Returns mock Monday boards."""
        return [
            {
                "id": "1001",
                "name": "Skylark - Deal Funnel (Sales Pipeline)",
                "state": "active",
                "board_kind": "public",
                "columns": [
                    {"id": "name", "title": "Deal Name", "type": "name"},
                    {"id": "owner", "title": "Owner code", "type": "people"},
                    {"id": "client", "title": "Client Code", "type": "text"},
                    {"id": "status", "title": "Deal Status", "type": "color"},
                    {"id": "stage", "title": "Deal Stage", "type": "dropdown"},
                    {"id": "value", "title": "Masked Deal value", "type": "numbers"},
                    {"id": "sector", "title": "Sector/service", "type": "dropdown"},
                    {"id": "prob", "title": "Closure Probability", "type": "color"},
                    {"id": "created", "title": "Created Date", "type": "date"},
                    {"id": "tentative_date", "title": "Tentative Close Date", "type": "date"},
                    {"id": "close_date", "title": "Close Date (A)", "type": "date"},
                    {"id": "product", "title": "Product deal", "type": "dropdown"},
                ],
            },
            {
                "id": "1002",
                "name": "Skylark - Work Order Tracker (Execution)",
                "state": "active",
                "board_kind": "public",
                "columns": [
                    {"id": "name", "title": "Deal name masked", "type": "name"},
                    {"id": "serial", "title": "Serial #", "type": "text"},
                    {"id": "client", "title": "Customer Name Code", "type": "text"},
                    {"id": "exec_status", "title": "Execution Status", "type": "color"},
                    {"id": "sector", "title": "Sector", "type": "dropdown"},
                    {"id": "nature", "title": "Nature of Work", "type": "dropdown"},
                    {"id": "amount_excl", "title": "Amount in Rupees (Excl of GST) (Masked)", "type": "numbers"},
                    {"id": "billed_excl", "title": "Billed Value in Rupees (Excl of GST.) (Masked)", "type": "numbers"},
                    {"id": "collected", "title": "Collected Amount in Rupees (Incl of GST.) (Masked)", "type": "numbers"},
                    {"id": "po_date", "title": "Date of PO/LOI", "type": "date"},
                    {"id": "start_date", "title": "Probable Start Date", "type": "date"},
                    {"id": "end_date", "title": "Probable End Date", "type": "date"},
                    {"id": "delivery_date", "title": "Data Delivery Date", "type": "date"},
                    {"id": "billing_status", "title": "Billing Status", "type": "color"},
                ],
            },
        ]

    def fetch_board_items(self, board_id: str) -> pd.DataFrame:
        """Dynamically simulates fetching items from Monday board."""
        board_id_str = str(board_id).lower()
        if "1001" in board_id_str or "deal" in board_id_str:
            if os.path.exists(self.deals_file):
                return pd.read_excel(self.deals_file)
            else:
                raise FileNotFoundError(f"Deals data file not found at {self.deals_file}")
        elif "1002" in board_id_str or "work" in board_id_str or "order" in board_id_str or "wo" in board_id_str:
            if os.path.exists(self.wo_file):
                return pd.read_excel(self.wo_file)
            else:
                raise FileNotFoundError(f"Work Orders data file not found at {self.wo_file}")
        else:
            raise ValueError(f"Unknown board ID: {board_id}")
