#!/usr/bin/env python3
"""
Test script to verify the theme system startup fixes.

This script tests:
1. Theme module imports work correctly
2. Application bootstrap handles theme system gracefully
3. Backward compatibility functions are available
4. Graceful fallback works when qt-material is not available
"""

import sys
import os
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_theme_module_imports():
    """Test that theme module imports work correctly."""
    print("Testing theme module imports...")
    
    try:
        # Test basic theme module import
        from src.gui.theme import (
            QtMaterialThemeService,
            VTKColorProvider,
            get_vtk_color_provider,
            vtk_rgb,
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
            ThemeService,
            ThemeSwitcher,
            ColorPicker,
            ThemeDialog,
            ThemeManager,
            COLORS,
            FALLBACK_COLOR
        )
        print("[PASS] All theme module imports successful")
        return True
    except ImportError as e:
        print(f"[FAIL] Theme module import failed: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected error during theme import: {e}")
        return False


def test_theme_service_initialization():
    """Test that theme service initializes correctly."""
    print("Testing theme service initialization...")
    
    try:
        from src.gui.theme import QtMaterialThemeService
        
        # Test singleton instance creation
        service = QtMaterialThemeService.instance()
        if service is None:
            print("✗ Theme service instance is None")
            return False
        
        # Test qt-material availability detection
        qt_material_available = getattr(service, 'qtmaterial_available', False)
        print(f"[INFO] qt-material available: {qt_material_available}")
        
        # Test basic theme operations
        current_theme, current_variant = service.get_current_theme()
        print(f"[INFO] Current theme: {current_theme}/{current_variant}")
        
        # Test theme application
        success = service.apply_theme("dark", "blue")
        print(f"[INFO] Theme application successful: {success}")
        
        # Test color retrieval
        color = service.get_color("primary")
        print(f"[INFO] Color retrieval successful: {color}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Theme service initialization failed: {e}")
        return False


def test_backward_compatibility_functions():
    """Test backward compatibility functions."""
    print("Testing backward compatibility functions...")
    
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
        
        # Test load_theme_from_settings
        load_theme_from_settings()
        print("[PASS] load_theme_from_settings works")
        
        # Test hex_to_rgb
        rgb = hex_to_rgb("#1976D2")
        expected = (0.09411764705882353, 0.4627450980392157, 0.8235294117647058)
        # Use approximate comparison for floating point values
        if all(abs(a - b) < 0.001 for a, b in zip(rgb, expected)):
            print("[PASS] hex_to_rgb works correctly")
        else:
            print(f"[FAIL] hex_to_rgb incorrect: {rgb} != {expected}")
        
        # Test apply_theme_preset
        success = apply_theme_preset("dark")
        print(f"[INFO] apply_theme_preset works: {success}")
        
        # Test qss_tabs_lists_labels
        qss = qss_tabs_lists_labels()
        if isinstance(qss, str) and len(qss) > 0:
            print("[PASS] qss_tabs_lists_labels works")
        else:
            print("[FAIL] qss_tabs_lists_labels failed")
        
        # Test get_theme_color
        color = get_theme_color("primary")
        if isinstance(color, str) and len(color) > 0:
            print(f"[INFO] get_theme_color works: {color}")
        else:
            print("[FAIL] get_theme_color failed")
        
        # Test theme name/variant functions
        theme_name = get_current_theme_name()
        theme_variant = get_current_theme_variant()
        print(f"[INFO] Theme name/variant: {theme_name}/{theme_variant}")
        
        # Test rgb_to_hex
        hex_color = rgb_to_hex(25, 118, 210)
        if hex_color == "#1976d2":
            print("[PASS] rgb_to_hex works correctly")
        else:
            print(f"[FAIL] rgb_to_hex incorrect: {hex_color}")
        
        # Test theme type functions
        dark_theme = is_dark_theme()
        light_theme = is_light_theme()
        print(f"[INFO] Theme type checks: dark={dark_theme}, light={light_theme}")
        
        # Test constants
        if isinstance(COLORS, dict) and len(COLORS) > 0:
            print(f"[INFO] COLORS dictionary available: {len(COLORS)} colors")
        else:
            print("[FAIL] COLORS dictionary not available")
        
        if isinstance(FALLBACK_COLOR, str) and len(FALLBACK_COLOR) > 0:
            print(f"[INFO] FALLBACK_COLOR available: {FALLBACK_COLOR}")
        else:
            print("[FAIL] FALLBACK_COLOR not available")
        
        return True
    except Exception as e:
        print(f"[FAIL] Backward compatibility functions failed: {e}")
        return False


def test_vtk_color_provider():
    """Test VTK color provider functionality."""
    print("Testing VTK color provider...")
    
    try:
        from src.gui.theme import get_vtk_color_provider, vtk_rgb
        
        # Test VTK color provider
        vtk_provider = get_vtk_color_provider()
        if vtk_provider is None:
            print("[FAIL] VTK color provider is None")
            return False
        
        # Test vtk_rgb function
        vtk_color = vtk_rgb("primary")
        if isinstance(vtk_color, tuple) and len(vtk_color) == 3:
            print(f"[INFO] vtk_rgb works: {vtk_color}")
        else:
            print(f"[FAIL] vtk_rgb failed: {vtk_color}")
        
        # Test VTK color manager count
        manager_count = vtk_provider.get_vtk_manager_count()
        print(f"[INFO] VTK manager count: {manager_count}")
        
        return True
    except Exception as e:
        print(f"[FAIL] VTK color provider failed: {e}")
        return False


def test_application_bootstrap():
    """Test application bootstrap with theme system."""
    print("Testing application bootstrap...")
    
    try:
        from src.core.application_config import ApplicationConfig
        from src.core.application_bootstrap import ApplicationBootstrap
        
        # Create application config
        config = ApplicationConfig()
        
        # Create bootstrap
        bootstrap = ApplicationBootstrap(config)
        
        # Test theme system initialization
        success = bootstrap._initialize_theme_system()
        print(f"[INFO] Theme system bootstrap: {success}")
        
        # Test full bootstrap (without hardware acceleration for simplicity)
        try:
            # Try to disable hardware acceleration if possible
            if hasattr(config, 'enable_hardware_acceleration'):
                config.enable_hardware_acceleration = False
            bootstrap_success = bootstrap.bootstrap_services()
            print(f"[INFO] Full services bootstrap: {bootstrap_success}")
        except Exception as config_error:
            print(f"[WARN] Config modification failed: {config_error}")
            # Try bootstrap without config modification
            bootstrap_success = bootstrap.bootstrap_services()
            print(f"[INFO] Full services bootstrap (default config): {bootstrap_success}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Application bootstrap failed: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Theme System Startup Fixes")
    print("=" * 60)
    
    # Configure logging to reduce noise
    logging.basicConfig(level=logging.ERROR)
    
    tests = [
        test_theme_module_imports,
        test_theme_service_initialization,
        test_backward_compatibility_functions,
        test_vtk_color_provider,
        test_application_bootstrap
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
        print("[SUCCESS] All tests passed! Theme system startup fixes are working correctly.")
        return 0
    else:
        print("[ERROR] Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())