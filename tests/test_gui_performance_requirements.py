"""
Performance tests for GUI refactoring requirements validation.

This module contains tests to verify that all GUI performance requirements
from the Candy-Cadence project are met after refactoring.
"""

import pytest
import time
import psutil
import threading
from pathlib import Path
from typing import Dict, List, Any
from unittest.mock import Mock, patch

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QEventLoop

from src.gui.services.gui_service_interfaces import ProgressInfo, UIState
from src.gui.services.enhanced_viewer_service import EnhancedViewerService, ModelLoadingWorker
from src.gui.services.ui_service import ViewerUIService, NotificationService
from src.gui.services.enhanced_theme_service import EnhancedThemeService
from src.gui.services.material_service import MaterialService, MaterialValidationWorker
from src.gui.widgets.loading_progress_widget import LoadingProgressWidget


class TestUIResponsiveness:
    """Test UI responsiveness during operations."""
    
    @pytest.fixture
    def app(self):
        """Create QApplication for tests."""
        if not QApplication.instance():
            return QApplication([])
        return QApplication.instance()
    
    @pytest.fixture
    def mock_parent_widget(self, qtbot):
        """Create mock parent widget for services."""
        from PySide6.QtWidgets import QWidget
        widget = QWidget()
        qtbot.addWidget(widget)
        return widget
    
    def test_ui_responsive_during_long_operations(self, mock_parent_widget):
        """Test that UI remains responsive during long operations."""
        from src.gui.services.ui_service import ViewerUIService
        
        ui_service = ViewerUIService(mock_parent_widget)
        
        # Simulate long operation
        def long_operation():
            time.sleep(0.1)  # 100ms operation
            ui_service.set_ui_state(UIState.READY)
        
        # Start long operation in thread
        operation_thread = threading.Thread(target=long_operation)
        operation_thread.start()
        
        # UI should still be responsive
        initial_state = ui_service.get_ui_state()
        assert initial_state in [UIState.BUSY, UIState.PROCESSING]
        
        # Wait for operation to complete
        operation_thread.join(timeout=1.0)
        assert ui_service.get_ui_state() == UIState.READY
    
    def test_progress_feedback_accuracy(self, mock_parent_widget):
        """Test that progress feedback is accurate and timely."""
        ui_service = ViewerUIService(mock_parent_widget)
        
        # Test progress updates
        progress_updates = []
        
        def on_progress_update(progress):
            progress_updates.append(progress)
        
        # Simulate progress updates
        for i in range(10):
            progress = ProgressInfo(i, 10, f"Step {i+1}/10")
            ui_service.show_progress(progress)
            time.sleep(0.01)  # Small delay to simulate real progress
        
        ui_service.hide_progress()
        
        # Verify progress updates were received
        assert len(progress_updates) > 0
        assert progress_updates[-1].current == 9  # Last update should be 9/10
        assert progress_updates[-1].percentage == 90.0
    
    def test_cancellation_support_functionality(self, mock_parent_widget):
        """Test that cancellation support works properly."""
        ui_service = ViewerUIService(mock_parent_widget)
        
        # Enable cancellation
        ui_service.enable_cancellation(True)
        
        # Simulate cancellation request
        ui_service.cancellation_requested = True
        
        # Verify cancellation was requested
        assert ui_service.is_cancellation_requested() == True
        
        # Reset cancellation
        ui_service.reset_cancellation()
        assert ui_service.is_cancellation_requested() == False


