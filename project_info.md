# Intelligent Ticket Triage - Architectural Plan & Roadmap

## 1. Migration Plan: Refactoring to ADK Workflows

*(Note: Previous initial flaws and fixes—such as async tool refactoring, external config, structured output parsing, and OTel tracing—have been fully implemented.)*

To scale the application, reduce prompt complexity, and introduce deterministic multi-step processing, we will replace the single `root_agent` with an **ADK Workflow (Multi-Agent Pipeline)**.

### Target Architecture Overview

The triage workflow decomposes processing into specialized sub-agents and a conditional Router node orchestrated via ADK 2.0 Graph `Workflow`:

```
START ➔ [Classifier Agent] ➔ [Diagnostic Agent] ➔ [Triage Router Node]
                                                          │
                               ┌──────────────────────────┴──────────────────────────┐
                               ▼ (human_escalation)                                 ▼ (auto_resolve)
                   [Human Escalation Agent]                             [Auto Resolve Agent]
```

1. **Classifier Agent (`classifier_agent`)**: Rapid initial classification (Category & Urgency, `mode="single_turn"`).
2. **Diagnostic Agent (`diagnostic_agent`)**: Service verification & tool execution (`check_service_status`, `mode="single_turn"`).
3. **Triage Router Node (`triage_router`)**: Evaluates severity and health check results to deterministically route to `"human_escalation"` or `"auto_resolve"`.
4. **Human Escalation Agent (`escalation_agent`)**: Handles CRITICAL/HIGH incidents, triggers `escalate_to_human`, and formats `TriageResponse` (`needs_human_escalation=True`).
5. **Auto Resolve Agent (`auto_resolve_agent`)**: Handles non-critical tickets, formats self-service resolution guidance, and returns `TriageResponse` (`needs_human_escalation=False`).

---

### Implementation Tasks

#### Task 1: Define Workflow State Schemas (`app/schemas.py`)
- Define `TriageWorkflowState` Pydantic model to carry state between workflow nodes (raw ticket, category, urgency, service status results, escalation flag, and final output).

#### Task 2: Implement Specialized Sub-Agents & Router (`app/agents/`)
- **`classifier_agent`**: Focused prompt for category/urgency detection (`mode="single_turn"`).
- **`diagnostic_agent`**: Prompt specialized in identifying referenced services and executing `check_service_status` (`mode="single_turn"`).
- **`triage_router`**: Conditional `@node` evaluating health & priority for graph routing.
- **`escalation_agent`**: Handles human escalation branch (`escalate_to_human`, `mode="single_turn"`).
- **`auto_resolve_agent`**: Handles non-critical self-service resolution branch (`mode="single_turn"`).

#### Task 3: Orchestrate ADK Workflow with Conditional Edges (`app/agent.py`)
- Construct `Workflow(name="triage_workflow", edges=[("START", classifier_agent), (classifier_agent, diagnostic_agent), (diagnostic_agent, triage_router), (triage_router, {"human_escalation": escalation_agent, "auto_resolve": auto_resolve_agent})])`.
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

