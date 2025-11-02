#!/usr/bin/env python3
"""
Test script for AI Description Service integration.
Tests service initialization, configuration management, and basic functionality.
"""

import sys
import os
import tempfile
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_service_initialization(service):
    """Test that the service initializes correctly."""
    logger.info("=== Testing Service Initialization ===")
    logger.info("Service instance: %s", service)
    logger.info("Service type: %s", type(service))
    
    try:
        # Test service initialization
        assert service is not None, "Service should be initialized"
        logger.info("✓ Service initialized successfully")
        
        # Test expected attributes
        expected_attrs = ['providers', 'current_provider', 'config', 'logger']
        for attr in expected_attrs:
            assert hasattr(service, attr), f"Service should have {attr} attribute"
        logger.info("✓ Service has expected attributes")
        
        # Test configuration loading
        config = service._load_config()
        assert config is not None, "Configuration should be loaded"
        assert 'providers' in config, "Configuration should contain providers"
        assert 'custom_prompts' in config, "Configuration should contain custom_prompts"
        assert 'settings' in config, "Configuration should contain settings"
        logger.info("✓ Configuration loaded successfully")
        
        logger.info("=== Service Initialization PASSED ===")
        
    except Exception as e:
        logger.error("✗ Service initialization failed: %s", e)
        raise

def test_configuration_management(service):
    """Test configuration management functionality."""
    logger.info("=== Testing Configuration Management ===")
    
    try:
        # Test available providers
        available_providers = service.get_available_providers()
        assert isinstance(available_providers, list), "Available providers should be a list"
        logger.info("✓ Available providers: %s", available_providers)
        
        # Test provider info for non-existent provider
        provider_info = service.get_provider_info("nonexistent")
        assert provider_info == {}, "Non-existent provider should return empty dict"
        logger.info("✓ Provider info for non-existent provider works correctly")
        
        # Test service availability
        is_available = service.is_available()
        assert isinstance(is_available, bool), "Service availability should be boolean"
        logger.info("✓ Service availability: %s", is_available)
        
        # Test custom prompts
        custom_prompts = service.get_custom_prompts()
        assert isinstance(custom_prompts, dict), "Custom prompts should be a dict"
        assert len(custom_prompts) > 0, "Should have at least one custom prompt"
        logger.info("✓ Custom prompts loaded: %s", list(custom_prompts.keys()))
        
        # Test settings
        settings = service.get_settings()
        assert isinstance(settings, dict), "Settings should be a dict"
        assert len(settings) > 0, "Should have at least one setting"
        logger.info("✓ Settings loaded: %s", list(settings.keys()))
        
        logger.info("=== Configuration Management PASSED ===")
        
    except Exception as e:
        logger.error("✗ Configuration management test failed: %s", e)
        raise

def test_provider_configuration(service):
    """Test provider configuration functionality."""
    logger.info("=== Testing Provider Configuration ===")
    
    try:
        # Test configuring provider with empty API key
        result = service.configure_provider("openai", "", "gpt-4-vision-preview")
        assert result == False, "Should reject empty API key"
        logger.info("✓ Provider configuration correctly rejects empty API key")
        
        # Test configuring unsupported provider
        result = service.configure_provider("unsupported", "fake-key", "fake-model")
        assert result == False, "Should reject unsupported provider"
        logger.info("✓ Provider configuration correctly rejects unsupported provider")
        
        logger.info("=== Provider Configuration PASSED ===")
        
    except Exception as e:
        logger.error("✗ Provider configuration test failed: %s", e)
        raise

def test_qsettings_integration(service):
    """Test QSettings integration."""
    logger.info("=== Testing QSettings Integration ===")
    
    try:
        from PySide6.QtCore import QSettings
        
        # Test QSettings access
        settings = QSettings()
        assert settings is not None, "QSettings should be accessible"
        
        # Test saving and loading configuration
        original_settings = service.get_settings()
        service.update_settings({"test_setting": "test_value"})
        new_settings = service.get_settings()
        assert "test_setting" in new_settings, "New setting should be saved"
        
        # Restore original settings
        service.update_settings(original_settings)
        logger.info("✓ QSettings integration working correctly")
        
        logger.info("=== QSettings Integration PASSED ===")
        
    except Exception as e:
        logger.error("✗ QSettings integration test failed: %s", e)
        raise

def test_error_handling(service):
    """Test error handling."""
    logger.info("=== Testing Error Handling ===")
    
    try:
        # Test analyzing without configured provider (main test)
        exception_caught = False
        exception_message = ""
        exception_type = None
        
        logger.info("Testing analyze_image with unconfigured provider...")
        
        try:
            result = service.analyze_image(__file__)  # Use this script as a dummy image
            logger.error("ERROR: No exception raised! Got result: %s", result)
            logger.error("Result type: %s", type(result))
            # If we get here, the service returned instead of raising
            raise AssertionError(f"Expected exception but got result: {result}")
        except ValueError as e:
            exception_caught = True
            exception_message = str(e)
            exception_type = "ValueError"
            logger.info("✓ Correctly raised ValueError for unconfigured provider: %s", exception_message)
        except Exception as e:
            exception_caught = True
            exception_message = str(e)
            exception_type = type(e).__name__
            logger.info("✓ Correctly raised %s for unconfigured provider: %s", exception_type, exception_message)
        
        logger.info("Exception caught: %s, message: %s", exception_caught, exception_message)
        
        assert exception_caught, f"Expected an exception for unconfigured provider, got: {exception_message}"
        assert "provider" in exception_message, f"Expected AI provider configuration error, got: {exception_message}"
        
        # Test setting current provider with non-existent provider
        result = service.set_current_provider("nonexistent")
        assert result == False, "Should return False for non-existent provider"
        logger.info("✓ Correctly handles setting non-existent current provider")
        
        logger.info("=== Error Handling PASSED ===")
        
    except Exception as e:
        logger.error("✗ Error handling test failed: %s", e)
        raise

def main():
    """Run all tests."""
    logger.info("Starting AI Description Service Integration Tests")
    logger.info("==================================================")
    
    try:
        # Initialize service
        from src.gui.services.ai_description_service import AIDescriptionService
        service = AIDescriptionService()
        
        # Run tests
        test_service_initialization(service)
        test_configuration_management(service)
        test_provider_configuration(service)
        test_qsettings_integration(service)
        test_error_handling(service)
        
        logger.info("==================================================")
        logger.info("✓ All tests passed successfully!")
        
    except Exception as e:
        logger.error("==================================================")
        logger.error("✗ Tests failed: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()