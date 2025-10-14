"""
Tests for the 3D viewer widget.

This module provides comprehensive testing for the PyQt3D viewer widget,
including unit tests, integration tests, and performance tests.
"""

import gc
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from parsers.stl_parser import STLModel, Triangle, Vector3D, ModelStats, STLFormat


class TestViewerWidget(unittest.TestCase):
    """Test cases for the 3D viewer widget."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class with sample data."""
        # Create a simple test model
        cls.test_triangles = [
            Triangle(
                normal=Vector3D(0, 0, 1),
                vertex1=Vector3D(0, 0, 0),
                vertex2=Vector3D(1, 0, 0),
                vertex3=Vector3D(0, 1, 0)
            ),
            Triangle(
                normal=Vector3D(0, 0, 1),
                vertex1=Vector3D(1, 0, 0),
                vertex2=Vector3D(1, 1, 0),
                vertex3=Vector3D(0, 1, 0)
            )
        ]
        
        cls.test_stats = ModelStats(
            vertex_count=6,
            triangle_count=2,
            min_bounds=Vector3D(0, 0, 0),
            max_bounds=Vector3D(1, 1, 0),
            file_size_bytes=1024,
            format_type=STLFormat.BINARY,
            parsing_time_seconds=0.1
        )
        
        cls.test_model = STLModel(
            header="Test Model",
            triangles=cls.test_triangles,
            stats=cls.test_stats
        )
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock PyQt3D components if not available
        self.pyqt3d_patcher = patch.dict('sys.modules', {
            'PyQt3D': MagicMock(),
            'PyQt3D.Qt3DCore': MagicMock(),
            'PyQt3D.Qt3DExtras': MagicMock(),
            'PyQt3D.Qt3DRender': MagicMock(),
            'PyQt3D.Qt3DInput': MagicMock()
        })
        self.pyqt3d_patcher.start()
        
        # Mock PySide6 components
        self.pyside6_patcher = patch.dict('sys.modules', {
            'PySide6': MagicMock(),
            'PySide6.QtCore': MagicMock(),
            'PySide6.QtGui': MagicMock(),
            'PySide6.QtWidgets': MagicMock()
        })
        self.pyside6_patcher.start()
        
        # Mock logging
        self.logging_patcher = patch('core.logging_config.get_logger')
        self.mock_logger = Mock()
        self.logging_patcher.start()
        self.logging_patcher.return_value = self.mock_logger
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.pyqt3d_patcher.stop()
        self.pyside6_patcher.stop()
        self.logging_patcher.stop()
        gc.collect()
    
    def test_viewer_widget_initialization(self):
        """Test that the viewer widget initializes correctly."""
        # Import after mocking
        from gui.viewer_widget import Viewer3DWidget
        
        # Create widget
        widget = Viewer3DWidget()
        
        # Check initial state
        self.assertIsNone(widget.current_model)
        self.assertEqual(widget.render_mode.value, "solid")
        self.assertIsNotNone(widget.camera)
        self.assertIsNotNone(widget.camera_controller)
        
        # Clean up
        widget.cleanup()
    
    def test_model_loading(self):
        """Test loading a model into the viewer."""
        from gui.viewer_widget import Viewer3DWidget
        
        # Create widget
        widget = Viewer3DWidget()
        
        # Load model
        result = widget.load_model(self.test_model)
        
        # Check result
        self.assertTrue(result)
        self.assertEqual(widget.current_model, self.test_model)
        
        # Check logging
        self.mock_logger.info.assert_called()
        
        # Clean up
        widget.cleanup()
    
    def test_model_info(self):
        """Test getting model information."""
        from gui.viewer_widget import Viewer3DWidget
        
        # Create widget
        widget = Viewer3DWidget()
        
        # Load model
        widget.load_model(self.test_model)
        
        # Get model info
        info = widget.get_model_info()
        
        # Check info
        self.assertIsNotNone(info)
        self.assertEqual(info['triangle_count'], 2)
        self.assertEqual(info['vertex_count'], 6)
        self.assertEqual(info['format'], 'binary')
        self.assertEqual(len(info['dimensions']), 3)
        
        # Clean up
        widget.cleanup()
    
    def test_render_mode_changes(self):
        """Test changing render modes."""
        from gui.viewer_widget import Viewer3DWidget, RenderMode
        
        # Create widget
        widget = Viewer3DWidget()
        
        # Test each render mode
        for mode in [RenderMode.SOLID, RenderMode.WIREFRAME, RenderMode.POINTS]:
            widget._set_render_mode(mode)
            self.assertEqual(widget.render_mode, mode)
        
        # Clean up
        widget.cleanup()
    
    def test_light_controls(self):
        """Test light intensity and position controls."""
        from gui.viewer_widget import Viewer3DWidget
        
        # Create widget
        widget = Viewer3DWidget()
        
        # Test light intensity
        widget.set_light_intensity(0.8)
        # In mocked environment, we can't check actual values, but we can ensure no errors
        
        # Test light position
        widget.set_light_position(5.0, 10.0, 15.0)
        
        # Clean up
        widget.cleanup()
    
    def test_view_reset(self):
        """Test view reset functionality."""
        from gui.viewer_widget import Viewer3DWidget
        
        # Create widget
        widget = Viewer3DWidget()
        
        # Load model
        widget.load_model(self.test_model)
        
        # Reset view
        widget.reset_view()
        
        # Check logging
        self.mock_logger.debug.assert_called()
        
        # Clean up
        widget.cleanup()
    
    def test_clear_scene(self):
        """Test clearing the scene."""
        from gui.viewer_widget import Viewer3DWidget
        
        # Create widget
        widget = Viewer3DWidget()
        
        # Load model
        widget.load_model(self.test_model)
        
        # Clear scene
        widget.clear_scene()
        
        # Check model is removed
        self.assertIsNone(widget.current_model)
        
        # Clean up
        widget.cleanup()
    
    def test_performance_monitoring(self):
        """Test performance monitoring functionality."""
        from gui.viewer_widget import Viewer3DWidget
        
        # Create widget
        widget = Viewer3DWidget()
        
        # Mock the performance update
        widget._update_performance()
        
        # Check that FPS is tracked
        self.assertIsInstance(widget.current_fps, float)
        
        # Clean up
        widget.cleanup()
    
    def test_memory_cleanup(self):
        """Test memory cleanup on model removal."""
        from gui.viewer_widget import Viewer3DWidget
        
        # Create widget
        widget = Viewer3DWidget()
        
        # Load model
        widget.load_model(self.test_model)
        
        # Check model is loaded
        self.assertIsNotNone(widget.current_model)
        
        # Remove model
        widget._remove_current_model()
        
        # Check model is removed
        self.assertIsNone(widget.current_model)
        
        # Clean up
        widget.cleanup()
    
    def test_camera_fitting(self):
        """Test camera fitting to model bounds."""
        from gui.viewer_widget import Viewer3DWidget
        
        # Create widget
        widget = Viewer3DWidget()
        
        # Test camera fitting
        widget._fit_camera_to_model(self.test_model)
        
        # Check logging
        self.mock_logger.debug.assert_called()
        
        # Clean up
        widget.cleanup()
    
    @patch('sys.platform', 'win32')
    def test_platform_specific_behavior(self):
        """Test platform-specific behavior on Windows."""
        from gui.viewer_widget import Viewer3DWidget
        
        # Create widget
        widget = Viewer3DWidget()
        
        # Check that widget initializes correctly on Windows
        self.assertIsNotNone(widget.view)
        
        # Clean up
        widget.cleanup()


