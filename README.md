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
3. **App:** Deploy as a Databricks App; open the app from **Workspace → Apps**. The URL is shown in the Apps UI (e.g. `https://<workspace>/apps/<app-id>`).

See [4_TECHNICAL](docs/4_TECHNICAL.md) (Bundle & Deploy) and [1_DEPLOYMENTS](docs/1_DEPLOYMENTS.md) for variables, commands, and one-click run links.
