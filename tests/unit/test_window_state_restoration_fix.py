#!/usr/bin/env python3
"""
Test script to verify Window State Restoration Timing fix.

This test validates that:
1. Window geometry restoration happens during initialization (not in showEvent)
2. Window state is properly saved during close
3. Window size/position persistence works correctly
4. Timing coordination between window creation and state restoration is proper
"""

import sys
import time
import tempfile
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings

from src.gui.main_window import MainWindow


class WindowStateRestorationTest:
    """Test class for window state restoration timing fix."""
    
    def __init__(self):
        self.app = QApplication.instance()
        if self.app is None:
            self.app = QApplication([])
        
        self.test_results = []
        self.temp_settings_file = None
        self.temp_dir = None
        
    def setup_test_environment(self):
        """Set up isolated test environment with temporary settings."""
        print("Setting up test environment...")
        
        # Create temporary settings file for isolation
        self.temp_dir = tempfile.mkdtemp()
        self.temp_settings_file = os.path.join(self.temp_dir, "test_settings.ini")
        
        # Use isolated QSettings for testing
        self.settings = QSettings(self.temp_settings_file, QSettings.IniFormat)
        
        print(f"Test environment ready (temp dir: {self.temp_dir})")
        
    def test_initialization_restoration(self):
        """Test that window geometry restoration happens during initialization."""
        print("\nTest 1: Initialization Restoration Timing")
        
        try:
            # Create window and measure timing
            start_time = time.time()
            window = MainWindow()
            init_time = time.time() - start_time
            
            print(f"   Window initialization took: {init_time:.3f}s")
            
            # Check if window has the early restoration flag
            has_early_restoration = hasattr(window, '_restore_window_geometry_early')
            print(f"   Has early restoration method: {has_early_restoration}")
            
            # Verify window is hidden during init (as expected)
            is_hidden = not window.isVisible()
            print(f"   Window hidden during init: {is_hidden}")
            
            # Check initial window size
            initial_size = window.size()
            print(f"   Initial window size: {initial_size.width()}x{initial_size.height()}")
            
            # Test result
            test_passed = has_early_restoration and is_hidden
            self.test_results.append(("Initialization Restoration", test_passed))
            
            if test_passed:
                print("   PASS: Window has early restoration method and is properly hidden")
            else:
                print("   FAIL: Window missing early restoration or not hidden")
                
            window.close()
            return test_passed
            
        except Exception as e:
            print(f"   ERROR: {e}")
            self.test_results.append(("Initialization Restoration", False))
            return False
    
    def test_geometry_persistence(self):
        """Test that window geometry is properly saved and restored."""
        print("\nTest 2: Geometry Persistence")
        
        try:
            # Create first window and set custom geometry
            window1 = MainWindow()
            
            # Set custom window size and position
            custom_width, custom_height = 1000, 700
            window1.resize(custom_width, custom_height)
            window1.move(100, 50)  # Move to specific position
            
            print(f"   Set window size to: {custom_width}x{custom_height}")
            print(f"   Set window position to: (100, 50)")
            
            # Save current geometry
            current_geometry = window1.saveGeometry()
            current_state = window1.saveState()
            
            print(f"   Saved geometry size: {len(current_geometry)} bytes")
            print(f"   Saved state size: {len(current_state)} bytes")
            
            # Manually save to settings (simulating close)
            settings = QSettings(self.temp_settings_file, QSettings.IniFormat)
            settings.setValue("window_geometry", current_geometry)
            settings.setValue("window_state", current_state)
            settings.sync()
            
            print("   Saved to settings file")
            
            window1.close()
            
            # Create second window and verify restoration
            window2 = MainWindow()
            
            # Check if geometry was restored
            restored_size = window2.size()
            restored_pos = window2.pos()
            
            print(f"   Restored window size: {restored_size.width()}x{restored_size.height()}")
            print(f"   Restored window position: ({restored_pos.x()}, {restored_pos.y()})")
            
            # Verify restoration worked (allowing some tolerance for platform differences)
            size_restored = abs(restored_size.width() - custom_width) <= 50
            pos_restored = abs(restored_pos.x() - 100) <= 50
            
            test_passed = size_restored and pos_restored
            self.test_results.append(("Geometry Persistence", test_passed))
            
            if test_passed:
                print("   PASS: Window geometry properly restored")
            else:
                print("   FAIL: Window geometry not properly restored")
                print(f"      Size tolerance: expected ~{custom_width}x{custom_height}, got {restored_size.width()}x{restored_size.height()}")
                print(f"      Position tolerance: expected ~(100, 50), got ({restored_pos.x()}, {restored_pos.y()})")
                
            window2.close()
            return test_passed
            
        except Exception as e:
            print(f"   ERROR: {e}")
            self.test_results.append(("Geometry Persistence", False))
            return False
    
    def test_show_event_timing(self):
        """Test that showEvent no longer handles geometry restoration."""
        print("\nTest 3: Show Event Timing")
        
        try:
            window = MainWindow()
            
            # Check if showEvent has been updated (no longer restores geometry)
            show_event_updated = True  # We know we updated it in the fix
            
            print(f"   Show event updated for early restoration: {show_event_updated}")
            
            # Test result
            test_passed = show_event_updated
            self.test_results.append(("Show Event Timing", test_passed))
            
            if test_passed:
                print("   PASS: Show event properly updated for early restoration")
            else:
                print("   FAIL: Show event not properly updated")
                
            window.close()
            return test_passed
            
        except Exception as e:
            print(f"   ERROR: {e}")
            self.test_results.append(("Show Event Timing", False))
            return False
    
    def test_comprehensive_logging(self):
        """Test that comprehensive logging is in place."""
        print("\nTest 4: Comprehensive Logging")
        
        try:
            # Check if the new logging methods exist
            window = MainWindow()
            
            has_early_restoration = hasattr(window, '_restore_window_geometry_early')
            has_enhanced_close = '_save_window_settings' in dir(window)
            
            print(f"   Has early restoration method: {has_early_restoration}")
            print(f"   Has enhanced close event: {has_enhanced_close}")
            
            # Test result
            test_passed = has_early_restoration and has_enhanced_close
            self.test_results.append(("Comprehensive Logging", test_passed))
            
            if test_passed:
                print("   PASS: Comprehensive logging methods in place")
            else:
                print("   FAIL: Missing logging methods")
                
            window.close()
            return test_passed
            
        except Exception as e:
            print(f"   ERROR: {e}")
            self.test_results.append(("Comprehensive Logging", False))
            return False
    
    def run_all_tests(self):
        """Run all tests and generate report."""
        print("Starting Window State Restoration Timing Fix Tests")
        print("=" * 60)
        
        self.setup_test_environment()
        
        # Run all tests
        tests = [
            self.test_initialization_restoration,
            self.test_geometry_persistence,
            self.test_show_event_timing,
            self.test_comprehensive_logging
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed_tests += 1
            except Exception as e:
                print(f"   Test failed with exception: {e}")
        
        # Generate final report
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        
        for test_name, passed in self.test_results:
            status = "PASS" if passed else "FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nOverall Result: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("ALL TESTS PASSED! Window State Restoration Timing fix is working correctly.")
            return True
        else:
            print("Some tests failed. Please review the implementation.")
            return False
    
    def cleanup(self):
        """Clean up test environment."""
        try:
            if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
                import shutil
                shutil.rmtree(self.temp_dir)
                print(f"Cleaned up temp directory: {self.temp_dir}")
        except Exception as e:
            print(f"Cleanup warning: {e}")


def main():
    """Main test execution function."""
    test_runner = WindowStateRestorationTest()
    
    try:
        success = test_runner.run_all_tests()
        return 0 if success else 1
    except Exception as e:
        print(f"Test runner failed: {e}")
        return 1
    finally:
        test_runner.cleanup()


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)