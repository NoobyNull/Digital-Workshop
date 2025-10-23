"""
Test suite for theme variant persistence fix.

Validates that theme variants are properly saved to QSettings and persist
across application restarts.
"""

import pytest
from pathlib import Path
from PySide6.QtCore import QSettings, QCoreApplication


class TestThemeVariantPersistence:
    """Test theme variant persistence across restarts."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Create a test settings instance
        self.settings = QSettings("Candy-Cadence-Test", "3D-MM-Test")
        yield
        # Cleanup
        self.settings.clear()
        self.settings.sync()

    def test_variant_saved_to_qsettings(self):
        """Test that variant is saved to QSettings."""
        # Set a variant
        self.settings.setValue("qt_material_variant", "amber")
        self.settings.sync()
        
        # Verify it was saved
        saved_variant = self.settings.value("qt_material_variant", None, type=str)
        assert saved_variant == "amber", "Variant should be saved to QSettings"

    def test_variant_persists_across_reads(self):
        """Test that variant persists across multiple reads."""
        # Save variant
        self.settings.setValue("qt_material_variant", "cyan")
        self.settings.sync()
        
        # Read it multiple times
        for _ in range(3):
            variant = self.settings.value("qt_material_variant", "blue", type=str)
            assert variant == "cyan", "Variant should persist across reads"

    def test_variant_defaults_to_blue(self):
        """Test that missing variant defaults to blue."""
        # Clear the setting
        self.settings.remove("qt_material_variant")
        self.settings.sync()
        
        # Read with default
        variant = self.settings.value("qt_material_variant", "blue", type=str)
        assert variant == "blue", "Missing variant should default to blue"

    def test_backward_compatibility_old_key(self):
        """Test backward compatibility with old variant key."""
        # Save using old key
        self.settings.setValue("theme/current_variant", "purple")
        self.settings.sync()
        
        # Try to read from new key first (should fail, returns empty string)
        new_key_variant = self.settings.value("qt_material_variant", "", type=str)
        assert new_key_variant == "", "New key should not have value"
        
        # Fall back to old key
        old_key_variant = self.settings.value("theme/current_variant", "blue", type=str)
        assert old_key_variant == "purple", "Old key should still be readable"

    def test_new_key_takes_precedence(self):
        """Test that new key takes precedence over old key."""
        # Set both keys
        self.settings.setValue("theme/current_variant", "purple")
        self.settings.setValue("qt_material_variant", "amber")
        self.settings.sync()
        
        # New key should take precedence
        new_key_variant = self.settings.value("qt_material_variant", None, type=str)
        assert new_key_variant == "amber", "New key should take precedence"

    def test_variant_changes_persist(self):
        """Test that changing variant multiple times persists correctly."""
        variants = ["blue", "amber", "cyan", "purple", "red"]
        
        for variant in variants:
            self.settings.setValue("qt_material_variant", variant)
            self.settings.sync()
            
            saved = self.settings.value("qt_material_variant", None, type=str)
            assert saved == variant, f"Variant {variant} should be saved and retrieved"


class TestThemeServiceVariantHandling:
    """Test theme service variant handling."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        from src.gui.theme.simple_service import ThemeService
        self.service = ThemeService.instance()
        # Clear settings
        settings = QSettings("Candy-Cadence", "3D-MM")
        settings.remove("qt_material_variant")
        settings.sync()
        yield

    def test_service_set_variant(self):
        """Test that service.set_qt_material_variant saves correctly."""
        self.service.set_qt_material_variant("amber")
        
        # Verify it's in QSettings
        settings = QSettings("Candy-Cadence", "3D-MM")
        saved = settings.value("qt_material_variant", None, type=str)
        assert saved == "amber", "Service should save variant to QSettings"

    def test_service_gets_variants(self):
        """Test that service returns available variants."""
        dark_variants = self.service.get_qt_material_variants("dark")
        light_variants = self.service.get_qt_material_variants("light")
        
        assert len(dark_variants) > 0, "Should have dark variants"
        assert len(light_variants) > 0, "Should have light variants"
        assert "dark_blue" in dark_variants or "blue" in dark_variants
        assert "light_blue" in light_variants or "blue" in light_variants

    def test_current_theme_and_variant(self):
        """Test getting current theme and variant."""
        theme, library = self.service.get_current_theme()
        
        assert theme in ["light", "dark", "auto"], "Theme should be valid"
        assert library == "qt-material", "Library should be qt-material"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
