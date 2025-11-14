#!/usr/bin/env python3
"""Interact with Digital Workshop app using pyMCPAutoGUI."""

import sys
import os

# Add pymcp_venv to path
sys.path.insert(0, os.path.join(os.getcwd(), 'pymcp_venv', 'Lib', 'site-packages'))

import pyautogui
import time

def main():
    print("=" * 70)
    print("Digital Workshop App Interaction")
    print("=" * 70)
    
    # Take a screenshot
    print("\n[1] Taking screenshot of current screen...")
    screenshot = pyautogui.screenshot()
    screenshot.save('current_screen.png')
    print("✓ Screenshot saved to current_screen.png")
    
    # Get screen info
    screen_width, screen_height = pyautogui.size()
    print(f"✓ Screen size: {screen_width}x{screen_height}")
    
    # Get current mouse position
    mouse_x, mouse_y = pyautogui.position()
    print(f"✓ Current mouse position: ({mouse_x}, {mouse_y})")
    
    # Get all window titles
    print("\n[2] Finding Digital Workshop window...")
    try:
        import pygetwindow as gw
        windows = gw.getAllWindows()
        print(f"✓ Found {len(windows)} windows:")
        
        dw_window = None
        for i, window in enumerate(windows):
            print(f"   {i+1}. {window.title}")
            if 'Digital Workshop' in window.title or 'Workshop' in window.title:
                dw_window = window
        
        if dw_window:
            print(f"\n✓ Found Digital Workshop window: {dw_window.title}")
            print(f"  Position: ({dw_window.left}, {dw_window.top})")
            print(f"  Size: {dw_window.width}x{dw_window.height}")
            
            # Activate the window
            print("\n[3] Activating Digital Workshop window...")
            dw_window.activate()
            time.sleep(1)
            print("✓ Window activated")
            
            # Take another screenshot
            print("\n[4] Taking screenshot of Digital Workshop...")
            screenshot = pyautogui.screenshot()
            screenshot.save('digital_workshop_screen.png')
            print("✓ Screenshot saved to digital_workshop_screen.png")
            
            # Move mouse to center of window
            center_x = dw_window.left + dw_window.width // 2
            center_y = dw_window.top + dw_window.height // 2
            print(f"\n[5] Moving mouse to window center ({center_x}, {center_y})...")
            pyautogui.moveTo(center_x, center_y, duration=0.5)
            print("✓ Mouse moved")
            
            # Take final screenshot
            print("\n[6] Taking final screenshot...")
            screenshot = pyautogui.screenshot()
            screenshot.save('digital_workshop_with_cursor.png')
            print("✓ Screenshot saved to digital_workshop_with_cursor.png")
            
            print("\n" + "=" * 70)
            print("✓ Successfully interacted with Digital Workshop!")
            print("=" * 70)
        else:
            print("✗ Digital Workshop window not found")
            
    except ImportError:
        print("✗ pygetwindow not available, using basic screenshot only")
    
    print("\nScreenshots saved:")
    print("  - current_screen.png")
    print("  - digital_workshop_screen.png")
    print("  - digital_workshop_with_cursor.png")

if __name__ == "__main__":
    main()

