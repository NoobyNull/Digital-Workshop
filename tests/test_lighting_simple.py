#!/usr/bin/env python3
"""
Simple test script to verify lighting slider functionality and integration.
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

def test_lighting_slider_functionality():
    """Test lighting slider responsiveness and integration."""
    print("=== Testing Lighting Slider Functionality ===")
    
    try:
        from PySide6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        from parsers.stl_parser import STLParser
        
        # Create application
        app = QApplication([])
        
        # Create main window
        main_window = MainWindow()
        
        # Check if lighting panel exists
        if not hasattr(main_window, 'lighting_panel') or not main_window.lighting_panel:
            print("FAIL: Lighting panel not found")
            return False
            
        lighting_panel = main_window.lighting_panel
        lighting_panel.setVisible(True)
        print("PASS: Lighting panel found and made visible")
        
        # Check if lighting manager exists
        if not hasattr(main_window, 'lighting_manager') or not main_window.lighting_manager:
            print("FAIL: Lighting manager not found")
            return False
            
        lighting_manager = main_window.lighting_manager
        print("PASS: Lighting manager found")
        
        # Load a test model
        stl_path = Path('Sample STL/cube.stl')
        if not stl_path.exists():
            print("FAIL: Test STL file not found")
            return False
            
        parser = STLParser()
        model = parser.parse_file(str(stl_path))
        main_window.viewer_widget.load_model(model)
        print("PASS: Test model loaded")
        
        # Test intensity slider
        print("\n--- Testing Intensity Slider ---")
        original_intensity = lighting_panel._intensity
        print(f"Original intensity: {original_intensity}")
        
        # Test slider values
        test_values = [0.5, 1.0, 1.5, 2.0]
        for test_val in test_values:
            slider_val = int(test_val * 100)
            lighting_panel.intensity_slider.setValue(slider_val)
            time.sleep(0.1)  # Allow UI to update
            
            current_intensity = lighting_panel._intensity
            manager_props = lighting_manager.get_properties()
            manager_intensity = manager_props['intensity']
            
            print(f"  Slider: {test_val:.1f} -> Panel: {current_intensity:.1f} -> Manager: {manager_intensity:.1f}")
            
            if abs(current_intensity - test_val) > 0.01:
                print(f"FAIL: Intensity slider mismatch: expected {test_val:.1f}, got {current_intensity:.1f}")
                return False
                
        print("PASS: Intensity slider working correctly")
        
        # Test position spinboxes
        print("\n--- Testing Position Spinboxes ---")
        original_pos = (lighting_panel._pos_x, lighting_panel._pos_y, lighting_panel._pos_z)
        print(f"Original position: {original_pos}")
        
        test_positions = [(50, 50, 50), (100, 100, 100), (200, 150, 75)]
        for test_pos in test_positions:
            lighting_panel.x_spin.setValue(test_pos[0])
            lighting_panel.y_spin.setValue(test_pos[1])
            lighting_panel.z_spin.setValue(test_pos[2])
            time.sleep(0.1)  # Allow UI to update
            
            current_pos = (lighting_panel._pos_x, lighting_panel._pos_y, lighting_panel._pos_z)
            manager_props = lighting_manager.get_properties()
            manager_pos = tuple(manager_props['position'])
            
            print(f"  Spinbox: {test_pos} -> Panel: {current_pos} -> Manager: {manager_pos}")
            
            for i in range(3):
                if abs(current_pos[i] - test_pos[i]) > 0.1:
                    print(f"FAIL: Position spinbox mismatch: expected {test_pos[i]}, got {current_pos[i]}")
                    return False
                    
        print("PASS: Position spinboxes working correctly")
        
        # Test color picker
        print("\n--- Testing Color Picker ---")
        original_color = lighting_panel._color
        print(f"Original color: {original_color}")
        
        # Test color changes
        test_colors = [(1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)]
        for test_color in test_colors:
            lighting_panel.set_values(color=test_color, emit_signals=True)
            time.sleep(0.1)  # Allow UI to update
            
            current_color = lighting_panel._color
            manager_props = lighting_manager.get_properties()
            manager_color = tuple(manager_props['color'])
            
            print(f"  Test: {test_color} -> Panel: {current_color} -> Manager: {manager_color}")
            
            for i in range(3):
                if abs(current_color[i] - test_color[i]) > 0.01:
                    print(f"FAIL: Color picker mismatch: expected {test_color[i]}, got {current_color[i]}")
                    return False
                    
        print("PASS: Color picker working correctly")
        
        # Test reset functionality
        print("\n--- Testing Reset Functionality ---")
        lighting_panel._reset_defaults()
        time.sleep(0.1)
        
        reset_props = lighting_manager.get_properties()
        expected_pos = (100.0, 100.0, 100.0)
        expected_color = (1.0, 1.0, 1.0)
        expected_intensity = 0.8
        
        if (tuple(reset_props['position']) == expected_pos and 
            tuple(reset_props['color']) == expected_color and 
            abs(reset_props['intensity'] - expected_intensity) < 0.01):
            print("PASS: Reset functionality working correctly")
        else:
            print(f"FAIL: Reset failed: got {reset_props}")
            return False
            
        print("\n=== All Lighting Slider Tests Passed! ===")
        return True
        
    except Exception as e:
        print(f"FAIL: Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_lighting_performance():
    """Test lighting update performance."""
    print("\n=== Testing Lighting Performance ===")
    
    try:
        from PySide6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        
        app = QApplication([])
        main_window = MainWindow()
        
        if not hasattr(main_window, 'lighting_manager') or not main_window.lighting_manager:
            print("FAIL: Lighting manager not found")
            return False
            
        lighting_manager = main_window.lighting_manager
        
        # Test performance of lighting updates
        print("Testing lighting update performance...")
        
        # Test position updates
        times = []
        for i in range(10):
            start = time.perf_counter()
            lighting_manager.update_position(i*10, i*10, i*10)
            end = time.perf_counter()
            times.append((end - start) * 1000)  # Convert to ms
            
        avg_time = sum(times) / len(times)
        max_time = max(times)
        print(f"Position updates: avg={avg_time:.2f}ms, max={max_time:.2f}ms")
        
        # Test color updates
        times = []
        for i in range(10):
            start = time.perf_counter()
            lighting_manager.update_color(i/10, i/10, i/10)
            end = time.perf_counter()
            times.append((end - start) * 1000)
            
        avg_time = sum(times) / len(times)
        max_time = max(times)
        print(f"Color updates: avg={avg_time:.2f}ms, max={max_time:.2f}ms")
        
        # Test intensity updates
        times = []
        for i in range(10):
            start = time.perf_counter()
            lighting_manager.update_intensity(i/5)
            end = time.perf_counter()
            times.append((end - start) * 1000)
            
        avg_time = sum(times) / len(times)
        max_time = max(times)
        print(f"Intensity updates: avg={avg_time:.2f}ms, max={max_time:.2f}ms")
        
        # Check if performance meets requirements (<16ms for 60fps)
        if max_time < 16.0:
            print("PASS: Lighting performance meets requirements (<16ms)")
            return True
        else:
            print(f"FAIL: Lighting performance too slow: {max_time:.2f}ms > 16ms")
            return False
            
    except Exception as e:
        print(f"FAIL: Performance test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Lighting System...")
    
    # Test functionality
    func_test = test_lighting_slider_functionality()
    
    # Test performance
    perf_test = test_lighting_performance()
    
    if func_test and perf_test:
        print("\n*** ALL LIGHTING TESTS PASSED! ***")
        sys.exit(0)
    else:
        print("\n*** SOME TESTS FAILED! ***")
        sys.exit(1)