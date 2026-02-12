# Approval Rate Optimization: Artifacts, Orchestration & App Integration

This document reviews all solution artifacts (registered models, UC functions, agents) and proposes how to leverage them to **maximize insights and actions that accelerate approval rates**—including whether to use a **Supervisor AgentBricks** (or Mosaic Agent) to orchestrate and how to bring information from all models into the app.

---

## 1. Artifact map: what you have and how it drives approval rates

### 1.1 Registered models (serve as endpoints)

| Model | Purpose | Approval-rate impact | Current use in app |
|-------|---------|----------------------|--------------------|
| **approval_propensity_model** | Predicts P(approve) per transaction | **Reduce false declines**: approve when propensity is high; decline only when low. | Decisioning: `/api/decision/ml/approval`; Command Center / Decisioning UI. |
| **risk_scoring_model** | Fraud/risk score per transaction | **Risk-based auth**: low risk → frictionless; high risk → step-up (3DS). Balances approval rate vs fraud loss. | Decisioning: `/api/decision/ml/risk`; auth policy uses risk tier. |
| **smart_routing_policy** | Recommends best payment route (standard, 3DS, token, passkey) | **Route to the solution** that has the highest approval rate for that segment. | Decisioning: `/api/decision/ml/routing`. |
| **smart_retry_policy** | Retry success likelihood and timing | **Recover declined volume**: retry when success probability is high; avoid retries when low. | Not yet called from Decisioning API (retry policy is rule-based). |
| **decline_analyst** | LangGraph agent: decline patterns, root causes, recovery potential | **Insights**: why declines happen, by segment/reason; prioritizes remediation. | Served as endpoint; app can call for chat or batch insights. |

**Gap:** **smart_retry_policy** is not yet wired into the Decisioning retry API. Wiring it would let retry decisions be ML-driven (e.g. “retry in 2h” when model says success probability is high).

### 1.2 UC functions (agent tools → also usable by app/API)

| UC function | Returns | Approval-rate insight / action |
|-------------|---------|--------------------------------|
| **get_kpi_summary** | total_transactions, approval_rate_pct, total_value, avg_fraud_score | **Executive snapshot**: current approval rate and volume; baseline for optimization. |
| **get_decline_trends** | decline_reason, decline_count, pct_of_declines, avg_fraud_score, total_declined_value | **Where to fix first**: top decline reasons and value at stake. |
| **get_decline_by_segment** | merchant_segment, decline_reason, decline_count, declined_value, avg_fraud_score | **Segment-level declines**: which segments and reasons to target. |
| **get_route_performance** | payment_solution, card_network, volume, approval_rate, avg_latency | **Routing insight**: which routes have best approval rate; tune cascades. |
| **get_cascade_recommendations** | payment_solution, approval_rate, latency, volume (by merchant_segment) | **Cascade tuning**: recommended primary/backup order per segment. |
| **get_retry_success_rates** | decline_reason, retry_count, attempts, success_rate, avg_amount | **Retry strategy**: which decline reasons are worth retrying and at what attempt. |
| **get_recovery_opportunities** | decline_reason, decline_count, total_value, avg_fraud_score, recovery_likelihood | **Recovery pipeline**: high-value, recoverable declines to retry or remediate. |
| **get_high_risk_transactions** | transaction_id, merchant_segment, amount, fraud_score, … | **Risk ops**: review high-risk transactions; adjust rules or auth. |
| **get_risk_distribution** | risk_tier, transaction_count, approval_rate, avg_fraud_score, total_value | **Risk vs approval**: how approval rate varies by risk tier. |
| **get_optimization_opportunities** | optimization_area, payment_solution, approval_rate_pct, transaction_count, priority | **Action list**: routing/geography opportunities ranked by priority. |
| **get_trend_analysis** | event_date, transaction_count, approval_rate_pct, total_value | **Trends**: approval rate over time; measure impact of changes. |

All of these can be called **directly from the app** (e.g. backend API that runs `SELECT * FROM catalog.schema.get_*(...)`) to power dashboards, “insights” panels, or batch reports—**without** going through an agent.

---

## 2. Orchestration: Supervisor AgentBricks vs Mosaic Agent vs current setup

### 2.1 Current setup

- **Orchestrator:** Custom Python (Job 6) — `agent_framework.py`. Routes the user query to specialists (Decline, Routing, Retry, Risk, Performance), each using **Statement Execution** to run SQL (equivalent to calling UC functions). Synthesis is returned to the app.
- **App:** `POST /api/agents/orchestrator/chat` triggers Job 6 with the user message and returns synthesis.
- **Pros:** Works today; specialists use the same data as UC functions.  
- **Cons:** Job-based latency; no MLflow tracing; agents not registered in UC or Model Serving; no single “supervisor” endpoint to call from the app.

### 2.2 Supervisor AgentBricks (recommended for production)

- **What it is:** One **supervisor** agent (LangGraph) that:
  - **Routes** the user message to the right specialist(s) (decline_analyst, smart_routing, etc.).
  - **Runs** only those specialists (each can be a LangGraph agent with UC functions as tools, or a Model Serving endpoint).
  - **Synthesizes** answers into one response.
