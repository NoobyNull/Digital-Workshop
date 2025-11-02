#!/usr/bin/env python3
"""
Full AI Workflow Test
Simulates the complete workflow: save API key in preferences, reload AI service
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
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def test_full_workflow():
    """Test the full workflow."""
    logger.info("=" * 70)
    logger.info("TEST: Full AI Workflow")
    logger.info("=" * 70)
    
    try:
        from src.gui.services.ai_description_service import AIDescriptionService
        
        # Step 1: Create AI service (simulating app startup)
        logger.info("\n[STEP 1] Creating AI service (app startup)...")
        ai_service_1 = AIDescriptionService()
        providers_1 = list(ai_service_1.providers.keys())
        logger.info(f"  Providers available: {providers_1}")
        
        if "gemini" not in providers_1:
            logger.error("✗ FAIL: Gemini not available at startup")
            return False
        
        logger.info("✓ Gemini provider available")
        
        # Step 2: Simulate preferences save (user enters API key and saves)
        logger.info("\n[STEP 2] Simulating preferences save...")
        settings = QSettings()
        test_api_key = "AIzaSyBPSlisUcMHwaiLTcCWLlSQlmjUFhTFR2c"
        settings.setValue("ai/provider_id", "gemini")
        settings.setValue("ai/api_key", test_api_key)
        settings.sync()
        logger.info(f"  Saved API key to QSettings")
        
        # Step 3: Reload AI service (simulating signal handler)
        logger.info("\n[STEP 3] Reloading AI service (after preferences save)...")
        ai_service_1.config = ai_service_1._load_config()
        ai_service_1._initialize_providers()
        providers_2 = list(ai_service_1.providers.keys())
        logger.info(f"  Providers available: {providers_2}")
        
        if "gemini" not in providers_2:
            logger.error("✗ FAIL: Gemini not available after reload")
            return False
        
        logger.info("✓ Gemini provider available after reload")
        
        # Step 4: Verify Gemini is configured
        logger.info("\n[STEP 4] Verifying Gemini configuration...")
        gemini = ai_service_1.providers["gemini"]
        logger.info(f"  Gemini is_configured: {gemini.is_configured()}")
        logger.info(f"  Gemini api_key: {gemini.api_key[:20] if gemini.api_key else '[EMPTY]'}...")
        
        if not gemini.is_configured():
            logger.error("✗ FAIL: Gemini not configured after reload")
            return False
        
        logger.info("✓ Gemini is properly configured")
        
        # Step 5: Create a fresh AI service (simulating new instance)
        logger.info("\n[STEP 5] Creating fresh AI service instance...")
        ai_service_2 = AIDescriptionService()
        providers_3 = list(ai_service_2.providers.keys())
        logger.info(f"  Providers available: {providers_3}")
        
        if "gemini" not in providers_3:
            logger.error("✗ FAIL: Gemini not available in fresh instance")
            return False
        
        logger.info("✓ Gemini provider available in fresh instance")
        
        gemini_2 = ai_service_2.providers["gemini"]
        if not gemini_2.is_configured():
            logger.error("✗ FAIL: Gemini not configured in fresh instance")
            return False
        
        logger.info("✓ Gemini is properly configured in fresh instance")
        
        logger.info("\n" + "=" * 70)
        logger.info("✓ ALL TESTS PASSED - Full workflow works correctly!")
        logger.info("=" * 70)
        return True
        
    except Exception as e:
        logger.error(f"✗ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_full_workflow()
    sys.exit(0 if success else 1)

