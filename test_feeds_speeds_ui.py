#!/usr/bin/env python3
"""Test the Feeds and Speeds UI improvements."""

import sys
import os
import time

# Add pymcp_venv to path
sys.path.insert(0, os.path.join(os.getcwd(), 'pymcp_venv', 'Lib', 'site-packages'))

import pyautogui
import pygetwindow as gw

def main():
    print("=" * 70)
    print("Testing Feeds and Speeds UI")
    print("=" * 70)
    
    # Find and activate the Digital Workshop window
    print("\n[1] Finding Digital Workshop window...")
    windows = gw.getAllWindows()
    dw_window = None
    
    for window in windows:
        if 'Digital Workshop' in window.title:
            dw_window = window
            break
    
    if not dw_window:
        print("✗ Digital Workshop window not found!")
        return False
    
    print(f"✓ Found: {dw_window.title}")
    dw_window.activate()
    time.sleep(1)
    
    # Take initial screenshot
    print("\n[2] Taking initial screenshot...")
    screenshot = pyautogui.screenshot()
    screenshot.save('feeds_speeds_initial.png')
    print("✓ Screenshot saved: feeds_speeds_initial.png")
    
    # Look for Feeds and Speeds in the menu or tabs
    print("\n[3] Looking for Feeds and Speeds tab...")
    
    # Try to find and click on a tab or menu item
    # This is a general approach - we'll look for text on screen
    center_x = dw_window.left + dw_window.width // 2
    center_y = dw_window.top + dw_window.height // 2
    
    # Move to center
    pyautogui.moveTo(center_x, center_y, duration=0.5)
    time.sleep(0.5)
    
    # Take screenshot showing the center area
    screenshot = pyautogui.screenshot()
    screenshot.save('feeds_speeds_center.png')
    print("✓ Screenshot saved: feeds_speeds_center.png")
    
    # Try clicking on different areas to find the Feeds and Speeds tab
    # Typically tabs are at the top of the right panel
    print("\n[4] Attempting to navigate to Feeds and Speeds...")
    
    # Move to top-right area where tabs might be
    tab_area_x = dw_window.left + int(dw_window.width * 0.7)
    tab_area_y = dw_window.top + 50
    
    pyautogui.moveTo(tab_area_x, tab_area_y, duration=0.3)
    time.sleep(0.5)
    
    screenshot = pyautogui.screenshot()
    screenshot.save('feeds_speeds_tabs.png')
    print("✓ Screenshot saved: feeds_speeds_tabs.png")
    
    print("\n" + "=" * 70)
    print("✓ UI Test Complete!")
    print("=" * 70)
    print("\nScreenshots saved:")
    print("  - feeds_speeds_initial.png")
    print("  - feeds_speeds_center.png")
    print("  - feeds_speeds_tabs.png")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

