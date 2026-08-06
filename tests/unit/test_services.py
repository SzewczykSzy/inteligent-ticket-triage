import os
from unittest.mock import patch

from google.adk.artifacts import FileArtifactService
from google.adk.sessions import DatabaseSessionService

from app.app_utils.services import get_artifact_service, get_session_service


def test_get_session_service_default():
    # Clear cache to ensure we test the function properly
    get_session_service.cache_clear()

    with patch.dict(os.environ, {}, clear=True):
        service = get_session_service()
        assert isinstance(service, DatabaseSessionService)
        # Verify db_url ends with data/sessions.db
        assert "data/sessions.db" in str(service.db_engine.url)


def test_get_session_service_with_uri():
    get_session_service.cache_clear()

    with patch.dict(os.environ, {"SESSION_SERVICE_URI": "memory://"}):
        service = get_session_service()
        # memory:// translates to InMemorySessionService
        # Just check it doesn't fail and uses the URI branch
        assert service is not None


def test_get_artifact_service_default():
    get_artifact_service.cache_clear()

    with patch.dict(os.environ, {}, clear=True):
        service = get_artifact_service()
        assert isinstance(service, FileArtifactService)
        # Verify root_dir ends with data/artifacts
        assert str(service.root_dir).endswith("data/artifacts")
