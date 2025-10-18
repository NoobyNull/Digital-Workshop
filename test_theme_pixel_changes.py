#!/usr/bin/env python3
"""
Pixel-based theme change detection test.

This test captures pixel colors before and after clicking the theme button
to verify that the theme actually changes the UI colors.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent
sys.path.insert(0, str(parent_dir))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QScreen
from src.main import main as app_main
from src.gui.main_window import MainWindow


def capture_pixel_color(x: int, y: int) -> tuple:
    """Capture the color of a pixel at (x, y) on the screen."""
    try:
        screen = QApplication.primaryScreen()
        if not screen:
            return None
        
        # Capture a small region around the pixel
        pixmap = screen.grabWindow(0, x, y, 1, 1)
        image = pixmap.toImage()
        
        if image.isNull():
            return None
        
        # Get the color at (0, 0) of the captured image
        color = image.pixelColor(0, 0)
        return (color.red(), color.green(), color.blue())
    except Exception as e:
        print(f"Error capturing pixel: {e}")
        return None


def test_theme_pixel_changes():
    """Test that theme changes actually change pixel colors."""
    print("=" * 80)
    print("PIXEL-BASED THEME CHANGE TEST")
    print("=" * 80)
    
    # Create application
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Import and create main window
    from src.gui.main_window import MainWindow
    main_window = MainWindow()
    main_window.show()
    
    # Process events to ensure window is fully rendered
    app.processEvents()
    time.sleep(1)
    
    # Get window geometry
    geometry = main_window.geometry()
    window_x = geometry.x()
    window_y = geometry.y()
    window_width = geometry.width()
    window_height = geometry.height()
    
    print(f"\nWindow geometry: x={window_x}, y={window_y}, w={window_width}, h={window_height}")
    
    # Capture pixel color at center of window (should be background)
    center_x = window_x + window_width // 2
    center_y = window_y + window_height // 2
    
    print(f"\nCapturing pixel at center: ({center_x}, {center_y})")
    
    # Capture initial color (should be light mode by default)
    initial_color = capture_pixel_color(center_x, center_y)
    print(f"Initial pixel color (RGB): {initial_color}")
    
    if not initial_color:
        print("ERROR: Could not capture initial pixel color")
        return False
    
    # Open preferences dialog
    print("\nOpening Preferences dialog...")
    main_window._show_preferences()
    app.processEvents()
    time.sleep(1)
    
    # Find the theme mode combo box and switch to dark
    try:
        from src.gui.preferences import PreferencesDialog
        # Get the preferences dialog
        for widget in app.topLevelWidgets():
            if isinstance(widget, PreferencesDialog):
                print("Found Preferences dialog")
                
                # Get the theming tab
                theming_tab = widget.theming_tab
                if theming_tab and hasattr(theming_tab, 'mode_combo'):
                    print("Found theme mode combo box")
                    
                    # Get current mode
                    current_index = theming_tab.mode_combo.currentIndex()
                    current_mode = theming_tab.mode_combo.itemData(current_index)
                    print(f"Current theme mode: {current_mode}")
                    
                    # Switch to dark if not already
                    if current_mode != "dark":
                        print("Switching to Dark mode...")
                        theming_tab.mode_combo.setCurrentIndex(0)  # Dark is index 0
                        app.processEvents()
                        time.sleep(2)  # Wait for theme to apply
                    else:
                        print("Switching to Light mode...")
                        theming_tab.mode_combo.setCurrentIndex(1)  # Light is index 1
                        app.processEvents()
                        time.sleep(2)  # Wait for theme to apply
                break
    except Exception as e:
        print(f"Error switching theme: {e}")
        import traceback
        traceback.print_exc()
    
    # Capture pixel color after theme change
    print(f"\nCapturing pixel after theme change at: ({center_x}, {center_y})")
    final_color = capture_pixel_color(center_x, center_y)
    print(f"Final pixel color (RGB): {final_color}")
    
    if not final_color:
        print("ERROR: Could not capture final pixel color")
        return False
    
    # Calculate color difference
    if initial_color and final_color:
        r_diff = abs(initial_color[0] - final_color[0])
        g_diff = abs(initial_color[1] - final_color[1])
        b_diff = abs(initial_color[2] - final_color[2])
        total_diff = r_diff + g_diff + b_diff
        
        print(f"\nColor difference:")
        print(f"  R: {initial_color[0]} -> {final_color[0]} (diff: {r_diff})")
        print(f"  G: {initial_color[1]} -> {final_color[1]} (diff: {g_diff})")
        print(f"  B: {initial_color[2]} -> {final_color[2]} (diff: {b_diff})")
        print(f"  Total difference: {total_diff}")
        
        # If total difference is > 50, consider it a successful theme change
        if total_diff > 50:
            print("\n✅ PASS: Theme change detected (significant color difference)")
            return True
        else:
            print("\n❌ FAIL: No significant color change detected")
            return False
    
    return False


if __name__ == "__main__":
    try:
        success = test_theme_pixel_changes()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

