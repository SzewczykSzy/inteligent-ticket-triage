from typing import Any

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


class ClassificationResult(BaseModel):
    category: TicketCategory = Field(
        ...,
        description="Categorized domain of the ticket.",
    )
    priority: TicketPriority = Field(
        ...,
        description="Assigned priority level based on severity and impact.",
    )
    summary: str = Field(
        default="",
        description="Brief summary of the issue detected by classifier.",
    )


class ServiceHealthResult(BaseModel):
    service_name: str = Field(..., description="Name of the evaluated service.")
    status: str = Field(
        ...,
        description="Status returned by service health check (e.g. HEALTHY, DEGRADED, DOWN, UNKNOWN).",
    )
    details: str | None = Field(default=None, description="Optional diagnostic notes.")


class TriageWorkflowState(BaseModel):
    ticket_text: str = Field(
        ...,
        description="Raw text content of the support ticket.",
    )
    user_id: str | None = Field(
        default=None,
        description="Optional ID of the user submitting the ticket.",
    )
    service_name: str | None = Field(
        default=None,
        description="Optional name of the affected service, if provided upfront.",
    )
    classification: ClassificationResult | None = Field(
        default=None,
        description="Result produced by ClassifierAgent (category, priority, summary).",
    )
    diagnostic_checks: list[ServiceHealthResult] = Field(
        default_factory=list,
        description="List of service health check results collected by DiagnosticAgent.",
    )
    needs_human_escalation: bool = Field(
        default=False,
        description="Flag indicating if human escalation is required or triggered.",
    )
    escalation_reason: str | None = Field(
        default=None,
        description="Reasoning provided if human escalation was triggered.",
    )
    final_response: TriageResponse | None = Field(
        default=None,
        description="Final schema output produced by EscalationAgent.",
    )