- **Where it runs:** Supervisor + specialists can be **registered in UC** and **served as Model Serving endpoints**. The app then calls **one** supervisor endpoint (e.g. `POST /serving-endpoints/supervisor/invocations`) instead of running a job.
- **Benefits for approval optimization:**
  - **Single entry point** for “How can I improve approval rate?” → supervisor calls decline_analyst + performance_recommender + (optionally) ML models and returns a consolidated answer.
  - **Lower latency** than job-based orchestrator; **scalable** and **MLflow-traced**.
  - Reuse the **same UC functions** as tools; optionally feed in **model scores** (approval propensity, risk, routing, retry) as context for the LLM.
- **Implementation path:** You already have `langgraph_agents.py` (create_decline_analyst_agent, create_smart_routing_agent, …) and an **orchestrator** builder. Register all to UC (e.g. `catalog.schema.decline_analyst`, `catalog.schema.orchestrator`), deploy **orchestrator** (and optionally each specialist) to Model Serving, then have the app call the **orchestrator** endpoint.

### 2.3 Mosaic Agent (workspace-native)

- **What it is:** Databricks **Agents** UI (AgentBricks): you configure a **Multi-Agent Supervisor** in the workspace and add subagents (e.g. Genie, Knowledge Assistant, **custom endpoints**). End users can chat in the workspace.
- **Use case:** Good for **internal users** who work in the workspace and want one chat that can hit Genie + your custom agents. For an **external app** (your React app), you still need an **API** that calls either the supervisor endpoint or your own backend that replicates routing/synthesis.
- **Recommendation:** Use **Supervisor AgentBricks** (LangGraph supervisor deployed to Model Serving) as the **programmatic** entry point for the app; optionally **also** add that same supervisor (or its subagents) to a Mosaic Multi-Agent Supervisor in the workspace for workspace users.

### 2.4 Summary: what to use

| Goal | Recommendation |
|------|----------------|
| **Single conversational entry point for the app** | **Serve the orchestrator/supervisor** as a Model Serving endpoint; app calls it for “recommendations & approval insights” (replace or complement Job 6). |
| **Use all 5 models + 11 UC functions in one answer** | **Supervisor** that can invoke specialist agents (which use UC functions) and optionally **call ML endpoints** (approval propensity, risk, routing, retry) for context or tool-like “scores” in the answer. |
| **Workspace users** | Add the same supervisor (or specialists) to **Mosaic Multi-Agent Supervisor** so they can chat in the workspace. |
| **Structured insights in the app (no chat)** | **Direct API** that calls UC functions and (optionally) model endpoints from the backend and returns JSON for dashboards/cards. |

---

## 3. How to bring all model + UC insights into the app and optimize approval rates

### 3.1 High-level flow

1. **Real-time decisions (already in place)**  
   - **Decisioning API** uses **approval_propensity_model**, **risk_scoring_model**, **smart_routing_policy** for auth and routing.  
   - **Add:** Use **smart_retry_policy** in `/api/decision/retry` so retry decisions are ML-driven (retry yes/no, suggested delay).

2. **Conversational “one place” for insights and actions**  
   - **Single supervisor endpoint** (orchestrator/supervisor AgentBricks served as Model Serving).  
   - User asks: “Why are my approval rates down?” or “What should I do first to improve approvals?”  
   - Supervisor routes to **decline_analyst** (get_decline_trends, get_decline_by_segment), **performance_recommender** (get_kpi_summary, get_optimization_opportunities, get_trend_analysis), **smart_routing** (get_route_performance, get_cascade_recommendations), **smart_retry** (get_retry_success_rates, get_recovery_opportunities), **risk_assessor** (get_high_risk_transactions, get_risk_distribution).  
   - Optionally, supervisor (or a tool) can **call ML endpoints** to inject “current approval propensity for this segment” or “retry success probability” into the answer.  
   - App: **AI Chatbot / Agent Recommendations** calls this supervisor endpoint instead of (or in addition to) Job 6.

3. **Structured “approval optimization” surface in the app**  
   - **New page or Command Center section:** e.g. “Approval optimization” with fixed cards:
     - **Executive KPIs:** `get_kpi_summary` → approval rate, volume, fraud.
     - **Top decline reasons:** `get_decline_trends` (or v_top_decline_reasons).
     - **Best routes:** `get_route_performance` / `get_cascade_recommendations`.
     - **Recovery opportunities:** `get_recovery_opportunities`.
     - **Optimization opportunities:** `get_optimization_opportunities` (priority list).
     - **Trend:** `get_trend_analysis` (approval rate over time).
   - Backend: one or more endpoints (e.g. `GET /api/analytics/approval-optimization`) that run the UC functions (and optionally aggregate) and return JSON. No agent needed for this.

