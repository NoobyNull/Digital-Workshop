"""
Perplexity Vision Provider
Implements vision analysis using Perplexity's API.
"""

import base64
import os
from typing import Dict, Any, Optional
import requests
from .base_provider import BaseProvider

class PerplexityProvider(BaseProvider):
    """Perplexity vision provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.2-90b-vision", base_url: Optional[str] = None, **kwargs):
        """
        Initialize Perplexity provider.

        Args:
            api_key: Perplexity API key
            model: Model to use for vision analysis
            base_url: Optional custom endpoint URL
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        self.model = model
        self.base_url = base_url or "https://api.perplexity.ai"
    
    def is_configured(self) -> bool:
        """Check if Perplexity API key is configured."""
        return self.api_key is not None
    
    def list_available_models(self) -> list:
        """List available vision models from Perplexity."""
        if not self.is_configured():
            return []
        
        # Perplexity vision models
        return ["llama-3.2-90b-vision", "llama-3.2-11b-vision"]
    
    def analyze_image(self, image_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze image using Perplexity.
        
        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt
            
        Returns:
            Structured analysis results
        """
        if not self.is_configured():
            raise ValueError("Perplexity provider is not configured. Please provide an API key.")
        
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
            
            # Prepare the request
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
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
                ],
                "max_tokens": 1000
            }
            
            # Make the API call
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            # Extract and parse the response
            response_json = response.json()
            response_text = response_json["choices"][0]["message"]["content"]
            return self.parse_response(response_text)
            
        except Exception as e:
            self.logger.error("Error analyzing image with Perplexity: %s", str(e))
            raise