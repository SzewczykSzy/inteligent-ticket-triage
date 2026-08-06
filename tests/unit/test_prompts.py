from app.agent import root_agent
from app.prompts import load_prompt


def test_load_prompt():
    prompt = load_prompt("triage_system.txt")
    assert "IT Support Triage Agent" in prompt
    assert "Ticket Categories" in prompt
    assert "Priority Levels" in prompt
    assert "DATABASE" in prompt
    assert "CRITICAL" in prompt


def test_root_agent_instruction_loaded():
    instruction = root_agent.instruction
    assert isinstance(instruction, str)
    assert "IT Support Triage Agent" in instruction
    assert "DATABASE" in instruction
