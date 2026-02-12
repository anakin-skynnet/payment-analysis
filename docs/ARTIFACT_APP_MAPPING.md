# Artifact & Databricks Resource → App Usage Mapping

Every artifact and Databricks resource in this solution is used in the app to deliver business value for **accelerating approval rates**. This document maps each resource to where it appears (interactive or presentational).

---

## Summary

| Category | Resources | Used in app |
|----------|-----------|-------------|
| **Streaming & real-time** | Bronze ingest, Silver transform, Gold views, Real-time pipeline, Job 2 (simulator) | Data & Quality page, Command Center KPIs, Dashboards, Recommendations |
| **ML models & inference** | Approval propensity, Risk scoring, Smart routing, Smart retry | Decisioning: policy decisions + **Live ML predictions** card; Models page (registry) |
| **Agents** | Orchestrator, Decline analyst, Smart routing/retry/risk/performance agents | AI Agents page; Orchestrator chat (recommendations, analysis); Genie |
| **Dashboards** | Data & Quality, ML & Optimization, Executive & Trends | Dashboards page (list, embed, open in workspace) |
| **Vector Search** | Similar-case index | Recommendations (Decisioning page) via `v_recommendations_from_lakehouse` |
| **Lakebase / Lakehouse** | Rules, recommendations, online features, app_config | Rules page, Decisioning (recommendations), analytics, control panel |

---

## 1. Streaming & real-time analysis

| Artifact | Purpose | App usage |
|----------|---------|-----------|
| **Bronze ingest** (Pipeline 8) | Ingest raw events | Feeds silver/gold; KPIs and trends in app come from gold views |
| **Silver transform** (Pipeline 8) | Enrich and clean | `payments_enriched_silver` and gold views used by analytics API |
| **Gold views** (Job 3, Pipeline 8) | KPIs, trends, geography, declines, retry, data quality | **Analytics API**: KPIs, approval trends, solution performance, reason codes, last-hour/60s performance, streaming TPS, data quality summary, active alerts, retry performance. **UI**: Command Center, Initiatives, Data Quality (Monitoring), Dashboards (underlying data) |
| **Real-time pipeline** (Pipeline 9) | Dedicated real-time stream | Feeds real-time views used by analytics (e.g. `getLast60SecondsPerformance`, `getStreamingTps`) |
| **Job 2 (Simulate transaction events)** | Produce sample events | Populates bronze so pipelines and jobs 3–7 have data; value is indirect (enables all downstream analytics and models) |

**UI pages**: Command Center (KPIs, TPS), **Data Quality** (streaming TPS, last hour, last 60s, data quality summary, incidents), Initiatives (KPIs), Dashboards (all three unified dashboards query gold/silver).

---

## 2. ML models & real-time inference

| Model / endpoint | Purpose | App usage |
|------------------|---------|-----------|
| **Approval propensity** | Approval probability and should_approve | **Decisioning** → **Live ML predictions** card; `POST /api/decision/ml/approval` |
| **Risk scoring** | Risk score, tier, is_high_risk | **Decisioning** → **Live ML predictions** card; `POST /api/decision/ml/risk` |
| **Smart routing** | Recommended solution, confidence, alternatives | **Decisioning** → **Live ML predictions** card; `POST /api/decision/ml/routing` |
| **Smart retry** | Retry success likelihood, should_retry | **Decisioning** → **Live ML predictions** card; `POST /api/decision/ml/retry` |
| **Decline analyst** (agent) | Decline analysis and recovery recommendations | Used by **Orchestrator chat** (Job 6 or Model Serving); AI Agents page lists it |

**UI**: **Decisioning** page has (1) policy-based decisions (authentication, retry, routing) and (2) **Live ML predictions** card: “Run all ML predictions” runs all four model endpoints and shows approval propensity, risk score, smart routing, and smart retry. **Models** page lists all four models (from UC/MLflow) and links to Decisioning and training notebooks.

---

## 3. Dashboards

| Dashboard | Content | App usage |
|-----------|---------|-----------|
| **Data & Quality** | Stream ingestion, data quality, real-time monitoring, alerts, geography | **Dashboards** page: list, open in workspace, optional embed |
| **ML & Optimization** | Routing, decline/recovery, fraud/risk, 3DS, financial impact | **Dashboards** page |
| **Executive & Trends** | KPIs, approval rates, trends, merchant performance | **Dashboards** page; Command Center overview |

**UI**: **Dashboards** page lists all three, opens them in Databricks, and can embed by ID. Dashboard data is backed by the same gold views and pipelines above.

---

## 4. Agents

