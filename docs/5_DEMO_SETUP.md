# 5. Demo Setup — Run End-to-End

One-click links and steps. **Base URL:** Replace `<WORKSPACE_URL>` with your Databricks workspace URL (e.g. `https://adb-984752964297111.11.azuredatabricks.net`).

## Recommended order (matches app **Setup & Run**)

| Order | Step | Description |
|-------|------|-------------|
| 1 | Deploy bundle | `databricks bundle deploy -t dev` — [1_DEPLOYMENTS](1_DEPLOYMENTS.md) |
| 2 | Data ingestion | Run Transaction Stream Simulator |
| 3 | ETL (Lakeflow) | Start Payment Analysis ETL pipeline (Bronze → Silver → Gold) |
| 4 | Gold views | Run Create Payment Analysis Gold Views job |
| 5 | Lakehouse (SQL) | In SQL Warehouse run in order: `app_config.sql`, `vector_search_and_recommendations.sql`, `approval_rules.sql`, `online_features.sql` (see `src/payment_analysis/transform/`) |
| 6 | Train ML models | Run Train Payment Approval ML Models (~10–15 min) |
| 7 | (Optional) Real-time | Start real-time Lakeflow pipeline or stream processor |
| 8 | (Optional) AI agents | Run Orchestrator or other agent jobs |

## Quick links (one-click)

Replace `<WORKSPACE_URL>` with your workspace URL. After deploy, get job IDs from **Workflows** and pipeline IDs from **Lakeflow** (names prefixed with `[dev ...]`).

| Step | Action | Link |
|------|--------|------|
| 2 | Run Transaction Simulator | `<WORKSPACE_URL>/#job/<JOB_ID>/run` |
| 3 | Open ETL Pipeline | `<WORKSPACE_URL>/pipelines/<PIPELINE_ID>` |
| 4 | Run Gold Views Job | `<WORKSPACE_URL>/#job/<JOB_ID>/run` |
| 5 | Open SQL Warehouse / run Lakehouse scripts | `<WORKSPACE_URL>/sql/warehouses` then run scripts from `transform/` |
| 6 | Run ML Training Job | `<WORKSPACE_URL>/#job/<JOB_ID>/run` |
| 8 | Run Orchestrator Job | `<WORKSPACE_URL>/#job/<JOB_ID>/run` |
| (Optional) | Open Real-Time Pipeline | `<WORKSPACE_URL>/pipelines/<PIPELINE_ID>` |
| (Optional) | Run Stream Processor | `<WORKSPACE_URL>/#job/<JOB_ID>/run` |

**CLI:** `databricks bundle run <job_name> -t dev` (e.g. `transaction_stream_simulator`, `create_gold_views_job`, `train_ml_models_job`, `orchestrator_agent_job`, `continuous_stream_processor`). Pipelines: `databricks pipelines start-update <pipeline-id>`.

## Deploy first

If not deployed: `databricks bundle deploy -t dev`. Full steps: [1_DEPLOYMENTS](1_DEPLOYMENTS.md).
