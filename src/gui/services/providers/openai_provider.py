"""
OpenAI Vision Provider
Implements vision analysis using OpenAI's GPT-4 Vision API.
"""

import base64
import os
from typing import Dict, Any, Optional
import openai
from .base_provider import BaseProvider


class OpenAIProvider(BaseProvider):
    """OpenAI GPT-4 Vision provider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-vision-preview",
        base_url: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model to use for vision analysis
            base_url: Optional custom endpoint URL for OpenAI-compatible providers
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        self.model = model
        self.base_url = base_url
        self.client = None

        if self.api_key:
            if self.base_url:
                self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            else:
                self.client = openai.OpenAI(api_key=self.api_key)

    def is_configured(self) -> bool:
        """Check if OpenAI API key is configured."""
        return self.api_key is not None and self.client is not None

    def list_available_models(self) -> list:
        """List available vision models from OpenAI."""
        if not self.is_configured():
            return []

        try:
            self.logger.info("Fetching OpenAI models...")
            models = self.client.models.list()
            self.logger.info("OpenAI API response received. Total models: %d", len(models.data))

            # Log all models for debugging
            all_model_ids = [model.id for model in models.data]
            self.logger.info("All available models: %s", all_model_ids)

            # Filter for vision-capable models
            vision_models = [
                model.id
                for model in models.data
                if "vision" in model.id.lower() or "gpt-4" in model.id.lower()
            ]
            self.logger.info("Filtered vision models: %s", vision_models)
            return vision_models
        except (openai.APIError, openai.OpenAIError, ConnectionError) as e:
            self.logger.error("Failed to fetch OpenAI models: %s", str(e))
            self.logger.info("Returning default OpenAI models")
            # Return default models if API call fails
            return ["gpt-4-vision-preview", "gpt-4o", "gpt-4o-mini"]

    def analyze_image(self, image_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze image using OpenAI's GPT-4 Vision.

        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt

        Returns:
            Structured analysis results
        """
        if not self.is_configured():
            raise ValueError("OpenAI provider is not configured. Please provide an API key.")

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
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt or self.get_default_prompt()},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:{mime_type};base64,{image_data}"},
                        },
                    ],
                }
            ]

            # Make the API call
            response = self.client.chat.completions.create(
                model=self.model, messages=messages, max_tokens=1000
            )

            # Extract and parse the response
            response_text = response.choices[0].message.content
            return self.parse_response(response_text)

        except Exception as e:
            self.logger.error("Error analyzing image with OpenAI: %s", str(e))
            raise
