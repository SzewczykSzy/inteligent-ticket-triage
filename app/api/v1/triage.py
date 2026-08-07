import json
import re
import uuid

from fastapi import APIRouter, HTTPException, Request, status
from google.genai import types

from app.schemas import TicketRequest, TriageResponse

router = APIRouter(tags=["triage"])


def parse_triage_response(text: str) -> TriageResponse:
    """Extracts and parses JSON from agent completion text into TriageResponse."""
    cleaned = text.strip()
    matches = list(re.finditer(r"```(?:json)?\s*(.*?)\s*```", cleaned, re.DOTALL))
    if matches:
        for match in reversed(matches):
            try:
                return TriageResponse.model_validate_json(match.group(1).strip())
            except Exception:
                continue

    try:
        return TriageResponse.model_validate_json(cleaned)
    except Exception as e:
        brace_matches = list(re.finditer(r"\{.*\}", cleaned, re.DOTALL))
        if brace_matches:
            for b_match in reversed(brace_matches):
                try:
                    return TriageResponse.model_validate_json(b_match.group(0).strip())
                except Exception:
                    continue

        raise ValueError(
            f"Failed to parse model response into TriageResponse: {e}"
        ) from e


def extract_triage_response(events: list, full_text: str) -> TriageResponse:
    """Extracts TriageResponse from a list of workflow events or full accumulated text.

    Checks events in reverse order (prioritizing terminal sub-agents like escalation_agent
    or auto_resolve_agent) before falling back to full text parsing.
    """
    for event in reversed(events):
        if hasattr(event, "output") and event.output is not None:
            if isinstance(event.output, TriageResponse):
                return event.output
            if isinstance(event.output, dict):
                try:
                    return TriageResponse.model_validate(event.output)
                except Exception:
                    pass
            if isinstance(event.output, str):
                try:
                    return parse_triage_response(event.output)
                except Exception:
                    pass

        if hasattr(event, "content") and event.content and hasattr(event.content, "parts") and event.content.parts:
            event_text = ""
            for part in event.content.parts:
                if hasattr(part, "text") and part.text:
                    event_text += part.text
            if event_text:
                try:
                    return parse_triage_response(event_text)
                except Exception:
                    pass

    if full_text:
        return parse_triage_response(full_text)

    raise ValueError("No valid response text found across workflow events.")


@router.post("/triage", response_model=TriageResponse)
@router.post("/api/v1/triage", response_model=TriageResponse)
async def triage_ticket(ticket_req: TicketRequest, request: Request) -> TriageResponse:
    """Triage an incoming IT support ticket using ADK agent runner workflow.

    Passes ticket text and initial state to ADK workflow runner, processes multi-event
    streaming execution, and returns parsed TriageResponse schema.
    """
    user_id = ticket_req.user_id or str(uuid.uuid4())

    input_text = f"Support Ticket: {ticket_req.ticket_text}"
    if ticket_req.service_name:
        input_text += f"\nAffected Service: {ticket_req.service_name}"

    initial_state = {
        "ticket_text": ticket_req.ticket_text,
        "user_id": user_id,
    }
    if ticket_req.service_name:
        initial_state["service_name"] = ticket_req.service_name

    try:
        runner = getattr(request.app.state, "runner", None)
        if runner is None:
            from google.adk.runners import InMemoryRunner

            from app.agent import root_agent

            runner = InMemoryRunner(agent=root_agent, app_name="app")

        session_service = runner.session_service
        try:
            session = await session_service.create_session(
                app_name="app", user_id=user_id, state=initial_state
            )
        except TypeError:
            session = await session_service.create_session(
                app_name="app", user_id=user_id
            )
            if hasattr(session, "state") and isinstance(session.state, dict):
                session.state.update(initial_state)

        user_message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=input_text)],
        )

        max_retries = 2
        for attempt in range(max_retries + 1):
            events = []
            final_response_text = ""
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session.id,
                new_message=user_message,
            ):
                events.append(event)
                if hasattr(event, "content") and event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_response_text += part.text

            if not events and not final_response_text:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Agent yielded empty response.",
                )

            try:
                return extract_triage_response(events, final_response_text)
            except ValueError as ve:
                if attempt < max_retries:
                    error_msg = f"Failed to parse JSON. Error: {ve}. Please return ONLY valid JSON matching the TriageResponse schema."
                    user_message = types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=error_msg)],
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"Agent triage execution failed after retries: {ve}",
                    ) from ve

    except HTTPException:
        raise
    except Exception as e:
        error_str = str(e).lower()
        type_str = type(e).__name__.lower()
        if any(
            x in error_str or x in type_str
            for x in ["connect", "timeout", "refused", "unreachable", "service unavailable"]
        ):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"LM Studio connection error: {e}",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent triage execution failed: {e}",
        ) from e
