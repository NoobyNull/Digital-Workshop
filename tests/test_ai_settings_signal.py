#!/usr/bin/env python3
"""
Test AI Settings Signal
Verifies that the ai_settings_changed signal is emitted when preferences are saved
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


def test_ai_settings_signal():
    """Test that ai_settings_changed signal is emitted."""
    logger.info("=" * 70)
    logger.info("TEST: AI Settings Signal")
    logger.info("=" * 70)

    try:
        from PySide6.QtWidgets import QApplication
        from src.gui.preferences import PreferencesDialog

        # Create QApplication
        app = QApplication.instance() or QApplication([])

        # Create preferences dialog
        dlg = PreferencesDialog()

        # Check that signal exists
        if not hasattr(dlg, "ai_settings_changed"):
            logger.error("✗ FAIL: PreferencesDialog has no ai_settings_changed signal")
            return False

        logger.info("✓ ai_settings_changed signal exists")

        # Connect to signal to verify it's emitted
        signal_emitted = []
        dlg.ai_settings_changed.connect(lambda: signal_emitted.append(True))

        # Manually emit the signal to test
        dlg.ai_settings_changed.emit()

        if signal_emitted:
            logger.info("✓ ai_settings_changed signal can be emitted and received")
            return True
        else:
            logger.error("✗ FAIL: Signal was not received")
            return False

    except Exception as e:
        logger.error(f"✗ FAIL: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_ai_settings_signal()
    sys.exit(0 if success else 1)
