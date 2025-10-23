"""
Tests for VTK Error Handling System.

This module tests the enhanced VTK error handling system that gracefully
handles OpenGL context loss and prevents the wglMakeCurrent error.
"""

import unittest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import pytest

import vtk

from src.gui.vtk import (
    VTKErrorHandler,
    VTKContextManager,
    VTKCleanupCoordinator,
    VTKResourceTracker,
    VTKFallbackRenderer,
    VTKDiagnosticTools,
    get_vtk_error_handler,
    get_vtk_context_manager,
    coordinate_vtk_cleanup,
    register_vtk_resource,
    generate_vtk_diagnostic_report,
    run_vtk_health_check,
    VTKErrorCode,
    VTKErrorSeverity,
    ContextState,
    CleanupPhase,
    ResourceType,
    FallbackMode
)


class TestVTKErrorHandler(unittest.TestCase):
    """Test VTK Error Handler functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = VTKErrorHandler()

    def test_error_classification(self):
        """Test error classification."""
        # Test wglMakeCurrent error classification
        wgl_error = "wglMakeCurrent failed in Clean(), error: 6"
        error_code = self.error_handler._classify_error(wgl_error)
        self.assertEqual(error_code, VTKErrorCode.CLEANUP_ERROR)

        # Test invalid handle error
        handle_error = "invalid handle error: 6"
        error_code = self.error_handler._classify_error(handle_error)
        self.assertEqual(error_code, VTKErrorCode.INVALID_HANDLE)

        # Test context lost error
        context_error = "OpenGL context lost"
        error_code = self.error_handler._classify_error(context_error)
        self.assertEqual(error_code, VTKErrorCode.CONTEXT_LOST)

    def test_error_severity(self):
        """Test error severity determination."""
        # Test cleanup error severity (should be low)
        severity = self.error_handler._determine_severity(VTKErrorCode.CLEANUP_ERROR, "cleanup error")
        self.assertEqual(severity, VTKErrorSeverity.LOW)

        # Test memory error severity (should be critical)
        severity = self.error_handler._determine_severity(VTKErrorCode.MEMORY_ERROR, "memory error")
        self.assertEqual(severity, VTKErrorSeverity.CRITICAL)

    def test_error_handling(self):
        """Test error handling."""
        test_error = RuntimeError("wglMakeCurrent failed in Clean(), error: 6")

        # Should handle gracefully
        result = self.error_handler.handle_error(test_error, "cleanup")
        self.assertTrue(result)

        # Check error was counted
        stats = self.error_handler.get_error_stats()
        self.assertEqual(stats["total_errors"], 1)
        self.assertEqual(stats["error_counts"]["cleanup_error"], 1)

    def test_error_callback_registration(self):
        """Test error callback registration."""
        callback_called = False
        callback_error = None

        def test_callback(error_info):
            nonlocal callback_called, callback_error
            callback_called = True
            callback_error = error_info

        self.error_handler.register_error_callback(VTKErrorCode.CLEANUP_ERROR, test_callback)

        test_error = RuntimeError("wglMakeCurrent failed in Clean(), error: 6")
        self.error_handler.handle_error(test_error, "cleanup")

        self.assertTrue(callback_called)
        self.assertIsNotNone(callback_error)
        self.assertEqual(callback_error["error_code"], "cleanup_error")


class TestVTKContextManager(unittest.TestCase):
    """Test VTK Context Manager functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.context_manager = VTKContextManager()

    def test_context_validation(self):
        """Test context validation."""
        # Create a mock render window
        render_window = Mock(spec=vtk.vtkRenderWindow)
        render_window.GetWindowId.return_value = 12345
        render_window.GetGenericDisplayId.return_value = 1

        is_valid, context_state = self.context_manager.validate_context(render_window, "test")

        self.assertTrue(is_valid)
        self.assertEqual(context_state, ContextState.VALID)

    def test_invalid_context_detection(self):
        """Test invalid context detection."""
        # Create a mock render window with invalid handle
        render_window = Mock(spec=vtk.vtkRenderWindow)
        render_window.GetWindowId.return_value = 0  # Invalid window ID

        is_valid, context_state = self.context_manager.validate_context(render_window, "test")

        self.assertFalse(is_valid)
        self.assertEqual(context_state, ContextState.LOST)

    def test_context_safe_for_cleanup(self):
        """Test context safety for cleanup."""
        # Mock render window with lost context
        render_window = Mock(spec=vtk.vtkRenderWindow)
        render_window.GetWindowId.return_value = 0

        is_safe = self.context_manager.is_context_safe_for_cleanup(render_window)
        self.assertFalse(is_safe)

    def test_context_info(self):
        """Test context information retrieval."""
        render_window = Mock(spec=vtk.vtkRenderWindow)
        render_window.GetWindowId.return_value = 12345
        render_window.GetSize.return_value = (800, 600)

        info = self.context_manager.get_context_info(render_window)

        self.assertEqual(info["window_id"], 12345)
        self.assertEqual(info["size"], (800, 600))
        self.assertTrue(info["validation_enabled"])


