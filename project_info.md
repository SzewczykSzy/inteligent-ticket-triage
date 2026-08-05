# Intelligent Ticket Triage (ITT) — Project Overview & Roadmap

## Overview

**Intelligent Ticket Triage (ITT)** is a production-grade AI system designed for automated analysis, categorization, and routing of IT support tickets. 

Unlike unstructured open-ended chatbots, enterprise ML/LLM solutions require deterministic workflows: accepting structured inputs, executing business logic using explicit agent tools, validating LLM outputs against strict schemas, and logging all invocations for observability and compliance.

### Technology Stack
- **Agent Engine & Orchestration:** [Google ADK (Agent Development Kit)](https://github.com/google/adk)
- **Data Validation & Schemas:** [Pydantic v2](https://docs.pydantic.dev/)
- **API Server & Routing:** [FastAPI](https://fastapi.tiangolo.com/)
- **Local Model Serving:** LM Studio / Ollama (OpenAI-compatible REST API v1 via LiteLLM)
- **Cli Tooling & Scaffolding:** `agents-cli`
- **Observability & Tracking:** OpenTelemetry / MLflow / Google Cloud Logging

---

## Solution Architecture

```
                                    +-----------------------------------+
                                    |        Client / System            |
                                    +-----------------------------------+
                                                      |
                                          POST /api/v1/triage (JSON)
                                                      v
                                    +-----------------------------------+
                                    |         FastAPI Controller        |
                                    +-----------------------------------+
                                                      |
                                           TicketRequest (Pydantic)
                                                      v
                                    +-----------------------------------+
                                    |      Google ADK Agent Engine      |
                                    |           (root_agent)            |
                                    +-----------------------------------+
                                       /                             \
                                      /                               \
               Tool Call             v                                 v            Tool Call
     +-----------------------------------+                 +-----------------------------------+
     |    check_service_status(service)  |                 |    escalate_to_human(urgency)    |
     +-----------------------------------+                 +-----------------------------------+
                                      \                               /
                                       \                             /
                                        v                           v
                                    +-----------------------------------+
                                    |     Pydantic Structured Output    |
                                    |          (TriageResponse)         |
                                    +-----------------------------------+
                                                      |
                                                HTTP 200 OK
                                                      v
                                    +-----------------------------------+
                                    |           Client Response         |
                                    +-----------------------------------+
```

### Key Architectural Layers
1. **API Interface:** FastAPI exposes a REST endpoint `POST /api/v1/triage` accepting `TicketRequest` payloads.
2. **Orchestration Layer:** Google ADK `Agent` & `Runner` coordinate execution, state management, and tool invocations.
3. **Tools Layer:**
   - `check_service_status(service_name)`: Checks operational health for mock IT services.
   - `escalate_to_human(urgency_level)`: Flags high-severity tickets for human operator review.
4. **Structured Output & Schema Validation:** Enforces strict return types using Pydantic (`TriageResponse`), ensuring predictable fields (category, priority, recommended action, escalation flag).
5. **Resilience & Observability:** Implements retries on schema parsing failures, HTTP 503 handling on local LLM connection drops, and structured logging/tracing.

---

## ADK & Project Best Practices

To adhere to Google ADK standard conventions and production standards:

1. **Directory & App Naming:** The ADK `App(name="app", root_agent=root_agent)` name strictly matches the top-level package directory `app` to maintain consistency during local testing, CLI runner sessions, and evaluations (`agents-cli eval`).
2. **Type Annotations & Tool Docstrings:** All tool functions feature type hints and clear docstrings so ADK can automatically convert them to model-compatible schema descriptions.
3. **Prompt Externalization:** Prompts are externalized into template files (e.g., `app/prompts/triage_system.txt`) rather than hardcoded in Python logic.
4. **Model Abstraction:** ADK's `LiteLlm` model wrapper connects seamlessly to local OpenAI-compatible providers (LM Studio / Ollama) via `http://192.168.0.195:1234/v1` while preserving standard ADK interface contracts.
5. **Quality Flywheel & CLI Workflow:** Local iteration utilizes `agents-cli playground` for interactive testing, `agents-cli lint` for code quality, and `agents-cli eval` for regression testing.

---

## Pre-Epic 1: Proposed Project Structure

Before starting feature development in Epic 1, the codebase adheres to the standard ADK project layout:

```
inteligent-ticket-triage/
├── app/                            # Core Agent & Application Package
│   ├── __init__.py
│   ├── agent.py                    # ADK root_agent & App definition
│   ├── fast_api_app.py             # FastAPI entrypoint & lifecycle setup
│   ├── tools.py                    # Custom tool implementations (check_service_status, etc.)
│   ├── schemas.py                  # Pydantic models (TicketRequest, TriageResponse, etc.)
│   ├── app_utils/                  # Helper modules (services, telemetry, typing)
│   │   ├── __init__.py
│   │   ├── a2a.py
│   │   ├── services.py
│   │   └── telemetry.py
│   └── prompts/                    # Externalized prompt templates
│       └── triage_system.txt       # System prompt for ticket triage
├── tests/                          # Test Suite
│   ├── unit/                       # Fast unit tests for models & tools
│   ├── integration/                # Integration tests for FastAPI endpoints
│   └── eval/                       # ADK evaluation datasets & benchmarks
│       ├── eval_config.yaml
│       └── datasets/
├── .env                            # Environment variables (local API keys, endpoints)
├── .gitignore                      # Ignored files (.env, .venv, etc.)
├── pyproject.toml                  # Project metadata, dependencies & tool configs
├── agents-cli-manifest.yaml        # ADK CLI configuration
└── project_info.md                 # Project iteration roadmap & architecture (this file)
```

---

## Project Backlog & Epics

### Epic 1: Project Skeleton and Local Infrastructure

*Focus: Setting up project environment, FastAPI entrypoints, Pydantic schemas, and local LLM connectivity.*

| Task ID | Title | Description & Acceptance Criteria (AC) / Definition of Done |
| :--- | :--- | :--- |
| **ITT-1** | **Project Initialization via `agents-cli`** | **Description:** Initialize project layout using standard ADK patterns.<br><br>**Acceptance Criteria:**<br>1. Project directory structure generated via `agents-cli scaffold` / standard layout.<br>2. `pyproject.toml` contains required dependencies (`google-adk[extensions]`, `fastapi`, `pydantic`, `uvicorn`, `python-dotenv`).<br>3. `.env` file exists with local configuration keys and is excluded from version control via `.gitignore`. |
| **ITT-2** | **FastAPI & Pydantic Configuration** | **Description:** Define API request/response schemas and set up the FastAPI route skeleton.<br><br>**Acceptance Criteria:**<br>1. `TicketRequest` Pydantic model defined for raw incoming ticket text and metadata.<br>2. `TriageResponse` Pydantic model defined for structured output (Category, Priority, Recommended Action, Escalation Flag).<br>3. `POST /api/v1/triage` endpoint created, returning mock static `TriageResponse` JSON adhering to the schema. |
| **ITT-3** | **Local Model Endpoint Configuration** | **Description:** Configure ADK model provider to point to local LLM server (LM Studio / Ollama).<br><br>**Acceptance Criteria:**<br>1. ADK `LiteLlm` configured in `app/agent.py` to route calls to local endpoint (`http://192.168.0.195:1234/v1`).<br>2. `LMSTUDIO_API_KEY` read securely from `.env`.<br>3. Local LLM connectivity verified via direct invocation test. |

---

### Epic 2: Core Agent Logic (ADK Implementation)

*Focus: Implementing the ADK agent engine, system prompts, tool calling, and integrating agent reasoning into the FastAPI endpoint.*

| Task ID | Title | Description & Acceptance Criteria (AC) / Definition of Done |
| :--- | :--- | :--- |
| **ITT-4** | **System Prompt Engineering & Externalization** | **Description:** Draft and externalize system instruction defining agent role, classification rules, and tool guidelines.<br><br>**Acceptance Criteria:**<br>1. System prompt externalized in `app/prompts/triage_system.txt`.<br>2. System prompt clearly defines agent persona, ticket categories, priority levels, and strict output format rules.<br>3. Prompt loaded dynamically during agent initialization. |
| **ITT-5** | **Agent Tools Implementation** | **Description:** Build and register simulated business tools for service health verification and escalation.<br><br>**Acceptance Criteria:**<br>1. `check_service_status(service_name: str) -> str` tool implemented returning mock status data.<br>2. `escalate_to_human(urgency_level: str) -> dict` tool implemented for manual triage triggers.<br>3. Tools registered in `root_agent` with full type annotations and Google-style docstrings. |
| **ITT-6** | **FastAPI Endpoint Agent Integration** | **Description:** Connect FastAPI endpoint to execute ADK agent runner and parse structured response.<br><br>**Acceptance Criteria:**<br>1. `POST /api/v1/triage` passes user input to ADK agent runner.<br>2. Agent processes input, executes relevant tools when needed, and yields completion.<br>3. Response parsed directly into Pydantic `TriageResponse` model and returned to client with HTTP 200. |

---

### Epic 3: Production Readiness & Quality Flywheel

*Focus: Hardening the system with retries, graceful degradation, error handling, structured logging, and observability.*

| Task ID | Title | Description & Acceptance Criteria (AC) / Definition of Done |
| :--- | :--- | :--- |
| **ITT-7** | **Fallbacks, Retries, and Error Handling** | **Description:** Ensure application resilience against LLM formatting errors and local endpoint timeouts.<br><br>**Acceptance Criteria:**<br>1. On Pydantic `ValidationError` or LLM JSON parse failure, application automatically executes up to 2 retry attempts with repair instructions.<br>2. If local LLM server is unreachable or fails persistently, endpoint returns a clean `HTTP 503 Service Unavailable` response without server crashes. |
| **ITT-8** | **Observability & Telemetry (Logging / MLflow)** | **Description:** Implement structured logging and latency/token monitoring for auditability.<br><br>**Acceptance Criteria:**<br>1. Every triage invocation logs execution duration (latency), token usage, and status.<br>2. Request input, executed tools, and generated output are logged in structured JSON format (or traced via MLflow / OpenTelemetry).<br>3. Sensitive payload sanitization verified for log outputs. |

---

## Iteration Workflow & Development Cycle

1. **Phase 1 (Skeleton Setup - ITT-1 to ITT-3):** Validate infrastructure wiring, FastAPI endpoints, Pydantic contracts, and local LLM connectivity before prompt engineering.
2. **Phase 2 (Logic & Tools - ITT-4 to ITT-6):** Build system prompt, tool definitions, and connect ADK runner to endpoint.
3. **Phase 3 (Production Hardening - ITT-7 to ITT-8):** Implement retries, error handling, and structured telemetry.
4. **Phase 4 (Evaluation & Validation):** Run `agents-cli lint` and `uv run pytest` to maintain quality standards across iterations.
