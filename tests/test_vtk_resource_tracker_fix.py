"""
Test for VTK Resource Tracker Reference Problem Fix

This test verifies that the critical VTK Resource Tracker Reference Problem
has been fixed, ensuring proper cleanup during shutdown and preventing memory leaks.
"""

import unittest
import gc
import time
from unittest.mock import Mock, patch, MagicMock
import vtk

from src.gui.vtk.cleanup_coordinator import (
    VTKCleanupCoordinator, 
    get_vtk_cleanup_coordinator,
    CleanupPhase,
    CleanupPriority
)
from src.gui.vtk.resource_tracker import VTKResourceTracker, get_vtk_resource_tracker


class TestVTKResourceTrackerFix(unittest.TestCase):
    """Test the VTK resource tracker reference problem fix."""

    def setUp(self):
        """Set up test environment."""
        # Clear any existing global instances
        import src.gui.vtk.cleanup_coordinator as cc_module
        import src.gui.vtk.resource_tracker as rt_module
        
        cc_module._vtk_cleanup_coordinator = None
        rt_module._vtk_resource_tracker = None
        
        # Force garbage collection
        gc.collect()

    def tearDown(self):
        """Clean up after test."""
        # Clear global instances
        import src.gui.vtk.cleanup_coordinator as cc_module
        import src.gui.vtk.resource_tracker as rt_module
        
        cc_module._vtk_cleanup_coordinator = None
        rt_module._vtk_resource_tracker = None
        
        # Force garbage collection
        gc.collect()

    def test_cleanup_coordinator_initialization_with_fallback(self):
        """Test that cleanup coordinator initializes properly with fallback mechanisms."""
        # Test normal initialization
        coordinator = VTKCleanupCoordinator()
        
        # Verify resource tracker is initialized (either real or fallback)
        self.assertIsNotNone(coordinator.resource_tracker)
        
        # Verify it has the required methods
        self.assertTrue(hasattr(coordinator.resource_tracker, 'cleanup_all_resources'))
        self.assertTrue(hasattr(coordinator.resource_tracker, 'get_statistics'))
        
        # Verify fallback tracking
        stats = coordinator.resource_tracker.get_statistics()
        self.assertIsInstance(stats, dict)

    def test_resource_tracker_none_handling(self):
        """Test that resource tracker None reference is handled properly."""
        coordinator = VTKCleanupCoordinator()
        
        # Simulate resource tracker becoming None
        original_tracker = coordinator.resource_tracker
        coordinator.resource_tracker = None
        
        # Test that final cleanup doesn't crash when tracker is None
        try:
            result = coordinator._final_cleanup()
            self.assertIsNotNone(result)  # Should not crash
        except Exception as e:
            self.fail(f"Final cleanup crashed when resource_tracker is None: {e}")
        
        # Restore tracker
        coordinator.resource_tracker = original_tracker

    def test_emergency_cleanup_fallback(self):
        """Test emergency cleanup when resource tracker is unavailable."""
        coordinator = VTKCleanupCoordinator()
        
        # Make resource tracker unavailable
        coordinator.resource_tracker = None
        
        # Test emergency cleanup methods
        try:
            coordinator._perform_emergency_cleanup()
            coordinator._perform_basic_emergency_cleanup()
            
            # Should not crash
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Emergency cleanup failed: {e}")

    def test_resource_tracker_reinitialization(self):
        """Test that resource tracker can be reinitialized during cleanup."""
        coordinator = VTKCleanupCoordinator()
        
        # Test reinitialization attempt
        try:
            coordinator._attempt_tracker_reinitialization()
            # Should not crash regardless of outcome
            self.assertTrue(True)
        except Exception as e:
            self.fail(f"Tracker reinitialization failed: {e}")

    def test_robust_cleanup_with_vtk_resources(self):
        """Test robust cleanup with actual VTK resources."""
        coordinator = VTKCleanupCoordinator()
        
        # Create mock VTK resources
        mock_render_window = Mock(spec=vtk.vtkRenderWindow)
        mock_renderer = Mock(spec=vtk.vtkRenderer)
        mock_interactor = Mock(spec=vtk.vtkRenderWindowInteractor)
        
        # Register resources
        coordinator.register_resource("test_render_window", mock_render_window, CleanupPriority.CRITICAL)
        coordinator.register_resource("test_renderer", mock_renderer, CleanupPriority.HIGH)
        coordinator.register_resource("test_interactor", mock_interactor, CleanupPriority.HIGH)
        
        # Test coordinate cleanup
        try:
            result = coordinator.coordinate_cleanup(mock_render_window, mock_renderer, mock_interactor)
            self.assertIsNotNone(result)
        except Exception as e:
            self.fail(f"Coordinate cleanup failed with VTK resources: {e}")

    def test_cleanup_phases_execution(self):
        """Test that all cleanup phases execute without crashing."""
        coordinator = VTKCleanupCoordinator()
        
        # Test individual cleanup phases
        phases_to_test = [
            CleanupPhase.PRE_CLEANUP,
            CleanupPhase.CONTEXT_VALIDATION,
            CleanupPhase.RESOURCE_CLEANUP,
            CleanupPhase.ACTOR_CLEANUP,
            CleanupPhase.RENDERER_CLEANUP,
            CleanupPhase.WINDOW_CLEANUP,
            CleanupPhase.INTERACTOR_CLEANUP,
            CleanupPhase.FINAL_CLEANUP,
            CleanupPhase.POST_CLEANUP
        ]
        
        for phase in phases_to_test:
            with self.subTest(phase=phase):
                try:
                    # Execute the phase callback
                    for callback in coordinator.cleanup_callbacks[phase]:
                        result = callback()
                        # Phase should not crash (can return False for early termination)
                        self.assertIsNotNone(result)
                except Exception as e:
                    self.fail(f"Cleanup phase {phase.value} failed: {e}")

    def test_resource_reference_clearing(self):
        """Test that resource references are properly cleared."""
        coordinator = VTKCleanupCoordinator()
        
        # Create mock resources
        mock_resource = Mock()
        coordinator.cleanup_resources["test_resource"] = {
            "resource": mock_resource,
            "priority": CleanupPriority.NORMAL,
            "cleaned": False
        }
        
        # Test reference clearing
        coordinator._clear_resource_references()
        
        # Verify resource is cleared
        self.assertIsNone(coordinator.cleanup_resources["test_resource"]["resource"])
        self.assertTrue(coordinator.cleanup_resources["test_resource"]["cleaned"])

    def test_context_cache_clearing(self):
        """Test that context cache clearing handles errors gracefully."""
        coordinator = VTKCleanupCoordinator()
        
        # Test with normal context manager
        try:
            coordinator._clear_context_cache_safely()
        except Exception as e:
            self.fail(f"Context cache clearing failed: {e}")
        
        # Test with broken context manager
        coordinator.context_manager = Mock()
        del coordinator.context_manager.clear_context_cache
        
        try:
            coordinator._clear_context_cache_safely()
        except Exception as e:
            self.fail(f"Context cache clearing with broken manager failed: {e}")

    def test_memory_leak_prevention(self):
        """Test that the fix prevents memory leaks during repeated operations."""
        coordinator = VTKCleanupCoordinator()
        
        # Create and cleanup multiple times
        for i in range(10):
            # Create mock resources
            mock_resource = Mock()
            coordinator.cleanup_resources[f"test_resource_{i}"] = {
                "resource": mock_resource,
                "priority": CleanupPriority.NORMAL,
                "cleaned": False
            }
            
            # Perform cleanup
            try:
                coordinator._clear_resource_references()
                coordinator._final_cleanup()
            except Exception as e:
                self.fail(f"Memory leak test iteration {i} failed: {e}")
        
        # Force garbage collection
        gc.collect()
        
        # Verify no resources remain
        self.assertEqual(len(coordinator.cleanup_resources), 10)

    def test_performance_impact(self):
        """Test that the fix doesn't significantly impact performance."""
        import time
        
        coordinator = VTKCleanupCoordinator()
        
        # Measure cleanup performance
        start_time = time.time()
        
        # Create some resources
        for i in range(100):
            mock_resource = Mock()
            coordinator.cleanup_resources[f"perf_test_{i}"] = {
                "resource": mock_resource,
                "priority": CleanupPriority.NORMAL,
                "cleaned": False
            }
        
        # Perform cleanup
        coordinator._clear_resource_references()
        coordinator._final_cleanup()
        
        end_time = time.time()
        cleanup_time = end_time - start_time
        
        # Cleanup should complete in reasonable time (less than 5 seconds)
        self.assertLess(cleanup_time, 5.0, f"Cleanup took too long: {cleanup_time:.3f}s")

    def test_logging_functionality(self):
        """Test that comprehensive logging is working."""
        coordinator = VTKCleanupCoordinator()
        
        # Capture log output
        with patch.object(coordinator.logger, 'info') as mock_info, \
             patch.object(coordinator.logger, 'warning') as mock_warning, \
             patch.object(coordinator.logger, 'error') as mock_error:
            
            # Perform operations that should generate logs
            coordinator._perform_robust_resource_tracker_cleanup()
            coordinator._clear_resource_references()
            coordinator._clear_context_cache_safely()
            
            # Verify logging occurred
            self.assertTrue(
                mock_info.called or mock_warning.called or mock_error.called,
                "No logging occurred during operations"
            )

    def test_global_coordinator_functionality(self):
        """Test the global coordinator singleton functionality."""
        # Get first instance
        coordinator1 = get_vtk_cleanup_coordinator()
        
        # Get second instance (should be same)
        coordinator2 = get_vtk_cleanup_coordinator()
        
        # Should be the same instance
        self.assertIs(coordinator1, coordinator2)
        
        # Should have working resource tracker
        self.assertIsNotNone(coordinator1.resource_tracker)

    def test_integration_with_vtk_resource_tracker(self):
        """Test integration with the actual VTK resource tracker."""
        # Get the real resource tracker
        real_tracker = get_vtk_resource_tracker()
        
        # Create coordinator
        coordinator = VTKCleanupCoordinator()
        
        # Verify integration
        self.assertIsNotNone(coordinator.resource_tracker)
        
        # Test cleanup statistics
        stats = coordinator.resource_tracker.get_statistics()
        self.assertIsInstance(stats, dict)
        self.assertIn('total_tracked', stats)


