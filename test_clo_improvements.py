#!/usr/bin/env python3
"""Test Cut List Optimizer UI improvements."""

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
    print("Testing Cut List Optimizer UI Improvements")
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
    take_screenshot('clo_01_initial.png')
    
    # Click on the "Cut List Optimizer" tab
    print("\n[3] Clicking on Cut List Optimizer tab...")
    # The tab is typically around 50% across the window
    tab_x = window.left + int(window.width * 0.50)
    tab_y = window.top + 40
    pyautogui.click(tab_x, tab_y)
    time.sleep(1)
    
    take_screenshot('clo_02_clo_tab.png')
    
    # Move to center to see the full interface
    print("\n[4] Viewing the full Cut List Optimizer interface...")
    center_x = window.left + window.width // 2
    center_y = window.top + window.height // 2
    pyautogui.moveTo(center_x, center_y)
    time.sleep(0.5)
    
    take_screenshot('clo_03_full_interface.png')
    
    # Scroll down in the left panel to see the options
    print("\n[5] Scrolling down to see optimization options...")
    left_panel_x = window.left + int(window.width * 0.25)
    left_panel_y = window.top + window.height // 2
    pyautogui.moveTo(left_panel_x, left_panel_y)
    time.sleep(0.3)
    pyautogui.scroll(-5)  # Scroll down
    time.sleep(0.5)
    
    take_screenshot('clo_04_options_visible.png')
    
    # Scroll down more to see all options
    print("\n[6] Scrolling down more to see all options...")
    pyautogui.scroll(-5)
    time.sleep(0.5)
    
    take_screenshot('clo_05_all_options.png')
    
    # Try to interact with a combo box
    print("\n[7] Testing option controls...")
    # Click on strategy combo box
    strategy_x = window.left + int(window.width * 0.25)
    strategy_y = window.top + int(window.height * 0.35)
    pyautogui.click(strategy_x, strategy_y)
    time.sleep(0.5)
    
    take_screenshot('clo_06_strategy_dropdown.png')
    
    # Press Escape to close dropdown
    pyautogui.press('escape')
    time.sleep(0.3)
    
    # Scroll back up to see materials table
    print("\n[8] Scrolling back up to see materials table...")
    pyautogui.scroll(10)
    time.sleep(0.5)
    
    take_screenshot('clo_07_materials_table.png')
    
    print("\n" + "=" * 70)
    print("✓ Testing Complete!")
    print("=" * 70)
    print("\nScreenshots saved:")
    print("  - clo_01_initial.png")
    print("  - clo_02_clo_tab.png")
    print("  - clo_03_full_interface.png")
    print("  - clo_04_options_visible.png")
    print("  - clo_05_all_options.png")
    print("  - clo_06_strategy_dropdown.png")
    print("  - clo_07_materials_table.png")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

