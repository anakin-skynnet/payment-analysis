# Payment Analysis — Reference Guide

Deployment, configuration, schema reference, version alignment, and troubleshooting. For business context see [Business Requirements](BUSINESS_REQUIREMENTS.md); for architecture and technical details see [Technical Solution](TECHNICAL_SOLUTION.md).

---

## 1. Prerequisites

Databricks workspace (Unity Catalog), SQL Warehouse, CLI configured. **Catalog and schema:** Either (1) create the **catalog** (default `ahs_demos_catalog`) under **Data → Catalogs** before deploy so the bundle can create the **schema** and volumes, or (2) deploy and run **Job 1** first — its first task creates the catalog and schema if they do not exist (requires metastore admin or CREATE_CATALOG/CREATE_SCHEMA). If you use different names, deploy with `--var catalog=<your_catalog> --var schema=<your_schema>`. Python 3.10+ with `uv`, Node 22+ with `bun`. Permissions: jobs, Lakeflow, model serving; write to catalog; deploy to `/Workspace/Users/<you>/payment-analysis`.

---

## 2. Deployment

Deployment is **two-phase**: deploy all resources first (no App), then deploy the App after its dependencies (model serving endpoints) exist.

### Phase 1 — deploy resources (no App)

```bash
./scripts/bundle.sh deploy dev
```

This runs **build** (frontend + wheel), **clean** (removes existing BI dashboards to avoid duplicates), **prepare** (writes `.build/dashboards/` and `.build/transform/*.sql` with catalog/schema), **deploy** (jobs, pipelines, dashboards, UC, model serving — everything except the App), and **publish** (embed credentials).

After phase 1, run **Job 5 (Train Models)** and **Job 6 (Deploy Agents)** from the app **Setup & Run** so ML models and agent registrations exist in UC.

### Phase 2 — deploy app

```bash
./scripts/bundle.sh deploy app dev
```

This **validates** that all app dependencies exist, then **deploys** the App with all 8 resources assigned (SQL warehouse, UC volume, Genie space, 5 serving endpoints).

### Automated two-phase deploy

```bash
./scripts/deploy_with_dependencies.sh dev
```

Runs phase 1, automatically executes Job 5 and Job 6 and waits for completion, then runs phase 2.

### Validate without deploying

```bash
./scripts/bundle.sh validate dev
```

### Steps at a glance

| # | Job (step) | Action |
|---|------------|--------|
| 0 | Deploy bundle | `./scripts/bundle.sh deploy dev` (includes prepare; no missing files) |
| 1 | **1. Create Data Repositories** | **Setup & Run** → Run job 1 (ensure catalog & schema → **create Lakebase Autoscaling** → **Lakebase data init** → lakehouse bootstrap → vector search). Run once. |
| 2 | **2. Simulate Transaction Events** | **Setup & Run** → Run **Transaction Stream Simulator** |
| — | **Pipeline (before Step 3)** | Start **Payment Analysis ETL** (Lakeflow) at least once so it creates `payments_enriched_silver`. |
| 3 | **3. Initialize Ingestion** | **Setup & Run** → Run job 3 (create gold views → **create UC agent tools** → sync vector search) |
| 4 | **4. Deploy Dashboards** | **Setup & Run** → Run job 4 (prepare assets → publish dashboards with embed credentials) |
| 5 | **5. Train Models & Model Serving** | **Setup & Run** → Run **Train Payment Approval ML Models** (~10–15 min) |
| 6 | **6. Deploy Agents** | **Setup & Run** → Run **Deploy Agents** (2 tasks: `run_agent_framework`, `register_responses_agent`) |
| 7 | **7. Genie Space Sync** | **Setup & Run** → Run **Genie Space Sync** (optional) |

---

## 3. App configuration

### Environment variables

**`ORCHESTRATOR_SERVING_ENDPOINT`** is set in **`app.yml`** at project root (`payment-response-agent`); redeploy to apply.

