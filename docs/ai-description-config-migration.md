# AI Description Service Configuration Migration Strategy

## Overview

This document outlines the strategy for migrating and integrating AI description service configuration with the existing application configuration system.

## Current Configuration Structure

### Existing Application Configuration
The main application likely uses a configuration system in `src/gui/preferences.py` or similar. We need to extend this to support AI description settings.

### AutoGenDesc-AI Configuration Structure
```json
{
  "OpenAI": {
    "api_key": "your-openai-api-key-here",
    "model": "gpt-4-vision-preview",
    "base_url": "https://api.openai.com/v1"
  },
  "Anthropic": {
    "api_key": "your-anthropic-api-key-here",
    "model": "claude-3-opus-20240229",
    "base_url": "https://api.anthropic.com"
  }
}
```

## Migration Strategy

### Phase 1: Configuration Schema Design

#### Extended Configuration Schema
```json
{
  "ai_description": {
    "enabled": true,
    "default_provider": "openai",
    "auto_generate_on_import": false,
    "cache_results": true,
    "cache_size_limit": 1000,
    "rate_limit_delay": 1.0,
    "providers": {
      "openai": {
        "api_key": "${OPENAI_API_KEY}",
        "model": "gpt-4-vision-preview",
        "base_url": "https://api.openai.com/v1",
        "enabled": true
      },
      "anthropic": {
        "api_key": "${ANTHROPIC_API_KEY}",
        "model": "claude-3-opus-20240229",
        "base_url": "https://api.anthropic.com",
        "enabled": false
      },
      "google_gemini": {
        "api_key": "${GOOGLE_API_KEY}",
        "model": "gemini-pro-vision",
        "enabled": false
      },
      "openrouter": {
        "api_key": "${OPENROUTER_API_KEY}",
        "model": "openai/gpt-4-vision-preview",
        "base_url": "https://openrouter.io/api/v1",
        "enabled": false
      },
      "xai": {
        "api_key": "${XAI_API_KEY}",
        "model": "grok-beta",
        "base_url": "https://api.x.ai/v1",
        "enabled": false
      },
      "zai": {
        "api_key": "${ZAI_API_KEY}",
        "model": "zai-model",
        "base_url": "https://api.z.ai/v1",
        "enabled": false
      },
      "perplexity": {
        "api_key": "${PERPLEXITY_API_KEY}",
        "model": "pplx-70b-online",
        "base_url": "https://api.perplexity.ai",
        "enabled": false
      },
      "ollama": {
        "base_url": "http://localhost:11434",
        "model": "llava",
        "enabled": false
      },
      "aistudio": {
        "api_key": "${AISTUDIO_API_KEY}",
        "model": "aistudio-model",
        "base_url": "https://api.aistudio.ai/v1",
        "enabled": false
      }
    },
    "custom_prompts": {
      "default": "Analyze this image and provide a detailed description including objects, colors, textures, and overall composition.",
      "mechanical": "Analyze this mechanical part or technical drawing. Describe its function, materials, and manufacturing considerations.",
      "artistic": "Analyze this artistic work. Describe the style, techniques, colors, composition, and artistic intent.",
      "architectural": "Analyze this architectural image. Describe the building style, materials, design elements, and spatial relationships."
    },
    "ui_settings": {
      "show_progress_dialog": true,
      "auto_close_progress": true,
      "enable_batch_processing": true,
      "max_batch_size": 10
    }
  }
}
```

### Phase 2: Configuration Migration Implementation

#### 1. Configuration Manager Extension
```python
# src/gui/preferences.py (extend existing class)
class PreferencesManager:
    def get_ai_description_config(self) -> Dict[str, Any]:
        """Get AI description service configuration."""
        return self.config.get("ai_description", self._get_default_ai_config())
    
    def set_ai_description_config(self, config: Dict[str, Any]):
        """Set AI description service configuration."""
        self.config["ai_description"] = config
        self.save_config()
    
    def _get_default_ai_config(self) -> Dict[str, Any]:
        """Get default AI description configuration."""
        return {
            "enabled": True,
            "default_provider": "openai",
            "auto_generate_on_import": False,
            "cache_results": True,
            "cache_size_limit": 1000,
            "rate_limit_delay": 1.0,
            "providers": {},
            "custom_prompts": {},
            "ui_settings": {
                "show_progress_dialog": True,
                "auto_close_progress": True,
                "enable_batch_processing": True,
                "max_batch_size": 10
            }
        }
```

