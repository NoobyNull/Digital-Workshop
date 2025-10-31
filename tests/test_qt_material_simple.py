#!/usr/bin/env python3
"""
Simple test script for Qt-Material Takeover

This script tests the qt-material-only theme system without complex singleton testing.
"""

import sys
import time
import traceback
from typing import Dict, Any

def test_basic_imports() -> Dict[str, Any]:
    """Test that all qt-material modules can be imported without circular dependencies."""
    print("Testing basic imports...")
    results = {"success": True, "errors": [], "import_time": 0}
    
    start_time = time.time()
    
    try:
        # Test public API import only
        print("  Importing public API...")
        from src.gui.theme import (
            QtMaterialThemeService, VTKColorProvider, vtk_rgb,
            QtMaterialThemeSwitcher, QtMaterialColorPicker, QtMaterialThemeDialog,
            save_theme_to_settings, SPACING_4, SPACING_8, SPACING_12, SPACING_16
        )
        print("    OK: Public API imported successfully")
        
        # Test backward compatibility
        print("  Testing backward compatibility...")
        from src.gui.theme import ThemeService, ThemeSwitcher
        print("    OK: Backward compatibility aliases work")
        
    except Exception as e:
        results["success"] = False
        results["errors"].append(f"Import error: {str(e)}")
        results["errors"].append(traceback.format_exc())
        print(f"    FAIL: Import failed: {e}")
    
    results["import_time"] = (time.time() - start_time) * 1000
    print(f"  Import time: {results['import_time']:.2f}ms")
    
    return results


def test_vtk_integration() -> Dict[str, Any]:
    """Test VTK integration."""
    print("\nTesting VTK integration...")
    results = {"success": True, "errors": [], "vtk_colors": 0}
    
    try:
        from src.gui.theme import VTKColorProvider, vtk_rgb
        
        # Test VTK color provider
        print("  Getting VTK color provider...")
        provider = VTKColorProvider.instance()
        print("    OK: VTK color provider instance created")
        
        # Test VTK color access
        print("  Testing VTK color access...")
        vtk_color_names = [
            "canvas_bg", "canvas_top", "primary", "secondary", "edge_color",
            "grid_color", "ground_color", "model_surface", "light_color", "text"
        ]
        
        for color_name in vtk_color_names:
            vtk_color = provider.get_vtk_color(color_name)
            results["vtk_colors"] += 1
            print(f"    OK: {color_name}: {vtk_color}")
        
        # Test backward compatibility function
        print("  Testing vtk_rgb function...")
        test_color = vtk_rgb("canvas_bg")
        print(f"    OK: vtk_rgb('canvas_bg'): {test_color}")
        
        # Test all VTK colors
        print("  Testing all VTK colors...")
        all_vtk_colors = provider.get_all_vtk_colors()
        print(f"    OK: Total VTK colors available: {len(all_vtk_colors)}")
        
    except Exception as e:
        results["success"] = False
        results["errors"].append(f"VTK integration error: {str(e)}")
        results["errors"].append(traceback.format_exc())
        print(f"    FAIL: VTK integration test failed: {e}")
    
    return results


def test_theme_service_basic() -> Dict[str, Any]:
    """Test basic theme service functionality."""
    print("\nTesting basic theme service functionality...")
    results = {"success": True, "errors": [], "theme_changes": 0}
    
    try:
        from src.gui.theme import QtMaterialThemeService
        
        # Get service instance
        print("  Getting theme service instance...")
        service = QtMaterialThemeService.instance()
        print("    OK: Theme service instance created")
        
        # Test getting current theme
        print("  Getting current theme...")
        current_theme, current_variant = service.get_current_theme()
        print(f"    OK: Current theme: {current_theme}/{current_variant}")
        
        # Test getting available themes
        print("  Getting available themes...")
        available_themes = service.get_available_themes()
        print(f"    OK: Available themes: {list(available_themes.keys())}")
        
        # Test getting colors
        print("  Testing color access...")
        test_colors = ["primary", "secondary", "canvas_bg", "text"]
        for color_name in test_colors:
            color = service.get_color(color_name)
            print(f"    OK: {color_name}: {color}")
        
        # Test VTK colors
        print("  Testing VTK color access...")
        vtk_colors = ["canvas_bg", "light_color", "edge_color", "grid_color"]
        for color_name in vtk_colors:
            vtk_color = service.get_vtk_color(color_name)
            print(f"    OK: {color_name}: {vtk_color}")
        
    except Exception as e:
        results["success"] = False
        results["errors"].append(f"Theme service error: {str(e)}")
        results["errors"].append(traceback.format_exc())
        print(f"    FAIL: Theme service test failed: {e}")
    
    return results


def test_legacy_removal() -> Dict[str, Any]:
    """Test that legacy components are removed."""
    print("\nTesting legacy component removal...")
    results = {"success": True, "errors": []}
    
    try:
        # Test that ThemeManager is not available (should be removed)
        print("  Testing ThemeManager removal...")
        try:
            from src.gui.theme import ThemeManager
            results["success"] = False
            results["errors"].append("ThemeManager is still available - should be removed")
            print("    FAIL: ThemeManager is still available (should be removed)")
        except ImportError:
            print("    OK: ThemeManager is not available (correctly removed)")
        
        # Test that spacing constants are available (backward compatibility)
        print("  Testing spacing constants availability...")
        from src.gui.theme import SPACING_4, SPACING_8, SPACING_12, SPACING_16
        print(f"    OK: Spacing constants available: {SPACING_4}, {SPACING_8}, {SPACING_12}, {SPACING_16}")
        
        # Test that save_theme_to_settings function is available
        print("  Testing save_theme_to_settings function...")
        from src.gui.theme import save_theme_to_settings
        print("    OK: save_theme_to_settings function is available")
        
    except Exception as e:
        results["success"] = False
        results["errors"].append(f"Legacy removal test error: {str(e)}")
        results["errors"].append(traceback.format_exc())
        print(f"    FAIL: Legacy removal test failed: {e}")
    
    return results


def main():
    """Run all tests."""
    print("=" * 60)
    print("Qt-Material Takeover Simple Test Suite")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    test_results["imports"] = test_basic_imports()
    test_results["vtk_integration"] = test_vtk_integration()
    test_results["theme_service"] = test_theme_service_basic()
    test_results["legacy_removal"] = test_legacy_removal()
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result["success"])
    
    for test_name, result in test_results.items():
        status = "PASS" if result["success"] else "FAIL"
        print(f"{status}: {test_name}")
        
        if not result["success"] and result["errors"]:
            print("  Errors:")
            for error in result["errors"]:
                print(f"    {error}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("SUCCESS: All tests passed! Qt-material takeover is working.")
        print("\nKey achievements:")
        print("  - No circular dependency errors")
        print("  - VTK integration works correctly")
        print("  - Theme service functions properly")
        print("  - Legacy components removed")
        print("  - Backward compatibility maintained")
        return 0
    else:
        print("FAILURE: Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())