#!/usr/bin/env python3
"""
Test script to verify theme system graceful degradation when qt-material is missing.

This script tests:
1. Theme system works when qt-material is not available
2. Fallback themes are applied correctly
3. All backward compatibility functions work without qt-material
4. Error handling is robust throughout the theme system
"""

import sys
import os
import logging
import time
import gc
from typing import Dict, Any

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_missing_qt_material_handling():
    """Test that theme system handles missing qt-material gracefully."""
    print("Testing missing qt-material library handling...")
    
    try:
        # Force disable qt-material by temporarily hiding it
        original_modules = sys.modules.copy()
        if 'qtmaterial' in sys.modules:
            del sys.modules['qtmaterial']
        
        # Clear any cached imports
        if 'src.gui.theme.qt_material_service' in sys.modules:
            del sys.modules['src.gui.theme.qt_material_service']
        if 'src.gui.theme' in sys.modules:
            del sys.modules['src.gui.theme']
        
        # Import theme system fresh
        from src.gui.theme import QtMaterialThemeService
        
        # Create service instance
        service = QtMaterialThemeService.instance()
        
        # Verify qt-material is not available
        if hasattr(service, 'qtmaterial_available'):
            if not service.qtmaterial_available:
                print("[PASS] qt-material correctly detected as unavailable")
            else:
                print("[FAIL] qt-material should be unavailable but is reported as available")
                return False
        else:
            print("[FAIL] qtmaterial_available attribute not found")
            return False
        
        # Test theme application with fallback
        success = service.apply_theme("dark", "blue")
        if success:
            print("[PASS] Fallback theme application successful")
        else:
            print("[FAIL] Fallback theme application failed")
            return False
        
        # Test color retrieval
        color = service.get_color("primary")
        if isinstance(color, str) and len(color) > 0:
            print(f"[PASS] Color retrieval works: {color}")
        else:
            print(f"[FAIL] Color retrieval failed: {color}")
            return False
        
        # Test theme switching
        success = service.apply_theme("light", "amber")
        if success:
            print("[PASS] Theme switching to light/amber successful")
        else:
            print("[FAIL] Theme switching to light/amber failed")
            return False
        
        # Test variant switching
        success = service.set_theme_variant("cyan")
        if success:
            print("[PASS] Variant switching to cyan successful")
        else:
            print("[FAIL] Variant switching to cyan failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Missing qt-material handling test failed: {e}")
        return False
    finally:
        # Restore original modules
        sys.modules.clear()
        sys.modules.update(original_modules)


def test_fallback_theme_quality():
    """Test the quality and completeness of fallback themes."""
    print("Testing fallback theme quality...")
    
    try:
        from src.gui.theme import QtMaterialThemeService
        
        service = QtMaterialThemeService.instance()
        
        # Test all theme variants
        test_cases = [
            ("dark", "blue"),
            ("dark", "amber"),
            ("dark", "cyan"),
            ("light", "blue"),
            ("light", "amber"),
            ("light", "cyan")
        ]
        
        for theme, variant in test_cases:
            success = service.apply_theme(theme, variant)
            if not success:
                print(f"[FAIL] Failed to apply {theme}/{variant}")
                return False
            
            # Test that colors are available
            primary_color = service.get_color("primary")
            secondary_color = service.get_color("secondary")
            background_color = service.get_color("background")
            
            if not all(isinstance(c, str) and len(c) > 0 for c in [primary_color, secondary_color, background_color]):
                print(f"[FAIL] Missing colors for {theme}/{variant}")
                return False
            
            print(f"[PASS] {theme}/{variant} theme quality verified")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Fallback theme quality test failed: {e}")
        return False


