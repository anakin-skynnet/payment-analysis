# 2. Data Flow

From transaction to insight in five stages.

## Overview

```
INGESTION → PROCESSING → INTELLIGENCE → ANALYTICS → APPLICATION
  1000/s    Medallion     ML + AI       Dashboards    Web App
            Bronze→Gold   Agents        + Genie
```

---

## Stage 1: Ingestion

- **Simulator:** 1,000 events/sec → Delta table (e.g. `payments_stream_input` or source for DLT)
- **Schema:** transaction_id, amount, merchant, card_network, fraud_score, timestamps
- **Target:** &lt;1s ingestion latency

---

## Stage 2: Processing (Medallion)

| Layer | Table/View | Purpose |
|-------|------------|---------|
| **Bronze** | `payments_raw_bronze` | Raw capture, audit columns |
| **Silver** | `payments_enriched_silver` | Clean, validate, derive risk_tier, amount_bucket, is_cross_border, composite_risk_score, time columns |
| **Gold** | 12+ views | Pre-aggregated metrics: `v_executive_kpis`, `v_approval_trends_hourly`, `v_top_decline_reasons`, `v_solution_performance`, `v_retry_performance`, etc. |

**Target:** &lt;5s Bronze → Silver → Gold

---

## Stage 3: Intelligence

**ML models (Unity Catalog):**

| Model | Accuracy | Purpose |
|-------|----------|---------|
| Approval Propensity | ~92% | Approval likelihood |
| Risk Scoring | ~88% | Fraud/AML risk |
| Smart Routing | ~75% | Optimal payment solution |
| Smart Retry | ~81% | Recovery opportunities |

**Flow:** Silver → features → MLflow training → Model Registry → Model Serving

**AI agents:** 7 agents (Genie, model serving, AI Gateway). Target: &lt;50ms serving, &lt;30s agent response.

---

## Stage 4: Analytics

- **10 AI/BI dashboards** – Executive, operations, technical (sources: gold views)
- **Genie** – Natural language over catalog/schema; e.g. “What’s our approval rate today?”, “Top decline reasons”
- **Target:** &gt;85% query success, 100+ MAU

---

## Stage 5: Application

- **Backend:** FastAPI – `/api/analytics/*`, `/api/decisioning/*`, `/api/notebooks/*`, `/api/agents/*`
- **Frontend:** React – Dashboard, Dashboards gallery, Notebooks, ML Models, AI Agents, Decisioning, Experiments, Declines
- **Target:** &lt;2s page load, &lt;500ms API

---

## Example: “Approval rate” KPI

1. Simulator emits event → Bronze (~1s) → Silver (~3s) → Gold view `v_executive_kpis` (~5s)
2. Backend queries `v_executive_kpis` via SQL Warehouse
3. Frontend shows approval rate in KPI card  
**End-to-end:** ~7s event → UI

---

## Performance targets

| Metric | Target |
|--------|--------|
| Ingestion | &lt;1s |
| Bronze → Silver | &lt;3s |
| Silver → Gold | &lt;2s |
| API query | &lt;2s |
| ML inference | &lt;100ms |
| Agent response | &lt;30s |

---

## Technologies

Delta Lake, Unity Catalog, Delta Live Tables, MLflow, Model Serving, AI/BI Dashboards, Genie, AI Gateway (Llama 3.1), FastAPI, React/TanStack Router. Deploy with **Databricks Asset Bundles**; see [1_DEPLOYMENTS](1_DEPLOYMENTS.md).
