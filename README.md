# Payment Approval Optimization Platform

A Databricks-powered solution that maximizes payment approval rates through real-time analytics, machine learning, and AI-driven recommendations.

---

## Documentation

| Document | Audience | Description |
|----------|----------|-------------|
| [0. Business Challenges](docs/0_BUSINESS_CHALLENGES.md) | **C-Suite / Business** | Business challenge, solution, capabilities, ROI |
| [1. Deployments](docs/1_DEPLOYMENTS.md) | **DevOps / Engineering** | **Step-by-step deployment and validation** (START HERE) |
| [2. Data Flow](docs/2_DATA_FLOW.md) | **Data Engineers** | 5-stage flow from ingestion to insight |
| [3. Agents & Value](docs/3_AGENTS_VALUE.md) | **ML / Data Science** | 7 AI agents and business value |
| [5. Technical](docs/5_TECHNICAL.md) | **Engineers / Architects** | Architecture, stack, implementation |
| [6. Demo Setup](docs/6_DEMO_SETUP.md) | **Everyone** | **One-click links to run the solution end-to-end** |

---

## Quick Start

```bash
# Install dependencies
uv sync && bun install

# Validate bundle
databricks bundle validate

# Deploy to development
databricks bundle deploy --target dev

# Run locally
uv run apx dev
```

---

## Architecture

```
Transactions ──▶ DLT Pipeline ──▶ ML Models ──▶ AI Agents ──▶ Web App
                      │                             │
                      ▼                             ▼
                 Gold Views ──────────────▶ Dashboards & Genie
```

---

## Key Features

- **Real-Time Processing**: 1000+ transactions/second with sub-second latency
- **Smart Routing**: ML-driven processor selection
- **Smart Retry**: Automated recovery for soft declines
- **AI Agents**: 7 specialized agents (Genie, Model Serving, AI Gateway) for continuous optimization
- **Self-Service Analytics**: Dashboards + natural language queries (Genie)

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Data | Delta Lake, Unity Catalog, DLT |
| ML | MLflow, Model Serving |
| AI | Databricks Agents, Llama 3.1 |
| Backend | FastAPI, SQLModel |
| Frontend | React, Vite, TanStack Router |
| Deploy | Databricks Asset Bundles |
