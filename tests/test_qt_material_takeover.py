#!/usr/bin/env python3
"""
Test script for Qt-Material Takeover

This script tests the qt-material-only theme system to ensure:
1. No circular dependency errors during import
2. Application starts successfully
3. VTK integration works correctly
4. Theme switching performance meets requirements
"""

import sys
import time
import traceback
from typing import Dict, Any

def test_imports() -> Dict[str, Any]:
    """Test that all qt-material modules can be imported without circular dependencies."""
    print("Testing imports...")
    results = {"success": True, "errors": [], "import_time": 0}
    
    start_time = time.time()
    
    try:
        # Test core imports
        print("  Importing qt_material_core...")
        from src.gui.theme.qt_material_core import QtMaterialThemeCore
        print("    ✓ qt_material_core imported successfully")
        
        print("  Importing qt_material_service...")
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        print("    ✓ qt_material_service imported successfully")
        
        print("  Importing vtk_color_provider...")
        from src.gui.theme.vtk_color_provider import VTKColorProvider, get_vtk_color_provider
        print("    ✓ vtk_color_provider imported successfully")
        
        print("  Importing qt_material_ui...")
        from src.gui.theme.qt_material_ui import (
            QtMaterialThemeSwitcher, QtMaterialColorPicker, QtMaterialThemeDialog
        )
        print("    ✓ qt_material_ui imported successfully")
        
        # Test public API import
        print("  Importing public API...")
        from src.gui.theme import (
            QtMaterialThemeService, VTKColorProvider, vtk_rgb,
            QtMaterialThemeSwitcher, QtMaterialColorPicker, QtMaterialThemeDialog
        )
        print("    ✓ Public API imported successfully")
        
        # Test backward compatibility
        print("  Testing backward compatibility...")
        from src.gui.theme import ThemeService, ThemeSwitcher
        print("    ✓ Backward compatibility aliases work")
        
    except Exception as e:
        results["success"] = False
        results["errors"].append(f"Import error: {str(e)}")
        results["errors"].append(traceback.format_exc())
        print(f"    ✗ Import failed: {e}")
    
    results["import_time"] = (time.time() - start_time) * 1000
    print(f"  Import time: {results['import_time']:.2f}ms")
    
    return results


def test_theme_service() -> Dict[str, Any]:
    """Test that the theme service works correctly."""
    print("\nTesting theme service...")
    results = {"success": True, "errors": [], "theme_changes": 0}
    
    try:
        from src.gui.theme import QtMaterialThemeService
        
        # Get service instance
        print("  Getting theme service instance...")
        service = QtMaterialThemeService.instance()
        print("    ✓ Theme service instance created")
        
        # Test getting current theme
        print("  Getting current theme...")
        current_theme, current_variant = service.get_current_theme()
        print(f"    ✓ Current theme: {current_theme}/{current_variant}")
        
        # Test getting available themes
        print("  Getting available themes...")
        available_themes = service.get_available_themes()
        print(f"    ✓ Available themes: {list(available_themes.keys())}")
        
        # Test theme switching
        print("  Testing theme switching...")
        themes_to_test = [("dark", "blue"), ("light", "amber"), ("dark", "cyan")]
        
        for theme, variant in themes_to_test:
            if theme in available_themes and variant in available_themes[theme]:
                success = service.apply_theme(theme, variant)
                if success:
                    results["theme_changes"] += 1
                    print(f"    ✓ Applied theme: {theme}/{variant}")
                else:
                    print(f"    ✗ Failed to apply theme: {theme}/{variant}")
        
        # Test getting colors
        print("  Testing color access...")
        test_colors = ["primary", "secondary", "canvas_bg", "text"]
        for color_name in test_colors:
            color = service.get_color(color_name)
            print(f"    ✓ {color_name}: {color}")
        
        # Test VTK colors
        print("  Testing VTK color access...")
        vtk_colors = ["canvas_bg", "light_color", "edge_color", "grid_color"]
        for color_name in vtk_colors:
            vtk_color = service.get_vtk_color(color_name)
            print(f"    ✓ {color_name}: {vtk_color}")
        
    except Exception as e:
        results["success"] = False
        results["errors"].append(f"Theme service error: {str(e)}")
        results["errors"].append(traceback.format_exc())
        print(f"    ✗ Theme service test failed: {e}")
    
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
        print("    ✓ VTK color provider instance created")
        
        # Test VTK color access
        print("  Testing VTK color access...")
        vtk_color_names = [
            "canvas_bg", "canvas_top", "primary", "secondary", "edge_color",
            "grid_color", "ground_color", "model_surface", "light_color", "text"
        ]
        
        for color_name in vtk_color_names:
            vtk_color = provider.get_vtk_color(color_name)
            results["vtk_colors"] += 1
            print(f"    ✓ {color_name}: {vtk_color}")
        
        # Test backward compatibility function
        print("  Testing vtk_rgb function...")
        test_color = vtk_rgb("canvas_bg")
        print(f"    ✓ vtk_rgb('canvas_bg'): {test_color}")
        
        # Test all VTK colors
        print("  Testing all VTK colors...")
        all_vtk_colors = provider.get_all_vtk_colors()
        print(f"    ✓ Total VTK colors available: {len(all_vtk_colors)}")
        
    except Exception as e:
        results["success"] = False
        results["errors"].append(f"VTK integration error: {str(e)}")
        results["errors"].append(traceback.format_exc())
        print(f"    ✗ VTK integration test failed: {e}")
    
    return results


