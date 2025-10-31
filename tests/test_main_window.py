#!/usr/bin/env python3
"""
Test main window creation to isolate the initialization issue.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

def test_main_window_creation():
    """Test creating a main window instance step by step."""
    print("Testing main window creation...")
    
    try:
        print("1. Creating QApplication...")
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import QTimer
        
        app = QApplication.instance()
        if not app:
            app = QApplication([])
        print("SUCCESS: QApplication created")
        
        print("2. Creating MainWindow instance...")
        from src.gui.main_window import MainWindow
        window = MainWindow()
        print("SUCCESS: MainWindow instance created")
        
        print("3. Testing window hide/show...")
        window.hide()
        print("SUCCESS: Window hide successful")
        
        # Use a timer to automatically quit after testing
        QTimer.singleShot(100, app.quit)
        app.exec()
        
        print("SUCCESS: Main window test completed!")
        return True
        
    except Exception as e:
        print(f"FAILED: Main window test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Candy-Cadence Main Window Test")
    print("=" * 50)
    
    if test_main_window_creation():
        print("\nMain window test passed!")
    else:
        print("\nMain window test failed!")
        sys.exit(1)