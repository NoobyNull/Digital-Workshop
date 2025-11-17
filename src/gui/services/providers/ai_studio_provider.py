"""AI Studio / LM Studio Vision Provider

Implements vision analysis using LM Studio's OpenAI-compatible API.

LM Studio runs a local HTTP server that is compatible with the OpenAI
client. By default it listens on http://localhost:1234/v1 and does not
require a real API key, though the OpenAI client expects one.
"""

from typing import Optional

from .openai_provider import OpenAIProvider


class AIStudioProvider(OpenAIProvider):
    """LM Studio provider using the OpenAI-compatible HTTP API.

    This provider reuses the OpenAIProvider implementation but points the
    client at the local LM Studio endpoint by default.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-1.5-pro-vision-001",
        base_url: Optional[str] = None,
        **kwargs,
    ) -> None:
        """Initialize AI Studio / LM Studio provider.

        Args:
            api_key: Optional API key. If not provided, a dummy key is used as
                required by the OpenAI client but ignored by LM Studio.
            model: Model to use for vision analysis.
            base_url: Endpoint URL for the LM Studio OpenAI-compatible API.
                Defaults to the local LM Studio server.
        """
        # LM Studio's OpenAI-compatible API requires an api_key parameter but
        # ignores its value. Use a sensible default so the user does not have
        # to enter one.
        effective_key = api_key or "lm-studio"
        effective_base_url = base_url or "http://localhost:1234/v1"

        super().__init__(
            api_key=effective_key,
            model=model,
            base_url=effective_base_url,
            **kwargs,
        )

    def is_configured(self) -> bool:  # type: ignore[override]
        """Return True when a client was created.

        For LM Studio we treat the provider as configured as soon as the
        client exists, regardless of whether the user supplied an API key.
        """
        return self.client is not None

