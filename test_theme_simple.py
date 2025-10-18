#!/usr/bin/env python3
"""
Simple theme application test.

Tests that applying a theme actually changes the QApplication stylesheet.
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt


def test_theme_application():
    """Test that theme application changes the stylesheet."""
    print("=" * 80)
    print("THEME APPLICATION TEST")
    print("=" * 80)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Check initial stylesheet
    initial_stylesheet = app.styleSheet()
    print(f"\nInitial app stylesheet length: {len(initial_stylesheet)}")
    print(f"Initial stylesheet (first 200 chars): {initial_stylesheet[:200]}")
    
    # Apply dark theme
    print("\n--- Applying Dark Theme ---")
    from src.gui.theme.simple_service import ThemeService
    service = ThemeService.instance()
    
    result = service.apply_theme("dark", "qt-material")
    print(f"Apply theme result: {result}")
    
    # Check stylesheet after applying theme
    after_dark_stylesheet = app.styleSheet()
    print(f"\nAfter dark theme stylesheet length: {len(after_dark_stylesheet)}")
    print(f"After dark stylesheet (first 200 chars): {after_dark_stylesheet[:200]}")
    
    if len(after_dark_stylesheet) > 0:
        print("✅ Dark theme stylesheet applied to QApplication")
    else:
        print("❌ Dark theme stylesheet NOT applied to QApplication")
        return False
    
    # Apply light theme
    print("\n--- Applying Light Theme ---")
    result = service.apply_theme("light", "qt-material")
    print(f"Apply theme result: {result}")
    
    # Check stylesheet after applying light theme
    after_light_stylesheet = app.styleSheet()
    print(f"\nAfter light theme stylesheet length: {len(after_light_stylesheet)}")
    print(f"After light stylesheet (first 200 chars): {after_light_stylesheet[:200]}")
    
    if len(after_light_stylesheet) > 0:
        print("✅ Light theme stylesheet applied to QApplication")
    else:
        print("❌ Light theme stylesheet NOT applied to QApplication")
        return False
    
    # Check if stylesheets are different
    if after_dark_stylesheet != after_light_stylesheet:
        print("\n✅ Dark and Light stylesheets are DIFFERENT")
        
        # Find differences
        dark_lines = after_dark_stylesheet.split('\n')
        light_lines = after_light_stylesheet.split('\n')
        
        print(f"\nDark theme has {len(dark_lines)} lines")
        print(f"Light theme has {len(light_lines)} lines")
        
        return True
    else:
        print("\n❌ Dark and Light stylesheets are IDENTICAL (no theme change)")
        return False


if __name__ == "__main__":
    try:
        success = test_theme_application()
        print("\n" + "=" * 80)
        if success:
            print("TEST PASSED ✅")
        else:
            print("TEST FAILED ❌")
        print("=" * 80)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

