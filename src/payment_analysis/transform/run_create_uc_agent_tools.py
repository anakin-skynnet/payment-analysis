# Databricks notebook source
# MAGIC %md
# MAGIC # Create UC Agent Tools
# MAGIC
# MAGIC Creates Unity Catalog functions for the Agent Framework (AgentBricks path):
# MAGIC `get_decline_trends`, `get_route_performance`, `get_retry_success_rates`, etc. in `catalog.schema`.
# MAGIC Run after gold views and `payments_enriched_silver` exist. Reads `uc_agent_tools.sql` from the workspace (no package import).
# MAGIC
# MAGIC **Widgets:** `workspace_path` (repo root under workspace, e.g. .../files), `catalog`, `schema`.

# COMMAND ----------

import os
import re

dbutils.widgets.text("workspace_path", "")  # type: ignore[name-defined]
dbutils.widgets.text("catalog", "ahs_demos_catalog")  # type: ignore[name-defined]
dbutils.widgets.text("schema", "payment_analysis")  # type: ignore[name-defined]

workspace_path = dbutils.widgets.get("workspace_path")  # type: ignore[name-defined]
catalog = dbutils.widgets.get("catalog")  # type: ignore[name-defined]
schema = dbutils.widgets.get("schema")  # type: ignore[name-defined]

if not catalog or not schema:
    raise ValueError("Widgets catalog and schema are required")

# Resolve path to uc_agent_tools.sql (agents/uc_tools/ relative to workspace src).
base = workspace_path or os.getcwd()
for prefix in ("", "files"):
    root = os.path.join(base, prefix) if prefix else base
    sql_path = os.path.join(root, "src", "payment_analysis", "agents", "uc_tools", "uc_agent_tools.sql")
    if os.path.isfile(sql_path):
        break
else:
    raise FileNotFoundError(
        f"uc_agent_tools.sql not found under {base}. Ensure bundle sync includes src/payment_analysis/agents/uc_tools and job passes workspace_path."
    )

with open(sql_path, encoding="utf-8") as f:
    raw = f.read()
sql_text = raw.replace("__CATALOG__", catalog).replace("__SCHEMA__", schema)
parts = re.split(r";\s*(?=\n|$)", sql_text)
statements = [s.strip() for s in parts if s.strip()]

try:
    _spark = spark  # noqa: F821
except NameError:
    from pyspark.sql import SparkSession
    _spark = SparkSession.builder.getOrCreate()

for stmt in statements:
    if stmt:
        _spark.sql(stmt)

print(f"Created {len(statements)} UC agent tool functions in {catalog}.{schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC UC agent tool functions are ready. Use them with LangGraph agents or the custom agent framework.
