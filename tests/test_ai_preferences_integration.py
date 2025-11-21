#!/usr/bin/env python3
"""
Test AI Preferences Integration

Tests the integration of AI Description Service with the preferences dialog.
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from PySide6.QtTest import QTest

from src.gui.preferences import PreferencesDialog, AITab
from src.gui.services.ai_description_service import AIDescriptionService


class TestAIPreferencesIntegration(unittest.TestCase):
    """Test AI preferences integration."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()

    def setUp(self):
        """Set up each test."""
        # Clear QSettings for clean test environment
        settings = QSettings()
        settings.clear()

        # Create preferences dialog
        self.preferences = PreferencesDialog()

    def tearDown(self):
        """Clean up after each test."""
        if hasattr(self, "preferences"):
            self.preferences.close()
            self.preferences.deleteLater()

    def test_ai_tab_exists(self):
        """Test that AI tab is created and accessible."""
        # Find AI tab
        ai_tab = None
        for i in range(self.preferences.tabs.count()):
            tab = self.preferences.tabs.widget(i)
            if isinstance(tab, AITab):
                ai_tab = tab
                break

        self.assertIsNotNone(ai_tab, "AI tab should exist in preferences dialog")
        self.assertIsInstance(ai_tab, AITab, "AI tab should be AITab instance")

    def test_ai_tab_ui_components(self):
        """Test that AI tab has all required UI components."""
        # Find AI tab
        ai_tab = None
        for i in range(self.preferences.tabs.count()):
            tab = self.preferences.tabs.widget(i)
            if isinstance(tab, AITab):
                ai_tab = tab
                break

        self.assertIsNotNone(ai_tab)

        # Check for required UI components
        self.assertTrue(
            hasattr(ai_tab, "provider_combo"), "Should have provider combo box"
        )
        self.assertTrue(hasattr(ai_tab, "api_key_edit"), "Should have API key edit")
        self.assertTrue(hasattr(ai_tab, "model_combo"), "Should have model combo box")
        self.assertTrue(hasattr(ai_tab, "prompt_edit"), "Should have prompt edit")
        self.assertTrue(
            hasattr(ai_tab, "batch_size_spin"), "Should have batch size spin box"
        )
        self.assertTrue(
            hasattr(ai_tab, "enable_batch_check"), "Should have enable batch check"
        )
        self.assertTrue(hasattr(ai_tab, "test_button"), "Should have test button")

    def test_ai_service_static_methods(self):
        """Test AI service static methods work correctly."""
        # Test get_available_providers
        providers = AIDescriptionService.get_available_providers()
        self.assertIsInstance(providers, dict, "Should return dict of providers")
        self.assertIn("openai", providers, "Should include OpenAI provider")
        self.assertIn("openrouter", providers, "Should include OpenRouter provider")

        # Test get_available_models for different providers
        openai_models = AIDescriptionService.get_available_models("openai")
        self.assertIsInstance(openai_models, dict, "Should return dict of models")
        self.assertIn(
            "gpt-4-vision-preview", openai_models, "Should include GPT-4 Vision model"
        )

        # Test unsupported provider
        unknown_models = AIDescriptionService.get_available_models("unknown_provider")
        self.assertEqual(
            unknown_models, {}, "Should return empty dict for unknown provider"
        )

    def test_ai_tab_provider_population(self):
        """Test that AI tab populates providers correctly."""
        # Find AI tab
        ai_tab = None
        for i in range(self.preferences.tabs.count()):
            tab = self.preferences.tabs.widget(i)
            if isinstance(tab, AITab):
                ai_tab = tab
                break

        self.assertIsNotNone(ai_tab)

        # Check that providers are populated
        provider_count = ai_tab.provider_combo.count()
        self.assertGreater(provider_count, 0, "Should have at least one provider")

        # Check that OpenAI is in the list
        provider_ids = [
            ai_tab.provider_combo.itemData(i) for i in range(provider_count)
        ]
        self.assertIn("openai", provider_ids, "OpenAI should be in provider list")

    def test_ai_tab_model_population(self):
        """Test that AI tab populates models when provider changes."""
        # Find AI tab
        ai_tab = None
        for i in range(self.preferences.tabs.count()):
            tab = self.preferences.tabs.widget(i)
            if isinstance(tab, AITab):
                ai_tab = tab
                break

        self.assertIsNotNone(ai_tab)

        # Select OpenAI provider
        openai_index = -1
        for i in range(ai_tab.provider_combo.count()):
            if ai_tab.provider_combo.itemData(i) == "openai":
                openai_index = i
                break

        if openai_index >= 0:
            ai_tab.provider_combo.setCurrentIndex(openai_index)

            # Check that models are populated
            model_count = ai_tab.model_combo.count()
            self.assertGreater(model_count, 0, "Should have models for OpenAI")

    def test_ai_settings_save_load(self):
        """Test that AI settings can be saved and loaded."""
        # Find AI tab
        ai_tab = None
        for i in range(self.preferences.tabs.count()):
            tab = self.preferences.tabs.widget(i)
            if isinstance(tab, AITab):
                ai_tab = tab
                break

        self.assertIsNotNone(ai_tab)

        # Set some test values
        ai_tab.api_key_edit.setText("test_api_key")
        ai_tab.prompt_edit.setText("Test prompt")
        ai_tab.batch_size_spin.setValue(10)
        ai_tab.enable_batch_check.setChecked(True)

        # Save settings
        ai_tab.save_settings()

        # Clear and reload
        ai_tab._load_settings()

        # Verify values are restored
        self.assertEqual(ai_tab.api_key_edit.text(), "test_api_key")
        self.assertEqual(ai_tab.prompt_edit.text(), "Test prompt")
        self.assertEqual(ai_tab.batch_size_spin.value(), 10)
        self.assertTrue(ai_tab.enable_batch_check.isChecked())

    def test_ai_tab_test_connection_ui(self):
        """Test that test connection UI updates correctly."""
        # Find AI tab
        ai_tab = None
        for i in range(self.preferences.tabs.count()):
            tab = self.preferences.tabs.widget(i)
            if isinstance(tab, AITab):
                ai_tab = tab
                break

        self.assertIsNotNone(ai_tab)

        # Test initial state
        self.assertEqual(ai_tab.test_button.text(), "Test Connection")
        self.assertTrue(ai_tab.test_button.isEnabled())

        # Test settings change feedback
        ai_tab._on_settings_changed()
        self.assertIn("Settings changed", ai_tab.test_result_label.text())

    def test_preferences_save_includes_ai(self):
        """Test that preferences save includes AI settings."""
        # Mock the save methods to avoid actual file operations
        with patch.object(self.preferences.ai_tab, "save_settings") as mock_ai_save:
            # Trigger save
            self.preferences._save_and_notify()

            # Verify AI save was called
            mock_ai_save.assert_called_once()

    def test_ai_service_provider_mapping(self):
        """Test that provider class mapping works correctly."""
        from src.gui.services.providers import get_provider_class

        # Test supported providers
        openai_class = get_provider_class("openai")
        self.assertIsNotNone(openai_class, "OpenAI provider class should exist")

        openrouter_class = get_provider_class("openrouter")
        self.assertIsNotNone(openrouter_class, "OpenRouter provider class should exist")

        # Test unsupported provider
        unknown_class = get_provider_class("unknown_provider")
        self.assertIsNone(unknown_class, "Unknown provider should return None")

    def test_ai_tab_error_handling(self):
        """Test that AI tab handles errors gracefully."""
        # Find AI tab
        ai_tab = None
        for i in range(self.preferences.tabs.count()):
            tab = self.preferences.tabs.widget(i)
            if isinstance(tab, AITab):
                ai_tab = tab
                break

        self.assertIsNotNone(ai_tab)

        # Test connection test with invalid data
        # This should not crash
        try:
            ai_tab._test_connection()
        except Exception as e:
            # Connection test may fail due to invalid credentials, but should not crash the UI
            self.assertIsInstance(e, (ValueError, TypeError, AttributeError))


def run_integration_test():
    """Run the integration test."""
    print("Running AI Preferences Integration Test...")

    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAIPreferencesIntegration)

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print(f"\n{'='*60}")
    print(f"Test Results Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(
        f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%"
    )

    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError:')[-1].strip()}")

    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Exception:')[-1].strip()}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_test()
    sys.exit(0 if success else 1)
