"""
Test script to verify async model loading doesn't block the UI.

This script simulates loading multiple models and measures UI responsiveness.
"""

import sys
import time
from pathlib import Path
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import QTimer, Qt

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gui.model_library import ModelLibraryWidget


class TestWindow(QMainWindow):
    """Test window to verify UI responsiveness during model loading."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Async Model Loading Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Add status label
        self.status_label = QLabel("Ready - Click button to test UI responsiveness")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Add test button
        self.test_button = QPushButton("Test UI Responsiveness (Click rapidly)")
        self.test_button.clicked.connect(self.on_test_click)
        self.click_count = 0
        layout.addWidget(self.test_button)
        
        # Add model library
        self.model_library = ModelLibraryWidget()
        layout.addWidget(self.model_library)
        
        # Timer to update status
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(100)  # Update every 100ms
        
        self.last_update = time.time()
        self.frame_times = []
        
    def on_test_click(self):
        """Handle test button click."""
        self.click_count += 1
        self.test_button.setText(f"Clicks: {self.click_count} (UI is responsive!)")
        
    def update_status(self):
        """Update status to show UI responsiveness."""
        current_time = time.time()
        frame_time = (current_time - self.last_update) * 1000  # Convert to ms
        self.last_update = current_time
        
        # Keep last 10 frame times
        self.frame_times.append(frame_time)
        if len(self.frame_times) > 10:
            self.frame_times.pop(0)
        
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        
        # Update status
        if avg_frame_time > 200:
            status = f"⚠️ UI BLOCKED - Frame time: {avg_frame_time:.1f}ms (should be ~100ms)"
            self.status_label.setStyleSheet("color: red; font-weight: bold;")
        elif avg_frame_time > 150:
            status = f"⚠️ UI SLOW - Frame time: {avg_frame_time:.1f}ms (should be ~100ms)"
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
        else:
            status = f"✅ UI RESPONSIVE - Frame time: {avg_frame_time:.1f}ms"
            self.status_label.setStyleSheet("color: green;")
        
        self.status_label.setText(status)


def main():
    """Run the test application."""
    app = QApplication(sys.argv)
    
    window = TestWindow()
    window.show()
    
    print("\n" + "="*80)
    print("ASYNC MODEL LOADING TEST")
    print("="*80)
    print("\nInstructions:")
    print("1. Import some models using the file browser")
    print("2. While models are loading, rapidly click the 'Test UI Responsiveness' button")
    print("3. Watch the status label:")
    print("   - ✅ GREEN = UI is responsive (good!)")
    print("   - ⚠️ ORANGE = UI is slow (acceptable)")
    print("   - ⚠️ RED = UI is blocked (bad!)")
    print("\nIf the UI remains GREEN/ORANGE during loading, the async implementation works!")
    print("If the UI turns RED, the main thread is being blocked.")
    print("="*80 + "\n")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

