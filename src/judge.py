from src.prompts import judge_prompt, judge_system
from tenacity import retry, stop_after_attempt, wait_exponential

from src.openrouter.client import client
from openai.types.chat.chat_completion import ChatCompletion


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
async def run_judge(original_image, clone_image):
    original_image_url = f"data:image/png;base64,{original_image}"
    clone_image_url = f"data:image/png;base64,{clone_image}"
    try:
        message: ChatCompletion = await client.chat.completions.create(
            model="anthropic/claude-sonnet-4",
            messages=[
                {"role": "system", "content": [{"type": "text", "text": judge_system}]},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": original_image_url,
                        },
                        {
                            "type": "image_url",
                            "image_url": clone_image_url,
                        },
                        {"type": "text", "text": judge_prompt},
                    ],
                },
            ],
        )
        return message.choices[0].message.content
    except Exception as e:
        # Catch-all for other errors
        raise RuntimeError(f"Failed to run judge: {str(e)}") from e
