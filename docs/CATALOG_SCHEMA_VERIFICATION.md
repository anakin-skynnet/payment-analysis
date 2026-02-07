# Catalog and Schema Verification

All references to catalog and schema use the correct source for the deployment context.

## Single source of truth

- **Bundle (jobs, pipelines, UC, dashboards):** `databricks.yml` variables `var.catalog` and `var.schema`.
  - Defaults: `ahs_demos_catalog`, `ahs_demo_payment_analysis_dev`.
  - Prod target: `catalog: prod_catalog`, `schema: ahs_demo_payment_analysis_prod`.

- **Backend / app runtime:** `DATABRICKS_CATALOG` and `DATABRICKS_SCHEMA` (env) or the `app_config` table (effective catalog/schema used by the app).

---

## Verified by category

### Bundle resources (use `${var.catalog}` / `${var.schema}`)

| File | Status |
|------|--------|
| `databricks.yml` | Variables with defaults; prod overrides |
| `resources/unity_catalog.yml` | `catalog_name: ${var.catalog}`, `schema_name: ${var.schema}` |
| `resources/pipelines.yml` | `catalog: ${var.catalog}`, `schema: ${var.schema}` |
| `resources/ml_jobs.yml` | `base_parameters`: catalog, schema from vars |
| `resources/agents.yml` | All jobs: catalog, schema from vars |
| `resources/streaming_simulator.yml` | catalog, schema, checkpoint path from vars |
| `resources/genie_spaces.yml` | base_parameters from vars |
| `resources/model_serving.yml` | entity_name and config use `${var.catalog}.${var.schema}` |
| `resources/vector_search.yml` | Uses `${var.catalog}.${var.schema}` |
| `resources/app.yml` | uc_securable uses `${var.catalog}.${var.schema}.reports` (when uncommented) |

### Dashboards

| File | Status |
|------|--------|
| `resources/dashboards/*.lvdash.json` | Template string `ahs_demos_catalog.ahs_demo_payment_analysis_dev`; **replaced at deploy** by `scripts/dashboards.py prepare` with target catalog.schema |
| `scripts/dashboards.py` | `DEV_CATALOG_SCHEMA` matches bundle default; prepare args from env or CLI (bundle.sh passes for prod) |
| `scripts/bundle.sh` | Dev: prepare with no args (script defaults). Prod: `--catalog prod_catalog --schema ahs_demo_payment_analysis_prod` |

### Notebooks (job parameters override defaults)

| File | Status |
|------|--------|
| `src/.../genie/sync_genie_space.py` | Widget defaults = bundle dev default; job passes `base_parameters` from vars |
| `src/.../ml/train_models.py` | Same |
| `src/.../streaming/transaction_simulator.py` | Same |
| `src/.../streaming/continuous_processor.py` | Same |
| `src/.../agents/agent_framework.py` | Same |

### Backend

| File | Status |
|------|--------|
| `backend/services/databricks_service.py` | `DatabricksConfig` default and `from_env()` use `DATABRICKS_CATALOG` / `DATABRICKS_SCHEMA` with fallback to dev default |
| `backend/routes/setup.py` | Defaults from env; effective config from `app_config` table |
| `backend/routes/agents.py` | `_effective_uc()` from app state (app_config) or dev default; `_apply_uc_config()` replaces default prefix in agent URLs/resources |
| `backend/app.py` | Bootstrap from app_config table or env; stores in `app.state.uc_config` |
| `backend/dependencies.py` | DatabricksService uses `uc_config` or bootstrap |

### SQL / transform

| File | Status |
|------|--------|
| `src/.../transform/app_config.sql` | Seed uses `CURRENT_CATALOG()` and `CURRENT_SCHEMA()` (no hardcoded catalog/schema) |
| `src/.../transform/gold_views.sql` | No hardcoded catalog/schema; run via job with `.build/transform/gold_views.sql` which has `USE CATALOG/Schema` from prepare |

### UI

| File | Status |
|------|--------|
| `src/.../ui/routes/_sidebar/setup.tsx` | Placeholder text only; actual values from API (app_config) |

### Docs

| File | Status |
|------|--------|
| `docs/1_DEPLOYMENTS.md`, `docs/4_TECHNICAL.md` | Document default catalog/schema; no code path |

---

## Summary

- **Jobs and pipelines:** Use bundle variables; correct for the active target.
- **Dashboards:** Template in repo; prepared with target catalog.schema before deploy.
- **Notebooks:** Receive catalog/schema from job `base_parameters` (bundle vars); widget defaults match dev.
- **Backend:** Uses env and `app_config` table; fallbacks match bundle dev default.
- **app_config seed:** Uses current SQL context (`CURRENT_CATALOG()` / `CURRENT_SCHEMA()`).

No changes required; all references are consistent with the chosen catalog and schema for each context.

---

## Intentional hardcoded strings

These are **defaults or templates**, not bugs:

- **`databricks.yml`** – Variable defaults (single source of truth for bundle).
- **`scripts/dashboards.py`** – Default catalog/schema for prepare; matches bundle. Dashboard JSONs use the same string as the **template** that prepare replaces with the target `catalog.schema`.
- **Notebooks** – Widget defaults match dev; jobs pass `base_parameters` from `${var.catalog}` / `${var.schema}`, so the actual run uses the target.
- **Backend** (`databricks_service.py`, `setup.py`, `agents.py`) – Fallbacks and `_DEFAULT_UC_PREFIX` match bundle dev; runtime uses env and `app_config` (and agents use `_apply_uc_config()` to rewrite default-prefix URLs to the effective catalog/schema).
- **UI** (`setup.tsx`) – Placeholder text only; values come from the API.
