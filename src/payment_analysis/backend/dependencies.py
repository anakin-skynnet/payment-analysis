"""Dependencies for FastAPI: config, runtime, session, Databricks client and service.

This module implements patterns for Databricks Apps:
- User authorization (on-behalf-of): token from x-forwarded-access-token header.
- Workspace URL derivation from X-Forwarded-Host / Host when app is served from Apps.
- Service principal + user token pattern: use SP for app-level operations (app_config,
  session, stats); use user token (X-Forwarded-Access-Token) for user-scoped operations
  (warehouse queries, run job on behalf of user). Example: query_warehouse(user_token)
  vs get_user_session(sp_cfg, email) / save_user_session(sp_cfg, email).
See: https://docs.databricks.com/aws/en/dev-tools/databricks-apps/configuration
     https://docs.databricks.com/aws/en/dev-tools/databricks-apps/auth
     https://docs.databricks.com/aws/en/dev-tools/databricks-apps/http-headers
Tokens are never logged or exposed in responses.
"""

import os
from typing import Annotated, Generator

from databricks.sdk import WorkspaceClient
from fastapi import Depends, Header, HTTPException, Request
from sqlmodel import Session

from .config import (
    AppConfig,
    WORKSPACE_URL_PLACEHOLDER,
    app_name,
    ensure_absolute_workspace_url,
    workspace_url_from_apps_host,
)
from .databricks_client_helpers import workspace_client_pat_only, workspace_client_service_principal
from .logger import logger
from .runtime import Runtime
from .services.databricks_service import DatabricksConfig, DatabricksService

# Shared message when no credentials are available (exported for use in routes)
AUTH_REQUIRED_DETAIL = (
    "Open this app from Workspace → Compute → Apps → payment-analysis so the platform forwards your token (recommended), "
    "or set DATABRICKS_TOKEN, or ensure the app's service principal credentials (DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET) are set in the app environment."
)


def get_config(request: Request) -> AppConfig:
    """
    Returns the AppConfig instance from app.state.
    The config is initialized during application lifespan startup.
    """
    if not hasattr(request.app.state, "config"):
        raise RuntimeError(
            "AppConfig not initialized. "
            "Ensure app.state.config is set during application lifespan startup."
        )
    return request.app.state.config


ConfigDep = Annotated[AppConfig, Depends(get_config)]


def get_runtime(request: Request) -> Runtime:
    """
    Returns the Runtime instance from app.state.
    The runtime is initialized during application lifespan startup.
    """
    if not hasattr(request.app.state, "runtime"):
        raise RuntimeError(
            "Runtime not initialized. "
            "Ensure app.state.runtime is set during application lifespan startup."
        )
    return request.app.state.runtime


RuntimeDep = Annotated[Runtime, Depends(get_runtime)]


def get_obo_ws(
    request: Request,
    token: Annotated[str | None, Header(alias="X-Forwarded-Access-Token")] = None,
) -> WorkspaceClient:
    """
    Returns a Databricks Workspace client (on-behalf-of user).
    Requires X-Forwarded-Access-Token header. Host is taken from app config so the client targets the correct workspace.
    """
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required: X-Forwarded-Access-Token header is missing",
        )
    config = get_config(request)
    raw = _config_raw_host(config)
    if not raw:
        raise HTTPException(status_code=503, detail="DATABRICKS_HOST is not set.")
    host = ensure_absolute_workspace_url(raw)
    return workspace_client_pat_only(host=host, token=token)


def _request_host_for_derivation(request: Request) -> str:
    """Host value to use for deriving workspace URL (X-Forwarded-Host when present, else Host)."""
    forwarded = request.headers.get("X-Forwarded-Host") or request.headers.get("x-forwarded-host")
    if forwarded and str(forwarded).strip():
        return str(forwarded).strip().split(",")[0].strip()
    return request.headers.get("host") or ""


