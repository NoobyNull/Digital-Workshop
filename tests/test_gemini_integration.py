#!/usr/bin/env python3
"""
Test Gemini Integration with AI Description Service
Verifies that the AI service properly loads Gemini from environment variables
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
    sys.argv.pop(1)  # Remove from argv so it doesn't interfere with other processing

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def test_environment_variable():
    """Test that environment variable is set."""
    logger.info("=" * 70)
    logger.info("TEST 1: Environment Variable Detection")
    logger.info("=" * 70)
    
    api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    
    if api_key:
        logger.info("✓ GOOGLE_API_KEY environment variable is SET")
        logger.info(f"  Key (masked): {api_key[:10]}...{api_key[-4:]}")
        return True
    else:
        logger.error("✗ GOOGLE_API_KEY environment variable is NOT SET")
        logger.error("  Please set it with: set GOOGLE_API_KEY=your_key")
        return False


def test_ai_service_initialization():
    """Test that AI service initializes with Gemini provider."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: AI Service Initialization")
    logger.info("=" * 70)
    
    try:
        from src.gui.services.ai_description_service import AIDescriptionService
        
        logger.info("Creating AIDescriptionService...")
        service = AIDescriptionService()
        
        logger.info("✓ AIDescriptionService created successfully")
        
        # Check available providers
        available_providers = service.get_available_providers()
        logger.info(f"✓ Available providers: {available_providers}")
        
        # Check initialized providers
        initialized = list(service.providers.keys())
        logger.info(f"✓ Initialized providers: {initialized}")
        
        if "gemini" in initialized:
            logger.info("✓ Gemini provider is INITIALIZED")
            return True
        else:
            logger.warning("⚠ Gemini provider is NOT initialized")
            logger.warning("  This might be because GOOGLE_API_KEY is not set")
            return False
            
    except Exception as e:
        logger.error(f"✗ Failed to initialize AIDescriptionService: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_gemini_provider_directly():
    """Test Gemini provider directly."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Gemini Provider Direct Test")
    logger.info("=" * 70)
    
    try:
        api_key = os.getenv("GOOGLE_API_KEY", "").strip()
        
        if not api_key:
            logger.error("✗ GOOGLE_API_KEY not set, skipping direct provider test")
            return False
        
        from src.gui.services.providers.gemini_provider import GeminiProvider
        
        logger.info("Creating GeminiProvider directly...")
        provider = GeminiProvider(api_key=api_key, model="gemini-2.5-flash")
        
        logger.info("✓ GeminiProvider created successfully")
        
        # Check if configured
        if provider.is_configured():
            logger.info("✓ GeminiProvider is CONFIGURED")
        else:
            logger.error("✗ GeminiProvider is NOT configured")
            return False
        
        # List models
        models = provider.list_available_models()
        logger.info(f"✓ Available models: {len(models)} models found")
        if models:
            logger.info(f"  First 3 models: {models[:3]}")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to test Gemini provider: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_metadata_editor_ai_service():
    """Test that metadata editor can get AI service."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Metadata Editor AI Service Access")
    logger.info("=" * 70)

    try:
        from src.gui.services.ai_description_service import AIDescriptionService

        # Create a mock parent with ai_service
        class MockParent:
            def __init__(self):
                self.ai_service = AIDescriptionService()

            def parent(self):
                return None

        logger.info("Creating mock parent with AI service...")
        parent = MockParent()

        logger.info("✓ Mock parent created with AI service")
        logger.info(f"  Parent has ai_service: {hasattr(parent, 'ai_service')}")
        logger.info(f"  AI service providers: {list(parent.ai_service.providers.keys())}")

        if "gemini" in parent.ai_service.providers:
            logger.info("✓ Gemini provider available in AI service")
            return True
        else:
            logger.warning("⚠ Gemini provider not available in AI service")
            return False

    except Exception as e:
        logger.error(f"✗ Failed to test metadata editor AI service: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 15 + "GEMINI INTEGRATION TEST SUITE" + " " * 24 + "║")
    logger.info("╚" + "=" * 68 + "╝")
    
    results = []
    
    # Run tests
    results.append(("Environment Variable", test_environment_variable()))
    results.append(("AI Service Initialization", test_ai_service_initialization()))
    results.append(("Gemini Provider Direct", test_gemini_provider_directly()))
    results.append(("Metadata Editor AI Service", test_metadata_editor_ai_service()))
    
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
        logger.info("✓ ALL TESTS PASSED - Gemini integration is working!")
        return 0
    else:
        logger.error("✗ SOME TESTS FAILED - See details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())

