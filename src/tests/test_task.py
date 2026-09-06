import pytest
from unittest.mock import AsyncMock, patch

from tenacity import RetryError, wait_none

from openai.types.chat.chat_completion import ChatCompletion, Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage

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
    )


@pytest.mark.asyncio
async def test_clone_ui_returns_message_content():
    """clone_ui unwraps the completion and returns the content string."""
    base64_image = read_file("src/tests/base64_image_string.txt")
    expected = "<HTML><body><h1>Hi</h1></body></HTML>\n<CSS>h1 { color: red; }</CSS>"

    create = AsyncMock(return_value=build_completion(expected))
    with patch("src.task.client.chat.completions.create", create):
        message = await clone_ui(base64_image, "openai/gpt-4.1")

    assert isinstance(message, str)
    assert message == expected


@pytest.mark.asyncio
async def test_clone_ui_sends_screenshot_as_data_url():
    """The screenshot must reach the model as a base64 png data URL."""
    base64_image = read_file("src/tests/base64_image_string.txt")

    create = AsyncMock(return_value=build_completion("<HTML></HTML><CSS></CSS>"))
    with patch("src.task.client.chat.completions.create", create):
        await clone_ui(base64_image, "openai/gpt-4.1")

    kwargs = create.await_args.kwargs
    assert kwargs["model"] == "openai/gpt-4.1"

    user_content = kwargs["messages"][1]["content"]
    assert user_content[1]["image_url"] == f"data:image/png;base64,{base64_image}"


@pytest.mark.asyncio
async def test_clone_ui_retries_then_raises_on_api_errors():
    """A persistent API failure is retried 3 times, then raises.

    clone_ui wraps the error in a RuntimeError, but tenacity keeps its default
    reraise=False, so what escapes is a RetryError holding that RuntimeError.
    """
    create = AsyncMock(side_effect=ConnectionError("boom"))
    # retry_with drops the exponential backoff so the test doesn't sleep
    no_wait_clone_ui = clone_ui.retry_with(wait=wait_none())

    with patch("src.task.client.chat.completions.create", create):
        with pytest.raises(RetryError) as excinfo:
            await no_wait_clone_ui("deadbeef", "openai/gpt-4.1")

    assert create.await_count == 3
    assert isinstance(excinfo.value.last_attempt.exception(), RuntimeError)
