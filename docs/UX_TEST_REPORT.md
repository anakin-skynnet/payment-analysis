# UX Test Report — Payment Analysis Databricks App

**App under test:** https://payment-analysis-984752964297111.11.azure.databricksapps.com/  
**Reference (navigation/structure):** https://payment-approval-dev-984752964297111.11.azure.databricksapps.com/ui  
**Workspace (expected target for links):** https://adb-984752964297111.11.azuredatabricks.net (with `?o=984752964297111` where applicable)  
**Report date:** 2025-02-05

---

## 1. Executive summary

Code and link logic were audited for all UI components. All links are intended to open **the specific Databricks resource** (job, pipeline, dashboard, notebook, warehouse, Genie, etc.), not the workspace root, except where noted. The following fixes were applied and recommendations are listed below.

---

## 2. Setup & Run section — buttons and URLs

All Setup buttons should be clickable when the app has a valid workspace URL (open from **Compute → Apps → payment-analysis** or with `DATABRICKS_HOST` set). Each **Execute** button opens the **specific job or pipeline page** in the workspace.

### 2.1 Expected URL format

- **Job (e.g. Lakehouse bootstrap):**  
  `https://adb-984752964297111.11.azuredatabricks.net/jobs/{job_id}?o=984752964297111`  
  Example: https://adb-984752964297111.11.azuredatabricks.net/jobs/1037597932745715?o=984752964297111

- **Pipeline:**  
  `https://adb-984752964297111.11.azuredatabricks.net/pipelines/{pipeline_id}?o=984752964297111`

- **Jobs list:**  
  `https://adb-984752964297111.11.azuredatabricks.net/jobs?o=984752964297111`

- **Pipelines list:**  
  `https://adb-984752964297111.11.azuredatabricks.net/pipelines?o=984752964297111`

- **SQL warehouse:**  
  `https://adb-984752964297111.11.azuredatabricks.net/sql/warehouses/{warehouse_id}?o=984752964297111`

- **Data explorer:**  
  `https://adb-984752964297111.11.azuredatabricks.net/explore/data/{catalog}/{schema}?o=984752964297111`

- **Genie:**  
  `https://adb-984752964297111.11.azuredatabricks.net/genie?o=984752964297111`

### 2.2 Setup buttons verified (code-level)

| Step | Resource | Button label | Expected behavior | URL when ID resolved |
|------|----------|--------------|-------------------|----------------------|
| 1 | Lakehouse bootstrap | Execute | Opens job page in workspace | `{host}/jobs/{id}?o={workspace_id}` |
| 1 | — | SQL Warehouse | Opens warehouse page | `{host}/sql/warehouses/{wid}?o={workspace_id}` |
| 2 | Vector Search index | Execute | Opens job page | `{host}/jobs/{id}?o={workspace_id}` |
| 3 | Create gold views | Execute | Opens job page | `{host}/jobs/{id}?o={workspace_id}` |
| 4 | Transaction simulator | Execute | Opens job page | `{host}/jobs/{id}?o={workspace_id}` |
| 5 | Real-time pipeline | Execute (pipeline) | Opens pipeline page | `{host}/pipelines/{id}?o={workspace_id}` |
| 5 | Stream processor | Execute (stream processor) | Opens job page | `{host}/jobs/{id}?o={workspace_id}` |
| 6 | Ingestion & ETL | Execute | Opens pipeline page | `{host}/pipelines/{id}?o={workspace_id}` |
| 7 | Train ML models | Execute | Opens job page | `{host}/jobs/{id}?o={workspace_id}` |
| 8 | Genie sync | Execute | Opens job page | `{host}/jobs/{id}?o={workspace_id}` |
| 9 | Orchestrator agent | Execute | Opens job page | `{host}/jobs/{id}?o={workspace_id}` |
| 9b | Specialist agents (5) | Smart Routing, etc. | Each opens that job’s page | `{host}/jobs/{id}?o={workspace_id}` |
| 10 | Publish dashboards | Execute | Opens job page | `{host}/jobs/{id}?o={workspace_id}` |

