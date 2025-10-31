#!/usr/bin/env python3
"""
Test script for the tabbed lighting control panel.
"""

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from src.gui.lighting_control_panel import LightingControlPanel


class TestMainWindow(QMainWindow):
    """Test main window to host the lighting control panel."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tabbed Lighting Panel Test")
        self.setGeometry(100, 100, 600, 400)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create layout
        layout = QVBoxLayout(central_widget)
        
        # Add button to show lighting panel
        self.show_panel_button = QPushButton("Show Lighting Control Panel")
        self.show_panel_button.clicked.connect(self.show_lighting_panel)
        layout.addWidget(self.show_panel_button)
        
        # Create lighting control panel
        self.lighting_panel = LightingControlPanel(self)
        
        # Connect signals to test functionality
        self._connect_signals()
        
    def _connect_signals(self):
        """Connect lighting panel signals for testing."""
        # Spot light signals
        self.lighting_panel.position_changed.connect(self.on_position_changed)
        self.lighting_panel.color_changed.connect(self.on_color_changed)
        self.lighting_panel.intensity_changed.connect(self.on_intensity_changed)
        self.lighting_panel.cone_angle_changed.connect(self.on_cone_angle_changed)
        
        # Headlight signals
        self.lighting_panel.headlight_intensity_changed.connect(self.on_headlight_intensity_changed)
        self.lighting_panel.headlight_enabled_changed.connect(self.on_headlight_enabled_changed)
        self.lighting_panel.headlight_color_changed.connect(self.on_headlight_color_changed)
        
    def show_lighting_panel(self):
        """Show the lighting control panel."""
        self.lighting_panel.show()
        
    def on_position_changed(self, x, y, z):
        print(f"Spot light position changed: X={x:.1f}, Y={y:.1f}, Z={z:.1f}")
        
    def on_color_changed(self, r, g, b):
        print(f"Spot light color changed: R={r:.2f}, G={g:.2f}, B={b:.2f}")
        
    def on_intensity_changed(self, intensity):
        print(f"Spot light intensity changed: {intensity:.2f}")
        
    def on_cone_angle_changed(self, angle):
        print(f"Spot light cone angle changed: {angle:.1f}°")
        
    def on_headlight_intensity_changed(self, intensity):
        print(f"Headlight intensity changed: {intensity:.2f}")
        
    def on_headlight_enabled_changed(self, enabled):
        print(f"Headlight enabled changed: {enabled}")
        
    def on_headlight_color_changed(self, r, g, b):
        print(f"Headlight color changed: R={r:.2f}, G={g:.2f}, B={b:.2f}")


def main():
    """Main function to run the test."""
    app = QApplication(sys.argv)
    
    # Create test window
    window = TestMainWindow()
    window.show()
    
    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()