"""Read app_config and app_settings from Lakebase (Postgres). Used at startup so backend processes use these before calling Lakehouse."""
# pyright: reportDeprecated=false  # session.execute() with text() for raw SQL; exec() is for ORM select

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import text

from .logger import logger

if TYPE_CHECKING:
    from .runtime import Runtime


def _safe_schema_name(raw: str) -> str:
    """Validate and return a safe schema name for SQL interpolation."""
    name = (raw or "payment_analysis").strip() or "payment_analysis"
    if not name.replace("_", "").isalnum():
        raise ValueError(f"Invalid schema name: {name!r} — only alphanumeric and underscore allowed")
    return name


def load_app_config_and_settings(runtime: Runtime) -> tuple[tuple[str, str] | None, dict[str, str]]:
    """
    Read app_config (catalog, schema) and app_settings (key-value) from Lakebase.
    Returns ((catalog, schema) or None, settings_dict). Use at startup before any Lakehouse calls.
    """
    config = runtime.config
    schema_name = _safe_schema_name(config.db.db_schema or "payment_analysis")
    if not runtime._db_configured():
        return (None, {})

    uc_config: tuple[str, str] | None = None
    settings: dict[str, str] = {}

    try:
        with runtime.get_session() as session:
            # Quoted identifier for PostgreSQL schema
            q = text(f'SELECT catalog, schema FROM "{schema_name}".app_config LIMIT 1')
            result = session.execute(q)
            row = result.fetchone()
            if row:
                c, s = str(row[0] or "").strip(), str(row[1] or "").strip()
                if c and s:
                    uc_config = (c, s)

            q2 = text(f'SELECT key, value FROM "{schema_name}".app_settings')
            result2 = session.execute(q2)
            for r in result2.fetchall():
                if r and len(r) >= 2:
                    settings[str(r[0])] = str(r[1] or "")
    except Exception as e:
        logger.warning("Could not read app_config/app_settings from Lakebase: %s", e)

    return (uc_config, settings)


def write_app_settings_keys(runtime: Runtime, settings: dict[str, str]) -> bool:
    """Write key-value pairs to Lakebase app_settings (e.g. control panel flags). Returns True on success."""
    config = runtime.config
    schema_name = _safe_schema_name(config.db.db_schema or "payment_analysis")
    if not runtime._db_configured() or not settings:
        return bool(settings)
    try:
        with runtime.get_session() as session:
            for key, val in settings.items():
                if not key or not isinstance(val, str):
                    continue
                q = text(
                    f"""
                    INSERT INTO "{schema_name}".app_settings (key, value)
                    VALUES (:key, :value)
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = current_timestamp
                    """
                )
                session.execute(q, {"key": key, "value": val})
            session.commit()
        return True
    except Exception as e:
        logger.warning("Could not write app_settings keys to Lakebase: %s", e)
        return False


def write_app_config(runtime: Runtime, catalog: str, schema: str) -> bool:
    """Write catalog and schema to Lakebase app_config and app_settings. Call after user saves config."""
    config = runtime.config
    schema_name = _safe_schema_name(config.db.db_schema or "payment_analysis")
    if not runtime._db_configured():
        return False
    try:
        with runtime.get_session() as session:
            q = text(
                f"""
                INSERT INTO "{schema_name}".app_config (id, catalog, schema)
                VALUES (1, :catalog, :schema)
                ON CONFLICT (id) DO UPDATE SET catalog = EXCLUDED.catalog, schema = EXCLUDED.schema, updated_at = current_timestamp
                """
            )
            session.execute(q, {"catalog": catalog, "schema": schema})
            for key, val in [("catalog", catalog), ("schema", schema)]:
                q2 = text(
                    f"""
                    INSERT INTO "{schema_name}".app_settings (key, value)
                    VALUES (:key, :value)
                    ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = current_timestamp
                    """
                )
                session.execute(q2, {"key": key, "value": val})
            session.commit()
        return True
    except Exception as e:
        logger.warning("Could not write app_config to Lakebase: %s", e)
        return False


