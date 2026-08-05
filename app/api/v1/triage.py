from fastapi import APIRouter

from app.schemas import TicketCategory, TicketPriority, TicketRequest, TriageResponse

router = APIRouter(tags=["triage"])


@router.post("/triage", response_model=TriageResponse)
@router.post("/api/v1/triage", response_model=TriageResponse)
def triage_ticket(request: TicketRequest) -> TriageResponse:
    """Triage an incoming IT support ticket.

    Currently returns a mock static response adhering to the TriageResponse schema.
    """
    # TODO: Implement actual triage logic
    return TriageResponse(
        category=TicketCategory.DATABASE,
        priority=TicketPriority.HIGH,
        recommended_action="Check database service logs and restart connection pool.",
        needs_human_escalation=True,
    )
