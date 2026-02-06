# Pre-Deployment Validation Checklist

Use this checklist to validate the full flow before deploying the Payment Analysis solution.

**Bundle variables (defaults):** `catalog=ahs_demos_catalog`, `schema=ahs_demo_payment_analysis_dev`, `environment=dev`

---

## 1. Real-time stream simulator

| Check | Resource | Status |
|-------|----------|--------|
| Job defined | `resources/streaming_simulator.yml` → `transaction_stream_simulator` | ✅ |
| Notebook | `src/payment_analysis/streaming/transaction_simulator.py` | ✅ |
| Writes to | Delta table `{catalog}.{schema}.raw_payment_events` (or DLT source) | ✅ |
| Params | `catalog`, `schema` from `${var.catalog}`, `${var.schema}` | ✅ |
| Output mode | `delta` | ✅ |

**Note:** Simulator runs as a job; it writes synthetic events so the ETL pipeline has a source. The Lakeflow pipelines consume from the Delta table via Change Data Feed (bronze tables or streaming source).

---

## 2. Real-time Lakeflow Declarative Pipeline (LDP) Ingestion

| Check | Resource | Status |
|-------|----------|--------|
| ETL pipeline | `resources/pipelines.yml` → `payment_analysis_etl` | ✅ |
| Target | `${var.schema}` (single schema for all layers) | ✅ |
| Libraries | bronze_ingest, silver_transform, gold_views | ✅ |
| Mode | `continuous: true`, `serverless: true` | ✅ |
| Real-time pipeline | `payment_realtime_pipeline` → realtime_pipeline notebook | ✅ |
| Schema alignment | Pipelines, jobs, UC, model_serving all use `${var.schema}` | ✅ |

**Note:** Data flows from simulator (or Kafka) → Bronze → Silver → Gold via Delta Live Tables.

---

## 3. Lakehouse and Unity Catalog

| Check | Resource | Status |
|-------|----------|--------|
| Schema | `resources/unity_catalog.yml` → schema name `${var.schema}` | ✅ |
| Volumes | raw_data, checkpoints, ml_artifacts, reports (same schema) | ✅ |
| Catalog | `${var.catalog}` | ✅ |

**Vector search:** Not present in this bundle. To add semantic/RAG use cases, you would add a Vector Search index (e.g. on document or embedding tables) and reference it from Genie or an agent. Optional for this demo.

---

## 4. Dashboards

| Check | Resource | Status |
|-------|----------|--------|
| Definition | `resources/dashboards.yml` (10 AI/BI Dashboards) | ✅ |
| Warehouse | `${var.warehouse_id}` | ✅ |
| Parent path | `${workspace.root_path}/dashboards` | ✅ |
| Included in bundle | **Commented out** in `databricks.yml` → uncomment when ready | ⚠️ |

**Action:** When gold views exist and data is available, uncomment `resources/dashboards.yml` in `databricks.yml` and redeploy.

---

## 5. Genie space

| Check | Resource | Status |
|-------|----------|--------|
| Sync job | `resources/genie_spaces.yml` → `genie_sync_job` | ✅ |
| Notebook | `src/payment_analysis/genie/sync_genie_space.py` | ✅ |
| Params | `catalog`, `schema` from `${var.catalog}`, `${var.schema}` | ✅ |
| Space config | Documented in genie_spaces.yml comments; job writes config to workspace | ✅ |

**Action:** After deployment, create/configure the Genie space in the UI or via API using the documented tables (e.g. `v_executive_kpis`, `v_top_decline_reasons`).

---

## 6. Information extraction

| Check | Status |
|-------|--------|
| Dedicated “information extraction” job or pipeline | ❌ Not a separate resource |
| Covered by | Genie (NL over tables), custom LLM agents (orchestrator/decline/routing/retry), and optional RAG if you add vector search | ✅ (implicit) |

**Note:** There is no standalone “information extraction” module. Insights are derived via Genie queries, agent notebooks, and (if added) vector search.

---

## 7. Custom LLM agents

