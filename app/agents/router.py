from typing import Any

from google.adk.events.event import Event
from google.adk.workflow import node


@node(name="triage_router")
def triage_router(node_input: Any = None) -> Event:
    """Evaluates classification & diagnostic data and routes to human escalation or auto-resolve."""
    text_input = str(node_input).upper() if node_input else ""

    # Terms indicating high urgency or service issues requiring human intervention
    needs_escalation = any(
        term in text_input
        for term in ["CRITICAL", "HIGH", "DOWN", "OUTAGE", "DEGRADED", "EXHAUSTED", "FAIL"]
    )

    if isinstance(node_input, dict):
        priority = str(node_input.get("priority", "")).upper()
        status = str(node_input.get("status", "")).upper()
        if priority in ["CRITICAL", "HIGH"] or status in ["DOWN", "DEGRADED"]:
            needs_escalation = True

    route = "human_escalation" if needs_escalation else "auto_resolve"
    return Event(output=node_input, route=route)
