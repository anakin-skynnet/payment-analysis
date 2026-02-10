#!/usr/bin/env python3
"""Resolve the schema name for a bundle target (same as DAB uses when deploying).

DAB dev naming: "dev" + current_user + base name (payment_analysis).
Usage: uv run python scripts/resolve_bundle_schema.py [target]
  target: dev (default) or prod
Prints the resolved schema name to stdout (e.g. dev_ariel_hdez_payment_analysis for dev).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def resolve_schema(target: str) -> str:
    """Resolve schema from bundle validate output, or fallback to env/convention."""
    if target != "dev":
        # Prod uses var from bundle or default
        try:
            result = subprocess.run(
                ["databricks", "bundle", "validate", "-t", target, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=REPO_ROOT,
            )
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                schema = (data.get("variables") or {}).get("schema") or {}
                if isinstance(schema, dict) and schema.get("value"):
                    return schema["value"]
        except Exception:
            pass
        return "ahs_demo_payment_analysis_prod" if target == "prod" else "payment_analysis"

    # Dev: resolve from bundle validate (same as DAB: dev_${workspace.current_user.short_name}_payment_analysis)
    try:
        result = subprocess.run(
            ["databricks", "bundle", "validate", "-t", "dev", "-o", "json"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=REPO_ROOT,
        )
        if result.returncode == 0 and result.stdout:
            data = json.loads(result.stdout)
            schema = (data.get("variables") or {}).get("schema") or {}
            if isinstance(schema, dict) and schema.get("value"):
                return schema["value"]
    except Exception:
        pass
    # Fallback: env or convention
    import os
    explicit = os.getenv("DATABRICKS_SCHEMA", "").strip()
    if explicit:
        return explicit
    short = (os.getenv("DATABRICKS_CURRENT_USER_SHORT_NAME") or "").strip()
    if short:
        return f"dev_{short}_payment_analysis"
    return "payment_analysis"


def main() -> int:
    target = (sys.argv[1:] or ["dev"])[0]
    print(resolve_schema(target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
