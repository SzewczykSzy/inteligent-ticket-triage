import os

from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models.lite_llm import LiteLlm

from app.prompts import load_prompt
from app.schemas import TriageResponse
from app.tools import check_service_status, escalate_to_human

load_dotenv()


root_agent = Agent(
    name="root_agent",
    model=LiteLlm(
        model="openai/lmstudio",
        api_base=os.getenv("LMSTUDIO_API_BASE", "http://localhost:1234/v1"),
        api_key=os.getenv("LMSTUDIO_API_KEY"),
    ),
    instruction=load_prompt("triage_system.txt"),
    output_schema=TriageResponse,
    tools=[check_service_status, escalate_to_human],
)

app = App(
    root_agent=root_agent,
    name="app",
)
