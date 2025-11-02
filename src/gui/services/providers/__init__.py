"""
AI Vision Providers
Provides AI-powered image analysis capabilities for the application.
"""

from .base_provider import BaseProvider
from .openai_provider import OpenAIProvider
from .openrouter_provider import OpenRouterProvider

__all__ = [
    'BaseProvider',
    'OpenAIProvider',
    'OpenRouterProvider',
    'get_provider_class'
]

def get_provider_class(provider_id: str):
    """Get provider class by ID."""
    provider_mapping = {
        'openai': OpenAIProvider,
        'openrouter': OpenRouterProvider,
        'anthropic': None,  # To be implemented
        'gemini': None,     # To be implemented
        'xai': None,        # To be implemented
        'zai': None,        # To be implemented
        'perplexity': None, # To be implemented
        'ollama': None,     # To be implemented
        'ai_studio': None,  # To be implemented
    }
    return provider_mapping.get(provider_id)