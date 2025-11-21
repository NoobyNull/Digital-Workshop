#!/usr/bin/env python3
"""Test script for VTK G-code viewer integration."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all components can be imported."""
    print("Testing imports...")

    try:
        from src.gui.gcode_previewer_components import (
            GcodePreviewerWidget,
            GcodeParser,
            GcodeRenderer,
            VTKWidget,
            CameraController,
            GcodeTimeline,
            InteractiveGcodeLoader,
            GcodeEditorWidget,
        )

        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_component_creation():
    """Test that components can be created."""
    print("\nTesting component creation...")

    try:
        from src.gui.gcode_previewer_components import (
            GcodeParser,
            GcodeRenderer,
        )

        # Create parser
        parser = GcodeParser()
        print("✓ GcodeParser created")

        # Create renderer
        renderer = GcodeRenderer()
        print("✓ GcodeRenderer created")

        return True
    except Exception as e:
        print(f"✗ Component creation failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_signal_connections():
    """Test that signal connections work."""
    print("\nTesting signal connections...")

    try:
        from PySide6.QtWidgets import QApplication
        from src.gui.gcode_previewer_components import (
            GcodeTimeline,
            GcodeRenderer,
        )

        # Create QApplication if needed
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        # Create components
        timeline = GcodeTimeline()
        renderer = GcodeRenderer()

        # Test signal emission
        timeline.frame_changed.emit(0)
        print("✓ Timeline signals work")

        return True
    except Exception as e:
        print(f"✗ Signal connection test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("VTK G-code Viewer Integration Test")
    print("=" * 60)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Component Creation", test_component_creation()))
    results.append(("Signal Connections", test_signal_connections()))

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
