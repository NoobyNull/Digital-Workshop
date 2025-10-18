#!/usr/bin/env python3
"""
Test that theme changes update the stylesheet on existing windows.
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from PySide6.QtWidgets import QApplication


def test_theme_update():
    """Test that changing theme updates the stylesheet on existing windows."""
    print("=" * 80)
    print("THEME UPDATE TEST")
    print("=" * 80)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Apply dark theme
    print("\n--- Applying Dark Theme ---")
    from src.gui.theme.simple_service import ThemeService
    service = ThemeService.instance()
    result = service.apply_theme("dark", "qt-material")
    print(f"Apply dark theme result: {result}")
    
    app_stylesheet_dark = app.styleSheet()
    print(f"App stylesheet length (dark): {len(app_stylesheet_dark)}")
    
    # Create main window
    print("\n--- Creating Main Window ---")
    from src.gui.main_window import MainWindow
    main_window = MainWindow()
    
    main_window_stylesheet_dark = main_window.styleSheet()
    print(f"Main window stylesheet length (dark): {len(main_window_stylesheet_dark)}")
    
    # Now change to light theme
    print("\n--- Changing to Light Theme ---")
    result = service.apply_theme("light", "qt-material")
    print(f"Apply light theme result: {result}")

    app_stylesheet_light = app.styleSheet()
    print(f"App stylesheet length (light): {len(app_stylesheet_light)}")

    # Check if main window stylesheet was updated (before calling _on_theme_changed)
    main_window_stylesheet_light_before = main_window.styleSheet()
    print(f"Main window stylesheet length (light, before update): {len(main_window_stylesheet_light_before)}")

    # Now manually call the update method (simulating what happens when theme_changed signal is emitted)
    print("\n--- Calling _on_theme_changed to update main window ---")
    main_window._on_theme_changed()

    # Check if main window stylesheet was updated (after calling _on_theme_changed)
    main_window_stylesheet_light = main_window.styleSheet()
    print(f"Main window stylesheet length (light, after update): {len(main_window_stylesheet_light)}")
    
    print("\n--- Analysis ---")
    print(f"App stylesheet changed: {app_stylesheet_dark != app_stylesheet_light}")
    print(f"Main window stylesheet changed: {main_window_stylesheet_dark != main_window_stylesheet_light}")
    
    if app_stylesheet_dark != app_stylesheet_light:
        print("[PASS] App stylesheet DID change")
    else:
        print("[FAIL] App stylesheet did NOT change")
        return False
    
    if main_window_stylesheet_dark != main_window_stylesheet_light:
        print("[PASS] Main window stylesheet DID change")
        return True
    else:
        print("[FAIL] Main window stylesheet did NOT change")
        print("       This is the problem - the main window is not getting updated!")
        return False


if __name__ == "__main__":
    try:
        success = test_theme_update()
        print("\n" + "=" * 80)
        if success:
            print("TEST PASSED - Theme updates work correctly")
        else:
            print("TEST FAILED - Theme updates are NOT working")
        print("=" * 80)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nTest failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

