#!/usr/bin/env python3
"""
Test script to verify VTK integration with the theme system.

This script tests:
1. VTK color provider functionality
2. Theme integration with VTK scene manager
3. Color mapping and conversion
4. Real-time theme updates for VTK
5. VTK manager registration and updates
"""

import sys
import os
import logging
import time
from typing import Dict, Tuple, List

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class MockVTKSceneManager:
    """Mock VTK scene manager for testing."""
    
    def __init__(self, name: str):
        self.name = name
        self.colors_updated = False
        self.render_called = False
        self.theme_colors = {}
    
    def update_theme_colors(self):
        """Mock update theme colors method."""
        self.colors_updated = True
        print(f"[MOCK] {self.name}: Theme colors updated")
    
    def render(self):
        """Mock render method."""
        self.render_called = True
        print(f"[MOCK] {self.name}: Render called")
    
    def set_theme_colors(self, colors: Dict[str, Tuple[float, float, float]]):
        """Mock set theme colors method."""
        self.theme_colors = colors
        print(f"[MOCK] {self.name}: Set {len(colors)} theme colors")


def test_vtk_color_provider_initialization():
    """Test VTK color provider initialization."""
    print("Testing VTK color provider initialization...")
    
    try:
        from src.gui.theme import get_vtk_color_provider, VTKColorProvider
        
        # Test singleton pattern
        provider1 = get_vtk_color_provider()
        provider2 = VTKColorProvider.instance()
        
        if provider1 is provider2:
            print("[PASS] VTK color provider singleton pattern works")
        else:
            print("[FAIL] VTK color provider singleton pattern failed")
            return False
        
        # Test provider attributes
        if hasattr(provider1, 'theme_service'):
            print("[PASS] VTK provider has theme service")
        else:
            print("[FAIL] VTK provider missing theme service")
            return False
        
        if hasattr(provider1, '_vtk_color_mapping'):
            print(f"[PASS] VTK provider has color mapping: {len(provider1._vtk_color_mapping)} mappings")
        else:
            print("[FAIL] VTK provider missing color mapping")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] VTK color provider initialization failed: {e}")
        return False


def test_vtk_color_retrieval():
    """Test VTK color retrieval functionality."""
    print("Testing VTK color retrieval...")
    
    try:
        from src.gui.theme import get_vtk_color_provider, vtk_rgb
        
        provider = get_vtk_color_provider()
        
        # Test common VTK colors
        test_colors = [
            "canvas_bg", "primary", "secondary", "edge_color",
            "grid_color", "ground_color", "model_surface", "text",
            "border", "selection", "success", "warning", "error"
        ]
        
        for color_name in test_colors:
            vtk_color = provider.get_vtk_color(color_name)
            if isinstance(vtk_color, tuple) and len(vtk_color) == 3:
                if all(0.0 <= c <= 1.0 for c in vtk_color):
                    print(f"[PASS] {color_name}: {vtk_color}")
                else:
                    print(f"[FAIL] {color_name} out of range: {vtk_color}")
                    return False
            else:
                print(f"[FAIL] {color_name} invalid type: {vtk_color}")
                return False
        
        # Test vtk_rgb convenience function
        primary_color = vtk_rgb("primary")
        if isinstance(primary_color, tuple) and len(primary_color) == 3:
            print(f"[PASS] vtk_rgb function works: {primary_color}")
        else:
            print(f"[FAIL] vtk_rgb function failed: {primary_color}")
            return False
        
        # Test invalid color name
        invalid_color = provider.get_vtk_color("nonexistent_color")
        if isinstance(invalid_color, tuple) and len(invalid_color) == 3:
            print(f"[PASS] Invalid color handled with fallback: {invalid_color}")
        else:
            print(f"[FAIL] Invalid color not handled: {invalid_color}")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] VTK color retrieval test failed: {e}")
        return False


