#!/usr/bin/env python3
"""
Prepare dashboard JSON files with catalog/schema substitution.

Dashboard source files use a literal catalog.schema (dev default). For prod
deployments we need to point at prod_catalog.ahs_demo_payment_analysis_prod.
This script copies dashboard JSONs to .build/dashboards/ with the literal
replaced by the given catalog.schema so bundle deploy uses the correct UC
tables per target.

Usage:
  # Dev (default): uv run python scripts/prepare_dashboards.py
  # Prod:         uv run python scripts/prepare_dashboards.py --catalog prod_catalog --schema ahs_demo_payment_analysis_prod
  # With env:      BUNDLE_VAR_catalog=prod_catalog BUNDLE_VAR_schema=... uv run python scripts/prepare_dashboards.py

Run before: databricks bundle deploy -t dev  (or -t prod).
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path

# Literal we replace (must match exactly what is in the source JSONs)
DEV_CATALOG_SCHEMA = "ahs_demos_catalog.ahs_demo_payment_analysis_dev"

SOURCE_DIR = Path(__file__).resolve().parent.parent / "src" / "payment_analysis" / "dashboards"
OUT_DIR = Path(__file__).resolve().parent.parent / ".build" / "dashboards"
GOLD_VIEWS_SOURCE = Path(__file__).resolve().parent.parent / "src" / "payment_analysis" / "transform" / "gold_views.sql"
GOLD_VIEWS_OUT_DIR = Path(__file__).resolve().parent.parent / ".build" / "transform"


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare dashboard JSONs and gold views SQL with catalog/schema for bundle deploy")
    parser.add_argument("--catalog", default=os.environ.get("BUNDLE_VAR_catalog", "ahs_demos_catalog"), help="Unity Catalog name")
    parser.add_argument("--schema", default=os.environ.get("BUNDLE_VAR_schema", "ahs_demo_payment_analysis_dev"), help="Schema name")
    args = parser.parse_args()

    catalog_schema = f"{args.catalog}.{args.schema}"
    if catalog_schema == DEV_CATALOG_SCHEMA:
        # No substitution needed, but we still copy so file_path in bundle is consistent
        pass

    # 1. Prepare dashboards (catalog.schema in asset_name)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    count = 0
    for path in sorted(SOURCE_DIR.glob("*.lvdash.json")):
        content = path.read_text(encoding="utf-8")
        if DEV_CATALOG_SCHEMA in content:
            content = content.replace(DEV_CATALOG_SCHEMA, catalog_schema)
        out_path = OUT_DIR / path.name
        out_path.write_text(content, encoding="utf-8")
        count += 1
    print(f"Prepared {count} dashboards in {OUT_DIR} with catalog.schema = {catalog_schema}")

    # 2. Prepare gold_views.sql with USE CATALOG/SCHEMA so the job runs in the same catalog.schema as dashboards
    GOLD_VIEWS_OUT_DIR.mkdir(parents=True, exist_ok=True)
    header = f"-- Catalog/schema for this run (must match dashboard asset_name)\nUSE CATALOG {args.catalog};\nUSE SCHEMA {args.schema};\n\n"
    gold_content = GOLD_VIEWS_SOURCE.read_text(encoding="utf-8")
    (GOLD_VIEWS_OUT_DIR / "gold_views.sql").write_text(header + gold_content, encoding="utf-8")
    print(f"Prepared gold_views.sql in {GOLD_VIEWS_OUT_DIR} with USE CATALOG {args.catalog}; USE SCHEMA {args.schema};")


if __name__ == "__main__":
    main()