4. **Use of each model in the app**  
   - **approval_propensity_model:** Already in Decisioning; optional: show “approval probability” in transaction detail or in supervisor answer.  
   - **risk_scoring_model:** Already in Decisioning; optional: “risk score” in insights or supervisor.  
   - **smart_routing_policy:** Already in Decisioning; optional: “recommended route” in optimization card.  
   - **smart_retry_policy:** Wire into Decisioning retry API; optional: “retry recommendation” in optimization or supervisor.  
   - **decline_analyst:** Serve as endpoint; call from supervisor (or directly) for “explain declines” and “recovery potential” in chat or batch.

---

## 4. Concrete recommendations

### 4.1 Serve models and use a single supervisor

1. **Keep all 5 models served** (you already have model_serving.yml with decline_analyst, approval_propensity, risk_scoring, smart_routing, smart_retry).  
2. **Register and serve the orchestrator/supervisor** (LangGraph supervisor from `langgraph_agents.py`) as one Model Serving endpoint (e.g. `orchestrator` or `payment-optimization-supervisor`).  
3. **App integration:**  
   - **Option A:** App calls **supervisor endpoint** for the “Agent Recommendations” / AI Chatbot flow (replace or complement Job 6).  
   - **Option B:** Keep Job 6 for backward compatibility and add a **second** path that calls the supervisor endpoint when available (preferred for latency and scaling).

### 4.2 Wire smart_retry_policy into Decisioning

- In **decisioning/policies.py** (or the retry route), call **smart_retry_policy** Model Serving when making retry decisions (e.g. “should_retry”, “suggested_delay_minutes”).  
- Fallback to current rule-based retry when the model is unavailable.

### 4.3 Expose UC functions to the app (structured insights)

- Add backend routes, e.g.:
  - `GET /api/analytics/approval-optimization/summary` → runs `get_kpi_summary`, returns JSON.
  - `GET /api/analytics/approval-optimization/decline-trends` → `get_decline_trends`.
  - `GET /api/analytics/approval-optimization/optimization-opportunities` → `get_optimization_opportunities`.
  - (Similarly for recovery, routes, trends if desired.)
- Frontend: **Approval optimization** or **Command Center** section that renders these as cards/lists so users get actionable lists (e.g. “Fix these 5 routes first”) without using chat.

### 4.4 Supervisor as the “brain” for open-ended questions

- **Supervisor AgentBricks** (orchestrator) with:
  - **Tools:** All 11 UC functions (exposed to specialists).  
  - **Optional tools:** Call approval_propensity, risk_scoring, smart_routing, smart_retry endpoints to get “current score” for a segment or a sample transaction and include in the answer.  
- User asks: “How can I improve approval rates?” → Supervisor invokes decline_analyst + performance_recommender + smart_routing + smart_retry (and optionally ML endpoints), then synthesizes: top decline reasons, best routes, recovery opportunities, and prioritized actions.  
- This gives **one place** where all artifacts (models + UC functions) contribute to a single, actionable answer.

---

## 5. Summary: optimize approval rates with your artifacts

| Artifact | How to leverage for approval optimization |
|----------|-------------------------------------------|
| **approval_propensity_model** | Already in Decisioning; use to avoid false declines. Optional: surface in supervisor or “transaction insight” card. |
| **risk_scoring_model** | Already in Decisioning; risk-based auth. Optional: risk distribution in optimization view. |
| **smart_routing_policy** | Already in Decisioning; route to best solution. Optional: “recommended route” in optimization card. |
| **smart_retry_policy** | **Wire into Decisioning retry API**; use for retry yes/no and timing. Optional: “retry opportunities” in supervisor and optimization view. |
| **decline_analyst** | Serve as endpoint; **supervisor** calls it for decline insights and recovery potential. |
| **All 11 UC functions** | **Supervisor** uses them via specialist agents. **Backend** calls them for **structured approval-optimization API** (summary, decline trends, opportunities, recovery, routes, trends). |
| **Orchestrator / Supervisor** | **Serve as one Model Serving endpoint**; app calls it for conversational “recommendations and approval insights” so one answer combines all models and UC data. |

**Recommended next steps**

1. **Wire smart_retry_policy** into the Decisioning retry API.  
2. **Register and serve the LangGraph supervisor** (orchestrator) as a Model Serving endpoint; point the app’s Agent Recommendations (or a new “Optimization chat”) at it.  
3. **Add an “Approval optimization” API** that calls `get_kpi_summary`, `get_decline_trends`, `get_optimization_opportunities`, `get_recovery_opportunities`, and (optionally) `get_route_performance` / `get_trend_analysis`, and surface them in the app as structured cards.  
4. **Optionally** add the same supervisor (or specialists) to a **Mosaic Multi-Agent Supervisor** in the workspace for internal users.  
5. **Optionally** give the supervisor (or a tool) access to the **ML endpoints** so answers can include “current propensity/risk/retry score” where relevant.

This way you **serve all five models**, use a **single Supervisor AgentBricks** (orchestrator) to orchestrate and bring together **all UC functions and model-backed insights**, and **optimize approval rates** both through real-time decisions (Decisioning) and through insights and actions surfaced in the app (structured optimization view + conversational supervisor).
