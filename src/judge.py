from src.prompts import judge_prompt, judge_system
from tenacity import retry

from src.openrouter.client import client
from src.task import RETRY_POLICY
from openai.types.chat.chat_completion import ChatCompletion


@retry(**RETRY_POLICY)
async def run_judge(original_image, clone_image):
    original_image_url = f"data:image/png;base64,{original_image}"
    clone_image_url = f"data:image/png;base64,{clone_image}"
    message: ChatCompletion = await client.chat.completions.create(
        model="anthropic/claude-sonnet-4",
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
