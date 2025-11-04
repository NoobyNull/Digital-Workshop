"""
Google Gemini Vision Provider
Implements vision analysis using Google's Gemini API.
"""

import os
from typing import Dict, Any, Optional
import google.generativeai as genai
from .base_provider import BaseProvider


class GeminiProvider(BaseProvider):
    """Google Gemini vision provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash", **kwargs) -> None:
        """
        Initialize Gemini provider.

        Args:
            api_key: Google AI API key
            model: Model to use for vision analysis
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        self.model_name = model
        self.model = None

        if self.api_key:
            genai.configure(api_key=self.api_key)

    def is_configured(self) -> bool:
        """Check if Google AI API key is configured."""
        # For Gemini, we only need the API key to be configured
        # The model can be set later
        return self.api_key is not None

    def list_available_models(self) -> list:
        """List available vision models from Google Gemini."""
        if not self.is_configured():
            self.logger.info("Gemini provider not configured, returning empty model list")
            return []

        self.logger.info("Returning available Gemini vision models")
        # Updated list of vision models for the new Gemini API (2.5 series)
        return [
            "gemini-2.5-flash",
            "gemini-2.5-pro-preview-03-25",
            "gemini-2.5-flash-lite-preview-06-17",
        ]

    def analyze_image(self, image_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze image using Google's Gemini.

        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt

        Returns:
            Structured analysis results
        """
        if not self.is_configured():
            raise ValueError("Gemini provider is not configured. Please provide an API key.")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Get model name - use the configured model or default
        model_name = self.model_name or "gemini-2.5-flash"
        if isinstance(self.model, str):
            model_name = self.model

        self.logger.info("Using Gemini model: %s", model_name)

        try:
            # Load the image
            import PIL.Image

            image = PIL.Image.open(image_path)

            # Prepare the prompt
            analysis_prompt = prompt or self.get_default_prompt()

            # Make the API call using genai.GenerativeModel
            model = genai.GenerativeModel(model_name)
            response = model.generate_content([analysis_prompt, image])

            # Extract and parse the response
            response_text = response.text
            return self.parse_response(response_text)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error analyzing image with Gemini: %s", str(e))
            raise
