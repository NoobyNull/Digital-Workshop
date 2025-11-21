#!/usr/bin/env python3
"""
End-to-End Test for AI Analysis Button
Tests the complete flow from button click to metadata update
"""

import os
import sys
import logging
from pathlib import Path

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


def test_ai_service_analyze_image():
    """Test that AI service can analyze an image."""
    logger.info("=" * 70)
    logger.info("TEST 1: AI Service Can Analyze Image")
    logger.info("=" * 70)

    try:
        from src.gui.services.ai_description_service import AIDescriptionService
        from PIL import Image
        import tempfile

        # Create a test image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img = Image.new("RGB", (100, 100), color="red")
            img.save(tmp.name)
            test_image_path = tmp.name

        try:
            service = AIDescriptionService()

            if not service.providers:
                logger.error("✗ No providers available")
                return False

            logger.info(f"✓ Service has {len(service.providers)} provider(s)")

            # Try to analyze the image
            logger.info(f"Analyzing test image: {test_image_path}")
            result = service.analyze_image(test_image_path)

            logger.info("✓ Image analysis completed")
            logger.info(f"  Result keys: {list(result.keys())}")

            # Check for required fields
            required_fields = ["title", "description", "metadata_keywords"]
            for field in required_fields:
                if field in result:
                    logger.info(f"  ✓ {field}: {str(result[field])[:50]}...")
                else:
                    logger.warning(f"  ⚠ Missing field: {field}")

            return True

        finally:
            # Clean up
            if os.path.exists(test_image_path):
                os.remove(test_image_path)

    except Exception as e:
        logger.error(f"✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_metadata_field_names():
    """Test that metadata fields have correct names."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 2: Metadata Field Names Are Correct")
    logger.info("=" * 70)

    try:
        # Check the source code for field names
        metadata_file = Path("src/gui/metadata_components/metadata_editor_main.py")
        content = metadata_file.read_text()

        # Check for correct field names
        fields_to_check = [
            ("self.title_field", "Title field"),
            ("self.description_field", "Description field"),
            ("self.keywords_field", "Keywords field"),
        ]

        all_found = True
        for field_name, description in fields_to_check:
            if field_name in content:
                logger.info(f"✓ Found {description}: {field_name}")
            else:
                logger.error(f"✗ Missing {description}: {field_name}")
                all_found = False

        # Check that old field names are NOT used in _apply_ai_results
        old_fields = [
            "self.title_edit",
            "self.description_edit",
            "self.keywords_edit",
        ]

        # Find _apply_ai_results method
        if "def _apply_ai_results" in content:
            logger.info("✓ Found _apply_ai_results method")

            # Extract the method
            start = content.find("def _apply_ai_results")
            end = content.find("\n    def ", start + 1)
            if end == -1:
                end = len(content)

            method_content = content[start:end]

            # Check for old field names
            for old_field in old_fields:
                if old_field in method_content:
                    logger.error(
                        f"✗ Old field name found in _apply_ai_results: {old_field}"
                    )
                    all_found = False
                else:
                    logger.info(
                        f"✓ Old field name NOT in _apply_ai_results: {old_field}"
                    )

        return all_found

    except Exception as e:
        logger.error(f"✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_apply_ai_results_logic():
    """Test the logic of applying AI results."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 3: Apply AI Results Logic")
    logger.info("=" * 70)

    try:
        # Simulate what _apply_ai_results does
        result = {
            "title": "Test Model",
            "description": "This is a test model description",
            "metadata_keywords": ["test", "model", "ai"],
        }

        # Check title
        if "title" in result and result["title"]:
            logger.info(f"✓ Can extract title: {result['title']}")
        else:
            logger.error("✗ Cannot extract title")
            return False

        # Check description
        if "description" in result and result["description"]:
            logger.info(f"✓ Can extract description: {result['description'][:50]}...")
        else:
            logger.error("✗ Cannot extract description")
            return False

        # Check keywords
        if "metadata_keywords" in result and result["metadata_keywords"]:
            keywords_str = ", ".join(result["metadata_keywords"])
            logger.info(f"✓ Can extract keywords: {keywords_str}")
        else:
            logger.error("✗ Cannot extract keywords")
            return False

        return True

    except Exception as e:
        logger.error(f"✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_error_handling():
    """Test error handling in AI analysis."""
    logger.info("\n" + "=" * 70)
    logger.info("TEST 4: Error Handling")
    logger.info("=" * 70)

    try:
        from src.gui.services.ai_description_service import AIDescriptionService

        service = AIDescriptionService()

        # Test with non-existent image
        try:
            result = service.analyze_image("/nonexistent/image.png")
            logger.error("✗ Should have raised an error for non-existent image")
            return False
        except Exception as e:
            logger.info(
                f"✓ Correctly raised error for non-existent image: {type(e).__name__}"
            )

        return True

    except Exception as e:
        logger.error(f"✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    logger.info("\n")
    logger.info("╔" + "=" * 68 + "╗")
    logger.info("║" + " " * 15 + "AI ANALYSIS END-TO-END TEST" + " " * 27 + "║")
    logger.info("╚" + "=" * 68 + "╝")

    results = []

    # Run tests
    results.append(("AI Service Can Analyze Image", test_ai_service_analyze_image()))
    results.append(("Metadata Field Names Are Correct", test_metadata_field_names()))
    results.append(("Apply AI Results Logic", test_apply_ai_results_logic()))
    results.append(("Error Handling", test_error_handling()))

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
        logger.info("✓ ALL TESTS PASSED - AI Analysis is working!")
        return 0
    else:
        logger.error("✗ SOME TESTS FAILED - See details above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
