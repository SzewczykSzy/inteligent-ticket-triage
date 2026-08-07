# Intelligent Ticket Triage - Project Analysis & Recommendations

## 1. Current State Analysis: Inconsistencies, Bottlenecks & Flaws

After reviewing the codebase in `app/`, here is an analysis of potential issues, bottlenecks, and suboptimal code patterns:

### A. Hardcoded Configuration in `app/agent.py`
- **Issue:** The `api_base` for `LiteLlm` is hardcoded to `http://192.168.0.195:1234/v1`. If your local IP changes or if you share this project, it will break.
- **Impact:** Low scalability and frustrating developer experience.

### B. Brittle JSON Parsing in `app/api/v1/triage.py`
- **Issue:** `parse_triage_response` uses Regex (`r"(\{.*\})"`) to extract JSON from the LLM's text. If the model outputs multiple JSON objects, lists, or unescaped characters, the regex will fail or capture invalid data.
- **Impact:** High risk of API returning `500 Internal Server Error` due to parsing failures, especially with local, smaller models that might not follow prompt instructions perfectly.

### C. Synchronous Tools in `app/tools.py`
- **Issue:** `check_service_status` and `escalate_to_human` are defined as synchronous functions (`def` instead of `async def`).
- **Impact:** FastAPI and ADK run in asynchronous event loops. While ADK can handle synchronous tools, making them `async` is a best practice to prevent blocking the event loop, especially if these tools were to make real network requests in the future.

### D. Hardcoded Mock Data
- **Issue:** `mock_services` in `app/tools.py` is hardcoded directly inside the function.
- **Impact:** Every time the tool is called, the dictionary is recreated. It's difficult to test dynamic scenarios (like a service changing from HEALTHY to CRITICAL).

---

## 2. Proposed Fixes

Here are immediate fixes you should apply to stabilize the current implementation:

1. **Environment Variables for API Base:**
   - Add `LMSTUDIO_API_BASE=http://192.168.0.195:1234/v1` to your `.env` file.
   - Update `app/agent.py`: `api_base=os.getenv("LMSTUDIO_API_BASE", "http://localhost:1234/v1")`.

2. **Improve Structured Output Handling:**
   - Update `app/prompts/triage_system.txt` to explicitly enforce JSON output format (e.g., `Output ONLY valid JSON. No markdown formatting.`).
   - Look into using a more resilient parsing library like `json-repair` in Python, or leverage ADK's built-in schema enforcement if LiteLLM + LM Studio supports it for your model.

3. **Refactor Tools to Async:**
   - Change the tool signatures in `app/tools.py` to `async def check_service_status(...)` and `async def escalate_to_human(...)`.

4. **Externalize Mock Data:**
   - Move `mock_services` out of the function scope, or better, read it from a local `data/services_state.json` file so you can modify it on the fly during testing without restarting the app.

---

## 3. New Features to Increase ADK Knowledge (Local Development)

Since you cannot use Google Cloud right now, local development is the perfect time to explore the advanced features of the **Google Agent Development Kit (ADK)**. Implementing the following features will significantly boost your understanding of the framework:

### A. Multi-Agent Orchestration (A2A - Agent to Agent)
**What it is:** Instead of one `root_agent` doing everything, create a hierarchy of specialized agents.
**Implementation Idea:**
- Create a `SupervisorAgent` that reads the ticket and decides which specialist to route it to.
- Create specialized agents: `DatabaseTriageAgent`, `NetworkTriageAgent`, and `SoftwareTriageAgent`.
- **ADK Skill Gained:** You will learn how to use ADK's `InMemoryTaskStore`, sub-agents, and delegation tools. This is crucial for building complex enterprise systems.

### B. Implement ADK Evaluation Loops (The Quality Flywheel)
**What it is:** Systematically measuring how well your local LM Studio model triages tickets.
**Implementation Idea:**
- Create a dataset of 20-30 fake IT tickets in `data/eval_dataset.jsonl`.
- Use the `google-agents-cli eval` suite to run your agent against the dataset.
- Define custom metrics (e.g., "Did it correctly identify the Priority?", "Did it call the `check_service_status` tool?").
- **ADK Skill Gained:** You will master the `agents-cli eval generate`, `grade`, and `analyze` commands, which is the most important skill for productionizing LLMs.

### C. Persistent Session Management
**What it is:** ADK supports stateful conversations. Currently, the API uses a fire-and-forget approach for every ticket.
**Implementation Idea:**
- Configure ADK to use a local SQLite database for the `SessionService` instead of `InMemoryRunner`.
- Allow a "conversation" mode where the agent can reply: *"I need more logs from the database before I can triage this."* and wait for the user to provide them in a subsequent API call.
- **ADK Skill Gained:** Understanding state management, session persistence, and multi-turn conversational agents in ADK.

### D. Custom ADK Callbacks & Observability
**What it is:** Tapping into the agent's internal lifecycle (when it thinks, when it calls a tool).
**Implementation Idea:**
- Create a custom ADK `Callback` class (e.g., `class TriageLoggingCallback(Callback):`) that overrides `on_tool_call` and `on_agent_turn_end`.
- Use this to log a detailed trace of the agent's thought process into your `logs/triage.log`.
- **ADK Skill Gained:** Deep understanding of ADK's event-driven architecture and how to build observability (crucial since you can't use Google Cloud Trace right now).

### E. Add RAG (Retrieval-Augmented Generation) Tools
**What it is:** Giving the agent access to "past resolved tickets".
**Implementation Idea:**
- Spin up a local ChromaDB instance (or just a local JSON file for simplicity).
- Add a new tool: `search_past_tickets(query)`.
- Teach the agent to search for similar past issues to propose better `recommended_action`s based on historical data.
- **ADK Skill Gained:** Integrating external data sources and Retrieval-Augmented Generation patterns into ADK toolsets.
