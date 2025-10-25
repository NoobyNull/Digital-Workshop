#!/usr/bin/env python3
"""Test G-code Previewer widget creation."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_widget_creation():
    """Test creating the G-code Previewer widget."""
    print("Testing G-code Previewer widget creation...")
    
    try:
        from PySide6.QtWidgets import QApplication
        
        # Create QApplication
        app = QApplication.instance() or QApplication(sys.argv)
        print("✓ QApplication created")
        
        # Try to import the widget
        from src.gui.gcode_previewer_components import GcodePreviewerWidget
        print("✓ GcodePreviewerWidget imported")
        
        # Try to create the widget
        widget = GcodePreviewerWidget()
        print("✓ GcodePreviewerWidget created")
        
        # Show the widget
        widget.show()
        print("✓ Widget shown")
        
        # Process events
        app.processEvents()
        print("✓ Events processed")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_widget_creation()
    sys.exit(0 if success else 1)

