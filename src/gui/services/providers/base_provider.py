"""
Base Provider Interface
Defines the common interface for all AI vision providers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import json
import logging


class BaseProvider(ABC):
    """Base class for all AI vision providers."""

    def __init__(self, api_key: Optional[str] = None, **kwargs) -> None:
        """
        Initialize the provider with API key and configuration.

        Args:
            api_key: API key for the provider
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def analyze_image(
        self, image_path: str, prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze an image and return structured results.

        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt for analysis

        Returns:
            Dictionary containing:
            - title: Generated title for the image
            - description: Detailed description of the image
            - metadata_keywords: List of relevant keywords
        """
        raise NotImplementedError("Subclasses must implement analyze_image method")

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Check if the provider is properly configured with required credentials.

        Returns:
            True if configured, False otherwise
        """
        raise NotImplementedError("Subclasses must implement is_configured method")

    def list_available_models(self) -> list:
        """
        List available models for the provider.

        Returns:
            List of available model names
        """
        # Default implementation returns empty list
        # Providers can override this to fetch available models
        return []

    def get_default_prompt(self) -> str:
        """
        Get the default prompt for image analysis.

        Returns:
            Default prompt string
        """
        return (
            "Analyze this image and return ONLY valid JSON with these fields:\n"
            "- title: A concise, descriptive title of what the image shows\n"
            "- category: Brief category for the subject (e.g., wildlife, architecture)\n"
            "- description: Describe what the image is representing (e.g., 'A hunting dog on alert' "
            "rather than 'A carving of a dog') focusing on subject and scene, not medium\n"
            "- metadata_keywords: An array of keywords for the subject/context/style\n"
        )

    def parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the response from the AI provider into a structured format.

        Args:
            response_text: Raw response text from the AI provider

        Returns:
            Structured dictionary with title, description, and metadata_keywords
        """
        if not response_text:
            return {
                "title": "Image Analysis",
                "description": "",
                "metadata_keywords": [],
                "category": "Uncategorized",
            }
        try:
            # Try to extract JSON from the response
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_str = response_text[start:end].strip()
            elif "{" in response_text and "}" in response_text:
                start = response_text.find("{")
                end = response_text.rfind("}") + 1
                json_str = response_text[start:end]
            else:
                # If no JSON found, create a structured response from the text
                return {
                    "title": "Image Analysis",
                    "description": response_text.strip(),
                    "category": "Uncategorized",
                    "metadata_keywords": [],
                }

            result = json.loads(json_str)

            # Ensure required fields exist
            if "title" not in result:
                result["title"] = "Image Analysis"
            if "description" not in result:
                result["description"] = str(result)
            if "category" not in result:
                result["category"] = "Uncategorized"
            if "metadata_keywords" not in result:
                result["metadata_keywords"] = []

            # Normalize keywords to list
            if isinstance(result["metadata_keywords"], str):
                result["metadata_keywords"] = [
                    kw.strip()
                    for kw in result["metadata_keywords"].split(",")
                    if kw.strip()
                ]
            if not isinstance(result["metadata_keywords"], list):
                result["metadata_keywords"] = [str(result["metadata_keywords"])]

            return result

        except (json.JSONDecodeError, KeyError, TypeError) as e:
            self.logger.warning("Failed to parse response as JSON: %s", e)
            return {
                "title": "Image Analysis",
                "description": response_text.strip(),
                "metadata_keywords": [],
            }
