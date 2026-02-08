#!/usr/bin/env python3
"""
Run and validate all payment-analysis Databricks jobs.

Uses the same job name matching as the app (setup.py). Runs each job, waits for
completion, and reports success/failure. Exits with 1 if any run fails.

Prerequisites: Unity Catalog and schema must exist (default ahs_demos_catalog.payment_analysis).
See docs/DEPLOYMENT_GUIDE.md. Set DATABRICKS_CATALOG / DATABRICKS_SCHEMA if different.

Usage:
  uv run python scripts/run_and_validate_jobs.py [--dry-run] [--job KEY] [--no-wait]
  DATABRICKS_HOST=... DATABRICKS_TOKEN=... uv run python scripts/run_and_validate_jobs.py
  # With job IDs (avoids listing in large workspaces):
  DATABRICKS_JOB_ID_LAKEHOUSE_BOOTSTRAP=123 ... uv run python scripts/run_and_validate_jobs.py

Options:
  --dry-run    List matched jobs only, do not run.
  --job KEY    Run only this job key (e.g. lakehouse_bootstrap, create_gold_views).
  --no-wait    Start runs but do not wait for completion.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Same name substrings as backend setup.py (must match job names from bundle).
JOB_NAME_SUBSTRINGS: dict[str, str] = {
    "lakehouse_bootstrap": "Lakehouse Bootstrap",
    "vector_search_index": "Vector Search Index",
    "create_gold_views": "Gold Views",
    "transaction_stream_simulator": "Transaction Stream Simulator",
    "train_ml_models": "Train Payment Approval ML Models",
    "genie_sync": "Genie Space Sync",
    "orchestrator_agent": "Orchestrator",
    "smart_routing_agent": "Smart Routing Agent",
    "smart_retry_agent": "Smart Retry Agent",
    "decline_analyst_agent": "Decline Analyst Agent",
    "risk_assessor_agent": "Risk Assessor Agent",
    "performance_recommender_agent": "Performance Recommender Agent",
    "continuous_stream_processor": "Continuous Stream Processor",
    "test_agent_framework": "Test AI Agent Framework",
    "publish_dashboards": "Publish Dashboards",
    "prepare_dashboards": "Prepare Dashboard",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run and validate payment-analysis Databricks jobs")
    parser.add_argument("--dry-run", action="store_true", help="List jobs only, do not run")
    parser.add_argument("--job", type=str, metavar="KEY", help="Run only this job key")
    parser.add_argument("--no-wait", action="store_true", help="Start runs but do not wait")
    args = parser.parse_args()

    try:
        from databricks.sdk import WorkspaceClient
    except ImportError:
        print("databricks-sdk not installed. Run: uv sync", file=sys.stderr)
        return 1

    catalog = os.getenv("DATABRICKS_CATALOG", "ahs_demos_catalog")
    schema = os.getenv("DATABRICKS_SCHEMA", "payment_analysis")
    warehouse_id = os.getenv("DATABRICKS_WAREHOUSE_ID", "")

    def _job_id_env(key: str) -> str:
        return os.getenv("DATABRICKS_JOB_ID_" + key.upper(), "")

    ws = WorkspaceClient()
    # Prefer job IDs from env (DATABRICKS_JOB_ID_LAKEHOUSE_BOOTSTRAP etc.); else resolve by listing
    key_to_job: dict[str, tuple[int, str]] = {}
    for key in JOB_NAME_SUBSTRINGS:
        jid = _job_id_env(key)
        if jid and jid != "0":
            try:
                job_id = int(jid)
                job = ws.jobs.get(job_id)
                name = (job.settings.name or "") if job.settings else str(job_id)
                key_to_job[key] = (job_id, name)
            except Exception:
                pass
    if not key_to_job or (args.job and args.job not in key_to_job):
        # Resolve by listing (single page to avoid slow full scan)
        try:
            for job in ws.jobs.list(limit=100):
                name = (job.settings.name or "") if job.settings else ""
                for key, substr in JOB_NAME_SUBSTRINGS.items():
                    if substr in name and job.job_id:
                        key_to_job[key] = (job.job_id, name)
                        break
        except Exception as e:
            print(f"Failed to list jobs: {e}", file=sys.stderr)
            return 1

    if args.job:
        if args.job not in key_to_job:
            print(f"Job key {args.job!r} not found. Available: {', '.join(sorted(key_to_job))}", file=sys.stderr)
            return 1
        key_to_job = {args.job: key_to_job[args.job]}

    if not key_to_job:
        print("No payment-analysis jobs found in workspace.", file=sys.stderr)
        return 1

    print("Matched jobs:")
    for key in sorted(key_to_job):
        jid, name = key_to_job[key]
        print(f"  {key}: {jid}  {name[:60]}...")
    if args.dry_run:
        return 0

    notebook_params = {"catalog": catalog, "schema": schema}
    if warehouse_id:
        notebook_params["warehouse_id"] = warehouse_id

    runs: list[tuple[str, int, int]] = []  # (key, job_id, run_id)
    for key in sorted(key_to_job):
        job_id, name = key_to_job[key]
        try:
            run = ws.jobs.run_now(
                job_id=job_id,
                notebook_params=notebook_params,
            )
            runs.append((key, job_id, run.run_id))
            print(f"Started {key}  job_id={job_id}  run_id={run.run_id}")
        except Exception as e:
            print(f"Failed to start {key}: {e}", file=sys.stderr)
            return 1

    if args.no_wait:
        print("Runs started (--no-wait). Check workspace for status.")
        return 0

    # Wait for all runs
    print("\nWaiting for runs to complete...")
    failed: list[str] = []
    for key, job_id, run_id in runs:
        while True:
            run = ws.jobs.get_run(run_id)
            state = run.state and run.state.life_cycle_state
            result = (run.state and run.state.result_state) or ""
            if state == "TERMINATED":
                if result == "SUCCESS":
                    print(f"  {key}: SUCCESS  run_id={run_id}")
                else:
                    print(f"  {key}: FAILED   run_id={run_id}  result_state={result}")
                    failed.append(key)
                break
            if state in ("INTERNAL_ERROR", "SKIPPED"):
                print(f"  {key}: {state}  run_id={run_id}")
                failed.append(key)
                break
            time.sleep(10)
    if failed:
        print(f"\nFailed jobs: {', '.join(failed)}", file=sys.stderr)
        return 1
    print("\nAll jobs completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
