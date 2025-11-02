"""
Configuration Dialog
Dialog for configuring AI provider settings.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFormLayout, QGroupBox, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, QThread, Signal

try:
    import google.generativeai as genai
except ImportError:
    genai = None

class ConfigDialog(QDialog):
    """Dialog for configuring AI provider settings."""
    
    def __init__(self, provider, parent=None):
        super().__init__(parent)
        self.provider = provider
        self.model_fetch_thread = None
        self.setup_ui()
        self.load_current_config()
    
    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle(f"Configure {self.provider.__class__.__name__}")
        self.setModal(True)
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # Configuration form
        form_layout = QFormLayout()
        
        # API Key (most providers have this)
        if hasattr(self.provider, 'api_key'):
            self.api_key_edit = QLineEdit()
            self.api_key_edit.setEchoMode(QLineEdit.Password)
            self.api_key_edit.setPlaceholderText("Enter API key...")
            form_layout.addRow("API Key:", self.api_key_edit)
        
        # Model (if available)
        if hasattr(self.provider, 'model'):
            model_layout = QHBoxLayout()
            
            self.model_combo = QComboBox()
            self.model_combo.setEditable(True)
            self.model_combo.setPlaceholderText("Select or enter model name...")
            model_layout.addWidget(self.model_combo)
            
            self.get_models_button = QPushButton("Get Models")
            self.get_models_button.clicked.connect(self.fetch_available_models)
            model_layout.addWidget(self.get_models_button)
            
            form_layout.addRow("Model:", model_layout)
        
        # Base URL (for providers like Ollama)
        if hasattr(self.provider, 'base_url'):
            self.base_url_edit = QLineEdit()
            self.base_url_edit.setPlaceholderText("Enter base URL...")
            form_layout.addRow("Base URL:", self.base_url_edit)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.test_button = QPushButton("Test Connection")
        self.test_button.clicked.connect(self.test_connection)
        button_layout.addWidget(self.test_button)
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_config)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        # Connect signals for auto-fetching models
        if hasattr(self, 'api_key_edit'):
            self.api_key_edit.textChanged.connect(self.on_api_key_changed)
        
        if hasattr(self, 'base_url_edit'):
            self.base_url_edit.textChanged.connect(self.on_config_changed)
        
        # Initially disable the Get Models button until provider is configured
        if hasattr(self, 'get_models_button'):
            self.get_models_button.setEnabled(False)
    
    def load_current_config(self):
        """Load current provider configuration into the form."""
        if hasattr(self, 'api_key_edit') and hasattr(self.provider, 'api_key'):
            if self.provider.api_key:
                self.api_key_edit.setText(self.provider.api_key)

        if hasattr(self, 'model_combo'):
            # Handle both 'model' and 'model_name' attributes (for Gemini compatibility)
            model_name = None
            if hasattr(self.provider, 'model') and self.provider.model:
                model_name = self.provider.model
            elif hasattr(self.provider, 'model_name') and self.provider.model_name:
                model_name = self.provider.model_name

            if model_name:
                # Get model name string (handle both string and object cases)
                if hasattr(model_name, 'model_name'):
                    model_name = model_name.model_name
                elif hasattr(model_name, 'name'):
                    model_name = model_name.name
                elif not isinstance(model_name, str):
                    model_name = str(model_name)

                # Add current model to combo if not already there
                if self.model_combo.findText(model_name) == -1:
                    self.model_combo.addItem(model_name)
                self.model_combo.setCurrentText(model_name)

        if hasattr(self, 'base_url_edit') and hasattr(self.provider, 'base_url'):
            if self.provider.base_url:
                self.base_url_edit.setText(self.provider.base_url)

        # Try to fetch models if provider is already configured
        if self.provider.is_configured():
            self.fetch_available_models()
            if hasattr(self, 'get_models_button'):
                self.get_models_button.setEnabled(True)
    
    def on_api_key_changed(self, text):
        """Handle API key text change."""
        # Enable/disable Get Models button based on API key presence
        if hasattr(self, 'get_models_button'):
            self.get_models_button.setEnabled(len(text) >= 10)
        
        # Auto-fetch models when API key is entered (minimum length check)
        if len(text) >= 10:  # Most API keys are at least 10 characters
            self.save_temp_config()
            # Check if provider is configured after saving temp config
            if self.provider.is_configured():
                self.fetch_available_models()
            else:
                print("Provider not configured after saving temp config")
    
    def on_config_changed(self):
        """Handle configuration changes (like base URL)."""
        # Save temporary settings
        self.save_temp_config()
        # Enable Get Models button if provider is configured
        if hasattr(self, 'get_models_button'):
            self.get_models_button.setEnabled(self.provider.is_configured())
    
    def fetch_available_models(self):
        """Fetch available models from the provider."""
        if self.model_fetch_thread and self.model_fetch_thread.isRunning():
            print("Model fetch already in progress...")
            return
        
        print(f"Fetching models for provider: {self.provider.__class__.__name__}")
        print(f"Provider configured: {self.provider.is_configured()}")
        
        # Update button to show loading state
        if hasattr(self, 'get_models_button'):
            self.get_models_button.setText("Loading...")
            self.get_models_button.setEnabled(False)
        
        self.model_fetch_thread = ModelFetchThread(self.provider)
        self.model_fetch_thread.models_fetched.connect(self.on_models_fetched)
        self.model_fetch_thread.error.connect(self.on_model_fetch_error)
        self.model_fetch_thread.start()
    
    def on_models_fetched(self, models):
        """Handle successful model fetch."""
        print(f"Models fetched successfully: {models}")
        
        # Restore button state
        if hasattr(self, 'get_models_button'):
            self.get_models_button.setText("Get Models")
            self.get_models_button.setEnabled(True)
        
        if hasattr(self, 'model_combo'):
            # Save current selection
            current_text = self.model_combo.currentText()
            
            # Clear and repopulate combo box
            self.model_combo.clear()
            if models:
                print(f"Adding {len(models)} models to combo box")
                self.model_combo.addItems(models)
            else:
                print("No models to add")
            
            # Restore selection if it still exists
            if current_text and self.model_combo.findText(current_text) != -1:
                self.model_combo.setCurrentText(current_text)
            elif current_text:
                # Add the current text if it's not in the list
                self.model_combo.addItem(current_text)
                self.model_combo.setCurrentText(current_text)
    
    def on_model_fetch_error(self, error_message):
        """Handle model fetch error."""
        print(f"Model fetch error: {error_message}")
        
        # Restore button state
        if hasattr(self, 'get_models_button'):
            self.get_models_button.setText("Get Models")
            self.get_models_button.setEnabled(True)
        
        # Silently handle errors - models will be populated with defaults
        # Could show a status message here if needed
    
    def test_connection(self):
        """Test the provider connection with current settings."""
        # Save temporary settings
        self.save_temp_config()
        
        # Test connection
        try:
            if self.provider.is_configured():
                QMessageBox.information(
                    self,
                    "Connection Test",
                    "Connection successful! Provider is properly configured."
                )
            else:
                QMessageBox.warning(
                    self,
                    "Connection Test",
                    "Connection failed. Please check your configuration."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Connection Test",
                f"Connection test failed with error:\n{str(e)}"
            )
    
    def save_temp_config(self):
        """Save configuration temporarily for testing."""
        print("Saving temporary configuration...")

        if hasattr(self, 'api_key_edit') and hasattr(self.provider, 'api_key'):
            api_key = self.api_key_edit.text().strip()
            if api_key:
                print(f"Setting API key: {'*' * (len(api_key) - 4)}{api_key[-4:]}")
                self.provider.api_key = api_key
                # For Gemini, we need to configure the API key
                if self.provider.__class__.__name__ == 'GeminiProvider' and genai:
                    genai.configure(api_key=api_key)
                    print("Gemini API key configured")

        if hasattr(self, 'model_combo'):
            model = self.model_combo.currentText().strip()
            if model:
                print(f"Setting model: {model}")
                # Handle both 'model' and 'model_name' attributes (for Gemini compatibility)
                if hasattr(self.provider, 'model_name'):
                    self.provider.model_name = model
                if hasattr(self.provider, 'model'):
                    self.provider.model = model

        if hasattr(self, 'base_url_edit') and hasattr(self.provider, 'base_url'):
            base_url = self.base_url_edit.text().strip()
            if base_url:
                print(f"Setting base URL: {base_url}")
                self.provider.base_url = base_url

        print(f"Provider configured after temp save: {self.provider.is_configured()}")
    
    def save_config(self):
        """Save the configuration and close dialog."""
        if hasattr(self, 'api_key_edit') and hasattr(self.provider, 'api_key'):
            api_key = self.api_key_edit.text().strip()
            if not api_key:
                QMessageBox.warning(
                    self,
                    "Configuration Error",
                    "API key is required for this provider."
                )
                return
            self.provider.api_key = api_key

        if hasattr(self, 'model_combo'):
            model = self.model_combo.currentText().strip()
            if model:
                # Handle both 'model' and 'model_name' attributes (for Gemini compatibility)
                if hasattr(self.provider, 'model_name'):
                    self.provider.model_name = model
                if hasattr(self.provider, 'model'):
                    self.provider.model = model

        if hasattr(self, 'base_url_edit') and hasattr(self.provider, 'base_url'):
            base_url = self.base_url_edit.text().strip()
            if base_url:
                self.provider.base_url = base_url

        # Reinitialize provider client if needed
        self.reinitialize_provider()

        self.accept()
    
    def reinitialize_provider(self):
        """Reinitialize the provider with new settings."""
        provider_class = self.provider.__class__

        # Get current settings
        kwargs = {}
        # Handle both 'model' and 'model_name' attributes (for Gemini compatibility)
        if hasattr(self.provider, 'model') and self.provider.model:
            kwargs['model'] = self.provider.model
        elif hasattr(self.provider, 'model_name') and self.provider.model_name:
            kwargs['model'] = self.provider.model_name
        if hasattr(self.provider, 'base_url'):
            kwargs['base_url'] = self.provider.base_url

        # Create new provider instance
        if hasattr(self.provider, 'api_key'):
            new_provider = provider_class(api_key=self.provider.api_key, **kwargs)
        else:
            new_provider = provider_class(**kwargs)

        # Update the provider reference with the new instance
        self.provider.__dict__.update(new_provider.__dict__)

class ModelFetchThread(QThread):
    """Worker thread for fetching available models."""
    
    models_fetched = Signal(list)
    error = Signal(str)
    
    def __init__(self, provider):
        super().__init__()
        self.provider = provider
    
    def run(self):
        """Fetch models in a separate thread."""
        try:
            print(f"ModelFetchThread: Starting fetch for {self.provider.__class__.__name__}")
            print(f"ModelFetchThread: Provider is_configured: {self.provider.is_configured()}")
            
            models = self.provider.list_available_models()
            print(f"ModelFetchThread: Received models: {models}")
            
            self.models_fetched.emit(models)
        except Exception as e:
            print(f"ModelFetchThread: Error occurred: {str(e)}")
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))