# Code Guidelines and Data Sources

This document aligns the payment-analysis app with Databricks Apps best practices and confirms that **all data and AI are fetched from Databricks** when the workspace connection is available.

## Reference Guidelines

- **[Databricks Apps Cookbook](https://apps-cookbook.dev/docs/intro)**  
  Ready-to-use patterns for reading/writing tables and volumes, invoking ML/GenAI, and triggering workflows from FastAPI/Streamlit/Dash. Our backend follows the FastAPI + Unity Catalog pattern for data reads.

- **[apx](https://github.com/databricks-solutions/apx)**  
  Toolkit for building Databricks Apps (FastAPI + React, Pydantic, Databricks SDK, uv). This project uses apx for init, build, and dev tooling.

- **[AI Dev Kit](https://github.com/databricks-solutions/ai-dev-kit)**  
  Patterns for Spark pipelines, Jobs, AI/BI Dashboards, Genie, MLflow, Model Serving, and Databricks Apps. Our agents and ML inference use Databricks Model Serving and Unity Catalog.

- **[dbdemos](https://github.com/databricks-demos/dbdemos)**  
  Lakehouse demos and packaging patterns. Our bundle and dashboard deployment align with Databricks Asset Bundles and DBSQL dashboards.

## Data and AI Source: Databricks-First

When the app is run from **Compute → Apps** (or with `DATABRICKS_HOST` and a valid token), all analytics and AI flows use Databricks:

| Area | Primary source | Fallback when Databricks unavailable |
|------|----------------|--------------------------------------|
| **Analytics (KPIs, trends, reason codes, etc.)** | Unity Catalog views via SQL Warehouse (Statement Execution API) | Mock data for development; `/kpis` also falls back to local DB counts |
| **ML inference (approval, risk, routing)** | Databricks Model Serving endpoints | Mock predictions |
| **Recommendations / Vector Search** | Unity Catalog tables + Vector Search / Lakehouse | Mock recommendations |
| **Online features** | Lakebase or Lakehouse feature tables | Mock features |
| **Rules (approval rules)** | Lakebase/Lakehouse or UC | Local DB / error when not available |
| **Agents list** | Workspace (Mosaic AI Gateway, Genie, UC models) | N/A (links to workspace) |
| **Dashboards** | DBSQL dashboards in workspace (embed URLs) | N/A |
| **Jobs / Pipelines** | Databricks Jobs & Pipelines APIs (run, open in workspace) | N/A |

### Unity Catalog views used by analytics

All of these are queried via `DatabricksService.execute_query()` against the configured catalog and schema (e.g. `ahs_demos_catalog.payment_analysis`):

- `v_executive_kpis` — KPIs and Databricks KPIs
- `v_approval_trends_hourly` — approval trends
- `v_solution_performance` — solution performance
- `v_top_decline_reasons` — decline summary
- `v_smart_checkout_*`, `v_3ds_funnel_br`, `v_reason_codes_br`, `v_reason_code_insights_br`, `v_entry_system_distribution_br`
- `v_dedup_collision_stats`, `v_false_insights_metric`, `v_retry_performance`
- Country and recommendation tables as defined in `databricks_service.py`

### AI / ML sources

- **Model Serving**: approval propensity, risk scoring, smart routing (UC-registered models or serving endpoints).
- **Genie / Mosaic AI Gateway**: linked from the UI; chat and natural language run in the workspace.
- **Agents**: listed from workspace config; open in Databricks.

## Validation

- **Programmatic**: `GET /api/v1/health/databricks` returns whether the Databricks connection is available and the effective data source for analytics and ML. Use it to validate that the app is using Databricks in your environment.
- **Docs**: This file and the inline docstrings in `backend/services/databricks_service.py` and `backend/routes/analytics.py` describe the Databricks-first behavior and fallbacks.

## Implementation notes

- **SQL execution**: We use the **Databricks SDK** `statement_execution.execute_statement()` (not the legacy SQL Connector). This matches the cookbook idea of “query Unity Catalog from FastAPI” and works with serverless SQL.
- **Auth**: When the app is opened from Compute → Apps, the token is forwarded via `X-Forwarded-Access-Token`; the SDK uses it for warehouse and UC access.
- **Fallbacks**: Mock data and local DB fallbacks exist only for development or when the Databricks connection is missing or fails; they are not used when the connection is healthy.
