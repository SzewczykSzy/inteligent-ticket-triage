from app.agents import classifier_agent, diagnostic_agent, escalation_agent
from app.prompts import load_prompt


def test_load_prompt():
    prompt = load_prompt("classifier.md")
    assert "Ticket Classification Specialist" in prompt
    assert "Ticket Categories" in prompt
    assert "Priority Levels" in prompt
    assert "DATABASE" in prompt
    assert "CRITICAL" in prompt


def test_workflow_agent_instructions_loaded():
    instructions = [
        str(classifier_agent.instruction),
        str(diagnostic_agent.instruction),
        str(escalation_agent.instruction),
    ]
    assert any("Classification Specialist" in inst for inst in instructions)
    assert any("Diagnostics Specialist" in inst for inst in instructions)
    assert any("Escalation Specialist" in inst for inst in instructions)