def get_approval_rules_from_lakebase(
    runtime: Runtime,
    *,
    rule_type: str | None = None,
    active_only: bool = False,
    limit: int = 200,
) -> list[dict[str, Any]] | None:
    """Read approval_rules from Lakebase. Returns list of dicts, or None on error/unconfigured (caller should fall back to Lakehouse)."""
    config = runtime.config
    schema_name = _safe_schema_name(config.db.db_schema or "payment_analysis")
    if not runtime._db_configured():
        return None
    limit = max(1, min(limit, 500))
    try:
        with runtime.get_session() as session:
            where = "WHERE is_active = true" if active_only else ""
            if rule_type:
                where += f" AND rule_type = :rule_type" if where else "WHERE rule_type = :rule_type"
            q = text(
                f"""
                SELECT id, name, rule_type, condition_expression, action_summary, priority, is_active, created_at, updated_at
                FROM "{schema_name}".approval_rules
                {where}
                ORDER BY priority ASC, updated_at DESC
                LIMIT :limit
                """
            )
            params: dict[str, Any] = {"limit": limit}
            if rule_type:
                params["rule_type"] = rule_type
            result = session.execute(q, params)
            rows = result.fetchall()
            return [
                {
                    "id": str(r[0]),
                    "name": str(r[1]),
                    "rule_type": str(r[2]),
                    "condition_expression": str(r[3]) if r[3] else None,
                    "action_summary": str(r[4]),
                    "priority": int(r[5]) if r[5] is not None else 100,
                    "is_active": bool(r[6]) if r[6] is not None else True,
                    "created_at": r[7],
                    "updated_at": r[8],
                }
                for r in rows
            ]
    except Exception as e:
        logger.debug("Could not read approval_rules from Lakebase: %s", e)
        return None


def get_countries_from_lakebase(runtime: Runtime, *, limit: int = 200) -> list[dict[str, Any]] | None:
    """Read countries/entities from Lakebase for the UI filter dropdown. Returns list of {code, name} or None on error/unconfigured."""
    config = runtime.config
    schema_name = _safe_schema_name(config.db.db_schema or "payment_analysis")
    if not runtime._db_configured():
        return None
    limit = max(1, min(limit, 500))
    try:
        with runtime.get_session() as session:
            q = text(
                f"""
                SELECT code, name
                FROM "{schema_name}".countries
                WHERE is_active = true
                ORDER BY display_order ASC, name ASC
                LIMIT :limit
                """
            )
            result = session.execute(q, {"limit": limit})
            rows = result.fetchall()
            if not rows:
                return None
            return [
                {"code": str(r[0] or "").strip() or "", "name": str(r[1] or "").strip() or ""}
                for r in rows
            ]
    except Exception as e:
        logger.debug("Could not read countries from Lakebase: %s", e)
        return None


def get_approval_rule_by_id(runtime: Runtime, rule_id: str) -> dict[str, Any] | None:
    """Return one approval rule from Lakebase by id, or None if not found / unconfigured."""
    config = runtime.config
    schema_name = _safe_schema_name(config.db.db_schema or "payment_analysis")
    if not runtime._db_configured():
        return None
    try:
        with runtime.get_session() as session:
            q = text(
                f"""
                SELECT id, name, rule_type, condition_expression, action_summary, priority, is_active, created_at, updated_at
                FROM "{schema_name}".approval_rules
                WHERE id = :rule_id
                LIMIT 1
                """
            )
            result = session.execute(q, {"rule_id": rule_id})
            r = result.fetchone()
            if not r:
                return None
            return {
                "id": str(r[0]),
                "name": str(r[1]),
                "rule_type": str(r[2]),
                "condition_expression": str(r[3]) if r[3] else None,
                "action_summary": str(r[4]),
                "priority": int(r[5]) if r[5] is not None else 100,
                "is_active": bool(r[6]) if r[6] is not None else True,
                "created_at": r[7],
                "updated_at": r[8],
            }
    except Exception as e:
        logger.debug("Could not read approval_rule by id from Lakebase: %s", e)
        return None


def create_approval_rule_in_lakebase(
    runtime: Runtime,
    *,
    id: str,
    name: str,
    rule_type: str,
    action_summary: str,
    condition_expression: str | None = None,
    priority: int = 100,
    is_active: bool = True,
) -> bool:
    """Insert one approval rule into Lakebase. Returns True on success."""
    config = runtime.config
    schema_name = _safe_schema_name(config.db.db_schema or "payment_analysis")
    if not runtime._db_configured():
        return False
    try:
        with runtime.get_session() as session:
            q = text(
                f"""
                INSERT INTO "{schema_name}".approval_rules
                (id, name, rule_type, condition_expression, action_summary, priority, is_active)
                VALUES (:id, :name, :rule_type, :condition_expression, :action_summary, :priority, :is_active)
                """
            )
            session.execute(
                q,
                {
                    "id": id,
                    "name": name,
                    "rule_type": rule_type,
                    "condition_expression": condition_expression or None,
                    "action_summary": action_summary,
                    "priority": priority,
                    "is_active": is_active,
                },
            )
            session.commit()
        return True
    except Exception as e:
        logger.warning("Could not create approval_rule in Lakebase: %s", e)
        return False


