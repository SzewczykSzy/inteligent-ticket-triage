# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import urllib.request

import pytest
from dotenv import load_dotenv
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.agent import root_agent


def is_llm_server_online() -> bool:
    load_dotenv()
    api_base = os.getenv("LMSTUDIO_API_BASE", "http://localhost:1234/v1")
    api_key = os.getenv("LMSTUDIO_API_KEY")
    models_url = f"{api_base.rstrip('/')}/models"
    headers = {"User-Agent": "pytest"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        req = urllib.request.Request(models_url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as response:
            return response.status == 200
    except Exception:
        return False


@pytest.mark.skipif(
    not is_llm_server_online(),
    reason="LM Studio local LLM server is offline or unreachable",
)
def test_agent_stream() -> None:
    """
    Integration test for the agent stream functionality.
    Tests that the agent returns valid streaming responses.
    """

    session_service = InMemorySessionService()

    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user", parts=[types.Part.from_text(text="Why is the sky blue?")]
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )
    assert len(events) > 0, "Expected at least one message"

    has_text_content = False
    for event in events:
        if (
            event.content
            and event.content.parts
            and any(part.text for part in event.content.parts)
        ):
            has_text_content = True
            break
    assert has_text_content, "Expected at least one message with text content"