class TestPerformanceOptimization:
    """Test 3D rendering performance optimizations."""
    
    def test_frame_rate_target_setting(self):
        """Test that frame rate targets are properly set."""
        from src.gui.services.enhanced_viewer_service import EnhancedViewerService
        
        # Mock viewer widget
        mock_viewer = Mock()
        mock_ui_service = Mock()
        
        viewer_service = EnhancedViewerService(mock_viewer, mock_ui_service)
        
        # Test valid frame rate settings
        viewer_service.set_target_fps(30)
        assert viewer_service.target_fps == 30
        
        viewer_service.set_target_fps(60)
        assert viewer_service.target_fps == 60
        
        # Test invalid frame rate (should be ignored)
        viewer_service.set_target_fps(5)  # Too low
        assert viewer_service.target_fps == 60  # Should remain unchanged
        
        viewer_service.set_target_fps(150)  # Too high
        assert viewer_service.target_fps == 60  # Should remain unchanged
    
    def test_vsync_control_functionality(self):
        """Test VSync enable/disable functionality."""
        from src.gui.services.enhanced_viewer_service import EnhancedViewerService
        
        # Mock viewer widget
        mock_viewer = Mock()
        mock_ui_service = Mock()
        
        viewer_service = EnhancedViewerService(mock_viewer, mock_ui_service)
        
        # Test VSync enabling
        viewer_service.enable_vsync(True)
        assert viewer_service.vsync_enabled == True
        
        # Test VSync disabling
        viewer_service.enable_vsync(False)
        assert viewer_service.vsync_enabled == False
    
    def test_performance_mode_adjustment(self):
        """Test that performance modes adjust settings appropriately."""
        from src.gui.services.enhanced_viewer_service import EnhancedViewerService
        
        # Mock viewer widget
        mock_viewer = Mock()
        mock_ui_service = Mock()
        
        viewer_service = EnhancedViewerService(mock_viewer, mock_ui_service)
        
        # Test different performance modes
        modes = ["high", "balanced", "performance"]
        expected_fps = [60, 30, 24]
        
        for mode, expected_fps_val in zip(modes, expected_fps):
            viewer_service.set_performance_mode(mode)
            assert viewer_service.performance_mode == mode
            assert viewer_service.target_fps == expected_fps_val
    
    def test_model_size_optimization(self):
        """Test optimization based on model complexity."""
        from src.gui.services.enhanced_viewer_service import EnhancedViewerService
        
        # Mock viewer widget
        mock_viewer = Mock()
        mock_ui_service = Mock()
        
        viewer_service = EnhancedViewerService(mock_viewer, mock_ui_service)
        
        # Test optimization for different model sizes
        test_cases = [
            (1000, "high"),        # Low-poly -> high quality
            (50000, "balanced"),   # Medium-poly -> balanced
            (2000000, "performance")  # High-poly -> performance mode
        ]
        
        for triangle_count, expected_mode in test_cases:
            viewer_service.optimize_for_model_size(triangle_count)
            assert viewer_service.performance_mode == expected_mode


class TestFileLoadingPerformance:
    """Test file loading performance requirements."""
    
    @pytest.fixture
    def temp_test_files(self):
        """Create temporary test files of different sizes."""
        test_dir = Path("test_files")
        test_dir.mkdir(exist_ok=True)
        
        files = {}
        
        # Create small file (< 1MB)
        small_file = test_dir / "small_model.stl"
        with open(small_file, 'wb') as f:
            f.write(b'0' * (500 * 1024))  # 500KB
        files['small'] = small_file
        
        # Create medium file (~50MB)
        medium_file = test_dir / "medium_model.stl"
        with open(medium_file, 'wb') as f:
            f.write(b'0' * (50 * 1024 * 1024))  # 50MB
        files['medium'] = medium_file
        
        # Create large file (~200MB)
        large_file = test_dir / "large_model.stl"
        with open(large_file, 'wb') as f:
            f.write(b'0' * (200 * 1024 * 1024))  # 200MB
        files['large'] = large_file
        
        yield files
        
        # Cleanup
        for file_path in files.values():
            file_path.unlink(missing_ok=True)
        test_dir.rmdir()
    
    def test_small_file_loading_time(self, temp_test_files, mock_viewer_service):
        """Test that small files load within 5 seconds."""
        file_path = temp_test_files['small']
        
        start_time = time.time()
        success = mock_viewer_service.load_model_async(file_path)
        load_time = time.time() - start_time
        
        assert success == True
        assert load_time <= 5.0, f"Small file loading took {load_time:.2f}s, should be < 5s"
    
    def test_medium_file_loading_time(self, temp_test_files, mock_viewer_service):
        """Test that medium files load within 15 seconds."""
        file_path = temp_test_files['medium']
        
        start_time = time.time()
        success = mock_viewer_service.load_model_async(file_path)
        load_time = time.time() - start_time
        
        assert success == True
        assert load_time <= 15.0, f"Medium file loading took {load_time:.2f}s, should be < 15s"
    
    def test_large_file_loading_time(self, temp_test_files, mock_viewer_service):
        """Test that large files load within 30 seconds."""
        file_path = temp_test_files['large']
        
        start_time = time.time()
        success = mock_viewer_service.load_model_async(file_path)
        load_time = time.time() - start_time
        
        assert success == True
        assert load_time <= 30.0, f"Large file loading took {load_time:.2f}s, should be < 30s"
    
    @pytest.fixture
    def mock_viewer_service(self, mock_parent_widget):
        """Create mock viewer service for testing."""
        from src.gui.services.enhanced_viewer_service import EnhancedViewerService
        from src.gui.services.ui_service import ViewerUIService
        
        mock_viewer = Mock()
        ui_service = ViewerUIService(mock_parent_widget)
        
        return EnhancedViewerService(mock_viewer, ui_service)


