# 🛸 Skylark Drones — Monday.com Business Intelligence Agent

> **Executive AI Pair-Programmer & BI Agent** built for Skylark Drones founders and leadership to dynamically analyze, clean, and synthesize business insights across messy Monday.com boards (Sales Funnel Deals & Work Order Execution).

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit App](https://img.shields.io/badge/UI-Streamlit%201.30+-FF4B4B.svg)](https://streamlit.io/)
[![Monday.com API](https://img.shields.io/badge/Monday.com-GraphQL%20v2-6C63FF.svg)](https://developer.monday.com/api-reference/docs)
[![Tests](https://img.shields.io/badge/tests-100%25%20passing-brightgreen.svg)]()

---

## 📌 Problem & Executive Solution

Founders and C-suite executives at drone intelligence companies need fast, accurate answers to cross-functional business questions like *"How is our pipeline looking for energy sector this quarter?"* or *"Which delayed work orders pose the highest revenue risk?"*.

In practice, data is fragmented across multiple Monday.com boards with inconsistent date formats, currency strings (`₹`, `Lakhs`, `Cr`), missing deal values, and unlinked records.

**Antigravity BI** solves this end-to-end:
1. **Dynamic GraphQL Ingestion:** Connects securely to Monday.com API v2 with pagination and rate-limit recovery (Zero hardcoding).
2. **Resilient Data Normalization:** Automatically cleans mixed dates, parses messy currencies, maps fuzzy vertical synonyms, and computes a **Data Quality Score (72.1/100)** with transparency caveats.
3. **Deterministic Math Execution:** Computes financial metrics in Python/Pandas to eliminate LLM arithmetic hallucinations.
4. **Conversational BI Interface:** Understands founder queries, clarifies ambiguity, and generates interactive Plotly visualizations.
5. **1-Click Leadership Update Generator:** Prepares weekly, monthly, and quarterly executive briefing reports with KPIs, sector matrices, SLA health, and action items.

---

## 🏛️ System Architecture

```
                               ┌────────────────────────┐
                               │   Founder / Executive  │
                               │  (Streamlit Web App)   │
                               └───────────┬────────────┘
                                           │ Natural Language Query
                                           ▼
                             ┌───────────────────────────┐
                             │  Conversational BI Agent  │
                             │  (Intent & Ambiguity NLP) │
                             └─────────────┬─────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    │                                             │
                    ▼                                             ▼
       ┌─────────────────────────┐                   ┌─────────────────────────┐
       │ Deterministic Analytics │                   │ Leadership Update Engine│
       │    (Python / Pandas)    │                   │   (1-Click Executive    │
       │  (Zero Math Hallucina)  │                   │    Digest Generator)    │
       └────────────┬────────────┘                   └────────────┬────────────┘
                    │                                             │
                    └──────────────────────┬──────────────────────┘
                                           │
                                           ▼
                             ┌───────────────────────────┐
                             │  Data Resilience Engine   │
                             │ - Mixed Date Normalizer   │
                             │ - Currency & Lakh/Cr Clean│
                             │ - Fuzzy Sector Taxonomy   │
                             │ - Quality Score & Caveats │
                             └─────────────┬─────────────┘
                                           │
                                           ▼
                             ┌───────────────────────────┐
                             │ Monday.com Dynamic Client │
                             │ - GraphQL v2 API Client   │
                             │ - Cursor Pagination       │
                             │ - Live Sync + Sandbox     │
                             └─────────────┬─────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    ▼                                             ▼
          [Monday Deals Board]                         [Monday Work Orders Board]
          (Sales Funnel Pipeline)                      (Project Execution Tracker)
```

---

## 🚀 Quickstart & Local Setup

### 1. Clone & Install Dependencies
```bash
git clone https://github.com/your-repo/skylark-bi-agent.git
cd skylark-bi-agent

# Create and activate virtual environment
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
Create a `.env` file from the example:
```bash
cp .env.example .env
```
Fill in your credentials if using a live Monday.com workspace or Gemini API:
```env
MONDAY_API_KEY=your_monday_personal_access_token
MONDAY_DEALS_BOARD_ID=1827364521
MONDAY_WO_BOARD_ID=1827364522
GEMINI_API_KEY=your_optional_gemini_key
```

### 3. Launch the Web Application
```bash
streamlit run src/ui/app.py
```
Open `http://localhost:8501` in your browser.

---

## 🔌 Monday.com Board Configuration Guide

To import the Skylark datasets into your live Monday.com workspace:

### Board 1: Deals Funnel (Sales Pipeline)
- Import `data/deals_raw.xlsx` or create a board named **"Skylark - Deal Funnel"**.
- Recommended Column Mappings:
  - `Deal Name` ➔ **Name** (Item Name)
  - `Owner code` ➔ **People / Text**
  - `Client Code` ➔ **Text**
  - `Deal Status` ➔ **Status** (`Won`, `Open`, `Dead`, `On Hold`)
  - `Deal Stage` ➔ **Dropdown / Status** (`A. Lead Generated`, `B. SQL`, `E. Proposal Sent`, `G. Project Won`, etc.)
  - `Masked Deal value` ➔ **Numbers** (Currency)
  - `Sector/service` ➔ **Dropdown** (`Renewables`, `Mining`, `Powerline`, `Railways`, `Construction`)
  - `Closure Probability` ➔ **Status** (`High`, `Medium`, `Low`)
  - `Created Date` ➔ **Date**
  - `Close Date (A)` ➔ **Date**

### Board 2: Work Order Tracker (Execution)
- Import `data/work_orders_raw.xlsx` or create a board named **"Skylark - Work Order Tracker"**.
- Recommended Column Mappings:
  - `Deal name masked` ➔ **Name** (Matches Deal Name)
  - `Serial #` ➔ **Text** (`SDPLDEAL-XXX`)
  - `Customer Name Code` ➔ **Text**
  - `Execution Status` ➔ **Status** (`Completed`, `Ongoing`, `Executed until current month`, `Not Started`, `Paused`)
  - `Sector` ➔ **Dropdown**
  - `Amount in Rupees (Excl of GST)` ➔ **Numbers**
  - `Billed Value in Rupees` ➔ **Numbers**
  - `Collected Amount in Rupees` ➔ **Numbers**
  - `Date of PO/LOI` ➔ **Date**
  - `Probable Start Date` ➔ **Date**
  - `Probable End Date` ➔ **Date**
  - `Data Delivery Date` ➔ **Date**

---

## 🌐 1-Click Cloud Deployment (Hosted Prototype)

This application is fully compatible with **Streamlit Community Cloud**, **Vercel**, **Railway**, and **Hugging Face Spaces**:

### Deploying on Streamlit Community Cloud:
1. Push this repository to GitHub.
2. Visit [share.streamlit.io](https://share.streamlit.io) and log in.
3. Click **"New app"**, select your repository, branch `main`, and main file path `src/ui/app.py`.
4. (Optional) Add `MONDAY_API_KEY` under **Advanced Settings ➔ Secrets**.
5. Click **"Deploy"**! Your hosted prototype will be live in 60 seconds with zero local setup needed.

---

## 🧪 Verification & Automated Test Suite

Run the full unit and integration test suite:
```bash
python -m pytest tests/ -v
# Or run with the built-in test runner:
python scripts/run_tests.py
```

### Test Coverage Summary:
- `test_normalizer.py`: Tests date parsers, currency formats (₹, Lakhs, Cr), sector taxonomies, duplicate header purging, and quality score computation.
- `test_cross_board.py`: Tests cross-board lifecycle joins, pipeline value vs won bookings, unbilled backlog, and SLA delay detection.
- `test_agent.py`: Tests conversational query routing, sector deep-dives, revenue reconciliation, ambiguity detection, and executive briefing markdown generation.

---

## 💡 Example Founder Queries & Expected Insights

| Founder Query | Agent Interpretation & Output |
| :--- | :--- |
| **"How's our pipeline looking for energy sector this quarter?"** | Maps *Energy* ➔ **Renewables**. Reports 111 total deals, ₹68.8M active pipeline, 51 Work Orders, 34.2-day average TAT, and caveats regarding unrecorded deal values. |
| **"Which work orders are delayed and what revenue is at risk?"** | Filters Work Orders where `delivery_date > end_date`. Identifies 25 delayed projects, lists top 5 high-value delayed orders with BD owners, and calculates total revenue at risk. |
| **"What is our win rate across Mining vs Renewables?"** | Computes exact mathematical closed-won conversion rates across verticals and highlights proposal-stage drop-off patterns. |
| **"Prepare a leadership update for weekly founder sync."** | Generates a complete 1-click executive briefing document with Scorecard, Highlights, Lowlights, Risk Radar, and Strategic Action Items. |
