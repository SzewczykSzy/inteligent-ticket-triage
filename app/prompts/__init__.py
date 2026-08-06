import os

PROMPTS_DIR = os.path.dirname(os.path.abspath(__file__))


def load_prompt(prompt_name: str = "triage_system.txt") -> str:
    """Load a system prompt text file dynamically from app/prompts/."""
    file_path = os.path.join(PROMPTS_DIR, prompt_name)
    with open(file_path, encoding="utf-8") as f:
        return f.read().strip()
