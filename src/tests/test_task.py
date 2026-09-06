import json

import httpx
import pytest
from unittest.mock import AsyncMock, patch

from openai import APIConnectionError, APIStatusError, BadRequestError
from tenacity import wait_none

from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from openai.types.completion_usage import CompletionUsage

from src.task import clone_ui


def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{file_path}' not found")
    except IOError as e:
        raise IOError(f"Error reading file '{file_path}': {e}")


def build_completion(content: str) -> ChatCompletion:
    """A minimal ChatCompletion shaped like what OpenRouter returns."""
    return ChatCompletion(
        id="chatcmpl-test",
        created=0,
        model="openai/gpt-4.1",
        object="chat.completion",
        choices=[
            Choice(
                index=0,
                finish_reason="stop",
                message=ChatCompletionMessage(role="assistant", content=content),
            )
        ],
        usage=CompletionUsage(prompt_tokens=100, completion_tokens=200, total_tokens=300),
    )


@pytest.mark.asyncio
async def test_clone_ui_returns_message_content():
    """clone_ui unwraps the completion into content plus usage."""
    base64_image = read_file("src/tests/base64_image_string.txt")
    expected = "<HTML><body><h1>Hi</h1></body></HTML>\n<CSS>h1 { color: red; }</CSS>"

    create = AsyncMock(return_value=build_completion(expected))
    with patch("src.task.client.chat.completions.create", create):
        message = await clone_ui(base64_image, "openai/gpt-4.1")

    assert isinstance(message.content, str)
    assert message.content == expected


@pytest.mark.asyncio
async def test_clone_ui_sends_screenshot_as_data_url():
    """The screenshot must reach the model as a base64 png data URL."""
    base64_image = read_file("src/tests/base64_image_string.txt")

    create = AsyncMock(return_value=build_completion("<HTML></HTML><CSS></CSS>"))
    with patch("src.task.client.chat.completions.create", create):
        await clone_ui(base64_image, "openai/gpt-4.1")

    kwargs = create.await_args.kwargs
    assert kwargs["model"] == "openai/gpt-4.1"
    # OpenRouter only reports credits spent when asked to
    assert kwargs["extra_body"] == {"usage": {"include": True}}

    user_content = kwargs["messages"][1]["content"]
    assert user_content[1]["image_url"] == {
        "url": f"data:image/png;base64,{base64_image}"
    }


@pytest.mark.asyncio
async def test_clone_ui_retries_transient_errors_then_raises():
    """A transient failure is retried 3 times, then the real error escapes."""
    create = AsyncMock(side_effect=APIConnectionError(request=httpx.Request("POST", "/")))
    # retry_with drops the exponential backoff so the test doesn't sleep
    no_wait_clone_ui = clone_ui.retry_with(wait=wait_none())

    with patch("src.task.client.chat.completions.create", create):
        with pytest.raises(APIConnectionError):
            await no_wait_clone_ui("deadbeef", "openai/gpt-4.1")

    assert create.await_count == 3


@pytest.mark.asyncio
async def test_clone_ui_does_not_retry_client_errors():
    """A bad request is the caller's fault - fail on the first attempt."""
    create = AsyncMock(
        side_effect=BadRequestError(
            "no such model",
            response=httpx.Response(400, request=httpx.Request("POST", "/")),
            body=None,
        )
    )

    with patch("src.task.client.chat.completions.create", create):
        with pytest.raises(BadRequestError):
            await clone_ui("deadbeef", "not-a-real/model")

    assert create.await_count == 1


@pytest.mark.asyncio
async def test_clone_ui_retries_non_json_gateway_responses():
    """OpenRouter occasionally returns a non-JSON body. That is transient."""
    create = AsyncMock(side_effect=json.JSONDecodeError("Expecting value", "", 0))
    no_wait_clone_ui = clone_ui.retry_with(wait=wait_none())

    with patch("src.task.client.chat.completions.create", create):
        with pytest.raises(json.JSONDecodeError):
            await no_wait_clone_ui("deadbeef", "openai/gpt-4.1")

    assert create.await_count == 3


@pytest.mark.asyncio
async def test_clone_ui_retries_server_errors_but_not_client_errors():
    """5xx is the gateway's problem and retried; 4xx is ours and is not."""
    def status_error(code):
        return APIStatusError(
            "boom",
            response=httpx.Response(code, request=httpx.Request("POST", "/")),
            body=None,
        )

    no_wait_clone_ui = clone_ui.retry_with(wait=wait_none())

    for code, expected_calls in [(500, 3), (429, 3), (404, 1), (400, 1)]:
        create = AsyncMock(side_effect=status_error(code))
        with patch("src.task.client.chat.completions.create", create):
            with pytest.raises(APIStatusError):
                await no_wait_clone_ui("deadbeef", "openai/gpt-4.1")
        assert create.await_count == expected_calls, f"HTTP {code}"


@pytest.mark.asyncio
async def test_clone_ui_reports_token_usage():
    """Usage rides along with the content so a run can price itself."""
    create = AsyncMock(return_value=build_completion("<HTML></HTML><CSS></CSS>"))
    with patch("src.task.client.chat.completions.create", create):
        message = await clone_ui("deadbeef", "openai/gpt-4.1")

    assert message.usage["prompt_tokens"] == 100
    assert message.usage["completion_tokens"] == 200