#### 2. Environment Variable Integration
```python
# src/gui/config/environment_config.py
import os
from typing import Dict, Any

class EnvironmentConfig:
    """Handle environment variable substitution in configuration."""
    
    @staticmethod
    def substitute_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively substitute environment variables in config."""
        if isinstance(config, dict):
            return {k: EnvironmentConfig.substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, str):
            return EnvironmentConfig._substitute_env_var(config)
        else:
            return config
    
    @staticmethod
    def _substitute_env_var(value: str) -> str:
        """Substitute environment variable in string."""
        if value.startswith("${") and value.endswith("}"):
            env_var = value[2:-1]
            return os.getenv(env_var, value)
        return value
```

### Phase 3: Migration Script

#### Configuration Migration Script
```python
# scripts/migrate_ai_config.py
#!/usr/bin/env python3
"""
Migration script for AI description service configuration.
"""

import json
import os
from pathlib import Path

def migrate_existing_config():
    """Migrate existing AutoGenDesc-AI config to new format."""
    
    # Load existing AutoGenDesc-AI config
    old_config_path = Path("AutoGenDESC-AI/config.json")
    if not old_config_path.exists():
        print("No existing AutoGenDesc-AI config found. Creating new config.")
        return create_new_config()
    
    with open(old_config_path, 'r') as f:
        old_config = json.load(f)
    
    # Convert to new format
    new_config = convert_to_new_format(old_config)
    
    # Save to new location
    new_config_path = Path("config/ai_description.json")
    new_config_path.parent.mkdir(exist_ok=True)
    
    with open(new_config_path, 'w') as f:
        json.dump(new_config, f, indent=2)
    
    print(f"Migrated configuration to {new_config_path}")
    return new_config

def convert_to_new_format(old_config: Dict[str, Any]) -> Dict[str, Any]:
    """Convert old config format to new format."""
    
    new_config = {
        "ai_description": {
            "enabled": True,
            "default_provider": "openai",
            "auto_generate_on_import": False,
            "cache_results": True,
            "cache_size_limit": 1000,
            "rate_limit_delay": 1.0,
            "providers": {},
            "custom_prompts": {},
            "ui_settings": {
                "show_progress_dialog": True,
                "auto_close_progress": True,
                "enable_batch_processing": True,
                "max_batch_size": 10
            }
        }
    }
    
    # Migrate provider configurations
    for provider_name, provider_config in old_config.items():
        if isinstance(provider_config, dict):
            new_provider_name = provider_name.lower().replace(" ", "_")
            new_config["ai_description"]["providers"][new_provider_name] = {
                "api_key": provider_config.get("api_key"),
                "model": provider_config.get("model", ""),
                "base_url": provider_config.get("base_url"),
                "enabled": bool(provider_config.get("api_key"))
            }
    
    return new_config

def create_new_config() -> Dict[str, Any]:
    """Create new default configuration."""
    return {
        "ai_description": {
            "enabled": True,
            "default_provider": "openai",
            "auto_generate_on_import": False,
            "cache_results": True,
            "cache_size_limit": 1000,
            "rate_limit_delay": 1.0,
            "providers": {},
            "custom_prompts": {
                "default": "Analyze this image and provide a detailed description including objects, colors, textures, and overall composition."
            },
            "ui_settings": {
                "show_progress_dialog": True,
                "auto_close_progress": True,
                "enable_batch_processing": True,
                "max_batch_size": 10
            }
        }
    }

if __name__ == "__main__":
    migrate_existing_config()
```

### Phase 4: Security Considerations

#### API Key Security
1. **Environment Variables**: Prefer environment variables for API keys
2. **Encryption**: Implement configuration encryption for stored API keys
3. **Access Control**: Limit API key access to authorized components
4. **Audit Logging**: Log all configuration changes

