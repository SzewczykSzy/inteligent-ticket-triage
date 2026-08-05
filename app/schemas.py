from enum import StrEnum

from pydantic import BaseModel, Field


class TicketPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TicketCategory(StrEnum):
    DATABASE = "DATABASE"
    NETWORK = "NETWORK"
    AUTHENTICATION = "AUTHENTICATION"
    INFRASTRUCTURE = "INFRASTRUCTURE"
    SOFTWARE = "SOFTWARE"
    OTHER = "OTHER"


class TicketRequest(BaseModel):
    ticket_text: str = Field(
        ...,
        description="Raw text content of the support ticket.",
        examples=["Database is not working for 15 minutes, error 500 is thrown."],
    )
    user_id: str | None = Field(
        default=None,
        description="Optional ID of the user submitting the ticket.",
        examples=["user_12345"],
    )
    service_name: str | None = Field(
        default=None,
        description="Optional name of the affected service, if known.",
        examples=["database_prod"],
    )


class TriageResponse(BaseModel):
    category: TicketCategory = Field(
        ...,
        description="Categorized domain of the ticket.",
        examples=[TicketCategory.DATABASE],
    )
    priority: TicketPriority = Field(
        ...,
        description="Assigned priority level based on severity and impact.",
        examples=[TicketPriority.HIGH],
    )
    recommended_action: str = Field(
        ...,
        description="Suggested immediate steps or resolution action.",
        examples=[
            "Check database service logs and restart if connection pool exhausted."
        ],
    )
    needs_human_escalation: bool = Field(
        ...,
        description="Flag indicating if the ticket requires manual human intervention.",
        examples=[True],
    )
