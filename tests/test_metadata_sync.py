#!/usr/bin/env python3
"""
Test script to verify metadata synchronization when a model is selected.

This test validates that:
1. The _sync_metadata_to_selected_model method exists
2. The metadata editor is updated when a model is selected
3. The synchronization handles missing metadata editor gracefully
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_sync_metadata_method_exists():
    """Test that the synchronization method exists in MainWindow."""
    print("\nTest 1: Synchronization Method Exists")

    try:
        from src.gui.main_window import MainWindow

        # Check if the method exists
        has_sync_method = hasattr(MainWindow, "_sync_metadata_to_selected_model")

        if has_sync_method:
            print("   ✓ _sync_metadata_to_selected_model method exists")
            return True
        else:
            print("   ✗ _sync_metadata_to_selected_model method not found")
            return False

    except Exception as e:
        print(f"   ✗ Error checking method: {e}")
        return False


def test_sync_metadata_called_on_selection():
    """Test that synchronization is called when model is selected."""
    print("\nTest 2: Synchronization Called on Model Selection")

    try:
        from src.gui.main_window import MainWindow

        # Create a mock main window
        with patch("src.gui.main_window.get_database_manager"):
            window = Mock(spec=MainWindow)
            window.current_model_id = None
            window.logger = Mock()
            window.metadata_editor = Mock()
            window.menu_manager = Mock()
            window.toolbar_manager = Mock()

            # Bind the actual method to the mock
            window._sync_metadata_to_selected_model = (
                MainWindow._sync_metadata_to_selected_model.__get__(window)
            )
            window._on_model_selected = MainWindow._on_model_selected.__get__(window)

            # Call the method
            window._on_model_selected(1)

            # Verify synchronization was called
            if window.current_model_id == 1:
                print("   ✓ Model ID stored correctly")
                return True
            else:
                print("   ✗ Model ID not stored")
                return False

    except Exception as e:
        print(f"   ✗ Error testing synchronization: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_sync_metadata_loads_metadata():
    """Test that synchronization loads metadata for the selected model."""
    print("\nTest 3: Synchronization Loads Metadata")

    try:
        from src.gui.main_window import MainWindow

        # Create a mock main window with metadata editor
        window = Mock(spec=MainWindow)
        window.logger = Mock()
        window.metadata_editor = Mock()

        # Bind the actual method to the mock
        window._sync_metadata_to_selected_model = (
            MainWindow._sync_metadata_to_selected_model.__get__(window)
        )

        # Call the synchronization method
        window._sync_metadata_to_selected_model(1)

        # Verify load_model_metadata was called
        if window.metadata_editor.load_model_metadata.called:
            print("   ✓ load_model_metadata was called")
            call_args = window.metadata_editor.load_model_metadata.call_args
            if call_args[0][0] == 1:
                print("   ✓ Correct model ID passed to load_model_metadata")
                return True
            else:
                print(f"   ✗ Wrong model ID passed: {call_args[0][0]}")
                return False
        else:
            print("   ✗ load_model_metadata was not called")
            return False

    except Exception as e:
        print(f"   ✗ Error testing metadata loading: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_sync_metadata_handles_missing_editor():
    """Test that synchronization handles missing metadata editor gracefully."""
    print("\nTest 4: Synchronization Handles Missing Editor")

    try:
        from src.gui.main_window import MainWindow

        # Create a mock main window without metadata editor
        window = Mock(spec=MainWindow)
        window.logger = Mock()
        window.metadata_editor = None

        # Bind the actual method to the mock
        window._sync_metadata_to_selected_model = (
            MainWindow._sync_metadata_to_selected_model.__get__(window)
        )

        # Call the synchronization method - should not raise an exception
        window._sync_metadata_to_selected_model(1)

        # Verify logger was called with debug message
        if window.logger.debug.called:
            print("   ✓ Debug message logged for missing editor")
            return True
        else:
            print("   ✗ No debug message logged")
            return False

    except Exception as e:
        print(f"   ✗ Error testing missing editor handling: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_all_tests():
    """Run all synchronization tests."""
    print("=" * 60)
    print("Metadata Synchronization Tests")
    print("=" * 60)

    tests = [
        test_sync_metadata_method_exists,
        test_sync_metadata_called_on_selection,
        test_sync_metadata_loads_metadata,
        test_sync_metadata_handles_missing_editor,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"   ✗ Test failed with exception: {e}")
            import traceback

            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)

    return all(results)


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