| Check | Resource | Status |
|-------|----------|--------|
| Agent framework | `src/payment_analysis/agents/agent_framework.py` | ✅ |
| Jobs | `resources/ai_gateway.yml` → smart_routing, smart_retry, decline_analyst, risk_assessor, performance_recommender, orchestrator_agent_job | ✅ |
| Params | `catalog`, `schema`, `agent_role`, `query` from `${var.catalog}`, `${var.schema}` | ✅ |
| LLM | Uses Databricks serving endpoint (e.g. `databricks-meta-llama-3-1-70b-instruct`) for chat | ✅ |

---

## 8. Model serving

| Check | Resource | Status |
|-------|----------|--------|
| Endpoints | `resources/model_serving.yml` (approval propensity, risk scoring, smart routing, smart retry) | ✅ |
| Model paths | `${var.catalog}.${var.schema}.<model_name>` | ✅ |
| Auto-capture | approval_propensity endpoint → inference table in same catalog/schema | ✅ |
| Included in bundle | **Commented out** in `databricks.yml` → uncomment after models are trained | ⚠️ |

**Action:** Train models first (ML job), then uncomment `resources/model_serving.yml` and redeploy.

---

## 9. AI Gateway

| Check | Resource | Status |
|-------|----------|--------|
| LLM endpoints | Used by agent jobs (serving endpoint name in code) | ✅ |
| Agent jobs | All in `resources/ai_gateway.yml`; call Model Serving + LLM as needed | ✅ |
| Guardrails / rate limits | Defined in model_serving.yml per endpoint (e.g. risk_scoring guardrails) | ✅ |

**Note:** “AI Gateway” here is the combination of model serving endpoints, LLM endpoint, and agent jobs; there is no separate gateway bundle resource.

---

## 10. Databricks apps

| Check | Resource | Status |
|-------|----------|--------|
| App definition | `app.yml` (uvicorn command for FastAPI app) | ✅ |
| Backend | `payment_analysis.backend.app:app` | ✅ |
| Deploy | `apx deploy` or `databricks apps deploy` per project docs | ✅ |
| Frontend | Served by backend; build via `uv run apx build` | ✅ |

**Action:** Deploy the app to the workspace after bundle deploy; ensure `DATABRICKS_HOST`, `DATABRICKS_TOKEN`, and (optionally) `DATABRICKS_WAREHOUSE_ID`, `DATABRICKS_CATALOG`, `DATABRICKS_SCHEMA` are set for the app environment.

---

## Deployment order (recommended)

1. **Deploy bundle (no dashboards/model serving):**  
   `databricks bundle deploy -t dev`
2. **Run simulator** → populate bronze/source.
3. **Start ETL pipeline** → bronze → silver → gold.
4. **Run gold views job** → create views for dashboards/Genie.
5. **Run ML training job** → register models in Unity Catalog.
6. **Uncomment and redeploy:** `resources/dashboards.yml`, then `resources/model_serving.yml` (if using).
7. **Configure Genie space** (UI or API).
8. **Deploy Databricks app** (apx deploy / apps deploy).
9. **Run AI orchestrator / agents** as needed.

---

## Quick validation commands

```bash
# Deploy (first time or after YAML changes)
databricks bundle deploy -t dev

# Validate bundle (syntax/resources)
databricks bundle validate -t dev

# Run simulator
databricks bundle run transaction_stream_simulator -t dev

# Start ETL pipeline (use pipeline ID from bundle output or workspace)
databricks pipelines start-update <pipeline_id>
```

---

## Schema consistency summary

All of the following use the **same** `catalog` and `schema` variables so that one Unity Catalog schema is used end-to-end:

- **Variables:** `var.catalog`, `var.schema` (defaults: `ahs_demos_catalog`, `ahs_demo_payment_analysis_dev`)
- **Streaming simulator job:** base_parameters `catalog`, `schema`
- **DLT pipelines:** `schema`, `configuration.schema_name`
- **ML jobs, agent jobs, Genie sync job:** notebook/sql params `catalog`, `schema`
- **Unity Catalog:** schema name and volume `schema_name`
- **Model serving:** `entity_name`, `schema_name`, `catalog_name`
- **Backend (setup, DatabricksService):** defaults aligned with `var.schema`

This avoids “tables in one schema, jobs querying another” issues after deployment.
