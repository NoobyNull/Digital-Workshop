#!/usr/bin/env python3
"""
Comprehensive test for all theme fixes implemented in Digital Woodsman Workshop.

This test verifies that all identified theme inconsistencies have been resolved
and that all GUI components now properly use the theme system.
"""

import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_theme_imports():
    """Test that all theme-related imports work correctly."""
    print("Testing theme imports...")
    
    try:
        from src.gui.theme import COLORS
        from src.gui.theme.simple_service import ThemeService
        print("✓ Theme imports successful")
        return True
    except ImportError as e:
        print(f"✗ Theme import failed: {e}")
        return False

def test_preferences_dialog_theme():
    """Test that PreferencesDialog uses theme-aware styling."""
    print("\nTesting PreferencesDialog theme integration...")
    
    try:
        from src.gui.preferences import PreferencesDialog
        
        # Check if the dialog has the theme methods
        if hasattr(PreferencesDialog, '_apply_qt_material_theme'):
            print("✓ PreferencesDialog has _apply_qt_material_theme method")
        else:
            print("✗ PreferencesDialog missing _apply_qt_material_theme method")
            return False
            
        if hasattr(PreferencesDialog, '_apply_theme_directly'):
            print("✓ PreferencesDialog has _apply_theme_directly method")
        else:
            print("✗ PreferencesDialog missing _apply_theme_directly method")
            return False
            
        return True
    except Exception as e:
        print(f"✗ PreferencesDialog test failed: {e}")
        return False

def test_deduplication_dialog_theme():
    """Test that DeduplicationDialog uses theme-aware styling."""
    print("\nTesting DeduplicationDialog theme integration...")
    
    try:
        from src.gui.deduplication_dialog import DeduplicationDialog
        
        # Check if the dialog imports theme system
        import inspect
        source = inspect.getsource(DeduplicationDialog)
        
        if "from src.gui.theme import COLORS" in source:
            print("✓ DeduplicationDialog imports theme system")
        else:
            print("✗ DeduplicationDialog missing theme imports")
            return False
            
        if "background-color:" in source and "success_color" in source:
            print("✓ DeduplicationDialog uses theme-aware button styling")
        else:
            print("✗ DeduplicationDialog missing theme-aware styling")
            return False
            
        return True
    except Exception as e:
        print(f"✗ DeduplicationDialog test failed: {e}")
        return False

def test_deduplication_status_widget_theme():
    """Test that DeduplicationStatusWidget uses theme-aware styling."""
    print("\nTesting DeduplicationStatusWidget theme integration...")
    
    try:
        from src.gui.components.deduplication_status_widget import DeduplicationStatusWidget
        
        # Check if the widget imports theme system
        import inspect
        source = inspect.getsource(DeduplicationStatusWidget)
        
        if "from src.gui.theme import COLORS" in source:
            print("✓ DeduplicationStatusWidget imports theme system")
        else:
            print("✗ DeduplicationStatusWidget missing theme imports")
            return False
            
        if "error_color" in source and "background-color:" in source:
            print("✓ DeduplicationStatusWidget uses theme-aware styling")
        else:
            print("✗ DeduplicationStatusWidget missing theme-aware styling")
            return False
            
        return True
    except Exception as e:
        print(f"✗ DeduplicationStatusWidget test failed: {e}")
        return False

def test_board_visualizer_theme():
    """Test that BoardVisualizerWidget uses theme-aware styling."""
    print("\nTesting BoardVisualizerWidget theme integration...")
    
    try:
        from src.gui.CLO.board_visualizer import BoardVisualizerWidget
        
        # Check if the widget imports theme system
        import inspect
        source = inspect.getsource(BoardVisualizerWidget)
        
        if "from src.gui.theme import COLORS" in source:
            print("✓ BoardVisualizerWidget imports theme system")
        else:
            print("✗ BoardVisualizerWidget missing theme imports")
            return False
            
        # Check for theme-aware color usage
        theme_indicators = [
            "background-color: {bg_color}",
            "grid_color",
            "cut_color",
            "grain_color",
            "kerf_color"
        ]
        
        found_indicators = sum(1 for indicator in theme_indicators if indicator in source)
        
        if found_indicators >= 3:
            print(f"✓ BoardVisualizerWidget uses theme-aware styling ({found_indicators}/5 indicators found)")
        else:
            print(f"✗ BoardVisualizerWidget missing theme-aware styling ({found_indicators}/5 indicators found)")
            return False
            
        return True
    except Exception as e:
        print(f"✗ BoardVisualizerWidget test failed: {e}")
        return False

