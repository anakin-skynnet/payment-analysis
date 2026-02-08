# Deep Review: Apps Cookbook, APX, and AI Dev Kit Alignment

This document reviews the **payment-analysis** project against:

1. **[Databricks Apps Cookbook](https://apps-cookbook.dev/docs/intro)** – FastAPI patterns, API structure, and Databricks Apps runtime  
   - [Create a FastAPI app](https://apps-cookbook.dev/docs/fastapi/getting_started/create): `/api` prefix for OAuth, versioned routes, healthcheck at `/api/v1/healthcheck`  
   - [Connect FastAPI to Lakebase](https://apps-cookbook.dev/docs/fastapi/getting_started/lakebase_connection): Postgres via instance name, `WorkspaceClient.database.get_database_instance()` and `generate_database_credential()`
2. **[apx](https://github.com/databricks-solutions/apx)** – Toolkit for building Databricks Apps (React + FastAPI, dev server, OpenAPI, MCP)
3. **[AI Dev Kit](https://github.com/databricks-solutions/ai-dev-kit)** – Skills and MCP tools for Databricks (pipelines, jobs, dashboards, UC, Genie, apps)

It also checks alignment with **previous prompts** captured in `.cursor/rules/project.mdc` and `.claude/skills/apx/SKILL.md`.

---

## 1. Apps Cookbook – What It Defines

### 1.1 Intro

- **Purpose:** Code snippets for building interactive data and AI applications on **Databricks Apps**.
- **Use cases:** Tables, volumes, ML models, GenAI, workflows.
- **Frameworks:** Streamlit, Dash, **FastAPI**, Reflex.

### 1.2 FastAPI – Create App

- **Structure:** `app.py` (entrypoint), `app.yaml` (deployment), `routes/` with versioned API (e.g. `routes/v1/healthcheck.py`).
- **Critical rule:** *“In order to use OAuth2 Bearer token authentication with Databricks Apps, your application code must provide valid routes with a **prefix of `/api`.**”*
- **Example:** Healthcheck at `https://<app-url>/api/v1/healthcheck`.
- **Running:** `uvicorn app:app` (locally); for Apps runtime, `command: ["uvicorn", "app:app"]` in `app.yaml`.
- **Dependencies:** FastAPI, uvicorn (and optionally in other recipes: databricks-sdk, databricks-sql-connector).

### 1.3 FastAPI – Read Table

- **Pattern:** GET endpoint under `/api` (e.g. `/api/v1/table`), Databricks SQL Connector + `Config()` from SDK.
- **Permissions:** SELECT on UC table, CAN USE on SQL warehouse.
- **Dependencies:** databricks-sdk, databricks-sql-connector, fastapi, uvicorn.

---

## 2. APX – What It Defines

- **Role:** Toolkit for **building Databricks Apps** (develop, build, deploy).
- **Stack:** **FastAPI** (backend), **React** + **TypeScript** + **shadcn/ui** + **Vite** + **Bun**, **uv** (Python).
- **Features:** Dev server, OpenAPI/client generation, MCP server, component CLI.
- **Project layout:** Backend (e.g. `app.py`, router, models, config), frontend (components, routes, lib).
- **Quickstart:** `uvx --index https://databricks-solutions.github.io/apx/simple apx init`.
- **Upgrade:** `uv sync --upgrade-package apx --index https://databricks-solutions.github.io/apx/simple`.

---

## 3. AI Dev Kit – What It Defines

- **Role:** Teach AI assistants (Cursor, Claude Code, etc.) **Databricks patterns** and provide **MCP tools**.
- **Covers:** Spark pipelines, Jobs, AI/BI Dashboards, Unity Catalog, Genie, Knowledge Assistants, MLflow, Model Serving, **Databricks Apps**.
- **Delivery:** Skills (markdown), MCP server (50+ tools), optional starter project / builder app.
- **Relationship to this repo:** **Complementary.** AI Dev Kit does not dictate app structure; it provides skills/tools that can be used while building an app (e.g. with apx).

---

## 4. Project Rules (Previous Prompts) – Summary

From `.cursor/rules/project.mdc` and `.claude/skills/apx/SKILL.md`:

| Area | Rule |
|------|------|
| **Structure** | Full-stack: `src/payment_analysis/ui/` (React + Vite), `src/payment_analysis/backend/` (FastAPI). Backend serves frontend at `/`, API at `/api`. |
| **OpenAPI** | Client auto-generated from OpenAPI; don’t manually regenerate when dev servers run. |
| **Package** | Python: **uv** only. Frontend: **bun** via `uv run apx bun install` / `uv run apx bun add`. |
| **Components** | shadcn/ui; add via MCP `add_component` or `uv run apx components add`; store under `src/payment_analysis/ui/components/`. |
| **API** | **3-model pattern:** Entity (DB), EntityIn (input), EntityOut (output). Routes must have **response_model** and **operation_id** for client generation. |
| **Frontend** | **Routing:** @tanstack/react-router (routes in `src/payment_analysis/ui/routes/`). **Data:** use **useXSuspense** hooks with **Suspense** and **Skeleton**. **Data access:** use **selector()** for destructuring. |
| **Dev** | `uv run apx dev check` for errors; `uv run apx build` for production. **Deploy:** run `uv run python scripts/dashboards.py prepare` before any `databricks bundle` (validate/deploy) so `.build/dashboards/*.lvdash.json` exist. |
| **Databricks** | Use apx MCP `docs` for SDK; use latest features/naming. |

---

## 5. Alignment Checklist

### 5.1 Apps Cookbook

| Requirement | Status | Notes |
|-------------|--------|--------|
| API prefix `/api` for OAuth | ✅ | `api = APIRouter(prefix=_api_prefix)` with `_api_prefix = "/api"` from `_metadata` (pyproject: `api-prefix = "/api"`). |
| Versioned routes under `/api/v1` | ✅ | `api.include_router(v1_router, prefix="/v1")` → `/api/v1/*`. |
| Healthcheck at `/api/v1/healthcheck` | ✅ | `v1/healthcheck.py`: `@router.get("/healthcheck")` → `/api/v1/healthcheck`. |
| FastAPI + uvicorn | ✅ | `app.py` uses FastAPI; `app.yml` / `resources/fastapi_app.yml` run `uvicorn payment_analysis.backend.app:app --host 0.0.0.0 --port 8000`. |
| app.yaml / app.yml for Apps runtime | ✅ | Root `app.yml` with `command` and `env` (PYTHONPATH, PGAPPNAME); bundle app resource in `resources/fastapi_app.yml`. |
| Dependencies (fastapi, uvicorn) | ✅ | In `pyproject.toml`: fastapi, uvicorn. |
| Databricks SDK usage | ✅ | Backend uses `databricks.sdk` (WorkspaceClient, Config, etc.); SQL/warehouse usage via services. |

- **operation_id and response_model:** The v1 health endpoints (`/healthcheck`, `/health/database`) **have** `response_model` and `operation_id` (`healthcheck`, `healthDatabase`), so they align with project rules and OpenAPI client generation.

### 5.2 APX

| Requirement | Status | Notes |
|-------------|--------|--------|
| FastAPI backend | ✅ | `src/payment_analysis/backend/app.py`, router, routes. |
| React + TypeScript + Vite | ✅ | `src/payment_analysis/ui/` with Vite, TS, React. |
| shadcn/ui | ✅ | Components under `ui/components/ui/` and `ui/components/apx/`. |
| uv for Python | ✅ | `pyproject.toml`, `uv.lock`; rules say “always use uv”. |
| Bun for frontend | ✅ | `package.json`, `bun.lock`; rules say use `uv run apx bun install` etc. |
| OpenAPI client generation | ✅ | `lib/api.ts` generated from OpenAPI; apx metadata in `pyproject.toml` (`api-prefix`, `app-entrypoint`, etc.). |
| Project layout (backend + ui) | ✅ | `src/payment_analysis/backend/` and `src/payment_analysis/ui/` with components, routes, lib. |
| Build command | ✅ | `uv run apx build`; produces wheel and frontend dist. |
| Dev commands (check, start, etc.) | ✅ | Documented in rules and apx skill; `uv run apx dev check` used for validation. |

### 5.3 AI Dev Kit

| Aspect | Status | Notes |
|--------|--------|------|
| Databricks Apps as a use case | ✅ | AI Dev Kit lists “Databricks Apps (full-stack web applications)”; this project is one. |
| No structural conflict | ✅ | AI Dev Kit does not impose app layout; skills/MCP complement development. |
| Optional use of skills/MCP | ✅ | Project can use ai-dev-kit skills and MCP for Databricks operations (jobs, dashboards, UC, etc.) while keeping apx-based app structure. |

### 5.4 Project Rules (Previous Prompts)

| Rule | Status | Notes |
|------|--------|-------|
| API at `/api`, frontend at `/` | ✅ | Router prefix `/api`; static UI mounted at `/` when dist present. |
| 3-model pattern (Entity, EntityIn, EntityOut) | ✅ | Used in backend (e.g. rules, experiments, incidents, analytics). |
| response_model + operation_id on routes | ✅ | All routes have both; v1 healthcheck and health/database use `HealthcheckOut`/`HealthDatabaseOut` and `operation_id="healthcheck"` / `operation_id="healthDatabase"`. |
| useXSuspense + Suspense + Skeleton | ✅ | e.g. dashboard.tsx, profile.tsx use `useGetKpisSuspense`, `useCurrentUserSuspense`, etc., with `Suspense` and `DashboardSkeleton`/`ProfileSkeleton`. |
| selector() for data | ✅ | e.g. `useGetKpisSuspense(selector())`, `useCurrentUserSuspense(selector())`. |
| Components under `src/payment_analysis/ui/components/` | ✅ | ui/components/apx, ui/components/ui, etc. |
| uv for Python, apx bun for frontend | ✅ | No pip; frontend deps via bun. |
| Dashboard prepare before bundle deploy | ✅ | Documented in rules and DEPLOYMENT_GUIDE; `scripts/dashboards.py prepare` populates `.build/dashboards/`. |

---

## 6. Gaps and Recommendations

### 6.1 Deep reasoning: previous prompts and behaviour

Requirements from earlier prompts and their implementation:

| Requirement | Implementation |
|-------------|----------------|
| OAuth / token from Compute → Apps | `_get_obo_token(request)` reads `X-Forwarded-Access-Token` / `x-forwarded-access-token`; used by `get_workspace_client`, `get_databricks_service`, setup config. |
| No OAuth scope error (PAT/OBO) | `workspace_client_pat_only(host, token)` unsets `DATABRICKS_CLIENT_ID`/`SECRET` when creating `WorkspaceClient`; used in dependencies, runtime, `DatabricksService`. |
| Workspace URL when opened from Apps | `workspace_url_from_apps_host(host, app_name)` in `config.py`; used in router, dependencies, setup. |
| DATABRICKS_HOST optional when from Apps | `_effective_databricks_host(request, bootstrap_host)` in `get_databricks_service` and setup PATCH /config. |
| Execute (open in Databricks) not Run from UI | Single **Execute** button per step; opens job/pipeline in Databricks; no UI call to run-job/run-pipeline. |
| Lakebase connection (Cookbook) | `Runtime`: `get_database_instance`, `generate_database_credential()`; instance from `PGAPPNAME`. |
| Exact dependency versions | `package.json` exact; `pyproject.toml` uses `==`. |

v1 health routes already have `operation_id` and `response_model` (no gap).

### 6.2 No other structural or “must-fix” gaps

- Cookbook: API prefix, versioning, healthcheck, Lakebase, uvicorn, and app config are correct.
- APX: Stack, layout, build, and dev workflow match.
- AI Dev Kit: Complementary; no conflict.
- Previous prompts: All requirements (OBO token, Execute button, env vars, workspace derivation, PAT-only client, v1 health operation_id/response_model) are implemented.

---

## 7. Conclusion

- **Apps Cookbook:** The project follows the cookbook’s FastAPI and Databricks Apps patterns (API under `/api`, `/api/v1/healthcheck`, uvicorn, app.yml).  
- **APX:** The project is an apx-style app (FastAPI + React + TypeScript + shadcn/ui + Vite, uv, OpenAPI client, correct layout and commands).  
- **AI Dev Kit:** Used as a complementary set of skills and MCP tools; no structural mismatch.  
- **Previous prompts:** Fully aligned; OBO token, Execute button, optional env when from Apps, workspace derivation, PAT-only client, and v1 health operation_id/response_model are all in place.

**Verdict:** The project is **correctly defined** relative to the [Apps Cookbook](https://apps-cookbook.dev/docs/intro), [apx](https://github.com/databricks-solutions/apx), and [AI Dev Kit](https://github.com/databricks-solutions/ai-dev-kit), and to the prior rules. No mandatory changes.
