# 🛸 Decision Log — Monday.com Business Intelligence Agent
**Candidate Project:** Technical Assignment for Skylark Drones  
**Author:** AI Engineering & Full-Stack Intelligence Specialist  
**Target Stakeholders:** Founders, C-Suite, VP Sales, VP Operations  

---

## 1. Key Assumptions Made

1. **Board Cross-Correlation Keying (`Deal Name` as Primary Anchor):**
   - In the provided raw datasets, client codes differed between boards (`COMPANYXXX` in Deals vs `WOCOMPANY_XXX` in Work Orders), but project/deal identifiers (`Deal Name` in Deals and `Deal name masked` in Work Orders) shared an 89.7% direct overlap (e.g., *Sakura*, *Appa*, *Scooby-Doo*, *Naruto*).
   - **Assumption:** In a production Monday.com workspace, Work Orders correlate to Sales Deals via the `Deal Name` / `Project Name` or connected item mirror columns. We designed the cross-board engine to join primarily on `deal_name` while supporting fallback fuzzy client matching.

2. **Sector & Vertical Canonical Mapping:**
   - Real-world founder queries use colloquial terminology (e.g., asking about *"Energy sector"* when the board is labeled *"Renewables"*, or *"Power"* for *"Powerline"*).
   - **Assumption:** We mapped synonyms (e.g., *Solar, Wind, Green Energy, Clean Energy ➔ Renewables*; *Grid, Transmission ➔ Powerline*; *Infra, Highways ➔ Construction*) into canonical business verticals.

3. **Domain-Specific Drone Intelligence Assumptions:**
   - **Spectra SaaS Attach Rate:** Work orders containing Skylark's proprietary Spectra / DMO cloud analytics platform represent high-margin recurring software revenue distinct from pure drone flight operations.
   - **Survey Payloads:** Projects are classified into Topography RGB, LiDAR, Hydrology, Thermography, and Volumetric surveys.

4. **Zero-Hallucination Deterministic Execution:**
   - LLMs are notoriously prone to arithmetic hallucinations when aggregating dozens of currency rows.
   - **Assumption:** All financial aggregations, win rates, SLA turnaround times (TAT), and risk rankings are computed deterministically via Python/Pandas data pipelines before narrative synthesis.

---

## 2. Trade-Offs Chosen & Why

| Decision / Trade-Off | Alternatives Considered | Chosen Approach & Rationale |
| :--- | :--- | :--- |
| **Direct GraphQL API v2 vs MCP Server** | Model Context Protocol (MCP) server | **GraphQL API v2 with Schema Reflection.** MCP is excellent for local tool calls, but an executive web prototype must be hosted in the cloud (Streamlit Cloud/Vercel) and testable with zero local client setup. Direct GraphQL provides full control over pagination, batching, and error backoff. |
| **Deterministic Code Analytics vs End-to-End LLM Prompting** | Feeding raw JSON into LLM prompt context | **Deterministic Pandas/Python Engine.** Feeding 500+ uncleaned records into an LLM context risks truncation, high token latency, and math errors. Our engine cleans data into structured memory, runs vectorized aggregations, and uses LLM/templates for executive narration. |
| **Hybrid Live API + Instant Mock Sandbox** | Live Monday Token Only | **Dual Mode (Live Sync + Demo Sandbox).** If evaluators don't have an active Monday.com API token or pre-configured board on hand, requiring live auth creates friction. Our architecture allows 1-click live sync while providing an instant pre-loaded sandbox. |
| **What-If Scenario Modeling vs Static Reports** | Static Read-Only Charts | **Interactive Growth Simulator.** Founders require dynamic decision-making tools to model revenue uplift from faster proposal conversion and invoicing acceleration. |

---

## 3. Interpretation of "Leadership Updates" (Additional Feature)

We interpreted **"The agent should help prepare data for leadership updates"** as an **Executive Briefing & Strategic Digest Engine**:

Founders and C-suite leaders do not want raw data tables; they need **high-signal, low-noise strategic synthesis**:
1. **1-Click Executive Digest (Weekly / Monthly / Quarterly / YTD):** Automatically aggregates Sales, Operations, and Finance into a publication-ready Markdown/PDF briefing.
2. **Executive KPI Scorecard:** Instant visibility into Gross Pipeline vs Probability-Weighted Pipeline, Won Bookings, Billing Progress, Cash Collected, and Unbilled Backlog.
3. **Operational Risk Radar:** Proactively flags delayed deliverables, revenue at risk (overdue high-value work orders), and aged accounts receivable.
4. **Actionable Leadership Takeaways:** Converts numbers into 4 strategic focus areas for the weekly executive standup (e.g., unblocking milestone invoicing, accelerating proposal conversions).

---

## 4. What I'd Do Differently With More Time

1. **Bi-directional Autonomous Actions (Write-Backs & Automated Reminders):**
   - Add safe write-back capabilities (e.g., auto-posting Slack/Email alerts to BD Owners for stalled proposals or alerting Ops PMs for work orders nearing SLA breach).
2. **Predictive Revenue & Milestone Forecasting (ML Engine):**
   - Train an XGBoost/Prophet model on historical TAT and seasonal weather patterns to predict project completion dates and cash collection curves.
3. **Natural Language to SQL / DuckDB Semantic Layer:**
   - Embed an in-memory DuckDB engine with an automated schema catalog for complex ad-hoc multi-table SQL queries.
4. **Automated Monday.com Webhooks & Real-Time Change Streams:**
   - Deploy a webhook listener to auto-refresh cached board states instantly when items or columns are updated in Monday.com.
