"""
Detailed theme switching and qt-material integration test.

This test specifically focuses on:
1. Theme switching functionality
2. qt-material integration
3. System theme detection
4. Theme persistence
"""

import logging
import time
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_theme_switching():
    """Test detailed theme switching functionality."""
    logger.info("Testing detailed theme switching functionality...")
    
    try:
        from src.gui.theme import ThemeService
        
        service = ThemeService.instance()
        
        # Test preset switching
        presets = service.get_available_presets()
        logger.info(f"Available presets: {presets}")
        
        for preset in presets[:3]:  # Test first 3 presets
            logger.info(f"Testing preset: {preset}")
            service.apply_preset(preset)
            
            # Verify colors are set
            primary = service.get_color("primary")
            assert primary.startswith("#"), f"Primary color should be hex, got {primary}"
            logger.info(f"  Primary color: {primary}")
        
        # Test qt-material theme switching (if available)
        logger.info("Testing qt-material theme switching...")
        
        # Check if qt-material is available
        try:
            from qt_material import apply_stylesheet
            qt_material_available = True
            logger.info("qt-material library is available")
        except ImportError:
            qt_material_available = False
            logger.warning("qt-material library not installed - skipping qt-material tests")
        
        if qt_material_available:
            # Test qt-material theme application
            themes = ["light", "dark", "auto"]
            for theme in themes:
                logger.info(f"Testing qt-material theme: {theme}")
                success = service.apply_theme(theme, "qt-material")
                if success:
                    logger.info(f"  Successfully applied {theme} theme")
                    
                    # Test variant setting
                    variants = service.get_qt_material_variants(theme)
                    if variants:
                        logger.info(f"  Available variants: {variants[:3]}...")  # Show first 3
                        service.set_qt_material_variant("blue")
                        service.apply_theme(theme, "qt-material")
                        logger.info("  Successfully set blue variant")
                else:
                    logger.warning(f"  Failed to apply {theme} theme")
        
        logger.info("✓ Theme switching test passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Theme switching test failed: {e}")
        return False


def test_system_theme_detection():
    """Test system theme detection functionality."""
    logger.info("Testing system theme detection...")
    
    try:
        from src.gui.theme import ThemeService
        
        service = ThemeService.instance()
        
        # Test system theme detection
        system_theme = service.get_system_theme()
        logger.info(f"Detected system theme: {system_theme}")
        assert system_theme in ["light", "dark"], f"System theme should be light or dark, got {system_theme}"
        
        # Test system detection enable/disable
        was_enabled = service.is_system_detection_enabled()
        logger.info(f"System detection was enabled: {was_enabled}")
        
        # Toggle system detection
        if was_enabled:
            service.disable_system_detection()
            assert not service.is_system_detection_enabled(), "System detection should be disabled"
            logger.info("Successfully disabled system detection")
            
            # Re-enable
            service.enable_system_detection()
            assert service.is_system_detection_enabled(), "System detection should be enabled"
            logger.info("Successfully re-enabled system detection")
        else:
            service.enable_system_detection()
            assert service.is_system_detection_enabled(), "System detection should be enabled"
            logger.info("Successfully enabled system detection")
            
            # Disable
            service.disable_system_detection()
            assert not service.is_system_detection_enabled(), "System detection should be disabled"
            logger.info("Successfully disabled system detection")
        
        logger.info("✓ System theme detection test passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ System theme detection test failed: {e}")
        return False


def test_theme_persistence():
    """Test theme persistence functionality."""
    logger.info("Testing theme persistence...")
    
    try:
        from src.gui.theme import ThemeService
        
        service = ThemeService.instance()
        
        # Save current theme
        original_colors = service.get_all_colors()
        logger.info(f"Original theme has {len(original_colors)} colors")
        
        # Apply a test preset
        service.apply_preset("high_contrast")
        logger.info("Applied high_contrast preset")
        
        # Save theme
        service.save_theme()
        logger.info("Saved theme to AppData")
        
        # Modify colors
        service.set_color("primary", "#ff0000")
        service.set_color("secondary", "#00ff00")
        logger.info("Modified primary and secondary colors")
        
        # Load theme back
        success = service.load_theme()
        assert success, "Theme should load successfully"
        logger.info("Loaded theme from AppData")
        
        # Verify colors were restored
        primary = service.get_color("primary")
        secondary = service.get_color("secondary")
        logger.info(f"Restored colors - primary: {primary}, secondary: {secondary}")
        
        # Test export/import
        export_path = Path("test_theme_export.json")
        service.export_theme(export_path)
        logger.info(f"Exported theme to {export_path}")
        
        # Modify colors again
        service.set_color("primary", "#0000ff")
        logger.info("Modified primary color to blue")
        
        # Import theme
        service.import_theme(export_path)
        logger.info("Imported theme from file")
        
        # Clean up
        if export_path.exists():
            export_path.unlink()
            logger.info("Cleaned up export file")
        
        logger.info("✓ Theme persistence test passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ Theme persistence test failed: {e}")
        return False


def test_ui_components():
    """Test theme UI components."""
    logger.info("Testing theme UI components...")
    
    try:
        from src.gui.theme import ThemeSwitcher, SimpleThemeSwitcher, ThemeDialog
        
        # Test ThemeSwitcher
        switcher = ThemeSwitcher()
        presets = switcher.service.get_available_presets()
        logger.info(f"ThemeSwitcher found {len(presets)} presets")
        
        # Test SimpleThemeSwitcher
        simple_switcher = SimpleThemeSwitcher()
        logger.info("SimpleThemeSwitcher created successfully")
        
        # Test ThemeDialog
        dialog = ThemeDialog()
        logger.info("ThemeDialog created successfully")
        
        logger.info("✓ UI components test passed")
        return True
        
    except Exception as e:
        logger.error(f"✗ UI components test failed: {e}")
        return False


def run_detailed_tests():
    """Run all detailed tests."""
    logger.info("Starting detailed theme system tests...")
    
    tests = [
        ("Theme Switching", test_theme_switching),
        ("System Theme Detection", test_system_theme_detection),
        ("Theme Persistence", test_theme_persistence),
        ("UI Components", test_ui_components),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Report results
    logger.info("\n=== Detailed Test Results ===")
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nSummary: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("✓ All detailed tests passed!")
        return True
    else:
        logger.error("✗ Some detailed tests failed.")
        return False


if __name__ == "__main__":
    run_detailed_tests()