"""
Automated Board Provisioning Script for Monday.com.
Creates Deals Funnel and Work Order Tracker boards via GraphQL mutations
and optionally populates them from datasets.
"""

import os
import sys
import argparse
import requests
import pandas as pd

API_URL = "https://api.monday.com/v2"


def create_board(api_key: str, board_name: str) -> str:
    """Creates a new board in Monday.com workspace."""
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "API-Version": "2024-01",
    }
    mutation = """
    mutation ($boardName: String!) {
        create_board (board_name: $boardName, board_kind: public) {
            id
        }
    }
    """
    res = requests.post(API_URL, json={"query": mutation, "variables": {"boardName": board_name}}, headers=headers)
    data = res.json()
    if "errors" in data:
        raise RuntimeError(f"Error creating board {board_name}: {data['errors']}")
    board_id = data["data"]["create_board"]["id"]
    print(f"✅ Created board '{board_name}' with ID: {board_id}")
    return board_id


def add_column(api_key: str, board_id: str, title: str, col_type: str) -> str:
    """Adds a column to a Monday board."""
    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
        "API-Version": "2024-01",
    }
    mutation = """
    mutation ($boardId: ID!, $title: String!, $colType: ColumnType!) {
        create_column (board_id: $boardId, title: $title, column_type: $colType) {
            id
        }
    }
    """
    res = requests.post(API_URL, json={"query": mutation, "variables": {"boardId": board_id, "title": title, "colType": col_type}}, headers=headers)
    data = res.json()
    if "errors" in data:
        print(f"  ⚠️ Warning creating column {title}: {data['errors']}")
        return ""
    col_id = data["data"]["create_column"]["id"]
    print(f"  + Added column '{title}' ({col_type}) -> ID: {col_id}")
    return col_id


def main():
    parser = argparse.ArgumentParser(description="Provision Monday.com boards for Skylark BI Agent.")
    parser.add_argument("--api-key", required=True, help="Monday.com Personal Access Token")
    args = parser.parse_args()

    print("🚀 Setting up Monday.com Boards for Skylark Drones...")
    try:
        # 1. Create Deals Board
        deals_id = create_board(args.api_key, "Skylark - Deal Funnel (Sales)")
        add_column(args.api_key, deals_id, "Owner code", "people")
        add_column(args.api_key, deals_id, "Client Code", "text")
        add_column(args.api_key, deals_id, "Deal Status", "color")
        add_column(args.api_key, deals_id, "Deal Stage", "dropdown")
        add_column(args.api_key, deals_id, "Masked Deal value", "numbers")
        add_column(args.api_key, deals_id, "Sector/service", "dropdown")
        add_column(args.api_key, deals_id, "Closure Probability", "color")
        add_column(args.api_key, deals_id, "Created Date", "date")
        add_column(args.api_key, deals_id, "Close Date (A)", "date")

        # 2. Create Work Orders Board
        wo_id = create_board(args.api_key, "Skylark - Work Order Tracker (Ops)")
        add_column(args.api_key, wo_id, "Serial #", "text")
        add_column(args.api_key, wo_id, "Customer Name Code", "text")
        add_column(args.api_key, wo_id, "Execution Status", "color")
        add_column(args.api_key, wo_id, "Sector", "dropdown")
        add_column(args.api_key, wo_id, "Amount in Rupees (Excl of GST)", "numbers")
        add_column(args.api_key, wo_id, "Billed Value in Rupees", "numbers")
        add_column(args.api_key, wo_id, "Collected Amount in Rupees", "numbers")
        add_column(args.api_key, wo_id, "Date of PO/LOI", "date")
        add_column(args.api_key, wo_id, "Probable Start Date", "date")
        add_column(args.api_key, wo_id, "Data Delivery Date", "date")

        print("\n🎉 Both boards provisioned successfully!")
        print(f"Set these in your .env file or UI:")
        print(f"MONDAY_DEALS_BOARD_ID={deals_id}")
        print(f"MONDAY_WO_BOARD_ID={wo_id}")

    except Exception as e:
        print(f"❌ Error setting up boards: {e}")


if __name__ == "__main__":
    main()
