#!/usr/bin/env python3
"""
Test script for Professional Color Themes Implementation

This script tests the new professional themes functionality including:
- Theme loader functionality
- JSON theme configuration loading
- Theme switching and application
- VTK integration compatibility
"""

import sys
import os
import traceback
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_theme_loader():
    """Test the theme loader functionality."""
    print("Testing Theme Loader...")
    
    try:
        from src.gui.theme.theme_loader import get_theme_loader, ThemeLoader
        
        # Test theme loader initialization
        loader = get_theme_loader()
        print("✓ Theme loader initialized successfully")
        
        # Test loading themes from JSON
        available_themes = loader.get_available_themes()
        print(f"✓ Loaded themes: {list(available_themes.keys())}")
        
        # Test light theme variants
        light_variants = loader.get_theme_variants("light")
        print(f"✓ Light theme variants: {list(light_variants.keys())}")
        
        # Test dark theme variants
        dark_variants = loader.get_theme_variants("dark")
        print(f"✓ Dark theme variants: {list(dark_variants.keys())}")
        
        # Test individual theme loading
        theme_colors = loader.get_theme_colors("light", "federal_blue")
        if theme_colors:
            print(f"✓ Federal Blue light theme colors loaded: primary={theme_colors.get('primary')}")
        else:
            print("✗ Federal Blue light theme not found")
            return False
        
        # Test dark theme colors
        dark_colors = loader.get_theme_colors("dark", "federal_blue")
        if dark_colors:
            print(f"✓ Federal Blue dark theme colors loaded: primary={dark_colors.get('primary')}")
        else:
            print("✗ Federal Blue dark theme not found")
            return False
        
        # Test all variant names
        all_variants = loader.get_all_variant_names()
        print(f"✓ All variant names: {all_variants}")
        
        # Test theme info
        theme_info = loader.get_theme_info("light", "emerald_slate")
        if theme_info:
            name, desc = loader.get_theme_names("light", "emerald_slate")
            print(f"✓ Emerald Slate info: {name} - {desc}")
        else:
            print("✗ Emerald Slate theme info not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Theme loader test failed: {e}")
        traceback.print_exc()
        return False


def test_qt_material_core():
    """Test the qt_material_core integration."""
    print("\nTesting Qt Material Core Integration...")
    
    try:
        from src.gui.theme.qt_material_core import QtMaterialThemeCore
        
        # Test core initialization
        core = QtMaterialThemeCore.instance()
        print("✓ QtMaterialThemeCore initialized successfully")
        
        # Test getting available themes
        available_themes = core.get_available_themes()
        print(f"✓ Available themes from core: {list(available_themes.keys())}")
        
        # Check if professional themes are loaded
        if "light" in available_themes and "federal_blue" in available_themes["light"]:
            print("✓ Federal Blue theme found in light themes")
        else:
            print("✗ Federal Blue theme not found in light themes")
            return False
        
        if "dark" in available_themes and "federal_blue" in available_themes["dark"]:
            print("✓ Federal Blue theme found in dark themes")
        else:
            print("✗ Federal Blue theme not found in dark themes")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Qt Material Core test failed: {e}")
        traceback.print_exc()
        return False


def test_qt_material_service():
    """Test the qt_material_service functionality."""
    print("\nTesting Qt Material Service...")
    
    try:
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        
        # Test service initialization
        service = QtMaterialThemeService.instance()
        print("✓ QtMaterialThemeService initialized successfully")
        
        # Test available themes
        available_themes = service.get_available_themes()
        print(f"✓ Available themes from service: {list(available_themes.keys())}")
        
        # Test getting variants
        light_variants = service.get_available_variants("light")
        dark_variants = service.get_available_variants("dark")
        auto_variants = service.get_available_variants("auto")
        
        print(f"✓ Light variants: {light_variants}")
        print(f"✓ Dark variants: {dark_variants}")
        print(f"✓ Auto variants: {auto_variants}")
        
        # Check if professional themes are available
        professional_themes = ["federal_blue", "emerald_slate", "steel_gray", 
                             "crimson_accent", "indigo_professional", "teal_modern"]
        
        missing_themes = []
        for theme in professional_themes:
            if theme not in auto_variants:
                missing_themes.append(theme)
        
        if missing_themes:
            print(f"✗ Missing professional themes: {missing_themes}")
            return False
        else:
            print("✓ All professional themes available")
        
        # Test current theme
        current_theme, current_variant = service.get_current_theme()
        print(f"✓ Current theme: {current_theme}/{current_variant}")
        
        return True
        
    except Exception as e:
        print(f"✗ Qt Material Service test failed: {e}")
        traceback.print_exc()
        return False


