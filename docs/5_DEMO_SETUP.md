# 5. Demo Setup — Run End-to-End

One-click links and steps. **Base URL:** Replace `<WORKSPACE_URL>` with your Databricks workspace URL (e.g. `https://adb-984752964297111.11.azuredatabricks.net`).

## Recommended Order

| Order | Step | Description |
|-------|------|-------------|
| 1 | Data ingestion | Generate test payment events |
| 2a | Batch ETL | Raw → Silver/Gold |
| 2b | Real-time pipeline | (Optional) Continuous streaming |
| 3 | Gold views | Create analytical views |
| 4 | Train ML models | 4 models |
| 5 | AI orchestrator | Coordinate agents |
| 6 | Stream processor | (Optional) Always-on stream |

## Quick Links (One-Click)

Replace `<WORKSPACE_URL>` in links below.

| Step | Action | Link |
|------|--------|------|
| 1 | Run Transaction Simulator | `<WORKSPACE_URL>/#job/<JOB_ID>/run` |
| 2a | Open ETL Pipeline | `<WORKSPACE_URL>/pipelines/<PIPELINE_ID>` |
| 2b | Open Real-Time Pipeline | `<WORKSPACE_URL>/pipelines/<PIPELINE_ID>` |
| 3 | Run Gold Views Job | `<WORKSPACE_URL>/#job/<JOB_ID>/run` |
| 4 | Run ML Training Job | `<WORKSPACE_URL>/#job/<JOB_ID>/run` |
| 5 | Run Orchestrator Job | `<WORKSPACE_URL>/#job/<JOB_ID>/run` |
| 6 | Run Stream Processor | `<WORKSPACE_URL>/#job/<JOB_ID>/run` |

**CLI equivalents:** `databricks bundle run <job_name> -t dev` (e.g. `transaction_stream_simulator`, `create_gold_views_job`, `train_ml_models_job`, `orchestrator_agent_job`, `continuous_stream_processor`). Pipelines: `databricks pipelines start-update <pipeline-id>`.

## Deploy First

If not deployed: `databricks bundle deploy -t dev`. Full steps: [1_DEPLOYMENTS](1_DEPLOYMENTS.md).
