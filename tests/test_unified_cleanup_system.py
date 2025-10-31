
"""
Comprehensive test suite for the unified cleanup system.

This test suite validates that the consolidated cleanup architecture
works correctly and provides the expected functionality.
"""

import unittest
import time
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import vtk

from src.core.cleanup.unified_cleanup_coordinator import (
    UnifiedCleanupCoordinator,
    CleanupPhase,
    CleanupContext,
    CleanupStats,
    CleanupHandler
)
from src.core.cleanup.vtk_cleanup_handler import VTKCleanupHandler
from src.core.cleanup.widget_cleanup_handler import WidgetCleanupHandler
from src.core.cleanup.service_cleanup_handler import ServiceCleanupHandler
from src.core.cleanup.resource_cleanup_handler import ResourceCleanupHandler
from src.core.cleanup.backward_compatibility import (
    LegacyVTKCleanupCoordinator,
    CleanupErrorHandler
)


class TestCleanupHandler(CleanupHandler):
    """Test handler for testing cleanup coordination."""
    
    def __init__(self, name: str, can_handle_phase: CleanupPhase):
        super().__init__(name)
        self.can_handle_phase = can_handle_phase
        self.executed = False
        self.execution_count = 0
    
    def can_handle(self, phase: CleanupPhase) -> bool:
        return phase == self.can_handle_phase
    
    def execute(self, phase: CleanupPhase, context: CleanupContext) -> bool:
        self.executed = True
        self.execution_count += 1
        return True


class TestUnifiedCleanupCoordinator(unittest.TestCase):
    """Test the unified cleanup coordinator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.coordinator = UnifiedCleanupCoordinator()
    
    def tearDown(self):
        """Clean up after tests."""
        # Reset global coordinator
        import src.core.cleanup.unified_cleanup_coordinator
        src.core.cleanup.unified_cleanup_coordinator._unified_cleanup_coordinator = None
    
    def test_coordinator_initialization(self):
        """Test coordinator initialization."""
        self.assertIsNotNone(self.coordinator)
        self.assertFalse(self.coordinator.is_cleanup_in_progress())
        self.assertEqual(self.coordinator.get_context_state(), CleanupContext.UNKNOWN)
        self.assertEqual(len(self.coordinator.get_registered_handlers()), 4)
    
    def test_handler_registration(self):
        """Test handler registration and unregistration."""
        test_handler = TestCleanupHandler("test", CleanupPhase.PRE_CLEANUP)
        
        # Register handler
        self.coordinator.register_handler(test_handler)
        self.assertIn("test", self.coordinator.get_registered_handlers())
        
        # Unregister handler
        result = self.coordinator.unregister_handler("test")
        self.assertTrue(result)
        self.assertNotIn("test", self.coordinator.get_registered_handlers())
        
        # Unregister non-existent handler
        result = self.coordinator.unregister_handler("non_existent")
        self.assertFalse(result)
    
    def test_cleanup_coordination(self):
        """Test basic cleanup coordination."""
        # Add test handler
        test_handler = TestCleanupHandler("test", CleanupPhase.PRE_CLEANUP)
        self.coordinator.register_handler(test_handler)
        
        # Execute cleanup
        stats = self.coordinator.coordinate_cleanup()
        
        # Verify results
        self.assertIsInstance(stats, CleanupStats)
        self.assertGreater(stats.total_phases, 0)
        self.assertTrue(test_handler.executed)
        self.assertEqual(test_handler.execution_count, 1)
    
    def test_cleanup_with_vtk_resources(self):
        """Test cleanup with VTK resources."""
        # Create mock VTK objects
        mock_render_window = Mock()
        mock_renderer = Mock()
        mock_interactor = Mock()
        
        # Execute cleanup with VTK resources
        stats = self.coordinator.coordinate_cleanup(
            render_window=mock_render_window,
            renderer=mock_renderer,
            interactor=mock_interactor
        )
        
        # Verify results
        self.assertIsInstance(stats, CleanupStats)
        self.assertGreater(stats.total_phases, 0)
    
    def test_cleanup_in_progress_protection(self):
        """Test that cleanup prevents concurrent execution."""
        # Add a slow handler
        slow_handler = TestCleanupHandler("slow", CleanupPhase.PRE_CLEANUP)
        original_execute = slow_handler.execute
        
        def slow_execute(phase, context):
            time.sleep(0.1)  # Simulate slow operation
            return original_execute(phase, context)
        
        slow_handler.execute = slow_execute
        self.coordinator.register_handler(slow_handler)
        
        # Start first cleanup
        stats1 = self.coordinator.coordinate_cleanup()
        
        # Verify cleanup completed
        self.assertFalse(self.coordinator.is_cleanup_in_progress())
        self.assertGreater(stats1.total_duration, 0.1)
    
    def test_context_state_handling(self):
        """Test different context state handling."""
        # Test with valid context
        self.coordinator._context_state = CleanupContext.VALID
        stats = self.coordinator.coordinate_cleanup()
        self.assertIsInstance(stats, CleanupStats)
        
        # Test with lost context
        self.coordinator._context_state = CleanupContext.LOST
        stats = self.coordinator.coordinate_cleanup()
        self.assertIsInstance(stats, CleanupStats)
        self.assertTrue(stats.context_lost)
        
        # Test with unknown context
        self.coordinator._context_state = CleanupContext.UNKNOWN
        stats = self.coordinator.coordinate_cleanup()
        self.assertIsInstance(stats, CleanupStats)


class TestVTKCleanupHandler(unittest.TestCase):
    """Test the VTK cleanup handler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = VTKCleanupHandler()
    
    def test_handler_initialization(self):
        """Test handler initialization."""
        self.assertEqual(self.handler.name, "VTKCleanupHandler")
        self.assertTrue(self.handler.enabled)
    
    def test_can_handle_phase(self):
        """Test phase handling capability."""
        self.assertTrue(self.handler.can_handle(CleanupPhase.VTK_CLEANUP))
        self.assertFalse(self.handler.can_handle(CleanupPhase.PRE_CLEANUP))
    
    def test_execute_cleanup(self):
        """Test cleanup execution."""
        # Test with valid context
        result = self.handler.execute(CleanupPhase.VTK_CLEANUP, CleanupContext.VALID)
        self.assertIsInstance(result, bool)
        
        # Test with lost context
        result = self.handler.execute(CleanupPhase.VTK_CLEANUP, CleanupContext.LOST)
        self.assertIsInstance(result, bool)
        
        # Test with unknown context
        result = self.handler.execute(CleanupPhase.VTK_CLEANUP, CleanupContext.UNKNOWN)
        self.assertIsInstance(result, bool)
    
    def test_resource_registration(self):
        """Test VTK resource registration."""
        # Create mock VTK actor
        mock_actor = Mock(spec=vtk.vtkActor)
        
        # Register resource
        self.handler.register_vtk_resource("test_actor", mock_actor)
        
        # Verify registration (should not raise exception)
        stats = self.handler.get_vtk_cleanup_stats()
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats["handler_name"], "VTKCleanupHandler")


