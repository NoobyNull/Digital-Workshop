#!/usr/bin/env python3
"""
Test to verify the theme consistency fix between main window and preferences dialog.

This test checks that both the main window and preferences dialog
apply the same qt-material theme styling.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication
from src.gui.main_window import MainWindow
from src.gui.preferences import PreferencesDialog
from src.gui.theme.simple_service import ThemeService


def test_theme_consistency():
    """Test that main window and preferences dialog have consistent themes."""
    print("🧪 Testing theme consistency fix...")
    
    # Create QApplication
    app = QApplication(sys.argv)
    
    # Initialize theme service
    theme_service = ThemeService.instance()
    
    # Apply a dark theme with blue variant
    print("📝 Applying dark blue theme...")
    theme_service.set_qt_material_variant("blue")
    success = theme_service.apply_theme("dark", "qt-material")
    
    if not success:
        print("❌ Failed to apply theme")
        return False
    
    # Create main window
    print("🏠 Creating main window...")
    main_window = MainWindow()
    
    # Check main window has stylesheet
    main_stylesheet = main_window.styleSheet()
    if not main_stylesheet:
        print("❌ Main window has no stylesheet")
        return False
    print("✅ Main window has stylesheet")
    
    # Create preferences dialog
    print("⚙️ Creating preferences dialog...")
    preferences = PreferencesDialog(parent=main_window)
    
    # Check preferences dialog has stylesheet
    pref_stylesheet = preferences.styleSheet()
    if not pref_stylesheet:
        print("❌ Preferences dialog has no stylesheet")
        return False
    print("✅ Preferences dialog has stylesheet")
    
    # Compare stylesheets
    if main_stylesheet == pref_stylesheet:
        print("✅ Theme consistency verified: Both have identical stylesheets")
    else:
        print("❌ Theme inconsistency: Stylesheets differ")
        print(f"Main window stylesheet length: {len(main_stylesheet)}")
        print(f"Preferences stylesheet length: {len(pref_stylesheet)}")
        return False
    
    # Test theme switching
    print("🔄 Testing theme switching to light...")
    theme_service.apply_theme("light", "qt-material")
    
    # Check if both windows update
    main_stylesheet_new = main_window.styleSheet()
    pref_stylesheet_new = preferences.styleSheet()
    
    if main_stylesheet_new == pref_stylesheet_new:
        print("✅ Theme switching consistency verified")
    else:
        print("❌ Theme switching inconsistency detected")
        return False
    
    # Clean up
    preferences.close()
    main_window.close()
    
    print("🎉 All theme consistency tests passed!")
    return True


if __name__ == "__main__":
    success = test_theme_consistency()
    if not success:
        print("\n❌ Theme consistency fix verification failed")
        sys.exit(1)
    else:
        print("\n✅ Theme consistency fix verification successful")
        sys.exit(0)