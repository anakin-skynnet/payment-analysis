# 1. Deployments

Step-by-step deployment for the Payment Approval Optimization Platform. **One-click run links:** [5_DEMO_SETUP](5_DEMO_SETUP.md).

## Prerequisites

Databricks workspace (Unity Catalog), SQL Warehouse, CLI configured. Python 3.10+ with `uv`, Node 18+ with `bun`. Permissions: jobs, **Lakeflow**, model serving; write to `ahs_demos_catalog`; deploy to `/Workspace/Users/<your_email>/`.

## Quick Start

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
```

For prod with different catalog/schema in dashboards, run `./scripts/validate_bundle.sh prod` (uses `prepare_dashboards.py`). Then run jobs/pipelines per [5_DEMO_SETUP](5_DEMO_SETUP.md).

## Steps at a glance

| # | Step | Where | Action |
|---|------|--------|--------|
| 1 | Deploy bundle | CLI | `databricks bundle validate -t dev` then `databricks bundle deploy -t dev` |
| 2 | Data ingestion | App **Setup & Run** or Workflows | Run **Transaction Stream Simulator**; output `raw_payment_events` |
| 3 | ETL (Lakeflow) | App **Setup & Run** or Lakeflow | Start **Payment Analysis ETL** pipeline; Bronze → Silver → Gold |
| 4 | Gold views | App **Setup & Run** or Workflows | Run **Create Payment Analysis Gold Views**; verify `v_executive_kpis` |
| 5 | Lakehouse tables (SQL) | SQL Warehouse / Notebook | Run in order: `vector_search_and_recommendations.sql`, `approval_rules.sql`, `online_features.sql` (same catalog/schema) |
| 6 | Train ML models | App **Setup & Run** or Workflows | Run **Train Payment Approval ML Models** (~10–15 min); 4 models in UC |
| 7 | Dashboards & app | — | 11 dashboards in bundle; app: `.env` + `uv run apx dev` or deploy |
| 8 | Model serving | After step 6 | Redeploy bundle (model_serving.yml) or already included |
| 9 | AI agents (optional) | Workflows | Run **Orchestrator** or other agents in `ai_gateway.yml`; Genie optional |
| 10 | Verify | App + Workspace | KPIs on **Dashboard**; **Rules**, **Decisioning**, **ML Models**; 4 models in UC. All jobs/pipelines have one-click Run and Open in **Setup & Run** (steps 1–7 and 6b; Quick links for Stream processor and Test Agent Framework). |

## Steps (detail)

| Step | Purpose | Action |
|------|---------|--------|
| **1** | Deploy bundle | Prepare dashboards for prod: `uv run python scripts/prepare_dashboards.py` (prod: add `--catalog`/`--schema`). Then `databricks bundle validate -t dev` and `databricks bundle deploy -t dev`. |
| **2** | Generate data | **Setup & Run** → “Run simulator” or Workflows → “Transaction Stream Simulator”; output `raw_payment_events`. |
| **3** | Lakeflow ETL | **Setup & Run** → “Start ETL pipeline” or Lakeflow → “Payment Analysis ETL” → Start; Bronze → Silver → Gold. |
| **4** | Gold views | **Setup & Run** → “Run gold views job” or Workflows → “Create Payment Analysis Gold Views”; verify `v_executive_kpis` etc. |
| **5** | Lakehouse (SQL) | In SQL Warehouse or a notebook (same catalog/schema), run in order: (a) `vector_search_and_recommendations.sql` — Vector Search source + recommendations; (b) `approval_rules.sql` — Rules table for app + agents; (c) `online_features.sql` — Online features for ML/AI in the app. Scripts live in `src/payment_analysis/transform/`. |
| **6** | ML models | **Setup & Run** → “Run ML training” or Workflows → “Train Payment Approval ML Models”; ~10–15 min; registers 4 models in UC. |
| **7** | Dashboards & app | Bundle deploys 11 dashboards; warehouse from `var.warehouse_id`. App: set `.env` (DATABRICKS_HOST, TOKEN, WAREHOUSE_ID, CATALOG, SCHEMA); `uv run apx dev` or `apx build` + deploy. |
| **8** | Model serving | After step 6, model serving deploys with bundle (or redeploy). **ML Models** page in app shows catalog/schema models. |
| **9** | Genie / AI agents | Optional: Genie Spaces; run **Orchestrator** or other agent jobs from **Setup & Run** or Workflows. |
| **10** | Verify | **Dashboard**: KPIs, online features, decisions. **Rules**: add/edit rules (Lakehouse). **Decisioning**: recommendations + policy test. **ML Models**: list and links to Registry/MLflow. Workspace: bronze/silver data; 4 models in UC. |

## Schema Consistency

Use one catalog/schema everywhere (defaults: `ahs_demos_catalog`, `ahs_demo_payment_analysis_dev`). Bundle: `var.catalog`, `var.schema`; backend: `DATABRICKS_CATALOG`, `DATABRICKS_SCHEMA`.

## Where to find resources in the workspace

After a **successful** `databricks bundle deploy -t dev`, look for:

- **Workspace:** **Workspace** → **Users** → your user → **getnet_approval_rates_v3** (files, dashboards folder).
- **Jobs:** **Workflow** (Jobs) → names like `[dev …] Train Payment Approval ML Models`, `[dev …] Transaction Stream Simulator`.
- **Lakeflow:** **Lakeflow** → `[dev] Payment Analysis ETL`, `[dev] Payment Real-Time Stream`.
- **SQL Warehouse:** **SQL** → **Warehouses** → `[dev] Payment Analysis Warehouse`.
- **Catalog:** **Catalog** → `ahs_demos_catalog` → schema `ahs_demo_payment_analysis_dev`.
- **Dashboards:** **SQL** → **Dashboards** (or under the workspace folder above).

If deploy **failed** (e.g. at model serving), some resources will be missing. Comment out `model_serving.yml` in `databricks.yml` and run `databricks bundle deploy -t dev` again. Confirm workspace/user with `databricks bundle validate -t dev`. **Vector Search** deploy can fail if the source table `transaction_summaries_for_search` does not exist (run `vector_search_and_recommendations.sql` first) or if the embedding model `databricks-bge-large-en` is not available in the workspace; you can comment out `resources/vector_search.yml` in `databricks.yml` to skip it.

## Troubleshooting

| Issue | Actions |
|-------|---------|
| Don't see resources | Redeploy after commenting out `model_serving.yml` if deploy failed; check workspace/user matches `databricks bundle validate -t dev`. |
| Lakeflow fails | Pipeline logs; confirm `raw_payment_events`; UC permissions; `pipelines reset` if needed |
| Dashboards empty | Gold views + data; warehouse running; warehouse_id in config |
| ML training fails | Silver data; ML runtime; UC model registry; MLflow logs |
| App won’t start | Ports 8000/5173; `uv sync`, `bun install`; `.env` |

## Scripts

- **validate_bundle.sh** — For **prod** (or when dashboards use a different catalog/schema): runs `prepare_dashboards.py` with optional `--catalog`/`--schema`, then `databricks bundle validate -t <target>`. For **dev**, `databricks bundle validate -t dev` and `databricks bundle deploy -t dev` work without this script.
- **prepare_dashboards.py** — Run once per prod deploy: copies dashboard JSONs to `.build/dashboards/` and optionally substitutes catalog/schema. Dev uses source files in `src/payment_analysis/dashboards/` directly.

**Estimated time:** 45–60 min.