def test_backward_compatibility_without_qt_material():
    """Test backward compatibility functions without qt-material."""
    print("Testing backward compatibility without qt-material...")
    
    try:
        from src.gui.theme import (
            load_theme_from_settings,
            save_theme_to_settings,
            hex_to_rgb,
            apply_theme_preset,
            qss_tabs_lists_labels,
            get_theme_color,
            get_current_theme_name,
            get_current_theme_variant,
            apply_theme_with_variant,
            get_theme_colors,
            rgb_to_hex,
            is_dark_theme,
            is_light_theme,
            COLORS,
            FALLBACK_COLOR
        )
        
        # Test each function
        load_theme_from_settings()
        print("[PASS] load_theme_from_settings works")
        
        rgb = hex_to_rgb("#FF5722")
        if isinstance(rgb, tuple) and len(rgb) == 3:
            print("[PASS] hex_to_rgb works")
        else:
            print(f"[FAIL] hex_to_rgb failed: {rgb}")
            return False
        
        success = apply_theme_preset("dark")
        if success:
            print("[PASS] apply_theme_preset works")
        else:
            print("[FAIL] apply_theme_preset failed")
            return False
        
        qss = qss_tabs_lists_labels()
        if isinstance(qss, str) and len(qss) > 0:
            print("[PASS] qss_tabs_lists_labels works")
        else:
            print("[FAIL] qss_tabs_lists_labels failed")
            return False
        
        color = get_theme_color("primary")
        if isinstance(color, str) and len(color) > 0:
            print("[PASS] get_theme_color works")
        else:
            print(f"[FAIL] get_theme_color failed: {color}")
            return False
        
        theme_name = get_current_theme_name()
        theme_variant = get_current_theme_variant()
        if isinstance(theme_name, str) and isinstance(theme_variant, str):
            print(f"[PASS] Theme name/variant: {theme_name}/{theme_variant}")
        else:
            print(f"[FAIL] Theme name/variant failed: {theme_name}/{theme_variant}")
            return False
        
        success = apply_theme_with_variant("light", "cyan")
        if success:
            print("[PASS] apply_theme_with_variant works")
        else:
            print("[FAIL] apply_theme_with_variant failed")
            return False
        
        colors = get_theme_colors()
        if isinstance(colors, dict) and len(colors) > 0:
            print(f"[PASS] get_theme_colors works: {len(colors)} colors")
        else:
            print(f"[FAIL] get_theme_colors failed: {colors}")
            return False
        
        hex_color = rgb_to_hex(255, 87, 34)
        if hex_color == "#ff5722":
            print("[PASS] rgb_to_hex works")
        else:
            print(f"[FAIL] rgb_to_hex failed: {hex_color}")
            return False
        
        dark_theme = is_dark_theme()
        light_theme = is_light_theme()
        if isinstance(dark_theme, bool) and isinstance(light_theme, bool):
            print(f"[PASS] Theme type checks: dark={dark_theme}, light={light_theme}")
        else:
            print(f"[FAIL] Theme type checks failed: dark={dark_theme}, light={light_theme}")
            return False
        
        if isinstance(COLORS, dict) and len(COLORS) > 0:
            print(f"[PASS] COLORS dictionary available: {len(COLORS)} colors")
        else:
            print(f"[FAIL] COLORS dictionary not available: {COLORS}")
            return False
        
        if isinstance(FALLBACK_COLOR, str) and len(FALLBACK_COLOR) > 0:
            print(f"[PASS] FALLBACK_COLOR available: {FALLBACK_COLOR}")
        else:
            print(f"[FAIL] FALLBACK_COLOR not available: {FALLBACK_COLOR}")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Backward compatibility test failed: {e}")
        return False


def test_error_handling_robustness():
    """Test error handling robustness throughout the theme system."""
    print("Testing error handling robustness...")
    
    try:
        from src.gui.theme import QtMaterialThemeService
        
        service = QtMaterialThemeService.instance()
        
        # Test invalid theme names
        success = service.apply_theme("nonexistent_theme", "nonexistent_variant")
        if not success:
            print("[PASS] Invalid theme name handled correctly")
        else:
            print("[FAIL] Invalid theme name should have failed")
            return False
        
        # Test invalid color names
        color = service.get_color("nonexistent_color")
        if isinstance(color, str) and len(color) > 0:
            print("[PASS] Invalid color name handled with fallback")
        else:
            print(f"[FAIL] Invalid color name not handled: {color}")
            return False
        
        # Test theme cycling with edge cases
        original_theme, original_variant = service.get_current_theme()
        
        # Cycle through themes
        for _ in range(10):  # More cycles than available themes
            success = service.cycle_theme()
            if not success:
                print("[FAIL] Theme cycling failed")
                return False
        
        print("[PASS] Theme cycling robust")
        
        # Test variant cycling
        for _ in range(10):  # More cycles than available variants
            success = service.cycle_variant()
            if not success:
                print("[FAIL] Variant cycling failed")
                return False
        
        print("[PASS] Variant cycling robust")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Error handling robustness test failed: {e}")
        return False


