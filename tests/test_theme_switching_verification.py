#!/usr/bin/env python3
"""
Theme Switching Functionality Verification Test

This test verifies that the professional themes can be applied and switched between correctly.
"""

import sys
import os
import traceback

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_theme_switching():
    """Test theme switching functionality."""
    print("Testing Theme Switching Functionality...")
    
    try:
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        
        # Get service instance
        service = QtMaterialThemeService.instance()
        print("[PASS] QtMaterialThemeService instance obtained")
        
        # Professional themes to test
        professional_themes = [
            ("light", "federal_blue"),
            ("dark", "emerald_slate"), 
            ("light", "steel_gray"),
            ("dark", "crimson_accent"),
            ("light", "indigo_professional"),
            ("dark", "teal_modern")
        ]
        
        successful_switches = 0
        failed_switches = 0
        
        print("\nTesting theme switching for all professional themes...")
        
        for theme, variant in professional_themes:
            try:
                # Apply theme
                result = service.apply_theme(theme, variant)
                if result:
                    # Verify current theme
                    current_theme, current_variant = service.get_current_theme()
                    if current_theme == theme and current_variant == variant:
                        print(f"[PASS] Switched to {theme}/{current_variant}")
                        successful_switches += 1
                    else:
                        print(f"[FAIL] Theme switched but current state incorrect: expected {theme}/{variant}, got {current_theme}/{current_variant}")
                        failed_switches += 1
                else:
                    print(f"[FAIL] Failed to apply theme {theme}/{variant}")
                    failed_switches += 1
                    
            except Exception as e:
                print(f"[FAIL] Error switching to {theme}/{variant}: {e}")
                failed_switches += 1
        
        print(f"\nTheme Switching Results:")
        print(f"  Successful switches: {successful_switches}")
        print(f"  Failed switches: {failed_switches}")
        print(f"  Total attempts: {len(professional_themes)}")
        
        return successful_switches == len(professional_themes)
        
    except Exception as e:
        print(f"[FAIL] Theme switching test failed: {e}")
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Test that original themes still work."""
    print("\nTesting Backward Compatibility...")
    
    try:
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        
        service = QtMaterialThemeService.instance()
        
        # Test original themes
        original_themes = [
            ("light", "blue"),
            ("dark", "amber"),
            ("light", "cyan")
        ]
        
        successful_switches = 0
        
        for theme, variant in original_themes:
            try:
                result = service.apply_theme(theme, variant)
                if result:
                    current_theme, current_variant = service.get_current_theme()
                    if current_theme == theme and current_variant == variant:
                        print(f"[PASS] Original theme {theme}/{variant} works correctly")
                        successful_switches += 1
                    else:
                        print(f"[FAIL] Original theme {theme}/{variant} state incorrect")
                else:
                    print(f"[FAIL] Failed to apply original theme {theme}/{variant}")
            except Exception as e:
                print(f"[FAIL] Error with original theme {theme}/{variant}: {e}")
        
        print(f"Backward compatibility: {successful_switches}/{len(original_themes)} original themes work")
        return successful_switches == len(original_themes)
        
    except Exception as e:
        print(f"[FAIL] Backward compatibility test failed: {e}")
        return False


def run_verification_tests():
    """Run all verification tests."""
    print("Professional Themes Switching Verification")
    print("=" * 50)
    
    tests = [
        ("Theme Switching", test_theme_switching),
        ("Backward Compatibility", test_backward_compatibility)
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
    print("VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<30} {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 50)
    print(f"Total: {len(results)} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n[SUCCESS] All verification tests passed! Professional themes implementation is complete and working.")
        return True
    else:
        print(f"\n[ERROR] {failed} verification test(s) failed.")
        return False


if __name__ == "__main__":
    success = run_verification_tests()
    sys.exit(0 if success else 1)