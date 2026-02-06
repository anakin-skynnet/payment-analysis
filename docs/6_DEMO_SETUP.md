# 6. Demo Setup — Run End-to-End

One-click links and short steps to run the Payment Analysis solution.

**Base URL:** `https://adb-984752964297111.11.azuredatabricks.net` (replace with your workspace if different)

---

## Recommended order

| Order | Step | Description |
|-------|------|-------------|
| 1 | [Data ingestion](#1-data-ingestion) | Generate test payment events |
| 2a | [Batch ETL](#2a-batch-etl-pipeline) | Process raw → Silver/Gold |
| 2b | [Real-time pipeline](#2b-real-time-pipeline-optional) | *(Optional)* Continuous streaming |
| 3 | [Gold views](#3-create-gold-views) | Create analytical views |
| 4 | [Train ML models](#4-train-ml-models) | Train 4 models |
| 5 | [AI orchestrator](#5-run-ai-orchestrator) | Coordinate AI agents |
| 6 | [Stream processor](#6-continuous-stream-processor-optional) | *(Optional)* Always-on stream |

---

## Quick links (one-click)

| Step | Action | Link |
|------|--------|------|
| 1. Data ingestion | Run Transaction Simulator | [Run job](https://adb-984752964297111.11.azuredatabricks.net/#job/782493643247677/run) |
| 2a. Batch ETL | Open ETL Pipeline | [Open pipeline](https://adb-984752964297111.11.azuredatabricks.net/pipelines/eb4edb4a-0069-4208-9261-2151f4bf33d9) |
| 2b. Real-time | Open Real-Time Pipeline | [Open pipeline](https://adb-984752964297111.11.azuredatabricks.net/pipelines/0ef506fd-d386-4581-a609-57fb9a23291c) |
| 3. Gold views | Run Gold Views Job | [Run job](https://adb-984752964297111.11.azuredatabricks.net/#job/775632375108394/run) |
| 4. Train ML | Run ML Training Job | [Run job](https://adb-984752964297111.11.azuredatabricks.net/#job/231255282351595/run) |
| 5. AI orchestrator | Run Orchestrator Job | [Run job](https://adb-984752964297111.11.azuredatabricks.net/#job/582671124403091/run) |
| 6. Stream processor | Run Continuous Stream Processor | [Run job](https://adb-984752964297111.11.azuredatabricks.net/#job/1124715161556931/run) |

Job links with `/run` open the “Run now” flow. Pipeline links open the pipeline; use **Start** or **Run update** there.

---

## Steps in detail

### 1. Data ingestion

Generate synthetic payment data (~1000 events/s).

- **One-click:** [Run Transaction Simulator](https://adb-984752964297111.11.azuredatabricks.net/#job/782493643247677/run)  
- **CLI:** `databricks bundle run transaction_stream_simulator -t dev`  
Let it run a few minutes to populate Bronze.

### 2a. Batch ETL pipeline

Bronze → Silver → Gold.

- **One-click:** [Open ETL Pipeline](https://adb-984752964297111.11.azuredatabricks.net/pipelines/eb4edb4a-0069-4208-9261-2151f4bf33d9) → Start / Run update  
- **CLI:** `databricks pipelines start-update eb4edb4a-0069-4208-9261-2151f4bf33d9`  
Wait for the run to complete before creating gold views.

### 2b. Real-time pipeline (optional)

- **One-click:** [Open Real-Time Pipeline](https://adb-984752964297111.11.azuredatabricks.net/pipelines/0ef506fd-d386-4581-a609-57fb9a23291c) → Start

### 3. Create gold views

- **One-click:** [Run Gold Views Job](https://adb-984752964297111.11.azuredatabricks.net/#job/775632375108394/run)  
- **CLI:** `databricks bundle run create_gold_views_job -t dev`

### 4. Train ML models

- **One-click:** [Run ML Training Job](https://adb-984752964297111.11.azuredatabricks.net/#job/231255282351595/run)  
- **CLI:** `databricks bundle run train_ml_models_job -t dev`

### 5. Run AI orchestrator

- **One-click:** [Run Orchestrator Job](https://adb-984752964297111.11.azuredatabricks.net/#job/582671124403091/run)  
- **CLI:** `databricks bundle run orchestrator_agent_job -t dev`

### 6. Continuous stream processor (optional)

- **One-click:** [Run Continuous Stream Processor](https://adb-984752964297111.11.azuredatabricks.net/#job/1124715161556931/run)  
- **CLI:** `databricks bundle run continuous_stream_processor -t dev`

---

## Useful links

| Resource | Link |
|----------|------|
| SQL Warehouse | [Open warehouse](https://adb-984752964297111.11.azuredatabricks.net/sql/warehouses/bf12ee0011ea4ced) |
| Unity Catalog schema | [Explore data](https://adb-984752964297111.11.azuredatabricks.net/explore/data/ahs_demos_catalog/ahs_demo_payment_analysis_dev) |

---

## Deploy before running

If resources are not deployed yet:

```bash
databricks bundle deploy -t dev
```

Full deployment and configuration: [1_DEPLOYMENTS](1_DEPLOYMENTS.md).
