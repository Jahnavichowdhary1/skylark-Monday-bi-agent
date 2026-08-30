"""
Monday.com GraphQL API v2 Client for dynamic board and item querying.
Strictly Read-Only, supporting pagination, schema introspection, rate-limit recovery,
and column value decoding.
"""

import time
import logging
from typing import Any, Dict, List, Optional, Tuple
import requests
import pandas as pd

logger = logging.getLogger(__name__)


class MondayAPIError(Exception):
    """Custom exception for Monday.com API errors."""
    pass


class MondayClient:
    """Client for querying Monday.com GraphQL v2 API dynamically."""

    API_URL = "https://api.monday.com/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or ""
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
            "API-Version": "2024-01",
        }

    def is_configured(self) -> bool:
        """Checks if API key is provided."""
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    def execute_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Executes a GraphQL query against Monday.com with retry on rate limits."""
        if not self.is_configured():
            raise MondayAPIError("Monday.com API key is not configured.")

        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        max_retries = 3
        backoff = 1.0

        for attempt in range(max_retries):
            try:
                response = requests.post(
                    self.API_URL,
                    json=payload,
                    headers=self.headers,
                    timeout=25,
                )

                if response.status_code == 429:
                    # Rate limit hit
                    time.sleep(backoff)
                    backoff *= 2
                    continue

                if response.status_code != 200:
                    raise MondayAPIError(
                        f"Monday.com API returned HTTP {response.status_code}: {response.text}"
                    )

                data = response.json()
                if "errors" in data and data["errors"]:
                    error_msg = "; ".join([e.get("message", "Unknown error") for e in data["errors"]])
                    raise MondayAPIError(f"GraphQL Errors: {error_msg}")

                return data.get("data", {})

            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise MondayAPIError(f"Network error communicating with Monday.com: {e}")
                time.sleep(backoff)
                backoff *= 2

        raise MondayAPIError("Max retries exceeded while calling Monday.com API.")

    def test_connection(self) -> Tuple[bool, str]:
        """Tests connection to Monday.com API."""
        if not self.is_configured():
            return False, "API key is missing."
        try:
            query = """
            query {
                me {
                    id
                    name
                    email
                }
            }
            """
            res = self.execute_query(query)
            me = res.get("me", {})
            user_name = me.get("name", "Unknown User")
            return True, f"Connected successfully as {user_name} ({me.get('email', '')})"
        except Exception as e:
            return False, f"Connection failed: {str(e)}"

    def list_boards(self) -> List[Dict[str, Any]]:
        """Lists available boards in workspace."""
        query = """
        query {
            boards(limit: 50) {
                id
                name
                state
                board_kind
                columns {
                    id
                    title
                    type
                }
            }
        }
        """
        res = self.execute_query(query)
        return res.get("boards", [])

    def fetch_board_items(self, board_id: str) -> pd.DataFrame:
        """Dynamically fetches all items and column values from a board with pagination."""
        query = """
        query ($boardId: [ID!], $cursor: String) {
            boards(ids: $boardId) {
                id
                name
                columns {
                    id
                    title
                    type
                }
                items_page(limit: 500, cursor: $cursor) {
                    cursor
                    items {
                        id
                        name
                        created_at
                        updated_at
                        column_values {
                            id
                            text
                            value
                            type
                        }
                    }
                }
            }
        }
        """
        all_rows = []
        cursor = None
        columns_map = {}

        while True:
            vars = {"boardId": [str(board_id)]}
            if cursor:
                vars["cursor"] = cursor

            res = self.execute_query(query, vars)
            boards = res.get("boards", [])
            if not boards:
                break

            board = boards[0]
            if not columns_map:
                for col in board.get("columns", []):
                    columns_map[col["id"]] = col["title"]

            items_page = board.get("items_page", {})
            items = items_page.get("items", [])

            for item in items:
                row = {
                    "item_id": item.get("id"),
                    "name": item.get("name"),
                    "created_at": item.get("created_at"),
                }
                for cv in item.get("column_values", []):
                    col_title = columns_map.get(cv["id"], cv["id"])
                    row[col_title] = cv.get("text")
                all_rows.append(row)

            cursor = items_page.get("cursor")
            if not cursor or len(items) == 0:
                break

        return pd.DataFrame(all_rows)