def _config_raw_host(config: AppConfig) -> str:
    """Normalized workspace URL from config, empty string if placeholder or missing."""
    raw = (config.databricks.workspace_url or "").strip().rstrip("/")
    if not raw or raw == WORKSPACE_URL_PLACEHOLDER.rstrip("/"):
        return ""
    return raw


def get_effective_workspace_url(request: Request, config: ConfigDep) -> str:
    """
    Workspace URL to use for dashboard embed and config. When the request is from a Databricks
    Apps host (e.g. *.databricksapps.com), derive the workspace URL from the request so end
    users always get their own workspace URL instead of a hardcoded or env-only host.
    """
    request_host = _request_host_for_derivation(request)
    if _is_apps_host(request_host):
        derived = workspace_url_from_apps_host(request_host, app_name).strip().rstrip("/")
        if derived:
            return ensure_absolute_workspace_url(derived).rstrip("/")
    raw = _config_raw_host(config)
    if not raw:
        return ""
    return ensure_absolute_workspace_url(raw).rstrip("/")


EffectiveWorkspaceUrlDep = Annotated[str, Depends(get_effective_workspace_url)]


def _is_apps_host(host: str) -> bool:
    """True if host looks like a Databricks Apps URL (e.g. payment-analysis-xxx.databricksapps.com)."""
    return bool(host and "databricksapps" in host.lower())


def _get_obo_token(request: Request) -> str | None:
    """User token when app is opened from Compute → Apps (user authorization / OBO).
    Primary: x-forwarded-access-token (Databricks Apps HTTP header). Fallback: Authorization Bearer when on Apps host."""
    # Primary: x-forwarded-access-token (Databricks Apps; case-insensitive)
    v = request.headers.get("X-Forwarded-Access-Token") or request.headers.get("x-forwarded-access-token")
    if v and str(v).strip():
        return v.strip()
    # Fallback when request is clearly from Apps: Authorization: Bearer (some proxies inject user token here)
    host = _request_host_for_derivation(request)
    if _is_apps_host(host):
        auth = request.headers.get("Authorization") or request.headers.get("authorization")
        if auth and str(auth).strip().lower().startswith("bearer "):
            token = str(auth).strip()[7:].strip()
            if token:
                return token
    return None


def get_workspace_client(request: Request) -> WorkspaceClient:
    """
    Returns a Databricks Workspace client. Credentials, in order of precedence:
    1. User token (OBO) when opened from Compute → Apps (X-Forwarded-Access-Token).
    2. DATABRICKS_TOKEN (PAT).
    3. Service principal: DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET (injected by
       Databricks Apps so the app can execute actions on behalf of the app).
    Host is always absolute (https://...). When DATABRICKS_HOST is unset, derives host
    from the request when the app is served from a Databricks Apps URL.
    """
    obo_token = _get_obo_token(request)
    config = get_config(request)
    raw = _config_raw_host(config) or workspace_url_from_apps_host(
        _request_host_for_derivation(request), app_name
    ).strip().rstrip("/")
    if not raw:
        raise HTTPException(
            status_code=503,
            detail="DATABRICKS_HOST is not set. Set it in the app environment or open the app from Compute → Apps so the workspace URL can be derived.",
        )
    host = ensure_absolute_workspace_url(raw)

    token = obo_token or os.environ.get("DATABRICKS_TOKEN")
    if token:
        return workspace_client_pat_only(host=host, token=token)

    client_id = os.environ.get("DATABRICKS_CLIENT_ID")
    client_secret = os.environ.get("DATABRICKS_CLIENT_SECRET")
    if client_id and client_secret:
        return workspace_client_service_principal(host=host, client_id=client_id, client_secret=client_secret)

    raise HTTPException(status_code=401, detail=AUTH_REQUIRED_DETAIL)


