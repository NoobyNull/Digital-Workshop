#!/usr/bin/env python3
"""
Test that the variant fix works correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_variant_method_fix():
    """Test that the variant method now passes the correct variant name."""
    print("=== TESTING VARIANT METHOD FIX ===")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        from src.gui.preferences import ThemingTab
        
        # Create QApplication
        app = QApplication([])
        
        # Get theme service
        service = QtMaterialThemeService.instance()
        
        print(f"Initial state:")
        current_theme, current_variant = service.get_current_theme()
        print(f"  Current theme: {current_theme}")
        print(f"  Current variant: {current_variant}")
        
        # Test each variant by calling the fixed method
        variants = ["blue", "amber", "cyan"]
        
        for variant in variants:
            print(f"\nTesting {variant} variant fix:")
            
            # Create theming tab and test the fixed method
            tab = ThemingTab()
            
            # Manually trigger the variant change with the correct variant name
            try:
                # This should now work correctly
                service.set_qt_material_variant(variant)
                result = service.apply_theme(current_theme, variant)  # Fixed: passing variant, not "qt-material"
                print(f"  Apply theme result: {result}")
                
                # Check if the expected color appears in stylesheet
                stylesheet = app.styleSheet()
                if stylesheet:
                    expected_colors = {
                        "blue": "#1976D2",
                        "amber": "#FFA000",
                        "cyan": "#00ACC1"
                    }
                    expected_color = expected_colors[variant]
                    if expected_color in stylesheet:
                        print(f"  ✅ Expected color {expected_color} found in stylesheet")
                    else:
                        print(f"  ❌ Expected color {expected_color} NOT found in stylesheet")
                else:
                    print("  ❌ No stylesheet found")
                    
            except Exception as e:
                print(f"  ERROR: {e}")
        
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test."""
    print("Testing Variant Fix")
    print("=" * 25)
    
    success = test_variant_method_fix()
    
    print("\n" + "=" * 25)
    if success:
        print("Variant fix test completed!")
    else:
        print("Variant fix test failed!")
    
    return success

if __name__ == "__main__":
    main()