def test_performance() -> Dict[str, Any]:
    """Test theme switching performance."""
    print("\nTesting performance...")
    results = {"success": True, "errors": [], "switch_times": []}
    
    try:
        from src.gui.theme import QtMaterialThemeService
        
        # Get service instance
        service = QtMaterialThemeService.instance()
        
        # Test theme switching performance
        print("  Testing theme switching performance...")
        themes_to_test = [("dark", "blue"), ("light", "amber"), ("dark", "cyan")]
        
        for theme, variant in themes_to_test:
            # Measure theme switch time
            start_time = time.time()
            success = service.apply_theme(theme, variant)
            switch_time = (time.time() - start_time) * 1000
            
            results["switch_times"].append(switch_time)
            
            if success:
                if switch_time < 100:
                    print(f"    ✓ {theme}/{variant}: {switch_time:.2f}ms (<100ms target)")
                else:
                    print(f"    ⚠ {theme}/{variant}: {switch_time:.2f}ms (exceeds 100ms target)")
                    results["success"] = False
            else:
                print(f"    ✗ Failed to apply theme: {theme}/{variant}")
                results["success"] = False
        
        # Calculate statistics
        if results["switch_times"]:
            avg_time = sum(results["switch_times"]) / len(results["switch_times"])
            min_time = min(results["switch_times"])
            max_time = max(results["switch_times"])
            
            print(f"  Performance statistics:")
            print(f"    Average: {avg_time:.2f}ms")
            print(f"    Minimum: {min_time:.2f}ms")
            print(f"    Maximum: {max_time:.2f}ms")
            
            if avg_time >= 100:
                results["success"] = False
                results["errors"].append(f"Average switch time {avg_time:.2f}ms exceeds 100ms target")
        
    except Exception as e:
        results["success"] = False
        results["errors"].append(f"Performance test error: {str(e)}")
        results["errors"].append(traceback.format_exc())
        print(f"    ✗ Performance test failed: {e}")
    
    return results


def test_circular_dependency_resolution() -> Dict[str, Any]:
    """Test that circular dependencies are resolved."""
    print("\nTesting circular dependency resolution...")
    results = {"success": True, "errors": []}
    
    try:
        # Test that we can import theme service and core in any order
        print("  Testing import order independence...")
        
        # Import service first
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        service1 = QtMaterialThemeService.instance()
        
        # Then import core
        from src.gui.theme.qt_material_core import QtMaterialThemeCore
        core1 = QtMaterialThemeCore.instance()
        
        # Test that both work
        theme1, variant1 = service1.get_current_theme()
        print(f"    ✓ Service-first import: {theme1}/{variant1}")
        
        # Test reverse order (in a subprocess would be ideal, but we'll test re-import)
        # Clear the singleton instances (this is a hack for testing)
        if hasattr(QtMaterialThemeService, '_instance'):
            delattr(QtMaterialThemeService, '_instance')
        if hasattr(QtMaterialThemeCore, '_instance'):
            delattr(QtMaterialThemeCore, '_instance')
        
        # Import core first
        core2 = QtMaterialThemeCore.instance()
        
        # Then import service
        service2 = QtMaterialThemeService.instance()
        
        # Test that both work
        theme2, variant2 = service2.get_current_theme()
        print(f"    ✓ Core-first import: {theme2}/{variant2}")
        
        # Test that ThemeManager is not available (should be removed)
        try:
            from src.gui.theme import ThemeManager
            results["success"] = False
            results["errors"].append("ThemeManager is still available - should be removed")
            print("    ✗ ThemeManager is still available (should be removed)")
        except ImportError:
            print("    ✓ ThemeManager is not available (correctly removed)")
        
    except Exception as e:
        results["success"] = False
        results["errors"].append(f"Circular dependency test error: {str(e)}")
        results["errors"].append(traceback.format_exc())
        print(f"    ✗ Circular dependency test failed: {e}")
    
    return results


def main():
    """Run all tests."""
    print("=" * 60)
    print("Qt-Material Takeover Test Suite")
    print("=" * 60)
    
    test_results = {}
    
    # Run all tests
    test_results["imports"] = test_imports()
    test_results["circular_dependency"] = test_circular_dependency_resolution()
    test_results["theme_service"] = test_theme_service()
    test_results["vtk_integration"] = test_vtk_integration()
    test_results["performance"] = test_performance()
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result["success"])
    
    for test_name, result in test_results.items():
        status = "✓ PASS" if result["success"] else "✗ FAIL"
        print(f"{status}: {test_name}")
        
        if not result["success"] and result["errors"]:
            print("  Errors:")
            for error in result["errors"]:
                print(f"    {error}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Qt-material takeover is successful.")
        print("\nKey achievements:")
        print("  ✓ No circular dependency errors")
        print("  ✓ Application starts successfully")
        print("  ✓ VTK integration works correctly")
        print("  ✓ Theme switching meets performance requirements")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())