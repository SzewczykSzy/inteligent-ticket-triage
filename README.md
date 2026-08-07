# Intelligent Ticket Triage (ITT)

Intelligent Ticket Triage (ITT) is a robust, 100% locally-hosted AI system designed to automate the analysis, categorization, and routing of IT support tickets. Leveraging local open-source infrastructure and the Google Agent Development Kit (ADK), ITT ensures data privacy by keeping all interactions, inferences, and logs out of the public cloud.

## Architecture

ITT uses a local-first stack:
- **Agent Engine:** Google ADK running a multi-agent `triage_workflow` Graph pipeline connected to an LLM directly (`app/agents/common.py`).
  - **Classifier Agent (`classifier_agent`)**: Analyzes raw tickets to extract initial category and priority (`app/prompts/classifier.md`).
  - **Diagnostic Agent (`diagnostic_agent`)**: Checks service health using tools (`check_service_status`) (`app/prompts/diagnostic.md`).
  - **Triage Router (`triage_router`)**: Graph node determining routing based on priority and health check findings.
  - **Escalation Agent (`escalation_agent`)**: Formulates remediation & human escalation for critical tickets (`app/prompts/escalation.md`).
  - **Auto Resolve Agent (`auto_resolve_agent`)**: Formulates self-service resolution for non-critical tickets (`app/prompts/auto_resolve.md`).
- **LLM Inference:** LM Studio running a local model (OpenAI-compatible REST API) configured via `LMSTUDIO_API_BASE` (default: `http://localhost:1234/v1`).
- **API Layer:** FastAPI exposing `/triage` and `/api/v1/triage` endpoints, validating inputs and outputs using Pydantic v2 schemas.
- **Storage:** Local filesystem (`data/artifacts/`) and SQLite (`data/sessions.db`) managed via ADK's `FileArtifactService` and `DatabaseSessionService`.
- **Telemetry:** OpenTelemetry exporting spans to `logs/traces.json`.
- **Containerization:** Docker Compose orchestrates the FastAPI application (`app`).

## App Flow

1. **Client Request:** A client sends a POST request with a JSON payload to `/api/v1/triage`. The payload is validated against the `TicketRequest` Pydantic model.
2. **Session Initialization:** In `app/api/v1/triage.py`, the `triage_ticket` endpoint function creates or retrieves an ADK session with initial ticket state using `DatabaseSessionService`.
3. **Workflow Invocation:** The endpoint passes the ticket details as a user message to `runner.run_async()`, executing the multi-agent `triage_workflow`.
4. **Multi-Agent Reasoning & Tool Execution:**
   - `classifier_agent` categorizes the issue and sets priority.
   - `diagnostic_agent` invokes diagnostic tools (`check_service_status`).
   - `triage_router` deterministically routes execution to `escalation_agent` or `auto_resolve_agent`.
5. **Structured Output & Stream Parsing:** `extract_triage_response` inspects multi-event streaming outputs to extract the final `TriageResponse` schema.
6. **Validation & Retry:** The response is validated against the `TriageResponse` schema. If it fails, a retry loop prompts the agent to fix formatting (up to 2 times).
7. **Resilience Fallback:** If the LM Studio endpoint is unreachable, the endpoint catches connection errors and yields an HTTP 503 (`Service Unavailable`).
8. **Telemetry & Logging:** Spans are logged to `logs/traces.json`, while unstructured logs are written to `logs/triage.log`.

## How to Test and Work With the App

### 1. Prerequisites
- [uv](https://github.com/astral-sh/uv) (Extremely fast Python package manager).
- Docker & Docker Compose.
- [LM Studio](https://lmstudio.ai/) running locally on `192.168.0.195:1234` with an active model server.

### 2. Local Development setup
Install the environment and sync dependencies:
```bash
uv sync
```

Run the unit and integration tests:
```bash
uv run pytest tests/unit tests/integration
```

Check code quality and linting:
```bash
uv run agents-cli lint
uv run ruff check .
```

### 3. Running with Docker Compose
The application is fully containerized. Start the stack (FastAPI app):
```bash
docker compose up -d
```
- The API will be available at `http://localhost:8000`.

### 4. Testing the API
You can test the triage endpoint using `curl`:
```bash
curl -X POST "http://localhost:8000/api/v1/triage" \
     -H "Content-Type: application/json" \
     -d '{
           "ticket_text": "The production database cluster is completely unresponsive. Applications are throwing 500 errors.",
           "service_name": "database_prod",
           "user_id": "oncall_user_1"
         }'
```
Expected response:
```json
{
  "category": "DATABASE",
  "priority": "CRITICAL",
  "recommended_action": "Verify database instance health and review latest query logs. Restart instance if necessary.",
  "needs_human_escalation": true
}
```
