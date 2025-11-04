"""
Anthropic Vision Provider
Implements vision analysis using Anthropic's Claude API.
"""

import base64
import os
from typing import Dict, Any, Optional
import anthropic
from .base_provider import BaseProvider


class AnthropicProvider(BaseProvider):
    """Anthropic Claude vision provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        base_url: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model to use for vision analysis
            base_url: Optional custom endpoint URL for Anthropic-compatible providers
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        self.model = model
        self.base_url = base_url
        self.client = None

        if self.api_key:
            if self.base_url:
                self.client = anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)
            else:
                self.client = anthropic.Anthropic(api_key=self.api_key)

    def is_configured(self) -> bool:
        """Check if Anthropic API key is configured."""
        return self.api_key is not None and self.client is not None

    def list_available_models(self) -> list:
        """List available vision models from Anthropic."""
        if not self.is_configured():
            return []

        try:
            # Anthropic doesn't have a public models list API, so return known vision models
            # These are the Claude 3 models that support vision
            return [
                "claude-3-5-sonnet-20241022",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229",
                "claude-3-haiku-20240307",
            ]
        except (anthropic.APIError, ConnectionError) as e:
            self.logger.warning("Failed to fetch Anthropic models: %s", str(e))
            return ["claude-3-5-sonnet-20241022", "claude-3-opus-20240229"]

    def analyze_image(self, image_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze image using Anthropic's Claude.

        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt

        Returns:
            Structured analysis results
        """
        if not self.is_configured():
            raise ValueError("Anthropic provider is not configured. Please provide an API key.")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            # Read and encode the image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")

            # Determine image MIME type
            ext = os.path.splitext(image_path)[1].lower()
            mime_type = {
                ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg",
                ".png": "image/png",
                ".gif": "image/gif",
                ".webp": "image/webp",
            }.get(ext, "image/jpeg")

            # Prepare the message
            message = {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt or self.get_default_prompt()},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": image_data,
                        },
                    },
                ],
            }

            # Make the API call
            response = self.client.messages.create(
                model=self.model, max_tokens=1000, messages=[message]
            )

            # Extract and parse the response
            response_text = response.content[0].text
            return self.parse_response(response_text)

        except Exception as e:
            self.logger.error("Error analyzing image with Anthropic: %s", str(e))
            raise