def update_approval_rule_in_lakebase(
    runtime: Runtime,
    rule_id: str,
    *,
    name: str | None = None,
    rule_type: str | None = None,
    condition_expression: str | None = None,
    action_summary: str | None = None,
    priority: int | None = None,
    is_active: bool | None = None,
) -> bool | None:
    """Update one approval rule in Lakebase. Returns True if a row was updated, False if rule not found (0 rows), None on error."""
    config = runtime.config
    schema_name = _safe_schema_name(config.db.db_schema or "payment_analysis")
    if not runtime._db_configured():
        return None
    try:
        with runtime.get_session() as session:
            # Build SET clause from provided fields
            updates: list[str] = ["updated_at = current_timestamp"]
            params: dict[str, Any] = {"rule_id": rule_id}
            if name is not None:
                updates.append("name = :name")
                params["name"] = name
            if rule_type is not None:
                updates.append("rule_type = :rule_type")
                params["rule_type"] = rule_type
            if condition_expression is not None:
                updates.append("condition_expression = :condition_expression")
                params["condition_expression"] = condition_expression
            if action_summary is not None:
                updates.append("action_summary = :action_summary")
                params["action_summary"] = action_summary
            if priority is not None:
                updates.append("priority = :priority")
                params["priority"] = priority
            if is_active is not None:
                updates.append("is_active = :is_active")
                params["is_active"] = is_active
            if len(updates) <= 1:
                # Only updated_at; still run UPDATE to touch the row
                pass
            q = text(
                f"""
                UPDATE "{schema_name}".approval_rules
                SET {", ".join(updates)}
                WHERE id = :rule_id
                """
            )
            result = session.execute(q, params)
            session.commit()
            return (getattr(result, "rowcount", 0) or 0) > 0
    except Exception as e:
        logger.warning("Could not update approval_rule in Lakebase: %s", e)
        return None


def delete_approval_rule_in_lakebase(runtime: Runtime, rule_id: str) -> bool:
    """Delete one approval rule from Lakebase. Returns True if the DELETE ran successfully (idempotent: 0 or 1 row), False on error."""
    config = runtime.config
    schema_name = _safe_schema_name(config.db.db_schema or "payment_analysis")
    if not runtime._db_configured():
        return False
    try:
        with runtime.get_session() as session:
            q = text(f'DELETE FROM "{schema_name}".approval_rules WHERE id = :rule_id')
            session.execute(q, {"rule_id": rule_id})
            session.commit()
            return True
    except Exception as e:
        logger.warning("Could not delete approval_rule from Lakebase: %s", e)
        return False


def get_online_features_from_lakebase(
    runtime: Runtime,
    *,
    source: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]] | None:
    """Read online_features from Lakebase (last 24h). Returns list of dicts, or None on error (caller should fall back to Lakehouse)."""
    config = runtime.config
    schema_name = _safe_schema_name(config.db.db_schema or "payment_analysis")
    if not runtime._db_configured():
        return None
    limit = max(1, min(limit, 500))
    try:
        with runtime.get_session() as session:
            where = "WHERE created_at >= current_timestamp - interval '24 hours'"
            if source and source.lower() in ("ml", "agent"):
                where += " AND source = :source"
            q = text(
                f"""
                SELECT id, source, feature_set, feature_name, feature_value, feature_value_str, entity_id, created_at
                FROM "{schema_name}".online_features
                {where}
                ORDER BY created_at DESC
                LIMIT :limit
                """
            )
            params: dict[str, Any] = {"limit": limit}
            if source and source.lower() in ("ml", "agent"):
                params["source"] = source.lower()
            result = session.execute(q, params)
            rows = result.fetchall()
            return [
                {
                    "id": str(r[0]),
                    "source": str(r[1]),
                    "feature_set": str(r[2]) if r[2] else None,
                    "feature_name": str(r[3]),
                    "feature_value": float(r[4]) if r[4] is not None else None,
                    "feature_value_str": str(r[5]) if r[5] else None,
                    "entity_id": str(r[6]) if r[6] else None,
                    "created_at": r[7],
                }
                for r in rows
            ]
    except Exception as e:
        logger.debug("Could not read online_features from Lakebase: %s", e)
        return None
