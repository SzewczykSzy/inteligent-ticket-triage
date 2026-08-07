from google.adk.agents import Agent

from app.agents.common import get_model
from app.prompts import load_prompt
from app.schemas import TriageResponse
from app.tools import escalate_to_human

escalation_agent = Agent(
    name="escalation_agent",
    model=get_model(),
    instruction=load_prompt("escalation.md"),
    output_schema=TriageResponse,
    tools=[escalate_to_human],
    mode="single_turn",
)
