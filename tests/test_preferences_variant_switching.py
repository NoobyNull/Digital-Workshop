#!/usr/bin/env python3
"""
Test that the preferences dialog variant switching works correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_preferences_variant_switching():
    """Test that preferences dialog variant switching works correctly."""
    print("=== TESTING PREFERENCES DIALOG VARIANT SWITCHING ===")
    
    try:
        from PySide6.QtWidgets import QApplication
        from src.gui.theme.qt_material_service import QtMaterialThemeService
        from src.gui.preferences import PreferencesDialog, ThemingTab
        
        # Create QApplication
        app = QApplication([])
        
        # Get theme service
        service = QtMaterialThemeService.instance()
        
        print(f"Initial state:")
        current_theme, current_variant = service.get_current_theme()
        print(f"  Current theme: {current_theme}")
        print(f"  Current variant: {current_variant}")
        
        # Create preferences dialog and theming tab
        print("\nCreating preferences dialog...")
        dialog = PreferencesDialog()
        dialog.show()
        
        # Get the theming tab
        theming_tab = dialog.theming_tab
        
        print("Testing variant switching through preferences dialog...")
        
        # Test each variant
        variants = ["blue", "amber", "cyan"]
        
        for variant in variants:
            print(f"\nSwitching to {variant} variant through preferences:")
            
            try:
                # Simulate the variant change via the preferences dialog method
                theming_tab._on_material_variant_changed(variant)
                
                # Check current state
                current_theme, current_variant = service.get_current_theme()
                print(f"  After change: theme={current_theme}, variant={current_variant}")
                
                if current_variant == variant:
                    print(f"  SUCCESS: Variant changed to {variant}")
                else:
                    print(f"  ERROR: Expected variant {variant}, got {current_variant}")
                    
            except Exception as e:
                print(f"  ERROR: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"\nFinal state:")
        current_theme, current_variant = service.get_current_theme()
        print(f"  Current theme: {current_theme}")
        print(f"  Current variant: {current_variant}")
        
        dialog.close()
        
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test."""
    print("Testing Preferences Dialog Variant Switching")
    print("=" * 45)
    
    success = test_preferences_variant_switching()
    
    print("\n" + "=" * 45)
    if success:
        print("Preferences dialog variant switching test completed!")
    else:
        print("Preferences dialog variant switching test failed!")
    
    return success

if __name__ == "__main__":
    main()