# Intelligent Ticket Triage (ITT)

Intelligent Ticket Triage (ITT) is a robust, 100% locally-hosted AI system designed to automate the analysis, categorization, and routing of IT support tickets. Leveraging local open-source infrastructure and the Google Agent Development Kit (ADK), ITT ensures data privacy by keeping all interactions, inferences, and logs out of the public cloud.

## Architecture

ITT uses a local-first stack:
- **Agent Engine:** Google ADK running a `root_agent` connected to an LLM via the LiteLLM proxy.
- **LLM Inference:** LM Studio running a local model (OpenAI-compatible REST API) on `192.168.0.195`.
- **API Layer:** FastAPI exposing a `/api/v1/triage` endpoint, validating inputs and outputs using Pydantic v2 schemas.
- **Storage:** Local filesystem (`data/artifacts/`) and SQLite (`data/sessions.db`) managed via ADK's `FileArtifactService` and `DatabaseSessionService`.
- **Telemetry:** OpenTelemetry exporting spans to a local `logs/traces.json` and a local Jaeger instance via OTLP (`http://localhost:4318/v1/traces`).
- **Containerization:** Docker Compose orchestrates the FastAPI application (`app`) and the Jaeger UI (`jaeger`).

## App Flow

1. **Client Request:** A client sends a POST request with a JSON payload to `/api/v1/triage`. The payload is validated against the `TicketRequest` Pydantic model.
2. **Session Initialization:** In `app/api/v1/triage.py`, the `triage_ticket` endpoint function creates or retrieves an ADK session using `DatabaseSessionService`.
3. **Agent Invocation:** The endpoint passes the ticket details as a user message to `runner.run_async()`, kicking off the `root_agent`.
4. **Reasoning & Tool Execution:** 
   - The `root_agent` uses its persona (from `app/prompts/triage_system.txt`) to process the ticket.
   - If needed, the agent invokes local tools defined in `app/tools.py` (e.g., `check_service_status(service_name: str)`, `escalate_to_human(urgency_level: str)`).
5. **Structured Output:** The agent completes its reasoning and returns a JSON payload.
6. **Validation & Retry:** The `parse_triage_response` function attempts to validate the response against the `TriageResponse` schema. If it fails, a retry loop prompts the agent to fix the formatting (up to 2 times).
7. **Resilience Fallback:** If the LM Studio endpoint is unreachable, the endpoint catches the connection error and gracefully yields an HTTP 503 (`Service Unavailable`).
8. **Telemetry & Logging:** Throughout the flow, traces are logged to Jaeger and `logs/traces.json`, while unstructured logs are written to `logs/triage.log`.

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

Check code quality with the ADK linter:
```bash
uv run agents-cli lint
```

### 3. Running with Docker Compose
The application is fully containerized. Start the stack (FastAPI app + Jaeger):
```bash
docker compose up -d
```
- The API will be available at `http://localhost:8000`.
- The Jaeger Observability UI will be available at `http://localhost:16686`.

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