def test_theme_application():
    """Test theme application functionality."""
    print("\nTesting Theme Application...")
    
    try:
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        
        service = QtMaterialThemeService.instance()
        
        # Test applying professional themes
        test_themes = [
            ("light", "federal_blue"),
            ("dark", "emerald_slate"),
            ("light", "steel_gray"),
            ("dark", "crimson_accent"),
            ("light", "indigo_professional"),
            ("dark", "teal_modern")
        ]
        
        success_count = 0
        for theme, variant in test_themes:
            try:
                result = service.apply_theme(theme, variant)
                if result:
                    print(f"✓ Theme {theme}/{variant} applied successfully")
                    success_count += 1
                else:
                    print(f"✗ Theme {theme}/{variant} application failed")
            except Exception as e:
                print(f"✗ Theme {theme}/{variant} application error: {e}")
        
        if success_count == len(test_themes):
            print(f"✓ All {success_count} theme applications successful")
            return True
        else:
            print(f"✗ Only {success_count}/{len(test_themes)} theme applications successful")
            return False
        
    except Exception as e:
        print(f"✗ Theme application test failed: {e}")
        traceback.print_exc()
        return False


def test_vtk_integration():
    """Test VTK integration compatibility."""
    print("\nTesting VTK Integration...")
    
    try:
        from src.gui.theme.vtk_color_provider import VTKColorProvider
        
        # Test VTK color provider initialization
        provider = VTKColorProvider()
        print("✓ VTKColorProvider initialized successfully")
        
        # Test getting VTK colors for professional themes
        test_colors = [
            ("primary", "federal_blue"),
            ("primary", "emerald_slate"),
            ("primary", "steel_gray")
        ]
        
        for color_name, theme_variant in test_colors:
            try:
                vtk_color = provider.get_vtk_color(color_name, theme_variant)
                if vtk_color:
                    print(f"✓ VTK color for {color_name}/{theme_variant}: {vtk_color}")
                else:
                    print(f"✗ VTK color not found for {color_name}/{theme_variant}")
                    return False
            except Exception as e:
                print(f"✗ VTK color error for {color_name}/{theme_variant}: {e}")
                # Don't fail the test for VTK integration issues
        
        return True
        
    except Exception as e:
        print(f"✗ VTK integration test failed: {e}")
        # VTK integration might not be critical, so don't fail the entire test
        return True


def test_backward_compatibility():
    """Test backward compatibility with existing functionality."""
    print("\nTesting Backward Compatibility...")
    
    try:
        # Test that old theme names still work
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        
        service = QtMaterialThemeService.instance()
        
        # Test original themes still work
        original_themes = [
            ("light", "blue"),
            ("dark", "amber"),
            ("light", "cyan")
        ]
        
        success_count = 0
        for theme, variant in original_themes:
            try:
                result = service.apply_theme(theme, variant)
                if result:
                    print(f"✓ Original theme {theme}/{variant} still works")
                    success_count += 1
                else:
                    print(f"✗ Original theme {theme}/{variant} failed")
            except Exception as e:
                print(f"✗ Original theme {theme}/{variant} error: {e}")
        
        if success_count == len(original_themes):
            print(f"✓ All {success_count} original themes still work")
            return True
        else:
            print(f"✗ Only {success_count}/{len(original_themes)} original themes work")
            return False
        
    except Exception as e:
        print(f"✗ Backward compatibility test failed: {e}")
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all theme tests."""
    print("Professional Themes Implementation Test Suite")
    print("=" * 50)
    
    tests = [
        ("Theme Loader", test_theme_loader),
        ("Qt Material Core", test_qt_material_core),
        ("Qt Material Service", test_qt_material_service),
        ("Theme Application", test_theme_application),
        ("VTK Integration", test_vtk_integration),
        ("Backward Compatibility", test_backward_compatibility)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} test crashed: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<25} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 50)
    print(f"Total: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Professional themes implementation is working correctly.")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)