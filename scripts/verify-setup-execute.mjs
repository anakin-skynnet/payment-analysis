#!/usr/bin/env node
/**
 * Verify Setup Execute flow: fetch /api/setup/defaults and simulate what happens
 * when the user clicks Execute (URL construction, enabled state). Optionally
 * trigger a job run via POST /api/setup/run-job and report errors.
 *
 * Usage:
 *   BASE_URL=https://payment-analysis-xxx.databricksapps.com node scripts/verify-setup-execute.mjs
 *   BASE_URL=http://localhost:8080 node scripts/verify-setup-execute.mjs [--run-job lakehouse_bootstrap]
 *
 * Without --run-job: only checks defaults and the URL that Execute would open.
 * With --run-job <key>: also POSTs to run the job (requires token from Apps or DATABRICKS_TOKEN).
 */

const BASE_URL = process.env.BASE_URL || "http://localhost:8080";
const RUN_JOB_KEY = process.argv.includes("--run-job")
  ? process.argv[process.argv.indexOf("--run-job") + 1]
  : null;

function ensureAbsolute(url) {
  if (!url || url.startsWith("http://") || url.startsWith("https://")) return url || "";
  return `https://${url}`;
}

async function main() {
  console.log("Verify Setup Execute");
  console.log("BASE_URL:", BASE_URL);
  console.log("");

  // 1. Fetch defaults (same as UI)
  let defaults;
  try {
    const res = await fetch(`${BASE_URL.replace(/\/$/, "")}/api/setup/defaults`, {
      method: "GET",
      credentials: "include",
      headers: { Accept: "application/json" },
    });
    if (!res.ok) {
      console.error("GET /api/setup/defaults failed:", res.status, res.statusText);
      const text = await res.text();
      console.error(text.slice(0, 500));
      process.exit(1);
    }
    defaults = await res.json();
  } catch (e) {
    console.error("Fetch error:", e.message);
    process.exit(1);
  }

  const tokenReceived = !!defaults.token_received;
  const workspaceUrlDerived = !!defaults.workspace_url_derived;
  const rawHost = defaults.workspace_host || "";
  const host =
    rawHost && !rawHost.toLowerCase().includes("databricksapps")
      ? ensureAbsolute(rawHost)
      : "";

  console.log("Defaults response:");
  console.log("  token_received:", tokenReceived);
  console.log("  workspace_url_derived:", workspaceUrlDerived);
  console.log("  workspace_host (raw):", rawHost ? `${rawHost.slice(0, 50)}...` : "(empty)");
  console.log("  host (for Execute):", host || "(empty – Execute buttons disabled)");
  console.log("");

  // 2. Simulate Execute for first job (lakehouse_bootstrap)
  const jobKey = "lakehouse_bootstrap";
  const jobId = defaults.jobs?.[jobKey];
  const isJobConfigured = jobId && jobId !== "0";
  const executeEnabled = !!host && isJobConfigured;
  const executeUrl = executeEnabled ? `${host}/#job/${jobId}/run` : null;

  console.log("Simulate Execute button (job:", jobKey + "):");
  console.log("  job_id:", jobId ?? "(missing)");
  console.log("  Execute enabled:", executeEnabled);
  if (executeUrl) {
    console.log("  URL that would open:", executeUrl);
    console.log("  OK – Execute would open the job run page in a new tab.");
  } else {
    console.log("  Execute would be disabled.");
    if (!host) console.log("  Reason: no workspace host (set DATABRICKS_HOST or open from Apps).");
    if (!isJobConfigured) console.log("  Reason: job ID not resolved (enable OBO and click Refresh job IDs).");
  }
  console.log("");

  // 3. Optional: trigger run-job and report errors
  if (RUN_JOB_KEY && isJobConfigured && host) {
    const id = defaults.jobs?.[RUN_JOB_KEY] || defaults.pipelines?.[RUN_JOB_KEY];
    if (!id || id === "0") {
      console.error("Job/pipeline not configured for key:", RUN_JOB_KEY);
      process.exit(1);
    }
    const isPipeline = !!defaults.pipelines?.[RUN_JOB_KEY];
    const url = isPipeline
      ? `${BASE_URL.replace(/\/$/, "")}/api/setup/run-pipeline`
      : `${BASE_URL.replace(/\/$/, "")}/api/setup/run-job`;
    const body = isPipeline ? { pipeline_id: id } : { job_id: id, catalog: defaults.catalog, schema: defaults.schema, warehouse_id: defaults.warehouse_id };
    console.log("POST", url, "(Run now for", RUN_JOB_KEY + ")...");
    try {
      const res = await fetch(url, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify(body),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        console.error("Run failed:", res.status, data.detail || data.message || res.statusText);
        process.exit(1);
      }
      console.log("Run started:", data.run_page_url || data.pipeline_page_url || data.message);
    } catch (e) {
      console.error("Request error:", e.message);
      process.exit(1);
    }
  } else if (RUN_JOB_KEY) {
    console.log("Skipping --run-job (Execute not enabled or job not configured).");
  }

  console.log("");
  console.log("Done.");
}

main();
