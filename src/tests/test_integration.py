"""Live checks against OpenRouter. Deselected by default - run with:

    pytest -m integration

These exist to catch the one thing the mocked tests cannot: OpenRouter
rejecting or ignoring the request payload we send. They cost money.
"""
import pytest

from src.task import clone_ui
from src.utils.parse_responses import extract_clone

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]

MODEL = "openai/gpt-4.1-mini"


def read_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


async def test_clone_ui_payload_is_accepted():
    """The screenshot reaches the model and the required blocks come back."""
    base64_image = read_file("src/tests/base64_image_string.txt")

    message = await clone_ui(base64_image, MODEL)

    assert isinstance(message, str)
    page = extract_clone(message)
    assert page["body"] is not None, "model returned no <HTML> block"
    assert page["css"] is not None, "model returned no <CSS> block"
