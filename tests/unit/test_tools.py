import pytest

from app.tools import check_service_status, escalate_to_human, load_services_state


@pytest.mark.asyncio
async def test_check_service_status_database():
    res = await check_service_status("database")
    assert "CRITICAL" in res
    assert "CPU utilization" in res


@pytest.mark.asyncio
async def test_check_service_status_unknown():
    res = await check_service_status("unknown_service_xyz")
    assert "HEALTHY" in res
    assert "No known active incidents" in res


@pytest.mark.asyncio
async def test_escalate_to_human():
    res = await escalate_to_human("CRITICAL")
    assert res["escalated"] is True
    assert res["urgency_level"] == "CRITICAL"
    assigned_team = res["assigned_team"]
    assert isinstance(assigned_team, str)
    assert "Tier-3" in assigned_team


def test_tools_registered_in_workflow_agents():
    from app.agents import diagnostic_agent, escalation_agent

    diag_tools = [tool.__name__ for tool in diagnostic_agent.tools]
    esc_tools = [tool.__name__ for tool in escalation_agent.tools]

    assert "check_service_status" in diag_tools
    assert "escalate_to_human" in esc_tools


def test_load_services_state():
    services = load_services_state()
    assert "database" in services
    assert "auth" in services