class TestVTKCleanupCoordinator(unittest.TestCase):
    """Test VTK Cleanup Coordinator functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.cleanup_coordinator = VTKCleanupCoordinator()

    def test_resource_registration(self):
        """Test resource registration."""
        mock_resource = Mock()
        resource_id = self.cleanup_coordinator.register_resource(
            "test_resource",
            mock_resource,
            CleanupPriority.NORMAL
        )

        self.assertIsNotNone(resource_id)
        self.assertIn("test_resource", self.cleanup_coordinator.cleanup_resources)

    def test_cleanup_coordination(self):
        """Test cleanup coordination."""
        # Mock VTK components
        render_window = Mock(spec=vtk.vtkRenderWindow)
        renderer = Mock(spec=vtk.vtkRenderer)
        interactor = Mock(spec=vtk.vtkRenderWindowInteractor)

        # Mock context manager to return valid context
        with patch.object(self.cleanup_coordinator.context_manager, 'validate_context') as mock_validate:
            mock_validate.return_value = (True, ContextState.VALID)

            success = self.cleanup_coordinator.coordinate_cleanup(
                render_window=render_window,
                renderer=renderer,
                interactor=interactor
            )

            self.assertTrue(success)

    def test_context_lost_handling(self):
        """Test context lost handling during cleanup."""
        # Mock VTK components
        render_window = Mock(spec=vtk.vtkRenderWindow)
        renderer = Mock(spec=vtk.vtkRenderer)
        interactor = Mock(spec=vtk.vtkRenderWindowInteractor)

        # Mock context manager to return lost context
        with patch.object(self.cleanup_coordinator.context_manager, 'validate_context') as mock_validate:
            mock_validate.return_value = (False, ContextState.LOST)

            success = self.cleanup_coordinator.coordinate_cleanup(
                render_window=render_window,
                renderer=renderer,
                interactor=interactor
            )

            # Should return False when context is lost
            self.assertFalse(success)
            self.assertTrue(self.cleanup_coordinator.was_context_lost())


class TestVTKResourceTracker(unittest.TestCase):
    """Test VTK Resource Tracker functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.resource_tracker = VTKResourceTracker()

    def test_resource_registration(self):
        """Test resource registration."""
        mock_resource = Mock()
        resource_id = self.resource_tracker.register_resource(
            mock_resource,
            ResourceType.ACTOR,
            "test_actor"
        )

        self.assertIsNotNone(resource_id)
        self.assertIn(resource_id, self.resource_tracker.resources)

    def test_resource_cleanup(self):
        """Test resource cleanup."""
        mock_resource = Mock()
        resource_id = self.resource_tracker.register_resource(
            mock_resource,
            ResourceType.ACTOR,
            "test_actor"
        )

        success = self.resource_tracker.cleanup_resource(resource_id)
        self.assertTrue(success)

        # Resource should be marked as cleaned
        resource_info = self.resource_tracker.get_resource_info(resource_id)
        self.assertEqual(resource_info["state"], "cleaned")

    def test_resource_leak_detection(self):
        """Test resource leak detection."""
        # Register a resource
        mock_resource = Mock()
        resource_id = self.resource_tracker.register_resource(
            mock_resource,
            ResourceType.ACTOR,
            "test_actor"
        )

        # Delete the mock resource to simulate a leak
        del mock_resource

        # Force garbage collection
        import gc
        gc.collect()

        # Check for leaks
        leaked = self.resource_tracker.find_leaked_resources()
        self.assertEqual(len(leaked), 1)
        self.assertEqual(leaked[0]["resource_id"], resource_id)

    def test_statistics(self):
        """Test statistics collection."""
        # Register some resources
        for i in range(5):
            mock_resource = Mock()
            self.resource_tracker.register_resource(
                mock_resource,
                ResourceType.ACTOR,
                f"test_actor_{i}"
            )

        stats = self.resource_tracker.get_statistics()

        self.assertEqual(stats["total_tracked"], 5)
        self.assertEqual(stats["total_created"], 5)
        self.assertEqual(stats["by_type"]["actor"], 5)


