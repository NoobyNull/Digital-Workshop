"""
Ollama Vision Provider
Implements vision analysis using local Ollama instance.
"""

import base64
import os
from typing import Dict, Any, Optional
import requests
from .base_provider import BaseProvider

class OllamaProvider(BaseProvider):
    """Ollama local vision provider."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "llava", base_url: str = "http://localhost:11434", **kwargs):
        """
        Initialize Ollama provider.
        
        Args:
            api_key: Not used for Ollama but kept for interface consistency
            model: Model to use for vision analysis
            base_url: Base URL for Ollama instance
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        self.model = model
        self.base_url = base_url
    
    def is_configured(self) -> bool:
        """Check if Ollama is accessible."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except (requests.RequestException, requests.ConnectionError):
            return False
    
    def list_available_models(self) -> list:
        """List available vision models from Ollama."""
        if not self.is_configured():
            return []
        
        try:
            url = f"{self.base_url}/api/tags"
            self.logger.info("Fetching Ollama models from: %s", url)
            response = requests.get(url, timeout=5)
            self.logger.info("Ollama API response status: %d", response.status_code)
            
            if response.status_code == 200:
                models_data = response.json()
                self.logger.info("Ollama API response data: %s", models_data)
                
                # Log all models
                all_models = [model['name'] for model in models_data.get('models', [])]
                self.logger.info("All available Ollama models: %s", all_models)
                
                # Filter for vision-capable models
                vision_models = [
                    model['name'].split(':')[0]  # Remove version tag
                    for model in models_data.get('models', [])
                    if any(vision_capable in model['name'].lower()
                           for vision_capable in ['llava', 'moondream', 'bakllava', 'vision'])
                ]
                self.logger.info("Filtered Ollama vision models: %s", vision_models)
                return list(set(vision_models))  # Remove duplicates
            else:
                self.logger.warning("Ollama API returned status %d", response.status_code)
                self.logger.warning("Response content: %s", response.text)
                return []
        except (requests.RequestException, requests.ConnectionError, ValueError) as e:
            self.logger.error("Failed to fetch Ollama models: %s", str(e))
            self.logger.info("Returning default Ollama model: llava")
            return ["llava"]  # Default vision model
    
    def analyze_image(self, image_path: str, prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze image using Ollama.
        
        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt
            
        Returns:
            Structured analysis results
        """
        if not self.is_configured():
            raise ValueError("Ollama provider is not configured or not accessible. Please ensure Ollama is running.")
        
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")
        
        try:
            # Read and encode the image
            with open(image_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Prepare the request
            data = {
                "model": self.model,
                "prompt": prompt or self.get_default_prompt(),
                "images": [image_data],
                "stream": False
            }
            
            # Make the API call
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=data,
                timeout=60
            )
            response.raise_for_status()
            
            # Extract and parse the response
            response_json = response.json()
            response_text = response_json.get("response", "")
            return self.parse_response(response_text)
            
        except Exception as e:
            self.logger.error("Error analyzing image with Ollama: %s", str(e))
            raise