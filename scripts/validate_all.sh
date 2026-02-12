#!/usr/bin/env bash
# Run full validation: dashboards (widgets/columns for visuals), jobs, pipelines, agents.
# Jobs 1–7 include Job 6 (Deploy Agents: run_agent_framework + register_agentbricks).
# Usage:
#   ./scripts/validate_all.sh           # Validate only (dashboards, list jobs/pipelines)
#   ./scripts/validate_all.sh --run-jobs   # Also trigger all jobs (no-wait); poll with: uv run python scripts/run_and_validate_jobs.py status
set -e
cd "$(dirname "$0")/.."

RUN_JOBS=""
for arg in "$@"; do
  if [[ "$arg" == "--run-jobs" ]]; then
    RUN_JOBS=1
  fi
done

echo "=== 1. Dashboard widgets and columns for visuals ==="
uv run python scripts/dashboards.py check-widgets || exit 1
echo ""

echo "=== 2. Dashboard assets (tables/views) ==="
uv run python scripts/dashboards.py validate-assets --catalog "${DATABRICKS_CATALOG:-ahs_demos_catalog}" --schema "${DATABRICKS_SCHEMA:-payment_analysis}" || exit 1
echo ""

echo "=== 3. Jobs (1–7, including Job 6 Deploy Agents) ==="
uv run python scripts/run_and_validate_jobs.py --dry-run || exit 1
echo ""

echo "=== 4. Pipelines (8. ETL, 9. Real-Time) ==="
uv run python scripts/run_and_validate_jobs.py pipelines || exit 1
echo ""

echo "=== 5. Agents (backend registry and routes) ==="
uv run python -c "
from payment_analysis.backend.routes.agents import router, AGENTS
assert router is not None, 'agents router missing'
assert len(AGENTS) > 0, 'AGENTS list must not be empty'
print(f'Agents registry OK: {len(AGENTS)} agent(s) defined.')
" || exit 1
echo ""

if [[ -n "$RUN_JOBS" ]]; then
  echo "=== 6. Triggering all jobs (no-wait) ==="
  uv run python scripts/run_and_validate_jobs.py --no-wait || exit 1
  echo ""
  echo "Poll status: uv run python scripts/run_and_validate_jobs.py status"
  echo "Or wait for completion: uv run python scripts/run_and_validate_jobs.py (without --no-wait)"
else
  echo "=== 6. (Skipped) To trigger all jobs: ./scripts/validate_all.sh --run-jobs ==="
fi

echo ""
echo "All validations passed."