class TestVTKFallbackRenderer(unittest.TestCase):
    """Test VTK Fallback Renderer functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.fallback_renderer = VTKFallbackRenderer()

    def test_fallback_activation(self):
        """Test fallback activation."""
        renderer = Mock(spec=vtk.vtkRenderer)

        success = self.fallback_renderer.activate_fallback(renderer)
        self.assertTrue(success)
        self.assertTrue(self.fallback_renderer.is_fallback_active())

    def test_fallback_deactivation(self):
        """Test fallback deactivation."""
        renderer = Mock(spec=vtk.vtkRenderer)

        # Activate first
        self.fallback_renderer.activate_fallback(renderer)
        self.assertTrue(self.fallback_renderer.is_fallback_active())

        # Then deactivate
        success = self.fallback_renderer.deactivate_fallback()
        self.assertTrue(success)
        self.assertFalse(self.fallback_renderer.is_fallback_active())

    def test_fallback_mode_selection(self):
        """Test fallback mode selection."""
        mode = self.fallback_renderer._select_best_fallback_mode()
        self.assertIsInstance(mode, FallbackMode)

    def test_fallback_rendering(self):
        """Test fallback rendering."""
        render_window = Mock(spec=vtk.vtkRenderWindow)

        success = self.fallback_renderer.render_with_fallback(render_window)
        # Should succeed even without proper setup
        self.assertTrue(success)


class TestVTKDiagnosticTools(unittest.TestCase):
    """Test VTK Diagnostic Tools functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.diagnostic_tools = VTKDiagnosticTools()

    def test_comprehensive_diagnostics(self):
        """Test comprehensive diagnostics."""
        diagnostics = self.diagnostic_tools.get_comprehensive_diagnostics()

        self.assertIn("timestamp", diagnostics)
        self.assertIn("platform", diagnostics)
        self.assertIn("vtk_version", diagnostics)
        self.assertIn("context_diagnostics", diagnostics)
        self.assertIn("resource_diagnostics", diagnostics)
        self.assertIn("error_diagnostics", diagnostics)

    def test_context_loss_diagnosis(self):
        """Test context loss diagnosis."""
        render_window = Mock(spec=vtk.vtkRenderWindow)
        render_window.GetWindowId.return_value = 0  # Invalid

        diagnosis = self.diagnostic_tools.diagnose_context_loss(render_window)

        self.assertTrue(diagnosis["context_loss_detected"])
        self.assertEqual(diagnosis["context_state"], "lost")
        self.assertIn("potential_causes", diagnosis)
        self.assertIn("recommendations", diagnosis)

    def test_memory_diagnosis(self):
        """Test memory issue diagnosis."""
        diagnosis = self.diagnostic_tools.diagnose_memory_issues()

        self.assertIn("memory_issues_detected", diagnosis)
        self.assertIn("resource_leaks", diagnosis)
        self.assertIn("recommendations", diagnosis)

    def test_performance_diagnosis(self):
        """Test performance issue diagnosis."""
        diagnosis = self.diagnostic_tools.diagnose_performance_issues()

        self.assertIn("performance_issues_detected", diagnosis)
        self.assertIn("recommendations", diagnosis)

    def test_health_check(self):
        """Test health check."""
        health = self.diagnostic_tools.run_health_check()

        self.assertIn("overall_status", health)
        self.assertIn("issues", health)
        self.assertIn("warnings", health)
        self.assertIn("recommendations", health)


