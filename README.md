# Payment Analysis

Databricks-powered payment approval optimization: real-time analytics, ML models, and AI agents.

## Overview

**Challenge:** Declined legitimate transactions mean lost revenue — false declines, static rules, suboptimal routing, manual analysis.

**Solution:** Real-time ML per transaction, smart routing, intelligent retry, 7 AI agents, Genie for natural-language analytics. Data flow: simulator → Lakeflow (Bronze → Silver → Gold) → Unity Catalog → FastAPI + React app.

| Initiative | Scope | Deliverables |
|------------|--------|--------------|
| Smart Checkout | Payment links, Brazil | Service-path breakdown, 3DS funnel, antifraud attribution |
| Reason Codes | E-commerce, Brazil | Consolidated declines, unified taxonomy, insights |
| Smart Retry | Brazil | Recurrence vs reattempt, success rate, effectiveness |

**AI agents (7):** Genie (2), Model Serving (3), Mosaic AI Gateway (2) — approval propensity, smart routing, retry optimizer, payment intelligence, risk advisor. See [Deployment](docs/DEPLOYMENT.md) for setup and [Technical](docs/TECHNICAL.md) for architecture.

## Documentation

| Doc | Description |
|-----|-------------|
| [Deployment](docs/DEPLOYMENT.md) | Deploy steps, app config, env vars, one-click run, troubleshooting |
| [Technical](docs/TECHNICAL.md) | Architecture, data flow, bundle resources, app compatibility |

## Quick Start

1. **Deploy:** `./scripts/bundle.sh deploy dev`
2. **Pipeline:** Use app **Setup & Run** (steps 2–6): data ingestion → ETL → gold views → Lakehouse SQL → ML training → agents.
3. **App:** **Workspace → Apps**; set `PGAPPNAME`, `DATABRICKS_HOST`, `DATABRICKS_WAREHOUSE_ID`, `DATABRICKS_TOKEN` in app environment.

See [Deployment](docs/DEPLOYMENT.md) and [Technical](docs/TECHNICAL.md) for details.
