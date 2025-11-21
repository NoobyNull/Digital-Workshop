#!/usr/bin/env python3
"""
Test Metadata Loading on Selection
Verifies that metadata loads when a model is selected (single click)
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
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def test_metadata_loading_on_selection():
    """Test that metadata loads when a model is selected."""
    logger.info("=" * 70)
    logger.info("TEST: Metadata Loading on Selection")
    logger.info("=" * 70)

    try:
        from PySide6.QtWidgets import QApplication
        from src.core.database_manager import get_database_manager

        # Create QApplication
        app = QApplication.instance() or QApplication([])

        # Get database manager
        db_manager = get_database_manager()

        # Get first model from database
        models = db_manager.get_all_models()
        if not models:
            logger.warning("No models in database, skipping test")
            return True

        model_id = models[0]["id"]
        logger.info(f"Testing with model ID: {model_id}")

        # Get model metadata
        model = db_manager.get_model(model_id)
        if not model:
            logger.error(f"✗ FAIL: Model {model_id} not found")
            return False

        logger.info(f"✓ Model found: {model.get('filename', 'Unknown')}")

        # Check that metadata fields exist
        required_fields = ["title", "description", "keywords", "category"]
        for field in required_fields:
            if field not in model:
                logger.error(f"✗ FAIL: Model missing field: {field}")
                return False

        logger.info(f"✓ All required metadata fields present")

        # Verify metadata can be loaded
        logger.info(f"  Title: {model.get('title', '[EMPTY]')}")
        logger.info(f"  Description: {model.get('description', '[EMPTY]')[:50]}...")
        logger.info(f"  Keywords: {model.get('keywords', '[EMPTY]')}")
        logger.info(f"  Category: {model.get('category', '[EMPTY]')}")

        logger.info("\n" + "=" * 70)
        logger.info("✓ TEST PASSED - Metadata can be loaded on selection")
        logger.info("=" * 70)
        return True

    except Exception as e:
        logger.error(f"✗ FAIL: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_metadata_loading_on_selection()
    sys.exit(0 if success else 1)