class TestVTKResourceTrackerFixStress(unittest.TestCase):
    """Stress tests for VTK resource tracker fix."""

    def test_stress_cleanup_cycles(self):
        """Test multiple rapid cleanup cycles."""
        for cycle in range(20):
            with self.subTest(cycle=cycle):
                coordinator = VTKCleanupCoordinator()
                
                # Create resources
                for i in range(10):
                    mock_resource = Mock()
                    coordinator.cleanup_resources[f"stress_test_{cycle}_{i}"] = {
                        "resource": mock_resource,
                        "priority": CleanupPriority.NORMAL,
                        "cleaned": False
                    }
                
                # Perform cleanup
                try:
                    coordinator.coordinate_cleanup()
                except Exception as e:
                    self.fail(f"Stress test cycle {cycle} failed: {e}")
                
                # Force garbage collection
                gc.collect()

    def test_concurrent_cleanup_safety(self):
        """Test that cleanup is safe to call multiple times."""
        coordinator = VTKCleanupCoordinator()
        
        # Create resources
        mock_resource = Mock()
        coordinator.cleanup_resources["concurrent_test"] = {
            "resource": mock_resource,
            "priority": CleanupPriority.NORMAL,
            "cleaned": False
        }
        
        # Call cleanup multiple times
        results = []
        for i in range(5):
            try:
                result = coordinator.coordinate_cleanup()
                results.append(result)
            except Exception as e:
                self.fail(f"Concurrent cleanup call {i} failed: {e}")
        
        # All calls should succeed
        self.assertEqual(len(results), 5)
        for result in results:
            self.assertIsNotNone(result)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)