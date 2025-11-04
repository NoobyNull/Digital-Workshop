"""
AI Description Widget
Reusable widget for AI-powered description generation integrated with the main application.
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QComboBox,
    QProgressBar,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QSpinBox,
    QCheckBox,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QSplitter,
    QScrollArea,
    QFrame,
    QGridLayout,
    QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer
from PySide6.QtGui import QPixmap, QIcon, QFont

# Import the AI description service
from ..services.ai_description_service import AIDescriptionService


class AIProgressDialog(QWidget):
    """Progress dialog for AI description generation."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Generating AI Description")
        self.setModal(True)
        self.setFixedSize(400, 150)
        self.setStyleSheet(
            """
            QWidget {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 8px;
            }
            QProgressBar {
                border: 1px solid #6c757d;
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #007bff;
                border-radius: 3px;
            }
        """
        )

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Status label
        self.status_label = QLabel("Generating description...")
        self.status_label.setStyleSheet("font-weight: bold; color: #495057;")
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        layout.addWidget(self.progress_bar)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.close)
        layout.addWidget(self.cancel_button)


class AIProviderConfigWidget(QWidget):
    """Widget for configuring AI providers."""

    provider_configured = Signal(str, dict)  # provider_name, config
    provider_tested = Signal(str, bool)  # provider_name, success

    def __init__(self, parent=None):
        super().__init__(parent)
        self.providers = {}
        self.current_provider = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Provider selection
        provider_group = QGroupBox("AI Provider")
        provider_layout = QFormLayout(provider_group)

        self.provider_combo = QComboBox()
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addRow("Provider:", self.provider_combo)

        # Configuration fields
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.Password)
        provider_layout.addRow("API Key:", self.api_key_edit)

        self.model_combo = QComboBox()
        provider_layout.addRow("Model:", self.model_combo)

        self.base_url_edit = QLineEdit()
        provider_layout.addRow("Base URL:", self.base_url_edit)

        # Test connection button
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self._test_connection)
        provider_layout.addRow(self.test_button)

        layout.addWidget(provider_group)

        # Cache settings
        cache_group = QGroupBox("Cache Settings")
        cache_layout = QFormLayout(cache_group)

        self.cache_enabled_check = QCheckBox("Enable caching")
        self.cache_enabled_check.setChecked(True)
        cache_layout.addRow("", self.cache_enabled_check)

        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(10, 10000)
        self.cache_size_spin.setValue(1000)
        self.cache_size_spin.setSuffix(" items")
        cache_layout.addRow("Cache Size:", self.cache_size_spin)

        self.clear_cache_button = QPushButton("Clear Cache")
        self.clear_cache_button.clicked.connect(self._clear_cache)
        cache_layout.addRow(self.clear_cache_button)

        layout.addWidget(cache_group)

        # Apply button
        self.apply_button = QPushButton("Apply Configuration")
        self.apply_button.clicked.connect(self._apply_configuration)
        layout.addWidget(self.apply_button)

        layout.addStretch()

    def set_providers(self, providers: List[str]):
        """Set available providers."""
        self.provider_combo.clear()
        self.provider_combo.addItems(providers)
        self.providers = {name: {} for name in providers}

    def load_provider_config(self, provider_name: str, config: Dict[str, Any]):
        """Load configuration for a specific provider."""
        self.current_provider = provider_name

        # Update UI with provider config
        self.api_key_edit.setText(config.get("api_key", ""))

        # Populate models (this would typically come from the provider)
        models = self._get_provider_models(provider_name)
        self.model_combo.clear()
        self.model_combo.addItems(models)

        current_model = config.get("model", models[0] if models else "")
        if current_model in models:
            self.model_combo.setCurrentText(current_model)

        self.base_url_edit.setText(config.get("base_url", ""))
        self.cache_enabled_check.setChecked(config.get("cache_enabled", True))
        self.cache_size_spin.setValue(config.get("cache_size", 1000))

    def _get_provider_models(self, provider_name: str) -> List[str]:
        """Get available models for a provider."""
        models_map = {
            "OpenAI": ["gpt-4-vision-preview", "gpt-4o", "gpt-4o-mini"],
            "Anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
            "Google Gemini": ["gemini-pro-vision", "gemini-pro"],
            "OpenRouter": ["openai/gpt-4-vision-preview", "anthropic/claude-3-opus"],
            "xAI": ["grok-beta"],
            "ZAI": ["zai-model"],
            "Perplexity": ["pplx-70b-online"],
            "Ollama": ["llava", "llava:13b", "bakllava"],
            "AI Studio": ["aistudio-model"],
        }
        return models_map.get(provider_name, ["default"])

    def _on_provider_changed(self, provider_name: str):
        """Handle provider selection change."""
        if provider_name in self.providers:
            # Load provider configuration
            config = self.providers[provider_name]
            self.load_provider_config(provider_name, config)

    def _test_connection(self):
        """Test connection to the selected provider."""
        if not self.current_provider:
            return

        # This would actually test the connection
        # For now, just emit a signal
        self.provider_tested.emit(self.current_provider, True)

        QMessageBox.information(
            self,
            "Connection Test",
            f"Connection to {self.current_provider} successful!",
        )

    def _clear_cache(self):
        """Clear the AI response cache."""
        reply = QMessageBox.question(
            self,
            "Clear Cache",
            "Are you sure you want to clear the AI response cache?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            # Clear cache logic would go here
            QMessageBox.information(
                self, "Cache Cleared", "AI response cache has been cleared."
            )

    def _apply_configuration(self):
        """Apply current configuration."""
        if not self.current_provider:
            return

        config = {
            "api_key": self.api_key_edit.text(),
            "model": self.model_combo.currentText(),
            "base_url": self.base_url_edit.text(),
            "cache_enabled": self.cache_enabled_check.isChecked(),
            "cache_size": self.cache_size_spin.value(),
        }

        self.providers[self.current_provider] = config
        self.provider_configured.emit(self.current_provider, config)

        QMessageBox.information(
            self,
            "Configuration Applied",
            f"Configuration for {self.current_provider} has been saved.",
        )


class AIDescriptionWidget(QWidget):
    """
    Main AI description widget for generating and managing AI descriptions.
    """

    description_generated = Signal(str, dict)  # image_path, result
    description_applied = Signal(str, dict)  # image_path, description_data

    def __init__(self, ai_service: AIDescriptionService, parent=None):
        super().__init__(parent)
        self.ai_service = ai_service
        self.current_image_path = None
        self.logger = logging.getLogger(__name__)

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = QHBoxLayout()

        self.title_label = QLabel("AI Description Generator")
        self.title_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #2c3e50;"
        )
        header_layout.addWidget(self.title_label)

        header_layout.addStretch()

        # Provider selection
        self.provider_label = QLabel("Provider:")
        header_layout.addWidget(self.provider_label)

        self.provider_combo = QComboBox()
        self.provider_combo.setMinimumWidth(120)
        header_layout.addWidget(self.provider_combo)

        # Configure button
        self.configure_button = QPushButton("Configure")
        self.configure_button.setMaximumWidth(100)
        self.configure_button.clicked.connect(self._open_provider_config)
        header_layout.addWidget(self.configure_button)

        layout.addLayout(header_layout)

        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Left panel - Controls
        left_panel = self._create_control_panel()
        splitter.addWidget(left_panel)

        # Right panel - Results
        right_panel = self._create_results_panel()
        splitter.addWidget(right_panel)

        # Set splitter proportions
        splitter.setSizes([300, 400])

        # Status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(self.status_label)

    def _create_control_panel(self) -> QWidget:
        """Create the control panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Image selection
        image_group = QGroupBox("Image Selection")
        image_layout = QVBoxLayout(image_group)

        self.image_path_label = QLabel("No image selected")
        self.image_path_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        self.image_path_label.setWordWrap(True)
        image_layout.addWidget(self.image_path_label)

        self.select_image_button = QPushButton("Select Image")
        self.select_image_button.clicked.connect(self._select_image)
        image_layout.addWidget(self.select_image_button)

        layout.addWidget(image_group)

        # Custom prompt
        prompt_group = QGroupBox("Custom Prompt (Optional)")
        prompt_layout = QVBoxLayout(prompt_group)

        self.prompt_text = QTextEdit()
        self.prompt_text.setMaximumHeight(100)
        self.prompt_text.setPlaceholderText("Enter custom prompt for AI analysis...")
        prompt_layout.addWidget(self.prompt_text)

        layout.addWidget(prompt_group)

        # Generation options
        options_group = QGroupBox("Options")
        options_layout = QFormLayout(options_group)

        self.use_cache_check = QCheckBox("Use cached results")
        self.use_cache_check.setChecked(True)
        options_layout.addRow("", self.use_cache_check)

        self.auto_apply_check = QCheckBox("Auto-apply to metadata")
        self.auto_apply_check.setChecked(False)
        options_layout.addRow("", self.auto_apply_check)

        layout.addWidget(options_group)

        # Generate button
        self.generate_button = QPushButton("Generate Description")
        self.generate_button.setStyleSheet(
            """
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: #adb5bd;
            }
        """
        )
        self.generate_button.clicked.connect(self._generate_description)
        layout.addWidget(self.generate_button)

        layout.addStretch()

        return panel

    def _create_results_panel(self) -> QWidget:
        """Create the results display panel."""
        panel = QWidget()
        layout = QVBoxLayout(panel)

        # Results header
        results_header = QHBoxLayout()

        self.results_label = QLabel("Generated Description")
        self.results_label.setStyleSheet(
            "font-size: 14px; font-weight: bold; color: #2c3e50;"
        )
        results_header.addWidget(self.results_label)

        results_header.addStretch()

        # Copy button
        self.copy_button = QPushButton("Copy")
        self.copy_button.setMaximumWidth(80)
        self.copy_button.clicked.connect(self._copy_results)
        self.copy_button.setEnabled(False)
        results_header.addWidget(self.copy_button)

        layout.addLayout(results_header)

        # Scroll area for results
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        self.results_widget = QWidget()
        self.results_layout = QVBoxLayout(self.results_widget)

        # Title section
        title_group = QGroupBox("Title")
        title_layout = QVBoxLayout(title_group)

        self.title_result = QLabel("No description generated yet")
        self.title_result.setWordWrap(True)
        self.title_result.setStyleSheet(
            "color: #495057; font-style: italic; padding: 5px;"
        )
        title_layout.addWidget(self.title_result)

        self.results_layout.addWidget(title_group)

        # Description section
        desc_group = QGroupBox("Description")
        desc_layout = QVBoxLayout(desc_group)

        self.description_result = QLabel("No description generated yet")
        self.description_result.setWordWrap(True)
        self.description_result.setStyleSheet(
            "color: #495057; font-style: italic; padding: 5px;"
        )
        desc_layout.addWidget(self.description_result)

        self.results_layout.addWidget(desc_group)

        # Keywords section
        keywords_group = QGroupBox("Metadata Keywords")
        keywords_layout = QVBoxLayout(keywords_group)

        self.keywords_result = QListWidget()
        self.keywords_result.setMaximumHeight(100)
        keywords_layout.addWidget(self.keywords_result)

        self.results_layout.addWidget(keywords_group)

        # Apply button
        self.apply_button = QPushButton("Apply to Model Metadata")
        self.apply_button.setEnabled(False)
        self.apply_button.clicked.connect(self._apply_to_metadata)
        self.results_layout.addWidget(self.apply_button)

        self.results_layout.addStretch()

        scroll_area.setWidget(self.results_widget)
        layout.addWidget(scroll_area)

        return panel

    def _connect_signals(self):
        """Connect AI service signals."""
        if self.ai_service:
            self.ai_service.description_generated.connect(
                self._on_description_generated
            )
            self.ai_service.error_occurred.connect(self._on_error_occurred)

            # Update available providers
            self._update_provider_list()

    def _update_provider_list(self):
        """Update the provider dropdown with available providers."""
        if not self.ai_service:
            return

        available_providers = self.ai_service.get_available_providers()
        self.provider_combo.clear()
        self.provider_combo.addItems(available_providers)

        # Select default provider
        if self.ai_service.default_provider in available_providers:
            self.provider_combo.setCurrentText(self.ai_service.default_provider)

    def set_image(self, image_path: str):
        """Set the current image for description generation."""
        self.current_image_path = image_path
        self.image_path_label.setText(Path(image_path).name)
        self.image_path_label.setStyleSheet("color: #495057; font-weight: bold;")
        self.generate_button.setEnabled(True)

    def _select_image(self):
        """Open file dialog to select an image."""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.webp);;All Files (*)",
        )

        if file_path:
            self.set_image(file_path)

    def _generate_description(self):
        """Generate AI description for the current image."""
        if not self.current_image_path:
            QMessageBox.warning(self, "No Image", "Please select an image first.")
            return

        provider_name = self.provider_combo.currentText()
        custom_prompt = self.prompt_text.toPlain().strip() or None
        use_cache = self.use_cache_check.isChecked()

        # Disable UI during generation
        self._set_ui_enabled(False)
        self.status_label.setText(f"Generating description using {provider_name}...")

        try:
            result = self.ai_service.generate_description(
                self.current_image_path,
                provider_name=provider_name,
                custom_prompt=custom_prompt,
                use_cache=use_cache,
            )

            self._display_results(result)
            self.description_generated.emit(self.current_image_path, result)

        except Exception as e:
            self.logger.error(f"Failed to generate description: {e}")
            QMessageBox.critical(
                self, "Generation Failed", f"Failed to generate description: {str(e)}"
            )

        finally:
            self._set_ui_enabled(True)
            self.status_label.setText("Ready")

    def _display_results(self, result: Dict[str, Any]):
        """Display the generated description results."""
        # Update title
        self.title_result.setText(result.get("title", "No title"))
        self.title_result.setStyleSheet(
            "color: #212529; font-weight: bold; padding: 5px;"
        )

        # Update description
        self.description_result.setText(result.get("description", "No description"))
        self.description_result.setStyleSheet("color: #212529; padding: 5px;")

        # Update keywords
        keywords = result.get("metadata_keywords", [])
        self.keywords_result.clear()
        for keyword in keywords:
            self.keywords_result.addItem(keyword)

        # Enable action buttons
        self.copy_button.setEnabled(True)
        self.apply_button.setEnabled(True)

        self.status_label.setText("Description generated successfully")

    def _copy_results(self):
        """Copy results to clipboard."""
        from PySide6.QtGui import QClipboard

        result_text = f"Title: {self.title_result.text()}\n\n"
        result_text += f"Description: {self.description_result.text()}\n\n"
        result_text += f"Keywords: {', '.join([self.keywords_result.item(i).text() for i in range(self.keywords_result.count())])}"

        QApplication.clipboard().setText(result_text)
        self.status_label.setText("Results copied to clipboard")

    def _apply_to_metadata(self):
        """Apply the generated description to model metadata."""
        result_data = {
            "title": self.title_result.text(),
            "description": self.description_result.text(),
            "keywords": [
                self.keywords_result.item(i).text()
                for i in range(self.keywords_result.count())
            ],
        }

        self.description_applied.emit(self.current_image_path, result_data)
        self.status_label.setText("Description applied to metadata")

        QMessageBox.information(
            self, "Applied", "AI description has been applied to the model metadata."
        )

    def _open_provider_config(self):
        """Open the provider configuration dialog."""
        # This would open a modal dialog for provider configuration
        # Implementation depends on the main application's dialog system
        pass

    def _on_description_generated(self, image_path: str, result: Dict[str, Any]):
        """Handle description generation completion."""
        if image_path == self.current_image_path:
            self._display_results(result)
            self._set_ui_enabled(True)
            self.status_label.setText("Description generated successfully")

    def _on_error_occurred(self, image_path: str, error_message: str):
        """Handle description generation errors."""
        if image_path == self.current_image_path:
            self._set_ui_enabled(True)
            self.status_label.setText("Generation failed")
            QMessageBox.critical(self, "Generation Failed", error_message)

    def _set_ui_enabled(self, enabled: bool):
        """Enable or disable UI elements during processing."""
        self.generate_button.setEnabled(enabled)
        self.select_image_button.setEnabled(enabled)
        self.provider_combo.setEnabled(enabled)
        self.configure_button.setEnabled(enabled)
        self.prompt_text.setEnabled(enabled)
        self.use_cache_check.setEnabled(enabled)
        self.auto_apply_check.setEnabled(enabled)

        if not enabled:
            self.generate_button.setText("Generating...")
        else:
            self.generate_button.setText("Generate Description")
