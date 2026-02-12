# Agent Stack: What’s Used at Runtime vs AgentBricks

## Short answer

- **Orchestrator chat in the app** can use either:
  - **AgentBricks / Supervisor** (recommended): when **ORCHESTRATOR_SERVING_ENDPOINT** is set (e.g. `payment-analysis-orchestrator`), the app calls that Model Serving endpoint and the UI stays unchanged.
  - **Job 6 (custom Python)**: when the env var is not set or the endpoint call fails, the app falls back to Job 6, task 1 (`agent_framework.py`).
- **AgentBricks (LangGraph)** is used to **build and register** agents to Unity Catalog (Job 6, task 2). The registered **orchestrator** is deployed as the **payment-analysis-orchestrator** serving endpoint (see `model_serving.yml`).
- There is **no “AI Framework PySpark”** in this solution for agents. Tool execution uses **Databricks Statement Execution** (SQL) and **Spark** in notebooks; the agents themselves are Python (custom) or LangGraph (AgentBricks).

---

## Runtime path (what the app uses)

| Component | Implementation | Where |
|-----------|----------------|-------|
| **Orchestrator chat** (`POST /api/agents/orchestrator/chat`) | If **ORCHESTRATOR_SERVING_ENDPOINT** is set: calls that **Model Serving** endpoint (AgentBricks/Supervisor) via `ws.serving_endpoints.query(...)`. Otherwise: triggers **Job 6** (run now), task 1 runs the **custom Python** framework. | Backend: `agents.py` — endpoint path first, then Job 6 fallback. |
| **Agent execution (endpoint)** | **AgentBricks:** Registered orchestrator (`catalog.agents.orchestrator`) served as **payment-analysis-orchestrator**; LangGraph supervisor routes to specialists (UC functions as tools). | `model_serving.yml` → `payment_analysis_orchestrator_endpoint`; app env `ORCHESTRATOR_SERVING_ENDPOINT=payment-analysis-orchestrator`. |
| **Agent execution (Job 6 fallback)** | **Custom Python:** `agent_framework.py` — `BaseAgent`, `OrchestratorAgent`, five specialist classes. Tools = Python callables + Statement Execution; LLM = Mosaic AI. | `src/payment_analysis/agents/agent_framework.py` |
| **Tool execution** | SQL via **Databricks** (Statement Execution in custom framework; UC functions in LangGraph agents). | Same notebook or served model. |

So: **set ORCHESTRATOR_SERVING_ENDPOINT=payment-analysis-orchestrator in the app environment to use AgentBricks at runtime; otherwise the app uses the custom Python framework (Job 6).**

---

## AgentBricks (Mosaic AI Agent Framework) — registration only

| Component | Implementation | Where |
|-----------|----------------|-------|
| **Agent definitions** | **LangGraph** agents: `create_decline_analyst_agent`, `create_smart_routing_agent`, etc., plus **orchestrator** (supervisor). Tools = **Unity Catalog functions** via UCFunctionToolkit / ChatDatabricks. | `src/payment_analysis/agents/langgraph_agents.py` |
| **Registration** | **Job 6, task 2:** `agentbricks_register.py` logs each agent (and orchestrator) to **MLflow** and registers them in **Unity Catalog** (e.g. `catalog.agents.decline_analyst`, `catalog.agents.orchestrator`). | `src/payment_analysis/agents/agentbricks_register.py`; Job 6 task `register_agentbricks` |
| **Use today** | Registered models can be **deployed to Model Serving** or used in the **Databricks Agents (AgentBricks)** UI. The **app does not call** these Model Serving endpoints for orchestrator chat; it only triggers Job 6 (which runs the custom framework in task 1). | — |

When the **payment-analysis-orchestrator** endpoint is deployed and **ORCHESTRATOR_SERVING_ENDPOINT** is set, the app invokes that AgentBricks orchestrator at runtime.

---

## PySpark vs “AI Framework PySpark”

- **PySpark** is used in the project for **data and SQL** (e.g. gold views, UC function creation, Genie sync) in notebooks. It is **not** used as an “agent framework” (no PySpark-based agent API or agent runtime).
- There is **no** separate “AI Framework PySpark” product or layer in this repo. Agents are either:
  - **Custom Python** (`agent_framework.py`), or  
  - **LangGraph (AgentBricks)** (`langgraph_agents.py`), registered to UC and deployable to Model Serving.

---

## Summary table

| Question | Answer |
|----------|--------|
| Are you using **Mosaic AI Agent Framework (AgentBricks)** agents at runtime for the app? | **Yes, when ORCHESTRATOR_SERVING_ENDPOINT is set.** The app then calls the configured Model Serving endpoint (e.g. `payment-analysis-orchestrator`). Otherwise it falls back to the **custom Python** framework (Job 6, task 1). |
| Are AgentBricks agents used at all? | **Yes.** Job 6, task 2 registers LangGraph agents to UC; the orchestrator is deployed as **payment-analysis-orchestrator**. Set the env var to use it from the app. |
| Are you using **AI Framework PySpark**? | **No.** There is no PySpark-based agent framework here. Tools run SQL via Databricks (Statement Execution); agent logic is Python or LangGraph. |

---

## Using the AgentBricks / Supervisor orchestrator in the app

1. **Register agents** (Job 6, task 2) so `catalog.agents.orchestrator` exists.
2. **Include** `resources/model_serving.yml` in `databricks.yml` and **deploy** so the **payment-analysis-orchestrator** endpoint is created.
3. In **Workspace → Apps → payment-analysis → Edit → Environment**, set:
   - **ORCHESTRATOR_SERVING_ENDPOINT** = `payment-analysis-orchestrator`
4. The app’s Orchestrator chat will then call that endpoint instead of Job 6. The UI (OrchestratorChatIn / OrchestratorChatOut) is unchanged.

---

## No-code Supervisor Agent (Databricks workspace)

**Supervisor Agent** (Workspace → Agents → Supervisor Agent) lets you combine Genie spaces, other agents, and tools in the UI with no code. To use it with the app:

1. In the workspace, create a **Supervisor Agent** and add your Genie space, UC functions, and/or other agents as subagents.
2. Deploy or expose the supervisor so it has an **endpoint name** (e.g. a Model Serving endpoint created from that agent).
3. Set **ORCHESTRATOR_SERVING_ENDPOINT** in the app environment to that endpoint name. The app will call it the same way as the LangGraph orchestrator.

If the no-code Supervisor is not deployed as a serving endpoint with a name you can call via `serving_endpoints.query`, use the **payment-analysis-orchestrator** endpoint (registered LangGraph orchestrator) as above.

See [APPROVAL_OPTIMIZATION_PROPOSAL.md](APPROVAL_OPTIMIZATION_PROPOSAL.md) and [DATABRICKS.md](DATABRICKS.md) Part 3.
