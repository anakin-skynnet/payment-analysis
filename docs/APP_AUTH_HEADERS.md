# Getting the user token (HTTP headers)

When the app is opened from **Compute → Apps**, Databricks forwards the user's token in the **X-Forwarded-Access-Token** header. Use it for on-behalf-of (OBO) operations (e.g. warehouse queries, run job).

Different frameworks expose the request differently. Examples:

## FastAPI

```python
# In a route: inject Request and read the header
from fastapi import Request

@app.get("/example")
def example(request: Request):
    user_token = request.headers.get("X-Forwarded-Access-Token")
    # or case-insensitive fallback:
    user_token = request.headers.get("X-Forwarded-Access-Token") or request.headers.get("x-forwarded-access-token")
    return {"has_token": bool(user_token)}
```

In this project, the token is read in `src/payment_analysis/backend/dependencies.py` via `_get_obo_token(request)` and used by `get_workspace_client` / `get_databricks_service`.

## Dash and Flask

```python
user_token = flask.request.headers.get('X-Forwarded-Access-Token')
```

## Gradio

```python
# 'request' is a parameter of your callback
user_token = request.headers.get('X-Forwarded-Access-Token')
```

## Shiny

```python
# 'session' is a parameter of your server function
user_token = session.http_conn.headers.get('X-Forwarded-Access-Token', None)
```

## Streamlit

```python
user_token = st.context.headers.get('X-Forwarded-Access-Token')
```

## Optional: user email

Some proxies also set **X-Forwarded-Email**. In FastAPI:

```python
email = request.headers.get("X-Forwarded-Email")
```

Use it for user session lookups or audit when needed.
