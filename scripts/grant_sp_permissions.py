"""Grant Unity Catalog, SQL Warehouse, and Lakebase permissions to the app's Service Principal.

Run automatically after `bundle.sh deploy app` to handle SP rotation on every deploy.
The Databricks App platform assigns a new SP client_id each time the app resource is created,
so all permissions must be re-granted.

Usage:
    uv run python scripts/grant_sp_permissions.py
"""

from __future__ import annotations

import json
import subprocess
import sys

from databricks.sdk import WorkspaceClient


def main() -> None:
    w = WorkspaceClient()

    app = w.apps.get("payment-analysis")
    sp = app.service_principal_client_id
    if not sp:
        print("No service principal found on the app. Skipping.")
        return

    print(f"App SP: {sp}")

    # Discover the warehouse ID from the app's environment or the bundle config
    import os
    wh_id = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
    if not wh_id:
        # Fallback: list warehouses and pick the payment-analysis one
        try:
            for wh in w.warehouses.list():
                if "payment" in (wh.name or "").lower():
                    wh_id = wh.id or ""
                    break
            if not wh_id:
                # Use first available warehouse
                for wh in w.warehouses.list():
                    if wh.id:
                        wh_id = wh.id
                        break
        except Exception:
            pass
    if not wh_id:
        print("  Could not discover warehouse ID. Set DATABRICKS_WAREHOUSE_ID env var.")
        return

    # 1. Unity Catalog grants
    uc_grants = [
        f"GRANT USE CATALOG ON CATALOG ahs_demos_catalog TO `{sp}`",
        f"GRANT USE SCHEMA ON SCHEMA ahs_demos_catalog.payment_analysis TO `{sp}`",
        f"GRANT SELECT ON SCHEMA ahs_demos_catalog.payment_analysis TO `{sp}`",
        f"GRANT EXECUTE ON SCHEMA ahs_demos_catalog.payment_analysis TO `{sp}`",
    ]
    for sql in uc_grants:
        r = w.statement_execution.execute_statement(statement=sql, warehouse_id=wh_id)
        state = r.status.state if r.status else "unknown"
        err = (r.status.error.message if r.status and r.status.error else "") or ""
        tag = "OK" if "SUCCEEDED" in str(state) else f"WARN({state} {err})"
        print(f"  UC: {tag} — {sql[:70]}")

    # 2. SQL Warehouse CAN_USE
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
        print(f"  Warehouse CAN_USE granted to {sp}")
    except Exception as e:
        print(f"  Warehouse grant issue (non-fatal): {e}")

    # 3. Lakebase Postgres role + grants
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

        conn = psycopg.connect(
            host="ep-broad-forest-e1dqz0rd.database.eastus2.azuredatabricks.net",
            port=5432,
            dbname="databricks_postgres",
            user=user,
            password=token,
            sslmode="require",
        )
        conn.autocommit = True
        cur = conn.cursor()

        from psycopg import sql

        cur.execute("CREATE EXTENSION IF NOT EXISTS databricks_auth;")  # type: ignore[arg-type]
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

        sp_ident = sql.Identifier(sp)
        grant_stmts = [
            sql.SQL("GRANT ALL PRIVILEGES ON SCHEMA payment_analysis TO {}").format(sp_ident),
            sql.SQL("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA payment_analysis TO {}").format(sp_ident),
            sql.SQL("GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA payment_analysis TO {}").format(sp_ident),
            sql.SQL("ALTER DEFAULT PRIVILEGES IN SCHEMA payment_analysis GRANT ALL ON TABLES TO {}").format(sp_ident),
        ]
        for stmt in grant_stmts:
            cur.execute(stmt)
        print("  Lakebase schema/table/sequence grants complete")

        cur.close()
        conn.close()
    except ImportError:
        print("  Lakebase: psycopg not installed — skipping Postgres grants")
    except Exception as e:
        print(f"  Lakebase grant issue (non-fatal): {e}")

    print("SP permission grants complete.")


if __name__ == "__main__":
    main()