| Variable | Purpose |
|----------|---------|
| **LAKEBASE_PROJECT_ID** | Lakebase Autoscaling project ID (e.g. `payment-analysis-db`). |
| **LAKEBASE_BRANCH_ID** | Lakebase Autoscaling branch (e.g. `production`). |
| **LAKEBASE_ENDPOINT_ID** | Lakebase Autoscaling endpoint (e.g. `primary`). |
| **LAKEBASE_CONNECTION_STRING** | Optional. Direct Postgres URL. When set, app uses this instead of project/branch/endpoint discovery. |
| **DATABRICKS_WAREHOUSE_ID** | Required for SQL/analytics. SQL Warehouse ID (from bundle or sql-warehouse binding). |
| **DATABRICKS_HOST** | Optional when opened from **Compute → Apps** (workspace URL derived from request). |
| **DATABRICKS_TOKEN** | Optional when using OBO. Open from **Compute → Apps** so your token is forwarded. |
| **ORCHESTRATOR_SERVING_ENDPOINT** | Set to `payment-response-agent` in `app.yml`. AI Chat calls this (Path 1). |
| **LLM_ENDPOINT** | Foundation model for AI Gateway fallback (Claude Opus 4.6). |
| **LLM_ENDPOINT_GENIE** | Model for Genie Assistant (Claude Sonnet 4.5). |
| **GENIE_SPACE_ID** | Genie space ID for natural language data queries. |
| **LAKEBASE_SCHEMA** | Optional. Postgres schema for app tables (default `payment_analysis`). |

**User token (OBO):** When the app is opened from **Compute → Apps**, Databricks forwards the user token in the **X-Forwarded-Access-Token** header. No DATABRICKS_TOKEN is required when using OBO.

### App resources in the bundle

**`resources/fastapi_app.yml`**: SQL warehouse, UC volume (reports), Genie space, 1 agent endpoint (`payment-response-agent`), and 4 ML model serving endpoints (`approval-propensity`, `risk-scoring`, `smart-routing`, `smart-retry`) — 8 resources total.

### Schema consistency

Schema name is always **`payment_analysis`** — the same in dev and prod. DAB schema prefixing is disabled via `experimental.skip_name_prefix_for_schema: true` in `databricks.yml`.

---

## 4. Version alignment

All dependency references use **exactly the same versions** everywhere (no ranges).

### Runtime (Databricks App)

| Runtime | Version | Source |
|--------|---------|--------|
| **Python** | 3.11 | `.python-version`; `pyproject.toml` `requires-python = ">=3.11"`. |
| **Node.js** | ≥22.0.0 | `package.json` `engines.node`. Databricks App uses Node.js 22.16. |

### Python (backend and scripts)

**Source of truth:** `pyproject.toml` (all direct deps use `==`). **Lock:** `uv.lock`. **App deploy:** `requirements.txt` is generated from `uv.lock` by `scripts/sync_requirements_from_lock.py`.

**Direct dependencies (exact versions):** databricks-sdk 0.88.0, fastapi 0.129.0, uvicorn 0.40.0, pydantic-settings 2.6.1, sqlmodel 0.0.27, psycopg[binary,pool] 3.2.3.

### Frontend (UI)

**Source of truth:** `package.json` (exact versions only; no `^` or `~`). **Lock:** `bun.lock`.

### Files that must stay aligned

| File | Role |
|------|------|
| `pyproject.toml` | Python direct deps (exact `==`); do not add ranges. |
| `uv.lock` | Resolved Python deps; run `uv lock` after changing pyproject.toml. |
| `requirements.txt` | Generated from uv.lock; do not edit by hand. |
| `package.json` | Frontend deps (exact versions only); run `uv run apx bun install` after changes. |
| `bun.lock` | Resolved frontend deps. |
| `.python-version` | 3.11 (matches Databricks App). |

---

## 5. Schema: tables and views

Catalog/schema: `ahs_demos_catalog.payment_analysis` (or your catalog/schema).

### Summary

| Type | Required | Optional / Not read by app |
|------|----------|----------------------------|
| **Silver/Bronze (Lakeflow)** | payments_enriched_silver, merchants_dim_bronze (100 merchants, 8 segments), merchant_visible_attempts_silver, reason_code_taxonomy_silver, insight_feedback_silver, smart_checkout_decisions_silver | decision_log_silver, payments_stream_alerts |
| **Gold views (Job 3 SQL)** | All 24 `v_*` and metric views (including `v_retry_success_by_reason`) | — |
| **Gold tables (Lakeflow)** | v_retry_performance, v_3ds_funnel_br, v_reason_codes_br, v_reason_code_insights_br, v_entry_system_distribution_br, v_dedup_collision_stats, v_false_insights_metric, v_smart_checkout_* | — |
| **Bootstrap (Job 1)** | v_recommendations_from_lakehouse, v_approval_rules_active, v_online_features_latest (and base tables) | — |

### Silver and Bronze tables (Lakeflow)

Created by **Lakeflow pipelines**. Empty until the pipeline runs and source data exists.

