from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.triage import router as triage_router
from app.schemas import TicketCategory, TicketPriority, TicketRequest, TriageResponse

app_instance = FastAPI()
app_instance.include_router(triage_router)
client = TestClient(app_instance)


def test_ticket_request_schema():
    req = TicketRequest(
        ticket_text="Database is not responding",
        user_id="user_1",
        service_name="database_prod",
    )
    assert req.ticket_text == "Database is not responding"
    assert req.user_id == "user_1"
    assert req.service_name == "database_prod"


def test_triage_response_schema():
    res = TriageResponse(
        category=TicketCategory.DATABASE,
        priority=TicketPriority.CRITICAL,
        recommended_action="Restart DB cluster",
        needs_human_escalation=True,
    )
    assert res.category == TicketCategory.DATABASE
    assert res.priority == TicketPriority.CRITICAL
    assert res.needs_human_escalation is True


def test_triage_endpoint_v1():
    payload = {
        "ticket_text": "Database is not working for 15 minutes, error 500 is thrown."
    }
    response = client.post("/api/v1/triage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "category" in data
    assert "priority" in data
    assert "recommended_action" in data
    assert "needs_human_escalation" in data
    assert data["category"] == "DATABASE"
    assert data["priority"] == "HIGH"


# TODO: Remove this test after triaging is implemented
def test_triage_endpoint_legacy_path():
    payload = {"ticket_text": "Network is down"}
    response = client.post("/triage", json=payload)
    assert response.status_code == 200
    assert response.json()["category"] == "DATABASE"
