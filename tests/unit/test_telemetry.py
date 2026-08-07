import os
from unittest.mock import patch

from app.app_utils.telemetry import setup_telemetry


def test_setup_telemetry(tmp_path):
    # Set up a temporary directory to act as AGENT_DIR/logs
    # We patch os.path.dirname to point to our tmp_path

    orig_dirname = os.path.dirname
    orig_abspath = os.path.abspath

    def mock_dirname(path):
        if "__file__" in path or "telemetry.py" in path:
            return str(tmp_path)
        if path == str(tmp_path):
            return str(tmp_path)
        return orig_dirname(path)

    def mock_abspath(path):
        if "__file__" in path or "telemetry.py" in path:
            return os.path.join(str(tmp_path), "telemetry.py")
        return orig_abspath(path)

    with (
        patch("os.path.abspath", side_effect=mock_abspath),
        patch("os.path.dirname", side_effect=mock_dirname),
    ):
        setup_telemetry()

        # Verify that logs/traces.json was created
        logs_dir = tmp_path / "logs"
        assert logs_dir.exists()

        traces_file = logs_dir / "traces.json"
        assert traces_file.exists()