class TestVTKErrorHandlingIntegration(unittest.TestCase):
    """Test integration of VTK error handling components."""

    def setUp(self):
        """Set up test fixtures."""
        # Clear any existing global instances
        from src.gui.vtk import (
            _vtk_error_handler,
            _vtk_context_manager,
            _vtk_cleanup_coordinator,
            _vtk_resource_tracker,
            _vtk_fallback_renderer,
            _vtk_diagnostic_tools
        )

        _vtk_error_handler = None
        _vtk_context_manager = None
        _vtk_cleanup_coordinator = None
        _vtk_resource_tracker = None
        _vtk_fallback_renderer = None
        _vtk_diagnostic_tools = None

    def test_global_instances(self):
        """Test global instance management."""
        # Test error handler
        handler1 = get_vtk_error_handler()
        handler2 = get_vtk_error_handler()
        self.assertIs(handler1, handler2)

        # Test context manager
        context1 = get_vtk_context_manager()
        context2 = get_vtk_context_manager()
        self.assertIs(context1, context2)

        # Test cleanup coordinator
        cleanup1 = get_vtk_cleanup_coordinator()
        cleanup2 = get_vtk_cleanup_coordinator()
        self.assertIs(cleanup1, cleanup2)

        # Test resource tracker
        tracker1 = get_vtk_resource_tracker()
        tracker2 = get_vtk_resource_tracker()
        self.assertIs(tracker1, tracker2)

        # Test fallback renderer
        fallback1 = get_vtk_fallback_renderer()
        fallback2 = get_vtk_fallback_renderer()
        self.assertIs(fallback1, fallback2)

        # Test diagnostic tools
        diag1 = get_vtk_diagnostic_tools()
        diag2 = get_vtk_diagnostic_tools()
        self.assertIs(diag1, diag2)

    def test_convenience_functions(self):
        """Test convenience functions."""
        # Test error handling
        test_error = RuntimeError("test error")
        result = self.error_handler.handle_error(test_error, "test")
        self.assertTrue(result)

        # Test context validation
        render_window = Mock(spec=vtk.vtkRenderWindow)
        is_valid, state = validate_vtk_context(render_window, "test")
        self.assertIsInstance(is_valid, bool)
        self.assertIsInstance(state, ContextState)

        # Test cleanup coordination
        success = coordinate_vtk_cleanup(render_window)
        self.assertIsInstance(success, bool)

        # Test resource registration
        mock_resource = Mock()
        resource_id = register_vtk_resource(mock_resource, ResourceType.ACTOR, "test")
        self.assertIsNotNone(resource_id)

        # Test diagnostic report generation
        report = generate_vtk_diagnostic_report()
        self.assertIsInstance(report, str)
        self.assertIn("VTK DIAGNOSTIC REPORT", report)

        # Test health check
        health = run_vtk_health_check()
        self.assertIn("overall_status", health)


class TestVTKErrorHandlingEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.error_handler = VTKErrorHandler()
        self.context_manager = VTKContextManager()
        self.cleanup_coordinator = VTKCleanupCoordinator()
        self.resource_tracker = VTKResourceTracker()

    def test_none_resource_handling(self):
        """Test handling of None resources."""
        # Should handle None render window gracefully
        is_valid, state = self.context_manager.validate_context(None, "test")
        self.assertFalse(is_valid)
        self.assertEqual(state, ContextState.INVALID)

        # Should handle None in cleanup
        success = self.cleanup_coordinator.coordinate_cleanup(None, None, None)
        self.assertTrue(success)  # Should not crash

    def test_exception_during_error_handling(self):
        """Test exception handling during error processing."""
        # This should not crash even if error handler has issues
        try:
            # Create an error that might cause issues in the handler
            problematic_error = Exception("problematic error")
            result = self.error_handler.handle_error(problematic_error, "test")
            # Should still return a boolean
            self.assertIsInstance(result, bool)
        except Exception as e:
            self.fail(f"Error handler should not raise exceptions: {e}")

    def test_resource_cleanup_with_exceptions(self):
        """Test resource cleanup when resources throw exceptions."""
        # Register a resource that throws exceptions during cleanup
        mock_resource = Mock()
        mock_resource.Delete.side_effect = Exception("cleanup error")

        resource_id = self.resource_tracker.register_resource(
            mock_resource,
            ResourceType.ACTOR,
            "problematic_actor"
        )

        # Cleanup should handle the exception gracefully
        success = self.resource_tracker.cleanup_resource(resource_id)
        self.assertTrue(success)  # Should still succeed

    def test_diagnostic_tools_with_exceptions(self):
        """Test diagnostic tools when components throw exceptions."""
        # Mock components to throw exceptions
        with patch.object(self.diagnostic_tools.context_manager, 'get_diagnostic_info') as mock_context:
            mock_context.side_effect = Exception("context error")

            # Should handle exceptions gracefully
            diagnostics = self.diagnostic_tools.get_comprehensive_diagnostics()
            self.assertIn("error", diagnostics)


if __name__ == "__main__":
    # Create test suite
    unittest.main(verbosity=2)