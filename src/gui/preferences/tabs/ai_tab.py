from __future__ import annotations

"""
Preferences dialog with tabbed interface:
- Display
- System
- Files
- Theming (live-apply + persist to AppData)

The Theming tab edits central color variables in gui.theme.COLORS and applies
changes live across the running app. On Save, the current theme is persisted
to AppData and loaded on next startup.
"""


from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)




class AITab(QWidget):
    """AI Description Service configuration tab."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.logger = None
        try:
            from src.core.logging_config import get_logger

            self.logger = get_logger(__name__)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
            pass
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Setup the AI configuration UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("AI Description Service")
        header.setStyleSheet("font-weight: bold; font-size: 13pt;")
        layout.addWidget(header)

        desc = QLabel(
            "Configure AI providers for automatic image description generation. "
            "Select your preferred provider and enter API keys to enable AI-powered descriptions."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.auto_tag_import_check = QCheckBox("Auto-tag imported models using AI after thumbnails")
        self.auto_tag_import_check.setToolTip(
            "When enabled, newly imported models will be submitted to the AI service for keywords/tags."
        )
        warning = QLabel(
            '<span style="color:#c00; font-weight:bold;">Note:</span> AI calls may incur charges from '
            "cloud providers. Consider using a self-hosted model like Ollama to avoid costs."
        )
        warning.setWordWrap(True)
        layout.addWidget(self.auto_tag_import_check)
        layout.addWidget(warning)

        # Provider Selection Group
        provider_group = QFrame()
        provider_layout = QVBoxLayout(provider_group)

        provider_label = QLabel("<b>AI Provider Selection</b>")
        provider_label.setStyleSheet("font-size: 11pt;")
        provider_layout.addWidget(provider_label)

        # Provider combo box
        provider_form = QFormLayout()
        self.provider_combo = QComboBox()
        self._populate_providers()
        provider_form.addRow("Preferred Provider:", self.provider_combo)
        provider_layout.addLayout(provider_form)

        layout.addWidget(provider_group)

        # API Configuration Group
        api_group = QFrame()
        api_layout = QVBoxLayout(api_group)

        api_label = QLabel("<b>API Configuration</b>")
        api_label.setStyleSheet("font-size: 11pt;")
        api_layout.addWidget(api_label)

        # Environment variable status
        env_status_desc = QLabel(
            "API keys can be provided via environment variables (recommended for security):\n"
            "• GOOGLE_API_KEY for Gemini\n"
            "• OPENAI_API_KEY for OpenAI\n"
            "• ANTHROPIC_API_KEY for Anthropic\n"
            "• OPENROUTER_API_KEY for OpenRouter\n"
            "Local providers (Ollama, LM Studio) do not require an API key; only the endpoint URL."
        )
        env_status_desc.setWordWrap(True)
        env_status_desc.setStyleSheet("font-size: 9pt; color: #666;")
        api_layout.addWidget(env_status_desc)

        # API Key input
        api_key_form = QFormLayout()
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        self.api_key_edit.setPlaceholderText("Enter API key for selected provider (or use environment variable)")
        api_key_form.addRow("API Key:", self.api_key_edit)
        api_layout.addLayout(api_key_form)

        # Model selection
        model_form = QFormLayout()
        self.model_combo = QComboBox()
        self.model_combo.setEditable(True)
        model_form.addRow("Model:", self.model_combo)
        api_layout.addLayout(model_form)

        # Base URL / endpoint selection
        base_url_form = QFormLayout()
        self.base_url_edit = QLineEdit()
        self.base_url_edit.setPlaceholderText(
            "Endpoint URL (for example http://localhost:11434/v1 for Ollama)"
        )
        base_url_form.addRow("Base URL:", self.base_url_edit)
        api_layout.addLayout(base_url_form)

        # Reset provider configuration
        reset_row = QHBoxLayout()
        reset_row.addStretch(1)
        self.reset_provider_button = QPushButton("Reset Provider to Defaults")
        self.reset_provider_button.clicked.connect(self._reset_current_provider)
        reset_row.addWidget(self.reset_provider_button)
        api_layout.addLayout(reset_row)

        layout.addWidget(api_group)

        # Custom Prompt Group
        prompt_group = QFrame()
        prompt_layout = QVBoxLayout(prompt_group)

        prompt_label = QLabel("<b>Custom Prompt</b>")
        prompt_label.setStyleSheet("font-size: 11pt;")
        prompt_layout.addWidget(prompt_label)

        prompt_desc = QLabel(
            "Customize the prompt used for image description. Use {image_path} as placeholder for image path."
        )
        prompt_desc.setWordWrap(True)
        prompt_layout.addWidget(prompt_desc)

        self.prompt_edit = QLineEdit()
        self.prompt_edit.setPlaceholderText("Describe this image in detail...")
        prompt_layout.addWidget(self.prompt_edit)

        layout.addWidget(prompt_group)

        # Batch Processing Group
        batch_group = QFrame()
        batch_layout = QVBoxLayout(batch_group)

        batch_label = QLabel("<b>Batch Processing</b>")
        batch_label.setStyleSheet("font-size: 11pt;")
        batch_layout.addWidget(batch_label)

        # Batch size
        batch_form = QFormLayout()
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 50)
        self.batch_size_spin.setValue(5)
        self.batch_size_spin.setSuffix(" images")
        batch_form.addRow("Batch Size:", self.batch_size_spin)
        batch_layout.addLayout(batch_form)

        # Enable batch processing
        self.enable_batch_check = QCheckBox("Enable batch processing for multiple images")
        batch_layout.addWidget(self.enable_batch_check)

        layout.addWidget(batch_group)

        # Test Connection Group
        test_group = QFrame()
        test_layout = QVBoxLayout(test_group)

        test_label = QLabel("<b>Connection Test</b>")
        test_label.setStyleSheet("font-size: 11pt;")
        test_layout.addWidget(test_label)

        test_desc = QLabel("Test your AI provider configuration to ensure it's working correctly.")
        test_desc.setWordWrap(True)
        test_layout.addWidget(test_desc)

        test_button_row = QHBoxLayout()
        test_button_row.addStretch(1)
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self._test_connection)
        test_button_row.addWidget(self.test_button)
        test_layout.addLayout(test_button_row)

        self.test_result_label = QLabel()
        self.test_result_label.setWordWrap(True)
        self.test_result_label.setStyleSheet("padding: 8px; border-radius: 4px;")
        test_layout.addWidget(self.test_result_label)

        layout.addWidget(test_group)

        layout.addStretch()

        # Connect signals
        self.provider_combo.currentIndexChanged.connect(self._on_provider_changed)
        # Also connect to activated signal for better compatibility
        self.provider_combo.activated.connect(self._on_provider_changed)
        self.api_key_edit.textChanged.connect(self._on_settings_changed)
        self.base_url_edit.textChanged.connect(self._on_settings_changed)

        self.model_combo.currentTextChanged.connect(self._on_settings_changed)
        self.prompt_edit.textChanged.connect(self._on_settings_changed)
        self.batch_size_spin.valueChanged.connect(self._on_settings_changed)
        self.enable_batch_check.stateChanged.connect(self._on_settings_changed)

    def _populate_providers(self) -> None:
        """Populate provider combo box."""
        try:
            from src.gui.services.ai_description_service import AIDescriptionService

            providers = AIDescriptionService.get_provider_display_names()
            for provider_id, provider_name in providers.items():
                self.provider_combo.addItem(provider_name, provider_id)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to populate providers: %s", e)

    def _populate_models(self, provider_id: str) -> None:
        """Populate model combo box for selected provider."""
        try:
            from src.gui.services.ai_description_service import AIDescriptionService

            # Clear existing items
            self.model_combo.clear()

            # Get available models for the provider
            models = AIDescriptionService.get_available_models(provider_id)

            if models:
                for model_id, model_name in models.items():
                    self.model_combo.addItem(model_name, model_id)
            else:
                # If no models found, add a default entry
                self.model_combo.addItem("Default Model", "default")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to populate models for {provider_id}: %s", e)
            # Add fallback model
            self.model_combo.clear()
            self.model_combo.addItem("Default Model", "default")

    def _load_settings(self) -> None:
        """Load current AI settings from QSettings."""
        try:
            from PySide6.QtCore import QSettings

            settings = QSettings()

            # Load provider selection (default to local Ollama)
            provider_id = settings.value("ai/provider_id", "ollama", type=str)
            if self.logger:
                self.logger.info("Loaded provider_id from QSettings: %s", provider_id)

            provider_index = self.provider_combo.findData(provider_id)
            if provider_index >= 0:
                # This will trigger _on_provider_changed and populate
                # provider-specific fields such as models, API key and base URL.
                self.provider_combo.setCurrentIndex(provider_index)

            # Load custom prompt
            prompt = settings.value("ai/custom_prompt", "", type=str)
            self.prompt_edit.setText(prompt)

            # Load batch settings
            batch_size = settings.value("ai/batch_size", 5, type=int)
            self.batch_size_spin.setValue(batch_size)

            enable_batch = settings.value("ai/enable_batch", False, type=bool)
            self.enable_batch_check.setChecked(enable_batch)

            # Import-time auto tagging
            self.auto_tag_import_check.setChecked(
                settings.value("ai/auto_tag_import", False, type=bool)
            )

            if self.logger:
                self.logger.info("✓ AI settings loaded from QSettings")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to load AI settings: %s", e, exc_info=True)

    def save_settings(self) -> None:
        """Save AI settings to QSettings."""
        try:
            from PySide6.QtCore import QSettings

            settings = QSettings()

            # Save provider selection
            provider_id = self.provider_combo.currentData()
            if self.logger:
                self.logger.info("Saving provider_id: %s", provider_id)
            if provider_id:
                settings.setValue("ai/provider_id", provider_id)
                # Keep AI description service in sync with preferences
                settings.setValue("ai_description/settings/default_provider", provider_id)

            # Save API key if provided by user
            api_key = self.api_key_edit.text().strip()
            if self.logger:
                self.logger.info(
                    "API key from field: %s (length: %s)",
                    "[PRESENT]" if api_key else "[EMPTY]",
                    len(api_key),
                )

            # Save model and base URL
            model_id = self.model_combo.currentData() or self.model_combo.currentText()
            base_url = self.base_url_edit.text().strip()

            # Backwards-compatible keys
            if api_key:
                settings.setValue("ai/api_key", api_key)
            if model_id:
                settings.setValue("ai/model_id", model_id)

            # Provider-specific configuration for AI description service
            if provider_id:
                group = f"ai_description/providers/{provider_id}"
                settings.setValue(f"{group}/api_key", api_key)
                settings.setValue(f"{group}/model", model_id or "")
                settings.setValue(f"{group}/base_url", base_url)
                is_local = provider_id in ("ollama", "ai_studio")
                enabled = bool(api_key or is_local)
                settings.setValue(f"{group}/enabled", enabled)

            # Save custom prompt
            prompt = self.prompt_edit.text().strip()
            settings.setValue("ai/custom_prompt", prompt)

            # Save batch settings
            settings.setValue("ai/batch_size", self.batch_size_spin.value())
            settings.setValue("ai/enable_batch", self.enable_batch_check.isChecked())
            settings.setValue("ai/auto_tag_import", self.auto_tag_import_check.isChecked())

            settings.sync()

            if self.logger:
                self.logger.info("\u2713 AI settings synced to QSettings")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to save AI settings: %s", e, exc_info=True)

    def _on_provider_changed(self, index: int) -> None:
        """Handle provider selection change."""
        del index  # unused
        provider_id = self.provider_combo.currentData()
        if not provider_id:
            self._on_settings_changed()
            return

        # Local providers (no API key required, endpoint required)
        local_providers = {"ollama", "ai_studio"}
        is_local = provider_id in local_providers

        if is_local:
            self.api_key_edit.setPlaceholderText(
                "Optional: API key (not required for local providers)"
            )
            self.base_url_edit.setPlaceholderText(
                "Endpoint URL for local provider (for example http://localhost:11434/v1)"
            )
        else:
            self.api_key_edit.setPlaceholderText(
                "Enter API key for selected provider (or use environment variable)"
            )
            self.base_url_edit.setPlaceholderText(
                "Optional: Override default endpoint URL for selected provider"
            )

        # Populate models for this provider
        self._populate_models(provider_id)

        # Load provider-specific settings
        try:
            from PySide6.QtCore import QSettings

            settings = QSettings()
            group = f"ai_description/providers/{provider_id}"

            # Base URL with sensible provider defaults
            default_base_urls = {
                "openai": "https://api.openai.com/v1",
                "openrouter": "https://openrouter.io/api/v1",
                "gemini": "https://generativelanguage.googleapis.com/v1",
                "anthropic": "https://api.anthropic.com",
                "ollama": "http://localhost:11434/v1",
                "ai_studio": "http://localhost:1234/v1",
            }
            base_url = settings.value(
                f"{group}/base_url",
                default_base_urls.get(provider_id, ""),
                type=str,
            )
            self.base_url_edit.setText(base_url)

            # API key resolution:
            # 1. Provider-specific stored key
            # 2. Global ai/api_key if this provider is the saved default
            # 3. Environment variable (cloud providers only)
            api_key = settings.value(f"{group}/api_key", "", type=str)

            default_provider = settings.value("ai/provider_id", "ollama", type=str)
            if not api_key and provider_id == default_provider:
                api_key = settings.value("ai/api_key", "", type=str)

            if not api_key and not is_local:
                import os

                env_var_map = {
                    "openai": "OPENAI_API_KEY",
                    "openrouter": "OPENROUTER_API_KEY",
                    "gemini": "GOOGLE_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY",
                }
                env_var = env_var_map.get(provider_id)
                if env_var:
                    env_value = os.getenv(env_var, "").strip()
                    if env_value:
                        api_key = env_value
                        if self.logger:
                            self.logger.info(
                                "Loaded API key for %s from environment variable %s",
                                provider_id,
                                env_var,
                            )

            self.api_key_edit.setText(api_key)

            # Model selection
            model_id = settings.value(f"{group}/model", "", type=str)
            if not model_id:
                model_id = settings.value("ai/model_id", "", type=str)

            if model_id:
                model_index = self.model_combo.findData(model_id)
                if model_index >= 0:
                    self.model_combo.setCurrentIndex(model_index)
                else:
                    self.model_combo.setCurrentText(model_id)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error(
                    "Failed to load provider-specific settings: %s", e, exc_info=True
                )

        self._on_settings_changed()

    def _on_settings_changed(self) -> None:
        """Handle settings change."""
        # Update test result to indicate unsaved changes (text only, no custom styling)
        self.test_result_label.setText("Settings changed - save to apply")


    def _reset_current_provider(self) -> None:
        """Reset only the currently selected provider to its default configuration."""
        provider_id = self.provider_combo.currentData()
        if not provider_id:
            return

        default_configs = {
            "openai": {
                "api_key": "",
                "model": "gpt-4-vision-preview",
                "base_url": "https://api.openai.com/v1",
            },
            "openrouter": {
                "api_key": "",
                "model": "gpt-4-vision-preview",
                "base_url": "https://openrouter.io/api/v1",
            },
            "gemini": {
                "api_key": "",
                "model": "gemini-2.5-flash",
                "base_url": "https://generativelanguage.googleapis.com/v1",
            },
            "anthropic": {
                "api_key": "",
                "model": "claude-3-5-sonnet-20241022",
                "base_url": "https://api.anthropic.com",
            },
            "ollama": {
                "api_key": "",
                "model": "llava",
                "base_url": "http://localhost:11434/v1",
            },
            "ai_studio": {
                "api_key": "",
                "model": "gemini-1.5-pro-vision-001",
                "base_url": "http://localhost:1234/v1",
            },
        }

        config = default_configs.get(provider_id)
        if not config:
            return

        # Update UI fields
        self.api_key_edit.clear()
        self.base_url_edit.setText(config["base_url"])

        self._populate_models(provider_id)
        default_model = config["model"]
        model_index = self.model_combo.findData(default_model)
        if model_index >= 0:
            self.model_combo.setCurrentIndex(model_index)
        else:
            self.model_combo.setCurrentText(default_model)

        # Persist defaults for this provider only
        try:
            from PySide6.QtCore import QSettings

            settings = QSettings()
            group = f"ai_description/providers/{provider_id}"
            settings.setValue(f"{group}/api_key", config["api_key"])
            settings.setValue(f"{group}/model", config["model"])
            settings.setValue(f"{group}/base_url", config["base_url"])
            is_local = provider_id in ("ollama", "ai_studio")
            settings.setValue(f"{group}/enabled", is_local)
            settings.sync()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error(
                    "Failed to reset provider %s: %s", provider_id, e, exc_info=True
                )

        self._show_test_result(
            "Provider reset to defaults. Remember to save settings.",
            "info",
        )

    def _test_connection(self) -> None:
        """Test AI provider connection."""
        try:
            import os

            from src.gui.services.ai_description_service import AIDescriptionService

            provider_id = self.provider_combo.currentData()
            api_key = self.api_key_edit.text().strip()
            model_id = self.model_combo.currentData() or self.model_combo.currentText()
            base_url = self.base_url_edit.text().strip()

            if not provider_id:
                self._show_test_result("Please select a provider.", "error")
                return

            local_providers = {"ollama", "ai_studio"}
            is_local = provider_id in local_providers

            # For cloud providers, require an API key (with environment fallback)
            if not is_local and not api_key:
                env_var_map = {
                    "openai": "OPENAI_API_KEY",
                    "openrouter": "OPENROUTER_API_KEY",
                    "gemini": "GOOGLE_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY",
                }
                env_var = env_var_map.get(provider_id)
                if env_var:
                    env_value = os.getenv(env_var, "").strip()
                    if env_value:
                        api_key = env_value
                        self._show_test_result(
                            f"Using API key from environment variable {env_var}.",
                            "info",
                        )

                if not api_key:
                    self._show_test_result(
                        "Please enter an API key or set the appropriate environment variable.",
                        "error",
                    )
                    return

            if not model_id:
                self._show_test_result("Please select or enter a model.", "error")
                return

            # Disable test button during test
            self.test_button.setEnabled(False)
            self.test_button.setText("Testing...")

            # Test provider connection (static method)
            success, message = AIDescriptionService.test_provider_connection(
                provider_id,
                api_key,
                model_id,
                base_url or None,
            )

            if success:
                self._show_test_result(f"Connection successful. {message}", "success")
            else:
                self._show_test_result(f"Connection failed: {message}", "error")

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self._show_test_result(f"Test failed: {str(e)}", "error")
        finally:
            self.test_button.setEnabled(True)
            self.test_button.setText("Test Connection")

    def _show_test_result(self, message: str, status: str) -> None:
        """Show test result message."""
        prefix_map = {
            "success": "Success: ",
            "error": "Error: ",
            "info": "Info: ",
        }
        prefix = prefix_map.get(status, "")
        self.test_result_label.setText(f"{prefix}{message}")