class TestViewerWidgetPerformance(unittest.TestCase):
    """Performance tests for the 3D viewer widget."""
    
    def setUp(self):
        """Set up performance test fixtures."""
        # Mock PyQt3D components
        self.pyqt3d_patcher = patch.dict('sys.modules', {
            'PyQt3D': MagicMock(),
            'PyQt3D.Qt3DCore': MagicMock(),
            'PyQt3D.Qt3DExtras': MagicMock(),
            'PyQt3D.Qt3DRender': MagicMock(),
            'PyQt3D.Qt3DInput': MagicMock()
        })
        self.pyqt3d_patcher.start()
        
        # Mock PySide6 components
        self.pyside6_patcher = patch.dict('sys.modules', {
            'PySide6': MagicMock(),
            'PySide6.QtCore': MagicMock(),
            'PySide6.QtGui': MagicMock(),
            'PySide6.QtWidgets': MagicMock()
        })
        self.pyside6_patcher.start()
        
        # Mock logging
        self.logging_patcher = patch('core.logging_config.get_logger')
        self.mock_logger = Mock()
        self.logging_patcher.start()
        self.logging_patcher.return_value = self.mock_logger
        
        # Create a large test model
        self.large_model = self._create_large_model(10000)  # 10K triangles
    
    def tearDown(self):
        """Clean up performance test fixtures."""
        self.pyqt3d_patcher.stop()
        self.pyside6_patcher.stop()
        self.logging_patcher.stop()
        gc.collect()
    
    def _create_large_model(self, triangle_count: int) -> STLModel:
        """Create a large test model with specified triangle count."""
        triangles = []
        
        for i in range(triangle_count):
            # Create a simple triangle at different positions
            x = i % 100
            y = (i // 100) % 100
            z = (i // 10000)
            
            triangle = Triangle(
                normal=Vector3D(0, 0, 1),
                vertex1=Vector3D(x, y, z),
                vertex2=Vector3D(x + 1, y, z),
                vertex3=Vector3D(x, y + 1, z)
            )
            triangles.append(triangle)
        
        stats = ModelStats(
            vertex_count=triangle_count * 3,
            triangle_count=triangle_count,
            min_bounds=Vector3D(0, 0, 0),
            max_bounds=Vector3D(100, 100, triangle_count // 10000),
            file_size_bytes=triangle_count * 50,  # Approximate
            format_type=STLFormat.BINARY,
            parsing_time_seconds=triangle_count / 10000.0
        )
        
        return STLModel(
            header=f"Large Test Model with {triangle_count} triangles",
            triangles=triangles,
            stats=stats
        )
    
    def test_large_model_loading_performance(self):
        """Test performance when loading large models."""
        from gui.viewer_widget import Viewer3DWidget
        
        # Create widget
        widget = Viewer3DWidget()
        
        # Measure loading time
        start_time = time.time()
        result = widget.load_model(self.large_model)
        load_time = time.time() - start_time
        
        # Check result
        self.assertTrue(result)
        self.assertEqual(widget.current_model.stats.triangle_count, 10000)
        
        # Check performance (should load within reasonable time)
        self.assertLess(load_time, 5.0, "Large model should load within 5 seconds")
        
        # Clean up
        widget.cleanup()
    
    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations."""
        import psutil
        import os
        
        from gui.viewer_widget import Viewer3DWidget
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Perform repeated operations
        for i in range(10):
            widget = Viewer3DWidget()
            widget.load_model(self.large_model)
            widget.clear_scene()
            widget.cleanup()
            del widget
            
            # Force garbage collection
            gc.collect()
        
        # Check final memory usage
        final_memory = process.memory_info().rss
        memory_increase = (final_memory - initial_memory) / 1024 / 1024  # MB
        
        # Memory increase should be minimal
        self.assertLess(memory_increase, 50, "Memory increase should be less than 50MB after repeated operations")


class TestViewerWidgetIntegration(unittest.TestCase):
    """Integration tests for the 3D viewer widget."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        # Mock PyQt3D components
        self.pyqt3d_patcher = patch.dict('sys.modules', {
            'PyQt3D': MagicMock(),
            'PyQt3D.Qt3DCore': MagicMock(),
            'PyQt3D.Qt3DExtras': MagicMock(),
            'PyQt3D.Qt3DRender': MagicMock(),
            'PyQt3D.Qt3DInput': MagicMock()
        })
        self.pyqt3d_patcher.start()
        
        # Mock PySide6 components
        self.pyside6_patcher = patch.dict('sys.modules', {
            'PySide6': MagicMock(),
            'PySide6.QtCore': MagicMock(),
            'PySide6.QtGui': MagicMock(),
            'PySide6.QtWidgets': MagicMock()
        })
        self.pyside6_patcher.start()
        
        # Mock logging
        self.logging_patcher = patch('core.logging_config.get_logger')
        self.mock_logger = Mock()
        self.logging_patcher.start()
        self.logging_patcher.return_value = self.mock_logger
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        self.pyqt3d_patcher.stop()
        self.pyside6_patcher.stop()
        self.logging_patcher.stop()
        gc.collect()
    
    def test_stl_parser_integration(self):
        """Test integration with STL parser."""
        from gui.viewer_widget import Viewer3DWidget
        from parsers.stl_parser import STLParser
        
        # Create a test STL file path
        test_file = Path(__file__).parent / "sample_files" / "cube_binary.stl"
        
        if test_file.exists():
            # Parse STL file
            parser = STLParser()
            model = parser.parse_file(test_file)
            
            # Create viewer and load model
            widget = Viewer3DWidget()
            result = widget.load_model(model)
            
            # Check result
            self.assertTrue(result)
            self.assertIsNotNone(widget.current_model)
            
            # Check model info
            info = widget.get_model_info()
            self.assertIsNotNone(info)
            self.assertGreater(info['triangle_count'], 0)
            
            # Clean up
            widget.cleanup()
    
    def test_error_handling(self):
        """Test error handling for invalid operations."""
        from gui.viewer_widget import Viewer3DWidget
        
        # Create widget
        widget = Viewer3DWidget()
        
        # Try to load None model
        result = widget.load_model(None)
        self.assertFalse(result)
        
        # Check error logging
        self.mock_logger.error.assert_called()
        
        # Clean up
        widget.cleanup()


if __name__ == '__main__':
    unittest.main()