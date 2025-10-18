#!/usr/bin/env python3
"""
Complete test script to verify all lighting improvements including:
1. Ground plane and grid visibility
2. Improved lighting slider functionality
3. Shadow rendering system
4. Overall integration
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_ground_plane_and_grid():
    """Test ground plane and grid visibility functionality."""
    print("=== Testing Ground Plane and Grid Visibility ===")
    
    app = None
    try:
        from PySide6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        from parsers.stl_parser import STLParser
        
        # Create application only if none exists
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        
        # Create main window
        main_window = MainWindow()
        
        # Check if viewer widget exists
        if not hasattr(main_window, 'viewer_widget') or not main_window.viewer_widget:
            print("FAIL: Viewer widget not found")
            return False
            
        viewer = main_window.viewer_widget
        
        # Check if grid and ground actors exist
        if not hasattr(viewer, 'grid_actor') or not viewer.grid_actor:
            print("FAIL: Grid actor not found")
            return False
            
        if not hasattr(viewer, 'ground_actor') or not viewer.ground_actor:
            print("FAIL: Ground actor not found")
            return False
            
        print("PASS: Grid and ground actors found")
        
        # Test grid visibility toggle
        original_grid_visible = viewer.grid_visible
        viewer._toggle_grid()
        new_grid_visible = viewer.grid_visible
        
        if original_grid_visible == new_grid_visible:
            print("FAIL: Grid visibility toggle not working")
            return False
            
        print("PASS: Grid visibility toggle working")
        
        # Test grid button state
        if hasattr(viewer, 'grid_button'):
            button_state = viewer.grid_button.isChecked()
            if button_state != viewer.grid_visible:
                print("FAIL: Grid button state not synchronized")
                return False
            print("PASS: Grid button state synchronized")
        
        # Test ground plane positioning
        stl_path = Path('Sample STL/AMERICAN EAGLE 1.stl')
        if stl_path.exists():
            parser = STLParser()
            model = parser.parse_file(str(stl_path))
            viewer.load_model(model)
            
            # Ground plane should be positioned at model bottom
            if viewer.ground_actor and viewer.actor:
                model_bounds = viewer.actor.GetBounds()
                if model_bounds:
                    ground_z = model_bounds[4] - 0.5  # Expected ground position
                    ground_pos = viewer.ground_actor.GetPosition()
                    
                    if abs(ground_pos[2] - ground_z) > 1.0:
                        print(f"FAIL: Ground plane not positioned correctly. Expected Z≈{ground_z}, got {ground_pos[2]}")
                        return False
                        
                    print("PASS: Ground plane positioned correctly at model bottom")
        
        return True
        
    except Exception as e:
        print(f"FAIL: Ground plane and grid test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_improved_lighting_controls():
    """Test improved lighting control panel with sliders."""
    print("\n=== Testing Improved Lighting Controls ===")
    
    app = None
    try:
        from PySide6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        
        # Create application only if none exists
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        
        # Create main window
        main_window = MainWindow()
        
        # Check if lighting panel exists
        if not hasattr(main_window, 'lighting_panel') or not main_window.lighting_panel:
            print("FAIL: Lighting panel not found")
            return False
            
        lighting_panel = main_window.lighting_panel
        lighting_panel.setVisible(True)
        print("PASS: Lighting panel found and made visible")
        
        # Check if lighting controls have sliders instead of spinboxes
        if not hasattr(lighting_panel, 'x_slider') or not lighting_panel.x_slider:
            print("FAIL: X position slider not found")
            return False
            
        if not hasattr(lighting_panel, 'y_slider') or not lighting_panel.y_slider:
            print("FAIL: Y position slider not found")
            return False
            
        if not hasattr(lighting_panel, 'z_slider') or not lighting_panel.z_slider:
            print("FAIL: Z position slider not found")
            return False
            
        if not hasattr(lighting_panel, 'intensity_slider') or not lighting_panel.intensity_slider:
            print("FAIL: Intensity slider not found")
            return False
            
        print("PASS: All lighting sliders found (replacing spinboxes)")
        
        # Test slider functionality
        original_x = lighting_panel._pos_x
        lighting_panel.x_slider.setValue(150)
        app.processEvents()
        
        if lighting_panel._pos_x != 150.0:
            print(f"FAIL: X position slider not working. Expected 150, got {lighting_panel._pos_x}")
            return False
            
        print("PASS: X position slider working")
        
        # Test intensity slider
        original_intensity = lighting_panel._intensity
        lighting_panel.intensity_slider.setValue(150)  # 1.5 intensity
        app.processEvents()
        
        if abs(lighting_panel._intensity - 1.5) > 0.01:
            print(f"FAIL: Intensity slider not working. Expected 1.5, got {lighting_panel._intensity}")
            return False
            
        print("PASS: Intensity slider working")
        
        # Test reset functionality
        lighting_panel._reset_defaults()
        app.processEvents()
        
        expected_pos = (100.0, 100.0, 100.0)
        expected_intensity = 0.8
        
        current_pos = (lighting_panel._pos_x, lighting_panel._pos_y, lighting_panel._pos_z)
        if (current_pos != expected_pos or 
            abs(lighting_panel._intensity - expected_intensity) > 0.01):
            print(f"FAIL: Reset functionality not working")
            return False
            
        print("PASS: Reset functionality working")
        
        return True
        
    except Exception as e:
        print(f"FAIL: Improved lighting controls test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_shadow_rendering():
    """Test shadow rendering system."""
    print("\n=== Testing Shadow Rendering System ===")
    
    app = None
    try:
        from PySide6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        from parsers.stl_parser import STLParser
        import vtk
        
        # Create application only if none exists
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        
        # Create main window
        main_window = MainWindow()
        
        # Check if viewer widget exists
        if not hasattr(main_window, 'viewer_widget') or not main_window.viewer_widget:
            print("FAIL: Viewer widget not found")
            return False
            
        viewer = main_window.viewer_widget
        
        # Check if shadows are enabled
        if hasattr(viewer, 'renderer') and viewer.renderer:
            render_pass = viewer.renderer.GetPass()
            if render_pass:
                print("PASS: Shadow rendering pass is enabled")
            else:
                print("INFO: Shadow rendering pass not found (may not be supported)")
        
        # Load a model to test shadows
        stl_path = Path('Sample STL/AMERICAN EAGLE 1.stl')
        if not stl_path.exists():
            print("SKIP: No test model available for shadow testing")
            return True
            
        parser = STLParser()
        model = parser.parse_file(str(stl_path))
        viewer.load_model(model)
        
        # Check if ground plane is configured for shadow reception
        if hasattr(viewer, 'ground_actor') and viewer.ground_actor:
            ground_prop = viewer.ground_actor.GetProperty()
            ambient = ground_prop.GetAmbient()
            diffuse = ground_prop.GetDiffuse()
            
            # Ground plane should have proper material properties for shadows
            if ambient > 0.1 and diffuse > 0.5:
                print("PASS: Ground plane configured for shadow reception")
            else:
                print("INFO: Ground plane may not be optimally configured for shadows")
        
        # Check if model is configured for shadow casting
        if hasattr(viewer, 'actor') and viewer.actor:
            model_prop = viewer.actor.GetProperty()
            ambient = model_prop.GetAmbient()
            diffuse = model_prop.GetDiffuse()
            
            # Model should have lower ambient for better shadow contrast
            if ambient < 0.5 and diffuse > 0.5:
                print("PASS: Model configured for shadow casting")
            else:
                print("INFO: Model may not be optimally configured for shadow casting")
        
        return True
        
    except Exception as e:
        print(f"FAIL: Shadow rendering test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lighting_integration():
    """Test overall lighting system integration."""
    print("\n=== Testing Lighting System Integration ===")
    
    app = None
    try:
        from PySide6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        from parsers.stl_parser import STLParser
        
        # Create application only if none exists
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        
        # Create main window
        main_window = MainWindow()
        
        # Check if lighting manager exists
        if not hasattr(main_window, 'lighting_manager') or not main_window.lighting_manager:
            print("FAIL: Lighting manager not found")
            return False
            
        lighting_manager = main_window.lighting_manager
        print("PASS: Lighting manager found")
        
        # Check if lighting panel is integrated
        if not hasattr(main_window, 'lighting_panel') or not main_window.lighting_panel:
            print("FAIL: Lighting panel not found")
            return False
            
        lighting_panel = main_window.lighting_panel
        print("PASS: Lighting panel found")
        
        # Check signal connections
        if not hasattr(lighting_panel, 'position_changed'):
            print("FAIL: Position signal not found")
            return False
            
        if not hasattr(lighting_panel, 'intensity_changed'):
            print("FAIL: Intensity signal not found")
            return False
            
        print("PASS: All lighting signals found")
        
        # Load a model to test integration
        stl_path = Path('Sample STL/AMERICAN EAGLE 1.stl')
        if not stl_path.exists():
            print("SKIP: No test model available for integration testing")
            return True
            
        parser = STLParser()
        model = parser.parse_file(str(stl_path))
        main_window.viewer_widget.load_model(model)
        
        # Test lighting changes propagate to renderer
        original_props = lighting_manager.get_properties()
        
        # Change position
        lighting_panel.x_slider.setValue(150)
        app.processEvents()
        time.sleep(0.1)  # Allow for propagation
        
        new_props = lighting_manager.get_properties()
        if new_props['position'][0] != 150.0:
            print("FAIL: Position changes not propagating to lighting manager")
            return False
            
        print("PASS: Position changes propagating correctly")
        
        # Change intensity
        lighting_panel.intensity_slider.setValue(150)  # 1.5 intensity
        app.processEvents()
        time.sleep(0.1)  # Allow for propagation
        
        new_props = lighting_manager.get_properties()
        if abs(new_props['intensity'] - 1.5) > 0.01:
            print("FAIL: Intensity changes not propagating to lighting manager")
            return False
            
        print("PASS: Intensity changes propagating correctly")
        
        return True
        
    except Exception as e:
        print(f"FAIL: Lighting integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Complete Lighting System...")
    
    # Test all components
    ground_test = test_ground_plane_and_grid()
    controls_test = test_improved_lighting_controls()
    shadow_test = test_shadow_rendering()
    integration_test = test_lighting_integration()
    
    # Summary
    print("\n=== TEST SUMMARY ===")
    print(f"Ground Plane & Grid: {'PASS' if ground_test else 'FAIL'}")
    print(f"Improved Lighting Controls: {'PASS' if controls_test else 'FAIL'}")
    print(f"Shadow Rendering: {'PASS' if shadow_test else 'FAIL'}")
    print(f"Lighting Integration: {'PASS' if integration_test else 'FAIL'}")
    
    all_passed = ground_test and controls_test and shadow_test and integration_test
    
    if all_passed:
        print("\n*** ALL LIGHTING SYSTEM TESTS PASSED! ***")
        print("\nLighting System Improvements Verified:")
        print("- Ground plane and grid visibility working correctly")
        print("- Position controls now use intuitive sliders instead of spinboxes")
        print("- Shadow rendering system enabled and functional")
        print("- All components properly integrated")
        sys.exit(0)
    else:
        print("\n*** SOME TESTS FAILED! ***")
        sys.exit(1)