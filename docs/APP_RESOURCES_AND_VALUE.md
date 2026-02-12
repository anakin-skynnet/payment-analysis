# App Resources, Model Serving, UC Functions — Creation & Business Value

This document lists **service endpoints**, **model serving**, and **Unity Catalog (UC) functions** used by the Payment Analysis app, how they are created, how to validate them, and the business value they provide for **approval rate optimization** and **payment analysis**.

## 1. Model serving endpoints (5)

| App resource name   | Endpoint name (dev)           | Created by                    | Purpose |
|---------------------|------------------------------|-------------------------------|--------|
| serving-decline-analyst | `decline-analyst-dev`       | `resources/model_serving.yml` | Decline analyst agent (LangGraph); register as `catalog.schema.decline_analyst` (e.g. via agentbricks). |
| serving-approval-prop | `approval-propensity-dev`     | `resources/model_serving.yml` | Predicts transaction approval probability; used by Decisioning and Command Center. |
| serving-risk-scoring | `risk-scoring-dev`            | `resources/model_serving.yml` | Fraud risk scoring with PII guardrails; risk-based auth and step-up. |
| serving-smart-routing | `smart-routing-dev`           | `resources/model_serving.yml` | Optimal payment route (standard, 3DS, token, passkey) to maximize approval. |
| serving-smart-retry   | `smart-retry-dev`             | `resources/model_serving.yml` | Retry success likelihood and recovery timing. |

**Creation**

1. Run **Step 5 (Train Payment Approval ML Models)** so these models exist in Unity Catalog: `approval_propensity_model`, `risk_scoring_model`, `smart_routing_policy`, `smart_retry_policy`. Register **decline_analyst** (LangGraph agent) in the same catalog/schema if you use that endpoint (e.g. via `agentbricks_register` or LangGraph + MLflow).
2. In `databricks.yml`, uncomment: `- resources/model_serving.yml`.
3. Redeploy: `./scripts/bundle.sh deploy dev`.

The bundle then creates the five endpoints. App resources in `resources/fastapi_app.yml` grant the app **CAN_QUERY** on them. If any endpoint does not exist yet (e.g. decline_analyst not registered), comment out the corresponding `serving-*` entry in `fastapi_app.yml` to avoid deploy errors.

**Validation**

- **Serving UI:** Compute → Serving → check for `decline-analyst-dev`, `approval-propensity-dev`, `risk-scoring-dev`, `smart-routing-dev`, `smart-retry-dev`.
- **App:** Open **Decisioning** or **Command Center**; use “Approval propensity” or “Risk score”; if Databricks is connected, calls hit the real endpoints (otherwise mock data is used).

**Business value**

- **Approval propensity:** Reduces false declines by approving likely-good transactions; improves approval rates and revenue.
- **Risk scoring:** Enables frictionless flows for low risk and step-up for high risk; balances fraud loss and approval rate.
- **Smart routing:** Routes each transaction to the best-performing solution/network; improves approval rate and latency.
- **Smart retry:** Identifies recoverable declines and optimal retry timing; recovers otherwise-lost revenue.

---

## 2. UC functions (agent tools) — 11 functions

Used by the **Agent Framework** (Orchestrator and specialists) and **LangGraph** agents for SQL-backed analytics (decline trends, routing, retry, risk, KPIs, optimization, trends).

| Function name                     | Description / use |
|----------------------------------|-------------------|
| `get_cascade_recommendations`    | Recommended cascade configuration by merchant segment (Smart Routing agent). |
| `get_decline_by_segment`         | Decline breakdown by merchant segment (Decline Analyst). |
| `get_decline_trends`             | Top decline reasons and characteristics (Decline Analyst). |
| `get_high_risk_transactions`     | High-risk transactions for review (Risk Assessor). |
| `get_kpi_summary`                | Executive KPI summary (Performance Recommender). |
| `get_optimization_opportunities`| Optimization opportunities by routing/geography (Performance Recommender). |
| `get_recovery_opportunities`     | High-value recovery opportunities for retry (Smart Retry). |
| `get_retry_success_rates`        | Historical retry success rates by decline reason (Smart Retry). |
| `get_risk_distribution`          | Risk score distribution across tiers (Risk Assessor). |
| `get_route_performance`          | Approval rates and latency by payment route (Smart Routing). |
| `get_trend_analysis`             | Performance trends over time (Performance Recommender). |