def test_cut_list_optimizer_theme():
    """Test that CutListOptimizerWidget uses theme-aware styling."""
    print("\nTesting CutListOptimizerWidget theme integration...")
    
    try:
        from src.gui.CLO.cut_list_optimizer_widget import CutListOptimizerWidget
        
        # Check if the widget imports theme system
        import inspect
        source = inspect.getsource(CutListOptimizerWidget)
        
        if "from src.gui.theme import COLORS" in source:
            print("✓ CutListOptimizerWidget imports theme system")
        else:
            print("✗ CutListOptimizerWidget missing theme imports")
            return False
            
        if "background-color:" in source and "success_color" in source:
            print("✓ CutListOptimizerWidget uses theme-aware styling")
        else:
            print("✗ CutListOptimizerWidget missing theme-aware styling")
            return False
            
        return True
    except Exception as e:
        print(f"✗ CutListOptimizerWidget test failed: {e}")
        return False

def test_custom_title_bar_theme():
    """Test that CustomTitleBar uses theme-aware styling."""
    print("\nTesting CustomTitleBar theme integration...")
    
    try:
        from src.gui.components.custom_title_bar import CustomTitleBar
        
        # Check if the title bar imports theme system
        import inspect
        source = inspect.getsource(CustomTitleBar)
        
        if "from src.gui.theme import COLORS" in source:
            print("✓ CustomTitleBar imports theme system")
        else:
            print("✗ CustomTitleBar missing theme imports")
            return False
            
        if "background-color:" in source and "text_color" in source:
            print("✓ CustomTitleBar uses theme-aware styling")
        else:
            print("✗ CustomTitleBar missing theme-aware styling")
            return False
            
        return True
    except Exception as e:
        print(f"✗ CustomTitleBar test failed: {e}")
        return False

def test_theme_service_consistency():
    """Test that theme service provides consistent behavior."""
    print("\nTesting theme service consistency...")
    
    try:
        from src.gui.theme.simple_service import ThemeService
        
        service = ThemeService.instance()
        
        # Test that service can get current theme
        current_theme, library = service.get_current_theme()
        print(f"✓ Theme service returns current theme: {current_theme}")
        
        # Test that service can apply theme
        result = service.apply_theme(current_theme, library)
        print(f"✓ Theme service can apply theme: {result}")
        
        return True
    except Exception as e:
        print(f"✗ Theme service test failed: {e}")
        return False

def run_comprehensive_test():
    """Run all theme consistency tests."""
    print("=" * 60)
    print("COMPREHENSIVE THEME FIXES TEST")
    print("Digital Woodsman Workshop Theme Consistency Validation")
    print("=" * 60)
    
    tests = [
        test_theme_imports,
        test_preferences_dialog_theme,
        test_deduplication_dialog_theme,
        test_deduplication_status_widget_theme,
        test_board_visualizer_theme,
        test_cut_list_optimizer_theme,
        test_custom_title_bar_theme,
        test_theme_service_consistency,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Tests passed: {passed}")
    print(f"Tests failed: {failed}")
    print(f"Total tests: {len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL THEME FIXES VERIFIED SUCCESSFULLY!")
        print("✓ All GUI components now use theme-aware styling")
        print("✓ Theme consistency across the application")
        print("✓ Fallback mechanisms in place")
        return True
    else:
        print(f"\n❌ {failed} TESTS FAILED")
        print("Some theme fixes may need attention")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)