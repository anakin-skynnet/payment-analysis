# Deep reasoning: alignment with Apps Cookbook, APX, and AI Dev Kit

This document reviews how the **payment-analysis** app aligns with:

- **[Databricks Apps Cookbook](https://apps-cookbook.dev/docs/intro)** – patterns for FastAPI/Streamlit apps, auth, and Databricks Apps runtime
- **[apx](https://github.com/databricks-solutions/apx)** – toolkit for building Databricks Apps (structure, CLI, build, deploy)
- **[AI Dev Kit](https://github.com/databricks-solutions/ai-dev-kit)** – skills, MCP tools, and Databricks development patterns

It also checks that the implementation matches the **previous prompts** (token propagation, Setup Execute/Run now, workspace URL derivation, OBO).

---

## 1. Apps Cookbook alignment

### 1.1 API prefix for token-based auth

**Cookbook (FastAPI):**  
*"In order to use OAuth2 Bearer token authentication with Databricks Apps, your application code must provide valid routes with a **prefix of /api**."*

**This project:**

- `pyproject.toml` has `api-prefix = "/api"` and `_metadata.py` exposes it.
- `router.py` uses `APIRouter(prefix=_api_prefix)` so all routes are under `/api`.
- Healthcheck and config are at `/api/v1/healthcheck`, `/api/config/workspace`, etc.

**Verdict:** Compliant. All API routes are under `/api`.

### 1.2 On-behalf-of-user (OBO) and X-Forwarded-Access-Token

**Cookbook (Streamlit OBO):**  
- Use header `X-Forwarded-Access-Token` for the user token when the app is opened from Compute → Apps with **on-behalf-of-user** enabled.  
- Token is not present when running locally.

**This project:**

- `dependencies.py`: `_get_obo_token(request)` reads `X-Forwarded-Access-Token` (case-insensitive) and, when the request host looks like an Apps URL, falls back to `Authorization: Bearer <token>`.
- `get_workspace_client` and `get_workspace_client_optional` use this token (or `DATABRICKS_TOKEN` when no OBO token).
- `router.py`: `/api/auth/status` returns `authenticated: bool` based on presence of the token.
- Setup UI shows "Token not received" and OBO instructions when `token_received === false`, and "Refresh job IDs" after enabling OBO.

**Verdict:** Aligned with Cookbook OBO pattern; we add a Bearer fallback for proxies that send the user token only in `Authorization`.

### 1.3 FastAPI structure (app, routes, healthcheck)

**Cookbook:**  
- `app.py` as main FastAPI app, `routes/` with versioned sub-routers (e.g. `/api/v1/`), `routes/v1/healthcheck.py` for status.

**This project:**

- `backend/app.py`: FastAPI app with lifespan, mounts UI, includes router.
- `backend/router.py`: Main API router at prefix `/api`; includes feature routers and `v1_router` at `/api/v1`.
- `backend/routes/v1/healthcheck.py`: `GET /healthcheck` returns status and timestamp; `GET /health/database` for Lakebase (Cookbook-style error-handling).

**Verdict:** Structure matches Cookbook (app, versioned API, healthcheck).

### 1.4 Runtime (uvicorn, app spec)

**Cookbook:**  
- Run with `uvicorn app:app`; for Apps use `app.yaml` with `command: ["uvicorn", "app:app"]`.

**This project:**

- `app.yml`: `command: [uvicorn, payment_analysis.backend.app:app, --host, 0.0.0.0, --port, 8000]` with `PYTHONPATH=src`, `PGAPPNAME` set.
- Bundle app definition is in `resources/fastapi_app.yml` (source path, bindings, env notes).

**Verdict:** Aligned with Cookbook runtime and app spec pattern.

---

## 2. APX alignment

### 2.1 Project structure

**APX docs:**  
- `src/<app_slug>/backend/` (FastAPI), `src/<app_slug>/ui/` (React + Vite), `pyproject.toml`, `databricks.yml`, `package.json`.

**This project:**

- `src/payment_analysis/backend/` (app.py, router.py, config, dependencies, routes).
- `src/payment_analysis/ui/` (components, routes, lib, styles).
- `pyproject.toml` with `[tool.apx.metadata]` (app-name, app-slug, app-entrypoint, api-prefix, metadata-path), `[tool.apx.ui]` root.
- `databricks.yml` for bundle (targets, sync, artifacts with `uv run apx build`).

**Verdict:** Matches APX project layout and metadata.

### 2.2 Stack

**APX:** Backend: Python, FastAPI, Pydantic. Frontend: React, TypeScript, Vite. UI: shadcn/ui, Tailwind. Runtime: Bun (bundled), uv.

**This project:** Same stack (FastAPI, Pydantic, SQLModel; React, TS, Vite; shadcn/ui, Tailwind; uv for Python; Bun for frontend tooling).

**Verdict:** Aligned.

### 2.3 Development workflow

**APX:** `uv run apx dev start` → add components with `uv run apx components add ...` → `uv run apx dev check` → `uv run apx build` → `databricks bundle deploy`.

**This project:**  
- `.cursor/rules/project.mdc` and `.claude/skills/apx/SKILL.md` document the same flow.  
- Build: `uv run apx build`; deploy: `./scripts/bundle.sh deploy [dev|prod]` (prepare dashboards + `databricks bundle deploy -t ... --force --auto-approve`).

**Verdict:** Workflow matches APX; we add a prepare step and bundle script.

### 2.4 API and OpenAPI

**APX:** API prefix from metadata; OpenAPI client generated at build time.

**This project:**  
- Routes use `response_model` and `operation_id` for client generation.  
- Rules say "OpenAPI client is generated at build time; don't manually regenerate."

**Verdict:** Consistent with APX.

---

## 3. AI Dev Kit alignment

**AI Dev Kit** focuses on: Databricks skills (markdown), MCP server (tools), starter project, and optional builder app. It does not define the app’s HTTP or auth surface.

**This project:**

- Uses **apx** for app structure and build (APX is the app toolkit).
- Can use **AI Dev Kit** skills/MCP in the same workspace for Databricks SDK, bundles, jobs, etc., without changing how this app handles auth or routes.

**Verdict:** No conflict; AI Dev Kit complements the app (skills/tools for agents), and the app follows Cookbook + APX for HTTP and auth.

---

## 4. Previous prompts – requirements vs implementation

### 4.1 Token propagation and Execute buttons

**Requirement:** Setup Execute buttons should enable when the app is opened from the Databricks workspace; token propagation must work so jobs can be run.

**Implementation:**

- **Token:** Read from `X-Forwarded-Access-Token` (and optionally `Authorization: Bearer` when on an Apps host) in `_get_obo_token`; used by `get_workspace_client_optional` and `get_workspace_client`.
- **Host:** Workspace URL from `DATABRICKS_HOST` or derived via `workspace_url_from_apps_host(_request_host_for_derivation(request), app_name)`; `_request_host_for_derivation` uses **X-Forwarded-Host** then **Host** everywhere (including `GET /api/config/workspace` after the fix below).
- **Setup defaults:** `GET /api/setup/defaults` returns `token_received`, `workspace_url_derived`, job/pipeline IDs (resolved when client is available), and `workspace_host`.
- **UI:** Execute enabled when `host` and `isJobConfigured(key)`; messages for missing token, missing workspace URL derivation, and "Refresh job IDs"; **Run now** calls `POST /api/setup/run-job` or `run-pipeline` with `credentials: "include"`.

**Verdict:** Token propagation and Execute/Run now behavior match the previous prompts.

### 4.2 Workspace URL derivation (Host / X-Forwarded-Host)

**Requirement:** Use the same host for workspace URL derivation everywhere so Execute and config are consistent behind proxies.

**Implementation:**

- **dependencies:** `_request_host_for_derivation(request)` uses `X-Forwarded-Host` then `Host`; used in `_get_obo_token` (Bearer fallback) and in `get_workspace_client` / `get_workspace_client_optional` for `workspace_url_from_apps_host(...)`.
- **setup.py:** Uses `_request_host_for_derivation(request)` for host in `get_setup_defaults`.
- **router.py (fixed):** `get_workspace_config` now uses `_request_host_for_derivation(request)` instead of only `request.headers.get("host")`, so `/api/config/workspace` derives the same workspace URL as setup and dependencies when behind a proxy.

**Verdict:** Single, consistent derivation path; fix applied in `router.py`.

### 4.3 Specific dependency versions and deploy

**Requirement:** Use specific dependency versions and do not change them; prepare, build, redeploy overwriting existing resources.

**Implementation:**  
- `pyproject.toml` pins versions (e.g. `databricks-sdk==0.84.0`, `fastapi==0.128.0`).  
- `package.json` uses exact versions for frontend deps.  
- Deploy: `./scripts/bundle.sh deploy dev` runs prepare (dashboards, SQL), then `databricks bundle deploy -t dev --force --auto-approve`.

**Verdict:** Pinned versions and overwrite deploy are as specified.

---

## 5. Summary table

| Area                    | Cookbook / APX / AI Dev Kit     | This project                                      | Status   |
|-------------------------|----------------------------------|---------------------------------------------------|----------|
| API prefix `/api`       | Required for Apps token auth    | All routes under `/api`                           | OK       |
| OBO token               | `X-Forwarded-Access-Token`       | Same + Bearer fallback on Apps host               | OK       |
| FastAPI layout          | app, versioned routes, health   | app.py, /api/v1/healthcheck, health/database      | OK       |
| APX structure           | backend + ui under src/<slug>   | payment_analysis/backend, payment_analysis/ui      | OK       |
| APX metadata            | pyproject.toml [tool.apx]       | app-name, api-prefix, entrypoint, ui root         | OK       |
| Build / deploy          | apx build, bundle deploy        | apx build; bundle.sh deploy (with prepare)         | OK       |
| Workspace URL           | N/A (Cookbook minimal)          | X-Forwarded-Host then Host everywhere             | OK (fixed) |
| Execute + Run now       | N/A                             | Execute opens workspace; Run now calls API        | OK       |
| Token in UI             | N/A                             | token_received, workspace_url_derived, messages   | OK       |

---

## 6. Change made during this review

- **router.py:** `get_workspace_config` now derives the host with `_request_host_for_derivation(request)` instead of `request.headers.get("host")` only, so workspace URL is consistent with setup and dependencies when the app is behind a proxy (e.g. Apps) that sets `X-Forwarded-Host`.

---

## 7. Databricks App–specific review (configuration)

The project is a **Databricks App**, not a generic custom deployment. All behavior is aligned with [Configure a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/configuration):

- **App execution:** `app.yml` at project root defines `command` and `env` per [Configure app execution (app-runtime)](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-runtime).
- **Authorization:** User authorization (on-behalf-of) uses the `x-forwarded-access-token` header per [Configure authorization](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth). No token is ever logged or exposed.
- **HTTP headers:** Workspace URL and host derivation use `X-Forwarded-Host` then `Host` per [Access HTTP headers](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/http-headers).
- **Backend:** Module docstrings in `app.py`, `config.py`, `dependencies.py`, `router.py`, and `routes/setup.py` reference the official configuration/auth/headers docs. `_effective_databricks_host` uses `_request_host_for_derivation(request)` for consistency.
- **Frontend:** `WorkspaceUrlBootstrapper` uses `credentials: "include"` for `/api/config/workspace`. Workspace config comments state the app is a Databricks App and that the backend derives the workspace URL from request headers.
- **Bundle:** `resources/fastapi_app.yml` comments link to configuration and authorization docs; no Databricks Apps–specific code was removed.

## 8. References

- [Configure a Databricks app](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/configuration)
- [Configure app execution (app.yaml)](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/app-runtime)
- [Configure authorization](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth)
- [Access HTTP headers](https://docs.databricks.com/aws/en/dev-tools/databricks-apps/http-headers)
- [Apps Cookbook – Intro](https://apps-cookbook.dev/docs/intro)
- [Apps Cookbook – FastAPI](https://apps-cookbook.dev/docs/category/fastapi)
- [Apps Cookbook – FastAPI create app](https://apps-cookbook.dev/docs/fastapi/getting_started/create)
- [Apps Cookbook – OBO (Streamlit)](https://apps-cookbook.dev/docs/streamlit/authentication/users_obo)
- [apx – GitHub](https://github.com/databricks-solutions/apx)
- [apx – Docs](https://databricks-solutions.github.io/apx/)
- [AI Dev Kit – GitHub](https://github.com/databricks-solutions/ai-dev-kit)
