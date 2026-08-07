from typing import Any

from google.adk.events.event import Event
from google.adk.workflow import node
from pydantic import BaseModel

from app.schemas import TicketPriority


@node(name="triage_router")
def triage_router(node_input: Any = None) -> Event:
    """Evaluates classification & diagnostic data and routes to human escalation or auto-resolve."""
    needs_escalation = False

    def check_priority_and_status(data: dict) -> bool:
        priority = str(data.get("priority", "")).upper()
        status = str(data.get("status", "")).upper()
        reason = str(data.get("summary", "") or data.get("details", "")).upper()
        return (
            priority in [TicketPriority.CRITICAL.value, TicketPriority.HIGH.value]
            or status in ["DOWN", "DEGRADED", "OUTAGE", "FAIL"]
            or any(
                term in reason for term in ["CRITICAL", "OUTAGE", "DOWN", "EXHAUSTED"]
            )
        )

    if isinstance(node_input, BaseModel):
        needs_escalation = check_priority_and_status(node_input.model_dump())
    elif isinstance(node_input, dict):
        needs_escalation = check_priority_and_status(node_input)
    elif hasattr(node_input, "output") and isinstance(
        node_input.output, (dict, BaseModel)
    ):
        data = (
            node_input.output.model_dump()
            if isinstance(node_input.output, BaseModel)
            else node_input.output
        )
        needs_escalation = check_priority_and_status(data)
    elif isinstance(node_input, str):
        text_upper = node_input.upper()
        needs_escalation = any(
            term in text_upper
            for term in [
                "CRITICAL",
                "HIGH",
                "DOWN",
                "OUTAGE",
                "DEGRADED",
                "EXHAUSTED",
                "FAIL",
            ]
        )
    elif hasattr(node_input, "content") and node_input.content:
        content_text = ""
        if hasattr(node_input.content, "parts") and node_input.content.parts:
            for part in node_input.content.parts:
                if hasattr(part, "text") and part.text:
                    content_text += part.text
        text_upper = content_text.upper()
        needs_escalation = any(
            term in text_upper
            for term in [
                "CRITICAL",
                "HIGH",
                "DOWN",
                "OUTAGE",
                "DEGRADED",
                "EXHAUSTED",
                "FAIL",
            ]
        )

    route = "human_escalation" if needs_escalation else "auto_resolve"
    return Event(output=node_input, branch=route)
