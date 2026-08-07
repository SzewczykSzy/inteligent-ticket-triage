import os

from dotenv import load_dotenv
from google.adk.models.lite_llm import LiteLlm

load_dotenv()


def get_model() -> LiteLlm:
    """Instantiate and return standard LiteLlm instance for sub-agents."""
    return LiteLlm(
        model="openai/lmstudio",
        api_base=os.getenv("LMSTUDIO_API_BASE", "http://localhost:1234/v1"),
        api_key=os.getenv("LMSTUDIO_API_KEY"),
    )
