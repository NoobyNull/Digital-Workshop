#!/usr/bin/env python3
"""
Test actual visual theme application with QApplication.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_visual_theme_with_qapp():
    """Test theme application with a real QApplication."""
    print("=== TESTING VISUAL THEME WITH QAPPLICATION ===")
    
    try:
        from PySide6.QtWidgets import QApplication, QPushButton, QVBoxLayout, QWidget
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        
        # Create QApplication
        app = QApplication([])
        
        # Create a simple test window
        window = QWidget()
        layout = QVBoxLayout(window)
        
        # Add some test buttons
        button1 = QPushButton("Test Button 1")
        button2 = QPushButton("Test Button 2")
        edit = QPushButton("Test Edit")
        
        layout.addWidget(button1)
        layout.addWidget(button2)
        layout.addWidget(edit)
        
        window.setWindowTitle("Theme Test Window")
        window.resize(300, 200)
        
        # Get theme service
        service = QtMaterialThemeService.instance()
        
        # Check current theme
        current_theme, current_variant = service.get_current_theme()
        print(f"Current theme: {current_theme}")
        print(f"Current variant: {current_variant}")
        print(f"qt-material available: {service.qtmaterial_available}")
        
        # Apply dark/blue theme
        print("\nApplying dark/blue theme...")
        result = service.apply_theme("dark", "blue")
        print(f"Apply result: {result}")
        
        # Check if stylesheet was applied
        stylesheet = app.styleSheet()
        print(f"Application stylesheet length: {len(stylesheet)}")
        if len(stylesheet) > 0:
            print("Stylesheet applied successfully!")
            # Show first few lines
            lines = stylesheet.split('\n')[:3]
            for i, line in enumerate(lines, 1):
                print(f"  Line {i}: {line[:60]}...")
        else:
            print("No stylesheet applied")
        
        # Show the window briefly to verify visual appearance
        print("\nShowing test window for 3 seconds...")
        window.show()
        
        # Test other themes
        import time
        time.sleep(1)
        
        print("Testing light/blue theme...")
        service.apply_theme("light", "blue")
        time.sleep(1)
        
        print("Testing dark/amber theme...")
        service.apply_theme("dark", "amber")
        time.sleep(1)
        
        print("Window will close...")
        window.close()
        
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test."""
    print("Testing Visual Theme Application")
    print("=" * 40)
    
    success = test_visual_theme_with_qapp()
    
    print("\n" + "=" * 40)
    if success:
        print("Visual theme test completed!")
    else:
        print("Visual theme test failed!")
    
    return success

if __name__ == "__main__":
    main()