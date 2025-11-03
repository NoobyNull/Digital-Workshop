#!/usr/bin/env python3
"""
Debug API Key Loading
Verifies what API keys are being loaded from QSettings
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


def debug_qsettings():
    """Debug what's in QSettings."""
    logger.info("=" * 70)
    logger.info("DEBUG: QSettings Contents")
    logger.info("=" * 70)
    
    settings = QSettings()
    
    # Check what's saved
    logger.info(f"ai/provider_id: {settings.value('ai/provider_id', 'NOT SET', type=str)}")
    logger.info(f"ai/api_key: {settings.value('ai/api_key', 'NOT SET', type=str)}")
    logger.info(f"ai/model_id: {settings.value('ai/model_id', 'NOT SET', type=str)}")
    
    # Check all keys
    logger.info("\nAll QSettings keys:")
    settings.beginGroup("ai")
    for key in settings.allKeys():
        value = settings.value(key, "")
        logger.info(f"  ai/{key}: {value}")
    settings.endGroup()


def debug_ai_service_config():
    """Debug what the AI service is loading."""
    logger.info("\n" + "=" * 70)
    logger.info("DEBUG: AI Service Config")
    logger.info("=" * 70)
    
    try:
        from src.gui.services.ai_description_service import AIDescriptionService
        
        service = AIDescriptionService()
        
        logger.info(f"Config: {service.config}")
        logger.info(f"\nProviders config:")
        for provider_name, provider_config in service.config.get("providers", {}).items():
            logger.info(f"  {provider_name}:")
            logger.info(f"    api_key: {provider_config.get('api_key', 'NOT SET')}")
            logger.info(f"    model: {provider_config.get('model', 'NOT SET')}")
        
        logger.info(f"\nInitialized providers: {list(service.providers.keys())}")
        for provider_name, provider in service.providers.items():
            logger.info(f"  {provider_name}: {provider.__class__.__name__}")
            logger.info(f"    is_configured: {provider.is_configured()}")
            logger.info(f"    api_key: {provider.api_key}")
        
        logger.info(f"\nCurrent provider: {service.current_provider}")
        if service.current_provider:
            logger.info(f"  Type: {service.current_provider.__class__.__name__}")
            logger.info(f"  is_configured: {service.current_provider.is_configured()}")
        
    except Exception as e:
        logger.error(f"Failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run debug."""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 20 + "DEBUG API KEY LOADING" + " " * 28 + "║")
    logger.info("╚" + "=" * 68 + "╝")
    
    debug_qsettings()
    debug_ai_service_config()


if __name__ == "__main__":
    main()

