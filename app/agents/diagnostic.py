from google.adk.agents import Agent

from app.agents.common import get_model
from app.prompts import load_prompt
from app.tools import check_service_status

diagnostic_agent = Agent(
    name="diagnostic_agent",
    model=get_model(),
    instruction=load_prompt("diagnostic.md"),
    tools=[check_service_status],
    mode="single_turn",
)
