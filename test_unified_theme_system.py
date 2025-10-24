#!/usr/bin/env python3
"""
Unified Theme System Integration Test

This script tests the unified theme system to verify that it correctly consolidates
all theme services and solves the color scheme persistence problems.

Test Coverage:
- Theme application and persistence
- Widget registration and dynamic updates
- Memory efficiency and cache performance
- Error handling and graceful degradation
- Backward compatibility with existing code
- Performance monitoring and statistics

Usage:
    python test_unified_theme_system.py
"""

import sys
import time
import os
# Type hints removed for simplicity in test file

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_theme_persistence():
    """Test theme persistence functionality."""
    print("Testing Theme Persistence...")

    try:
        from src.gui.theme import ThemePersistence

        persistence = ThemePersistence()

        # Test save/load cycle
        test_theme = {
            "theme_name": "dark",
            "theme_variant": "blue",
            "custom_colors": {
                "primary": "#1976D2",
                "background": "#121212",
                "surface": "#1E1E1E"
            }
        }

        # Save theme
        save_success = persistence.save_theme(test_theme)
        assert save_success, "Failed to save theme"

        # Load theme
        loaded_theme = persistence.load_theme()
        assert loaded_theme["theme_name"] == "dark", "Theme name not saved correctly"
        assert loaded_theme["theme_variant"] == "blue", "Theme variant not saved correctly"

        # Test atomic save
        atomic_success = persistence.save_theme_atomic(test_theme)
        assert atomic_success, "Failed to save theme atomically"

        print("✓ Theme persistence tests passed")
        return True

    except Exception as e:
        print(f"✗ Theme persistence tests failed: {e}")
        return False

def test_theme_validation():
    """Test theme validation functionality."""
    print("Testing Theme Validation...")

    try:
        from src.gui.theme import ThemeValidator

        validator = ThemeValidator()

        # Test valid theme
        valid_theme = {
            "theme_name": "dark",
            "theme_variant": "blue",
            "custom_colors": {
                "primary": "#1976D2",
                "background": "#121212"
            }
        }

        is_valid, errors, _ = validator.validate_theme(valid_theme)
        assert is_valid, f"Valid theme failed validation: {errors}"
        assert len(errors) == 0, f"Valid theme had errors: {errors}"

        # Test invalid theme
        invalid_theme = {
            "theme_name": "invalid_theme",
            "theme_variant": "blue"
        }

        is_valid, errors, _ = validator.validate_theme(invalid_theme)
        assert not is_valid, "Invalid theme passed validation"
        assert len(errors) > 0, "Invalid theme should have errors"

        print("✓ Theme validation tests passed")
        return True

    except Exception as e:
        print(f"✗ Theme validation tests failed: {e}")
        return False

def test_theme_cache():
    """Test theme cache functionality."""
    print("Testing Theme Cache...")

    try:
        from src.gui.theme import ThemeCache

        cache = ThemeCache(max_size=10)

        # Test basic cache operations
        test_data = {"theme": "dark", "colors": {"primary": "#1976D2"}}

        # Put data in cache
        put_success = cache.put("test_key", test_data)
        assert put_success, "Failed to put data in cache"

        # Get data from cache
        cached_data = cache.get("test_key")
        assert cached_data is not None, "Failed to get data from cache"
        assert cached_data["theme"] == "dark", "Cached data corrupted"

        # Test cache stats
        stats = cache.get_stats()
        assert stats["size"] == 1, "Cache size incorrect"
        assert stats["hits"] >= 0, "Cache hits should be non-negative"
        assert stats["misses"] >= 0, "Cache misses should be non-negative"

        print("✓ Theme cache tests passed")
        return True

    except Exception as e:
        print(f"✗ Theme cache tests failed: {e}")
        return False

def test_theme_registry():
    """Test theme registry functionality."""
    print("Testing Theme Registry...")

    try:
        from src.gui.theme import ThemeRegistry
        from PySide6.QtWidgets import QApplication, QLabel

        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)

        registry = ThemeRegistry()

        # Create test widget
        test_widget = QLabel("Test Widget")
        test_widget.setObjectName("test_widget")

        # Test widget registration
        register_success = registry.register_widget(test_widget, "test_widget")
        assert register_success, "Failed to register widget"

        # Check if widget is registered
        registered_widgets = registry.get_registered_widgets()
        assert "test_widget" in registered_widgets, "Widget not found in registry"

        # Test widget info
        widget_info = registry.get_widget_info("test_widget")
        assert widget_info is not None, "Widget info not found"
        assert widget_info["widget_name"] == "test_widget", "Widget name incorrect"

        # Test registry stats
        stats = registry.get_registry_stats()
        assert stats["total_registered"] >= 1, "Registry should have at least one widget"
        assert stats["alive_widgets"] >= 1, "Registry should have at least one alive widget"

        print("✓ Theme registry tests passed")
        return True

    except Exception as e:
        print(f"✗ Theme registry tests failed: {e}")
        return False

