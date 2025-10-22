"""
Test script for theme system consolidation.

This script tests:
1. Backward compatibility with existing imports and function calls
2. Theme switching performance (<100ms target)
3. Memory stability during repeated operations
4. All existing theme functionality preservation
"""

import gc
import logging
import time
import tracemalloc
# No typing imports needed for this test

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_backward_compatibility():
    """Test that all existing imports and function calls work."""
    logger.info("Testing backward compatibility...")
    
    try:
        # Test imports that should work with the new consolidated system
        from src.gui.theme import (
            ThemeService,
            ThemeManager,
            COLORS,
            color,
            qcolor,
            vtk_rgb,
            theme_to_dict,
            set_theme,
            list_theme_presets,
            apply_theme_preset,
            load_theme_from_settings,
            save_theme_to_settings,
            PRESET_LIGHT,
            get_preset,
            list_presets,
            SPACING_4,
            FALLBACK_COLOR,
            hex_to_rgb,
        )
        
        # Test that functions are callable
        assert callable(color), "color function should be callable"
        assert callable(qcolor), "qcolor function should be callable"
        assert callable(vtk_rgb), "vtk_rgb function should be callable"
        assert callable(theme_to_dict), "theme_to_dict function should be callable"
        assert callable(set_theme), "set_theme function should be callable"
        assert callable(list_theme_presets), "list_theme_presets function should be callable"
        assert callable(apply_theme_preset), "apply_theme_preset function should be callable"
        assert callable(load_theme_from_settings), "load_theme_from_settings function should be callable"
        assert callable(save_theme_to_settings), "save_theme_to_settings function should be callable"
        assert callable(get_preset), "get_preset function should be callable"
        assert callable(list_presets), "list_presets function should be callable"
        assert callable(hex_to_rgb), "hex_to_rgb function should be callable"
        # Note: hex_to_qcolor and hex_to_vtk_rgb are not imported in the test but are available
        
        # Test that constants are accessible
        assert isinstance(SPACING_4, int), "SPACING_4 should be an integer"
        assert isinstance(FALLBACK_COLOR, str), "FALLBACK_COLOR should be a string"
        assert isinstance(PRESET_LIGHT, dict), "PRESET_LIGHT should be a dictionary"
        
        # Test that classes are instantiable
        service = ThemeService.instance()
        assert service is not None, "ThemeService should be instantiable"
        
        manager = ThemeManager.instance()
        assert manager is not None, "ThemeManager should be instantiable"
        
        # Test that COLORS proxy works
        primary_color = COLORS.primary
        assert isinstance(primary_color, str), "COLORS.primary should return a string"
        
        logger.info("✓ Backward compatibility test passed")
        return True
        
    except Exception as e:
        logger.error("✗ Backward compatibility test failed: %s", e)
        return False


def test_theme_switching_performance():
    """Test that theme switching meets <100ms target."""
    logger.info("Testing theme switching performance...")
    
    try:
        from src.gui.theme import ThemeService
        
        service = ThemeService.instance()
        
        # Test qt-material theme switching performance
        themes_to_test = ["light", "dark", "auto"]
        total_time = 0
        iterations = 10
        
        for _ in range(iterations):
            for theme in themes_to_test:
                start_time = time.perf_counter()
                success = service.apply_theme(theme, "qt-material")
                end_time = time.perf_counter()
                
                if not success:
                    logger.warning("Failed to apply theme %s", theme)
                    continue
                
                switch_time = (end_time - start_time) * 1000  # Convert to ms
                total_time += switch_time
                
                if switch_time > 100:
                    logger.warning("Theme switch to %s took %.2fms (>100ms target)", theme, switch_time)
        
        avg_time = total_time / (iterations * len(themes_to_test))
        logger.info("Average theme switching time: %.2fms", avg_time)
        
        if avg_time < 100:
            logger.info("✓ Theme switching performance test passed")
            return True
        else:
            logger.error("✗ Theme switching performance test failed: %.2fms > 100ms target", avg_time)
            return False
            
    except Exception as e:
        logger.error("✗ Theme switching performance test failed: %s", e)
        return False


