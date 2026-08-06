from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from google.adk.events import Event
from google.adk.runners import InMemoryRunner
from google.genai import types

from app.agent import root_agent
from app.api.v1.triage import parse_triage_response
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


def test_parse_triage_response_plain_json():
    json_text = '{"category": "DATABASE", "priority": "HIGH", "recommended_action": "Check DB pool", "needs_human_escalation": true}'
    parsed = parse_triage_response(json_text)
    assert parsed.category == TicketCategory.DATABASE
    assert parsed.priority == TicketPriority.HIGH
    assert parsed.needs_human_escalation is True


def test_parse_triage_response_markdown_fenced():
    markdown_text = 'Here is the result:\n```json\n{"category": "NETWORK", "priority": "MEDIUM", "recommended_action": "Reset gateway", "needs_human_escalation": false}\n```'
    parsed = parse_triage_response(markdown_text)
    assert parsed.category == TicketCategory.NETWORK
    assert parsed.priority == TicketPriority.MEDIUM
    assert parsed.needs_human_escalation is False


def test_triage_endpoint_v1_mocked_runner():
    mock_json = '{"category": "DATABASE", "priority": "HIGH", "recommended_action": "Check database connection pool", "needs_human_escalation": true}'

    app_instance.state.runner = InMemoryRunner(
        agent=root_agent, app_name="app")

    async def mock_run_async(*args, **kwargs):
        yield Event(
            author="root_agent",
            content=types.Content(
                role="model",
                parts=[types.Part.from_text(text=mock_json)],
            ),
        )

    with patch.object(
        app_instance.state.runner, "run_async", side_effect=mock_run_async
    ):
        payload = {
            "ticket_text": "Database is not working for 15 minutes, error 500 is thrown."
        }
        response = client.post("/api/v1/triage", json=payload)
        assert response.status_code == 200, f"Unexpected response: {response.json()}"
        data = response.json()
        assert data["category"] == "DATABASE"
        assert data["priority"] == "HIGH"
        assert data["needs_human_escalation"] is True
        assert "Check database" in data["recommended_action"]


def test_triage_endpoint_v1_parse_retry():
    # Missing required fields
    mock_invalid_json = '{"category": "INVALID", "priority": "HIGH"}'
    mock_valid_json = '{"category": "DATABASE", "priority": "HIGH", "recommended_action": "Check database connection pool", "needs_human_escalation": true}'

    app_instance.state.runner = InMemoryRunner(
        agent=root_agent, app_name="app")

    call_count = {"count": 0}

    async def mock_run_async(*args, **kwargs):
        call_count["count"] += 1
        if call_count["count"] == 1:
            yield Event(
                author="root_agent",
                content=types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=mock_invalid_json)],
                ),
            )
        else:
            yield Event(
                author="root_agent",
                content=types.Content(
                    role="model",
                    parts=[types.Part.from_text(text=mock_valid_json)],
                ),
            )

    with patch.object(
        app_instance.state.runner, "run_async", side_effect=mock_run_async
    ):
        payload = {
            "ticket_text": "Database is not working for 15 minutes, error 500 is thrown."
        }
        response = client.post("/api/v1/triage", json=payload)
        assert response.status_code == 200, f"Unexpected response: {response.json()}"
        data = response.json()
        assert data["category"] == "DATABASE"
        assert call_count["count"] == 2


def test_triage_endpoint_v1_connection_error():
    app_instance.state.runner = InMemoryRunner(
        agent=root_agent, app_name="app")

    async def mock_run_async_connection_error(*args, **kwargs):
        raise ConnectionError("Failed to connect to LM Studio")
        # Need a yield so it's a generator
        yield

    with patch.object(
        app_instance.state.runner, "run_async", side_effect=mock_run_async_connection_error
    ):
        payload = {
            "ticket_text": "Database is not working."
        }
        response = client.post("/api/v1/triage", json=payload)
        assert response.status_code == 503
        assert "LM Studio connection error" in response.json()["detail"]
