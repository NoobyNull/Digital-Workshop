"""AI Description Service

Provides AI-powered image analysis capabilities for the application.
Integrates with the application's QSettings-based configuration system.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from PySide6.QtCore import QObject, Signal, QSettings
from PySide6.QtWidgets import QApplication

from .providers import BaseProvider, OpenAIProvider, OpenRouterProvider


class AIDescriptionService(QObject):
    """Service for AI-powered image description generation."""

    # Signals for UI updates
    analysis_started = Signal()
    analysis_completed = Signal(dict)  # Analysis results
    analysis_failed = Signal(str)  # Error message
    progress_updated = Signal(int)  # Progress percentage

    def __init__(self, config_manager=None) -> None:
        """
        Initialize the AI Description Service.

        Args:
            config_manager: Configuration manager for loading/saving settings
        """
        super().__init__()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.config_manager = config_manager
        self.providers: Dict[str, BaseProvider] = {}
        self.current_provider: Optional[BaseProvider] = None
        self.config = self._load_config()
        self._initialize_providers()

    def _load_config(self) -> Dict[str, Any]:
        """Load AI description configuration."""
        try:
            settings = QSettings()

            # Load provider configurations from QSettings
            providers = {}
            for provider_name in [
                "openai",
                "openrouter",
                "gemini",
                "anthropic",
                "ollama",
                "ai_studio",
            ]:
                group = f"ai_description/providers/{provider_name}"

                # Get API key from multiple sources (in order of priority):
                # 1. User-entered key in preferences (ai/api_key)
                # 2. Provider-specific key in preferences (ai_description/providers/{provider}/api_key)
                # 3. Environment variable
                api_key = ""

                # Check if this is the selected provider and has a user-entered key
                selected_provider = settings.value("ai/provider_id", "ollama", type=str)
                if provider_name == selected_provider:
                    api_key = settings.value("ai/api_key", "", type=str)

                # If not found, check provider-specific setting
                if not api_key:
                    api_key = settings.value(f"{group}/api_key", "", type=str)

                # If still not found, check environment variable
                if not api_key:
                    env_var_map = {
                        "openai": "OPENAI_API_KEY",
                        "openrouter": "OPENROUTER_API_KEY",
                        "gemini": "GOOGLE_API_KEY",
                        "anthropic": "ANTHROPIC_API_KEY",
                    }
                    api_key = os.getenv(env_var_map.get(provider_name, ""), "")

                # Get default model for each provider
                default_models = {
                    "openai": "gpt-4-vision-preview",
                    "openrouter": "gpt-4-vision-preview",
                    "gemini": "gemini-2.5-flash",
                    "anthropic": "claude-3-5-sonnet-20241022",
                    "ollama": "llava",
                    "ai_studio": "gemini-1.5-pro-vision-001",
                }

                # Default endpoints for providers that support custom base URLs
                default_base_urls = {
                    "openai": "https://api.openai.com/v1",
                    "openrouter": "https://openrouter.io/api/v1",
                    "gemini": "https://generativelanguage.googleapis.com/v1",
                    "anthropic": "https://api.anthropic.com",
                    "ollama": "http://localhost:11434/v1",
                    "ai_studio": "http://localhost:1234/v1",
                }

                providers[provider_name] = {
                    "api_key": api_key,
                    "model": settings.value(
                        f"{group}/model",
                        default_models.get(provider_name, ""),
                        type=str,
                    ),
                    "base_url": settings.value(
                        f"{group}/base_url",
                        default_base_urls.get(provider_name, ""),
                        type=str,
                    ),
                    # Local providers (ollama, ai_studio) are enabled by default; others
                    # remain disabled until explicitly configured.
                    "enabled": settings.value(
                        f"{group}/enabled",
                        provider_name in ("ollama", "ai_studio"),
                        type=bool,
                    ),
                }

            # Load custom prompts from QSettings
            custom_prompts = {}
            prompt_types = ["default", "mechanical", "artistic", "architectural"]
            for prompt_type in prompt_types:
                custom_prompts[prompt_type] = settings.value(
                    f"ai_description/custom_prompts/{prompt_type}",
                    self._get_default_prompt(prompt_type),
                    type=str,
                )

            # Load settings from QSettings
            settings_dict = {
                "default_provider": settings.value(
                    "ai_description/settings/default_provider", "ollama", type=str
                ),
                "auto_apply_results": settings.value(
                    "ai_description/settings/auto_apply_results", True, type=bool
                ),
                "batch_processing": settings.value(
                    "ai_description/settings/batch_processing", False, type=bool
                ),
            }

            return {
                "providers": providers,
                "custom_prompts": custom_prompts,
                "settings": settings_dict,
            }

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning(
                "Failed to load AI description config from QSettings, using defaults: %s",
                e,
            )
            return self._get_default_config()

    def _save_config(self) -> None:
        """Save AI description configuration."""
        try:
            settings = QSettings()

            # Save provider configurations
            for provider_name, provider_config in self.config.get("providers", {}).items():
                group = f"ai_description/providers/{provider_name}"
                settings.setValue(f"{group}/api_key", provider_config.get("api_key", ""))
                settings.setValue(
                    f"{group}/model",
                    provider_config.get("model", "gpt-4-vision-preview"),
                )
                settings.setValue(f"{group}/base_url", provider_config.get("base_url", ""))
                settings.setValue(f"{group}/enabled", provider_config.get("enabled", False))

            # Save custom prompts
            for prompt_type, prompt_text in self.config.get("custom_prompts", {}).items():
                settings.setValue(f"ai_description/custom_prompts/{prompt_type}", prompt_text)

            # Save settings
            for setting_name, setting_value in self.config.get("settings", {}).items():
                settings.setValue(f"ai_description/settings/{setting_name}", setting_value)

            settings.sync()
            self.logger.debug("AI description configuration saved to QSettings")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to save AI description config: %s", e)

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "providers": {
                "openai": {
                    "api_key": "",
                    "model": "gpt-4-vision-preview",
                    "base_url": "https://api.openai.com/v1",
                    "enabled": False,
                },
                "openrouter": {
                    "api_key": "",
                    "model": "gpt-4-vision-preview",
                    "base_url": "https://openrouter.io/api/v1",
                    "enabled": False,
                },
                "gemini": {
                    "api_key": "",
                    "model": "gemini-2.5-flash",
                    "base_url": "https://generativelanguage.googleapis.com/v1",
                    "enabled": False,
                },
                "anthropic": {
                    "api_key": "",
                    "model": "claude-3-5-sonnet-20241022",
                    "base_url": "https://api.anthropic.com",
                    "enabled": False,
                },
                "ollama": {
                    "api_key": "",
                    "model": "llava",
                    "base_url": "http://localhost:11434/v1",
                    "enabled": True,
                },
                "ai_studio": {
                    "api_key": "",
                    "model": "gemini-1.5-pro-vision-001",
                    "base_url": "http://localhost:1234/v1",
                    "enabled": True,
                },
            },
            "custom_prompts": {
                "default": """Analyze this image and provide a structured response in JSON format with the following fields:
