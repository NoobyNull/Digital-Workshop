#!/usr/bin/env python3
"""
Simple test script for Professional Color Themes Implementation
"""

import sys
import os
import traceback

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_theme_loader():
    """Test the theme loader functionality."""
    print("Testing Theme Loader...")
    
    try:
        from src.gui.theme.theme_loader import get_theme_loader
        
        # Test theme loader initialization
        loader = get_theme_loader()
        print("[PASS] Theme loader initialized successfully")
        
        # Test loading themes from JSON
        available_themes = loader.get_available_themes()
        print(f"[PASS] Loaded themes: {list(available_themes.keys())}")
        
        # Test light theme variants
        light_variants = loader.get_theme_variants("light")
        print(f"[PASS] Light theme variants: {list(light_variants.keys())}")
        
        # Test dark theme variants
        dark_variants = loader.get_theme_variants("dark")
        print(f"[PASS] Dark theme variants: {list(dark_variants.keys())}")
        
        # Test individual theme loading
        theme_colors = loader.get_theme_colors("light", "federal_blue")
        if theme_colors:
            print(f"[PASS] Federal Blue light theme colors loaded: primary={theme_colors.get('primary')}")
        else:
            print("[FAIL] Federal Blue light theme not found")
            return False
        
        # Test dark theme colors
        dark_colors = loader.get_theme_colors("dark", "federal_blue")
        if dark_colors:
            print(f"[PASS] Federal Blue dark theme colors loaded: primary={dark_colors.get('primary')}")
        else:
            print("[FAIL] Federal Blue dark theme not found")
            return False
        
        # Test all variant names
        all_variants = loader.get_all_variant_names()
        print(f"[PASS] All variant names: {all_variants}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Theme loader test failed: {e}")
        traceback.print_exc()
        return False


def test_qt_material_core():
    """Test the qt_material_core integration."""
    print("\nTesting Qt Material Core Integration...")
    
    try:
        from src.gui.theme.qt_material_core import QtMaterialThemeCore
        
        # Test core initialization
        core = QtMaterialThemeCore.instance()
        print("[PASS] QtMaterialThemeCore initialized successfully")
        
        # Test getting available themes
        available_themes = core.get_available_themes()
        print(f"[PASS] Available themes from core: {list(available_themes.keys())}")
        
        # Check if professional themes are loaded
        if "light" in available_themes and "federal_blue" in available_themes["light"]:
            print("[PASS] Federal Blue theme found in light themes")
        else:
            print("[FAIL] Federal Blue theme not found in light themes")
            return False
        
        if "dark" in available_themes and "federal_blue" in available_themes["dark"]:
            print("[PASS] Federal Blue theme found in dark themes")
        else:
            print("[FAIL] Federal Blue theme not found in dark themes")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Qt Material Core test failed: {e}")
        traceback.print_exc()
        return False


def test_qt_material_service():
    """Test the qt_material_service functionality."""
    print("\nTesting Qt Material Service...")
    
    try:
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        
        # Test service initialization
        service = QtMaterialThemeService.instance()
        print("[PASS] QtMaterialThemeService initialized successfully")
        
        # Test available themes
        available_themes = service.get_available_themes()
        print(f"[PASS] Available themes from service: {list(available_themes.keys())}")
        
        # Test getting variants
        light_variants = service.get_available_variants("light")
        dark_variants = service.get_available_variants("dark")
        auto_variants = service.get_available_variants("auto")
        
        print(f"[PASS] Light variants: {light_variants}")
        print(f"[PASS] Dark variants: {dark_variants}")
        print(f"[PASS] Auto variants: {auto_variants}")
        
        # Check if professional themes are available
        professional_themes = ["federal_blue", "emerald_slate", "steel_gray", 
                             "crimson_accent", "indigo_professional", "teal_modern"]
        
        missing_themes = []
        for theme in professional_themes:
            if theme not in auto_variants:
                missing_themes.append(theme)
        
        if missing_themes:
            print(f"[FAIL] Missing professional themes: {missing_themes}")
            return False
        else:
            print("[PASS] All professional themes available")
        
        # Test current theme
        current_theme, current_variant = service.get_current_theme()
        print(f"[PASS] Current theme: {current_theme}/{current_variant}")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Qt Material Service test failed: {e}")
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all theme tests."""
    print("Professional Themes Implementation Test Suite")
    print("=" * 50)
    
    tests = [
        ("Theme Loader", test_theme_loader),
        ("Qt Material Core", test_qt_material_core),
        ("Qt Material Service", test_qt_material_service)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"[FAIL] {test_name} test crashed: {e}")
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
        print("\n[SUCCESS] All tests passed! Professional themes implementation is working correctly.")
        return True
    else:
        print(f"\n[ERROR] {failed} test(s) failed. Please check the implementation.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)