def get_workspace_client_optional(request: Request) -> WorkspaceClient | None:
    """
    Returns a Workspace client when credentials are available; otherwise None.
    Used by GET /setup/defaults to resolve job/pipeline IDs from the workspace when possible.
    Credentials: OBO token (X-Forwarded-Access-Token), then DATABRICKS_TOKEN, then
    service principal (DATABRICKS_CLIENT_ID + DATABRICKS_CLIENT_SECRET).
    """
    obo_token = _get_obo_token(request)
    config = get_config(request)
    raw = _config_raw_host(config) or workspace_url_from_apps_host(
        _request_host_for_derivation(request), app_name
    ).strip().rstrip("/")
    if not raw:
        return None

    host = ensure_absolute_workspace_url(raw)
    token = obo_token or os.environ.get("DATABRICKS_TOKEN")
    if token:
        return workspace_client_pat_only(host=host, token=token)
    client_id = os.environ.get("DATABRICKS_CLIENT_ID")
    client_secret = os.environ.get("DATABRICKS_CLIENT_SECRET")
    if client_id and client_secret:
        return workspace_client_service_principal(host=host, client_id=client_id, client_secret=client_secret)
    return None


def get_session(rt: RuntimeDep) -> Generator[Session, None, None]:
    """
    Returns a SQLModel session. Raises 503 if database is not configured or unavailable.
    """
    try:
        with rt.get_session() as session:
            yield session
    except HTTPException:
        raise
    except (RuntimeError, ValueError) as e:
        if "not configured" in str(e).lower():
            raise HTTPException(
                status_code=503,
                detail="Database not configured. Set LAKEBASE_PROJECT_ID, LAKEBASE_BRANCH_ID, LAKEBASE_ENDPOINT_ID in the app Environment (same as Job 1 create_lakebase_autoscaling).",
            ) from e
        raise HTTPException(
            status_code=503,
            detail=f"Database unavailable: {e}",
        ) from e
    except ConnectionError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database connection failed: {e}",
        ) from e
    except Exception as e:
        # Catch-all for psycopg, sqlalchemy, and other DB driver errors
        logger.warning("Database session error: %s", e, exc_info=False)
        raise HTTPException(
            status_code=503,
            detail=f"Database temporarily unavailable: {type(e).__name__}",
        ) from e


SessionDep = Annotated[Session, Depends(get_session)]


def get_session_optional(rt: RuntimeDep) -> Generator[Session | None, None, None]:
    """
    Returns a SQLModel session when available; ``None`` when the database is
    down or not configured. Use for routes that have a Databricks/Lakehouse
    fallback and don't strictly need Lakebase.
    """
    try:
        with rt.get_session() as session:
            yield session
    except Exception as exc:
        logger.debug("Optional session unavailable: %s", exc)
        yield None


OptionalSessionDep = Annotated[Session | None, Depends(get_session_optional)]


def _effective_databricks_host(request: Request, bootstrap_host: str | None) -> str | None:
    """Workspace host from env or derived from request (X-Forwarded-Host / Host) when running as a Databricks App."""
    raw = (bootstrap_host or "").strip().rstrip("/")
    if raw and "example.databricks.com" not in raw:
        return raw
    derived = workspace_url_from_apps_host(_request_host_for_derivation(request), app_name).strip().rstrip("/")
    return derived if derived else None


