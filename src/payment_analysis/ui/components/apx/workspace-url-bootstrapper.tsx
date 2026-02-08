import { useEffect } from "react";
import { setWorkspaceUrlFromApi } from "@/config/workspace";

/**
 * Fetches workspace URL from backend and caches it so getWorkspaceUrl() and
 * all UI links (jobs, pipelines, dashboards, Genie, MLflow) resolve correctly.
 * Uses credentials: "include" so the request is sent with the same context as the
 * Databricks App (backend derives workspace from X-Forwarded-Host / Host). Renders nothing; run once at app root.
 */
export function WorkspaceUrlBootstrapper() {
  useEffect(() => {
    fetch("/api/config/workspace", { credentials: "include" })
      .then((res) => (res.ok ? res.json() : Promise.reject(new Error("config/workspace failed"))))
      .then((data: { workspace_url?: string }) => {
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