When a job or pipeline ID is not resolved (`0` or missing), the same button opens the **Jobs** or **Pipelines** list respectively so the user can find and run the resource there.

### 2.3 Quick links (Setup page)

| Link | Opens |
|------|--------|
| Jobs | `{host}/jobs?o={workspace_id}` |
| Pipelines | `{host}/pipelines?o={workspace_id}` |
| SQL Warehouse | `{host}/sql/warehouses/{id}?o={workspace_id}` |
| Explore schema | `{host}/explore/data/{catalog}/{schema}?o={workspace_id}` |
| Genie (Ask Data) | `{host}/genie?o={workspace_id}` |
| Stream processor (job run) | Job page when configured |
| Test Agent Framework | Job page when configured |
| All jobs | Same as Jobs |

### 2.4 Connect to Databricks card

- **Open workspace Settings** → `{host}/?o={workspace_id}#setting/account` (or `{host}/#setting/account` if no workspace_id).

---

## 3. Other UI components — links to Databricks

### 3.1 Home (index)

| Element | Behavior | Note |
|--------|----------|------|
| “See how to accelerate” | In-app nav → `/dashboard` | OK |
| “Recommendations & actions” | In-app nav → `/decisioning` | OK |
| “Open workspace to sign in” | Opens workspace base URL | Opens workspace root so user can go to Apps/Settings; acceptable for sign-in. |

### 3.2 KPI overview (dashboard)

- **View Executive dashboard** → `/sql/dashboards/executive_overview` (specific dashboard).
- **Daily trends**, **Routing optimization** cards → open same dashboard path via `getDashboardUrl()`.
- All use `openWorkspaceUrl(getDashboardUrl(...))` → **specific dashboard** in workspace.

### 3.3 Dashboards page

- Each dashboard card → `{workspaceUrl}{dashboard.url_path}` (e.g. `/sql/dashboards/executive_overview`) → **specific dashboard**.
- “Open in Databricks” for embed view → same.
- Genie button → `/genie` (specific resource).
- Notebook links → backend `getNotebookUrl` → **specific notebook** in workspace.

### 3.4 Reason Codes

- “Open in Databricks” (decline dashboard) → `/sql/dashboards/decline_analysis` → **specific dashboard**.

### 3.5 Declines

- Dashboard link → `/sql/dashboards/decline_analysis` → **specific dashboard**.

### 3.6 Decisioning (Recommendations & decisions)

- Notebook links → `/api/notebooks/notebooks/{id}/url` then `openWorkspaceUrl(data.url)` → **specific notebook**.

### 3.7 Rules

- Uses in-app data; no direct workspace link in the audited flow.

### 3.8 Smart Checkout

- Dashboard links → `/sql/dashboards/authentication_security`, `/sql/dashboards/routing_optimization` → **specific dashboards**.

### 3.9 Smart Retry

- “Open in Databricks” → `/sql/dashboards/routing_optimization` → **specific dashboard**.

### 3.10 AI agents

- External docs only (e.g. learn.microsoft.com). No workspace link in the audited content.

### 3.11 Notebooks

- Each notebook → `getNotebookUrl` API → `openWorkspaceUrl(data.url)` → **specific notebook** in workspace.

### 3.12 ML models

- “Financial impact” / “Routing optimization” → `/sql/dashboards/financial_impact`, `/sql/dashboards/routing_optimization` → **specific dashboards**.

### 3.13 Incidents

- “Monitoring Dashboard” → `/sql/dashboards/realtime_monitoring` → **specific dashboard**.
- “Alert Pipeline” → notebook `realtime_pipeline` → **specific notebook**.
- Incident row click → same realtime_monitoring dashboard.

### 3.14 Experiments

