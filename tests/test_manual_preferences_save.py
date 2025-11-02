#!/usr/bin/env python3
"""
Manual test for preferences API key saving
This simulates what happens when user enters API key and clicks Save
"""

import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Initialize QSettings with organization and application names BEFORE importing anything else
from PySide6.QtCore import QCoreApplication, QSettings
QCoreApplication.setOrganizationName("Digital Workshop")
QCoreApplication.setApplicationName("3D Model Manager")

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def test_manual_save():
    """Simulate manual save of API key."""
    logger.info("=" * 70)
    logger.info("TEST: Manual API Key Save")
    logger.info("=" * 70)
    
    # Clear existing settings
    settings = QSettings()
    settings.remove("ai")
    settings.sync()
    logger.info("✓ Cleared existing AI settings")
    
    # Simulate user entering API key
    # Use environment variable for API key (set GOOGLE_API_KEY before running)
    test_api_key = os.getenv("GOOGLE_API_KEY", "")
    if not test_api_key:
        logger.warning("GOOGLE_API_KEY environment variable not set, skipping test")
        logger.info("To run this test, set: export GOOGLE_API_KEY=your_api_key")
        return True

    test_provider = "gemini"

    logger.info(f"\nSimulating user input:")
    logger.info(f"  Provider: {test_provider}")
    logger.info(f"  API Key: {test_api_key[:20]}... (from GOOGLE_API_KEY env var)")
    
    # Simulate save
    logger.info(f"\nSaving to QSettings...")
    settings.setValue("ai/provider_id", test_provider)
    settings.setValue("ai/api_key", test_api_key)
    settings.sync()
    logger.info("✓ Settings saved and synced")
    
    # Verify what was saved
    logger.info(f"\nVerifying saved settings:")
    saved_provider = settings.value("ai/provider_id", "", type=str)
    saved_api_key = settings.value("ai/api_key", "", type=str)
    
    logger.info(f"  Saved provider_id: {saved_provider}")
    logger.info(f"  Saved api_key: {saved_api_key[:20] if saved_api_key else '[EMPTY]'}...")
    
    if saved_provider == test_provider and saved_api_key == test_api_key:
        logger.info("✓ PASS: Settings saved correctly")
    else:
        logger.error("✗ FAIL: Settings not saved correctly")
        return False
    
    # Now test if AI service can load it
    logger.info(f"\nTesting AI Service loading:")
    try:
        from src.gui.services.ai_description_service import AIDescriptionService
        
        service = AIDescriptionService()
        
        logger.info(f"  Providers initialized: {list(service.providers.keys())}")
        
        if "gemini" in service.providers:
            logger.info("✓ PASS: Gemini provider initialized")
            gemini = service.providers["gemini"]
            logger.info(f"    is_configured: {gemini.is_configured()}")
            logger.info(f"    api_key: {gemini.api_key[:20] if gemini.api_key else '[EMPTY]'}...")
            return True
        else:
            logger.error("✗ FAIL: Gemini provider not initialized")
            logger.error(f"  Available providers: {list(service.providers.keys())}")
            logger.error(f"  Config: {service.config.get('providers', {})}")
            return False
            
    except Exception as e:
        logger.error(f"✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_manual_save()
    sys.exit(0 if success else 1)

