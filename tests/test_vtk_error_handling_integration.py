"""
Integration tests for VTK Error Handling System.

This module tests the integration of the VTK error handling system with
the actual viewer components to ensure the wglMakeCurrent error is handled.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

import vtk

from src.gui.viewer_3d.viewer_widget_facade import Viewer3DWidget
from src.gui.vtk import (
    get_vtk_error_handler,
    get_vtk_context_manager,
    get_vtk_cleanup_coordinator,
    get_vtk_resource_tracker,
    get_vtk_fallback_renderer,
    generate_vtk_diagnostic_report
)


class TestVTKErrorHandlingIntegration(unittest.TestCase):
    """Integration tests for VTK error handling with viewer components."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the UI manager to avoid Qt dependencies
        with patch('src.gui.viewer_3d.viewer_widget_facade.ViewerUIManager') as mock_ui_manager:
            mock_ui_manager_instance = Mock()
            mock_ui_manager_instance.get_vtk_widget.return_value = self._create_mock_vtk_widget()
            mock_ui_manager_instance.setup_ui.return_value = None
            mock_ui_manager_instance.apply_theme.return_value = None
            mock_ui_manager_instance.update_grid_button_state.return_value = None
            mock_ui_manager_instance.update_ground_button_state.return_value = None
            mock_ui_manager_instance.reset_save_view_button.return_value = None
            mock_ui_manager.return_value = mock_ui_manager_instance

            # Create viewer widget
            self.viewer = Viewer3DWidget()

    def _create_mock_vtk_widget(self):
        """Create a mock VTK widget."""
        mock_widget = Mock()

        # Mock render window
        mock_render_window = Mock(spec=vtk.vtkRenderWindow)
        mock_render_window.GetWindowId.return_value = 12345
        mock_render_window.GetSize.return_value = (800, 600)
        mock_render_window.Render.return_value = None
        mock_render_window.Finalize.return_value = None
        mock_render_window.AddRenderer.return_value = None

        # Mock interactor
        mock_interactor = Mock(spec=vtk.vtkRenderWindowInteractor)
        mock_interactor.GetRenderWindow.return_value = mock_render_window
        mock_interactor.Initialize.return_value = None
        mock_interactor.TerminateApp.return_value = None

        # Mock renderer
        mock_renderer = Mock(spec=vtk.vtkRenderer)
        mock_renderer.GetActiveCamera.return_value = Mock(spec=vtk.vtkCamera)
        mock_renderer.ResetCamera.return_value = None
        mock_renderer.RemoveAllViewProps.return_value = None
        mock_renderer.GetActors.return_value = Mock()
        mock_renderer.GetLights.return_value = None

        mock_widget.GetRenderWindow.return_value = mock_interactor
        mock_render_window.GetInteractor.return_value = mock_interactor

        return mock_widget

    def test_viewer_initialization_with_error_handling(self):
        """Test viewer initialization with error handling integration."""
        # Check that error handling components are initialized
        self.assertIsNotNone(self.viewer.error_handler)
        self.assertIsNotNone(self.viewer.context_manager)
        self.assertIsNotNone(self.viewer.cleanup_coordinator)
        self.assertIsNotNone(self.viewer.resource_tracker)
        self.assertIsNotNone(self.viewer.fallback_renderer)

        # Check that resources are registered
        stats = self.viewer.resource_tracker.get_statistics()
        self.assertGreater(stats["total_tracked"], 0)

    def test_cleanup_with_context_loss(self):
        """Test cleanup when OpenGL context is lost."""
        # Mock context manager to simulate lost context
        with patch.object(self.viewer.context_manager, 'validate_context') as mock_validate:
            mock_validate.return_value = (False, self.viewer.context_manager.ContextState.LOST)

            # Cleanup should handle context loss gracefully
            success = self.viewer.cleanup_coordinator.coordinate_cleanup(
                render_window=self.viewer.render_window,
                renderer=self.viewer.renderer,
                interactor=self.viewer.interactor
            )

            # Should return False when context is lost
            self.assertFalse(success)

            # Should detect context loss
            self.assertTrue(self.viewer.cleanup_coordinator.was_context_lost())

    def test_rendering_with_fallback(self):
        """Test rendering with fallback when context is invalid."""
        # Mock context manager to simulate invalid context
        with patch.object(self.viewer.context_manager, 'validate_context') as mock_validate:
            mock_validate.return_value = (False, self.viewer.context_manager.ContextState.INVALID)

            # Rendering should use fallback
            success = self.viewer.fallback_renderer.render_with_fallback(self.viewer.render_window)

            # Should succeed with fallback
            self.assertTrue(success)

    def test_error_handler_integration(self):
        """Test error handler integration with viewer."""
        # Simulate a wglMakeCurrent error
        wgl_error = RuntimeError("wglMakeCurrent failed in Clean(), error: 6")

        # Error should be handled gracefully
        result = self.viewer.error_handler.handle_error(wgl_error, "cleanup")
        self.assertTrue(result)

        # Check error was logged
        stats = self.viewer.error_handler.get_error_stats()
        self.assertEqual(stats["total_errors"], 1)

    def test_resource_tracking_integration(self):
        """Test resource tracking integration."""
        # Register a mock resource
        mock_actor = Mock(spec=vtk.vtkActor)
        resource_id = self.viewer.resource_tracker.register_resource(
            mock_actor,
            self.viewer.resource_tracker.ResourceType.ACTOR,
            "test_actor"
        )

        self.assertIsNotNone(resource_id)

        # Check resource is tracked
        stats = self.viewer.resource_tracker.get_statistics()
        self.assertEqual(stats["total_tracked"], stats["total_created"])

        # Cleanup resource
        success = self.viewer.resource_tracker.cleanup_resource(resource_id)
        self.assertTrue(success)

        # Check resource is cleaned
        self.assertEqual(stats["total_cleaned"], 1)

    def test_diagnostic_integration(self):
        """Test diagnostic tools integration."""
        # Generate diagnostic report
        report = generate_vtk_diagnostic_report()

        self.assertIsInstance(report, str)
        self.assertIn("VTK DIAGNOSTIC REPORT", report)
        self.assertIn("CONTEXT DIAGNOSTICS", report)
        self.assertIn("RESOURCE DIAGNOSTICS", report)

        # Run health check
        health = self.viewer.diagnostic_tools.run_health_check()

        self.assertIn("overall_status", health)
        self.assertIn("issues", health)
        self.assertIn("warnings", health)
        self.assertIn("recommendations", health)

    def test_context_validation_integration(self):
        """Test context validation integration."""
        # Test with valid context
        is_valid, context_state = self.viewer.context_manager.validate_context(
            self.viewer.render_window, "integration_test"
        )

        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(context_state, self.viewer.context_manager.ContextState)

        # Test context safety for cleanup
        is_safe = self.viewer.context_manager.is_context_safe_for_cleanup(self.viewer.render_window)
        self.assertIsInstance(is_safe, bool)

    def test_fallback_renderer_integration(self):
        """Test fallback renderer integration."""
        # Test fallback activation
        success = self.viewer.fallback_renderer.activate_fallback(self.viewer.renderer)
        self.assertTrue(success)

        # Check fallback is active
        self.assertTrue(self.viewer.fallback_renderer.is_fallback_active())

        # Test fallback rendering
        render_success = self.viewer.fallback_renderer.render_with_fallback(self.viewer.render_window)
        self.assertTrue(render_success)

        # Test fallback deactivation
        deactivate_success = self.viewer.fallback_renderer.deactivate_fallback()
        self.assertTrue(deactivate_success)

        # Check fallback is inactive
        self.assertFalse(self.viewer.fallback_renderer.is_fallback_active())

    def test_comprehensive_error_scenario(self):
        """Test comprehensive error scenario simulation."""
        # Simulate a complete error scenario:
        # 1. Context becomes invalid
        # 2. wglMakeCurrent error occurs during cleanup
        # 3. Fallback rendering is used
        # 4. Resources are properly cleaned up

        # Step 1: Mock context as invalid
        with patch.object(self.viewer.context_manager, 'validate_context') as mock_validate:
            mock_validate.return_value = (False, self.viewer.context_manager.ContextState.LOST)

            # Step 2: Simulate cleanup with context loss
            cleanup_success = self.viewer.cleanup_coordinator.coordinate_cleanup(
                render_window=self.viewer.render_window,
                renderer=self.viewer.renderer,
                interactor=self.viewer.interactor
            )

            # Should handle context loss gracefully
            self.assertFalse(cleanup_success)

            # Step 3: Test fallback rendering
            fallback_success = self.viewer.fallback_renderer.render_with_fallback(self.viewer.render_window)
            self.assertTrue(fallback_success)

            # Step 4: Test resource cleanup
            cleanup_stats = self.viewer.resource_tracker.cleanup_all_resources()
            self.assertIn("success", cleanup_stats)
            self.assertIn("errors", cleanup_stats)

    def test_memory_leak_prevention(self):
        """Test memory leak prevention."""
        # Register multiple resources
        resources = []
        for i in range(10):
            mock_resource = Mock(spec=vtk.vtkActor)
            resource_id = self.viewer.resource_tracker.register_resource(
                mock_resource,
                self.viewer.resource_tracker.ResourceType.ACTOR,
                f"leak_test_actor_{i}"
            )
            resources.append(resource_id)

        # Check resources are tracked
        stats = self.viewer.resource_tracker.get_statistics()
        self.assertEqual(stats["total_tracked"], 10)

        # Cleanup all resources
        cleanup_stats = self.viewer.resource_tracker.cleanup_all_resources()

        # Check cleanup results
        self.assertEqual(cleanup_stats["total"], 10)
        self.assertEqual(cleanup_stats["success"], 10)
        self.assertEqual(cleanup_stats["errors"], 0)

        # Check no leaks detected
        leaked = self.viewer.resource_tracker.find_leaked_resources()
        self.assertEqual(len(leaked), 0)

    def test_error_recovery_mechanisms(self):
        """Test error recovery mechanisms."""
        # Test error handler recovery strategies
        error_info = {
            "error_text": "wglMakeCurrent failed in Clean(), error: 6",
            "error_code": "cleanup_error",
            "severity": "low"
        }

        # Test cleanup error recovery
        recovery_success = self.viewer.error_handler.recovery_strategies[
            self.viewer.error_handler.VTKErrorCode.CLEANUP_ERROR
        ](error_info)

        self.assertTrue(recovery_success)

        # Test context lost recovery
        context_error_info = {
            "error_text": "OpenGL context lost",
            "error_code": "context_lost",
            "severity": "high"
        }

        context_recovery_success = self.viewer.error_handler.recovery_strategies[
            self.viewer.error_handler.VTKErrorCode.CONTEXT_LOST
        ](context_error_info)

        self.assertTrue(context_recovery_success)


if __name__ == "__main__":
    # Run integration tests
    unittest.main(verbosity=2)