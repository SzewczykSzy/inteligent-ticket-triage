# Intelligent Ticket Triage - Architectural Plan & Roadmap

## 1. Migration Plan: Refactoring to ADK Workflows

*(Note: Previous initial flaws and fixes—such as async tool refactoring, external config, structured output parsing, and OTel tracing—have been fully implemented.)*

To scale the application, reduce prompt complexity, and introduce deterministic multi-step processing, we will replace the single `root_agent` with an **ADK Workflow (Multi-Agent Pipeline)**.

### Target Architecture Overview

The triage workflow decomposes processing into three specialized, sequential ADK agent steps orchestrated via `SequentialAgent`:

```
Incoming Ticket ➔ [1. Classifier Agent] ➔ [2. Diagnostic Agent] ➔ [3. Escalation & Response Agent] ➔ TriageResponse
```

1. **Classifier Agent (`TriageClassifierAgent`)**: Rapid initial classification (Category & Urgency).
2. **Diagnostic Agent (`DiagnosticAgent`)**: Service verification & tool execution (`check_service_status`).
3. **Escalation & Response Agent (`EscalationAgent`)**: Evaluates severity, triggers human escalation tool (`escalate_to_human`), and produces structured `TriageResponse`.

---

### Implementation Tasks

#### Task 1: Define Workflow State Schemas (`app/schemas.py`)
- Define `TriageWorkflowState` Pydantic model to carry state between workflow nodes (raw ticket, category, urgency, service status results, escalation flag, and final output).

#### Task 2: Implement Specialized Sub-Agents (`app/agents/`)
- **`classifier_agent`**: Focused prompt for category/urgency detection without tool clutter.
- **`diagnostic_agent`**: Prompt specialized in identifying referenced services and executing `check_service_status`.
- **`escalation_agent`**: Prompt specialized in evaluating health results, executing `escalate_to_human`, and producing schema-compliant `TriageResponse`.

#### Task 3: Orchestrate ADK Workflow (`app/agent.py`)
- Replace single `Agent` in `app/agent.py` with `SequentialAgent(name="triage_workflow", sub_agents=[classifier_agent, diagnostic_agent, escalation_agent])`.
- Export `app = App(root_agent=triage_workflow, name="app")`.

#### Task 4: Update Runner & API Integration (`app/api/v1/triage.py`)
- Update `triage_ticket` endpoint to handle multi-event workflow streaming from `runner.run_async()`.
- Ensure session state propagation across workflow steps.

#### Task 5: End-to-End Verification
- Run test tickets through `/api/v1/triage` and verify sub-agent turn progression in `app/logs/traces.json` and ADK Web UI.

---

## 2. Analysis of New Features (Post-Workflow Architecture Validity)

Evaluating how planned advanced features align with the new **ADK Workflows** architecture:

### A. Multi-Agent Orchestration (A2A - Agent to Agent)
- **Validity Status:** ✅ **Fully Valid & Enhanced**
- **Impact:** ADK Workflows provide in-process multi-agent execution (`SequentialAgent`). If specialized diagnostic agents need to run as standalone microservices across teams, they can be exposed via the **A2A Protocol** (`attach_a2a_routes` in `app/app_utils/a2a.py`).

### B. Implement ADK Evaluation Loops (The Quality Flywheel)
- **Validity Status:** ✅ **Fully Valid & Critical**
- **Impact:** `agents-cli eval` becomes even more effective. You can evaluate the overall workflow output as well as individual sub-agent nodes (e.g. evaluating Classifier node precision separately from Diagnostic node tool calls).

### C. Persistent Session Management
- **Validity Status:** ✅ **Fully Valid & Essential**
- **Impact:** Multi-step workflows rely directly on stateful `DatabaseSessionService` (`data/sessions.db`) to retain state as execution moves through sequential sub-agent turns.

### D. Custom ADK Callbacks & Observability
- **Validity Status:** ✅ **Fully Valid & Enhanced**
- **Impact:** Callbacks (`on_agent_turn_start`, `on_tool_call`) gain extra value in workflows by tracking handoffs between sub-agents and tool invocations per step.

### E. Add RAG (Retrieval-Augmented Generation) Tools
- **Validity Status:** ✅ **Fully Valid**
- **Impact:** RAG search tools (`search_past_tickets`) can be neatly attached specifically to the `DiagnosticAgent` or `EscalationAgent` step without cluttering the initial `ClassifierAgent`.