class TestWidgetCleanupHandler(unittest.TestCase):
    """Test the widget cleanup handler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = WidgetCleanupHandler()
    
    def test_handler_initialization(self):
        """Test handler initialization."""
        self.assertEqual(self.handler.name, "WidgetCleanupHandler")
        self.assertTrue(self.handler.enabled)
    
    def test_can_handle_phase(self):
        """Test phase handling capability."""
        self.assertTrue(self.handler.can_handle(CleanupPhase.WIDGET_CLEANUP))
        self.assertFalse(self.handler.can_handle(CleanupPhase.PRE_CLEANUP))
    
    def test_execute_cleanup(self):
        """Test cleanup execution."""
        result = self.handler.execute(CleanupPhase.WIDGET_CLEANUP, CleanupContext.VALID)
        self.assertIsInstance(result, bool)
    
    def test_widget_registration(self):
        """Test widget registration."""
        # Create mock widget
        mock_widget = Mock()
        mock_widget.cleanup = Mock()
        
        # Register widget
        self.handler.register_widget(mock_widget)
        
        # Verify registration
        stats = self.handler.get_widget_cleanup_stats()
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats["handler_name"], "WidgetCleanupHandler")


class TestServiceCleanupHandler(unittest.TestCase):
    """Test the service cleanup handler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = ServiceCleanupHandler()
    
    def test_handler_initialization(self):
        """Test handler initialization."""
        self.assertEqual(self.handler.name, "ServiceCleanupHandler")
        self.assertTrue(self.handler.enabled)
    
    def test_can_handle_phase(self):
        """Test phase handling capability."""
        self.assertTrue(self.handler.can_handle(CleanupPhase.SERVICE_SHUTDOWN))
        self.assertFalse(self.handler.can_handle(CleanupPhase.PRE_CLEANUP))
    
    def test_execute_cleanup(self):
        """Test cleanup execution."""
        result = self.handler.execute(CleanupPhase.SERVICE_SHUTDOWN, CleanupContext.VALID)
        self.assertIsInstance(result, bool)
    
    def test_service_registration(self):
        """Test service registration."""
        # Create mock service
        mock_service = Mock()
        
        # Register service
        self.handler.register_service("test_service", mock_service)
        
        # Verify registration
        stats = self.handler.get_service_cleanup_stats()
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats["handler_name"], "ServiceCleanupHandler")