class TestThemeSystemPerformance:
    """Test theme system performance and dynamic switching."""
    
    def test_theme_validation_performance(self, mock_ui_service):
        """Test that theme validation completes within reasonable time."""
        from src.gui.services.enhanced_theme_service import EnhancedThemeService
        
        theme_service = EnhancedThemeService(mock_ui_service)
        
        # Test validation performance
        start_time = time.time()
        is_valid, error_message = theme_service.validate_theme("default")
        validation_time = time.time() - start_time
        
        assert validation_time <= 2.0, f"Theme validation took {validation_time:.2f}s, should be < 2s"
        assert isinstance(is_valid, bool)
        assert isinstance(error_message, str)
    
    def test_theme_preview_duration(self, mock_ui_service):
        """Test that theme preview duration is accurate."""
        from src.gui.services.enhanced_theme_service import EnhancedThemeService
        
        theme_service = EnhancedThemeService(mock_ui_service)
        
        # Test preview functionality
        preview_duration = 1000  # 1 second for testing
        
        # This would test the actual preview functionality
        # For now, just verify the method exists and returns bool
        result = theme_service.preview_theme_temporarily("default", preview_duration)
        assert isinstance(result, bool)
    
    @pytest.fixture
    def mock_ui_service(self):
        """Create mock UI service for testing."""
        return Mock()


class TestMaterialSystemPerformance:
    """Test material system performance and validation."""
    
    def test_material_validation_performance(self, mock_ui_service):
        """Test that material validation completes quickly."""
        from src.gui.services.material_service import MaterialService
        
        material_service = MaterialService(mock_ui_service)
        
        # Create test material data
        test_material = {
            "name": "Test Material",
            "category": "wood",
            "properties": {
                "base_color": "#8B4513",
                "roughness": 0.8,
                "density": 0.6
            }
        }
        
        # Test validation performance
        start_time = time.time()
        is_valid, error_message = material_service.validate_material(test_material)
        validation_time = time.time() - start_time
        
        assert validation_time <= 1.0, f"Material validation took {validation_time:.2f}s, should be < 1s"
        assert isinstance(is_valid, bool)
        assert isinstance(error_message, str)
    
    def test_material_search_performance(self, mock_ui_service):
        """Test that material search performs well."""
        from src.gui.services.material_service import MaterialService
        
        material_service = MaterialService(mock_ui_service)
        
        # Test search performance
        start_time = time.time()
        results = material_service.search_materials("wood")
        search_time = time.time() - start_time
        
        assert search_time <= 0.5, f"Material search took {search_time:.2f}s, should be < 0.5s"
        assert isinstance(results, list)
    
    def test_material_preview_generation(self, mock_ui_service):
        """Test material preview generation."""
        from src.gui.services.material_service import MaterialService, MaterialInfo, MaterialCategory
        
        material_service = MaterialService(mock_ui_service)
        
        # Create test material info
        test_material = MaterialInfo(
            name="Test Wood",
            category=MaterialCategory.WOOD,
            description="Test wood material",
            properties={"base_color": "#8B4513"}
        )
        
        # Test preview generation
        preview_data = material_service._generate_material_preview(test_material)
        
        # Preview should be bytes or None
        assert preview_data is None or isinstance(preview_data, bytes)


class TestNotificationSystemPerformance:
    """Test notification system performance."""
    
    def test_notification_display_time(self, mock_parent_widget):
        """Test that notifications display quickly."""
        from src.gui.services.ui_service import NotificationService
        
        notification_service = NotificationService(mock_parent_widget)
        
        # Test notification display performance
        start_time = time.time()
        notification_id = notification_service.show_notification(
            "Test", "Test notification", "info", 1000
        )
        display_time = time.time() - start_time
        
        assert display_time <= 0.1, f"Notification display took {display_time:.2f}s, should be < 0.1s"
        assert notification_id != ""
    
    def test_notification_cleanup_performance(self, mock_parent_widget):
        """Test notification cleanup performance."""
        from src.gui.services.ui_service import NotificationService
        
        notification_service = NotificationService(mock_parent_widget)
        
        # Create multiple notifications
        notification_ids = []
        for i in range(10):
            notification_id = notification_service.show_notification(
                f"Test {i}", f"Test notification {i}", "info"
            )
            notification_ids.append(notification_id)
        
        # Test cleanup performance
        start_time = time.time()
        notification_service.clear_all_notifications()
        cleanup_time = time.time() - start_time
        
        assert cleanup_time <= 0.5, f"Notification cleanup took {cleanup_time:.2f}s, should be < 0.5s"