def get_workspace_client_app_identity(request: Request) -> WorkspaceClient | None:
    """
    Returns a Workspace client using only the service principal (DATABRICKS_CLIENT_ID/SECRET).

    Use for app-level operations (e.g. app_config, session DB, stats). For user-scoped
    operations (warehouse queries, run job on behalf of user) use get_workspace_client
    so the user token (X-Forwarded-Access-Token) is used when present.
    """
    config = get_config(request)
    raw = _config_raw_host(config) or workspace_url_from_apps_host(
        _request_host_for_derivation(request), app_name
    ).strip().rstrip("/")
    if not raw:
        return None
    client_id = os.environ.get("DATABRICKS_CLIENT_ID")
    client_secret = os.environ.get("DATABRICKS_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None
    host = ensure_absolute_workspace_url(raw)
    return workspace_client_service_principal(host=host, client_id=client_id, client_secret=client_secret)


async def get_databricks_service_app_identity(request: Request) -> DatabricksService | None:
    """
    Returns a DatabricksService using only the service principal (for app-level operations).

    Use for reading/writing app_config, session, or other app-managed data. For
    user-scoped warehouse queries use get_databricks_service (user token when present).
    """
    bootstrap = DatabricksConfig.from_environment()
    effective_host = _effective_databricks_host(request, bootstrap.host)
    if not effective_host or not bootstrap.client_id or not bootstrap.client_secret:
        return None
    config = DatabricksConfig(
        host=effective_host,
        token=None,
        client_id=bootstrap.client_id,
        client_secret=bootstrap.client_secret,
        warehouse_id=bootstrap.warehouse_id,
        catalog=bootstrap.catalog,
        schema=bootstrap.schema,
    )
    return DatabricksService(config=config)


async def get_databricks_service(request: Request) -> DatabricksService:
    """
    Returns a DatabricksService using the forwarded user token when the app is opened
    from Compute → Apps (OBO), or DATABRICKS_TOKEN when set. Host is taken from
    DATABRICKS_HOST or derived from the request Host when served from a Databricks Apps URL.
    Catalog/schema come from app_config in Lakehouse (loaded at startup or lazy on first request).
    """
    bootstrap = DatabricksConfig.from_environment()
    obo_token = _get_obo_token(request)
    token = obo_token or bootstrap.token
    effective_host = _effective_databricks_host(request, bootstrap.host)
    catalog, schema = getattr(request.app.state, "uc_config", (None, None))
    if not catalog or not schema:
        catalog, schema = bootstrap.catalog, bootstrap.schema
    # Lazy-load catalog/schema from app_config in Lakehouse once (skip if already from Lakebase).
    # Prefer service principal for app_config (app-level data); fall back to user token if no SP.
    lazy_tried = getattr(request.app.state, "uc_config_lazy_tried", False)
    from_lakebase = getattr(request.app.state, "uc_config_from_lakebase", False)
    if not from_lakebase and not getattr(request.app.state, "uc_config_from_lakehouse", False) and not lazy_tried:
        if effective_host and bootstrap.warehouse_id:
            request.app.state.uc_config_lazy_tried = True
            row = None
            try:
                # Use SP for app_config when available (app-level data)
                if bootstrap.client_id and bootstrap.client_secret:
                    sp_svc = await get_databricks_service_app_identity(request)
                    if sp_svc:
                        row = await sp_svc.read_app_config()
                # Fall back to user token (OBO) for read_app_config
                if (not row or not row[0] or not row[1]) and obo_token:
                    lazy_config = DatabricksConfig(
                        host=effective_host,
                        token=obo_token,
                        warehouse_id=bootstrap.warehouse_id,
                        catalog=bootstrap.catalog,
                        schema=bootstrap.schema,
                    )
                    lazy_svc = DatabricksService(config=lazy_config)
                    row = await lazy_svc.read_app_config()
                if row and row[0] and row[1]:
                    request.app.state.uc_config = row
                    request.app.state.uc_config_from_lakehouse = True
                    catalog, schema = row
            except Exception:
                logger.debug("Lazy UC config lookup failed; using env defaults", exc_info=True)
    # When no user token, use service principal (DATABRICKS_CLIENT_ID/SECRET from Apps) if set
    config = DatabricksConfig(
        host=effective_host,
        token=token,
        client_id=bootstrap.client_id if not token else None,
        client_secret=bootstrap.client_secret if not token else None,
        warehouse_id=bootstrap.warehouse_id,
        catalog=catalog,
        schema=schema,
    )
    return DatabricksService(config=config)


DatabricksServiceDep = Annotated[DatabricksService, Depends(get_databricks_service)]
