from abc import ABC, abstractmethod
from tenacity import retry, stop_after_attempt, wait_exponential

import asyncio
from asyncio import Semaphore

from prompts import system

import anthropic

CONCURRENT_REQUESTS_PER_PROVIDER = 3

class Provider(ABC):
    @abstractmethod
    def run_task(self):
        pass

    @classmethod
    @abstractmethod
    def get_supported_models(cls):
        """Return list of supported model names"""
        pass

    @classmethod
    def supports_model(cls, model_name):
        """Check if this provider supports a model"""
        return model_name in cls.get_supported_models()
    

# Thread-safe singleton client 
# Rate limiting 
# Retry logic
# Clean error handling
# Proper async/await usage
class AnthropicProvider(Provider):
    MODEL_LIST = [
        "claude-sonnet-4-20250514",
        "claude-opus-20240514",
        "claude-haiku-20240307"
    ]
    _client = None
    _lock = asyncio.Lock()

    # Limit concurrent requests per provider.. that means only x requests can be sent to anthropic at a time
    _semaphore = Semaphore(CONCURRENT_REQUESTS_PER_PROVIDER)  # not limiting concurrent requests will likely fail due to anthropic rate limits

    def __init__(self, model_name):
        if model_name not in self.MODEL_LIST:
            raise ValueError(f"Unsupported model: {model_name}")
        self.model_name = model_name  # Store model name in instance

    @classmethod
    async def get_client(cls):
        if cls._client is None:
            async with cls._lock:
                if cls._client is None:
                    cls._client = anthropic.AsyncAnthropic()
        return cls._client  

    @classmethod
    def get_supported_models(cls):
        return cls.MODEL_LIST
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def run_task(self, base64_image):
        client = await self.get_client()
        async with self._semaphore:
            try:
                message = await client.messages.create(
                    model=self.model_name,
                    max_tokens=10000,
                    temperature=1,
                    system=system,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": base64_image,
                                    }
                                },
                                {
                                    "type": "text",
                                    "text": "clone this website"
                                }
                            ]
                        }
                    ]
                )
                return message.content[0].text
            
            except Exception as e:
                # Catch-all for other errors
                raise RuntimeError(f"Failed to run task: {str(e)}") from e


class ProviderFactory:
    # Registry of available providers
    PROVIDERS = [AnthropicProvider]
    
    @classmethod
    def get_provider(cls, model_name):
        """Instantiate the appropriate provider for a model"""
        for provider_cls in cls.PROVIDERS:
            if provider_cls.supports_model(model_name):
                return provider_cls(model_name) 
        raise ValueError(f"No provider found for model: {model_name}")