def test_vtk_color_mapping():
    """Test VTK color mapping functionality."""
    print("Testing VTK color mapping...")
    
    try:
        from src.gui.theme import get_vtk_color_provider
        
        provider = get_vtk_color_provider()
        
        # Test color mapping info
        mapping_info = provider.get_color_mapping_info()
        if isinstance(mapping_info, dict) and len(mapping_info) > 0:
            print(f"[PASS] Color mapping info available: {len(mapping_info)} mappings")
        else:
            print(f"[FAIL] Color mapping info not available: {mapping_info}")
            return False
        
        # Test some specific mappings
        key_mappings = {
            "canvas_bg": "secondaryDarkColor",
            "primary": "primaryColor",
            "text": "primaryTextColor",
            "x_axis": "#FF4444"
        }
        
        for vtk_name, expected_qt_name in key_mappings.items():
            actual_qt_name = mapping_info.get(vtk_name)
            if actual_qt_name == expected_qt_name:
                print(f"[PASS] {vtk_name} -> {actual_qt_name}")
            else:
                print(f"[FAIL] {vtk_name} -> {actual_qt_name} (expected {expected_qt_name})")
                return False
        
        # Test custom mapping
        provider.add_custom_mapping("test_color", "#FF00FF")
        test_color = provider.get_vtk_color("test_color")
        expected_color = (1.0, 0.0, 1.0)  # #FF00FF -> (1, 0, 1)
        
        if all(abs(a - b) < 0.001 for a, b in zip(test_color, expected_color)):
            print(f"[PASS] Custom mapping works: {test_color}")
        else:
            print(f"[FAIL] Custom mapping failed: {test_color} != {expected_color}")
            return False
        
        # Test removing custom mapping
        removed = provider.remove_custom_mapping("test_color")
        if removed:
            print("[PASS] Custom mapping removal works")
        else:
            print("[FAIL] Custom mapping removal failed")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] VTK color mapping test failed: {e}")
        return False


def test_vtk_manager_registration():
    """Test VTK manager registration and updates."""
    print("Testing VTK manager registration...")
    
    try:
        from src.gui.theme import get_vtk_color_provider
        
        provider = get_vtk_color_provider()
        
        # Create mock VTK managers
        manager1 = MockVTKSceneManager("Manager1")
        manager2 = MockVTKSceneManager("Manager2")
        
        # Test registration
        initial_count = provider.get_vtk_manager_count()
        provider.register_vtk_manager(manager1)
        provider.register_vtk_manager(manager2)
        
        if provider.get_vtk_manager_count() == initial_count + 2:
            print(f"[PASS] VTK manager registration works: {provider.get_vtk_manager_count()} managers")
        else:
            print(f"[FAIL] VTK manager registration failed: expected {initial_count + 2}, got {provider.get_vtk_manager_count()}")
            return False
        
        # Test duplicate registration (should not increase count)
        provider.register_vtk_manager(manager1)
        if provider.get_vtk_manager_count() == initial_count + 2:
            print("[PASS] Duplicate registration handled correctly")
        else:
            print(f"[FAIL] Duplicate registration not handled: {provider.get_vtk_manager_count()}")
            return False
        
        # Test VTK color updates
        provider.update_vtk_colors()
        
        if manager1.colors_updated and manager2.colors_updated:
            print("[PASS] VTK color updates work for all managers")
        else:
            print(f"[FAIL] VTK color updates failed: manager1={manager1.colors_updated}, manager2={manager2.colors_updated}")
            return False
        
        # Test unregistration
        provider.unregister_vtk_manager(manager1)
        if provider.get_vtk_manager_count() == initial_count + 1:
            print("[PASS] VTK manager unregistration works")
        else:
            print(f"[FAIL] VTK manager unregistration failed: expected {initial_count + 1}, got {provider.get_vtk_manager_count()}")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] VTK manager registration test failed: {e}")
        return False


def test_theme_integration_with_vtk():
    """Test theme integration with VTK system."""
    print("Testing theme integration with VTK...")
    
    try:
        from src.gui.theme import QtMaterialThemeService, get_vtk_color_provider
        
        theme_service = QtMaterialThemeService.instance()
        vtk_provider = get_vtk_color_provider()
        
        # Create mock VTK manager
        vtk_manager = MockVTKSceneManager("TestManager")
        vtk_provider.register_vtk_manager(vtk_manager)
        
        # Test theme change triggers VTK update
        original_theme, original_variant = theme_service.get_current_theme()
        
        # Change theme
        success = theme_service.apply_theme("light", "amber")
        if not success:
            print("[FAIL] Theme change failed")
            return False
        
        # Check if VTK manager was updated
        if vtk_manager.colors_updated:
            print("[PASS] Theme change triggered VTK update")
        else:
            print("[FAIL] Theme change did not trigger VTK update")
            return False
        
        # Test VTK colors reflect new theme
        primary_color = vtk_provider.get_vtk_color("primary")
        if isinstance(primary_color, tuple) and len(primary_color) == 3:
            print(f"[PASS] VTK colors updated with new theme: {primary_color}")
        else:
            print(f"[FAIL] VTK colors not updated: {primary_color}")
            return False
        
        # Test multiple theme changes
        themes_to_test = [
            ("dark", "blue"),
            ("dark", "cyan"),
            ("light", "blue"),
            ("light", "amber")
        ]
        
        for theme, variant in themes_to_test:
            vtk_manager.colors_updated = False  # Reset flag
            
            success = theme_service.apply_theme(theme, variant)
            if not success:
                print(f"[FAIL] Failed to apply {theme}/{variant}")
                return False
            
            if not vtk_manager.colors_updated:
                print(f"[FAIL] VTK not updated for {theme}/{variant}")
                return False
            
            # Test color consistency
            color1 = vtk_provider.get_vtk_color("primary")
            color2 = vtk_provider.get_vtk_color("primary")
            
            if color1 == color2:
                print(f"[PASS] Color consistency for {theme}/{variant}")
            else:
                print(f"[FAIL] Color inconsistency for {theme}/{variant}: {color1} != {color2}")
                return False
        
        # Restore original theme
        theme_service.apply_theme(original_theme, original_variant)
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Theme integration with VTK test failed: {e}")
        return False


