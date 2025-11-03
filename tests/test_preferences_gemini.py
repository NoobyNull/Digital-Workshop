#!/usr/bin/env python3
"""
Test Preferences Dialog Gemini Support
Verifies that the preferences dialog can properly test Gemini connection
"""

import os
import sys
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Handle API key from command line argument
if len(sys.argv) > 1:
    api_key_arg = sys.argv[1]
    os.environ["GOOGLE_API_KEY"] = api_key_arg
    sys.argv.pop(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def test_provider_class_mapping():
    """Test that get_provider_class returns GeminiProvider for 'gemini'."""
    logger.info("=" * 70)
    logger.info("TEST 1: Provider Class Mapping")
    logger.info("=" * 70)
    
    try:
        from src.gui.services.providers import get_provider_class
        
        # Test Gemini provider class
        gemini_class = get_provider_class("gemini")
        
        if gemini_class is None:
            logger.error("✗ get_provider_class('gemini') returned None")
            logger.error("  This means Gemini is marked as 'not supported'")
            return False
        
        logger.info(f"✓ get_provider_class('gemini') returned: {gemini_class.__name__}")
        
        # Test Anthropic provider class
        anthropic_class = get_provider_class("anthropic")
        if anthropic_class is None:
            logger.error("✗ get_provider_class('anthropic') returned None")
            return False
        
        logger.info(f"✓ get_provider_class('anthropic') returned: {anthropic_class.__name__}")
        
        # Test OpenAI provider class
        openai_class = get_provider_class("openai")
        if openai_class is None:
            logger.error("✗ get_provider_class('openai') returned None")
            return False
        
        logger.info(f"✓ get_provider_class('openai') returned: {openai_class.__name__}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to test provider class mapping: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ai_service_test_connection():
    """Test that AIDescriptionService.test_provider_connection works for Gemini."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: AI Service Test Connection")
    logger.info("=" * 70)
    
    try:
        from src.gui.services.ai_description_service import AIDescriptionService
        
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        
        if not api_key:
            logger.error("✗ GOOGLE_API_KEY not set, skipping test")
            return False
        
        logger.info("Testing Gemini provider connection...")
        success, message = AIDescriptionService.test_provider_connection(
            provider_id="gemini",
            api_key=api_key,
            model_id="gemini-2.5-flash"
        )
        
        if success:
            logger.info(f"✓ Connection test PASSED: {message}")
            return True
        else:
            logger.error(f"✗ Connection test FAILED: {message}")
            return False
        
    except Exception as e:
        logger.error(f"✗ Failed to test connection: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_preferences_provider_list():
    """Test that preferences dialog can list Gemini as a provider."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Preferences Provider List")
    logger.info("=" * 70)
    
    try:
        from src.gui.services.ai_description_service import AIDescriptionService
        
        providers = AIDescriptionService.get_provider_display_names()
        
        logger.info(f"✓ Available providers: {len(providers)} providers")
        
        if "gemini" not in providers:
            logger.error("✗ Gemini not in provider display names")
            return False
        
        logger.info(f"✓ Gemini provider found: {providers['gemini']}")
        
        # Check other providers
        for provider_id, provider_name in providers.items():
            logger.info(f"  - {provider_id}: {provider_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to test provider list: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_preferences_model_list():
    """Test that preferences dialog can list Gemini models."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Preferences Model List")
    logger.info("=" * 70)
    
    try:
        from src.gui.services.ai_description_service import AIDescriptionService
        
        models = AIDescriptionService.get_available_models("gemini")
        
        if not models:
            logger.error("✗ No models found for Gemini provider")
            return False
        
        logger.info(f"✓ Found {len(models)} Gemini models:")
        for model_id, model_name in models.items():
            logger.info(f"  - {model_id}: {model_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to test model list: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 12 + "PREFERENCES DIALOG GEMINI SUPPORT TEST" + " " * 20 + "║")
    logger.info("╚" + "=" * 68 + "╝")
    
    results = []
    
    # Run tests
    results.append(("Provider Class Mapping", test_provider_class_mapping()))
    results.append(("AI Service Test Connection", test_ai_service_test_connection()))
    results.append(("Preferences Provider List", test_preferences_provider_list()))
    results.append(("Preferences Model List", test_preferences_model_list()))
    
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
        logger.info("✓ ALL TESTS PASSED - Preferences dialog Gemini support is working!")
        return 0
    else:
        logger.error("✗ SOME TESTS FAILED - See details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

