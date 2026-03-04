"""Grant Unity Catalog, SQL Warehouse, and Lakebase permissions to the app's Service Principal.

Run automatically after `bundle.sh deploy app` to handle SP rotation on every deploy.
The Databricks App platform assigns a new SP client_id each time the app resource is created,
so all permissions must be re-granted.

Usage:
    uv run python scripts/grant_sp_permissions.py [--catalog CATALOG] [--schema SCHEMA]
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from databricks.sdk import WorkspaceClient

DEFAULT_CATALOG = "ahs_demos_catalog"
DEFAULT_SCHEMA = "payment_analysis"


def main() -> None:
    parser = argparse.ArgumentParser(description="Grant SP permissions for the app")
    parser.add_argument("--catalog", default=os.environ.get("DATABRICKS_CATALOG", DEFAULT_CATALOG))
    parser.add_argument("--schema", default=os.environ.get("DATABRICKS_SCHEMA", DEFAULT_SCHEMA))
    args = parser.parse_args()
    catalog = args.catalog
    schema = args.schema

    w = WorkspaceClient()

    app = w.apps.get("payment-analysis")
    sp = app.service_principal_client_id
    if not sp:
        print("No service principal found on the app. Skipping.")
        return

    print(f"App SP: {sp} (catalog={catalog}, schema={schema})")

    wh_id = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
    if not wh_id:
        try:
            for wh in w.warehouses.list():
                if "payment" in (wh.name or "").lower():
                    wh_id = wh.id or ""
                    break
            if not wh_id:
                for wh in w.warehouses.list():
                    if wh.id:
                        wh_id = wh.id
                        break
        except Exception:
            pass
    if not wh_id:
        print("  Could not discover warehouse ID. Set DATABRICKS_WAREHOUSE_ID env var.")
        return

    uc_grants = [
        f"GRANT USE CATALOG ON CATALOG {catalog} TO `{sp}`",
        f"GRANT USE SCHEMA ON SCHEMA {catalog}.{schema} TO `{sp}`",
        f"GRANT SELECT ON SCHEMA {catalog}.{schema} TO `{sp}`",
        f"GRANT EXECUTE ON SCHEMA {catalog}.{schema} TO `{sp}`",
    ]

    def _run_uc_grant(sql_stmt: str) -> str:
        import time as _time
        r = w.statement_execution.execute_statement(statement=sql_stmt, warehouse_id=wh_id, wait_timeout="0s")
        sid = r.statement_id or ""
        for _ in range(60):
            st = w.statement_execution.get_statement(sid)
            state_str = str(st.status.state) if st.status else "unknown"
            if "SUCCEEDED" in state_str:
                return f"  UC: OK — {sql_stmt[:70]}"
            if "FAILED" in state_str or "CANCELED" in state_str:
                err = (st.status.error.message if st.status and st.status.error else "") or ""
                return f"  UC: WARN({state_str} {err}) — {sql_stmt[:70]}"
            _time.sleep(0.5)
        return f"  UC: WARN(timeout) — {sql_stmt[:70]}"

    def _run_warehouse_grant() -> str:
        try:
            w.api_client.do(
                "PATCH",
                f"/api/2.0/permissions/sql/warehouses/{wh_id}",
                body={
                    "access_control_list": [
                        {"service_principal_name": sp, "permission_level": "CAN_USE"}
                    ]
                },
            )
            return f"  Warehouse CAN_USE granted to {sp}"
        except Exception as e:
            return f"  Warehouse grant issue (non-fatal): {e}"

    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(_run_uc_grant, sql): sql for sql in uc_grants}
        futures[pool.submit(_run_warehouse_grant)] = "warehouse"
        for fut in as_completed(futures):
            print(fut.result())

    # 3. Lakebase Postgres role + grants
    lakebase_project_id = os.environ.get("LAKEBASE_PROJECT_ID", "payment-analysis-db")
    lakebase_branch_id = os.environ.get("LAKEBASE_BRANCH_ID", "production")
    lakebase_endpoint_id = os.environ.get("LAKEBASE_ENDPOINT_ID", "primary")
    try:
        import psycopg  # noqa: F811

        result = subprocess.run(
            ["databricks", "auth", "token", "--host", w.config.host],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"  Lakebase: could not get OAuth token — {result.stderr.strip()}")
            return

        token = json.loads(result.stdout)["access_token"]
        user = w.current_user.me().user_name

        lakebase_host = None
        try:
            postgres_api = w.postgres
            endpoint_name = f"projects/{lakebase_project_id}/branches/{lakebase_branch_id}/endpoints/{lakebase_endpoint_id}"
            ep = postgres_api.get_endpoint(name=endpoint_name)
            hosts_obj = getattr(getattr(ep, "status", None), "hosts", None)
            lakebase_host = getattr(hosts_obj, "host", None)
            if not lakebase_host:
                branch_name = f"projects/{lakebase_project_id}/branches/{lakebase_branch_id}"
                for ep_item in postgres_api.list_endpoints(parent=branch_name):
                    hosts_obj = getattr(getattr(ep_item, "status", None), "hosts", None)
                    h = getattr(hosts_obj, "host", None)
                    if h:
                        lakebase_host = h
                        break
        except Exception as e:
            print(f"  Lakebase: endpoint discovery failed ({e}), trying LAKEBASE_HOST env var...")
        if not lakebase_host:
            lakebase_host = os.environ.get("LAKEBASE_HOST", "")
        if not lakebase_host:
            print("  Lakebase: could not discover endpoint host. Set LAKEBASE_HOST env var or verify Lakebase project exists.")
            return

        conn = psycopg.connect(
            host=lakebase_host,
            port=5432,
            dbname="databricks_postgres",
            user=user,
            password=token,
            sslmode="require",
        )
        conn.autocommit = True
        cur = conn.cursor()

        from psycopg import sql

        cur.execute("CREATE EXTENSION IF NOT EXISTS databricks_auth;")
        try:
            cur.execute(
                sql.SQL("SELECT databricks_create_role({sp}, 'SERVICE_PRINCIPAL')").format(
                    sp=sql.Literal(sp)
                )
            )
            print(f"  Lakebase role created for {sp}")
        except Exception as e:
            if "already exists" in str(e):
                print(f"  Lakebase role already exists for {sp}")
            else:
                print(f"  Lakebase role issue: {e}")

        schema_ident = sql.Identifier(schema)
        sp_ident = sql.Identifier(sp)
        grant_stmts = [
            sql.SQL("GRANT ALL PRIVILEGES ON SCHEMA {} TO {}").format(schema_ident, sp_ident),
            sql.SQL("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {} TO {}").format(schema_ident, sp_ident),
            sql.SQL("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA {} TO {}").format(schema_ident, sp_ident),
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA {} GRANT ALL ON TABLES TO {}").format(schema_ident, sp_ident),
        ]
        for stmt in grant_stmts:
            cur.execute(stmt)
        print(f"  Lakebase {schema} schema/table/sequence grants complete")

        cur.close()
        conn.close()
    except ImportError:
        print("  Lakebase: psycopg not installed — skipping Postgres grants")
    except Exception as e:
        print(f"  Lakebase grant issue (non-fatal): {e}")

    print("SP permission grants complete.")


if __name__ == "__main__":
    main()
