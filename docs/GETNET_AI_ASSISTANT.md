# Two Chatbots – Backend Verification

The app exposes **two distinct floating chat dialogs**, each connected to a different backend:

| Chat | Endpoint | Purpose |
|------|----------|---------|
| **AI Chatbot** | `POST /api/agents/orchestrator/chat` | Orchestrator agent (Job 6): recommendations, semantic search, payment analysis from specialist agents. |
| **Genie Assistant** | `POST /api/agents/chat` | Databricks Genie Conversation API: natural language over your data (when `GENIE_SPACE_ID` is set). |

- **Header:** Two buttons – “AI Chatbot” (opens Orchestrator chat, right) and “Genie Assistant” (opens Genie chat, left).
- **Command Center** “Chat with Orchestrator” opens the **AI Chatbot** panel.

Legacy **Getnet AI Assistant** (single chat with fallback) is still exported but the layout uses the two separate chatbots above.

## Backend flow

1. **Primary: Orchestrator (Job 6)**  
   - Frontend calls `POST /api/agents/orchestrator/chat`.  
   - Backend runs **Job 6 (Deploy Agents)** via `WorkspaceClient.jobs.run_now()`, waits for the run, and returns the notebook output (synthesis from the LangGraph Orchestrator and specialists).  
   - **Not Genie** – this path uses the custom LangGraph agent framework (AgentBricks).

2. **Fallback: Genie or static reply**  
   - If the Orchestrator call fails (e.g. job not deployed or 4xx), the frontend calls `POST /api/agents/chat`.  
   - Backend then:
     - **If `GENIE_SPACE_ID` is set and the app has Databricks auth:**  
       Uses the **Databricks Genie Conversation API** (`WorkspaceClient.genie.start_conversation_and_wait`) to answer the user message in the context of the configured Genie space (payment/approval data). The reply is the Genie response text; the UI still shows an “Open in Genie” link when applicable.
     - **Otherwise:**  
       Returns a static reply and a `genie_url` so the user can open Genie in the workspace.

## Verifying Genie backend (fallback)

1. **Ensure a Genie space exists**  
   Create or use an existing Genie space that includes your payment/approval tables (e.g. from Job 7 – Genie Space Sync). Note the **space ID** (e.g. from the Genie space URL or `GET /api/2.0/genie/spaces`).

2. **Configure the app**  
   Set in the app environment (Compute → Apps → payment-analysis → Edit → Environment):
   - `GENIE_SPACE_ID=<your-genie-space-id>`

3. **Use the assistant without Orchestrator**  
   - Either do not deploy Job 6, or temporarily break Orchestrator (e.g. wrong job ID) so the frontend falls back to `POST /api/agents/chat`.  
   - Open the app from **Compute → Apps** (so `X-Forwarded-Access-Token` is set).  
   - Send a message in the Getnet AI Assistant.  
   - You should get a reply from Genie (natural language over your data), not the static “open Genie in your workspace” message.

4. **Check backend logs**  
   If you log when the Genie API is used (e.g. in `agents.py` in the `if space_id and ws is not None` branch), confirm that branch runs when you send a message with Orchestrator disabled.

## Summary

| Path              | Backend used                          | Genie? |
|-------------------|----------------------------------------|--------|
| Orchestrator OK   | Job 6 (LangGraph Orchestrator)         | No     |
| Fallback + config | Genie Conversation API (Databricks)    | Yes    |
| Fallback, no config | Static reply + link to Genie in UI | No (link only) |

So: the assistant **is** connected to the **Databricks Genie backend API** when the fallback is used and `GENIE_SPACE_ID` is set and the app has Databricks auth.
