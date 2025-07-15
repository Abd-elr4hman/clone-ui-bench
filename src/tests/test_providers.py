from src.providers import ProviderFactory, AnthropicProvider

def test_provider_factory():
    model_name = "claude-sonnet-4-20250514"
    provider = ProviderFactory.get_provider(model_name)
    assert isinstance(provider, AnthropicProvider)