#!/usr/bin/env python3
"""
Test script to verify QSettings persistence.
"""

from PySide6.QtCore import QSettings, QCoreApplication, QRect, QPoint, QSize

# Initialize QSettings with organization and application names
QCoreApplication.setOrganizationName("Digital Workshop")
QCoreApplication.setApplicationName("3D Model Manager")


def test_persistence():
    """Test QSettings persistence."""

    # First run - save some data
    print("=== First Run: Saving Data ===")
    settings = QSettings()
    print(f"QSettings location: {settings.fileName()}")

    # Create a test geometry
    test_rect = QRect(100, 200, 1024, 768)
    test_state = b"test_state_data"

    # Save the data
    settings.setValue("window_geometry", test_rect)
    settings.setValue("window_state", test_state)
    settings.sync()  # Force write to disk

    print(f"Saved window_geometry: {test_rect}")
    print(f"Saved window_state: {test_state}")
    print(f"All keys: {settings.allKeys()}")

    # Second run - read the data
    print("\n=== Second Run: Reading Data ===")
    settings2 = QSettings()

    if settings2.contains("window_geometry"):
        restored_rect = settings2.value("window_geometry")
        print(f"[OK] Restored window_geometry: {restored_rect}")
        print(f"     Type: {type(restored_rect)}")
    else:
        print("[FAIL] window_geometry not found")

    if settings2.contains("window_state"):
        restored_state = settings2.value("window_state")
        print(f"[OK] Restored window_state: {restored_state}")
        print(f"     Type: {type(restored_state)}")
    else:
        print("[FAIL] window_state not found")

    print(f"All keys: {settings2.allKeys()}")


if __name__ == "__main__":
    test_persistence()
