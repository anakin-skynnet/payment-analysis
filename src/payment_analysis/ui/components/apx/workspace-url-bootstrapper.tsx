import { useEffect } from "react";
import { setWorkspaceUrlFromApi } from "@/config/workspace";
import { getWorkspaceConfig } from "@/lib/api";

/**
 * Fetches workspace URL from backend (GET /api/config/workspace) and caches it so getWorkspaceUrl()
 * and all UI links (jobs, pipelines, dashboards, Genie, MLflow) resolve correctly.
 * Uses credentials: "include" so the request is sent with the same context as the Databricks App.
 * Renders nothing; run once at app root.
 */
export function WorkspaceUrlBootstrapper() {
  useEffect(() => {
    getWorkspaceConfig({ credentials: "include" })
      .then(({ data }) => {
        if (data?.workspace_url) {
          setWorkspaceUrlFromApi(data.workspace_url);
        }
      })
      .catch(() => {
        // Ignore: getWorkspaceUrl() will use env or window.location when on workspace host
      });
  }, []);
  return null;
}