| Object | Required | Where used | Why empty |
|--------|----------|------------|-----------|
| **payments_enriched_silver** | **Yes** | gold_views.sql, gold_views.py, agent_framework.py, uc_agent_tools.sql, vector_search, train_models.py, genie | ETL pipeline not run, or bronze tables empty. |
| **merchants_dim_bronze** | **Yes** | silver_transform.py (payments_enriched_silver reads it) | Bronze ingest not run. Generates 100 merchants (`spark.range(100)`) with 8 segments to match the transaction simulator. |
| **merchant_visible_attempts_silver** | **Yes** | gold_views.py | payments_enriched_silver empty. |
| **reason_code_taxonomy_silver** | **Yes** | gold_views.py | Pipeline not run. Has **static seed**. |
| **insight_feedback_silver** | **Yes** | databricks_service.py (INSERT), gold_views.py | Pipeline not run. Has **seed rows**. |
| **smart_checkout_decisions_silver** | **Yes** | gold_views.py | Pipeline not run. |
| **decision_log_silver** | **No** | Defined in silver_transform.py only | Audit/decision log for future use. Safe to drop. |
| **payments_stream_alerts** | **No** | Defined in realtime_pipeline.py only | Real-time alert table; no reader in app. Safe to drop. |

### Gold views (Job 3 — 24 SQL views)

Created by **Job 3** from `gold_views.sql`. All depend on **payments_enriched_silver**.

| View | Required | Where used |
|------|----------|------------|
| **v_executive_kpis** | Yes | databricks_service.py, dashboards, Genie, agents |
| **v_approval_trends_hourly** | Yes | databricks_service.py, Genie |
| **v_approval_trends_by_second** | Yes | Dashboards, databricks_service |
| **v_performance_by_geography** | Yes | databricks_service.py, dashboards, Genie, agents |
| **v_top_decline_reasons** | Yes | databricks_service.py, dashboards, Genie, agents |
| **v_decline_recovery_opportunities** | Yes | Dashboards |
| **v_last_hour_performance** | Yes | databricks_service.py, dashboards |
| **v_last_60_seconds_performance** | Yes | databricks_service.py, data-quality UI |
| **v_active_alerts** | Yes | databricks_service.py, dashboards |
| **v_solution_performance** | Yes | databricks_service.py, dashboards, Genie, agents |
| **v_card_network_performance** | Yes | databricks_service.py, dashboards |
| **v_merchant_segment_performance** | Yes | Dashboards |
| **v_daily_trends** | Yes | databricks_service.py, dashboards, Genie, agents |
| **v_streaming_ingestion_hourly** | Yes | dashboards.py (asset check) |
| **v_streaming_ingestion_by_second** | Yes | Dashboards |
| **v_streaming_volume_per_second** | Yes | databricks_service.py, dashboards |
| **v_silver_processed_hourly** | Yes | dashboards.py (asset check) |
| **v_silver_processed_by_second** | Yes | Dashboards |
| **v_data_quality_summary** | Yes | databricks_service.py, dashboards |
| **v_uc_data_quality_metrics** | Yes | dashboards.py (asset check) |
| **payment_metrics** | Yes | UC metrics; dashboards.py validation |
| **decline_metrics** | Yes | UC metrics; dashboards.py validation |
| **merchant_metrics** | Yes | UC metrics; dashboards.py validation |
| **v_retry_success_by_reason** | Yes | Smart Retry analytics, retry by decline reason |

### Gold tables (Lakeflow — 9 DLT tables)

Created by **Lakeflow pipeline** (Payment Analysis ETL). Consumed by backend `databricks_service.py`.

| Table | Required | Where used |
|-------|----------|------------|
| **v_retry_performance** | Yes | databricks_service.py (retry-performance API) |
| **v_smart_checkout_service_path_br** | Yes | databricks_service.py |
| **v_smart_checkout_path_performance_br** | Yes | databricks_service.py |
| **v_3ds_funnel_br** | Yes | databricks_service.py |
| **v_reason_codes_br** | Yes | databricks_service.py |
| **v_reason_code_insights_br** | Yes | databricks_service.py |
| **v_entry_system_distribution_br** | Yes | databricks_service.py |
| **v_dedup_collision_stats** | Yes | databricks_service.py |
| **v_false_insights_metric** | Yes | databricks_service.py |

### Bootstrap tables and views (Job 1)

Created by **Job 1**, task `lakehouse_bootstrap`. Base tables are seeded when empty.

| Object | Required | Where used |
|--------|----------|------------|
| **approval_recommendations** | Yes | v_recommendations_from_lakehouse |
| **v_recommendations_from_lakehouse** | Yes | databricks_service.py |
| **approval_rules** | Yes | v_approval_rules_active, agent_framework |
| **v_approval_rules_active** | Yes | agent_framework.py |
| **countries** | Yes | Backend /api/countries, UI filter |
| **online_features** | Yes | v_online_features_latest |
| **incidents_lakehouse** | Yes | uc_agent_tools.sql, backend incidents.py |

