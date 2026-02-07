# Deep Code Review: Ingestion → Analytics → AI → App

End-to-end review of the Payment Analysis platform. **Status:** Verified with two fixes applied.

---

## 1. Ingestion Layer

### 1.1 Transaction Simulator (`streaming/transaction_simulator.py`)
- **Writes to:** `{CATALOG}.{SCHEMA}.payments_stream_input` (widget params from job `base_parameters` = bundle vars).
- **Schema:** Creates table with CDF enabled (`delta.enableChangeDataFeed = true`), required for downstream streaming.
- **Event shape:** Matches silver expectations (transaction_id, amount, fraud_score, is_approved, decline_reason, etc.).
- **Verdict:** Correct; catalog/schema from job params.

### 1.2 Bronze Ingest (`streaming/bronze_ingest.py`)
- **Reads:** `payments_stream_input` (unqualified; pipeline runs in `var.catalog` / `var.schema`).
- **Output:** `payments_raw_bronze` (CDF from stream input), `merchants_dim_bronze` (static dimension).
- **Verdict:** Correct; pipeline config sets catalog/schema.

### 1.3 Silver Transform (`transform/silver_transform.py`)
- **Reads:** DLT `payments_raw_bronze`, `merchants_dim_bronze`.
- **Output:** `payments_enriched_silver` with expectations, derived columns (canonical_transaction_key, risk_tier, decline_reason_standard, retry_scenario, prior_approved_count, attempt_sequence, time_since_last_attempt_seconds, merchant_retry_policy_max_attempts).
- **ML alignment:** All columns required by `ml/train_models.py` exist in silver.
- **Verdict:** Correct.

### 1.4 Pipelines (`resources/pipelines.yml`)
- **ETL pipeline:** bronze_ingest → silver_transform → gold_views (DLT notebooks). Catalog/schema from `${var.catalog}` / `${var.schema}`.
- **Realtime pipeline:** Single notebook `realtime_pipeline.py`; reads `payments_stream_input` (same source as ETL bronze).
- **Verdict:** Correct.

### 1.5 Continuous Stream Processor (`streaming/continuous_processor.py`)
- **Reads:** `{CATALOG}.{SCHEMA}.payments_stream_input` via CDF.
- **Checkpoint:** From job param (e.g. `/Volumes/${var.catalog}/${var.schema}/checkpoints/stream_processor`).
- **Verdict:** Correct.

---

## 2. Analytics Layer

### 2.1 Gold Views
- **Two paths:**
  1. **DLT (pipeline):** `transform/gold_views.py` → tables like `v_approval_kpis`, `v_decline_patterns` (different naming from SQL views).
  2. **SQL (Create Gold Views job):** `gold_views.sql` (in `.build/transform` after prepare) → `v_executive_kpis`, `v_approval_trends_hourly`, `v_solution_performance`, etc.
- **Backend/dashboards:** Use SQL view names (v_executive_kpis, v_approval_trends_hourly, v_solution_performance, …). The **Create Gold Views** job must be run so these views exist; they read from `payments_enriched_silver` (created by ETL pipeline).
- **Fixes applied:**
  - **v_approval_trends_hourly:** Backend and UI expect `approved_count`; it was missing in SQL. Added `SUM(CASE WHEN is_approved ...) as approved_count` to `gold_views.sql`.
  - **v_solution_performance:** Same; added `approved_count` so API/UI columns align.

### 2.2 app_config
- **Table:** `app_config` (id, catalog, schema, updated_at). Seed uses `CURRENT_CATALOG()`, `CURRENT_SCHEMA()` when empty.
- **Backend:** Bootstrap from `DATABRICKS_CATALOG` / `DATABRICKS_SCHEMA`; at startup reads app_config and sets `app.state.uc_config`; all analytics and agents use this via `get_databricks_service(request)`.
- **Verdict:** Correct.

### 2.3 DatabricksService
- **Queries:** Use `self.config.full_schema_name` (catalog.schema from config, which is effective UC from app_config or env).
- **Views used:** v_executive_kpis, v_approval_trends_hourly, v_top_decline_reasons, v_solution_performance, v_smart_checkout_*, v_3ds_funnel_br, v_reason_codes_br, v_reason_code_insights_br, v_entry_system_distribution_br, v_dedup_collision_stats, v_false_insights_metric, v_retry_performance, v_recommendations_from_lakehouse.
- **Verdict:** After gold view fixes, column alignment is correct.

### 2.4 Dashboards
- **Prepare:** `scripts/dashboards.py prepare` injects target catalog.schema into dashboard JSONs under `.build/dashboards`.
- **Bundle:** Deploys from `.build/dashboards`; dashboard assets reference the same view names as backend.
- **Verdict:** Correct.

