#!/usr/bin/env python3
"""
Test script to verify window state persistence.
"""

import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, parent_dir)

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QLabel,
)
from PySide6.QtCore import QSettings, QCoreApplication, QSize, QPoint

# Initialize QSettings with organization and application names
QCoreApplication.setOrganizationName("Digital Workshop")
QCoreApplication.setApplicationName("3D Model Manager")


class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Window Persistence Test")

        # Create a simple UI
        central_widget = QWidget()
        layout = QVBoxLayout(central_widget)

        label = QLabel(
            "Resize and move this window, then close it.\nReopen to see if position/size are restored."
        )
        layout.addWidget(label)

        button = QPushButton("Close App")
        button.clicked.connect(self.close)
        layout.addWidget(button)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Set default size
        self.resize(800, 600)
        self.move(100, 100)

        # Restore saved geometry
        self._restore_window_state()

        print("Window initialized")
        print(f"Current geometry: {self.geometry()}")
        print(f"Current size: {self.size()}")
        print(f"Current position: {self.pos()}")

    def _restore_window_state(self):
        """Restore saved window geometry and state from QSettings."""
        try:
            settings = QSettings()

            # Try to restore window geometry (size and position)
            if settings.contains("window_geometry"):
                geometry_data = settings.value("window_geometry")
                if geometry_data:
                    if self.restoreGeometry(geometry_data):
                        print("[OK] Window geometry restored successfully")
                    else:
                        print("[FAIL] Failed to restore window geometry")
            else:
                print("[FAIL] No saved window geometry found")

            # Try to restore window state (maximized/normal)
            if settings.contains("window_state"):
                state_data = settings.value("window_state")
                if state_data:
                    if self.restoreState(state_data):
                        print("[OK] Window state restored successfully")
                    else:
                        print("[FAIL] Failed to restore window state")
            else:
                print("[FAIL] No saved window state found")
        except Exception as e:
            print(f"[FAIL] Failed to restore window state: {e}")

    def closeEvent(self, event):
        """Handle window close event - save settings before closing."""
        try:
            settings = QSettings()

            # Save window geometry and state
            settings.setValue("window_geometry", self.saveGeometry())
            settings.setValue("window_state", self.saveState())

            print("[OK] Window geometry and state saved")
            print(f"Saved geometry: {self.geometry()}")
            print(f"Saved size: {self.size()}")
            print(f"Saved position: {self.pos()}")
        except Exception as e:
            print(f"[FAIL] Failed to save window settings: {e}")

        super().closeEvent(event)


def main():
    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    print("\nWindow shown. Resize/move it and close to test persistence.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
