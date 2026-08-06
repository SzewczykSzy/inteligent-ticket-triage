import contextlib
import json
import logging
import os
from collections.abc import AsyncIterator
from logging.handlers import RotatingFileHandler

from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv
from fastapi import FastAPI
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner

from app.api.v1.triage import router as triage_router
from app.app_utils import services
from app.app_utils.a2a import attach_a2a_routes
from app.app_utils.telemetry import setup_telemetry
from app.app_utils.typing import Feedback

load_dotenv()
setup_telemetry()
AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set up standard logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(os.path.join(AGENT_DIR, "logs",
                            "triage.log"), maxBytes=10485760, backupCount=5),
    ]
)
logger = logging.getLogger(__name__)


def log_feedback(feedback_data: dict):
    feedback_file = os.path.join(AGENT_DIR, "logs", "feedback.jsonl")
    with open(feedback_file, "a") as f:
        f.write(json.dumps(feedback_data) + "\n")


allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(
        ",") if os.getenv("ALLOW_ORIGINS") else None
)


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    from app.agent import app as adk_app
    from app.agent import root_agent

    runner = Runner(
        app=adk_app,
        session_service=services.get_session_service(),
        artifact_service=services.get_artifact_service(),
        auto_create_session=True,
    )
    app.state.runner = runner
    app.state.agent_app_name = adk_app.name
    await attach_a2a_routes(
        app,
        agent=root_agent,
        runner=runner,
        task_store=InMemoryTaskStore(),
        rpc_path=f"/a2a/{adk_app.name}",
    )
    yield


app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=services.ARTIFACT_SERVICE_URI,
    allow_origins=allow_origins,
    session_service_uri=services.SESSION_SERVICE_URI,
    otel_to_cloud=False,
    lifespan=lifespan,
)
app.title = "inteligent-ticket-triage"
app.description = "API for interacting with the Agent inteligent-ticket-triage"
app.include_router(triage_router)


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    log_feedback(feedback.model_dump())
    logger.info("Feedback received and logged.")
    return {"status": "success"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