- title: A concise, descriptive title for the image (string)
- description: A detailed description including objects, colors, textures, and overall composition (string)
- metadata_keywords: A list of relevant keywords that describe the image content, style, and context (array of strings)

Return ONLY valid JSON, no additional text.""",
                "mechanical": """Analyze this mechanical part and provide a structured response in JSON format with the following fields:
- title: A concise title for the mechanical part (string)
- description: Describe its function, materials, manufacturing considerations, and technical specifications (string)
- metadata_keywords: A list of relevant keywords (array of strings)

Return ONLY valid JSON, no additional text.""",
                "artistic": """Analyze this artistic work and provide a structured response in JSON format with the following fields:
- title: A concise title for the artwork (string)
- description: Describe the style, techniques, colors, composition, and artistic intent (string)
- metadata_keywords: A list of relevant keywords (array of strings)

Return ONLY valid JSON, no additional text.""",
                "architectural": """Analyze this architectural image and provide a structured response in JSON format with the following fields:
- title: A concise title for the building or structure (string)
- description: Describe the building style, materials, design elements, and spatial relationships (string)
- metadata_keywords: A list of relevant keywords (array of strings)

Return ONLY valid JSON, no additional text.""",
            },
            "settings": {
                "default_provider": "ollama",
                "auto_apply_results": True,
                "batch_processing": False,
            },
        }

    def _get_default_prompt(self, prompt_type: str) -> str:
        """Get default prompt for a specific type."""
        defaults = {
            "default": """Analyze this image and provide a structured response in JSON format with the following fields:
- title: A concise, descriptive title for the image (string)
- description: A detailed description including objects, colors, textures, and overall composition (string)
- metadata_keywords: A list of relevant keywords that describe the image content, style, and context (array of strings)

Return ONLY valid JSON, no additional text.""",
            "mechanical": """Analyze this mechanical part and provide a structured response in JSON format with the following fields:
- title: A concise title for the mechanical part (string)
- description: Describe its function, materials, manufacturing considerations, and technical specifications (string)
- metadata_keywords: A list of relevant keywords (array of strings)

Return ONLY valid JSON, no additional text.""",
            "artistic": """Analyze this artistic work and provide a structured response in JSON format with the following fields:
- title: A concise title for the artwork (string)
- description: Describe the style, techniques, colors, composition, and artistic intent (string)
- metadata_keywords: A list of relevant keywords (array of strings)

Return ONLY valid JSON, no additional text.""",
            "architectural": """Analyze this architectural image and provide a structured response in JSON format with the following fields:
- title: A concise title for the building or structure (string)
- description: Describe the building style, materials, design elements, and spatial relationships (string)
- metadata_keywords: A list of relevant keywords (array of strings)

Return ONLY valid JSON, no additional text.""",
        }
        return defaults.get(prompt_type, defaults["default"])

    def _initialize_providers(self) -> None:
        """Initialize AI providers based on configuration."""
        providers_config = self.config.get("providers", {})

        # Initialize OpenAI provider
        openai_config = providers_config.get("openai", {})
        if openai_config.get("api_key"):
            try:
                self.providers["openai"] = OpenAIProvider(
                    api_key=openai_config["api_key"],
                    model=openai_config.get("model", "gpt-4-vision-preview"),
                    base_url=openai_config.get("base_url") or None,
                )
                self.logger.info("OpenAI provider initialized")
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                self.logger.error("Failed to initialize OpenAI provider: %s", e)

        # Initialize OpenRouter provider
        openrouter_config = providers_config.get("openrouter", {})
        if openrouter_config.get("api_key"):
            try:
                self.providers["openrouter"] = OpenRouterProvider(
                    api_key=openrouter_config["api_key"],
                    model=openrouter_config.get("model", "gpt-4-vision-preview"),
                    base_url=openrouter_config.get("base_url") or None,
                )
                self.logger.info("OpenRouter provider initialized")
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                self.logger.error("Failed to initialize OpenRouter provider: %s", e)

        # Initialize Gemini provider
        gemini_config = providers_config.get("gemini", {})
        if gemini_config.get("api_key"):
            try:
                from .providers.gemini_provider import GeminiProvider

                self.providers["gemini"] = GeminiProvider(
                    api_key=gemini_config["api_key"],
                    model=gemini_config.get("model", "gemini-2.5-flash"),
                )
                self.logger.info("Gemini provider initialized")
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                self.logger.error("Failed to initialize Gemini provider: %s", e)

        # Initialize Anthropic provider
        anthropic_config = providers_config.get("anthropic", {})
        if anthropic_config.get("api_key"):
            try:
                from .providers.anthropic_provider import AnthropicProvider

                self.providers["anthropic"] = AnthropicProvider(
                    api_key=anthropic_config["api_key"],
                    model=anthropic_config.get("model", "claude-3-5-sonnet-20241022"),
                )
                self.logger.info("Anthropic provider initialized")
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                self.logger.error("Failed to initialize Anthropic provider: %s", e)

        # Initialize Ollama provider (local, optional API key)
        ollama_config = providers_config.get("ollama", {})
        if ollama_config.get("enabled", False):
            try:
                from .providers.ollama_provider import OllamaProvider

                self.providers["ollama"] = OllamaProvider(
                    api_key=ollama_config.get("api_key") or None,
                    model=ollama_config.get("model", "llava"),
                    base_url=ollama_config.get("base_url") or "http://localhost:11434/v1",
                )
                self.logger.info("Ollama provider initialized")
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                self.logger.error("Failed to initialize Ollama provider: %s", e)

        # Initialize AI Studio / LM Studio provider (local, optional API key)
        ai_studio_config = providers_config.get("ai_studio", {})
        if ai_studio_config.get("enabled", False):
            try:
                from .providers.ai_studio_provider import AIStudioProvider

                self.providers["ai_studio"] = AIStudioProvider(
                    api_key=ai_studio_config.get("api_key") or None,
                    model=ai_studio_config.get("model", "gemini-1.5-pro-vision-001"),
                    base_url=ai_studio_config.get("base_url") or "http://localhost:1234/v1",
                )
                self.logger.info("AI Studio provider initialized")
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                self.logger.error("Failed to initialize AI Studio provider: %s", e)


        # Set current provider
        default_provider = self.config.get("settings", {}).get("default_provider", "ollama")
        if default_provider in self.providers:
            self.current_provider = self.providers[default_provider]
        elif self.providers:
            # If default provider not available, use first available provider
            self.current_provider = next(iter(self.providers.values()))
            self.logger.info("Default provider not available, using first available provider")

    @staticmethod
    def get_available_providers() -> List[str]:
        """Get list of available AI providers."""
        return [
            "openai",
            "anthropic",
            "gemini",
            "xai",
            "zai",
            "perplexity",
            "ollama",
            "ai_studio",
            "openrouter",
        ]

    @staticmethod
    def get_provider_display_names() -> Dict[str, str]:
        """Get display names for AI providers."""
        return {
            "openai": "OpenAI GPT-4 Vision",
            "anthropic": "Anthropic Claude Vision",
            "gemini": "Google Gemini Vision",
            "xai": "xAI Grok Vision",
            "zai": "ZAI Vision",
            "perplexity": "Perplexity Vision",
            "ollama": "Ollama Local",
            "ai_studio": "Google AI Studio",
            "openrouter": "OpenRouter",
        }

    @staticmethod
    def get_available_models(provider_id: str) -> Dict[str, str]:
        """Get available models for a specific provider."""
        model_mappings = {
            "openai": {
                "gpt-4-vision-preview": "GPT-4 Vision (Preview)",
                "gpt-4o": "GPT-4o",
                "gpt-4o-mini": "GPT-4o Mini",
            },
            "anthropic": {
                "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet",
                "claude-3-opus-20240229": "Claude 3 Opus",
                "claude-3-sonnet-20240229": "Claude 3 Sonnet",
            },
            "gemini": {
                "gemini-2.5-flash": "Gemini 2.5 Flash",
                "gemini-2.5-pro-preview-03-25": "Gemini 2.5 Pro Preview",
                "gemini-2.5-flash-lite-preview-06-17": "Gemini 2.5 Flash Lite",
            },
            "xai": {"grok-vision-beta": "Grok Vision Beta"},
            "zai": {"zai-vision-1": "ZAI Vision 1"},
            "perplexity": {"llava-7b": "LLaVA 7B", "llava-13b": "LLaVA 13B"},
            "ollama": {"llava": "LLaVA (Local)", "bakllava": "BakLLaVA (Local)"},
            "ai_studio": {"gemini-1.5-pro-vision-001": "Gemini 1.5 Pro Vision (AI Studio)"},
            "openrouter": {
                "openai/gpt-4o": "GPT-4o (via OpenRouter)",
                "openai/gpt-4-vision-preview": "GPT-4 Vision (via OpenRouter)",
            },
        }
        return model_mappings.get(provider_id, {})

    @staticmethod
    def test_provider_connection(
        provider_id: str,
        api_key: str,
        model_id: str,
        base_url: str | None = None,
    ) -> tuple[bool, str]:
        """Test provider connection with given credentials.

        For OpenAI-compatible providers, the ``base_url`` parameter allows
        testing against custom endpoints such as local Ollama or LM Studio
        instances.
        """
        try:
            from .providers import get_provider_class

            provider_class = get_provider_class(provider_id)
            if not provider_class:
                return False, f"Provider {provider_id} not supported"

            # Create temporary provider instance for testing. Many providers
            # accept a ``base_url`` parameter, but some do not, so we handle
            # that gracefully.
            try:
                if base_url:
                    provider = provider_class(
                        api_key=api_key,
                        model=model_id,
                        base_url=base_url,
                    )
                else:
                    provider = provider_class(api_key=api_key, model=model_id)
            except TypeError:
                # Fallback for providers whose constructors do not accept a
                # ``base_url`` argument.
                provider = provider_class(api_key=api_key, model=model_id)

            if not provider.is_configured():
                return False, "Invalid configuration"

            # Test with a simple request (would need to check provider implementation)
            try:
                # For now, just check if we can list models
                models = provider.list_available_models()
                if models:
                    return (
                        True,
                        f"Connected successfully. {len(models)} models available.",
                    )
                return False, "No models available"
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                return False, f"Connection test failed: {str(e)}"

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            return False, f"Failed to initialize provider: {str(e)}"

    def get_provider_info(self, provider_name: str) -> Dict[str, Any]:
        """Get information about a specific provider."""
        if provider_name not in self.providers:
            return {}

        provider = self.providers[provider_name]
        return {
            "name": provider_name,
            "configured": provider.is_configured(),
            "available_models": provider.list_available_models(),
            "has_custom_endpoint": bool(getattr(provider, "base_url", None)),
        }

    def set_current_provider(self, provider_name: str) -> bool:
        """Set the current AI provider."""
        if provider_name in self.providers and self.providers[provider_name].is_configured():
            self.current_provider = self.providers[provider_name]
            # Update default provider in config
            self.config.setdefault("settings", {})["default_provider"] = provider_name
            self._save_config()
            return True
        return False

    def configure_provider(
        self, provider_name: str, api_key: str, model: str = "", base_url: str = ""
    ) -> bool:
        """Configure an AI provider.

        For local OpenAI-compatible providers (Ollama, AI Studio / LM Studio),
        the API key is optional and a default local endpoint is used when no
        base URL is provided.
        """
        try:
            if provider_name == "openai":
                provider = OpenAIProvider(
                    api_key=api_key,
                    model=model or "gpt-4-vision-preview",
                    base_url=base_url or None,
                )
                default_model = "gpt-4-vision-preview"
                default_base_url = base_url
            elif provider_name == "openrouter":
                provider = OpenRouterProvider(
                    api_key=api_key,
                    model=model or "gpt-4-vision-preview",
                    base_url=base_url or "https://openrouter.io/api/v1",
                )
                default_model = "gpt-4-vision-preview"
                default_base_url = base_url or "https://openrouter.io/api/v1"
            elif provider_name == "ollama":
                # Local Ollama provider: API key is optional, local endpoint by default
                from .providers.ollama_provider import OllamaProvider

                provider = OllamaProvider(
                    api_key=api_key or None,
                    model=model or "llava",
                    base_url=base_url or "http://localhost:11434/v1",
                )
                default_model = "llava"
                default_base_url = base_url or "http://localhost:11434/v1"
            elif provider_name == "ai_studio":
                # Local AI Studio / LM Studio provider: API key is optional
                from .providers.ai_studio_provider import AIStudioProvider

                provider = AIStudioProvider(
                    api_key=api_key or None,
                    model=model or "gemini-1.5-pro-vision-001",
                    base_url=base_url or "http://localhost:1234/v1",
                )
                default_model = "gemini-1.5-pro-vision-001"
                default_base_url = base_url or "http://localhost:1234/v1"
            else:
                self.logger.error("Unsupported provider: %s", provider_name)
                return False

            # Test provider configuration
            if not provider.is_configured():
                self.logger.error("Provider %s failed configuration test", provider_name)
                return False

            # Store provider
            self.providers[provider_name] = provider

            # Update configuration
            self.config.setdefault("providers", {})[provider_name] = {
                "api_key": api_key,
                "model": model or default_model,
                "base_url": default_base_url,
                "enabled": True,
            }

            self._save_config()
            self.logger.info("Provider %s configured successfully", provider_name)
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to configure provider %s: %s", provider_name, e)
            return False

    def test_configured_provider_connection(self, provider_name: str) -> bool:
        """Test connection to a configured provider."""
        if provider_name not in self.providers:
            return False

        try:
            provider = self.providers[provider_name]
            models = provider.list_available_models()
            return len(models) > 0
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Provider connection test failed for %s: %s", provider_name, e)
            return False

    def analyze_image(
        self,
        image_path: str,
        prompt: Optional[str] = None,
        provider_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Analyze an image using AI.

        Args:
            image_path: Path to the image file
            prompt: Optional custom prompt
            provider_name: Specific provider to use (uses current if not specified)

        Returns:
            Analysis results dictionary
        """
        # Select provider
        provider = None
        if provider_name and provider_name in self.providers:
            provider = self.providers[provider_name]
        elif self.current_provider:
            provider = self.current_provider
        else:
            raise ValueError("No AI provider configured")

        if not provider.is_configured():
            raise ValueError(f"Provider {provider_name or 'current'} is not configured")

        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            self.analysis_started.emit()
            self.progress_updated.emit(10)

            # Use custom prompt or get default
            analysis_prompt = prompt
            if not analysis_prompt:
                # Check for custom prompts in config
                custom_prompts = self.config.get("custom_prompts", {})
                analysis_prompt = custom_prompts.get("default", provider.get_default_prompt())

            self.progress_updated.emit(30)

            # Perform analysis
            try:
                result = provider.analyze_image(image_path, analysis_prompt)
            except Exception as e:
                # Normalize provider-level failures into a clear configuration error
                error_msg = f"AI provider error: {e}"
                self.logger.error(error_msg)
                self.analysis_failed.emit(error_msg)
                raise ValueError(error_msg) from e

            self.progress_updated.emit(90)

            # Add metadata
            result["provider_used"] = provider_name or "current"
            result["image_path"] = image_path

            # Get timestamp safely (QApplication might not exist in tests)
            try:
                app = QApplication.instance()
                if app:
                    result["timestamp"] = str(app.property("current_time"))
                else:
                    from datetime import datetime

                    result["timestamp"] = datetime.now().isoformat()
            except Exception:
                from datetime import datetime

                result["timestamp"] = datetime.now().isoformat()

            self.progress_updated.emit(100)
            self.analysis_completed.emit(result)

            return result

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Analysis failed: {str(e)}"
            self.logger.error(error_msg)
            self.analysis_failed.emit(error_msg)
            raise

    def get_custom_prompts(self) -> Dict[str, str]:
        """Get custom prompts configuration."""
        return self.config.get("custom_prompts", {})

    def set_custom_prompt(self, prompt_type: str, prompt_text: str) -> None:
        """Set a custom prompt."""
        self.config.setdefault("custom_prompts", {})[prompt_type] = prompt_text
        self._save_config()

    def get_settings(self) -> Dict[str, Any]:
        """Get service settings."""
        return self.config.get("settings", {})

    def update_settings(self, settings: Dict[str, Any]) -> None:
        """Update service settings."""
        self.config.setdefault("settings", {}).update(settings)
        self._save_config()

    def is_available(self) -> bool:
        """Check if AI description service is available."""
        return len(self.get_available_providers()) > 0

    def get_provider_models(self, provider_name: str) -> List[str]:
        """Get available models for a provider."""
        if provider_name not in self.providers:
            return []
        return self.providers[provider_name].list_available_models()
