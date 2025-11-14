#!/usr/bin/env python3
"""Automate Digital Workshop app using pyMCPAutoGUI."""

import sys
import os
import time

# Add pymcp_venv to path
sys.path.insert(0, os.path.join(os.getcwd(), 'pymcp_venv', 'Lib', 'site-packages'))

import pyautogui
import pygetwindow as gw

def main():
    print("=" * 70)
    print("Digital Workshop App Automation")
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
    print(f"  Position: ({dw_window.left}, {dw_window.top})")
    print(f"  Size: {dw_window.width}x{dw_window.height}")
    
    # Activate window
    print("\n[2] Activating window...")
    dw_window.activate()
    time.sleep(1)
    print("✓ Window activated")
    
    # Take screenshot
    print("\n[3] Taking screenshot...")
    screenshot = pyautogui.screenshot()
    screenshot.save('dw_active.png')
    print("✓ Screenshot saved: dw_active.png")
    
    # Move mouse to window center
    print("\n[4] Moving mouse to window center...")
    center_x = dw_window.left + dw_window.width // 2
    center_y = dw_window.top + dw_window.height // 2
    pyautogui.moveTo(center_x, center_y, duration=0.5)
    print(f"✓ Mouse moved to ({center_x}, {center_y})")
    
    # Get current mouse position
    pos = pyautogui.position()
    print(f"✓ Current position: {pos}")
    
    # Take screenshot with cursor
    print("\n[5] Taking screenshot with cursor...")
    screenshot = pyautogui.screenshot()
    screenshot.save('dw_with_cursor.png')
    print("✓ Screenshot saved: dw_with_cursor.png")
    
    # Perform some interactions
    print("\n[6] Performing interactions...")
    
    # Move to top-left area (likely menu/toolbar)
    print("  - Moving to top-left area...")
    pyautogui.moveTo(dw_window.left + 50, dw_window.top + 50, duration=0.3)
    time.sleep(0.5)
    
    # Take screenshot
    screenshot = pyautogui.screenshot()
    screenshot.save('dw_topleft.png')
    print("  ✓ Screenshot saved: dw_topleft.png")
    
    # Move to center
    print("  - Moving to center...")
    pyautogui.moveTo(center_x, center_y, duration=0.3)
    time.sleep(0.5)
    
    # Take screenshot
    screenshot = pyautogui.screenshot()
    screenshot.save('dw_center.png')
    print("  ✓ Screenshot saved: dw_center.png")
    
    # Get screen info
    print("\n[7] Screen Information:")
    screen_width, screen_height = pyautogui.size()
    print(f"  Screen size: {screen_width}x{screen_height}")
    print(f"  Mouse position: {pyautogui.position()}")
    
    print("\n" + "=" * 70)
    print("✓ Successfully automated Digital Workshop!")
    print("=" * 70)
    print("\nScreenshots saved:")
    print("  - dw_active.png")
    print("  - dw_with_cursor.png")
    print("  - dw_topleft.png")
    print("  - dw_center.png")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

