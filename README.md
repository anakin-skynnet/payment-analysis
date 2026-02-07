# Payment Analysis

Databricks-powered payment approval optimization: real-time analytics, ML models, and AI agents.

## Overview

**Challenge:** Declined legitimate transactions mean lost revenue — false declines, static rules, suboptimal routing.

**Solution:** Real-time ML per transaction, smart routing, intelligent retry, 7 AI agents, Genie. Data flow: simulator → Lakeflow (Bronze → Silver → Gold) → Unity Catalog → FastAPI + React app.

| Initiative | Scope | Deliverables |
|------------|--------|--------------|
| Smart Checkout | Payment links, Brazil | 3DS funnel, antifraud attribution |
| Reason Codes | E-commerce, Brazil | Consolidated declines, unified taxonomy |
| Smart Retry | Brazil | Reattempt success rate, effectiveness |

**AI agents (7):** Genie (2), Model Serving (3), Mosaic AI Gateway (2). See [Deployment guide](docs/DEPLOYMENT_GUIDE.md) and [Architecture & reference](docs/ARCHITECTURE_REFERENCE.md).

## Documentation

| Document | Purpose |
|----------|---------|
| [Deployment guide](docs/DEPLOYMENT_GUIDE.md) | Deploy steps, app config, env vars, troubleshooting, scripts |
| [Architecture & reference](docs/ARCHITECTURE_REFERENCE.md) | Architecture, data flow, bundle resources, app compliance |

## Quick start

1. **Deploy:** `./scripts/bundle.sh deploy dev`
2. **Pipeline:** App **Setup & Run** (steps 2–6): ingestion → ETL → gold views → Lakehouse SQL → ML training → agents.
3. **App:** **Workspace → Apps**; set `PGAPPNAME`, `DATABRICKS_HOST`, `DATABRICKS_WAREHOUSE_ID`, `DATABRICKS_TOKEN` in app environment.

See [Deployment guide](docs/DEPLOYMENT_GUIDE.md) for details.
