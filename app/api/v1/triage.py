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
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        match_obj = re.search(r"(\{.*\})", cleaned, re.DOTALL)
        if match_obj:
            json_str = match_obj.group(1)
        else:
            json_str = cleaned

    try:
        data = json.loads(json_str)
        return TriageResponse.model_validate(data)
    except Exception as e:
        raise ValueError(
            f"Failed to parse model response into TriageResponse: {e}"
        ) from e


@router.post("/triage", response_model=TriageResponse)
@router.post("/api/v1/triage", response_model=TriageResponse)
async def triage_ticket(ticket_req: TicketRequest, request: Request) -> TriageResponse:
    """Triage an incoming IT support ticket using ADK agent runner.

    Passes ticket text to ADK agent runner, executes tools when appropriate,
    and returns parsed TriageResponse schema.
    """
    user_id = ticket_req.user_id or str(uuid.uuid4())

    input_text = f"Support Ticket: {ticket_req.ticket_text}"
    if ticket_req.service_name:
        input_text += f"\nAffected Service: {ticket_req.service_name}"

    try:
        runner = getattr(request.app.state, "runner", None)
        if runner is None:
            from google.adk.runners import InMemoryRunner

            from app.agent import root_agent

            runner = InMemoryRunner(agent=root_agent, app_name="app")

        session_service = runner.session_service
        session = await session_service.create_session(app_name="app", user_id=user_id)

        user_message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=input_text)],
        )

        max_retries = 2
        for attempt in range(max_retries + 1):
            final_response_text = ""
            async for event in runner.run_async(
                user_id=user_id,
                session_id=session.id,
                new_message=user_message,
            ):
                if hasattr(event, "content") and event.content and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, "text") and part.text:
                            final_response_text += part.text

            if not final_response_text:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Agent yielded empty response.",
                )

            try:
                return parse_triage_response(final_response_text)
            except ValueError as ve:
                if attempt < max_retries:
                    error_msg = f"Failed to parse JSON. Error: {ve}. Please return ONLY valid JSON matching the TriageResponse schema."
                    user_message = types.Content(
                        role="user",
                        parts=[types.Part.from_text(text=error_msg)]
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
        if any(x in error_str or x in type_str for x in ["connect", "timeout", "refused", "unreachable", "service unavailable"]):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"LM Studio connection error: {e}",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent triage execution failed: {e}",
        ) from e
