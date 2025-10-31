#!/usr/bin/env python3
"""
Test default theme behavior on startup.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_default_theme_initialization():
    """Test what happens when theme service is first initialized."""
    print("=== TESTING DEFAULT THEME INITIALIZATION ===")
    
    try:
        # Reset singleton instance to test fresh initialization
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        QtMaterialThemeService._instance = None
        
        # Create new instance (fresh start)
        service = QtMaterialThemeService.instance()
        
        # Check what the current theme is
        current_theme, current_variant = service.get_current_theme()
        print(f"Default theme after initialization: {current_theme}")
        print(f"Default variant after initialization: {current_variant}")
        
        # Check what themes are available
        available_themes = service.get_available_themes()
        print(f"Available themes: {list(available_themes.keys())}")
        
        # Check what settings are saved
        print(f"Settings values:")
        settings = service.settings
        print(f"  theme: {settings.value('theme', 'NOT_SET')}")
        print(f"  variant: {settings.value('variant', 'NOT_SET')}")
        print(f"  qt_material_variant: {settings.value('qt_material_variant', 'NOT_SET')}")
        
        # Test resetting to default
        print("\nTesting reset_to_default()...")
        result = service.reset_to_default()
        print(f"reset_to_default() result: {result}")
        
        new_theme, new_variant = service.get_current_theme()
        print(f"After reset - theme: {new_theme}, variant: {new_variant}")
        
        # Test applying each theme combination
        print("\nTesting each theme combination:")
        themes = ["dark", "light", "auto"]
        variants = ["blue", "amber", "cyan"]
        
        for theme in themes:
            for variant in variants:
                result = service.apply_theme(theme, variant)
                applied_theme, applied_variant = service.get_current_theme()
                print(f"  apply_theme('{theme}', '{variant}') -> {result}, current: {applied_theme}/{applied_variant}")
        
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_theme_application_without_qt_material():
    """Test theme application when qt-material library is not available."""
    print("\n=== TESTING THEME APPLICATION WITHOUT QT-MATERIAL ===")
    
    try:
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        
        service = QtMaterialThemeService.instance()
        
        # Check if qt-material is available
        print(f"qt-material available: {service.qtmaterial_available}")
        
        # Try applying dark theme
        print("Applying dark/blue theme...")
        result = service.apply_theme("dark", "blue")
        print(f"Apply result: {result}")
        
        current_theme, current_variant = service.get_current_theme()
        print(f"Current after apply: {current_theme}/{current_variant}")
        
        # Check application stylesheet
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            stylesheet = app.styleSheet()
            print(f"Application has stylesheet: {len(stylesheet) > 0}")
            if len(stylesheet) > 0:
                print(f"Stylesheet length: {len(stylesheet)} characters")
                # Print first few lines
                lines = stylesheet.split('\n')[:5]
                for i, line in enumerate(lines, 1):
                    print(f"  Line {i}: {line[:50]}...")
        else:
            print("No QApplication instance found")
        
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Testing Default Theme Behavior")
    print("=" * 40)
    
    success = True
    
    # Test 1: Default theme initialization
    if not test_default_theme_initialization():
        success = False
    
    # Test 2: Theme application without qt-material
    if not test_theme_application_without_qt_material():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("All tests completed!")
    else:
        print("Some tests failed!")
    
    return success

if __name__ == "__main__":
    main()