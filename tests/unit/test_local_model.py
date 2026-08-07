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
    """Verify sub-agent uses LiteLlm with the local endpoint settings."""
    from app.agents import classifier_agent

    sub_agent_model = classifier_agent.model
    assert isinstance(sub_agent_model, LiteLlm)
    assert sub_agent_model.model == "openai/lmstudio"
    expected_api_base = os.getenv("LMSTUDIO_API_BASE", "http://localhost:1234/v1")
    assert (
        sub_agent_model._additional_args.get("api_base")
        == expected_api_base
    )
    expected_api_key = os.getenv("LMSTUDIO_API_KEY")
    assert sub_agent_model._additional_args.get("api_key") == expected_api_key


@pytest.mark.asyncio
async def test_lite_llm_generate_content_mocked():
    """Test LiteLlm model invocation using a mocked response."""
    from app.agents import classifier_agent

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

    target_model = classifier_agent.model
    with patch.object(
        target_model.llm_client,
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
        async for resp in target_model.generate_content_async(request):
            responses.append(resp)

        assert len(responses) == 1
        assert (
            responses[0].content.parts[0].text
            == "Hello! I am ready to triage your ticket."
        )


