import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from app.prompts import load_prompt
from app.schemas import TriageResponse
from app.tools import escalate_to_human

load_dotenv()


def get_model() -> LiteLlm:
    return LiteLlm(
        model="openai/lmstudio",
        api_base=os.getenv("LMSTUDIO_API_BASE", "http://localhost:1234/v1"),
        api_key=os.getenv("LMSTUDIO_API_KEY"),
    )


escalation_agent = Agent(
    name="escalation_agent",
    model=get_model(),
    instruction=load_prompt("escalation.md"),
    output_schema=TriageResponse,
    tools=[escalate_to_human],
)
