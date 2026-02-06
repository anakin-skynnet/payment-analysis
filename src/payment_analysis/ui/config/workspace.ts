/**
 * Workspace Configuration
 * 
 * Dynamically configures Databricks workspace URLs based on environment.
 * This ensures no hardcoded workspace URLs in the frontend code.
 */

/**
 * Get the Databricks workspace base URL from environment or API.
 * 
 * In production, this would be:
 * 1. Retrieved from the backend API
 * 2. Set via environment variables at build time
 * 3. Configured in a runtime config file
 */
export function getWorkspaceUrl(): string {
  // Try to get from environment variable (set at build time)
  const envUrl = import.meta.env.VITE_DATABRICKS_HOST;
  if (envUrl) {
    return envUrl;
  }
  
  // Fallback: try to detect from window location if running in Databricks
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname.includes('.azuredatabricks.net')) {
      return `https://${hostname}`;
    }
  }
  
  // Final fallback: empty string disables external links until configured
  // Set VITE_DATABRICKS_HOST at build time or the backend will provide the URL
  return '';
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
