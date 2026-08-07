import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from app.prompts import load_prompt
from app.tools import check_service_status

load_dotenv()


def get_model() -> LiteLlm:
    return LiteLlm(
        model="openai/lmstudio",
        api_base=os.getenv("LMSTUDIO_API_BASE", "http://localhost:1234/v1"),
        api_key=os.getenv("LMSTUDIO_API_KEY"),
    )


diagnostic_agent = Agent(
    name="diagnostic_agent",
    model=get_model(),
    instruction=load_prompt("diagnostic.md"),
    tools=[check_service_status],
    mode="single_turn",
)
