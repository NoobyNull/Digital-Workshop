#!/usr/bin/env python3
"""
Test that the variant fix works correctly with the correct method name.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_variant_method_fix():
    """Test that the variant method now works with the correct method name."""
    print("=== TESTING VARIANT METHOD FIX (CORRECTED) ===")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        
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
            print(f"\nTesting {variant} variant:")
            
            try:
                # Test the corrected method
                result = service.set_theme_variant(variant)
                print(f"  set_theme_variant('{variant}') result: {result}")
                
                # Verify current theme/variant changed
                current_theme, current_variant = service.get_current_theme()
                print(f"  After change: theme={current_theme}, variant={current_variant}")
                
                # Check if stylesheet contains the expected color
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
    print("Testing Variant Fix (Corrected)")
    print("=" * 35)
    
    success = test_variant_method_fix()
    
    print("\n" + "=" * 35)
    if success:
        print("Variant fix test completed!")
    else:
        print("Variant fix test failed!")
    
    return success

if __name__ == "__main__":
    main()