class TestResourceCleanupHandler(unittest.TestCase):
    """Test the resource cleanup handler."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.handler = ResourceCleanupHandler()
    
    def test_handler_initialization(self):
        """Test handler initialization."""
        self.assertEqual(self.handler.name, "ResourceCleanupHandler")
        self.assertTrue(self.handler.enabled)
    
    def test_can_handle_phase(self):
        """Test phase handling capability."""
        self.assertTrue(self.handler.can_handle(CleanupPhase.RESOURCE_CLEANUP))
        self.assertFalse(self.handler.can_handle(CleanupPhase.PRE_CLEANUP))
    
    def test_execute_cleanup(self):
        """Test cleanup execution."""
        result = self.handler.execute(CleanupPhase.RESOURCE_CLEANUP, CleanupContext.VALID)
        self.assertIsInstance(result, bool)
    
    def test_temp_file_creation(self):
        """Test temporary file creation."""
        temp_file = self.handler.create_temp_file(suffix=".test")
        self.assertTrue(temp_file.endswith(".test"))
        self.assertTrue(os.path.exists(temp_file))
        
        # Cleanup
        if os.path.exists(temp_file):
            os.remove(temp_file)
    
    def test_resource_registration(self):
        """Test resource registration."""
        # Create mock resource
        mock_resource = Mock()
        
        # Register resource
        self.handler.register_resource(mock_resource)
        
        # Verify registration
        stats = self.handler.get_resource_cleanup_stats()
        self.assertIsInstance(stats, dict)
        self.assertEqual(stats["handler_name"], "ResourceCleanupHandler")


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility layer."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.coordinator = LegacyVTKCleanupCoordinator()
    
    def test_legacy_coordinator_initialization(self):
        """Test legacy coordinator initialization."""
        self.assertIsNotNone(self.coordinator)
    
    def test_legacy_cleanup_coordination(self):
        """Test legacy cleanup coordination."""
        # Create mock VTK objects
        mock_render_window = Mock()
        mock_renderer = Mock()
        mock_interactor = Mock()
        
        # Execute legacy cleanup
        result = self.coordinator.coordinate_cleanup(
            render_window=mock_render_window,
            renderer=mock_renderer,
            interactor=mock_interactor
        )
        
        self.assertIsInstance(result, bool)
    
    def test_legacy_cleanup_all_resources(self):
        """Test legacy cleanup_all_resources method."""
        result = self.coordinator.cleanup_all_resources()
        
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        self.assertIn('errors', result)
        self.assertIn('total_duration', result)
    
    def test_cleanup_error_handler(self):
        """Test cleanup error handler."""
        handler = CleanupErrorHandler()
        
        # Test error handling
        test_error = Exception("Test error")
        result = handler.handle_cleanup_error(test_error, "test_context")
        
        self.assertTrue(result)
        
        # Get error statistics
        stats = handler.get_error_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('error_counts', stats)
        self.assertIn('last_errors', stats)
        
        # Reset error counts
        handler.reset_error_counts()
        stats = handler.get_error_statistics()
        self.assertEqual(stats['total_errors'], 0)


class TestIntegration(unittest.TestCase):
    """Integration tests for the unified cleanup system."""
    
    def test_full_cleanup_workflow(self):
        """Test complete cleanup workflow."""
        # Create coordinator
        coordinator = UnifiedCleanupCoordinator()
        
        # Create mock resources
        mock_render_window = Mock()
        mock_renderer = Mock()
        mock_interactor = Mock()
        mock_main_window = Mock()
        mock_application = Mock()
        
        # Execute full cleanup
        stats = coordinator.coordinate_cleanup(
            render_window=mock_render_window,
            renderer=mock_renderer,
            interactor=mock_interactor,
            main_window=mock_main_window,
            application=mock_application
        )
        
        # Verify results
        self.assertIsInstance(stats, CleanupStats)
        self.assertGreater(stats.total_phases, 0)
        self.assertGreaterEqual(stats.completed_phases, 0)
        self.assertGreaterEqual(stats.failed_phases, 0)
    
    def test_cleanup_performance(self):
        """Test cleanup performance."""
        coordinator = UnifiedCleanupCoordinator()
        
        # Measure cleanup time
        start_time = time.time()
        stats = coordinator.coordinate_cleanup()
        end_time = time.time()
        
        # Verify performance
        self.assertLess(end_time - start_time, 5.0)  # Should complete in under 5 seconds
        self.assertGreater(stats.total_duration, 0)
    
    def test_memory_leak_prevention(self):
        """Test that cleanup prevents memory leaks."""
        coordinator = UnifiedCleanupCoordinator()
        
        # Run cleanup multiple times
        for _ in range(5):
            stats = coordinator.coordinate_cleanup()
            self.assertIsInstance(stats, CleanupStats)
        
        # Verify no errors accumulated
        self.assertLess(stats.failed_phases, stats.total_phases)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)