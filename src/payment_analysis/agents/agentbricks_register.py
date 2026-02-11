# Databricks notebook source
# MAGIC %md
# MAGIC # Register AgentBricks Agents to Unity Catalog (MLflow)
# MAGIC
# MAGIC Logs each specialist (Tool-Calling Agent) and the Orchestrator (Multi-Agent System)
# MAGIC to MLflow and registers them in Unity Catalog under `{catalog}.agents.*`.
# MAGIC
# MAGIC **Prerequisites:**
# MAGIC - UC agent tool functions exist (Job 3: create_uc_agent_tools)
# MAGIC - Schema `agents` exists in the catalog (e.g. `ahs_demos_catalog.agents`)
# MAGIC
# MAGIC **Outcome:** Models registered as `{catalog}.agents.decline_analyst`, `smart_routing`, `smart_retry`, `risk_assessor`, `performance_recommender`, `orchestrator`. You can then deploy them to Model Serving or add to the workspace Agents (AgentBricks) UI.

# COMMAND ----------

import os
import json

# COMMAND ----------

def _get_config():
    """Read catalog, schema, and model registry from widgets or env."""
    defaults = {
        "catalog": os.environ.get("CATALOG", "ahs_demos_catalog"),
        "schema": os.environ.get("SCHEMA", "payment_analysis"),
        "model_registry_schema": os.environ.get("MODEL_REGISTRY_SCHEMA", "agents"),
        "llm_endpoint": os.environ.get("LLM_ENDPOINT", "databricks-meta-llama-3-3-70b-instruct"),
    }
    try:
        from databricks.sdk.runtime import dbutils
        dbutils.widgets.text("catalog", defaults["catalog"])
        dbutils.widgets.text("schema", defaults["schema"])
        dbutils.widgets.text("model_registry_schema", defaults["model_registry_schema"])
        dbutils.widgets.text("llm_endpoint", defaults["llm_endpoint"])
        return {
            "catalog": (dbutils.widgets.get("catalog") or defaults["catalog"]).strip(),
            "schema": (dbutils.widgets.get("schema") or defaults["schema"]).strip(),
            "model_registry_schema": (dbutils.widgets.get("model_registry_schema") or defaults["model_registry_schema"]).strip(),
            "llm_endpoint": (dbutils.widgets.get("llm_endpoint") or defaults["llm_endpoint"]).strip(),
        }
    except Exception:
        return defaults

# COMMAND ----------

def register_agents():
    """Log each agent to MLflow and register to UC. Returns list of registered model names."""
    import mlflow
    from mlflow import set_registry_uri

    from payment_analysis.agents.langgraph_agents import (
        get_all_agent_builders,
        create_orchestrator_agent,
    )

    config = _get_config()
    catalog = config["catalog"]
    schema = config["schema"]
    model_schema = config["model_registry_schema"]
    llm_endpoint = config["llm_endpoint"]
    registered = []

    set_registry_uri("databricks-uc")
    mlflow.set_experiment(f"/Users/{os.environ.get('USER', 'unknown')}/agentbricks_register")

    # 1. Register each specialist (Tool-Calling Agent)
    for create_fn, suffix in get_all_agent_builders():
        model_name = f"{catalog}.{model_schema}.{suffix}"
        with mlflow.start_run(run_name=f"register_{suffix}"):
            agent = create_fn(catalog, schema=schema, llm_endpoint=llm_endpoint)
            mlflow.langchain.log_model(
                lc_model=agent,
                artifact_path="model",
                registered_model_name=model_name,
            )
            registered.append(model_name)
            print(f"Registered: {model_name}")

    # 2. Register Orchestrator (Multi-Agent System)
    with mlflow.start_run(run_name="register_orchestrator"):
        orchestrator = create_orchestrator_agent(catalog, schema=schema, llm_endpoint=llm_endpoint)
        model_name = f"{catalog}.{model_schema}.orchestrator"
        mlflow.langchain.log_model(
            lc_model=orchestrator,
            artifact_path="model",
            registered_model_name=model_name,
        )
        registered.append(model_name)
        print(f"Registered: {model_name}")

    return registered

# COMMAND ----------

if __name__ == "__main__":
    registered = register_agents()
    print("\n" + "=" * 60)
    print("AgentBricks registration complete")
    print("=" * 60)
    for name in registered:
        print(f"  - {name}")
    try:
        from databricks.sdk.runtime import dbutils
        dbutils.notebook.exit(json.dumps({"registered_models": registered}))
    except Exception:
        pass