def test_unified_theme_manager():
    """Test unified theme manager functionality."""
    print("Testing Unified Theme Manager...")

    try:
        from src.gui.theme import QtMaterialThemeService

        # Get manager instance
        manager = QtMaterialThemeService.instance()

        # Test theme application
        apply_success = manager.apply_theme("dark", "blue")
        assert apply_success, "Failed to apply theme"

        # Test getting current theme
        current_theme, current_variant = manager.get_current_theme()
        assert current_theme == "dark", f"Current theme incorrect: {current_theme}"
        assert current_variant == "blue", f"Current variant incorrect: {current_variant}"

        # Test getting available themes
        available_themes = manager.get_available_themes()
        assert "dark" in available_themes, "Dark theme not available"
        assert "blue" in available_themes["dark"], "Blue variant not available"

        # Test getting colors
        colors = manager.get_theme_colors()
        assert isinstance(colors, dict), "Colors should be a dictionary"
        assert "primary" in colors, "Primary color should be available"

        primary_color = manager.get_color("primary")
        assert primary_color.startswith("#"), "Primary color should be hex format"

        # Test system status
        status = manager.get_system_status()
        assert "initialized" in status, "Status should contain initialized flag"
        assert "current_theme" in status, "Status should contain current theme"
        assert status["current_theme"] == "dark", "Status theme should match current theme"

        print("✓ Unified theme manager tests passed")
        return True

    except Exception as e:
        print(f"✗ Unified theme manager tests failed: {e}")
        return False

def test_backward_compatibility():
    """Test backward compatibility with existing code."""
    print("Testing Backward Compatibility...")

    try:
        from src.gui.theme import (
            ThemeService, ThemeManager,
            color, qcolor, vtk_rgb, theme_to_dict
        )

        # Test that old aliases still work
        assert ThemeService is not None, "ThemeService alias should work"
        assert ThemeManager is not None, "ThemeManager alias should work"

        # Test old-style color access
        primary_color = color("primary")
        assert primary_color.startswith("#"), "Color function should return hex color"

        # Test QColor conversion
        q_color = qcolor("primary")
        assert hasattr(q_color, 'red'), "qcolor should return QColor object"

        # Test VTK RGB conversion
        vtk_color = vtk_rgb("primary")
        assert len(vtk_color) == 3, "vtk_rgb should return RGB tuple"
        assert all(0 <= c <= 1 for c in vtk_color), "VTK colors should be normalized"

        # Test theme to dict conversion
        theme_dict = theme_to_dict()
        assert isinstance(theme_dict, dict), "theme_to_dict should return dictionary"

        print("✓ Backward compatibility tests passed")
        return True

    except Exception as e:
        print(f"✗ Backward compatibility tests failed: {e}")
        return False

def test_performance():
    """Test theme system performance."""
    print("Testing Performance...")

    try:
        from src.gui.theme import QtMaterialThemeService

        manager = QtMaterialThemeService.instance()

        # Test multiple theme applications
        start_time = time.time()

        for i in range(10):
            theme_name = "dark" if i % 2 == 0 else "light"
            variant = ["blue", "amber", "cyan"][i % 3]

            assert manager.apply_theme(theme_name, variant), f"Failed to apply theme {theme_name}/{variant}"

        elapsed = (time.time() - start_time) * 1000  # Convert to milliseconds

        # Should complete 10 theme applications in reasonable time
        assert elapsed < 5000, f"Theme applications too slow: {elapsed:.2f}ms"

        # Test cache performance
        status_info = manager.get_system_status()
        cache_stats = status_info["components"]["cache"]
        assert cache_stats["hit_ratio"] >= 0, "Cache hit ratio should be non-negative"

        print(f"✓ Performance tests passed ({elapsed:.2f}ms for 10 theme applications)")
        return True

    except Exception as e:
        print(f"✗ Performance tests failed: {e}")
        return False

def test_memory_efficiency():
    """Test memory efficiency and leak prevention."""
    print("Testing Memory Efficiency...")

    try:
        import gc
        from src.gui.theme import QtMaterialThemeService

        # Get initial object count
        initial_objects = len(gc.get_objects())

        manager = QtMaterialThemeService.instance()

        # Perform multiple operations that could cause memory leaks
        for i in range(50):
            # Apply different themes
            theme = "dark" if i % 2 == 0 else "light"
            manager.apply_theme(theme, "blue")

            # Register dummy widgets
            manager.register_widget(type('DummyWidget', (), {'__class__': type})())

            # Get status (creates new objects)
            manager.get_system_status()

        # Force garbage collection
        gc.collect()

        # Check for significant memory growth
        final_objects = len(gc.get_objects())
        object_growth = final_objects - initial_objects

        # Allow some growth but not excessive (less than 1000 new objects)
        assert object_growth < 1000, f"Excessive memory growth: {object_growth} new objects"

        print(f"✓ Memory efficiency tests passed ({object_growth} new objects)")
        return True

    except Exception as e:
        print(f"✗ Memory efficiency tests failed: {e}")
        return False

def run_all_tests():
    """Run all theme system tests."""
    print("Running Unified Theme System Integration Tests")
    print("=" * 50)

    tests = [
        test_theme_persistence,
        test_theme_validation,
        test_theme_cache,
        test_theme_registry,
        test_unified_theme_manager,
        test_backward_compatibility,
        test_performance,
        test_memory_efficiency
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
        print()

    print("=" * 50)
    print(f"Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! Unified theme system is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)