from app.agents import classifier_agent, diagnostic_agent, escalation_agent
from app.prompts import load_prompt


def test_load_prompt():
    prompt = load_prompt("triage_system.md")
    assert "IT Support Triage Agent" in prompt
    assert "Ticket Categories" in prompt
    assert "Priority Levels" in prompt
    assert "DATABASE" in prompt
    assert "CRITICAL" in prompt


def test_workflow_agent_instructions_loaded():
    instructions = [
        classifier_agent.instruction,
        diagnostic_agent.instruction,
        escalation_agent.instruction,
    ]
    assert any("Classification Specialist" in inst for inst in instructions)
    assert any("Diagnostics Specialist" in inst for inst in instructions)
    assert any("Escalation Specialist" in inst for inst in instructions)
