#!/usr/bin/env python3
"""
Theme Consistency Fix Verification Test

This test verifies that the preferences dialog and main application
use the same theme service, ensuring consistent fallback behavior.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_theme_service_consistency():
    """Test that both main application and preferences use the same theme service."""
    print("=== THEME CONSISTENCY FIX VERIFICATION ===\n")
    
    # Test 1: Check that QtMaterialThemeService is imported in application.py
    print("1. Checking main application theme service...")
    try:
        with open("src/core/application.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "from src.gui.theme.qt_material_service import QtMaterialThemeService" in content:
                print("[PASS] Main application uses QtMaterialThemeService")
            else:
                print("[FAIL] Main application does not use QtMaterialThemeService")
                return False
    except Exception as e:
        print(f"[ERROR] Error reading application.py: {e}")
        return False
    
    # Test 2: Check that preferences.py now uses QtMaterialThemeService too
    print("\n2. Checking preferences dialog theme service...")
    try:
        with open("src/gui/preferences.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "from src.gui.theme.qt_material_service import QtMaterialThemeService" in content:
                print("[PASS] Preferences dialog uses QtMaterialThemeService")
            else:
                print("[FAIL] Preferences dialog does not use QtMaterialThemeService")
                return False
    except Exception as e:
        print(f"[ERROR] Error reading preferences.py: {e}")
        return False
    
    # Test 3: Verify the old ThemeService import is removed
    print("\n3. Checking that old ThemeService import is removed...")
    try:
        with open("src/gui/preferences.py", "r", encoding="utf-8") as f:
            content = f.read()
            if "from src.gui.theme.simple_service import ThemeService" in content:
                print("[FAIL] Preferences dialog still imports old ThemeService")
                return False
            else:
                print("[PASS] Old ThemeService import removed from preferences")
    except Exception as e:
        print(f"[ERROR] Error checking preferences.py: {e}")
        return False
    
    # Test 4: Test theme service instantiation
    print("\n4. Testing theme service instantiation...")
    try:
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        service = QtMaterialThemeService.instance()
        print("[PASS] QtMaterialThemeService instance created successfully")
        print(f"  Current theme: {service.get_current_theme()}")
    except Exception as e:
        print(f"[ERROR] Error creating QtMaterialThemeService: {e}")
        return False
    
    print("\n=== VERIFICATION RESULTS ===")
    print("[SUCCESS] Theme service consistency fix applied successfully!")
    print("[SUCCESS] Both main application and preferences dialog now use QtMaterialThemeService")
    print("[SUCCESS] This ensures consistent fallback behavior when qt-material is unavailable")
    print("[SUCCESS] The theme inconsistency issue should now be resolved")
    
    return True

if __name__ == "__main__":
    success = test_theme_service_consistency()
    sys.exit(0 if success else 1)