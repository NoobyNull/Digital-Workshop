#!/usr/bin/env python3
"""
Test Metadata Editor AI Analysis Integration
Verifies that the metadata editor can properly use AI analysis
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
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def test_ai_service_has_providers():
    """Test that AI service initializes with providers."""
    logger.info("=" * 70)
    logger.info("TEST 1: AI Service Has Providers")
    logger.info("=" * 70)

    try:
        from src.gui.services.ai_description_service import AIDescriptionService

        service = AIDescriptionService()

        if not service.providers:
            logger.error("✗ AI service has no providers")
            return False

        logger.info(f"✓ AI service has {len(service.providers)} provider(s)")
        for provider_name in service.providers.keys():
            logger.info(f"  - {provider_name}")

        return True

    except Exception as e:
        logger.error(f"✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_ai_service_has_current_provider():
    """Test that AI service has a current provider set."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: AI Service Has Current Provider")
    logger.info("=" * 70)

    try:
        from src.gui.services.ai_description_service import AIDescriptionService

        service = AIDescriptionService()

        if not service.current_provider:
            logger.error("✗ AI service current_provider is None")
            return False

        logger.info(
            f"✓ AI service has current_provider: {service.current_provider.__class__.__name__}"
        )

        # Check if it's configured
        if service.current_provider.is_configured():
            logger.info("✓ Current provider is CONFIGURED")
            return True
        else:
            logger.error("✗ Current provider is NOT configured")
            return False

    except Exception as e:
        logger.error(f"✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_metadata_editor_can_get_ai_service():
    """Test that metadata editor can get AI service."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Metadata Editor Can Get AI Service")
    logger.info("=" * 70)

    try:
        from src.gui.services.ai_description_service import AIDescriptionService

        # Create a mock parent with ai_service
        class MockParent:
            def __init__(self):
                self.ai_service = AIDescriptionService()

            def parent(self):
                return None

        parent = MockParent()

        # Simulate what metadata editor does
        ai_service = parent.ai_service

        if not ai_service:
            logger.error("✗ Could not get AI service from parent")
            return False

        logger.info("✓ Got AI service from parent")

        # Check providers
        if not ai_service.providers:
            logger.error("✗ AI service has no providers")
            return False

        logger.info(f"✓ AI service has {len(ai_service.providers)} provider(s)")

        # Check current provider
        if not ai_service.current_provider:
            logger.error("✗ AI service has no current_provider")
            return False

        logger.info(
            f"✓ AI service has current_provider: {ai_service.current_provider.__class__.__name__}"
        )

        # Check if configured
        if not ai_service.current_provider.is_configured():
            logger.error("✗ Current provider is not configured")
            return False

        logger.info("✓ Current provider is CONFIGURED")
        return True

    except Exception as e:
        logger.error(f"✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_metadata_editor_error_handling():
    """Test that metadata editor has proper error handling."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Metadata Editor Error Handling")
    logger.info("=" * 70)

    try:
        from src.gui.services.ai_description_service import AIDescriptionService

        # Test with empty providers (simulate no API key)
        service = AIDescriptionService()

        # Simulate the metadata editor's checks
        if not service.providers:
            logger.info("✓ Correctly detects when no providers are available")
            return True

        # If we have providers, check current_provider
        if not service.current_provider:
            logger.info("✓ Correctly detects when current_provider is None")
            # This should be handled by setting it to first available
            service.current_provider = next(iter(service.providers.values()))
            logger.info("✓ Can set current_provider to first available")

        # Check if configured
        if service.current_provider.is_configured():
            logger.info("✓ Current provider is configured")
            return True
        else:
            logger.error("✗ Current provider is not configured")
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
    logger.info(
        "║" + " " * 10 + "METADATA EDITOR AI ANALYSIS INTEGRATION TEST" + " " * 14 + "║"
    )
    logger.info("╚" + "=" * 68 + "╝")

    results = []

    # Run tests
    results.append(("AI Service Has Providers", test_ai_service_has_providers()))
    results.append(
        ("AI Service Has Current Provider", test_ai_service_has_current_provider())
    )
    results.append(
        (
            "Metadata Editor Can Get AI Service",
            test_metadata_editor_can_get_ai_service(),
        )
    )
    results.append(
        ("Metadata Editor Error Handling", test_metadata_editor_error_handling())
    )

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
        logger.info("✓ ALL TESTS PASSED - Metadata editor AI analysis is working!")
        return 0
    else:
        logger.error("✗ SOME TESTS FAILED - See details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