### How data is inserted

| Source | Mechanism | Tables / views affected |
|--------|-----------|--------------------------|
| **Lakeflow pipeline (ETL)** | Pipeline reads upstream DLT tables and writes to the next table. | **Bronze:** payments_raw_bronze, merchants_dim_bronze (synthetic `spark.range(100)` with 8 segments in bronze_ingest.py, matching the 100 merchants generated by transaction_simulator). **Silver:** payments_enriched_silver, merchant_visible_attempts_silver, reason_code_taxonomy_silver (static seed), insight_feedback_silver (seed + app INSERT), decision_log_silver, smart_checkout_decisions_silver. **Gold (Lakeflow):** v_retry_performance, v_3ds_funnel_br, v_reason_codes_br, v_reason_code_insights_br, v_entry_system_distribution_br, v_dedup_collision_stats, v_false_insights_metric, v_smart_checkout_*. |
| **Lakeflow pipeline (Real-Time)** | readStream from payments_stream_input → 10s windowed metrics → alerts. | payments_stream_bronze, payments_stream_silver, payments_stream_metrics_10s, payments_stream_alerts. |
| **Job 1 – lakehouse_bootstrap.sql** | `INSERT INTO ... WHERE (SELECT COUNT(*) FROM ...) = 0` (seed when empty). | app_config, approval_rules, countries. |
| **Job 2 – transaction_simulator** | `df.write.mode("append").saveAsTable(target_table)`. | payments_stream_input. |
| **Job 1 – vector_search create_index** | MERGE from payments_enriched_silver into transaction_summaries_for_search. | transaction_summaries_for_search → similar_transactions_index (Vector Search). |
| **Job 3 – run_gold_views.py** | Executes `gold_views.sql`; only creates VIEWs. | All 24 gold SQL views. |
| **Backend (FastAPI)** | `DatabricksService` runs INSERT/MERGE via SQL Warehouse. Dual-write for rules. | app_config, approval_rules, insight_feedback_silver. |

### Order of operations for "no empty tables"

1. Run Job 1 (lakehouse_bootstrap, etc.)
2. Run Lakeflow **Payment Analysis ETL** pipeline so `payments_enriched_silver` exists
3. Run Job 3 (run_gold_views) so SQL gold views exist
4. Optionally run Real-Time pipeline and Job 2 (transaction simulator) to populate streaming views

---

## 6. Job inventory

All bundle jobs have been reviewed for duplicates. **There are no repeated jobs.** Each has a single, distinct purpose.

| Job | Purpose | Notes |
|-----|---------|-------|
| **Job 1** (5 tasks) | Create Data Repositories | ensure_catalog_schema → create_lakebase_autoscaling → lakebase_data_init → lakehouse_bootstrap → create_vector_search_index |
| **Job 2** | Simulate Transaction Events | Producer only (synthetic payment events) |
| **Job 3** | Initialize Ingestion | Create gold views, UC agent tools, sync vector search |
| **Job 4** | Deploy Dashboards | Prepare assets + publish with embed credentials |
| **Job 5** | Train Models & Model Serving | Train 4 ML models; register in UC |
| **Job 6** (2 tasks) | Deploy Agents | run_agent_framework + register_responses_agent |
| **Job 7** | Genie Space Sync | Optional; syncs Genie space config |
| **ETL Pipeline** | Payment Analysis ETL | Bronze → Silver → Gold (Lakeflow) |
| **Real-Time Pipeline** | Real-Time Stream | Streaming events processing |

---

## 7. Scripts

| Script | Purpose |
|--------|---------|
| **bundle.sh** | Two-phase deploy: `deploy [target]` (phase 1); `deploy app [target]` (phase 2); `validate` / `verify`. |
| **deploy_with_dependencies.sh** | Automated two-phase: phase 1 → runs Job 5 & 6 → phase 2. |
| **toggle_app_resources.py** | Toggle serving endpoint bindings in `fastapi_app.yml`. |
| **dashboards.py** | **prepare**, **validate-assets**, **publish**, **check-widgets**, **best-widgets**. |
| **run_and_validate_jobs.py** | Run and validate bundle jobs; optional `--run-pipelines`. |
| **sync_requirements_from_lock.py** | Generate `requirements.txt` from `uv.lock`. |

---

## 8. Workspace resources