| Agent | Purpose | App usage |
|-------|---------|-----------|
| **Orchestrator** (Job 6 or Model Serving) | Coordinates specialists; synthesis and recommendations | **AI Agents** page; **Orchestrator chat** (recommendations, payment analysis) in Command Center / layout |
| **Decline analyst** | Decline patterns, root causes, recovery | Invoked by orchestrator; listed on AI Agents page |
| **Smart routing / Smart retry / Risk assessor / Performance recommender** | Routing, retry, risk, optimization | Invoked by orchestrator; listed on AI Agents page |
| **Genie** (optional) | Q&A over workspace data | **AI Agents** page (Genie link); **Genie assistant** component when configured |

**UI**: **AI Agents** page lists all agents and types; **Orchestrator chat** sends messages to `POST /api/agents/orchestrator/chat` (endpoint or Job 6) and shows reply and agents used.

---

## 5. Vector Search & recommendations

| Resource | Purpose | App usage |
|----------|---------|-----------|
| **Vector Search index** | Similar transactions for recommendations | Feeds Lakehouse `approval_recommendations` / `v_recommendations_from_lakehouse` |
| **v_recommendations_from_lakehouse** | Similar-case and rule-based recommendations | **Decisioning** page → “Similar cases & recommendations” card via `GET /api/analytics/recommendations` |

**UI**: **Decisioning** shows recommendations that combine Vector Search–backed similar cases and rules to suggest actions that accelerate approval rates.

---

## 6. Lakebase / Lakehouse (rules, config, features)

| Resource | Purpose | App usage |
|----------|---------|-----------|
| **approval_rules, online_features, app_config, app_settings** | Rules and app configuration | **Rules** page (CRUD); **Decisioning** and analytics use rules and features; **Setup** references them |
| **Lakebase Autoscaling** | Hosted Postgres for app DB and rules | Health check `GET /api/v1/health/database`; app uses it for rules, experiments, incidents, decision log |

**UI**: **Rules** page, **Setup** (control panel), **Decisioning** (recommendations and context), **Experiments** (A/B), **Incidents** (alerts).

---

## 7. Jobs & pipelines (execution)

| Job / pipeline | Purpose | App usage |
|----------------|--------|-----------|
| **Job 1** – Create data repositories | Catalog, schema, Lakebase, lakehouse, vector search | **Setup** → Run job; enables all data and models |
| **Job 2** – Simulate events | Produce bronze events | **Setup** → Run job |
| **Job 3** – Initialize ingestion | Gold views, UC agent tools, etc. | **Setup** → Run job |
| **Job 4** – Deploy dashboards | Prepare & publish dashboards | **Setup** → Run job |
| **Job 5** – Train models | Train and register ML models | **Setup** → Run job; **Models** page links to training |
| **Job 6** – Deploy agents | Run agent framework + register AgentBricks | **Setup** → Run job; **Orchestrator chat** uses it when no serving endpoint |
| **Job 7** – Genie sync | Sync Genie space, sample questions | **Setup** → Run job; **Genie** in app |
| **Pipeline 8** – ETL | Bronze → Silver → Gold | **Setup** → Run pipeline; feeds all analytics and dashboards |
| **Pipeline 9** – Real-time | Real-time stream | **Setup** → Run pipeline; feeds real-time analytics |

**UI**: **Setup** page lists all steps, Run/Open for each job and pipeline. All built artifacts above depend on these runs.

---

## Changes made to ensure full coverage

1. **Smart retry model in app**  
   - Backend: `call_retry_model` in `DatabricksService`, `RetryPredictionOut`, and `POST /api/decision/ml/retry` (`predictRetry`).  
   - Frontend: `predictRetry` / `usePredictRetry` in `api.ts`, and **Live ML predictions** card on Decisioning page now includes **Smart retry** (should_retry, retry_success_probability).

2. **Live ML predictions on Decisioning**  
   - New card “Live ML predictions (Model Serving)” on **Decisioning** page: single button runs approval propensity, risk, routing, and retry with the same context and displays results. This ties all four Model Serving endpoints to approval-rate value in the UI.

3. **Documentation**  
   - This mapping doc: every artifact (streaming, models, agents, dashboards, vector search, Lakebase, jobs/pipelines) is linked to specific app surfaces (pages, APIs, chat).

---

## Quick reference: where to find what

- **Real-time / streaming** → Data Quality page, Command Center KPIs, Dashboards.
- **Predictions / scoring / propensity** → Decisioning page (policy decisions + **Live ML predictions** card), Models page (registry).
- **Recommendations** → Decisioning page (“Similar cases & recommendations” + rules).
- **Dashboards** → Dashboards page (list, open, embed).
- **Agents & chat** → AI Agents page, Orchestrator chat in layout.
- **Rules & config** → Rules page, Setup (control panel).

Everything built here is used in the app to accelerate approval rates.
