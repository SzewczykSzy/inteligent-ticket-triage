import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from app.prompts import load_prompt
from app.schemas import TriageResponse

load_dotenv()


def get_model() -> LiteLlm:
    return LiteLlm(
        model="openai/lmstudio",
        api_base=os.getenv("LMSTUDIO_API_BASE", "http://localhost:1234/v1"),
        api_key=os.getenv("LMSTUDIO_API_KEY"),
    )


auto_resolve_agent = Agent(
    name="auto_resolve_agent",
    model=get_model(),
    instruction=load_prompt("auto_resolve.md"),
    output_schema=TriageResponse,
    mode="single_turn",
)
