"""
Main Window GUI
The main application window for the Vision AI Analysis Tool.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QComboBox, QTextEdit, QFileDialog,
    QMessageBox, QScrollArea, QFrame, QSplitter, QProgressBar,
    QGroupBox, QLineEdit
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import QPixmap, QFont

from providers import (
    OpenAIProvider, OpenRouterProvider, AnthropicProvider, GeminiProvider,
    XAIProvider, ZAIProvider, PerplexityProvider,
    OllamaProvider, AIStudioProvider
)
from .config_dialog import ConfigDialog

class AnalysisThread(QThread):
    """Worker thread for image analysis to keep GUI responsive."""
    
    finished = Signal(dict)
    error = Signal(str)
    
    def __init__(self, provider, image_path: str, prompt: Optional[str] = None):
        super().__init__()
        self.provider = provider
        self.image_path = image_path
        self.prompt = prompt
    
    def run(self):
        """Run the analysis in a separate thread."""
        try:
            result = self.provider.analyze_image(self.image_path, self.prompt)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.providers = {}
        self.current_provider = None
        self.current_image_path = None
        self.analysis_thread = None
        
        self.setup_logging()
        self.load_providers()
        self.setup_ui()
        self.setup_connections()
        
        # Set window properties
        self.setWindowTitle("Vision AI Analysis Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        # Load configuration if available
        self.load_config()
    
    def setup_logging(self):
        """Setup logging for the application."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def load_providers(self):
        """Initialize all available providers."""
        self.providers = {
            "OpenAI": OpenAIProvider(),
            "Anthropic": AnthropicProvider(),
            "Google Gemini": GeminiProvider(),
            "xAI": XAIProvider(),
            "ZAI": ZAIProvider(),
            "Perplexity": PerplexityProvider(),
            "Ollama": OllamaProvider(),
            "AI Studio": AIStudioProvider()
        }
    
    def setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("Vision AI Analysis Tool")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Left panel - Controls
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - Results
        right_panel = self.create_results_panel()
        splitter.addWidget(right_panel)
        
        # Set initial splitter sizes
        splitter.setSizes([400, 800])
        
        # Status bar
        self.statusBar().showMessage("Ready")
        
        # Progress bar (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.statusBar().addPermanentWidget(self.progress_bar)
    
    def create_control_panel(self) -> QWidget:
        """Create the control panel with image selection and provider options."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Provider selection
        provider_group = QGroupBox("AI Provider")
        provider_layout = QVBoxLayout(provider_group)
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(list(self.providers.keys()))
        provider_layout.addWidget(self.provider_combo)
        
        # Configure provider button
        self.config_button = QPushButton("Configure Provider")
        provider_layout.addWidget(self.config_button)
        
        layout.addWidget(provider_group)
        
        # Image selection
        image_group = QGroupBox("Image Selection")
        image_layout = QVBoxLayout(image_group)
        
        self.image_path_label = QLabel("No image selected")
        self.image_path_label.setWordWrap(True)
        image_layout.addWidget(self.image_path_label)
        
        self.select_image_button = QPushButton("Select Image")
        image_layout.addWidget(self.select_image_button)
        
        # Image preview
        self.image_preview_label = QLabel()
        self.image_preview_label.setAlignment(Qt.AlignCenter)
        self.image_preview_label.setMinimumSize(300, 200)
        self.image_preview_label.setStyleSheet("border: 2px dashed #ccc;")
        self.image_preview_label.setText("Image Preview")
        image_layout.addWidget(self.image_preview_label)
        
        layout.addWidget(image_group)
        
        # Custom prompt
        prompt_group = QGroupBox("Custom Prompt (Optional)")
        prompt_layout = QVBoxLayout(prompt_group)
        
        self.prompt_text = QTextEdit()
        self.prompt_text.setPlaceholderText("Enter custom prompt for image analysis...")
        self.prompt_text.setMaximumHeight(100)
        prompt_layout.addWidget(self.prompt_text)
        
        layout.addWidget(prompt_group)
        
        # Analyze button
        self.analyze_button = QPushButton("Analyze Image")
        self.analyze_button.setEnabled(False)
        layout.addWidget(self.analyze_button)
        
        # Add stretch to push everything to the top
        layout.addStretch()
        
        return panel
    
    def create_results_panel(self) -> QWidget:
        """Create the results panel for displaying analysis output."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Results group
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)
        
        # Title
        self.title_label = QLabel("Title: ")
        self.title_label.setWordWrap(True)
        title_font = QFont()
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        results_layout.addWidget(self.title_label)
        
        # Description
        self.description_label = QLabel("Description: ")
        self.description_label.setWordWrap(True)
        results_layout.addWidget(self.description_label)
        
        # Keywords
        self.keywords_label = QLabel("Keywords: ")
        self.keywords_label.setWordWrap(True)
        results_layout.addWidget(self.keywords_label)
        
        # Raw JSON output
        json_group = QGroupBox("Raw JSON Output")
        json_layout = QVBoxLayout(json_group)
        
        self.json_output = QTextEdit()
        self.json_output.setReadOnly(True)
        self.json_output.setMaximumHeight(200)
        json_layout.addWidget(self.json_output)
        
        layout.addWidget(results_group)
        layout.addWidget(json_group)
        
        return panel
    
    def setup_connections(self):
        """Setup signal connections."""
        self.provider_combo.currentTextChanged.connect(self.on_provider_changed)
        self.config_button.clicked.connect(self.show_config_dialog)
        self.select_image_button.clicked.connect(self.select_image)
        self.analyze_button.clicked.connect(self.analyze_image)
    
    def on_provider_changed(self, provider_name: str):
        """Handle provider selection change."""
        self.current_provider = self.providers.get(provider_name)
        self.update_analyze_button_state()
    
    def show_config_dialog(self):
        """Show configuration dialog for the current provider."""
        if not self.current_provider:
            QMessageBox.warning(self, "Warning", "Please select a provider first.")
            return
        
        dialog = ConfigDialog(self.current_provider, self)
        if dialog.exec() == ConfigDialog.Accepted:
            self.save_config()
    
    def select_image(self):
        """Open file dialog to select an image."""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Select Image",
            "",
            "Image Files (*.png *.jpg *.jpeg *.gif *.webp)"
        )
        
        if file_path:
            self.current_image_path = file_path
            self.image_path_label.setText(f"Selected: {os.path.basename(file_path)}")
            
            # Load preview
            pixmap = QPixmap(file_path)
            if not pixmap.isNull():
                # Scale image to fit preview area
                scaled_pixmap = pixmap.scaled(
                    300, 200,
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation
                )
                self.image_preview_label.setPixmap(scaled_pixmap)
            else:
                self.image_preview_label.setText("Failed to load image")
            
            self.update_analyze_button_state()
    
    def update_analyze_button_state(self):
        """Update the enabled state of the analyze button."""
        enabled = (
            self.current_provider is not None and
            self.current_provider.is_configured() and
            self.current_image_path is not None and
            os.path.exists(self.current_image_path)
        )
        self.analyze_button.setEnabled(enabled)
    
    def analyze_image(self):
        """Start image analysis in a separate thread."""
        if not self.current_provider or not self.current_image_path:
            return
        
        # Get custom prompt if provided
        custom_prompt = self.prompt_text.toPlainText().strip()
        prompt = custom_prompt if custom_prompt else None
        
        # Create and start analysis thread
        self.analysis_thread = AnalysisThread(
            self.current_provider,
            self.current_image_path,
            prompt
        )
        self.analysis_thread.finished.connect(self.on_analysis_finished)
        self.analysis_thread.error.connect(self.on_analysis_error)
        
        # Update UI for analysis
        self.analyze_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.statusBar().showMessage("Analyzing image...")
        
        # Clear previous results
        self.clear_results()
        
        self.analysis_thread.start()
    
    def on_analysis_finished(self, result: Dict[str, Any]):
        """Handle successful analysis completion."""
        self.progress_bar.setVisible(False)
        self.analyze_button.setEnabled(True)
        self.statusBar().showMessage("Analysis complete")
        
        # Display results
        self.display_results(result)
    
    def on_analysis_error(self, error_message: str):
        """Handle analysis error."""
        self.progress_bar.setVisible(False)
        self.analyze_button.setEnabled(True)
        self.statusBar().showMessage("Analysis failed")
        
        QMessageBox.critical(
            self,
            "Analysis Error",
            f"Failed to analyze image:\n{error_message}"
        )
    
    def clear_results(self):
        """Clear previous analysis results."""
        self.title_label.setText("Title: ")
        self.description_label.setText("Description: ")
        self.keywords_label.setText("Keywords: ")
        self.json_output.clear()
    
    def display_results(self, result: Dict[str, Any]):
        """Display analysis results in the UI."""
        # Title
        title = result.get('title', 'No title generated')
        self.title_label.setText(f"Title: {title}")
        
        # Description
        description = result.get('description', 'No description generated')
        self.description_label.setText(f"Description: {description}")
        
        # Keywords
        keywords = result.get('metadata_keywords', [])
        if keywords:
            keywords_text = ', '.join(keywords) if isinstance(keywords, list) else str(keywords)
            self.keywords_label.setText(f"Keywords: {keywords_text}")
        else:
            self.keywords_label.setText("Keywords: No keywords generated")
        
        # Raw JSON
        json_str = json.dumps(result, indent=2)
        self.json_output.setPlainText(json_str)
    
    def load_config(self):
        """Load configuration from file."""
        config_path = "config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info("Loaded configuration file: %s", config_path)
                
                # Configure providers with saved API keys
                for provider_name, provider_config in config.items():
                    if provider_name in self.providers:
                        self.logger.info("Loading configuration for provider: %s", provider_name)
                        provider = self.providers[provider_name]
                        if 'api_key' in provider_config:
                            # Reinitialize provider with API key
                            if provider_name == "OpenAI":
                                self.providers[provider_name] = OpenAIProvider(
                                    api_key=provider_config['api_key'],
                                    model=provider_config.get('model', 'gpt-4-vision-preview'),
                                    base_url=provider_config.get('base_url')
                                )
                            elif provider_name == "OpenRouter":
                                self.providers[provider_name] = OpenRouterProvider(
                                    api_key=provider_config['api_key'],
                                    model=provider_config.get('model', 'gpt-4-vision-preview'),
                                    base_url=provider_config.get('base_url', 'https://openrouter.io/api/v1')
                                )
                            elif provider_name == "Anthropic":
                                self.providers[provider_name] = AnthropicProvider(
                                    api_key=provider_config['api_key'],
                                    model=provider_config.get('model', 'claude-3-opus-20240229'),
                                    base_url=provider_config.get('base_url')
                                )
                            elif provider_name == "Google Gemini":
                                self.providers[provider_name] = GeminiProvider(
                                    api_key=provider_config['api_key'],
                                    model=provider_config.get('model', 'gemini-pro-vision')
                                )
                            elif provider_name == "xAI":
                                self.providers[provider_name] = XAIProvider(
                                    api_key=provider_config['api_key'],
                                    model=provider_config.get('model', 'grok-vision-beta'),
                                    base_url=provider_config.get('base_url')
                                )
                            elif provider_name == "ZAI":
                                self.providers[provider_name] = ZAIProvider(
                                    api_key=provider_config['api_key'],
                                    model=provider_config.get('model', 'zai-vision-1'),
                                    base_url=provider_config.get('base_url')
                                )
                            elif provider_name == "Perplexity":
                                self.providers[provider_name] = PerplexityProvider(
                                    api_key=provider_config['api_key'],
                                    model=provider_config.get('model', 'llama-3.2-90b-vision'),
                                    base_url=provider_config.get('base_url')
                                )
                            elif provider_name == "Ollama":
                                self.providers[provider_name] = OllamaProvider(
                                    base_url=provider_config.get('base_url', 'http://localhost:11434'),
                                    model=provider_config.get('model', 'llava')
                                )
                            elif provider_name == "AI Studio":
                                self.providers[provider_name] = AIStudioProvider(
                                    api_key=provider_config['api_key'],
                                    model=provider_config.get('model', 'aistudio-vision-1'),
                                    base_url=provider_config.get('base_url')
                                )
                
                # Update current provider reference
                current_name = self.provider_combo.currentText()
                self.current_provider = self.providers.get(current_name)
                
                self.logger.info("Configuration loaded successfully")
                
            except Exception as e:
                self.logger.error("Failed to load configuration: %s", str(e))
    
    def save_config(self):
        """Save current configuration to file."""
        config = {}
        
        for provider_name, provider in self.providers.items():
            provider_config = {}
            
            if hasattr(provider, 'api_key') and provider.api_key:
                provider_config['api_key'] = provider.api_key
            
            if hasattr(provider, 'model'):
                provider_config['model'] = provider.model
            
            if hasattr(provider, 'base_url'):
                provider_config['base_url'] = provider.base_url
            
            if provider_config:
                config[provider_name] = provider_config
        
        try:
            with open('config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            self.logger.info("Configuration saved successfully")
        except Exception as e:
            self.logger.error("Failed to save configuration: %s", str(e))
    
    def closeEvent(self, event):
        """Handle application close event."""
        # Save configuration before closing
        self.save_config()
        
        # Wait for any running analysis thread
        if self.analysis_thread and self.analysis_thread.isRunning():
            self.analysis_thread.quit()
            self.analysis_thread.wait()
        
        event.accept()