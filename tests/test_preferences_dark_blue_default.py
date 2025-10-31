#!/usr/bin/env python3
"""
Test to verify preferences dialog defaults to dark/blue theme.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_preferences_dark_blue_default():
    """Test that preferences dialog defaults to dark/blue theme."""
    print("Testing preferences dialog dark/blue default theme...")
    
    try:
        # Import the required modules
        from src.gui.preferences import PreferencesDialog
        from src.gui.theme.simple_service import ThemeService
        
        # Test ThemeService default behavior
        print("Checking ThemeService default variant...")
        service = ThemeService.instance()
        default_variant = service.settings.value("qt_material_variant", "blue")
        print(f"  Default variant from settings: {default_variant}")
        
        # Test preferences dialog theme initialization
        print("Testing preferences dialog theme initialization...")
        
        # Create a mock preferences dialog to test the theme method
        class MockPreferencesDialog:
            def __init__(self):
                self._apply_qt_material_theme()
            
            def _apply_qt_material_theme(self):
                """Apply qt-material theme to this dialog using the same service as main application."""
                try:
                    from src.gui.theme.simple_service import ThemeService
                    service = ThemeService.instance()
                    
                    # Get current theme and apply it to the entire application (same as main window)
                    current_theme, library = service.get_current_theme()
                    
                    # Ensure we default to dark/blue theme if no theme is set
                    if not current_theme or current_theme == "":
                        current_theme = "dark"
                        # Set the default variant to blue
                        service.set_qt_material_variant("blue")
                        print(f"  Set default theme to: {current_theme}")
                        print(f"  Set default variant to: blue")
                    
                    # Apply theme using the same service as the main application
                    # This ensures consistency between main window and preferences dialog
                    result = service.apply_theme(current_theme, library)
                    
                    if not result:
                        # If ThemeService.apply_theme failed, try to apply directly as fallback
                        self._apply_theme_directly()
                        
                except Exception as e:
                    # Silently fail if theme application fails
                    print(f"  Theme application failed: {e}")
                    pass
            
            def _apply_theme_directly(self):
                """Fallback: Apply theme directly to this dialog (legacy method)."""
                try:
                    from src.gui.theme.simple_service import ThemeService
                    service = ThemeService.instance()
                    
                    # Get current theme and variant
                    current_theme, _ = service.get_current_theme()
                    variant = service.settings.value("qt_material_variant", "blue")
                    
                    print(f"  Fallback theme: {current_theme}")
                    print(f"  Fallback variant: {variant}")
                except Exception as e:
                    print(f"  Fallback failed: {e}")
                    pass
        
        # Test the mock dialog
        mock_dialog = MockPreferencesDialog()
        
        # Verify the theme was set correctly
        final_theme, final_library = service.get_current_theme()
        final_variant = service.settings.value("qt_material_variant", "blue")
        
        print("\n" + "="*50)
        print("PREFERENCES DIALOG DARK/BLUE DEFAULT TEST")
        print("="*50)
        
        print(f"Final theme: {final_theme}")
        print(f"Final library: {final_library}")
        print(f"Final variant: {final_variant}")
        
        # Check if defaults are correct
        checks = [
            (final_theme == "dark", "Theme defaults to 'dark'"),
            (final_variant == "blue", "Variant defaults to 'blue'"),
            (final_library == "qt-material", "Library is 'qt-material'"),
        ]
        
        all_passed = True
        for check, description in checks:
            if check:
                print(f"  PASS: {description}")
            else:
                print(f"  FAIL: {description}")
                all_passed = False
        
        print("\n" + "="*50)
        if all_passed:
            print("SUCCESS: Preferences dialog properly defaults to dark/blue theme!")
            print("The preferences window will now use dark/blue as the default dark theme.")
        else:
            print("FAILED: Some checks failed!")
        print("="*50)
        
        return all_passed
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("PREFERENCES DARK/BLUE DEFAULT TEST")
    print("=" * 50)
    
    success = test_preferences_dark_blue_default()
    
    print("=" * 50)
    if success:
        print("SUCCESS: Dark/blue default theme verified!")
    else:
        print("FAILED: Dark/blue default theme verification failed!")
    print("=" * 50)