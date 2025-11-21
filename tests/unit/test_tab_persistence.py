"""
Comprehensive test suite for Preferences Dialog Tab Selection Persistence.

This test suite verifies that the preferences dialog correctly:
1. Saves the last selected tab when switching tabs
2. Restores the last selected tab when reopened
3. Handles invalid tab indices gracefully
4. Persists tab selection across application restarts
"""

import sys
import time
from pathlib import Path

from PySide6.QtCore import QSettings, QCoreApplication, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QTest

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gui.preferences import PreferencesDialog


class TabPersistenceTester:
    """Test harness for preferences dialog tab persistence."""

    def __init__(self):
        self.app = QApplication.instance() or QApplication(sys.argv)

        # CRITICAL: Initialize QSettings with organization and application names
        # This must match the initialization in src/core/application.py
        QCoreApplication.setOrganizationName("Digital Workshop")
        QCoreApplication.setApplicationName("3D Model Manager")
        self.results = []
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0

    def log(self, message: str, level: str = "INFO") -> None:
        """Log test message."""
        prefix = {"INFO": "[i]", "PASS": "[+]", "FAIL": "[-]", "WARN": "[!]"}.get(
            level, "[*]"
        )
        print(f"{prefix} {message}")

    def assert_equal(self, actual, expected, test_name: str) -> bool:
        """Assert that actual equals expected."""
        self.test_count += 1
        if actual == expected:
            self.log(f"PASS: {test_name}", "PASS")
            self.log(f"  Expected: {expected}, Got: {actual}")
            self.passed_count += 1
            self.results.append(
                {
                    "test": test_name,
                    "status": "PASS",
                    "expected": expected,
                    "actual": actual,
                }
            )
            return True
        else:
            self.log(f"FAIL: {test_name}", "FAIL")
            self.log(f"  Expected: {expected}, Got: {actual}")
            self.failed_count += 1
            self.results.append(
                {
                    "test": test_name,
                    "status": "FAIL",
                    "expected": expected,
                    "actual": actual,
                }
            )
            return False

    def clear_settings(self) -> None:
        """Clear test settings."""
        settings = QSettings()
        settings.remove("preferences/last_tab_index")
        settings.sync()
        self.log("Cleared QSettings for clean test environment")

    def get_stored_tab_index(self) -> int:
        """Get the stored tab index from QSettings."""
        settings = QSettings()
        return settings.value("preferences/last_tab_index", 0, type=int)

    def set_stored_tab_index(self, index: int) -> None:
        """Set the stored tab index in QSettings."""
        settings = QSettings()
        settings.setValue("preferences/last_tab_index", index)
        settings.sync()

    def test_basic_persistence(self) -> None:
        """Test 1: Basic Persistence Test"""
        self.log("\n" + "=" * 70)
        self.log("TEST 1: BASIC PERSISTENCE TEST")
        self.log("=" * 70)

        # Clear any existing settings
        self.clear_settings()

        # Create dialog and verify it starts at tab 0
        dialog1 = PreferencesDialog()
        initial_tab = dialog1.tabs.currentIndex()
        self.assert_equal(
            initial_tab, 0, "Dialog opens at General tab (index 0) initially"
        )

        # Navigate to Content tab (index 3)
        self.log("Navigating to Content tab (index 3)...")
        dialog1.tabs.setCurrentIndex(3)
        QTest.qWait(100)  # Wait for signal processing

        current_tab = dialog1.tabs.currentIndex()
        self.assert_equal(current_tab, 3, "Tab switched to Content (index 3)")

        # Close the dialog
        self.log("Closing dialog...")
        dialog1.close()
        QTest.qWait(100)

        # Check that the setting was saved
        stored_index = self.get_stored_tab_index()
        self.assert_equal(stored_index, 3, "Tab index 3 saved to QSettings")

        # Reopen dialog and verify Content tab is selected
        self.log("Reopening dialog...")
        dialog2 = PreferencesDialog()
        restored_tab = dialog2.tabs.currentIndex()
        self.assert_equal(restored_tab, 3, "Content tab (index 3) restored on reopen")

        dialog2.close()
        self.log("[OK] Basic persistence test complete")

    def test_multiple_tab_switching(self) -> None:
        """Test 2: Multiple Tab Switching Test"""
        self.log("\n" + "=" * 70)
        self.log("TEST 2: MULTIPLE TAB SWITCHING TEST")
        self.log("=" * 70)

        # Clear settings
        self.clear_settings()

        # Create dialog
        dialog = PreferencesDialog()

        # Switch through tabs: General (0) → Appearance (1) → 3D Viewer (2) → Content (3)
        tab_sequence = [
            (0, "General"),
            (1, "Appearance"),
            (2, "3D Viewer"),
            (3, "Content"),
        ]

        for index, name in tab_sequence:
            self.log(f"Switching to {name} tab (index {index})...")
            dialog.tabs.setCurrentIndex(index)
            QTest.qWait(100)

            current = dialog.tabs.currentIndex()
            self.assert_equal(current, index, f"Successfully switched to {name} tab")

            # Verify it was saved
            stored = self.get_stored_tab_index()
            self.assert_equal(stored, index, f"{name} tab index saved to QSettings")

        # Close on Content tab
        self.log("Closing dialog on Content tab...")
        dialog.close()
        QTest.qWait(100)

        # Verify final saved state
        final_stored = self.get_stored_tab_index()
        self.assert_equal(final_stored, 3, "Final tab index (3) persisted after close")

        # Reopen and verify
        dialog2 = PreferencesDialog()
        restored = dialog2.tabs.currentIndex()
        self.assert_equal(restored, 3, "Content tab restored after multiple switches")

        dialog2.close()
        self.log("[OK] Multiple tab switching test complete")

    def test_invalid_index_handling(self) -> None:
        """Test 3: Invalid Index Handling Test"""
        self.log("\n" + "=" * 70)
        self.log("TEST 3: INVALID INDEX HANDLING TEST")
        self.log("=" * 70)

        # Test with invalid index (too high)
        self.log("Setting invalid tab index (99) in QSettings...")
        self.set_stored_tab_index(99)

        dialog1 = PreferencesDialog()
        current = dialog1.tabs.currentIndex()
        self.assert_equal(current, 0, "Invalid index (99) gracefully defaults to tab 0")
        dialog1.close()

        # Test with invalid index (negative)
        self.log("Setting invalid tab index (-5) in QSettings...")
        self.set_stored_tab_index(-5)

        dialog2 = PreferencesDialog()
        current = dialog2.tabs.currentIndex()
        self.assert_equal(current, 0, "Invalid index (-5) gracefully defaults to tab 0")
        dialog2.close()

        # Test with valid edge case (last tab index)
        total_tabs = dialog2.tabs.count()
        last_valid_index = total_tabs - 1
        self.log(f"Setting edge case tab index ({last_valid_index}) in QSettings...")
        self.set_stored_tab_index(last_valid_index)

        dialog3 = PreferencesDialog()
        current = dialog3.tabs.currentIndex()
        self.assert_equal(
            current,
            last_valid_index,
            f"Valid edge case index ({last_valid_index}) works correctly",
        )
        dialog3.close()

        self.log("[OK] Invalid index handling test complete")

    def test_settings_storage_verification(self) -> None:
        """Test 4: Settings Storage Verification Test"""
        self.log("\n" + "=" * 70)
        self.log("TEST 4: SETTINGS STORAGE VERIFICATION TEST")
        self.log("=" * 70)

        # Clear settings
        self.clear_settings()

        # Verify the key doesn't exist initially
        settings = QSettings()
        has_key = settings.contains("preferences/last_tab_index")
        self.log(f"Initial state - key exists: {has_key}")

        # Create dialog and switch tabs
        dialog = PreferencesDialog()

        # Test each tab saves correctly
        for i in range(dialog.tabs.count()):
            tab_name = dialog.tabs.tabText(i)
            self.log(f"Testing storage for {tab_name} (index {i})...")

            dialog.tabs.setCurrentIndex(i)
            QTest.qWait(50)

            stored = self.get_stored_tab_index()
            self.assert_equal(stored, i, f"Index {i} correctly stored in QSettings")

        dialog.close()

        # Verify key exists and has correct value
        has_key_after = settings.contains("preferences/last_tab_index")
        self.log(f"After operations - key exists: {has_key_after}")
        self.assert_equal(
            has_key_after, True, "QSettings key 'preferences/last_tab_index' exists"
        )

        self.log("[OK] Settings storage verification test complete")

    def test_application_restart_simulation(self) -> None:
        """Test 5: Application Restart Simulation Test"""
        self.log("\n" + "=" * 70)
        self.log("TEST 5: APPLICATION RESTART SIMULATION TEST")
        self.log("=" * 70)

        # Clear settings and set Content tab (index 3)
        self.clear_settings()
        self.log("Setting Content tab (index 3) as last selected...")
        self.set_stored_tab_index(3)

        # Simulate first session
        self.log("Session 1: Opening preferences...")
        dialog1 = PreferencesDialog()
        current1 = dialog1.tabs.currentIndex()
        self.assert_equal(current1, 3, "Session 1: Content tab restored")
        dialog1.close()

        # Simulate app restart by creating new dialog instance
        self.log("Simulating app restart...")
        QTest.qWait(200)

        # Session 2
        self.log("Session 2: Opening preferences after 'restart'...")
        dialog2 = PreferencesDialog()
        current2 = dialog2.tabs.currentIndex()
        self.assert_equal(current2, 3, "Session 2: Content tab still restored")

        # Switch to Appearance tab
        self.log("Session 2: Switching to Appearance tab (index 1)...")
        dialog2.tabs.setCurrentIndex(1)
        QTest.qWait(100)
        dialog2.close()

        # Session 3 - verify new selection persisted
        self.log("Session 3: Opening preferences after another 'restart'...")
        dialog3 = PreferencesDialog()
        current3 = dialog3.tabs.currentIndex()
        self.assert_equal(
            current3, 1, "Session 3: Appearance tab restored from previous session"
        )
        dialog3.close()

        self.log("[OK] Application restart simulation test complete")

    def run_all_tests(self) -> None:
        """Run all test scenarios."""
        self.log("\n" + "=" * 70)
        self.log("PREFERENCES DIALOG TAB PERSISTENCE TEST SUITE")
        self.log("=" * 70)
        self.log(f"Starting at: {time.strftime('%Y-%m-%d %H:%M:%S')}")

        # Run all tests
        self.test_basic_persistence()
        self.test_multiple_tab_switching()
        self.test_invalid_index_handling()
        self.test_settings_storage_verification()
        self.test_application_restart_simulation()

        # Print summary
        self.print_summary()

    def print_summary(self) -> None:
        """Print test summary."""
        self.log("\n" + "=" * 70)
        self.log("TEST SUMMARY")
        self.log("=" * 70)
        self.log(f"Total Tests: {self.test_count}")
        self.log(f"Passed: {self.passed_count}", "PASS")
        self.log(
            f"Failed: {self.failed_count}", "FAIL" if self.failed_count > 0 else "INFO"
        )
        self.log(f"Success Rate: {(self.passed_count/self.test_count*100):.1f}%")

        if self.failed_count > 0:
            self.log("\nFailed Tests:", "FAIL")
            for result in self.results:
                if result["status"] == "FAIL":
                    self.log(f"  - {result['test']}", "FAIL")
                    self.log(
                        f"    Expected: {result['expected']}, Got: {result['actual']}"
                    )

        self.log("\n" + "=" * 70)
        if self.failed_count == 0:
            self.log("ALL TESTS PASSED!", "PASS")
        else:
            self.log("SOME TESTS FAILED - REVIEW REQUIRED", "FAIL")
        self.log("=" * 70)


def main():
    """Main test execution."""
    tester = TabPersistenceTester()
    tester.run_all_tests()

    # Exit after tests complete
    QTimer.singleShot(500, tester.app.quit)
    tester.app.exec()

    # Return exit code based on test results
    return 0 if tester.failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
