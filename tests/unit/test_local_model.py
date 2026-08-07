import os
from unittest.mock import AsyncMock, patch

import pytest
from google.adk.models.lite_llm import LiteLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from litellm.utils import ModelResponse

from app.agent import root_agent


def test_agent_model_configuration():
    """Verify that root_agent uses LiteLlm with the local endpoint settings."""
    assert isinstance(root_agent.model, LiteLlm)
    assert root_agent.model.model == "openai/lmstudio"
    expected_api_base = os.getenv("LMSTUDIO_API_BASE", "http://localhost:1234/v1")
    assert (
        root_agent.model._additional_args.get("api_base")
        == expected_api_base
    )
    expected_api_key = os.getenv("LMSTUDIO_API_KEY")
    assert root_agent.model._additional_args.get("api_key") == expected_api_key


@pytest.mark.asyncio
async def test_lite_llm_generate_content_mocked():
    """Test LiteLlm model invocation using a mocked response."""
    mock_response = ModelResponse(
        id="chatcmpl-123",
        choices=[
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello! I am ready to triage your ticket.",
                },
                "finish_reason": "stop",
            }
        ],
        model="openai/lmstudio",
    )

    with patch.object(
        root_agent.model.llm_client,
        "acompletion",
        new_callable=AsyncMock,
        return_value=mock_response,
    ):
        request = LlmRequest(
            contents=[
                types.Content(role="user", parts=[types.Part.from_text(text="Hi")])
            ]
        )

        responses: list[LlmResponse] = []
        async for resp in root_agent.model.generate_content_async(request):
            responses.append(resp)

        assert len(responses) == 1
        assert (
            responses[0].content.parts[0].text
            == "Hello! I am ready to triage your ticket."
        )


