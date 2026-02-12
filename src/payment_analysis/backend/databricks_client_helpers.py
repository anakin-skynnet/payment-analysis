"""
Helpers to create Databricks WorkspaceClient with PAT/OBO token or service principal.

When DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET are set in the environment
(e.g. by Databricks Apps for app authorization), the SDK still loads them into
Config. Passing client_id=None/client_secret=None does not prevent that (the SDK
skips setting attributes when value is None, then loads from env). Passing empty
string can still be overridden in some SDK code paths. The only reliable fix is
to temporarily unset the env vars while constructing the PAT client.
"""

import os
import threading
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from databricks.sdk import WorkspaceClient

_PAT_CLIENT_LOCK = threading.Lock()


def workspace_client_service_principal(host: str, client_id: str, client_secret: str) -> "WorkspaceClient":
    """
    Create a WorkspaceClient using OAuth client credentials (service principal).

    Use when the app runs as a service principal (e.g. DATABRICKS_CLIENT_ID and
    DATABRICKS_CLIENT_SECRET set by Databricks Apps) to execute actions on behalf
    of the app without a user token.
    """
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient(
        host=host,
        client_id=client_id,
        client_secret=client_secret,
    )


def workspace_client_pat_only(host: str, token: str) -> "WorkspaceClient":
    """
    Create a WorkspaceClient using only host + token (PAT or OBO).

    Temporarily unsets DATABRICKS_CLIENT_ID and DATABRICKS_CLIENT_SECRET so the
    SDK does not merge OAuth credentials and trigger "Provided OAuth token does
    not have required scopes" when using a PAT or forwarded user token.
    """
    from databricks.sdk import WorkspaceClient

    with _PAT_CLIENT_LOCK:
        saved_id = os.environ.pop("DATABRICKS_CLIENT_ID", None)
        saved_secret = os.environ.pop("DATABRICKS_CLIENT_SECRET", None)
        try:
            return WorkspaceClient(
                host=host,
                token=token,
                auth_type="pat",
            )
        finally:
            if saved_id is not None:
                os.environ["DATABRICKS_CLIENT_ID"] = saved_id
            if saved_secret is not None:
                os.environ["DATABRICKS_CLIENT_SECRET"] = saved_secret