#### Implementation
```python
# src/gui/config/secure_config.py
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os

class SecureConfig:
    """Handle secure storage of sensitive configuration data."""
    
    def __init__(self, master_password: str = None):
        self.master_password = master_password or os.getenv("APP_MASTER_PASSWORD", "")
        self.key = self._derive_key()
        self.cipher = Fernet(self.key)
    
    def _derive_key(self) -> bytes:
        """Derive encryption key from master password."""
        password = self.master_password.encode()
        salt = b'stable_salt_for_ai_config'  # In production, use random salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password))
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive configuration data."""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive configuration data."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()
```

### Phase 5: Configuration Validation

#### Configuration Validator
```python
# src/gui/config/config_validator.py
from typing import Dict, Any, List
import re

class AIConfigValidator:
    """Validate AI description service configuration."""
    
    VALID_PROVIDERS = [
        "openai", "anthropic", "google_gemini", "openrouter",
        "xai", "zai", "perplexity", "ollama", "aistudio"
    ]
    
    VALID_MODELS = {
        "openai": ["gpt-4-vision-preview", "gpt-4o", "gpt-4o-mini"],
        "anthropic": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
        "google_gemini": ["gemini-pro-vision", "gemini-pro"],
        # Add more valid models for each provider
    }
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate main config
        if "ai_description" not in config:
            errors.append("Missing 'ai_description' section")
            return errors
        
        ai_config = config["ai_description"]
        
        # Validate providers
        providers = ai_config.get("providers", {})
        for provider_name, provider_config in providers.items():
            if provider_name not in self.VALID_PROVIDERS:
                errors.append(f"Invalid provider: {provider_name}")
            
            # Validate API key format (basic check)
            api_key = provider_config.get("api_key", "")
            if api_key and not self._is_valid_api_key(api_key, provider_name):
                errors.append(f"Invalid API key format for {provider_name}")
            
            # Validate model
            model = provider_config.get("model", "")
            if model and not self._is_valid_model(model, provider_name):
                errors.append(f"Invalid model '{model}' for {provider_name}")
        
        return errors
    
    def _is_valid_api_key(self, api_key: str, provider: str) -> bool:
        """Basic API key validation."""
        if not api_key:
            return True  # Empty is OK (provider disabled)
        
        # Provider-specific validation
        if provider == "openai":
            return re.match(r'^sk-[a-zA-Z0-9]{48}$', api_key) is not None
        elif provider == "anthropic":
            return re.match(r'^sk-ant-[a-zA-Z0-9\-_]{95}$', api_key) is not None
        # Add more provider-specific validation
        
        return True  # Default to valid for unknown providers
    
    def _is_valid_model(self, model: str, provider: str) -> bool:
        """Validate model name for provider."""
        valid_models = self.VALID_MODELS.get(provider, [])
        return model in valid_models if valid_models else True
```

## Migration Steps

### Step 1: Backup Existing Configuration
```bash
# Backup existing configuration
cp config.json config.json.backup
cp AutoGenDESC-AI/config.json AutoGenDESC-AI/config.json.backup
```

### Step 2: Run Migration Script
```bash
python scripts/migrate_ai_config.py
```

### Step 3: Validate New Configuration
```python
from src.gui.config.config_validator import AIConfigValidator

validator = AIConfigValidator()
with open("config/ai_description.json", "r") as f:
    config = json.load(f)

errors = validator.validate_config(config)
if errors:
    print("Configuration errors:")
    for error in errors:
        print(f"  - {error}")
else:
    print("Configuration is valid!")
```

### Step 4: Update Application Code
- Update configuration loading in main application
- Integrate with existing preferences system
- Update UI components to use new configuration

### Step 5: Test Configuration
- Test configuration loading and saving
- Verify API key encryption/decryption
- Test environment variable substitution
- Validate all provider configurations

## Rollback Plan

If issues arise during migration:

1. **Restore Backup**: Use backed up configuration files
2. **Disable AI Features**: Set `ai_description.enabled = false`
3. **Manual Configuration**: Users can manually configure through UI
4. **Environment Variables**: Fallback to environment variable configuration

## Success Criteria

- [ ] Configuration migration completes without errors
- [ ] All existing provider configurations are preserved
- [ ] New configuration schema is validated
- [ ] Environment variable substitution works
- [ ] API key encryption/decryption functions correctly
- [ ] Application starts successfully with new configuration
- [ ] All AI features work as expected with new configuration