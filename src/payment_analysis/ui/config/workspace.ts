/**
 * Workspace Configuration
 *
 * Dynamically configures Databricks workspace URLs based on environment and API.
 * Used by all UI links to jobs, pipelines, dashboards, Genie, MLflow, etc.
 */

/** Cache for workspace URL from GET /api/config/workspace (set at app load). */
let workspaceUrlFromApi: string | null = null;

/** Placeholder returned by backend when DATABRICKS_HOST is unset; do not cache so getWorkspaceUrl() can fall back to window.location.origin. */
const PLACEHOLDER_HOST = "example.databricks.com";

/**
 * Set workspace base URL from backend (e.g. after GET /api/config/workspace).
 * Call this once at app load so getWorkspaceUrl() returns the correct host.
 * Does not cache placeholder URLs so that window.location.origin detection can be used on Databricks domains.
 */
export function setWorkspaceUrlFromApi(url: string): void {
  const normalized = (url || "").trim().replace(/\/+$/, "");
  if (!normalized || normalized.includes(PLACEHOLDER_HOST)) {
    workspaceUrlFromApi = null;
    return;
  }
  workspaceUrlFromApi = normalized;
}

/**
 * Get the Databricks workspace base URL (no trailing slash).
 * Order: env → API cache → window.origin when on Databricks host → "".
 */
export function getWorkspaceUrl(): string {
  const envUrl = import.meta.env.VITE_DATABRICKS_HOST;
  if (envUrl) {
    return (envUrl as string).trim().replace(/\/+$/, "");
  }
  if (workspaceUrlFromApi) {
    return workspaceUrlFromApi;
  }
  if (typeof window !== "undefined") {
    const hostname = window.location.hostname;
    if (hostname.includes("databricks")) {
      return window.location.origin;
    }
  }
  return "";
}

/**
 * Construct a full Databricks workspace URL for a given path.
 */
export function getWorkspacePath(path: string): string {
  const baseUrl = getWorkspaceUrl();
  // Ensure path starts with /
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${baseUrl}${normalizedPath}`;
}

/**
 * Construct a dashboard URL.
 */
export function getDashboardUrl(dashboardPath: string): string {
  return getWorkspacePath(dashboardPath);
}

/**
 * Construct an MLflow URL.
 */
export function getMLflowUrl(path: string = '/ml/experiments'): string {
  return getWorkspacePath(path);
}

/**
 * Construct a Genie URL.
 */
export function getGenieUrl(): string {
  return getWorkspacePath('/genie');
}