By default: Workspace folder, Lakebase, Jobs (7 steps), 2 pipelines, SQL warehouse, Unity Catalog, 3 unified dashboards, Databricks App. **Model Serving:** 4 ML endpoints managed by DAB; 1 agent endpoint created by Job 6. **Vector Search:** endpoint and delta-sync index created by Job 1.

### Where to find resources

- **Workspace:** **Workspace** → **Users** → you → **payment-analysis**
- **Jobs:** **Workflow** → `[dev …]` job names
- **Lakeflow:** **Lakeflow** → ETL and Real-Time Stream
- **SQL Warehouse:** **SQL** → **Warehouses**
- **Catalog / Dashboards:** **Data** → Catalogs; **SQL** → **Dashboards**

---

## 9. Troubleshooting

| Issue | Action |
|-------|--------|
| Database instance STARTING | Wait, then redeploy |
| Don't see resources | Redeploy; run `./scripts/bundle.sh validate dev` |
| Registered model does not exist | Run Step 5 (Train ML models), redeploy |
| Lakebase project/endpoint not found | Run Job 1 or create in **Compute → Lakebase** and set bundle vars |
| Error installing packages (app deploy) | Check **Logs** for pip error. Run `uv lock` then `uv run python scripts/sync_requirements_from_lock.py`. |
| **Catalog '…' or schema not found** | Create catalog in Data → Catalogs, or run Job 1 (creates catalog and schema). |
| **permission denied for schema public** | Set **LAKEBASE_SCHEMA** (`payment_analysis`) in app environment. |
| **Databricks credentials not configured** | Enable OBO (open from Compute → Apps) or set DATABRICKS_HOST + DATABRICKS_WAREHOUSE_ID + DATABRICKS_TOKEN. |
| **Web UI shows "API only"** | Run `uv run apx build` then `databricks bundle deploy -t dev`. Restart app. |
| **Logs show "Uvicorn running on 0.0.0.0:8000"** | Expected for Databricks App (platform proxies requests). |
| **OAuth token lacks scopes** | Remove DATABRICKS_CLIENT_ID/SECRET when using PAT or OBO. |
| **403 / Invalid scope** | Add required scope in Compute → Apps → Configure → User authorization. |
| **Node named '…' already exists** (dashboard) | Run `./scripts/bundle.sh deploy dev` (cleans existing dashboards first). |
| **payments_enriched_silver not found** (Job 3) | Run ETL pipeline first, then Job 3. |
| **Dashboard TABLE_OR_VIEW_NOT_FOUND** | Run Job 3 (gold views) and ETL pipeline in the same catalog.schema. |

### Fix: Lakebase project not found

**Option A (recommended):** `uv run python scripts/create_lakebase_autoscaling.py` — creates project/branch/endpoint matching bundle defaults.

**Option B:** Create in **Compute → Lakebase** UI, then redeploy with `--var lakebase_project_id=... --var lakebase_branch_id=... --var lakebase_endpoint_id=...`.

### Fix: Catalog or schema not found

**Option A:** Create catalog in **Data → Catalogs → Create catalog**, then redeploy.
**Option B:** Deploy with `--var catalog=YOUR_EXISTING_CATALOG`.
**Option C:** Run Job 1 (creates catalog and schema; requires metastore admin or CREATE_CATALOG).

### Fix: PAT / token scopes

Remove DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET from app environment when using PAT or OBO. Create a new PAT with sufficient scope if needed.

---

## 10. Databricks Apps compatibility

**Environment:** Python 3.11, Ubuntu 22.04 LTS, Node.js 22.16.

**Our `requirements.txt`:** Overrides three pre-installed packages (databricks-sdk → 0.88.0, fastapi → 0.129.0, uvicorn → 0.40.0) and adds pydantic-settings, sqlmodel, psycopg[binary]. Overriding is supported; pinning exact versions is recommended.

**Workspace layout:** `workspace.root_path` is the single path for sync, jobs, and the app. `workspace.file_path` is set to `${workspace.root_path}` so there is one tree and no duplicate `files/` copy.

---

## 11. Demo setup

1. **Deploy once:** `./scripts/bundle.sh deploy dev`
2. **Run in order from the app:** Setup & Run → jobs 1 → 2 → (ETL pipeline) → 3 → 4 → 5 → 6 → 7 (optional)
3. **Estimated time:** 45–60 min

---

**See also:** [Overview](OVERVIEW.md) — executive summary. [Business Requirements](BUSINESS_REQUIREMENTS.md) — business context and impact. [Technical Solution](TECHNICAL_SOLUTION.md) — architecture, ML, agents, UI.
