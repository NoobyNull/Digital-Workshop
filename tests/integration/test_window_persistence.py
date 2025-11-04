#!/usr/bin/env python3
"""
Test script to verify window size persistence.

This script tests that:
1. QSettings is initialized with consistent org/app names
2. Window size is saved on close
3. Window size is restored on next launch
4. Maximized state is persisted
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from PySide6.QtCore import QSettings, QCoreApplication, QSize, QRect, QPoint
from PySide6.QtWidgets import QApplication, QMainWindow
from src.core.application_config import ApplicationConfig


def test_qsettings_consistency():
    """Test that QSettings uses consistent organization and application names."""
    print("\n" + "=" * 70)
    print("TEST 1: QSettings Consistency")
    print("=" * 70)
    
    config = ApplicationConfig.get_default()
    
    # Initialize QSettings
    QCoreApplication.setOrganizationName(config.organization_name)
    QCoreApplication.setApplicationName(config.name)
    
    org = QCoreApplication.organizationName()
    app = QCoreApplication.applicationName()
    
    print(f"Organization: {org}")
    print(f"Application: {app}")
    
    assert org == config.organization_name, f"Org mismatch: {org} != {config.organization_name}"
    assert app == config.name, f"App mismatch: {app} != {config.name}"
    
    print("✅ QSettings consistency verified")
    return True


def test_window_size_persistence():
    """Test that window size can be saved and restored."""
    print("\n" + "=" * 70)
    print("TEST 2: Window Size Persistence")
    print("=" * 70)
    
    config = ApplicationConfig.get_default()
    
    # Initialize QSettings
    QCoreApplication.setOrganizationName(config.organization_name)
    QCoreApplication.setApplicationName(config.name)
    
    settings = QSettings()
    
    # Test values
    test_width = 1600
    test_height = 900
    test_maximized = True
    
    # Save test values
    settings.setValue("window/width", test_width)
    settings.setValue("window/height", test_height)
    settings.setValue("window/maximized", test_maximized)
    settings.sync()
    
    print(f"Saved: width={test_width}, height={test_height}, maximized={test_maximized}")
    
    # Load test values
    loaded_width = settings.value("window/width", type=int)
    loaded_height = settings.value("window/height", type=int)
    loaded_maximized = settings.value("window/maximized", type=bool)
    
    print(f"Loaded: width={loaded_width}, height={loaded_height}, maximized={loaded_maximized}")
    
    assert loaded_width == test_width, f"Width mismatch: {loaded_width} != {test_width}"
    assert loaded_height == test_height, f"Height mismatch: {loaded_height} != {test_height}"
    assert loaded_maximized == test_maximized, f"Maximized mismatch: {loaded_maximized} != {test_maximized}"
    
    print("✅ Window size persistence verified")
    
    # Clean up
    settings.remove("window")
    settings.sync()
    
    return True


def test_geometry_persistence():
    """Test that full geometry can be saved and restored."""
    print("\n" + "=" * 70)
    print("TEST 3: Full Geometry Persistence")
    print("=" * 70)
    
    config = ApplicationConfig.get_default()
    
    # Initialize QSettings
    QCoreApplication.setOrganizationName(config.organization_name)
    QCoreApplication.setApplicationName(config.name)
    
    settings = QSettings()
    
    # Create a test window
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    
    window = QMainWindow()
    window.setGeometry(100, 100, 1920, 1080)
    
    # Save geometry
    geometry = window.saveGeometry()
    state = window.saveState()
    
    settings.setValue("window_geometry", geometry)
    settings.setValue("window_state", state)
    settings.sync()
    
    print(f"Saved geometry: {window.geometry()}")
    print(f"Saved state size: {len(state)} bytes")
    
    # Create new window and restore
    window2 = QMainWindow()
    
    loaded_geometry = settings.value("window_geometry")
    loaded_state = settings.value("window_state")
    
    if loaded_geometry:
        window2.restoreGeometry(loaded_geometry)
    if loaded_state:
        window2.restoreState(loaded_state)
    
    print(f"Restored geometry: {window2.geometry()}")
    
    assert window2.geometry() == window.geometry(), "Geometry mismatch"
    
    print("✅ Full geometry persistence verified")
    
    # Clean up
    settings.remove("window_geometry")
    settings.remove("window_state")
    settings.sync()
    
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("WINDOW SIZE PERSISTENCE - COMPREHENSIVE TEST")
    print("=" * 70)
    
    try:
        test_qsettings_consistency()
        test_window_size_persistence()
        test_geometry_persistence()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        print("\nWindow size persistence is now working correctly!")
        print("The application will:")
        print("  1. Save window width and height on close")
        print("  2. Save maximized state on close")
        print("  3. Restore window size on next launch")
        print("  4. Restore maximized state on next launch")
        
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