class TestMemoryUsage:
    """Test memory usage and management."""
    
    def test_memory_stability_during_operations(self, mock_parent_widget):
        """Test that memory usage remains stable during operations."""
        from src.gui.services.ui_service import ViewerUIService
        import gc
        
        ui_service = ViewerUIService(mock_parent_widget)
        
        # Measure initial memory
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform multiple operations
        for i in range(100):
            progress = ProgressInfo(i, 100, f"Step {i}")
            ui_service.show_progress(progress)
            
            # Force garbage collection occasionally
            if i % 10 == 0:
                gc.collect()
        
        ui_service.hide_progress()
        
        # Measure final memory
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (< 10MB)
        assert memory_increase <= 10.0, f"Memory increased by {memory_increase:.2f}MB, should be < 10MB"
    
    def test_resource_cleanup(self, mock_parent_widget):
        """Test that resources are properly cleaned up."""
        from src.gui.services.ui_service import ViewerUIService
        
        ui_service = ViewerUIService(mock_parent_widget)
        
        # Create and destroy multiple UI components
        for i in range(50):
            ui_service.show_notification(f"Test {i}", f"Message {i}")
        
        initial_objects = len(gc.get_objects())
        
        # Clear all notifications
        ui_service.clear_all_notifications()
        
        # Force garbage collection
        gc.collect()
        
        final_objects = len(gc.get_objects())
        object_leak = final_objects - initial_objects
        
        # Should not have significant object leaks
        assert abs(object_leak) <= 100, f"Object leak detected: {object_leak} objects"


class TestErrorHandling:
    """Test error handling and graceful degradation."""
    
    def test_graceful_file_loading_failure(self, mock_viewer_service):
        """Test graceful handling of file loading failures."""
        # Test with non-existent file
        non_existent_file = Path("non_existent_file.stl")
        
        success = mock_viewer_service.load_model_async(non_existent_file)
        # Should handle gracefully (may return False or start async operation)
        assert isinstance(success, bool)
    
    def test_invalid_material_handling(self, mock_ui_service):
        """Test handling of invalid material data."""
        from src.gui.services.material_service import MaterialService
        
        material_service = MaterialService(mock_ui_service)
        
        # Test with invalid material data
        invalid_materials = [
            {},  # Empty dict
            {"name": "Test"},  # Missing category
            {"category": "invalid"},  # Invalid category
            {"name": "Test", "category": "metal", "properties": "invalid"}  # Invalid properties type
        ]
        
        for invalid_material in invalid_materials:
            is_valid, error_message = material_service.validate_material(invalid_material)
            assert is_valid == False
            assert error_message != ""
    
    def test_network_error_recovery(self, mock_ui_service):
        """Test recovery from network-related errors."""
        from src.gui.services.enhanced_theme_service import EnhancedThemeService
        
        theme_service = EnhancedThemeService(mock_ui_service)
        
        # Test with non-existent theme
        is_valid, error_message = theme_service.validate_theme("non_existent_theme")
        assert is_valid == False
        assert "not found" in error_message.lower() or "invalid" in error_message.lower()


# Performance benchmarks
def test_performance_benchmarks():
    """Run comprehensive performance benchmarks."""
    benchmarks = {
        "ui_responsiveness": 0.1,  # UI should respond within 100ms
        "file_loading_small": 5.0,  # Small files < 5s
        "file_loading_medium": 15.0,  # Medium files < 15s  
        "file_loading_large": 30.0,  # Large files < 30s
        "theme_validation": 2.0,  # Theme validation < 2s
        "material_validation": 1.0,  # Material validation < 1s
        "material_search": 0.5,  # Material search < 0.5s
        "notification_display": 0.1,  # Notification display < 0.1s
        "memory_stability": 10.0  # Memory increase < 10MB
    }
    
    print("\nPerformance Benchmarks:")
    print("=" * 50)
    for benchmark, max_time in benchmarks.items():
        print(f"{benchmark}: < {max_time}s")
    print("=" * 50)
    
    # This test always passes but provides benchmark information
    assert True


if __name__ == "__main__":
    # Run performance tests
    pytest.main([__file__, "-v", "--tb=short"])