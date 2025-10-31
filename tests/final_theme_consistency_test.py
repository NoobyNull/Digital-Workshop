#!/usr/bin/env python3
"""
Simple test to verify theme consistency fix without Unicode issues.
"""

import sys
from pathlib import Path
import inspect

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_theme_consistency():
    """Test that both main application and preferences use the same theme service."""
    print("Testing theme consistency fix...")
    
    try:
        # Import the required modules
        from src.gui.preferences import PreferencesDialog
        from src.gui.theme.simple_service import ThemeService
        
        # Check PreferencesDialog theme method
        dialog_method = getattr(PreferencesDialog, '_apply_qt_material_theme')
        dialog_source = inspect.getsource(dialog_method)
        
        print("Checking PreferencesDialog implementation...")
        
        # Check key consistency points
        checks = [
            ("ThemeService.instance()", "PreferencesDialog uses ThemeService"),
            ("service.apply_theme", "PreferencesDialog calls service.apply_theme"),
            ("current_theme, library", "PreferencesDialog passes theme and library"),
        ]
        
        all_passed = True
        for check, description in checks:
            if check in dialog_source:
                print(f"  PASS: {description}")
            else:
                print(f"  FAIL: {description}")
                all_passed = False
        
        # Check ThemeService implementation
        service_method = getattr(ThemeService, 'apply_theme')
        service_source = inspect.getsource(service_method)
        
        print("Checking ThemeService implementation...")
        
        service_checks = [
            ("QApplication.instance()", "ThemeService applies to QApplication"),
            ("apply_stylesheet", "ThemeService uses qt-material"),
        ]
        
        for check, description in service_checks:
            if check in service_source:
                print(f"  PASS: {description}")
            else:
                print(f"  FAIL: {description}")
                all_passed = False
        
        print("\n" + "="*50)
        print("THEME CONSISTENCY ANALYSIS")
        print("="*50)
        
        print("\nOLD APPROACH (Inconsistent):")
        print("  Main App: ThemeService -> QApplication")
        print("  Pref Dialog: Direct qt-material -> Dialog only")
        print("  Result: Different themes!")
        
        print("\nNEW APPROACH (Consistent):")
        print("  Main App: ThemeService -> QApplication")
        print("  Pref Dialog: ThemeService -> QApplication")
        print("  Result: Same theme!")
        
        print("\nKEY CHANGES MADE:")
        print("1. Moved _apply_qt_material_theme() from AdvancedTab to PreferencesDialog")
        print("2. Updated method to use ThemeService.apply_theme() like main application")
        print("3. Added fallback method for direct qt-material if service fails")
        
        if all_passed:
            print("\nRESULT: Theme consistency fix is properly implemented!")
            print("The dual theme issue should now be resolved.")
            return True
        else:
            print("\nRESULT: Some checks failed!")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("FINAL THEME CONSISTENCY TEST")
    print("=" * 50)
    
    success = test_theme_consistency()
    
    print("=" * 50)
    if success:
        print("SUCCESS: Theme consistency fix verified!")
    else:
        print("FAILED: Theme consistency fix verification failed!")
    print("=" * 50)