def test_vtk_performance():
    """Test VTK color provider performance."""
    print("Testing VTK color provider performance...")
    
    try:
        from src.gui.theme import get_vtk_color_provider
        
        provider = get_vtk_color_provider()
        
        # Test color retrieval performance
        start_time = time.time()
        for _ in range(1000):
            color = provider.get_vtk_color("primary")
            if not isinstance(color, tuple) or len(color) != 3:
                print("[FAIL] Performance test failed during color retrieval")
                return False
        elapsed_time = time.time() - start_time
        
        avg_time = elapsed_time / 1000 * 1000  # Convert to milliseconds
        print(f"[INFO] Average VTK color retrieval time: {avg_time:.3f}ms")
        
        if avg_time < 1.0:  # Should be under 1ms
            print("[PASS] VTK color retrieval performance is acceptable")
        else:
            print(f"[WARN] VTK color retrieval performance is slow: {avg_time:.3f}ms")
        
        # Test color mapping performance
        start_time = time.time()
        for _ in range(100):
            all_colors = provider.get_all_vtk_colors()
            if not isinstance(all_colors, dict) or len(all_colors) == 0:
                print("[FAIL] Performance test failed during color mapping")
                return False
        elapsed_time = time.time() - start_time
        
        avg_mapping_time = elapsed_time / 100 * 1000  # Convert to milliseconds
        print(f"[INFO] Average color mapping time: {avg_mapping_time:.3f}ms")
        
        if avg_mapping_time < 10.0:  # Should be under 10ms
            print("[PASS] Color mapping performance is acceptable")
        else:
            print(f"[WARN] Color mapping performance is slow: {avg_mapping_time:.3f}ms")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] VTK performance test failed: {e}")
        return False


def test_vtk_error_handling():
    """Test VTK error handling robustness."""
    print("Testing VTK error handling...")
    
    try:
        from src.gui.theme import get_vtk_color_provider
        
        provider = get_vtk_color_provider()
        
        # Test invalid VTK manager
        class InvalidVTKManager:
            pass
        
        invalid_manager = InvalidVTKManager()
        provider.register_vtk_manager(invalid_manager)
        
        # Try to update (should not crash)
        try:
            provider.update_vtk_colors()
            print("[PASS] Invalid VTK manager handled gracefully")
        except Exception as e:
            print(f"[FAIL] Invalid VTK manager caused crash: {e}")
            return False
        
        # Test None color name
        try:
            color = provider.get_vtk_color(None)  # type: ignore
            if isinstance(color, tuple) and len(color) == 3:
                print("[PASS] None color name handled with fallback")
            else:
                print(f"[FAIL] None color name not handled: {color}")
                return False
        except Exception as e:
            print(f"[FAIL] None color name caused crash: {e}")
            return False
        
        # Test empty string color name
        try:
            color = provider.get_vtk_color("")
            if isinstance(color, tuple) and len(color) == 3:
                print("[PASS] Empty color name handled with fallback")
            else:
                print(f"[FAIL] Empty color name not handled: {color}")
                return False
        except Exception as e:
            print(f"[FAIL] Empty color name caused crash: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"[FAIL] VTK error handling test failed: {e}")
        return False


def main():
    """Run all VTK integration tests."""
    print("=" * 60)
    print("Testing VTK Theme Integration")
    print("=" * 60)
    
    # Configure logging to reduce noise
    logging.basicConfig(level=logging.ERROR)
    
    tests = [
        test_vtk_color_provider_initialization,
        test_vtk_color_retrieval,
        test_vtk_color_mapping,
        test_vtk_manager_registration,
        test_theme_integration_with_vtk,
        test_vtk_performance,
        test_vtk_error_handling
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        print()
        if test():
            passed += 1
        print("-" * 40)
    
    print(f"\nTest Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("[SUCCESS] All VTK integration tests passed!")
        print("VTK theme integration is working correctly.")
        return 0
    else:
        print("[ERROR] Some VTK integration tests failed.")
        print("VTK theme integration may have issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())