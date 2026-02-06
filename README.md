# Payment Analysis

Databricks-powered payment approval optimization: real-time analytics, ML models, and AI agents.

## Documentation

| Doc | Audience | Description |
|-----|----------|-------------|
| [0. Business Challenges](docs/0_BUSINESS_CHALLENGES.md) | C-Suite / Business | Challenges, solution, initiatives, ROI |
| [1. Deployments](docs/1_DEPLOYMENTS.md) | Everyone | Deploy, run steps, **one-click run links**, troubleshooting |
| [3. Agents & Value](docs/3_AGENTS_VALUE.md) | ML / Data Science | 7 AI agents and business value |
| [4. Technical](docs/4_TECHNICAL.md) | Engineers / Architects | Architecture, data flow, bundle & deployment, stack |

## Quick Start

1. **Deploy:** `./scripts/bundle.sh deploy dev` (prepares dashboards, then deploys; or `./scripts/bundle.sh validate dev` then `databricks bundle deploy -t dev`)
2. **Run pipeline:** Use app **Setup & Run** (steps 2–6) or [1_DEPLOYMENTS](docs/1_DEPLOYMENTS.md#demo-setup--one-click-run): data ingestion → ETL → gold views → Lakehouse SQL → ML training → agents.
3. **App:** `uv sync && bun install` then `uv run apx dev` (set `.env` for Databricks).

See [4_TECHNICAL](docs/4_TECHNICAL.md) (Bundle & Deploy) and [1_DEPLOYMENTS](docs/1_DEPLOYMENTS.md) for variables, commands, and one-click run links.

## App URL

- **Local:** After `uv run apx dev`, open **http://localhost:8000** (backend serves the app and API at `/api`).
- **Databricks Apps:** If you deploy the app as a Databricks App, the URL is shown in the Apps UI (e.g. `https://<workspace>/apps/<app-id>`).
