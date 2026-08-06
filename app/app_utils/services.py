"""Process-wide ADK session/artifact services shared by every serving surface.

Registered under ``shared://`` so the ADK web routes, the A2A path, and the
reasoning_engine adapter share one instance: a session created on any surface
is visible to the others.
"""

from __future__ import annotations

import functools
import os

from google.adk.artifacts import FileArtifactService, InMemoryArtifactService
from google.adk.cli.service_registry import get_service_registry
from google.adk.cli.utils.service_factory import create_session_service_from_options
from google.adk.sessions import DatabaseSessionService

SESSION_SERVICE_URI = "shared://session"
ARTIFACT_SERVICE_URI = "shared://artifact"

_AGENT_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


@functools.cache
def get_session_service():
    """Process-wide session service shared across every serving surface."""
    if uri := os.environ.get("SESSION_SERVICE_URI"):
        return create_session_service_from_options(
            base_dir=_AGENT_DIR, session_service_uri=uri
        )
    db_path = os.path.join(_AGENT_DIR, "data", "sessions.db")
    return DatabaseSessionService(db_url=f"sqlite+aiosqlite:///{db_path}")


@functools.cache
def get_artifact_service():
    """Process-wide artifact service: local filesystem."""
    artifacts_dir = os.path.join(_AGENT_DIR, "data", "artifacts")
    return FileArtifactService(root_dir=artifacts_dir)


_registry = get_service_registry()
_registry.register_session_service(
    "shared", lambda uri, **kw: get_session_service())
_registry.register_artifact_service(
    "shared", lambda uri, **kw: get_artifact_service())
