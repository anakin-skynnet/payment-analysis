# Mosaic AI Agent Framework – Review of `agent.py`

Review of `src/payment_analysis/agents/agent.py` against [Mosaic AI Agent Framework](https://docs.databricks.com/en/generative-ai/agent-framework/author-agent.html) and [MLflow ResponsesAgent](https://mlflow.org/docs/latest/genai/serving/responses-agent.html) best practices.

---

## ✅ Applied Best Practices

### 1. **ResponsesAgent interface**
- Subclasses `mlflow.pyfunc.ResponsesAgent` and implements the required contract.
- **`predict(request)`** – Collects stream events and returns `ResponsesAgentResponse` with `output` and `custom_outputs`.
- **`predict_stream(request)`** – Generator yielding `ResponsesAgentStreamEvent` for streaming.
- Uses `ResponsesAgentRequest`, `ResponsesAgentResponse`, `ResponsesAgentStreamEvent`, and MLflow helpers (`create_text_output_item`, `create_function_call_output_item`).

### 2. **Tool calling**
- **`get_tool_specs()`** – Returns tool specs in OpenAI format (cached at init).
- **`execute_tool(tool_name, args)`** – Executes UC tools and returns result or error string.
- Tool calls and results are emitted as `response.output_item.done` events with the correct item types (function_call, function_call_output, text).
- Uses `output_to_responses_items_stream()` to turn LLM stream chunks into Responses API stream events.

### 3. **MLflow tracing**
- **`@mlflow.trace(span_type=SpanType.TOOL)`** on `execute_tool`.
- **`@mlflow.trace(span_type=SpanType.LLM)`** on `call_llm` and `_fallback_non_streaming`.
- **Session tagging** – `_tag_session()` sets `mlflow.trace.session` from `request.custom_inputs["session_id"]` or `request.context.conversation_id`.
- **`mlflow.openai.autolog()`** – Wrapped in try/except so it does not break when the trace provider is uninitialized (e.g. Job 6).
- **`mlflow.models.set_model(AGENT)`** – Enables models-from-code logging and serving.

### 4. **Custom inputs and outputs**
- **Custom inputs** – `_get_session_id()` reads `session_id` from `request.custom_inputs` or `request.context.conversation_id`.
- **Custom outputs** – `predict()` returns `custom_outputs=request.custom_inputs` so client context is preserved.

### 5. **Streaming**
- **`predict_stream`** is the primary path; `predict` is implemented on top of it.
- Uses `output_to_responses_items_stream()` to convert LLM stream chunks into Responses API events.
- Fallback to non-streaming on `json.JSONDecodeError` (chunk assembly race) so the agent still completes.

### 6. **Resilience**
- **Backoff** – `@backoff.on_exception(backoff.expo, (RateLimitError, APIConnectionError, APITimeoutError), max_tries=3)` on `call_llm`.
- **Tool errors** – Caught and returned as error strings so the LLM can react.
- **Invalid tool args** – JSON decode errors yield an error result instead of crashing.

### 7. **Unity Catalog tools**
- Uses **`databricks_openai.UCFunctionToolkit`** and **`get_uc_function_client()`** for UC function tools.
- Stays within the 10 UC-function limit (5 consolidated + 5 shared + `system.ai.python_exec`).
- Catalog/schema from env (`CATALOG`, `SCHEMA`) for portability.

### 8. **System prompt and tool use**
- Clear system prompt with tool modes and safety guidance (parameterized SQL, no f-strings for user content).
- Recommendation write-back via `python_exec` with documented pattern.

---

## ⚠️ Optional Improvements

### 1. **Text delta streaming**
- **Doc:** For “real-time” streaming, emit **`response.output_text.delta`** events (e.g. via `create_text_delta()`) with a stable `item_id`, then a final **`response.output_item.done`** with the full text.
- **Current:** The agent relies on `output_to_responses_items_stream()` to turn LLM chunks into events. If that helper already emits `output_text.delta`, behavior matches the doc; if it only emits `response.output_item.done` at the end, the UI may show a single final chunk instead of token-by-token.
- **Suggestion:** Confirm in MLflow docs/source whether `output_to_responses_items_stream` emits deltas. If not, consider iterating over LLM chunks and yielding `ResponsesAgentStreamEvent(**create_text_delta(delta=chunk, item_id=...))` plus a final done event.

### 2. **Retriever spans (Vector Search)**
- **Doc:** For retrieval (e.g. vector search), use **`SpanType.RETRIEVER`** and, for custom schemas, **`mlflow.models.set_retriever_schema()`** so evaluation and Playground can use retrieval groundedness/relevance.
- **Current:** `search_similar_transactions` is invoked as a UC tool (tool span), not as a dedicated retriever span.
- **Suggestion:** Optional: wrap the similar-transactions call in `@mlflow.trace(span_type=SpanType.RETRIEVER)` and, if the return shape is custom, call `set_retriever_schema()` so it fits MLflow’s `primary_key` / `text_column` / `doc_uri` expectations.

### 3. **Streaming error propagation**
- **Doc:** Errors during streaming can be surfaced under `databricks_output.error` in the last token/event.
- **Current:** Tool/LLM failures are handled with backoff and fallbacks; there is no explicit `databricks_output.error` on stream events.
- **Suggestion:** For critical failures (e.g. after fallback exhaustion), consider emitting an event that includes `databricks_output.error` if the serving contract supports it, so clients can show a clear error.

---

## Summary

| Area              | Status | Notes                                              |
|-------------------|--------|----------------------------------------------------|
| ResponsesAgent API| ✅     | predict, predict_stream, tools, helpers            |
| Tool calling      | ✅     | get_tool_specs, execute_tool, done events          |
| MLflow tracing    | ✅     | TOOL/LLM spans, session tag, set_model, autolog    |
| Custom I/O        | ✅     | custom_inputs (session_id), custom_outputs         |
| Streaming         | ✅     | predict_stream + helper; fallback on parse error    |
| Resilience        | ✅     | Backoff, tool error handling, non-stream fallback   |
| UC tools          | ✅     | UCFunctionToolkit, 10-function limit                 |
| Text deltas       | ⚠️     | Optional: confirm/add explicit delta events          |
| Retriever spans   | ⚠️     | Optional: RETRIEVER span + set_retriever_schema      |
| Error in stream   | ⚠️     | Optional: databricks_output.error on failure         |

**Conclusion:** The agent aligns well with Mosaic AI / ResponsesAgent best practices. Remaining items are optional refinements (text deltas, retriever spans, and streaming error reporting) for better UX and evaluation.
