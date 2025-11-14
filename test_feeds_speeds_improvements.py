#!/usr/bin/env python3
"""Test and demonstrate Feeds and Speeds UI improvements."""

import sys
import os
import time

# Add pymcp_venv to path
sys.path.insert(0, os.path.join(os.getcwd(), 'pymcp_venv', 'Lib', 'site-packages'))

import pyautogui
import pygetwindow as gw

def find_and_activate_window():
    """Find and activate the Digital Workshop window."""
    windows = gw.getAllWindows()
    for window in windows:
        if 'Digital Workshop' in window.title:
            window.activate()
            time.sleep(0.5)
            return window
    return None

def take_screenshot(filename):
    """Take a screenshot and save it."""
    screenshot = pyautogui.screenshot()
    screenshot.save(filename)
    print(f"  ✓ {filename}")

def main():
    print("=" * 70)
    print("Testing Feeds and Speeds UI Improvements")
    print("=" * 70)
    
    # Find window
    print("\n[1] Activating Digital Workshop window...")
    window = find_and_activate_window()
    if not window:
        print("✗ Window not found!")
        return False
    print(f"✓ Window activated: {window.title}")
    
    # Take initial screenshot
    print("\n[2] Taking initial screenshot...")
    take_screenshot('test_01_initial.png')
    
    # Click on the "Feed and Speed" tab
    print("\n[3] Clicking on Feed and Speed tab...")
    # The tab is typically around 65% across the window
    tab_x = window.left + int(window.width * 0.65)
    tab_y = window.top + 40
    pyautogui.click(tab_x, tab_y)
    time.sleep(1)
    
    take_screenshot('test_02_feeds_speeds_tab.png')
    
    # Click on "My Tools" tab to see the expanded columns
    print("\n[4] Clicking on 'My Tools' tab...")
    my_tools_x = window.left + int(window.width * 0.55)
    my_tools_y = window.top + 100
    pyautogui.click(my_tools_x, my_tools_y)
    time.sleep(0.5)
    
    take_screenshot('test_03_my_tools_tab.png')
    
    # Scroll down to see more tools if available
    print("\n[5] Scrolling down in My Tools table...")
    center_x = window.left + window.width // 2
    center_y = window.top + window.height // 2
    pyautogui.moveTo(center_x, center_y)
    time.sleep(0.3)
    pyautogui.scroll(-3)  # Scroll down
    time.sleep(0.5)
    
    take_screenshot('test_04_my_tools_scrolled.png')
    
    # Click on "Feeds & Speeds Data" tab
    print("\n[6] Clicking on 'Feeds & Speeds Data' tab...")
    feeds_data_x = window.left + int(window.width * 0.75)
    feeds_data_y = window.top + 100
    pyautogui.click(feeds_data_x, feeds_data_y)
    time.sleep(1)
    
    take_screenshot('test_05_feeds_speeds_data_tab.png')
    
    # Try to interact with filters if visible
    print("\n[7] Looking for filter controls...")
    take_screenshot('test_06_filters_visible.png')
    
    # Scroll down to see the table
    print("\n[8] Scrolling to see feeds and speeds table...")
    pyautogui.scroll(-3)
    time.sleep(0.5)
    
    take_screenshot('test_07_table_view.png')
    
    # Scroll right to see more columns
    print("\n[9] Scrolling right to see more columns...")
    pyautogui.moveTo(center_x, center_y)
    time.sleep(0.2)
    # Use arrow keys to scroll right
    pyautogui.press('right')
    pyautogui.press('right')
    time.sleep(0.5)
    
    take_screenshot('test_08_table_scrolled_right.png')
    
    print("\n" + "=" * 70)
    print("✓ Testing Complete!")
    print("=" * 70)
    print("\nScreenshots saved:")
    print("  - test_01_initial.png")
    print("  - test_02_feeds_speeds_tab.png")
    print("  - test_03_my_tools_tab.png")
    print("  - test_04_my_tools_scrolled.png")
    print("  - test_05_feeds_speeds_data_tab.png")
    print("  - test_06_filters_visible.png")
    print("  - test_07_table_view.png")
    print("  - test_08_table_scrolled_right.png")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

