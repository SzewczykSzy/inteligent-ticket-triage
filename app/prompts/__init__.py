import os

PROMPTS_DIR = os.path.dirname(os.path.abspath(__file__))
COMPONENTS_DIR = os.path.join(PROMPTS_DIR, "components")


def load_prompt(prompt_name: str = "triage_system.md") -> str:
    """Load a markdown system prompt file dynamically from app/prompts/

    and resolve any {{component_name}} placeholders from app/prompts/components/.
    """
    if not os.path.splitext(prompt_name)[1]:
        prompt_name = f"{prompt_name}.md"

    file_path = os.path.join(PROMPTS_DIR, prompt_name)
    if not os.path.exists(file_path):
        base_name = os.path.splitext(prompt_name)[0]
        md_path = os.path.join(PROMPTS_DIR, f"{base_name}.md")
        if os.path.exists(md_path):
            file_path = md_path

    with open(file_path, encoding="utf-8") as f:
        content = f.read()

    if os.path.exists(COMPONENTS_DIR):
        for comp_file in os.listdir(COMPONENTS_DIR):
            if comp_file.endswith(".md") or comp_file.endswith(".txt"):
                comp_key = os.path.splitext(comp_file)[0]
                placeholder = f"{{{{{comp_key}}}}}"
                if placeholder in content:
                    comp_path = os.path.join(COMPONENTS_DIR, comp_file)
                    with open(comp_path, encoding="utf-8") as cf:
                        comp_content = cf.read().strip()
                        content = content.replace(placeholder, comp_content)

    return content.strip()