**Creation**

- **Source:** `src/payment_analysis/agents/uc_tools/uc_agent_tools.sql` (placeholders `__CATALOG__` / `__SCHEMA__`).
- **Job:** **Step 3 (Initialize Ingestion)** includes task **create_uc_agent_tools** (notebook `run_create_uc_agent_tools`). Run Job 3 after gold views and `payments_enriched_silver` exist (pipeline must have run).
- **Catalog/schema:** Same as bundle variables (e.g. `ahs_demos_catalog.payment_analysis`).

**Validation**

- **SQL:** In a notebook or SQL editor:  
  `SELECT * FROM ahs_demos_catalog.payment_analysis.get_kpi_summary();`  
  (Replace catalog/schema if different.)
- **Agents:** In the app, open **AI Agents**, run a specialist (e.g. Decline Analyst or Performance Recommender); agents call these functions when Databricks is connected.

**App resource bindings**

The bundle schema does not yet support **function** as an app resource type. To grant the app permission to execute these UC functions, add them manually:

**Workspace → Compute → Apps → payment-analysis → Edit → Configure → App resources → + Add resource → Function**

Add each of the 11 functions with **Can execute** (e.g. `ahs_demos_catalog.payment_analysis.get_cascade_recommendations`, …). The full list is in `resources/fastapi_app.yml` (commented) for copy-paste.

**Business value**

- **Decline analysis:** Understand why transactions decline and by segment; prioritize fixes to improve approval rates.
- **Routing optimization:** See route-level approval and latency; tune cascades and routing rules.
- **Retry and recovery:** Identify which decline reasons and segments are worth retrying; improve recovery revenue.
- **Risk and KPIs:** Monitor risk tiers and executive KPIs; align fraud controls with approval and revenue goals.
- **Trends and optimization:** Track performance over time and by geography; focus on high-impact optimization areas.

---

## 3. Checklist: ensure full value

| # | Item | How to verify |
|---|------|----------------|
| 1 | **Step 5 (Train ML Models)** run | Job 5 completed; models visible in **Data → Catalog → &lt;catalog&gt;.&lt;schema&gt; → Models**. |
| 2 | **model_serving.yml** included | `databricks.yml` has `- resources/model_serving.yml` uncommented; redeploy. |
| 3 | **Five serving endpoints** exist | Compute → Serving shows decline-analyst-*, approval-propensity-*, risk-scoring-*, smart-routing-*, smart-retry-*. |
| 4 | **App has CAN_QUERY** on endpoints | `resources/fastapi_app.yml` has the 5 `serving-*` resources (or add in Apps UI). |
| 5 | **Job 3 (Initialize Ingestion)** run | Gold views + **create_uc_agent_tools** task completed. |
| 6 | **UC functions** exist | `SELECT * FROM <catalog>.<schema>.get_kpi_summary();` returns data. |
| 7 | **App can execute UC functions** | Add 11 functions in Apps → Configure → App resources (Function, Can execute), or wait for bundle support. |
| 8 | **Agents and Decisioning** | Open app → AI Agents and Decisioning; use propensity/risk/routing/retry; confirm real data when Databricks is connected. |

---

## 4. References

- **Model serving config:** `resources/model_serving.yml`
- **App resources (bindings):** `resources/fastapi_app.yml`
- **UC functions SQL:** `src/payment_analysis/agents/uc_tools/uc_agent_tools.sql`
- **Backend model calls:** `src/payment_analysis/backend/services/databricks_service.py` (e.g. `call_approval_model`, `call_risk_model`, `call_routing_model`)
- **Agents and tools:** `src/payment_analysis/agents/agent_framework.py`, `src/payment_analysis/agents/langgraph_agents.py`
- **Deployment order:** [DEPLOYMENT.md](DEPLOYMENT.md) (Steps 1–7)
