import asyncio

from src.prompts import judge_prompt, judge_system
from tenacity import retry

from src.openrouter.client import client
from src.task import RETRY_POLICY
from openai.types.chat.chat_completion import ChatCompletion

# Judged by a panel rather than one model: averaging across labs dilutes any
# single judge's preference for its own family. Per-judge scores are kept so
# that bias stays measurable instead of invisible.
DEFAULT_JUDGES = [
    "google/gemini-3.8-flash",
    "x-ai/grok-4.6",
    "openai/gpt-6-astra",
]


@retry(**RETRY_POLICY)
async def run_judge(original_image, clone_image, judge_model: str):
    original_image_url = f"data:image/png;base64,{original_image}"
    clone_image_url = f"data:image/png;base64,{clone_image}"
    message: ChatCompletion = await client.chat.completions.create(
        model=judge_model,
        messages=[
            {"role": "system", "content": [{"type": "text", "text": judge_system}]},
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": original_image_url},
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": clone_image_url},
                    },
                    {"type": "text", "text": judge_prompt},
                ],
            },
        ],
    )
    return message.choices[0].message.content


async def run_judges(original_image, clone_image, judge_models):
    """Score one clone with every judge on the panel, concurrently.

    Returns {judge_model: response_text_or_None}. A judge that fails is
    recorded as None rather than sinking the whole scenario - a panel of two
    still produces a usable score.
    """
    responses = await asyncio.gather(
        *(run_judge(original_image, clone_image, m) for m in judge_models),
        return_exceptions=True,
    )

    out = {}
    for model, response in zip(judge_models, responses):
        if isinstance(response, BaseException):
            print(f"judge {model} failed: {type(response).__name__}: {response}")
            out[model] = None
        else:
            out[model] = response
    return out
