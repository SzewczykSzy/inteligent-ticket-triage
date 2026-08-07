from dotenv import load_dotenv
from google.adk.apps import App
from google.adk.workflow import Workflow

from app.agents import (
    auto_resolve_agent,
    classifier_agent,
    diagnostic_agent,
    escalation_agent,
    triage_router,
)

load_dotenv()

triage_workflow = Workflow(
    name="triage_workflow",
    edges=[
        ("START", classifier_agent),
        (classifier_agent, diagnostic_agent),
        (diagnostic_agent, triage_router),
        (
            triage_router,
            {
                "human_escalation": escalation_agent,
                "auto_resolve": auto_resolve_agent,
            },
        ),
    ],
)

root_agent = triage_workflow

app = App(
    root_agent=triage_workflow,
    name="app",
)
