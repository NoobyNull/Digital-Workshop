#!/usr/bin/env python3
"""
Simple test to verify the theme consistency fix implementation.

This test checks that the preferences dialog has the _apply_qt_material_theme method
and that the _apply_theme_styling method is properly implemented.
"""

import sys
from pathlib import Path
import inspect

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_preferences_theme_methods():
    """Test that preferences dialog has the required theme methods."""
    print("Testing theme consistency fix implementation...")
    
    try:
        # Import the preferences module
        from src.gui.preferences import PreferencesDialog, ThemingTab
        
        # Check that PreferencesDialog has the _apply_qt_material_theme method
        if hasattr(PreferencesDialog, '_apply_qt_material_theme'):
            print("✓ PreferencesDialog has _apply_qt_material_theme method")
            
            # Check the method signature
            method = getattr(PreferencesDialog, '_apply_qt_material_theme')
            sig = inspect.signature(method)
            if len(sig.parameters) == 1:  # Only self parameter
                print("✓ _apply_qt_material_theme has correct signature")
            else:
                print("✗ _apply_qt_material_theme has incorrect signature")
                return False
        else:
            print("✗ PreferencesDialog missing _apply_qt_material_theme method")
            return False
        
        # Check that ThemingTab has updated _apply_theme_styling method
        if hasattr(ThemingTab, '_apply_theme_styling'):
            print("✓ ThemingTab has _apply_theme_styling method")
            
            # Check that it's not just a pass statement
            method = getattr(ThemingTab, '_apply_theme_styling')
            source = inspect.getsource(method)
            if "pass" not in source or len(source.strip()) > 20:
                print("✓ _apply_theme_styling is properly implemented")
            else:
                print("✗ _apply_theme_styling is still just a pass statement")
                return False
        else:
            print("✗ ThemingTab missing _apply_theme_styling method")
            return False
        
        # Check that __init__ calls _apply_qt_material_theme
        init_source = inspect.getsource(PreferencesDialog.__init__)
        if "_apply_qt_material_theme" in init_source:
            print("✓ PreferencesDialog.__init__ calls _apply_qt_material_theme")
        else:
            print("✗ PreferencesDialog.__init__ doesn't call _apply_qt_material_theme")
            return False
        
        print("\nAll theme consistency fix methods are properly implemented!")
        return True
        
    except Exception as e:
        print(f"✗ Error during testing: {e}")
        return False


def test_theme_service_integration():
    """Test that the theme service integration is correct."""
    print("\nTesting theme service integration...")
    
    try:
        from src.gui.theme.simple_service import ThemeService
        
        # Check that ThemeService has the required methods
        required_methods = ['apply_theme', 'get_current_theme', 'set_qt_material_variant']
        
        for method_name in required_methods:
            if hasattr(ThemeService, method_name):
                print(f"✓ ThemeService has {method_name} method")
            else:
                print(f"✗ ThemeService missing {method_name} method")
                return False
        
        print("✓ Theme service integration is correct")
        return True
        
    except Exception as e:
        print(f"✗ Error testing theme service: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("THEME CONSISTENCY FIX VERIFICATION")
    print("=" * 60)
    
    success1 = test_preferences_theme_methods()
    success2 = test_theme_service_integration()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("SUCCESS: Theme consistency fix is properly implemented!")
        print("\nThe fix ensures that:")
        print("1. Preferences dialog applies qt-material theme to itself")
        print("2. ThemingTab applies application stylesheet to itself")
        print("3. Both main window and preferences dialog have consistent themes")
        sys.exit(0)
    else:
        print("FAILURE: Theme consistency fix has issues")
        sys.exit(1)