- Uses in-app data / MLflow; any “Open in workspace” style links would go to MLflow (specific resource) if present.

### 3.15 Profile

- In-app only in audited code.

---

## 4. Fixes applied in this pass

1. **Pipeline URLs** — Append `?o={workspace_id}` when available for pipeline detail and pipelines list (consistent with jobs).
2. **Pipelines list** — Use `?o={workspace_id}` when available.
3. **Jobs list** — Removed hardcoded tags filter; now opens `/jobs?o={workspace_id}` so the link always targets the **Jobs** list resource without user-specific tags.
4. **SQL Warehouse, Explore schema, Genie** — Append `?o={workspace_id}` when available so all open-in-workspace links are consistent.
5. **Open workspace Settings** — Use `/?o={workspace_id}#setting/account` when workspace_id is available.

---

## 5. Recommendations and UX improvements

### 5.1 Manual verification (when you have app access)

- Open the app from **Compute → Apps → payment-analysis** so `workspace_host` and `workspace_id` are set.
- Click each **Execute** button on Setup and confirm:
  - Lakehouse bootstrap opens: `https://adb-984752964297111.11.azuredatabricks.net/jobs/1037597932745715?o=984752964297111` (or your actual job ID).
  - Every other job opens `.../jobs/{id}?o=984752964297111` and each pipeline opens `.../pipelines/{id}?o=984752964297111`.
- Use **Refresh job IDs** if any job IDs show as “0” after deployment.
- Check Quick links: Jobs, Pipelines, SQL Warehouse, Explore schema, Genie open the correct resource with `o=` in the URL.

### 5.2 When Execute is disabled

- Ensure the app is opened from the Apps URL (Compute → Apps) so the backend can derive workspace URL and token.
- If token is present but URL is not, set `DATABRICKS_HOST` in the app environment (e.g. `https://adb-984752964297111.11.azuredatabricks.net`).

### 5.3 Navigation alignment with reference

- The reference app (payment-approval-dev-.../ui) uses a similar sidebar layout. This app’s sidebar matches that structure (Overview, Reasons & factors, Recommendations, Initiatives, AI & automation, Operations, Settings). No change required for consistency.

### 5.4 Accessibility / UX polish

- All Execute and Quick link buttons use `ExternalLink` icon to signal “opens in new tab.”
- Cards that open a resource use `onClick` and `onKeyDown` (Enter) so they are keyboard-activatable.
- Consider adding `aria-label` to icon-only or ambiguous buttons (e.g. “Open Lakehouse bootstrap job in Databricks”) for screen readers.

### 5.5 Error handling

- If `/api/setup/defaults` fails or returns no workspace_host, the Setup page shows guidance and “Refresh job IDs”; no link is opened with an empty host. This is correct.

---

## 6. Summary table — “Opens correct resource?”

| Area | Links open specific resource? | Notes |
|------|--------------------------------|--------|
| Setup — Execute (jobs) | Yes | `{host}/jobs/{id}?o=` or jobs list |
| Setup — Execute (pipelines) | Yes | `{host}/pipelines/{id}?o=` or pipelines list |
| Setup — Quick links | Yes | Jobs, Pipelines, Warehouse, Explore, Genie with `?o=` |
| Dashboard / Dashboards | Yes | Specific dashboard paths |
| Reason Codes / Declines | Yes | Decline analysis dashboard |
| Decisioning | Yes | Notebook URLs from API |
| Smart Checkout / Smart Retry | Yes | Specific dashboards |
| Notebooks | Yes | Notebook URL from API |
| ML models | Yes | Dashboard paths |
| Incidents | Yes | Realtime monitoring dashboard + notebook |
| Home “Open workspace to sign in” | Opens workspace root | Acceptable for sign-in |

---

*This report was produced by auditing the codebase and link construction logic. Run manual checks in the live app and workspace to confirm URLs match your deployment (e.g. job IDs after bundle deploy).*
