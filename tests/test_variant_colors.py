#!/usr/bin/env python3
"""
Test that variants actually change the primary colors in the UI.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_variant_color_differences():
    """Test that different variants produce different primary colors."""
    print("=== TESTING VARIANT COLOR DIFFERENCES ===")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        
        # Create QApplication
        app = QApplication([])
        
        # Get theme service
        service = QtMaterialThemeService.instance()
        
        # Test each variant with dark theme and see the colors
        variants = ["blue", "amber", "cyan"]
        
        for variant in variants:
            print(f"\nTesting dark/{variant} theme:")
            
            # Apply the theme
            result = service.apply_theme("dark", variant)
            print(f"  Apply result: {result}")
            
            # Get current theme
            current_theme, current_variant = service.get_current_theme()
            print(f"  Current theme: {current_theme}")
            print(f"  Current variant: {current_variant}")
            
            # Check the application stylesheet
            stylesheet = app.styleSheet()
            if stylesheet:
                # Look for primary color in stylesheet
                lines = stylesheet.split('\n')
                for line in lines:
                    if 'background-color:' in line and any(color in line for color in ['#1976D2', '#FFA000', '#00ACC1']):
                        print(f"  Primary color line: {line.strip()}")
                        break
                else:
                    # If we didn't find the primary color lines, look for QPushButton styling
                    for line in lines:
                        if 'QPushButton' in line and 'background-color:' in line:
                            print(f"  Button color line: {line.strip()}")
                            break
            else:
                print("  No stylesheet found")
        
        # Test light variants too
        print(f"\nTesting light variants:")
        for variant in variants:
            print(f"\nTesting light/{variant} theme:")
            service.apply_theme("light", variant)
            current_theme, current_variant = service.get_current_theme()
            print(f"  Current: {current_theme}/{current_variant}")
            
            # Check for color differences
            stylesheet = app.styleSheet()
            if stylesheet:
                lines = stylesheet.split('\n')
                for line in lines:
                    if 'QPushButton' in line and 'background-color:' in line:
                        print(f"  Button color: {line.strip()}")
                        break
        
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_variant_applied_colors():
    """Test what colors are actually being used for each variant."""
    print("\n=== TESTING ACTUAL COLORS USED ===")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        
        app = QApplication([])
        service = QtMaterialThemeService.instance()
        
        # Expected colors for dark theme variants
        expected_colors = {
            "blue": "#1976D2",
            "amber": "#FFA000", 
            "cyan": "#00ACC1"
        }
        
        print("Expected primary colors for dark theme:")
        for variant, color in expected_colors.items():
            print(f"  {variant}: {color}")
        
        print("\nActual colors applied:")
        for variant in expected_colors.keys():
            service.apply_theme("dark", variant)
            
            # Get the stylesheet and extract the actual color used
            stylesheet = app.styleSheet()
            if stylesheet:
                lines = stylesheet.split('\n')
                for line in lines:
                    if 'background-color:' in line and any(c in line for c in ['#1976D2', '#FFA000', '#00ACC1', '#42A5F5', '#FFB74D', '#4DD0E1']):
                        print(f"  dark/{variant}: {line.strip()}")
                        break
        
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("Testing Variant Color Application")
    print("=" * 40)
    
    success = True
    
    # Test 1: Color differences between variants
    if not test_variant_color_differences():
        success = False
    
    # Test 2: Actual colors used
    if not test_variant_applied_colors():
        success = False
    
    print("\n" + "=" * 40)
    if success:
        print("Variant color tests completed!")
    else:
        print("Some tests failed!")
    
    return success

if __name__ == "__main__":
    main()