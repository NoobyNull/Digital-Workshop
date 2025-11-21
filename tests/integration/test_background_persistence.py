#!/usr/bin/env python3
"""
Test to verify background image persistence in QSettings.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from PySide6.QtCore import QSettings, QCoreApplication
from src.core.application_config import ApplicationConfig


def test_background_persistence():
    """Test that background image is saved and loaded correctly."""
    print("\n" + "=" * 70)
    print("TEST: Background Image Persistence")
    print("=" * 70)

    config = ApplicationConfig.get_default()

    # Initialize QSettings
    QCoreApplication.setOrganizationName(config.organization_name)
    QCoreApplication.setApplicationName(config.name)

    settings = QSettings()

    # Get the Brick background path
    brick_path = (
        Path(__file__).parent / "src" / "resources" / "backgrounds" / "Brick.png"
    )
    print(f"\nBrick background path: {brick_path}")
    print(f"Brick background exists: {brick_path.exists()}")

    if not brick_path.exists():
        print("❌ ERROR: Brick.png not found!")
        return False

    # Save background image
    print(f"\nSaving background image to QSettings...")
    settings.setValue("thumbnail/background_image", str(brick_path))
    settings.sync()
    print("✓ Background image saved")

    # Read it back
    print(f"\nReading background image from QSettings...")
    bg_image = settings.value("thumbnail/background_image", None, type=str)
    print(f"Read value: {bg_image}")
    print(f"Type: {type(bg_image)}")

    if bg_image is None:
        print("❌ ERROR: Background image is None!")
        return False

    if bg_image == "":
        print("❌ ERROR: Background image is empty string!")
        return False

    if bg_image != str(brick_path):
        print(f"❌ ERROR: Background image mismatch!")
        print(f"  Expected: {brick_path}")
        print(f"  Got: {bg_image}")
        return False

    print(f"✓ Background image matches: {bg_image}")

    # Verify path exists
    if not Path(bg_image).exists():
        print(f"❌ ERROR: Saved path doesn't exist: {bg_image}")
        return False

    print(f"✓ Saved path exists")

    # Test the logic used in import_dialog.py
    print(f"\nTesting import_dialog.py logic...")
    bg_image_from_settings = settings.value(
        "thumbnail/background_image", config.thumbnail_bg_image, type=str
    )
    bg_color = settings.value(
        "thumbnail/background_color", config.thumbnail_bg_color, type=str
    )

    # Use background image if set, otherwise use background color
    background = bg_image_from_settings if bg_image_from_settings else bg_color

    print(f"bg_image_from_settings: {bg_image_from_settings}")
    print(f"bg_color: {bg_color}")
    print(f"background (used for thumbnail): {background}")

    if background == str(brick_path):
        print(f"✓ Background image will be used for thumbnail generation")
    else:
        print(f"❌ ERROR: Background color will be used instead of image!")
        return False

    # Clean up
    settings.remove("thumbnail/background_image")
    settings.sync()

    print("\n" + "=" * 70)
    print("✅ ALL TESTS PASSED")
    print("=" * 70)
    return True


if __name__ == "__main__":
    try:
        if test_background_persistence():
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
