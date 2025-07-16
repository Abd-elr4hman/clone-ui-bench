import anthropic
from prompts import judge_prompt
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def run_judge(original_image, clone_image):
    client = anthropic.AsyncAnthropic()
    
    try:
        judge_message = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10000,
            temperature=1,
            system=judge_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": original_image,
                            }
                        },
                        {
                            "type": "image",
                            "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": clone_image,
                            }
                        },
                        {
                            "type": "text",
                            "text": "given these two images of the same website, one of them is a clone and another is the original... on a scale of 1 to 5 rate how good the cloning is."
                        }
                    ]
                }
            ]
        )
        return judge_message.content[0].text
    except Exception as e:
        # Catch-all for other errors
        raise RuntimeError(f"Failed to run judge: {str(e)}") from e

    