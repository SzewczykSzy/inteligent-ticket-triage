from google.adk.agents import Agent

from app.agents.common import get_model
from app.prompts import load_prompt
from app.schemas import TriageResponse

auto_resolve_agent = Agent(
    name="auto_resolve_agent",
    model=get_model(),
    instruction=load_prompt("auto_resolve.md"),
    output_schema=TriageResponse,
    mode="single_turn",
)
