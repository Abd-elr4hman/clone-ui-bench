import json
from typing import NamedTuple

from openai import APIError, APIStatusError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from src.openrouter.client import client
from src.prompts import system, user
from openai.types.chat.chat_completion import ChatCompletion


def is_transient(exc: BaseException) -> bool:
    """Whether a failure is worth retrying.

    Network blips, 429s, 5xx and non-JSON bodies from the gateway are transient.
    A 4xx is our own request being wrong - retrying just burns the backoff.
    """
    if isinstance(exc, json.JSONDecodeError):
        return True
    if isinstance(exc, APIStatusError):
        return exc.status_code == 429 or exc.status_code >= 500
    return isinstance(exc, APIError)


class ModelResponse(NamedTuple):
    """A model's text plus what the call cost."""

    content: str
    usage: dict


def usage_of(message) -> dict:
    """Pull token counts and OpenRouter's own cost figure off a response."""
    u = getattr(message, "usage", None)
    if u is None:
        return {}
    d = u.model_dump() if hasattr(u, "model_dump") else dict(u)
    return {
        "prompt_tokens": d.get("prompt_tokens"),
        "completion_tokens": d.get("completion_tokens"),
        # present because we ask for it via extra_body usage.include
        "cost": d.get("cost"),
    }


# Ask OpenRouter to report credits spent alongside the completion.
USAGE_ACCOUNTING = {"usage": {"include": True}}


RETRY_POLICY = dict(
    retry=retry_if_exception(is_transient),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
)


@retry(**RETRY_POLICY)
async def clone_ui(base64_image, model):
    image_url = f"data:image/png;base64,{base64_image}"
    message: ChatCompletion = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            },
        ],
        extra_body=USAGE_ACCOUNTING,
    )
    return ModelResponse(message.choices[0].message.content, usage_of(message))
