"""
AI Vision Providers
Provides AI-powered image analysis capabilities for the application.
"""

from .base_provider import BaseProvider
from .openai_provider import OpenAIProvider
from .openrouter_provider import OpenRouterProvider
from .gemini_provider import GeminiProvider
from .anthropic_provider import AnthropicProvider
from .ollama_provider import OllamaProvider
from .ai_studio_provider import AIStudioProvider

__all__ = [
    "BaseProvider",
    "OpenAIProvider",
    "OpenRouterProvider",
    "GeminiProvider",
    "AnthropicProvider",
    "OllamaProvider",
    "AIStudioProvider",
    "get_provider_class",
]


def get_provider_class(provider_id: str):
    """Get provider class by ID.

    Returns the provider implementation class for a given provider ID.
    Providers that are not yet implemented return None.
    """
    provider_mapping = {
        "openai": OpenAIProvider,
        "openrouter": OpenRouterProvider,
        "anthropic": AnthropicProvider,
        "gemini": GeminiProvider,
        "xai": None,  # To be implemented
        "zai": None,  # To be implemented
        "perplexity": None,  # To be implemented
        "ollama": OllamaProvider,
        "ai_studio": AIStudioProvider,
    }
    return provider_mapping.get(provider_id)
