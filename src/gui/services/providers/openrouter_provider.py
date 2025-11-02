"""
OpenRouter Vision Provider
Implements vision analysis using OpenRouter's API (OpenAI-compatible).
"""

import base64
import os
from typing import Dict, Any, Optional
import openai
from .base_provider import BaseProvider

class OpenRouterProvider(BaseProvider):
    """OpenRouter vision provider (OpenAI-compatible)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-vision-preview", base_url: Optional[str] = None, **kwargs):
        """
        Initialize OpenRouter provider.

        Args:
            api_key: OpenRouter API key
            model: Model to use for vision analysis
            base_url: Optional custom endpoint URL (defaults to OpenRouter)
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        self.model = model
        self.base_url = base_url or "https://openrouter.io/api/v1"
        self.client = None

        if self.api_key:
            self.client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)

    def is_configured(self) -> bool:
        """Check if OpenRouter API key is configured."""
        return self.api_key is not None and self.client is not None

    def list_available_models(self) -> list:
        """List available vision models from OpenRouter."""
        if not self.is_configured():
            return []

        try:
            self.logger.info("Fetching OpenRouter models...")
            models = self.client.models.list()
            self.logger.info("OpenRouter API response received. Total models: %d", len(models.data))

            # Log all models for debugging
            all_model_ids = [model.id for model in models.data]
            self.logger.info("All available models: %s", all_model_ids)

            # Filter for vision-capable models
            vision_models = [
                model.id for model in models.data
                if 'vision' in model.id.lower() or 'gpt-4' in model.id.lower() or 'claude' in model.id.lower()
            ]
            self.logger.info("Filtered vision models: %s", vision_models)
            return vision_models
        except (openai.APIError, openai.OpenAIError, ConnectionError) as e:
            self.logger.error("Failed to fetch OpenRouter models: %s", str(e))
            self.logger.info("Returning default OpenRouter models")
            # Return default models if API call fails
            return [
                "gpt-4-vision-preview",
                "gpt-4o",
                "gpt-4o-mini",
                "claude-3-opus-20240229",
                "claude-3-sonnet-20240229"
            ]

    def analyze_image(self, image_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze image using OpenRouter's API.

        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt

        Returns:
            Structured analysis results
        """
        if not self.is_configured():
            raise ValueError("OpenRouter provider is not configured. Please provide an API key.")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            # Read and encode the image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')

            # Determine image MIME type
            ext = os.path.splitext(image_path)[1].lower()
            mime_type = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.webp': 'image/webp'
            }.get(ext, 'image/jpeg')

            # Prepare the message
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt or self.get_default_prompt()
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{image_data}"
                            }
                        }
                    ]
                }
            ]

            # Make the API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1000
            )

            # Extract and parse the response
            response_text = response.choices[0].message.content
            return self.parse_response(response_text)

        except Exception as e:
            self.logger.error("Error analyzing image with OpenRouter: %s", str(e))
            raise