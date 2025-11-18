"""Ollama Vision Provider

Implements vision analysis using Ollama's OpenAI-compatible API.

Ollama runs locally by default and does not require a real API key.
We still pass a dummy key because the OpenAI client expects one, but
from the user's perspective the key is optional.
"""

from typing import Optional

from .openai_provider import OpenAIProvider


class OllamaProvider(OpenAIProvider):
    """Ollama provider using the OpenAI-compatible HTTP API.

    This provider reuses the OpenAIProvider implementation but points the
    client at the local Ollama endpoint by default.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llava",
        base_url: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Initialize Ollama provider.

        Args:
            api_key: Optional API key. If not provided, a dummy key is used as
                required by the OpenAI client but ignored by Ollama.
            model: Model to use for vision analysis (for example "llava").
            base_url: Endpoint URL for the Ollama OpenAI-compatible API.
                Defaults to the local Ollama server.
        """
        # Ollama's OpenAI-compatible API requires an api_key parameter but
        # ignores its value. Use a sensible default so the user does not have
        # to enter one.
        effective_key = api_key or "ollama"
        effective_base_url = base_url or "http://localhost:11434/v1"

        super().__init__(
            api_key=effective_key,
            model=model,
            base_url=effective_base_url,
            **kwargs,
        )

    def is_configured(self) -> bool:  # type: ignore[override]
        """Return True when a client was created.

        For Ollama we treat the provider as configured as soon as the client
        exists, regardless of whether the user supplied an API key or not.
        """
        return self.client is not None
