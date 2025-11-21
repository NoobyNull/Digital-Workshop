#!/usr/bin/env python3
"""
Minimal error handling test to isolate the issue.
"""

import sys
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(".") / "src"))

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    """Minimal error handling test."""
    logger.info("Starting minimal error handling test")

    try:
        from src.gui.services.ai_description_service import AIDescriptionService

        service = AIDescriptionService()

        logger.info("Service created successfully")
        logger.info("Available providers: %s", service.get_available_providers())
        logger.info("Current provider: %s", service.current_provider)
        logger.info("Service available: %s", service.is_available())

        # Test error handling
        logger.info("Testing analyze_image with unconfigured provider...")

        try:
            result = service.analyze_image(__file__)
            logger.error("ERROR: No exception raised! Got result: %s", result)
            print("FAILED: No exception raised")
            return False
        except ValueError as e:
            exception_message = str(e)
            logger.info("✓ ValueError raised: %s", exception_message)

            # Test assertions
            assert (
                "provider" in exception_message
            ), f"Expected 'provider' in message, got: {exception_message}"
            logger.info("✓ Assertion passed: message contains 'provider'")

            print("PASSED: Error handling test successful")
            return True
        except Exception as e:
            logger.error("✗ Unexpected exception: %s: %s", type(e).__name__, e)
            print(f"FAILED: Unexpected exception {type(e).__name__}: {e}")
            return False

    except Exception as e:
        logger.error("✗ Test setup failed: %s", e)
        print(f"FAILED: Test setup error {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
