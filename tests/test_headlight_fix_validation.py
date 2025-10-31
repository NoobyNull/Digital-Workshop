#!/usr/bin/env python3
"""
Comprehensive test suite for headlight fix validation.

This test validates that the headlight system works correctly after the implementation
of the architectural fixes for the critical headlight issues.
"""

import sys
import time
import logging
from typing import Optional
import multiprocessing as _mp

# Add src to path for imports
sys.path.insert(0, 'src')

try:
    import vtk
    from PyQt6.QtWidgets import QApplication, QVBoxLayout, QWidget, QPushButton
    from PyQt6.QtCore import QTimer
    from src.gui.viewer_3d.vtk_scene_manager import VTKSceneManager
    from src.gui.theme import get_vtk_color_provider
    from src.core.logging_config import get_logger
    from src.parsers.stl_parser import STLModel
except ImportError as e:
    print(f"Import error: {e}")
    print("This test requires VTK, PyQt6, and the application modules to be available.")
    sys.exit(1)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = get_logger(__name__)


class HeadlightTestWidget(QWidget):
    """Test widget for headlight validation."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Headlight Fix Validation Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create layout
        layout = QVBoxLayout()
        
        # Create VTK widget
        self.vtk_widget = vtk.vtkGenericOpenGLRenderWindow()
        self.scene_manager = VTKSceneManager(self.vtk_widget)
        
        # Add VTK widget to layout
        from src.gui.viewer_widget_vtk import QVTKRenderWindowInteractor
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        self.scene_manager = VTKSceneManager(self.vtk_widget)
        
        # Create test buttons
        self.create_test_buttons(layout)
        
        # Set layout
        self.setLayout(layout)
        
        # Setup scene
        self.scene_manager.setup_scene()
        
        # Create test geometry
        self.create_test_geometry()
        
        # Start timer for animation tests
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.animate_camera)
        self.animation_running = False
        
        logger.info("Headlight test widget initialized")
    
    def create_test_buttons(self, layout):
        """Create test control buttons."""
        # Test headlight intensity
        intensity_btn = QPushButton("Test Headlight Intensity")
        intensity_btn.clicked.connect(self.test_headlight_intensity)
        layout.addWidget(intensity_btn)
        
        # Test headlight enable/disable
        enable_btn = QPushButton("Test Headlight Enable/Disable")
        enable_btn.clicked.connect(self.test_headlight_enable_disable)
        layout.addWidget(enable_btn)
        
        # Test headlight color
        color_btn = QPushButton("Test Headlight Color")
        color_btn.clicked.connect(self.test_headlight_color)
        layout.addWidget(color_btn)
        
        # Test camera following
        camera_btn = QPushButton("Test Camera Following")
        camera_btn.clicked.connect(self.test_camera_following)
        layout.addWidget(camera_btn)
        
        # Test animation
        self.anim_btn = QPushButton("Start Animation Test")
        self.anim_btn.clicked.connect(self.toggle_animation)
        layout.addWidget(self.anim_btn)
        
        # Test memory leak
        memory_btn = QPushButton("Test Memory Leak (20 iterations)")
        memory_btn.clicked.connect(self.test_memory_leak)
        layout.addWidget(memory_btn)
        
        # Performance test
        perf_btn = QPushButton("Test Performance")
        perf_btn.clicked.connect(self.test_performance)
        layout.addWidget(perf_btn)
    
    def create_test_geometry(self):
        """Create test geometry for shadow testing."""
        try:
            # Create a simple cube for testing
            cube_source = vtk.vtkCubeSource()
            cube_source.SetXLength(2.0)
            cube_source.SetYLength(2.0)
            cube_source.SetZLength(2.0)
            
            # Create mapper and actor
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(cube_source.GetOutputPort())
            
            self.test_actor = vtk.vtkActor()
            self.test_actor.SetMapper(mapper)
            
            # Add to renderer
            self.scene_manager.renderer.AddActor(self.test_actor)
            
            # Fit camera to the test geometry
            self.scene_manager.renderer.ResetCamera()
            
            logger.info("Test geometry created successfully")
            
        except Exception as e:
            logger.error(f"Failed to create test geometry: {e}")
    
    def test_headlight_intensity(self):
        """Test headlight intensity changes."""
        logger.info("Testing headlight intensity changes")
        
        try:
            # Test various intensity values
            test_values = [0.0, 0.25, 0.5, 0.75, 1.0, 0.6]
            
            for intensity in test_values:
                self.scene_manager.set_headlight_intensity(intensity)
                time.sleep(0.5)  # Allow time to see changes
                
                # Verify headlight exists and intensity is set
                if self.scene_manager.headlight:
                    actual_intensity = self.scene_manager.headlight.GetIntensity()
                    logger.debug(f"Set intensity to {intensity}, actual: {actual_intensity}")
                    
                    if abs(actual_intensity - intensity) > 0.01:
                        logger.error(f"Intensity mismatch: expected {intensity}, got {actual_intensity}")
                        return False
                else:
                    logger.error("Headlight does not exist after intensity change")
                    return False
            
            logger.info("✓ Headlight intensity test passed")
            return True
            
        except Exception as e:
            logger.error(f"Headlight intensity test failed: {e}")
            return False
    
    def test_headlight_enable_disable(self):
        """Test headlight enable/disable functionality."""
        logger.info("Testing headlight enable/disable")
        
        try:
            # Test disable
            self.scene_manager.set_headlight_enabled(False)
            if self.scene_manager.headlight:
                switch_state = self.scene_manager.headlight.GetSwitch()
                if switch_state != 0:
                    logger.error(f"Headlight should be disabled (0), but switch state is {switch_state}")
                    return False
            
            time.sleep(0.5)
            
            # Test enable
            self.scene_manager.set_headlight_enabled(True)
            if self.scene_manager.headlight:
                switch_state = self.scene_manager.headlight.GetSwitch()
                if switch_state != 1:
                    logger.error(f"Headlight should be enabled (1), but switch state is {switch_state}")
                    return False
            
            time.sleep(0.5)
            
            logger.info("✓ Headlight enable/disable test passed")
            return True
            
        except Exception as e:
            logger.error(f"Headlight enable/disable test failed: {e}")
            return False
    
    def test_headlight_color(self):
        """Test headlight color changes."""
        logger.info("Testing headlight color changes")
        
        try:
            # Test various colors
            test_colors = [
                (1.0, 0.0, 0.0),  # Red
                (0.0, 1.0, 0.0),  # Green
                (0.0, 0.0, 1.0),  # Blue
                (1.0, 1.0, 1.0),  # White
                (0.8, 0.8, 0.8),  # Light gray (default)
            ]
            
            for r, g, b in test_colors:
                self.scene_manager.set_headlight_color(r, g, b)
                time.sleep(0.5)  # Allow time to see changes
                
                # Verify color is set
                if self.scene_manager.headlight:
                    actual_color = self.scene_manager.headlight.GetColor()
                    logger.debug(f"Set color to ({r},{g},{b}), actual: {actual_color}")
                    
                    # Allow small floating point differences
                    if (abs(actual_color[0] - r) > 0.01 or 
                        abs(actual_color[1] - g) > 0.01 or 
                        abs(actual_color[2] - b) > 0.01):
                        logger.error(f"Color mismatch: expected ({r},{g},{b}), got {actual_color}")
                        return False
                else:
                    logger.error("Headlight does not exist after color change")
                    return False
            
            logger.info("✓ Headlight color test passed")
            return True
            
        except Exception as e:
            logger.error(f"Headlight color test failed: {e}")
            return False
    
    def test_camera_following(self):
        """Test that headlight follows camera movements."""
        logger.info("Testing headlight camera following")
        
        try:
            camera = self.scene_manager.renderer.GetActiveCamera()
            if not camera:
                logger.error("No camera found")
                return False
            
            # Store initial positions
            initial_camera_pos = camera.GetPosition()
            initial_focal_point = camera.GetFocalPoint()
            
            if self.scene_manager.headlight:
                initial_headlight_pos = self.scene_manager.headlight.GetPosition()
                initial_headlight_focal = self.scene_manager.headlight.GetFocalPoint()
                
                # Check if headlight starts at camera position
                if (abs(initial_headlight_pos[0] - initial_camera_pos[0]) > 0.1 or
                    abs(initial_headlight_pos[1] - initial_camera_pos[1]) > 0.1 or
                    abs(initial_headlight_pos[2] - initial_camera_pos[2]) > 0.1):
                    logger.error(f"Initial headlight position {initial_headlight_pos} does not match camera position {initial_camera_pos}")
                    return False
            
            # Move camera to different positions
            test_positions = [
                (5.0, 5.0, 5.0),
                (-5.0, 5.0, 5.0),
                (0.0, 0.0, 10.0),
                (-3.0, -3.0, 8.0),
            ]
            
            for pos in test_positions:
                camera.SetPosition(*pos)
                self.scene_manager.update_headlight_position()
                time.sleep(0.2)
                
                if self.scene_manager.headlight:
                    headlight_pos = self.scene_manager.headlight.GetPosition()
                    
                    # Check if headlight followed camera
                    if (abs(headlight_pos[0] - pos[0]) > 0.1 or
                        abs(headlight_pos[1] - pos[1]) > 0.1 or
                        abs(headlight_pos[2] - pos[2]) > 0.1):
                        logger.error(f"Headlight position {headlight_pos} does not match camera position {pos}")
                        return False
            
            # Reset camera
            camera.SetPosition(*initial_camera_pos)
            camera.SetFocalPoint(*initial_focal_point)
            self.scene_manager.update_headlight_position()
            
            logger.info("✓ Headlight camera following test passed")
            return True
            
        except Exception as e:
            logger.error(f"Headlight camera following test failed: {e}")
            return False
    
    def toggle_animation(self):
        """Toggle camera animation test."""
        if self.animation_running:
            self.animation_timer.stop()
            self.anim_btn.setText("Start Animation Test")
            self.animation_running = False
            logger.info("Animation test stopped")
        else:
            self.animation_timer.start(50)  # 20 FPS
            self.anim_btn.setText("Stop Animation Test")
            self.animation_running = True
            self.animation_angle = 0
            logger.info("Animation test started")
    
    def animate_camera(self):
        """Animate camera around the test geometry."""
        try:
            camera = self.scene_manager.renderer.GetActiveCamera()
            if not camera:
                return
            
            # Rotate camera around the origin
            import math
            radius = 8.0
            self.animation_angle += 2.0  # degrees per frame
            
            if self.animation_angle >= 360:
                self.animation_angle = 0
            
            angle_rad = math.radians(self.animation_angle)
            x = radius * math.cos(angle_rad)
            y = radius * math.sin(angle_rad)
            z = 5.0
            
            camera.SetPosition(x, y, z)
            camera.SetFocalPoint(0, 0, 0)
            camera.SetViewUp(0, 0, 1)
            
            # Update headlight position
            self.scene_manager.update_headlight_position()
            
            # Render
            self.scene_manager.render()
            
        except Exception as e:
            logger.error(f"Animation error: {e}")
    
    def test_memory_leak(self):
        """Test for memory leaks during repeated operations."""
        logger.info("Testing for memory leaks (20 iterations)")
        
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            logger.debug(f"Initial memory usage: {initial_memory:.2f} MB")
            
            # Perform 20 iterations of headlight operations
            for i in range(20):
                # Test intensity changes
                self.scene_manager.set_headlight_intensity(0.1)
                self.scene_manager.set_headlight_intensity(0.9)
                
                # Test enable/disable
                self.scene_manager.set_headlight_enabled(False)
                self.scene_manager.set_headlight_enabled(True)
                
                # Test color changes
                self.scene_manager.set_headlight_color(1.0, 0.0, 0.0)
                self.scene_manager.set_headlight_color(0.0, 1.0, 0.0)
                self.scene_manager.set_headlight_color(1.0, 1.0, 1.0)
                
                # Test position updates
                self.scene_manager.update_headlight_position()
                
                if i % 5 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    logger.debug(f"Iteration {i}: Memory usage: {current_memory:.2f} MB")
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            logger.debug(f"Final memory usage: {final_memory:.2f} MB")
            logger.debug(f"Memory increase: {memory_increase:.2f} MB")
            
            # Check for excessive memory increase (> 10 MB)
            if memory_increase > 10:
                logger.error(f"Potential memory leak detected: {memory_increase:.2f} MB increase")
                return False
            
            logger.info(f"✓ Memory leak test passed: {memory_increase:.2f} MB increase")
            return True
            
        except ImportError:
            logger.warning("psutil not available, skipping memory leak test")
            return True
        except Exception as e:
            logger.error(f"Memory leak test failed: {e}")
            return False
    
    def test_performance(self):
        """Test performance during headlight operations."""
        logger.info("Testing headlight performance")
        
        try:
            # Measure time for multiple operations
            iterations = 100
            
            # Test intensity changes
            start_time = time.time()
            for i in range(iterations):
                intensity = (i % 10) / 10.0  # 0.0 to 0.9
                self.scene_manager.set_headlight_intensity(intensity)
            intensity_time = time.time() - start_time
            
            # Test position updates
            start_time = time.time()
            for i in range(iterations):
                self.scene_manager.update_headlight_position()
            position_time = time.time() - start_time
            
            # Test color changes
            start_time = time.time()
            for i in range(iterations):
                r = (i % 3) / 2.0
                g = ((i + 1) % 3) / 2.0
                b = ((i + 2) % 3) / 2.0
                self.scene_manager.set_headlight_color(r, g, b)
            color_time = time.time() - start_time
            
            # Calculate averages
            avg_intensity = intensity_time / iterations * 1000  # ms
            avg_position = position_time / iterations * 1000    # ms
            avg_color = color_time / iterations * 1000         # ms
            
            logger.debug(f"Average intensity time: {avg_intensity:.3f} ms")
            logger.debug(f"Average position time: {avg_position:.3f} ms")
            logger.debug(f"Average color time: {avg_color:.3f} ms")
            
            # Performance thresholds (should be very fast)
            if avg_intensity > 1.0:  # 1ms per operation
                logger.warning(f"Intensity operations slower than expected: {avg_intensity:.3f} ms")
            
            if avg_position > 1.0:  # 1ms per operation
                logger.warning(f"Position operations slower than expected: {avg_position:.3f} ms")
            
            if avg_color > 1.0:  # 1ms per operation
                logger.warning(f"Color operations slower than expected: {avg_color:.3f} ms")
            
            logger.info("✓ Performance test completed")
            return True
            
        except Exception as e:
            logger.error(f"Performance test failed: {e}")
            return False


def run_headlight_validation_tests():
    """Run all headlight validation tests."""
    logger.info("Starting comprehensive headlight validation tests")
    
    app = QApplication(sys.argv)
    
    # Create test widget
    test_widget = HeadlightTestWidget()
    test_widget.show()
    
    # Run tests automatically
    test_results = {}
    
    # Test 1: Headlight creation (should exist after scene setup)
    test_results['creation'] = test_widget.scene_manager.headlight is not None
    logger.info(f"Headlight creation test: {'✓ PASSED' if test_results['creation'] else '✗ FAILED'}")
    
    # Test 2: Intensity changes
    test_results['intensity'] = test_widget.test_headlight_intensity()
    
    # Test 3: Enable/disable
    test_results['enable_disable'] = test_widget.test_headlight_enable_disable()
    
    # Test 4: Color changes
    test_results['color'] = test_widget.test_headlight_color()
    
    # Test 5: Camera following
    test_results['camera_following'] = test_widget.test_camera_following()
    
    # Test 6: Memory leak
    test_results['memory_leak'] = test_widget.test_memory_leak()
    
    # Test 7: Performance
    test_results['performance'] = test_widget.test_performance()
    
    # Summary
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    logger.info(f"\n{'='*60}")
    logger.info(f"HEADLIGHT VALIDATION TEST SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Tests passed: {passed_tests}/{total_tests}")
    
    for test_name, result in test_results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        logger.info(f"  {test_name.replace('_', ' ').title()}: {status}")
    
    if passed_tests == total_tests:
        logger.info("\n🎉 ALL HEADLIGHT TESTS PASSED! 🎉")
        logger.info("The headlight fix implementation is working correctly.")
    else:
        logger.error(f"\n❌ {total_tests - passed_tests} TESTS FAILED")
        logger.error("Some headlight functionality may not be working correctly.")
    
    logger.info(f"{'='*60}")
    
    # Keep window open for manual inspection
    logger.info("Test window will remain open for manual inspection.")
    logger.info("Close the window to exit.")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    run_headlight_validation_tests()