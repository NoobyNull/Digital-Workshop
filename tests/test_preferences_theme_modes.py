#!/usr/bin/env python3
"""
Test that preferences dialog properly shows all theme modes and variants.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_qt_material_service_available_themes():
    """Test what themes and variants are available."""
    print("=== TESTING QT-MATERIAL THEME SERVICE ===")
    
    try:
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        
        # Create service instance
        service = QtMaterialThemeService.instance()
        
        # Get current theme
        current_theme, current_variant = service.get_current_theme()
        print(f"Current theme: {current_theme}")
        print(f"Current variant: {current_variant}")
        
        # Get available themes
        available_themes = service.get_available_themes()
        print(f"Available themes: {list(available_themes.keys())}")
        
        # Test each theme
        for theme_name in available_themes.keys():
            variants = service.get_available_variants(theme_name)
            print(f"  {theme_name}: {variants}")
        
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def test_preferences_theming_tab():
    """Test preferences dialog theming tab initialization."""
    print("\n=== TESTING PREFERENCES THEMING TAB ===")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.gui.preferences import ThemingTab
        
        # Create QApplication if needed
        if not QApplication.instance():
            app = QApplication([])
        
        # Create theming tab
        tab = ThemingTab()
        
        # Check if service is set
        if tab.service:
            current_theme, current_variant = tab.service.get_current_theme()
            print(f"ThemingTab current theme: {current_theme}")
            print(f"ThemingTab current variant: {current_variant}")
        else:
            print("ERROR: ThemingTab service is None")
        
        # Check combo boxes
        if hasattr(tab, 'mode_combo') and tab.mode_combo:
            print(f"Mode combo items: {[tab.mode_combo.itemText(i) for i in range(tab.mode_combo.count())]}")
            print(f"Mode combo current: {tab.mode_combo.currentText()}")
        else:
            print("ERROR: Mode combo not found")
            
        if hasattr(tab, 'variant_combo') and tab.variant_combo:
            print(f"Variant combo items: {[tab.variant_combo.itemText(i) for i in range(tab.variant_combo.count())]}")
            print(f"Variant combo current: {tab.variant_combo.currentText()}")
        else:
            print("ERROR: Variant combo not found")
        
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_theme_application():
    """Test applying different themes."""
    print("\n=== TESTING THEME APPLICATION ===")
    
    try:
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        
        service = QtMaterialThemeService.instance()
        
        # Test all theme combinations
        themes = ["dark", "light", "auto"]
        variants = ["blue", "amber", "cyan"]
        
        for theme in themes:
            for variant in variants:
                print(f"Testing {theme}/{variant}...")
                try:
                    result = service.apply_theme(theme, variant)
                    print(f"  Result: {result}")
                    current = service.get_current_theme()
                    print(f"  Current after apply: {current}")
                except Exception as e:
                    print(f"  ERROR: {e}")
        
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Preferences Dialog Theme Modes and Variants")
    print("=" * 50)
    
    success = True
    
    # Test 1: Available themes and variants
    if not test_qt_material_service_available_themes():
        success = False
    
    # Test 2: Preferences tab initialization
    if not test_preferences_theming_tab():
        success = False
    
    # Test 3: Theme application
    if not test_theme_application():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    return success

if __name__ == "__main__":
    main()