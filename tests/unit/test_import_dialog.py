"""
Test script for the ImportDialog UI component.

This script demonstrates how to use the ImportDialog for importing 3D models
with progress tracking and all backend service integration.

Usage:
    python test_import_dialog.py
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import Qt

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gui.import_components import ImportDialog
from src.core.logging_config import setup_logging


class TestWindow(QMainWindow):
    """Test window for ImportDialog."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Import Dialog Test")
        self.setGeometry(100, 100, 400, 200)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setAlignment(Qt.AlignCenter)
        
        # Test button
        self.import_button = QPushButton("Open Import Dialog")
        self.import_button.setMinimumSize(200, 50)
        self.import_button.clicked.connect(self.open_import_dialog)
        layout.addWidget(self.import_button)
        
        # Results label
        from PySide6.QtWidgets import QLabel
        self.result_label = QLabel("No imports yet")
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setWordWrap(True)
        layout.addWidget(self.result_label)
    
    def open_import_dialog(self):
        """Open the import dialog."""
        dialog = ImportDialog(self)
        
        if dialog.exec() == ImportDialog.Accepted:
            result = dialog.get_import_result()
            
            if result:
                self.result_label.setText(
                    f"Import Completed!\n\n"
                    f"Total Files: {result.total_files}\n"
                    f"Processed: {result.processed_files}\n"
                    f"Failed: {result.failed_files}\n"
                    f"Skipped: {result.skipped_files}\n"
                    f"Duplicates: {result.duplicate_count}\n"
                    f"Duration: {result.duration_seconds:.2f}s\n"
                    f"Size: {result.total_size_bytes / (1024 * 1024):.2f} MB"
                )
            else:
                self.result_label.setText("Import was cancelled or failed")
        else:
            self.result_label.setText("Import was cancelled")


def main():
    """Main test function."""
    # Setup logging
    setup_logging()
    
    # Create application
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show test window
    window = TestWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()