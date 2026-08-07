# Intelligent Ticket Triage - Architectural Plan & Roadmap

## 1. Migration Plan: Refactoring to ADK Workflows

*(Note: Previous initial flaws and fixes—such as async tool refactoring, external config, structured output parsing, and OTel tracing—have been fully implemented. Furthermore, the migration to ADK Workflows is **COMPLETE**.)*

### Target Architecture Overview

The triage workflow decomposes processing into specialized sub-agents and a conditional Router node orchestrated via ADK 2.0 Graph `Workflow`:

```
START ➔ [Classifier Agent] ➔ [Diagnostic Agent] ➔ [Triage Router Node]
                                                          │
                               ┌──────────────────────────┴──────────────────────────┐
                               ▼ (human_escalation)                                 ▼ (auto_resolve)
                   [Human Escalation Agent]                             [Auto Resolve Agent]
```

### Current Status
The core workflow is implemented and unit tests are passing. The multi-agent routing logic is tested locally and runs reliably using the local LLM proxy.

---

## 2. Analysis of New Features (Next Steps)

Evaluating how planned advanced features align with the new **ADK Workflows** architecture:

### A. Retrieval-Augmented Generation (RAG) Tools
- **Impact:** Add RAG search tools (`search_past_tickets`) and attach them to the `DiagnosticAgent` or `EscalationAgent` step. This will provide historical context to resolve recurring tickets faster without cluttering the initial `ClassifierAgent`.

### B. Multi-Agent Orchestration (A2A - Agent to Agent)
- **Impact:** The ADK A2A routes are already attached in `fast_api_app.py`. The next step is to spin up separate agents (e.g. a dedicated `NetworkDiagnosticMicroservice`) and call them over A2A RPC, creating a true distributed agent ecosystem.
