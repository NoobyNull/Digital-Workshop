#!/usr/bin/env python3
"""Navigate to Feeds and Speeds tab and take screenshots."""

import sys
import os
import time

# Add pymcp_venv to path
sys.path.insert(0, os.path.join(os.getcwd(), 'pymcp_venv', 'Lib', 'site-packages'))

import pyautogui
import pygetwindow as gw

def main():
    print("=" * 70)
    print("Navigating to Feeds and Speeds Tab")
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
    screenshot.save('fs_01_initial.png')
    print("✓ Screenshot saved: fs_01_initial.png")
    
    # Look for the tab bar - typically at the top of the window
    # The tabs should be around y = top + 30-50 pixels
    print("\n[3] Looking for Feeds and Speeds tab...")
    
    # Move to the tab area
    tab_y = dw_window.top + 40
    
    # Try clicking on different x positions to find the "Feed and Speed" tab
    # Tabs are usually spread across the top
    for x_offset in range(200, dw_window.width, 150):
        tab_x = dw_window.left + x_offset
        pyautogui.moveTo(tab_x, tab_y, duration=0.2)
        time.sleep(0.3)
        
        # Take a screenshot to see what tab we're hovering over
        screenshot = pyautogui.screenshot()
        screenshot.save(f'fs_02_tab_search_{x_offset}.png')
        print(f"  - Checked position x={x_offset}")
    
    # Try clicking on the rightmost tabs area (Feed and Speed is usually later)
    print("\n[4] Clicking on Feed and Speed tab...")
    
    # Estimate the tab position - usually around 60-70% across
    tab_x = dw_window.left + int(dw_window.width * 0.65)
    tab_y = dw_window.top + 40
    
    pyautogui.moveTo(tab_x, tab_y, duration=0.3)
    time.sleep(0.5)
    
    # Take screenshot before clicking
    screenshot = pyautogui.screenshot()
    screenshot.save('fs_03_before_click.png')
    print("✓ Screenshot saved: fs_03_before_click.png")
    
    # Click
    pyautogui.click()
    time.sleep(1)
    
    # Take screenshot after clicking
    screenshot = pyautogui.screenshot()
    screenshot.save('fs_04_after_click.png')
    print("✓ Screenshot saved: fs_04_after_click.png")
    
    # Move to center to see the full tab content
    center_x = dw_window.left + dw_window.width // 2
    center_y = dw_window.top + dw_window.height // 2
    pyautogui.moveTo(center_x, center_y, duration=0.3)
    time.sleep(0.5)
    
    # Take final screenshot
    screenshot = pyautogui.screenshot()
    screenshot.save('fs_05_final.png')
    print("✓ Screenshot saved: fs_05_final.png")
    
    print("\n" + "=" * 70)
    print("✓ Navigation Complete!")
    print("=" * 70)
    print("\nScreenshots saved:")
    print("  - fs_01_initial.png")
    print("  - fs_02_tab_search_*.png (multiple)")
    print("  - fs_03_before_click.png")
    print("  - fs_04_after_click.png")
    print("  - fs_05_final.png")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

