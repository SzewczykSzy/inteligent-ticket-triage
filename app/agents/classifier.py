from google.adk.agents import Agent

from app.agents.common import get_model
from app.prompts import load_prompt
from app.schemas import ClassificationResult

classifier_agent = Agent(
    name="classifier_agent",
    model=get_model(),
    instruction=load_prompt("classifier.md"),
    output_schema=ClassificationResult,
    mode="single_turn",
)
