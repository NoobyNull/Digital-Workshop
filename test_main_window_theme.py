#!/usr/bin/env python3
"""
Test that main window gets the theme stylesheet.
"""

import sys
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from PySide6.QtWidgets import QApplication


def test_main_window_theme():
    """Test that main window inherits the theme stylesheet."""
    print("=" * 80)
    print("MAIN WINDOW THEME INHERITANCE TEST")
    print("=" * 80)
    
    # Create application
    app = QApplication(sys.argv)
    
    # Apply dark theme BEFORE creating main window
    print("\n--- Applying Dark Theme ---")
    from src.gui.theme.simple_service import ThemeService
    service = ThemeService.instance()
    result = service.apply_theme("dark", "qt-material")
    print(f"Apply theme result: {result}")
    
    app_stylesheet = app.styleSheet()
    print(f"App stylesheet length: {len(app_stylesheet)}")
    
    # Now create main window
    print("\n--- Creating Main Window ---")
    from src.gui.main_window import MainWindow
    main_window = MainWindow()
    
    # Check main window stylesheet
    main_window_stylesheet = main_window.styleSheet()
    print(f"Main window stylesheet length: {len(main_window_stylesheet)}")
    
    if len(main_window_stylesheet) > 0:
        print("[PASS] Main window HAS a stylesheet")
        print(f"Main window stylesheet (first 200 chars): {main_window_stylesheet[:200]}")
    else:
        print("[FAIL] Main window HAS NO stylesheet")

    # Check if main window stylesheet matches app stylesheet
    if main_window_stylesheet == app_stylesheet:
        print("[PASS] Main window stylesheet MATCHES app stylesheet")
        return True
    elif len(main_window_stylesheet) > 0 and len(app_stylesheet) > 0:
        print("[WARN] Main window has stylesheet but it's DIFFERENT from app stylesheet")
        print(f"   App stylesheet length: {len(app_stylesheet)}")
        print(f"   Main window stylesheet length: {len(main_window_stylesheet)}")
        return False
    else:
        print("[FAIL] Main window stylesheet is EMPTY")
        return False


if __name__ == "__main__":
    try:
        success = test_main_window_theme()
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

