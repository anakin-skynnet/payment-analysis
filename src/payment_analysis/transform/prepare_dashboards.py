# Databricks notebook source
# MAGIC %md
# MAGIC # Prepare Dashboard Assets
# MAGIC
# MAGIC Runs `scripts/dashboards.py prepare` to copy dashboard JSONs to `.build/dashboards/`
# MAGIC and gold_views.sql to `.build/transform/` with catalog/schema substitution.
# MAGIC Use this job when you want to (re)generate dashboard assets in the workspace
# MAGIC before or after deploy. For local deploy, you can instead run:
# MAGIC `uv run python scripts/dashboards.py prepare --catalog <catalog> --schema <schema>`.
# MAGIC
# MAGIC **Widgets:** `workspace_path` (repo root under workspace, e.g. .../files), `catalog`, `schema`.

# COMMAND ----------

import os
import subprocess
import sys

workspace_path = dbutils.widgets.get("workspace_path")  # type: ignore[name-defined]  # noqa: F821
catalog = dbutils.widgets.get("catalog")  # type: ignore[name-defined]  # noqa: F821
schema = dbutils.widgets.get("schema")  # type: ignore[name-defined]  # noqa: F821

if not workspace_path or not catalog or not schema:
    raise ValueError("Widgets workspace_path, catalog, and schema are required")

os.chdir(workspace_path)
result = subprocess.run(
    [sys.executable, "scripts/dashboards.py", "prepare", "--catalog", catalog, "--schema", schema],
    capture_output=False,
)
if result.returncode != 0:
    sys.exit(result.returncode)

print("Prepare completed. .build/dashboards and .build/transform are updated.")
