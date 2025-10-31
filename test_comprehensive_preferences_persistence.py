"""
Comprehensive Preferences Persistence Test Suite
=================================================

This script provides comprehensive testing for:
1. Tab selection persistence across dialog cycles
2. Content tab settings persistence (background image + material)
3. QSettings storage verification
4. Edge cases and error handling

Usage:
    python test_comprehensive_preferences_persistence.py

The script will guide you through all test scenarios interactively.
"""

import sys
import time
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit, QMessageBox
from PySide6.QtCore import Qt, QSettings, QTimer

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.gui.preferences import PreferencesDialog
from src.core.logging_config import get_logger

logger = get_logger(__name__)


class TestController(QMainWindow):
    """
    Main test controller that runs through all comprehensive test scenarios.
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Preferences Persistence - Comprehensive Test Suite")
        self.setMinimumSize(900, 700)
        
        self.test_results = []
        self.current_test = 0
        self.preferences_dialog: Optional[PreferencesDialog] = None
        
        self._setup_ui()
        self._clear_test_settings()
        
        # Show welcome message
        QTimer.singleShot(500, self._show_welcome)
    
    def _setup_ui(self):
        """Setup the test controller UI."""
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setStyleSheet("font-family: 'Consolas', monospace; font-size: 10pt;")
        layout.addWidget(self.log_display)
        
        # Test buttons
        self.btn_start = QPushButton("▶ Start Comprehensive Test Suite")
        self.btn_start.setStyleSheet("font-size: 12pt; font-weight: bold; padding: 10px;")
        self.btn_start.clicked.connect(self._start_test_suite)
        layout.addWidget(self.btn_start)
        
        self.btn_manual_prefs = QPushButton("🔧 Open Preferences (Manual Testing)")
        self.btn_manual_prefs.clicked.connect(self._open_preferences_manual)
        layout.addWidget(self.btn_manual_prefs)
        
        self.btn_check_settings = QPushButton("🔍 Inspect Current QSettings")
        self.btn_check_settings.clicked.connect(self._inspect_qsettings)
        layout.addWidget(self.btn_check_settings)
        
        self.btn_clear = QPushButton("🗑 Clear All Test Settings")
        self.btn_clear.clicked.connect(self._clear_test_settings)
        layout.addWidget(self.btn_clear)
    
    def _log(self, message: str, level: str = "INFO"):
        """Add a log message to the display."""
        timestamp = time.strftime("%H:%M:%S")
        
        if level == "PASS":
            color = "green"
            prefix = "✓"
        elif level == "FAIL":
            color = "red"
            prefix = "✗"
        elif level == "WARN":
            color = "orange"
            prefix = "⚠"
        elif level == "TEST":
            color = "blue"
            prefix = "►"
        else:
            color = "black"
            prefix = "•"
        
        html = f'<span style="color: gray;">[{timestamp}]</span> <span style="color: {color}; font-weight: bold;">{prefix}</span> {message}'
        self.log_display.append(html)
        self.log_display.ensureCursorVisible()
        QApplication.processEvents()
    
    def _show_welcome(self):
        """Show welcome message."""
        self._log("=" * 80, "INFO")
        self._log("COMPREHENSIVE PREFERENCES PERSISTENCE TEST SUITE", "TEST")
        self._log("=" * 80, "INFO")
        self._log("")
        self._log("This test suite will validate:", "INFO")
        self._log("  1. Tab selection persistence across dialog cycles", "INFO")
        self._log("  2. Content tab settings persistence (background + material)", "INFO")
        self._log("  3. QSettings storage and synchronization", "INFO")
        self._log("  4. Cross-tab interactions", "INFO")
        self._log("  5. Edge cases and error handling", "INFO")
        self._log("")
        self._log("Click 'Start Comprehensive Test Suite' to begin automated testing.", "INFO")
        self._log("Or use 'Open Preferences' for manual testing.", "INFO")
        self._log("")
    
    def _clear_test_settings(self):
        """Clear all test-related QSettings."""
        try:
            settings = QSettings()
            settings.remove("preferences/last_tab_index")
            settings.remove("thumbnail/background_image")
            settings.remove("thumbnail/material")
            settings.sync()
            self._log("Cleared all test settings from QSettings", "INFO")
        except Exception as e:
            self._log(f"Failed to clear settings: {e}", "FAIL")
    
    def _inspect_qsettings(self):
        """Inspect current QSettings values."""
        try:
            settings = QSettings()
            self._log("=" * 60, "INFO")
            self._log("CURRENT QSETTINGS VALUES:", "TEST")
            self._log("=" * 60, "INFO")
            
            # Tab index
            tab_index = settings.value("preferences/last_tab_index", None)
            self._log(f"preferences/last_tab_index = {tab_index}", "INFO")
            
            # Background image
            bg_image = settings.value("thumbnail/background_image", None)
            self._log(f"thumbnail/background_image = {bg_image}", "INFO")
            
            # Material
            material = settings.value("thumbnail/material", None)
            self._log(f"thumbnail/material = {material}", "INFO")
            
            self._log("=" * 60, "INFO")
        except Exception as e:
            self._log(f"Failed to inspect settings: {e}", "FAIL")
    
    def _open_preferences_manual(self):
        """Open preferences dialog for manual testing."""
        try:
            self._log("Opening preferences dialog for manual testing...", "INFO")
            self.preferences_dialog = PreferencesDialog(self)
            self.preferences_dialog.finished.connect(self._on_manual_prefs_closed)
            self.preferences_dialog.show()
        except Exception as e:
            self._log(f"Failed to open preferences: {e}", "FAIL")
    
    def _on_manual_prefs_closed(self):
        """Handle manual preferences dialog close."""
        self._log("Preferences dialog closed", "INFO")
        self._log("You can inspect settings or reopen to verify persistence", "INFO")
    
    def _start_test_suite(self):
        """Start the comprehensive automated test suite."""
        self.btn_start.setEnabled(False)
        self.test_results.clear()
        self.current_test = 0
        
        self._log("", "INFO")
        self._log("=" * 80, "TEST")
        self._log("STARTING COMPREHENSIVE TEST SUITE", "TEST")
        self._log("=" * 80, "TEST")
        self._log("", "INFO")
        
        # Run tests in sequence
        QTimer.singleShot(500, self._run_test_1)
    
    def _run_test_1(self):
        """Test 1: Complete Integration Test - Tab Persistence + Content Settings"""
        self._log("", "INFO")
        self._log("TEST 1: Complete Integration Test", "TEST")
        self._log("-" * 80, "INFO")
        
        try:
            # Step 1: Clear settings
            self._clear_test_settings()
            self._log("Step 1: Cleared all settings", "INFO")
            
            # Step 2: Open preferences and check Content tab is selected (index 3)
            self._log("Step 2: Opening preferences (should default to General tab)...", "INFO")
            prefs = PreferencesDialog(self)
            
            initial_tab = prefs.tabs.currentIndex()
            self._log(f"Initial tab index: {initial_tab}", "INFO")
            
            # Step 3: Navigate to Content tab (index 3)
            self._log("Step 3: Navigating to Content tab...", "INFO")
            prefs.tabs.setCurrentIndex(3)
            QApplication.processEvents()
            time.sleep(0.3)
            
            current_tab = prefs.tabs.currentIndex()
            if current_tab == 3:
                self._log("✓ Successfully navigated to Content tab (index 3)", "PASS")
            else:
                self._log(f"✗ Failed to navigate to Content tab. Current: {current_tab}", "FAIL")
            
            # Step 4: Select background and material
            self._log("Step 4: Selecting background image and material...", "INFO")
            content_tab = prefs.thumbnail_settings_tab
            
            # Select first background
            if content_tab.bg_list.count() > 0:
                content_tab.bg_list.setCurrentRow(0)
                bg_item = content_tab.bg_list.currentItem()
                bg_path = bg_item.data(Qt.UserRole) if bg_item else None
                self._log(f"Selected background: {Path(bg_path).stem if bg_path else 'None'}", "INFO")
            
            # Select second material (not "None")
            if content_tab.material_combo.count() > 1:
                content_tab.material_combo.setCurrentIndex(1)
                material = content_tab.material_combo.currentData()
                self._log(f"Selected material: {material}", "INFO")
            
            QApplication.processEvents()
            time.sleep(0.3)
            
            # Step 5: Save settings
            self._log("Step 5: Clicking Save button...", "INFO")
            prefs.btn_save.click()
            QApplication.processEvents()
            time.sleep(0.5)
            
            # Dismiss the success message box if present
            QTimer.singleShot(100, lambda: self._dismiss_message_box())
            QApplication.processEvents()
            time.sleep(0.3)
            
            # Step 6: Close dialog
            self._log("Step 6: Closing preferences dialog...", "INFO")
            prefs.close()
            QApplication.processEvents()
            time.sleep(0.3)
            
            # Step 7: Verify QSettings were written
            self._log("Step 7: Verifying QSettings storage...", "INFO")
            settings = QSettings()
            
            saved_tab = settings.value("preferences/last_tab_index", None, type=int)
            saved_bg = settings.value("thumbnail/background_image", None, type=str)
            saved_mat = settings.value("thumbnail/material", None, type=str)
            
            self._log(f"  Saved tab index: {saved_tab}", "INFO")
            self._log(f"  Saved background: {Path(saved_bg).stem if saved_bg else 'None'}", "INFO")
            self._log(f"  Saved material: {saved_mat}", "INFO")
            
            # Step 8: Reopen and verify
            self._log("Step 8: Reopening preferences to verify persistence...", "INFO")
            prefs2 = PreferencesDialog(self)
            QApplication.processEvents()
            time.sleep(0.3)
            
            restored_tab = prefs2.tabs.currentIndex()
            content_tab2 = prefs2.thumbnail_settings_tab
            
            restored_bg_item = content_tab2.bg_list.currentItem()
            restored_bg = restored_bg_item.data(Qt.UserRole) if restored_bg_item else None
            restored_mat = content_tab2.material_combo.currentData()
            
            self._log(f"  Restored tab index: {restored_tab}", "INFO")
            self._log(f"  Restored background: {Path(restored_bg).stem if restored_bg else 'None'}", "INFO")
            self._log(f"  Restored material: {restored_mat}", "INFO")
            
            # Verify results
            test_passed = True
            if restored_tab == 3:
                self._log("✓ Tab persistence PASSED", "PASS")
            else:
                self._log(f"✗ Tab persistence FAILED (expected 3, got {restored_tab})", "FAIL")
                test_passed = False
            
            if restored_bg == saved_bg:
                self._log("✓ Background persistence PASSED", "PASS")
            else:
                self._log(f"✗ Background persistence FAILED", "FAIL")
                test_passed = False
            
            if restored_mat == saved_mat:
                self._log("✓ Material persistence PASSED", "PASS")
            else:
                self._log(f"✗ Material persistence FAILED", "FAIL")
                test_passed = False
            
            prefs2.close()
            
            self.test_results.append(("Test 1: Integration Test", test_passed))
            
            # Continue to next test
            QTimer.singleShot(1000, self._run_test_2)
            
        except Exception as e:
            self._log(f"Test 1 ERROR: {e}", "FAIL")
            self.test_results.append(("Test 1: Integration Test", False))
            QTimer.singleShot(1000, self._run_test_2)
    
    def _run_test_2(self):
        """Test 2: Multiple Dialog Cycles"""
        self._log("", "INFO")
        self._log("TEST 2: Multiple Dialog Cycles Test", "TEST")
        self._log("-" * 80, "INFO")
        
        try:
            test_passed = True
            
            for i in range(3):
                self._log(f"Cycle {i+1}/3: Opening and closing preferences...", "INFO")
                
                prefs = PreferencesDialog(self)
                QApplication.processEvents()
                time.sleep(0.2)
                
                tab_index = prefs.tabs.currentIndex()
                self._log(f"  Tab index in cycle {i+1}: {tab_index}", "INFO")
                
                if tab_index != 3:
                    self._log(f"  ✗ Expected tab 3, got {tab_index}", "FAIL")
                    test_passed = False
                
                prefs.close()
                QApplication.processEvents()
                time.sleep(0.2)
            
            if test_passed:
                self._log("✓ Multiple cycles test PASSED", "PASS")
            else:
                self._log("✗ Multiple cycles test FAILED", "FAIL")
            
            self.test_results.append(("Test 2: Multiple Cycles", test_passed))
            
            # Continue to next test
            QTimer.singleShot(1000, self._run_test_3)
            
        except Exception as e:
            self._log(f"Test 2 ERROR: {e}", "FAIL")
            self.test_results.append(("Test 2: Multiple Cycles", False))
            QTimer.singleShot(1000, self._run_test_3)
    
    def _run_test_3(self):
        """Test 3: Cross-Tab Interaction"""
        self._log("", "INFO")
        self._log("TEST 3: Cross-Tab Interaction Test", "TEST")
        self._log("-" * 80, "INFO")
        
        try:
            # Open preferences
            prefs = PreferencesDialog(self)
            QApplication.processEvents()
            time.sleep(0.2)
            
            # Should be on Content tab (3)
            self._log(f"Initial tab: {prefs.tabs.currentIndex()}", "INFO")
            
            # Switch to General tab (0)
            self._log("Switching to General tab...", "INFO")
            prefs.tabs.setCurrentIndex(0)
            QApplication.processEvents()
            time.sleep(0.2)
            
            # Switch to Appearance tab (1)
            self._log("Switching to Appearance tab...", "INFO")
            prefs.tabs.setCurrentIndex(1)
            QApplication.processEvents()
            time.sleep(0.2)
            
            # Switch back to Content tab (3)
            self._log("Switching back to Content tab...", "INFO")
            prefs.tabs.setCurrentIndex(3)
            QApplication.processEvents()
            time.sleep(0.2)
            
            # Save
            self._log("Saving settings...", "INFO")
            prefs.btn_save.click()
            QApplication.processEvents()
            time.sleep(0.3)
            QTimer.singleShot(100, lambda: self._dismiss_message_box())
            QApplication.processEvents()
            time.sleep(0.3)
            
            prefs.close()
            QApplication.processEvents()
            time.sleep(0.3)
            
            # Reopen and verify Content tab is still selected
            prefs2 = PreferencesDialog(self)
            QApplication.processEvents()
            time.sleep(0.2)
            
            final_tab = prefs2.tabs.currentIndex()
            self._log(f"Tab after cross-tab navigation: {final_tab}", "INFO")
            
            test_passed = (final_tab == 3)
            
            if test_passed:
                self._log("✓ Cross-tab interaction test PASSED", "PASS")
            else:
                self._log(f"✗ Cross-tab interaction test FAILED (expected 3, got {final_tab})", "FAIL")
            
            prefs2.close()
            
            self.test_results.append(("Test 3: Cross-Tab Interaction", test_passed))
            
            # Continue to next test
            QTimer.singleShot(1000, self._run_test_4)
            
        except Exception as e:
            self._log(f"Test 3 ERROR: {e}", "FAIL")
            self.test_results.append(("Test 3: Cross-Tab Interaction", False))
            QTimer.singleShot(1000, self._run_test_4)
    
    def _run_test_4(self):
        """Test 4: Edge Cases - None Material"""
        self._log("", "INFO")
        self._log("TEST 4: Edge Cases - None Material Test", "TEST")
        self._log("-" * 80, "INFO")
        
        try:
            prefs = PreferencesDialog(self)
            content_tab = prefs.thumbnail_settings_tab
            
            # Select "None (Default)" material
            self._log("Setting material to 'None (Default)'...", "INFO")
            content_tab.material_combo.setCurrentIndex(0)
            QApplication.processEvents()
            time.sleep(0.2)
            
            # Save
            prefs.btn_save.click()
            QApplication.processEvents()
            time.sleep(0.3)
            QTimer.singleShot(100, lambda: self._dismiss_message_box())
            QApplication.processEvents()
            time.sleep(0.3)
            
            prefs.close()
            QApplication.processEvents()
            
            # Verify
            settings = QSettings()
            saved_mat = settings.value("thumbnail/material", None)
            self._log(f"Saved material: {saved_mat}", "INFO")
            
            # Reopen
            prefs2 = PreferencesDialog(self)
            content_tab2 = prefs2.thumbnail_settings_tab
            restored_mat = content_tab2.material_combo.currentData()
            
            self._log(f"Restored material: {restored_mat}", "INFO")
            
            test_passed = (restored_mat == saved_mat)
            
            if test_passed:
                self._log("✓ None material test PASSED", "PASS")
            else:
                self._log("✗ None material test FAILED", "FAIL")
            
            prefs2.close()
            
            self.test_results.append(("Test 4: Edge Cases", test_passed))
            
            # Show summary
            QTimer.singleShot(1000, self._show_test_summary)
            
        except Exception as e:
            self._log(f"Test 4 ERROR: {e}", "FAIL")
            self.test_results.append(("Test 4: Edge Cases", False))
            QTimer.singleShot(1000, self._show_test_summary)
    
    def _show_test_summary(self):
        """Show comprehensive test summary."""
        self._log("", "INFO")
        self._log("=" * 80, "TEST")
        self._log("COMPREHENSIVE TEST SUITE COMPLETE", "TEST")
        self._log("=" * 80, "TEST")
        self._log("", "INFO")
        
        passed = sum(1 for _, result in self.test_results if result)
        total = len(self.test_results)
        
        self._log(f"Results: {passed}/{total} tests passed", "INFO")
        self._log("", "INFO")
        
        for test_name, result in self.test_results:
            if result:
                self._log(f"  ✓ {test_name}", "PASS")
            else:
                self._log(f"  ✗ {test_name}", "FAIL")
        
        self._log("", "INFO")
        
        if passed == total:
            self._log("🎉 ALL TESTS PASSED! Preferences persistence is fully functional!", "PASS")
        else:
            self._log(f"⚠ {total - passed} test(s) failed. Review logs above for details.", "WARN")
        
        self._log("", "INFO")
        self._log("You can now:", "INFO")
        self._log("  • Use 'Open Preferences' for additional manual testing", "INFO")
        self._log("  • Use 'Inspect QSettings' to verify storage", "INFO")
        self._log("  • Restart the application to test app-level persistence", "INFO")
        
        self.btn_start.setEnabled(True)
    
    def _dismiss_message_box(self):
        """Dismiss any open message box."""
        try:
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QMessageBox) and widget.isVisible():
                    widget.accept()
        except Exception:
            pass


def main():
    """Main test entry point."""
    app = QApplication(sys.argv)
    app.setOrganizationName("3DMM")
    app.setApplicationName("3DModelManager")
    
    controller = TestController()
    controller.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()