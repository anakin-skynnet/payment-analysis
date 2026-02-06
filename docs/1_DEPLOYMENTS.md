# 1. Deployments

Step-by-step deployment for **Payment Analysis**. **One-click run links:** [Demo setup & one-click run](#demo-setup--one-click-run) below.

## Prerequisites

Databricks workspace (Unity Catalog), SQL Warehouse, CLI configured. Python 3.10+ with `uv`, Node 18+ with `bun`. Databricks App Node runtime is 22.16; `package.json` engines should target it (e.g. `>=22.0.0`). Permissions: jobs, **Lakeflow**, model serving; write to `ahs_demos_catalog`; deploy to `/Workspace/Users/<your_email>/payment-analysis` (or `var.workspace_folder`). **Databricks App:** You cannot install system-level packages (e.g. `apt-get`, Conda); only dependencies in `requirements.txt` and `package.json` are used. See [4_TECHNICAL](4_TECHNICAL.md) (Databricks App compatibility).

## Quick Start

**Before every deploy** (so dashboards and the Gold Views job use the same catalog/schema):

```bash
./scripts/bundle.sh validate dev    # dev: prepares .build/dashboards and .build/transform, then validates
# or: uv run python scripts/dashboards.py prepare   then  databricks bundle validate -t dev
databricks bundle deploy -t dev
```

For prod with different catalog/schema, run `./scripts/bundle.sh validate prod` (prepares with prod catalog/schema). Then run jobs/pipelines per [Demo setup](#demo-setup--one-click-run) below. Dashboards read from `.build/dashboards/`; the **Create Gold Views** job runs `.build/transform/gold_views.sql` (with `USE CATALOG`/`USE SCHEMA`) so views are created in the same catalog.schema and dashboards find them.

## Steps at a glance

| # | Step | Where | Action |
|---|------|--------|--------|
| 1 | Deploy bundle | CLI | `./scripts/bundle.sh deploy dev` (or prepare dashboards, then validate, then deploy) |
| 2 | Data ingestion | App **Setup & Run** or Workflows | Run **Transaction Stream Simulator**; output `raw_payment_events` |
| 3 | ETL (Lakeflow) | App **Setup & Run** or Lakeflow | Start **Payment Analysis ETL** pipeline; Bronze → Silver → Gold |
| 4 | Gold views | App **Setup & Run** or Workflows | Run **Create Payment Analysis Gold Views**; verify `v_executive_kpis` |
| 5 | Lakehouse tables (SQL) | SQL Warehouse / Notebook | Run in order: `app_config.sql`, `vector_search_and_recommendations.sql`, `approval_rules.sql`, `online_features.sql` (same catalog/schema) |
| 6 | Train ML models | App **Setup & Run** or Workflows | Run **Train Payment Approval ML Models** (~10–15 min); 4 models in UC |
| 7 | Dashboards & app | — | 12 dashboards in bundle; app: `.env` + `uv run apx dev` or deploy |
| 8 | Model serving | After step 6 | Redeploy bundle (model_serving.yml) or already included |
| 9 | AI agents (optional) | Workflows | Run **Orchestrator** or other agents in `agents.yml`; Genie optional |
| 10 | Verify | App + Workspace | KPIs on **Dashboard**; **Rules**, **Decisioning**, **ML Models**; 4 models in UC. All jobs/pipelines have one-click Run and Open in **Setup & Run** (steps 1–7 and 6b; Quick links for Stream processor and Test Agent Framework). |

## Steps (detail)

| Step | Purpose | Action |
|------|---------|--------|
| **1** | Deploy bundle | Run `./scripts/bundle.sh deploy dev` (or for prod: `./scripts/bundle.sh deploy prod`). For manual steps: run `uv run python scripts/dashboards.py prepare` (prod: add `--catalog`/`--schema`), then `databricks bundle validate -t dev` and `databricks bundle deploy -t dev`. |
| **2** | Generate data | **Setup & Run** → “Run simulator” or Workflows → “Transaction Stream Simulator”; output `raw_payment_events`. |
| **3** | Lakeflow ETL | **Setup & Run** → “Start ETL pipeline” or Lakeflow → “Payment Analysis ETL” → Start; Bronze → Silver → Gold. |
| **4** | Gold views | **Setup & Run** → “Run gold views job” or Workflows → “Create Payment Analysis Gold Views”; verify `v_executive_kpis` etc. |
| **5** | Lakehouse (SQL) | In SQL Warehouse or a notebook (same catalog/schema), run in order: (a) `app_config.sql` — single-row table for app catalog/schema (used by UI and all Lakehouse operations); (b) `vector_search_and_recommendations.sql` — Vector Search source + recommendations; (c) `approval_rules.sql` — Rules table for app + agents; (d) `online_features.sql` — Online features for ML/AI in the app. Scripts live in `src/payment_analysis/transform/`. |
| **6** | ML models | **Setup & Run** → “Run ML training” or Workflows → “Train Payment Approval ML Models”; ~10–15 min; registers 4 models in UC. |
| **7** | Dashboards & app | Bundle deploys 12 dashboards; warehouse from `var.warehouse_id`. App: set `.env` (DATABRICKS_HOST, TOKEN, WAREHOUSE_ID, and optionally DATABRICKS_CATALOG, DATABRICKS_SCHEMA for bootstrap); run locally with `uv run apx dev`, or deploy as a Databricks App (see **Deploy app as a Databricks App** below). Effective catalog/schema can be set in the UI via **Setup & Run** → **Save catalog & schema**. |
| **8** | Model serving | After step 6, model serving deploys with bundle (or redeploy). **ML Models** page in app shows catalog/schema models. |
| **9** | Genie / AI agents | Optional: Genie Spaces; run **Orchestrator** or other agent jobs from **Setup & Run** or Workflows. |
| **10** | Verify | **Dashboard**: KPIs, online features, decisions. **Rules**: add/edit rules (Lakehouse). **Decisioning**: recommendations + policy test. **ML Models**: list and links to Registry/MLflow. Workspace: bronze/silver data; 4 models in UC. |

## Deploy app as a Databricks App

The same app you run at **http://localhost:8000** (FastAPI + React UI) can be deployed to Databricks Apps via the bundle.

1. **Build** the frontend and wheel (so the app serves the UI):  
   `uv run apx build`
2. **Deploy** the bundle (this creates/updates the app in the workspace):  
   `./scripts/bundle.sh deploy dev`  
   If deploy fails with *"The maximum number of apps for your workspace... is 200"*, delete unused apps in **Workspace → Apps** and redeploy.
3. **Run** the app and get the URL:
   - From the CLI: `databricks bundle run payment_analysis_app -t dev`
   - Or in the workspace: **Apps** → find **payment-analysis** → open and start the app.
4. **App URL** is shown after starting (e.g. `https://<workspace-host>/apps/payment-analysis?o=...`). You can also run `databricks bundle summary -t dev` to see the app and its URL.

The app resource is defined in `resources/app.yml`; runtime is configured in `app.yaml` (uvicorn, PYTHONPATH=src). Python dependencies for the Apps container are in `requirements.txt` at the project root (Databricks installs these during app deployment).

## Schema Consistency

Use one catalog/schema everywhere (defaults: `ahs_demos_catalog`, `ahs_demo_payment_analysis_dev`). Bundle: `var.catalog`, `var.schema`; backend: bootstrap from `DATABRICKS_CATALOG`, `DATABRICKS_SCHEMA` (used to locate the `app_config` table). The **effective** catalog/schema for all app operations (analytics, rules, ML, agents) is read from the Lakehouse `app_config` table at startup; you can change it via **Setup & Run** → **Save catalog & schema** (`PATCH /api/setup/config`). See [4_TECHNICAL](4_TECHNICAL.md) (“Catalog and schema (app_config)”).

## Will I see all resources in my workspace?

**Yes.** By default the bundle deploys (without Lakebase and model serving so deploy always succeeds):

- **Workspace** folder and synced files under **Workspace → Users → &lt;you&gt; → payment-analysis** (`var.workspace_folder`)
- **Workflow (Jobs):** simulator, gold views, ML training, test agent, 6 AI agents, stream processor, Genie sync
- **Lakeflow:** 2 pipelines (ETL, real-time)
- **SQL** warehouse, **Unity Catalog** (schema + volumes), **12 dashboards**, **Databricks App**

**Optional — enable after deploy:**

| Resource | How to enable |
|----------|----------------|
| **Lakebase** (Postgres for rules/experiments/incidents) | In `databricks.yml`, uncomment `resources/lakebase.yml`. Use a **unique** instance name to avoid "Instance name is not unique" (e.g. `--var lakebase_instance_name=payment-analysis-db-YOURNAME` or set in target variables). Then set app env **PGAPPNAME** to that name. |
| **Model serving** (4 endpoints) | Run **Step 6** (Train Payment Approval ML Models) so the 4 models exist in UC. Then in `databricks.yml`, uncomment `resources/model_serving.yml` and run `./scripts/bundle.sh deploy dev` again. |

**Vector Search** is not in the bundle schema; create the endpoint and index manually from `resources/vector_search.yml` after running `vector_search_and_recommendations.sql`.

## Where to find resources in the workspace

After a **successful** `./scripts/bundle.sh deploy dev` (or equivalent deploy), look for:

- **Workspace:** **Workspace** → **Users** → your user → **payment-analysis** (files, dashboards folder; from `var.workspace_folder`).
- **Jobs:** **Workflow** (Jobs) → names like `[dev …] Train Payment Approval ML Models`, `[dev …] Transaction Stream Simulator`. Agent jobs (Orchestrator, Smart Routing, etc.) are defined in `resources/agents.yml`.
- **Mosaic AI Gateway:** Governed LLM access is configured on the four custom endpoints in `model_serving.yml` (rate limits, usage tracking, guardrails). For pay-per-token LLM endpoints, enable AI Gateway in **Serving** → endpoint → **Edit AI Gateway**. See [AI Gateway docs](https://docs.databricks.com/aws/en/ai-gateway/).
- **Lakeflow:** **Lakeflow** → `[dev] Payment Analysis ETL`, `[dev] Payment Real-Time Stream`.
- **SQL Warehouse:** **SQL** → **Warehouses** → `[dev] Payment Analysis Warehouse`.
- **Catalog (Lakehouse database):** **Data** (Catalog Explorer) → **Catalogs** → `ahs_demos_catalog` → schema `ahs_demo_payment_analysis_dev`. Tables, views, and volumes appear under the schema.
- **Dashboards:** **SQL** → **Dashboards** (or under the workspace folder above). After deploy, run `uv run python scripts/dashboards.py publish` to publish all 12 dashboards (embed credentials).

If deploy failed, confirm workspace path with `./scripts/bundle.sh validate dev`. By default, Lakebase and model serving are commented out in `databricks.yml` so deploy succeeds; enable them as in the table above when prerequisites are met.

**Dashboard TABLE_OR_VIEW_NOT_FOUND:** Dashboards use tables/views in the catalog.schema chosen when you ran `dashboards.py prepare`. Run **Create Payment Analysis Gold Views** in that same catalog.schema (the job uses `.build/transform/gold_views.sql`, which sets `USE CATALOG`/`USE SCHEMA`). List required assets: `uv run python scripts/dashboards.py validate-assets --catalog X --schema Y`.

## Troubleshooting

| Issue | Actions |
|-------|---------|
| Don't see resources | Redeploy after commenting out `model_serving.yml` if deploy failed; check workspace path with `./scripts/bundle.sh validate dev`. |
| Lakebase "Instance name is not unique" | Use a unique `lakebase_instance_name` (e.g. `payment-analysis-db-<yourname>`) via `--var lakebase_instance_name=...` or target variables. Or leave Lakebase commented out in `databricks.yml`. |
| Lakeflow fails | Pipeline logs; confirm `raw_payment_events`; UC permissions; `pipelines reset` if needed |
| Dashboards empty | Gold views + data; warehouse running; warehouse_id in config |
| ML training fails | Silver data; ML runtime; UC model registry; MLflow logs |
| App won’t start | Ports 8000/5173; `uv sync`, `bun install`; `.env` |

**Error deploying app: error installing packages** — `requirements.txt` uses pinned versions and pure `psycopg` (no `[binary]`) so pip install succeeds in the container. The world-map (global_coverage) dashboard is a Lakeview dashboard, not a Python/Node package, so it does not cause this error. If the error persists, the platform may be running `npm install` from `package.json`: ensure all three TanStack packages are **1.158.1** and `package.json` has **overrides** for `@tanstack/react-router`, `@tanstack/react-router-devtools`, and `@tanstack/router-plugin` at 1.158.1. Do not commit `package-lock.json` (use `bun.lock` only). Then redeploy. To reproduce locally: delete `node_modules` and `package-lock.json` (if present), run `npm install`, then `npm ls @tanstack/react-router` to confirm a single version. See [4_TECHNICAL](4_TECHNICAL.md) (Databricks Apps package compatibility).

## Scripts

- **bundle.sh** — Single script for bundle and verification. **`./scripts/bundle.sh deploy [dev|prod]`** — prepare dashboards then deploy. **`./scripts/bundle.sh validate [dev|prod]`** — prepare then validate (use before deploy). **`./scripts/bundle.sh verify [dev|prod]`** — full pre-commit: apx dev check, build, backend smoke test, dashboard assets, bundle validate.
- **dashboards.py** — **`prepare`** copies dashboard JSONs and gold_views.sql to `.build/` (run by bundle.sh). **`validate-assets`** lists required tables/views. **`publish`** publishes all 12 dashboards with embed credentials after deploy: `uv run python scripts/dashboards.py publish` (optional `--path`).

## Demo setup & one-click run

One-click links and recommended order for **Payment Analysis**. Replace `<WORKSPACE_URL>` with your Databricks workspace URL. After deploy, bundle files live under **Workspace → Users → &lt;you&gt; → payment-analysis** (or `var.workspace_folder`).

**Recommended order:** (1) Deploy bundle — `./scripts/bundle.sh deploy dev`; (2) Data ingestion — Transaction Stream Simulator; (3) ETL — Payment Analysis ETL pipeline; (4) Gold views — Create Payment Analysis Gold Views job; (5) Lakehouse SQL — run `app_config.sql`, `vector_search_and_recommendations.sql`, `approval_rules.sql`, `online_features.sql` (see `src/payment_analysis/transform/`); (6) Train ML models; (7–8) Optional: real-time pipeline, AI agents.

**Quick links:** Get job/pipeline IDs from **Workflows** / **Lakeflow** (names prefixed with `[dev ...]`). Run simulator: `<WORKSPACE_URL>/#job/<JOB_ID>/run`; ETL: `<WORKSPACE_URL>/pipelines/<PIPELINE_ID>`; Gold views / ML training / Orchestrator: same job-run pattern. **CLI:** `databricks bundle run <job_name> -t dev` (e.g. `transaction_stream_simulator`, `create_gold_views_job`, `train_ml_models_job`, `orchestrator_agent_job`).

**Estimated time:** 45–60 min.
