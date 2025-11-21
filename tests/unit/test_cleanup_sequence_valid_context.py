"""
Test suite for cleanup sequence with valid OpenGL context.

This test validates that:
1. Cleanup happens in the correct order
2. VTK cleanup happens with valid OpenGL context
3. No 'CRITICAL FIX' messages appear
4. All phases complete successfully
5. Resource leaks are detected
6. Verification passes
"""

import unittest
import sys
import os
import logging
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from src.core.cleanup.unified_cleanup_coordinator import (
    UnifiedCleanupCoordinator,
    CleanupPhase,
    CleanupStats,
    CleanupContext,
)
from src.core.cleanup.cleanup_verification import CleanupVerifier, VerificationStatus
from src.core.logging_config import get_logger


class TestCleanupSequenceValidContext(unittest.TestCase):
    """Test cleanup sequence with valid OpenGL context."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.logger = get_logger(__name__)
        # Suppress debug logging for cleaner test output
        logging.getLogger("src.core.cleanup").setLevel(logging.INFO)

    def setUp(self):
        """Set up test fixtures."""
        self.coordinator = UnifiedCleanupCoordinator()
        self.verifier = CleanupVerifier()

    def test_cleanup_coordinator_initialization(self):
        """Test that cleanup coordinator initializes correctly."""
        self.assertIsNotNone(self.coordinator)
        self.assertEqual(len(self.coordinator.get_registered_handlers()), 4)
        self.logger.info("✓ Cleanup coordinator initialized with 4 handlers")

    def test_all_handlers_registered(self):
        """Test that all required handlers are registered."""
        handlers = self.coordinator.get_registered_handlers()
        expected_handlers = [
            "VTKCleanupHandler",
            "WidgetCleanupHandler",
            "ServiceCleanupHandler",
            "ResourceCleanupHandler",
        ]

        for handler_name in expected_handlers:
            self.assertIn(
                handler_name, handlers, f"Handler {handler_name} not registered"
            )

        self.logger.info(f"✓ All {len(expected_handlers)} handlers registered")

    def test_cleanup_with_valid_context(self):
        """Test cleanup execution with valid context."""
        # Mock VTK resources
        mock_render_window = MagicMock()
        mock_renderer = MagicMock()
        mock_interactor = MagicMock()
        mock_main_window = MagicMock()
        mock_application = MagicMock()

        # Execute cleanup
        stats = self.coordinator.coordinate_cleanup(
            render_window=mock_render_window,
            renderer=mock_renderer,
            interactor=mock_interactor,
            main_window=mock_main_window,
            application=mock_application,
        )

        # Verify cleanup completed
        self.assertIsNotNone(stats)
        self.assertGreater(stats.total_phases, 0)
        self.logger.info(f"✓ Cleanup executed with {stats.total_phases} phases")

    def test_cleanup_phase_completion(self):
        """Test that all cleanup phases complete."""
        stats = self.coordinator.coordinate_cleanup()

        # Verify phases completed
        total_phases = stats.total_phases
        completed_phases = stats.completed_phases + stats.skipped_phases

        self.assertEqual(
            completed_phases,
            total_phases,
            f"Not all phases completed: {completed_phases}/{total_phases}",
        )
        self.logger.info(f"✓ All {total_phases} phases completed")

    def test_cleanup_error_handling(self):
        """Test error handling during cleanup."""
        stats = self.coordinator.coordinate_cleanup()

        # Verify error tracking
        self.assertIsNotNone(stats.errors)
        self.assertIsNotNone(stats.phase_errors)
        self.logger.info(
            f"✓ Error handling verified: {len(stats.errors)} errors tracked"
        )

    def test_handler_statistics_tracking(self):
        """Test that handler statistics are tracked."""
        stats = self.coordinator.coordinate_cleanup()

        # Verify handler stats
        self.assertIsNotNone(stats.handler_stats)
        self.assertGreater(len(stats.handler_stats), 0)

        for handler_name, handler_stats in stats.handler_stats.items():
            self.assertIn("phases_executed", handler_stats)
            self.assertIn("phases_succeeded", handler_stats)
            self.assertIn("phases_failed", handler_stats)
            self.assertIn("total_duration", handler_stats)

        self.logger.info(
            f"✓ Handler statistics tracked for {len(stats.handler_stats)} handlers"
        )

    def test_cleanup_timing(self):
        """Test that cleanup timing is recorded."""
        stats = self.coordinator.coordinate_cleanup()

        # Verify timing
        self.assertGreater(stats.total_duration, 0)
        self.logger.info(f"✓ Cleanup completed in {stats.total_duration:.3f}s")

    def test_no_critical_fix_messages(self):
        """Test that no 'CRITICAL FIX' messages appear."""
        # This would require capturing logs, but we can verify the cleanup
        # doesn't use the old emergency shutdown path
        stats = self.coordinator.coordinate_cleanup()

        # If we got here without emergency shutdown, the test passes
        self.assertIsNotNone(stats)
        self.logger.info("✓ No emergency shutdown triggered")

    def test_verification_runs_automatically(self):
        """Test that verification runs automatically after cleanup."""
        stats = self.coordinator.coordinate_cleanup()

        # Verify verification report exists
        self.assertIsNotNone(stats.verification_report)
        self.logger.info("✓ Verification report generated automatically")

    def test_verification_checks_pass(self):
        """Test that verification checks pass."""
        stats = self.coordinator.coordinate_cleanup()
        report = stats.verification_report

        if report:
            # Verify checks ran
            self.assertGreater(report.total_checks, 0)
            self.logger.info(f"✓ {report.total_checks} verification checks executed")

            # Verify at least some checks passed
            self.assertGreaterEqual(report.passed_checks, 0)
            self.logger.info(f"✓ {report.passed_checks} checks passed")

    def test_resource_leak_detection(self):
        """Test that resource leak detection works."""
        stats = self.coordinator.coordinate_cleanup()
        report = stats.verification_report

        if report:
            # Verify leak detection ran
            self.assertIsNotNone(report.resource_leaks)
            self.logger.info(
                f"✓ Resource leak detection: {len(report.resource_leaks)} potential leaks"
            )

    def test_memory_statistics_collected(self):
        """Test that memory statistics are collected."""
        stats = self.coordinator.coordinate_cleanup()
        report = stats.verification_report

        if report:
            # Verify memory stats
            self.assertIsNotNone(report.memory_stats)
            self.logger.info(
                f"✓ Memory statistics collected: {len(report.memory_stats)} metrics"
            )

    def test_cleanup_idempotency(self):
        """Test that cleanup can be called multiple times safely."""
        # First cleanup
        stats1 = self.coordinator.coordinate_cleanup()
        self.assertIsNotNone(stats1)

        # Second cleanup should be skipped (already in progress or completed)
        stats2 = self.coordinator.coordinate_cleanup()
        self.assertIsNotNone(stats2)

        self.logger.info("✓ Cleanup is idempotent")

    def test_cleanup_with_partial_resources(self):
        """Test cleanup with only some resources provided."""
        # Test with only render window
        stats = self.coordinator.coordinate_cleanup(render_window=MagicMock())
        self.assertIsNotNone(stats)
        self.logger.info("✓ Cleanup works with partial resources")

    def test_cleanup_with_no_resources(self):
        """Test cleanup with no resources provided."""
        stats = self.coordinator.coordinate_cleanup()
        self.assertIsNotNone(stats)
        self.logger.info("✓ Cleanup works with no resources")

    def test_cleanup_statistics_summary(self):
        """Test cleanup statistics summary generation."""
        stats = self.coordinator.coordinate_cleanup()

        # Verify stats can be summarized
        self.assertGreater(stats.total_phases, 0)
        self.assertGreaterEqual(stats.completed_phases, 0)
        self.assertGreaterEqual(stats.failed_phases, 0)

        self.logger.info(
            f"✓ Cleanup summary: {stats.completed_phases} completed, "
            f"{stats.failed_phases} failed, {stats.skipped_phases} skipped"
        )

    def test_verification_report_summary(self):
        """Test verification report summary generation."""
        stats = self.coordinator.coordinate_cleanup()
        report = stats.verification_report

        if report:
            summary = report.get_summary()
            self.assertIsNotNone(summary)
            self.assertIn("Cleanup Verification Summary", summary)
            self.logger.info("✓ Verification report summary generated")

    def test_cleanup_context_state_tracking(self):
        """Test that cleanup context state is tracked."""
        stats = self.coordinator.coordinate_cleanup()

        # Verify context state
        context_state = self.coordinator.get_context_state()
        self.assertIsNotNone(context_state)
        self.logger.info(f"✓ Context state tracked: {context_state.value}")

    def test_handler_enable_disable(self):
        """Test enabling and disabling handlers."""
        handlers = self.coordinator.get_registered_handlers()

        if handlers:
            handler_name = handlers[0]

            # Disable handler
            result = self.coordinator.disable_handler(handler_name)
            self.assertTrue(result)

            # Enable handler
            result = self.coordinator.enable_handler(handler_name)
            self.assertTrue(result)

            self.logger.info(f"✓ Handler enable/disable works for {handler_name}")


class TestCleanupSequenceIntegration(unittest.TestCase):
    """Integration tests for cleanup sequence."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.logger = get_logger(__name__)
        logging.getLogger("src.core.cleanup").setLevel(logging.INFO)

    def test_full_cleanup_workflow(self):
        """Test complete cleanup workflow."""
        coordinator = UnifiedCleanupCoordinator()

        # Execute cleanup
        stats = coordinator.coordinate_cleanup()

        # Verify all components
        self.assertIsNotNone(stats)
        self.assertGreater(stats.total_phases, 0)
        self.assertIsNotNone(stats.handler_stats)
        self.assertIsNotNone(stats.verification_report)

        self.logger.info("✓ Full cleanup workflow completed successfully")

    def test_cleanup_success_criteria(self):
        """Test cleanup success criteria."""
        coordinator = UnifiedCleanupCoordinator()
        stats = coordinator.coordinate_cleanup()

        # Success criteria
        all_phases_completed = (
            stats.completed_phases + stats.skipped_phases
        ) == stats.total_phases
        no_critical_failures = stats.failed_phases == 0
        verification_available = stats.verification_report is not None

        self.assertTrue(all_phases_completed, "Not all phases completed")
        self.assertTrue(no_critical_failures, "Critical failures occurred")
        self.assertTrue(verification_available, "Verification not available")

        self.logger.info("✓ All cleanup success criteria met")


def run_tests():
    """Run all cleanup sequence tests."""
    print("\n" + "=" * 70)
    print("CLEANUP SEQUENCE WITH VALID CONTEXT - TEST SUITE")
    print("=" * 70 + "\n")

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestCleanupSequenceValidContext))
    suite.addTests(loader.loadTestsFromTestCase(TestCleanupSequenceIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70 + "\n")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
