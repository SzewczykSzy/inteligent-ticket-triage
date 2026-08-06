from app.agent import root_agent
from app.tools import check_service_status, escalate_to_human


def test_check_service_status_database():
    res = check_service_status("database")
    assert "CRITICAL" in res
    assert "CPU utilization" in res


def test_check_service_status_unknown():
    res = check_service_status("unknown_service_xyz")
    assert "HEALTHY" in res
    assert "No known active incidents" in res


def test_escalate_to_human():
    res = escalate_to_human("CRITICAL")
    assert res["escalated"] is True
    assert res["urgency_level"] == "CRITICAL"
    assigned_team = res["assigned_team"]
    assert isinstance(assigned_team, str)
    assert "Tier-3" in assigned_team


def test_tools_registered_in_root_agent():
    tool_names = [tool.__name__ for tool in root_agent.tools]
    assert "check_service_status" in tool_names
    assert "escalate_to_human" in tool_names