def test_memory_stability():
    """Test memory stability during repeated operations."""
    logger.info("Testing memory stability...")
    
    try:
        from src.gui.theme import ThemeService
        
        service = ThemeService.instance()
        
        # Start memory tracking
        tracemalloc.start()
        gc.collect()
        
        # Get initial memory snapshot
        snapshot1 = tracemalloc.take_snapshot()
        
        # Perform multiple theme operations
        operations = 20
        for _ in range(operations):
            # Test preset application
            service.apply_preset("light")
            service.apply_preset("dark")
            service.apply_preset("high_contrast")
            
            # Test qt-material theme application
            service.apply_theme("light", "qt-material")
            service.apply_theme("dark", "qt-material")
            
            # Test color setting
            service.set_color("primary", "#ff0000")
            service.set_color("primary", "#0078d4")
            
            # Test save/load
            service.save_theme()
            service.load_theme()
        
        # Force garbage collection
        gc.collect()
        
        # Get final memory snapshot
        snapshot2 = tracemalloc.take_snapshot()
        
        # Compare snapshots
        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        total_diff = sum(stat.size_diff for stat in top_stats)
        
        tracemalloc.stop()
        
        logger.info("Total memory difference: %.2f KB", total_diff / 1024)
        
        # Check for significant memory increase (>1MB)
        if abs(total_diff) < 1024 * 1024:
            logger.info("✓ Memory stability test passed")
            return True
        else:
            logger.error("✗ Memory stability test failed: %.2f KB difference > 1MB", total_diff / 1024)
            return False
            
    except Exception as e:
        logger.error("✗ Memory stability test failed: %s", e)
        return False


def test_theme_functionality():
    """Test that all existing theme functionality is preserved."""
    logger.info("Testing theme functionality preservation...")
    
    try:
        from src.gui.theme import (
            ThemeService,
            color,
            qcolor,
            vtk_rgb,
            apply_theme_preset,
            get_preset,
            list_presets,
            hex_to_rgb,
        )
        from PySide6.QtGui import QColor
        
        service = ThemeService.instance()
        # manager = ThemeManager.instance()  # Not used in this test
        
        # Test preset functionality
        presets = list_presets()
        assert len(presets) > 0, "Should have at least one preset"
        
        for preset_name in presets[:3]:  # Test first 3 presets
            preset = get_preset(preset_name)
            assert isinstance(preset, dict), "Preset should be a dictionary"
            assert len(preset) > 0, "Preset should have at least one color"
            
            # Test preset application
            apply_theme_preset(preset_name)
            
            # Test color retrieval
            if 'primary' in preset:
                primary_color = color('primary')
                assert isinstance(primary_color, str), "Color should be a string"
                assert primary_color.startswith('#'), "Color should be a hex string"
                
                # Test color conversion functions
                rgb = hex_to_rgb(primary_color)
                assert len(rgb) == 3, "RGB should have 3 components"
                assert all(0 <= c <= 255 for c in rgb), "RGB components should be in 0-255 range"
                
                q_color = qcolor('primary')
                assert isinstance(q_color, QColor), "qcolor should return a QColor"
                
                vtk_rgb_result = vtk_rgb('primary')
                assert len(vtk_rgb_result) == 3, "VTK RGB should have 3 components"
                assert all(0.0 <= c <= 1.0 for c in vtk_rgb_result), "VTK RGB components should be in 0-1 range"
        
        # Test qt-material theme functionality
        success = service.apply_theme("dark", "qt-material")
        if success:
            # Test variant setting
            service.set_qt_material_variant("blue")
            service.apply_theme("light", "qt-material")
        
        # Test system theme detection
        system_theme = service.get_system_theme()
        assert system_theme in ["light", "dark"], "System theme should be light or dark"
        
        # Test color setting
        original_primary = service.get_color("primary")
        service.set_color("primary", "#ff0000")
        assert service.get_color("primary") == "#ff0000", "Color should be updated"
        service.set_color("primary", original_primary)  # Restore
        
        # Test save/load functionality
        service.save_theme()
        service.load_theme()
        
        logger.info("✓ Theme functionality preservation test passed")
        return True
        
    except Exception as e:
        logger.error("✗ Theme functionality preservation test failed: %s", e)
        return False


def run_all_tests():
    """Run all tests and report results."""
    logger.info("Starting theme system consolidation tests...")
    
    tests = [
        ("Backward Compatibility", test_backward_compatibility),
        ("Theme Switching Performance", test_theme_switching_performance),
        ("Memory Stability", test_memory_stability),
        ("Theme Functionality Preservation", test_theme_functionality),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info("\n--- Running %s Test ---", test_name)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error("Test %s failed with exception: %s", test_name, e)
            results.append((test_name, False))
    
    # Report results
    logger.info("\n=== Test Results ===")
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        logger.info("%s: %s", test_name, status)
        if result:
            passed += 1
    
    logger.info("\nSummary: %d/%d tests passed", passed, total)
    
    if passed == total:
        logger.info("✓ All tests passed! Theme system consolidation is successful.")
        return True
    else:
        logger.error("✗ Some tests failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    run_all_tests()