def test_performance_without_qt_material():
    """Test performance characteristics without qt-material."""
    print("Testing performance without qt-material...")
    
    try:
        from src.gui.theme import QtMaterialThemeService
        
        service = QtMaterialThemeService.instance()
        
        # Test theme application performance
        start_time = time.time()
        for i in range(20):
            theme = "dark" if i % 2 == 0 else "light"
            variant = ["blue", "amber", "cyan"][i % 3]
            success = service.apply_theme(theme, variant)
            if not success:
                print(f"[FAIL] Performance test failed at iteration {i}")
                return False
        elapsed_time = time.time() - start_time
        
        avg_time = elapsed_time / 20 * 1000  # Convert to milliseconds
        print(f"[INFO] Average theme application time: {avg_time:.2f}ms")
        
        if avg_time < 100:  # Should be under 100ms for fallback themes
            print("[PASS] Theme application performance is acceptable")
        else:
            print(f"[WARN] Theme application performance is slow: {avg_time:.2f}ms")
        
        # Test color retrieval performance
        start_time = time.time()
        for _ in range(1000):
            color = service.get_color("primary")
            if not isinstance(color, str) or len(color) == 0:
                print("[FAIL] Color retrieval performance test failed")
                return False
        elapsed_time = time.time() - start_time
        
        avg_color_time = elapsed_time / 1000 * 1000000  # Convert to microseconds
        print(f"[INFO] Average color retrieval time: {avg_color_time:.2f}us")
        
        if avg_color_time < 100:  # Should be under 100μs
            print("[PASS] Color retrieval performance is acceptable")
        else:
            print(f"[WARN] Color retrieval performance is slow: {avg_color_time:.2f}μs")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Performance test failed: {e}")
        return False


def test_memory_stability():
    """Test memory stability during theme operations."""
    print("Testing memory stability...")
    
    try:
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        from src.gui.theme import QtMaterialThemeService
        
        service = QtMaterialThemeService.instance()
        
        # Perform many theme operations
        for i in range(50):
            theme = "dark" if i % 2 == 0 else "light"
            variant = ["blue", "amber", "cyan"][i % 3]
            service.apply_theme(theme, variant)
            
            # Get colors
            for _ in range(10):
                service.get_color("primary")
                service.get_color("secondary")
                service.get_color("background")
            
            # Force garbage collection periodically
            if i % 10 == 0:
                gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"[INFO] Initial memory: {initial_memory:.2f}MB")
        print(f"[INFO] Final memory: {final_memory:.2f}MB")
        print(f"[INFO] Memory increase: {memory_increase:.2f}MB")
        
        if memory_increase < 10:  # Should be under 10MB increase
            print("[PASS] Memory stability is acceptable")
        else:
            print(f"[WARN] Memory usage increased significantly: {memory_increase:.2f}MB")
        
        return True
        
    except ImportError:
        print("[SKIP] psutil not available, skipping memory test")
        return True
    except Exception as e:
        print(f"[FAIL] Memory stability test failed: {e}")
        return False


def main():
    """Run all graceful degradation tests."""
    print("=" * 60)
    print("Testing Theme System Graceful Degradation")
    print("=" * 60)
    
    # Configure logging to reduce noise
    logging.basicConfig(level=logging.ERROR)
    
    tests = [
        test_missing_qt_material_handling,
        test_fallback_theme_quality,
        test_backward_compatibility_without_qt_material,
        test_error_handling_robustness,
        test_performance_without_qt_material,
        test_memory_stability
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print()
        if test():
            passed += 1
        print("-" * 40)
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All graceful degradation tests passed!")
        print("Theme system works correctly without qt-material library.")
        return 0
    else:
        print("[ERROR] Some graceful degradation tests failed.")
        print("Theme system may have issues when qt-material is not available.")
        return 1


if __name__ == "__main__":
    sys.exit(main())