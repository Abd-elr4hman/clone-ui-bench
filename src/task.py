from tenacity import retry, stop_after_attempt, wait_exponential
from src.openrouter.client import client
from src.prompts import system
from openai.types.chat.chat_completion import ChatCompletion

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
async def clone_ui(base64_image, model):
    image_url = f"data:image/png;base64,{base64_image}"
    try:
        message:ChatCompletion = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        
                        {
                            "type": "text",
                            "text": system
                        },
                        {
                            "type": "image_url",
                            "image_url":image_url
                        }
                    ]
                }
            ]
        )
        return message.choices[0].message.content
    
    except Exception as e:
        # Catch-all for other errors
        raise RuntimeError(f"Failed to run task: {str(e)}") from e
    