---

## 3. AI Layer

### 3.1 ML Training (`ml/train_models.py`)
- **Data source:** `{CATALOG}.{SCHEMA}.payments_enriched_silver`; catalog/schema from widgets (job base_parameters).
- **Models:** Approval propensity, risk scoring, smart routing, smart retry; registered to UC at `{CATALOG}.{SCHEMA}.{model_suffix}`.
- **Features:** Match silver columns (prior_approved_count, attempt_sequence, etc.).
- **Verdict:** Correct.

### 3.2 Model Serving
- **Backend:** `databricks_service.py` calls endpoints `approval-propensity-{ENVIRONMENT}`, `risk-scoring-{ENVIRONMENT}`, etc.; fallback to mock when unavailable.
- **Bundle:** `model_serving.yml` commented out by default; when enabled, endpoints align with backend names.
- **Verdict:** Correct.

### 3.3 Agents (`backend/routes/agents.py`)
- **Registry:** AGENTS list with Genie, Model Serving, AI Gateway, Custom LLM entries.
- **UC in responses:** `_apply_uc_config()` replaces `_DEFAULT_UC_PREFIX` with effective catalog.schema from `request.app.state.uc_config`.
- **Workspace URLs:** Built from `get_workspace_url()`; model links use effective catalog.schema.
- **Verdict:** Correct.

### 3.4 Genie (`genie/sync_genie_space.py`)
- **Catalog/schema:** From widgets (job params). Syncs space config and sample questions; references views (e.g. v_approval_trends_hourly) in same catalog.schema.
- **Verdict:** Correct.

---

## 4. App Layer

### 4.1 Backend
- **Lifespan:** Loads app_config (or env), sets `app.state.uc_config`; initializes Runtime (DB), mounts API, serves UI from `__dist__`.
- **Auth:** `get_obo_ws` requires `X-Forwarded-Access-Token` for Databricks calls (Setup & Run, jobs, pipelines).
- **Setup defaults:** `setup.py` uses hardcoded job/pipeline/warehouse IDs; docs state to override via env after deploy. **Recommendation:** Consider resolving job/pipeline IDs from bundle or workspace API so one deploy works across workspaces.
- **Verdict:** Correct for current design; one improvement noted above.

### 4.2 Decisioning
- **Policies:** `decisioning/policies.py` (routing, retry, auth); decision route uses SessionDep (Lakebase) and DatabricksServiceDep (effective UC).
- **ML calls:** Use DatabricksService (model endpoints); mock when unavailable.
- **Verdict:** Correct.

### 4.3 UI
- **Setup & Run:** Fetches `/api/setup/defaults`, runs jobs/pipelines via `/api/setup/run-job`, `/api/setup/run-pipeline`; updates catalog/schema via PATCH `/api/setup/config`.
- **Data fetching:** Uses API client; error handling per project rules.
- **Verdict:** Correct.

### 4.4 Dashboard URLs
- **dashboards.py:** Returns relative paths (e.g. `/sql/dashboards/executive_overview`). Embed URL uses a hardcoded `o=984752964297111`; this is workspace-specific. **Recommendation:** Build embed URL from workspace host (e.g. from config) and omit or set `o` from current workspace context so it works in any workspace.

---

## 5. Summary of Fixes Applied

| File | Change |
|------|--------|
| `src/payment_analysis/transform/gold_views.sql` | Added `approved_count` to `v_approval_trends_hourly` so backend/UI columns match. |
| `src/payment_analysis/transform/gold_views.sql` | Added `approved_count` to `v_solution_performance` for same reason. |

---

## 6. Recommendations (Non-Blocking)

1. **Setup job/pipeline IDs:** After bundle deploy, job and pipeline IDs are workspace-specific. Either document env vars for each (e.g. `DATABRICKS_JOB_ID_SIMULATOR`) or resolve IDs at runtime from workspace/bundle so the app works without manual env after deploy.
2. **Dashboard embed URL:** Replace hardcoded `o=984752964297111` in `get_dashboard_url(..., embed=True)` with workspace ID from config or request context so embed works in any workspace.
3. **Run Create Gold Views:** Ensure the **Create Payment Analysis Gold Views** job is run (or gold_views.sql executed once) in the target catalog/schema so all v_* views exist before using dashboards or app analytics.

---

## 7. Verification

- `uv run apx dev check`: TypeScript and Python type checks passed.
- Ingestion → silver → gold (SQL views) → backend analytics: data flow and naming aligned.
- Catalog/schema: Bundle vars, app_config, and backend effective UC are consistent; agents and ML use the same context.
