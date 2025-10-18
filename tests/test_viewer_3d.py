#!/usr/bin/env python3
"""
Test script to verify the 3D viewer implementation with PySide6.Qt3D.

This script tests the viewer widget with sample STL files to ensure
the migration from PyQt3D to PySide6.Qt3D was successful.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QFileDialog
from PySide6.QtCore import Qt

# Try to import VTK-based viewer first
try:
    from gui.viewer_widget_vtk import Viewer3DWidget
except ImportError:
    # Fallback to original viewer if VTK is not available
    try:
        from gui.viewer_widget import Viewer3DWidget
    except ImportError:
        print("Neither VTK nor PyQt3D viewer is available")
        sys.exit(1)
from parsers.stl_parser import STLParser


class TestViewerWindow(QMainWindow):
    """Test window for the 3D viewer widget."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Viewer Test - PySide6.Qt3D")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Create viewer widget
        self.viewer = Viewer3DWidget()
        layout.addWidget(self.viewer)
        
        # Create control buttons
        button_layout = QVBoxLayout()
        
        # Load sample STL button
        self.load_sample_button = QPushButton("Load Sample STL")
        self.load_sample_button.clicked.connect(self.load_sample_stl)
        button_layout.addWidget(self.load_sample_button)
        
        # Load custom file button
        self.load_file_button = QPushButton("Load Custom STL")
        self.load_file_button.clicked.connect(self.load_custom_stl)
        button_layout.addWidget(self.load_file_button)
        
        # Reset view button
        self.reset_button = QPushButton("Reset View")
        self.reset_button.clicked.connect(self.viewer.reset_view)
        button_layout.addWidget(self.reset_button)
        
        layout.addLayout(button_layout)
        
        # Load sample STL on startup
        self.load_sample_stl()
    
    def load_sample_stl(self):
        """Load a sample STL file."""
        sample_path = Path(__file__).parent / "tests" / "sample_files" / "cube_binary.stl"
        if sample_path.exists():
            self.load_stl_file(str(sample_path))
        else:
            print(f"Sample STL file not found: {sample_path}")
    
    def load_custom_stl(self):
        """Load a custom STL file selected by the user."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select STL File",
            "",
            "STL Files (*.stl);;All Files (*)"
        )
        
        if file_path:
            self.load_stl_file(file_path)
    
    def load_stl_file(self, file_path):
        """Load an STL file into the viewer."""
        try:
            print(f"Loading STL file: {file_path}")
            
            # Parse the STL file
            parser = STLParser()
            model = parser.parse_file(file_path)
            
            if model:
                # Load the model into the viewer
                success = self.viewer.load_model(model)
                if success:
                    print(f"Successfully loaded model with {model.stats.triangle_count} triangles")
                else:
                    print("Failed to load model into viewer")
            else:
                print("Failed to parse STL file")
                
        except Exception as e:
            print(f"Error loading STL file: {str(e)}")
            import traceback
            traceback.print_exc()


def main():
    """Main function to run the test viewer."""
    app = QApplication(sys.argv)
    
    # Create and show the test window
    window = TestViewerWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()