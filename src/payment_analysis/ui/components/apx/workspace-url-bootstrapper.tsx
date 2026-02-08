import { useEffect } from "react";
import { setWorkspaceUrlFromApi } from "@/config/workspace";

/**
 * Fetches workspace URL from backend and caches it so getWorkspaceUrl() and
 * all UI links (jobs, pipelines, dashboards, Genie, MLflow) resolve correctly.
 * Renders nothing; run once at app root.
 */
export function WorkspaceUrlBootstrapper() {
  useEffect(() => {
    fetch("/api/config/workspace")
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error("config/workspace failed"))))
      .then((data: { workspace_url?: string }) => {
        if (data?.workspace_url) {
          setWorkspaceUrlFromApi(data.workspace_url);
        }
      })
      .catch(() => {
        // Ignore: getWorkspaceUrl() will use env or window.location.origin when on Databricks host
      });
  }, []);
  return null;
}
