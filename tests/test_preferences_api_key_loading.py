#!/usr/bin/env python3
"""
Test API Key Loading from Preferences
Verifies that API keys saved in preferences are loaded correctly
"""

import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize QSettings with organization and application names BEFORE importing anything else
from PySide6.QtCore import QCoreApplication
QCoreApplication.setOrganizationName("Digital Workshop")
QCoreApplication.setApplicationName("3D Model Manager")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def test_api_key_saved_to_qsettings():
    """Test that API key can be saved to QSettings."""
    logger.info("=" * 70)
    logger.info("TEST 1: API Key Saved to QSettings")
    logger.info("=" * 70)
    
    try:
        from PySide6.QtCore import QSettings
        
        # Create a test settings object
        settings = QSettings()
        
        # Save a test API key
        test_key = "test_api_key_12345"
        settings.setValue("ai/api_key", test_key)
        settings.sync()
        
        # Load it back
        loaded_key = settings.value("ai/api_key", "", type=str)
        
        if loaded_key == test_key:
            logger.info(f"✓ API key saved and loaded correctly")
            return True
        else:
            logger.error(f"✗ API key mismatch: saved '{test_key}', loaded '{loaded_key}'")
            return False
        
    except Exception as e:
        logger.error(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_service_loads_api_key_from_qsettings():
    """Test that AI service loads API key from QSettings."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: AI Service Loads API Key from QSettings")
    logger.info("=" * 70)
    
    try:
        from PySide6.QtCore import QSettings
        from src.gui.services.ai_description_service import AIDescriptionService
        
        # Save a test API key for Gemini
        settings = QSettings()
        settings.setValue("ai/provider_id", "gemini")
        settings.setValue("ai/api_key", "test_gemini_key_12345")
        settings.sync()
        
        # Create AI service
        service = AIDescriptionService()
        
        # Check if Gemini provider is initialized
        if "gemini" not in service.providers:
            logger.error("✗ Gemini provider not initialized")
            return False
        
        logger.info("✓ Gemini provider initialized")
        
        # Check if it has the API key
        gemini_provider = service.providers["gemini"]
        if gemini_provider.api_key == "test_gemini_key_12345":
            logger.info("✓ API key loaded from QSettings")
            return True
        else:
            logger.error(f"✗ API key not loaded correctly: {gemini_provider.api_key}")
            return False
        
    except Exception as e:
        logger.error(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_key_priority():
    """Test that API key priority is correct (QSettings > env var)."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: API Key Priority (QSettings > Environment)")
    logger.info("=" * 70)
    
    try:
        from PySide6.QtCore import QSettings
        from src.gui.services.ai_description_service import AIDescriptionService
        
        # Set environment variable
        os.environ["GOOGLE_API_KEY"] = "env_var_key_12345"
        
        # Save a different key to QSettings
        settings = QSettings()
        settings.setValue("ai/provider_id", "gemini")
        settings.setValue("ai/api_key", "qsettings_key_12345")
        settings.sync()
        
        # Create AI service
        service = AIDescriptionService()
        
        # Check if QSettings key takes priority
        if "gemini" in service.providers:
            gemini_provider = service.providers["gemini"]
            if gemini_provider.api_key == "qsettings_key_12345":
                logger.info("✓ QSettings API key takes priority over environment variable")
                return True
            else:
                logger.error(f"✗ Wrong API key: {gemini_provider.api_key}")
                return False
        else:
            logger.error("✗ Gemini provider not initialized")
            return False
        
    except Exception as e:
        logger.error(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_api_key_fallback_to_env():
    """Test that API key falls back to environment variable if not in QSettings."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: API Key Fallback to Environment Variable")
    logger.info("=" * 70)
    
    try:
        from PySide6.QtCore import QSettings
        from src.gui.services.ai_description_service import AIDescriptionService
        
        # Clear QSettings
        settings = QSettings()
        settings.remove("ai/api_key")
        settings.setValue("ai/provider_id", "gemini")
        settings.sync()
        
        # Set environment variable
        os.environ["GOOGLE_API_KEY"] = "env_var_key_fallback"
        
        # Create AI service
        service = AIDescriptionService()
        
        # Check if environment variable is used
        if "gemini" in service.providers:
            gemini_provider = service.providers["gemini"]
            if gemini_provider.api_key == "env_var_key_fallback":
                logger.info("✓ Falls back to environment variable when QSettings is empty")
                return True
            else:
                logger.error(f"✗ Wrong API key: {gemini_provider.api_key}")
                return False
        else:
            logger.error("✗ Gemini provider not initialized")
            return False
        
    except Exception as e:
        logger.error(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 12 + "API KEY LOADING FROM PREFERENCES TEST" + " " * 20 + "║")
    logger.info("╚" + "=" * 68 + "╝")
    
    results = []
    
    # Run tests
    results.append(("API Key Saved to QSettings", test_api_key_saved_to_qsettings()))
    results.append(("AI Service Loads API Key from QSettings", test_ai_service_loads_api_key_from_qsettings()))
    results.append(("API Key Priority (QSettings > Environment)", test_api_key_priority()))
    results.append(("API Key Fallback to Environment Variable", test_api_key_fallback_to_env()))
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info("=" * 70)
    logger.info(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✓ ALL TESTS PASSED - API key loading is working!")
        return 0
    else:
        logger.error("✗ SOME TESTS FAILED - See details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

