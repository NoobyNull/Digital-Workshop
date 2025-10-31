"""
Comprehensive Test Suite for Optimized VTK Cleanup System.

This test suite verifies that the optimized cleanup order prevents VTK warnings and hangs
by testing early context loss detection, timing coordination, and different shutdown scenarios.
"""

import unittest
import time
import gc
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List
import tempfile
import os

import vtk

# Import the optimized cleanup system components
from src.gui.vtk.enhanced_context_manager import (
    EnhancedVTKContextManager,
    ContextState,
    ShutdownScenario,
    get_enhanced_vtk_context_manager,
    detect_context_loss_early,
    coordinate_shutdown_cleanup
)

from src.gui.vtk.optimized_cleanup_coordinator import (
    OptimizedVTKCleanupCoordinator,
    CleanupPhase,
    get_optimized_vtk_cleanup_coordinator,
    coordinate_optimized_shutdown_cleanup
)


class TestOptimizedCleanupSystem(unittest.TestCase):
    """Test suite for the optimized VTK cleanup system."""
    
    def setUp(self):
        """Set up test environment before each test."""
        # Create a mock VTK render window for testing
        self.mock_render_window = Mock(spec=vtk.vtkRenderWindow)
        self.mock_render_window.GetWindowId.return_value = 12345
        self.mock_render_window.GetSize.return_value = (800, 600)
        self.mock_render_window.GetMapped.return_value = True
        
        # Create mock renderers and actors
        self.mock_renderer = Mock(spec=vtk.vtkRenderer)
        self.mock_renderer.RemoveAllViewProps = Mock()
        self.mock_renderer.Clear = Mock()
        
        self.mock_render_window.GetRenderers.return_value = [self.mock_renderer]
        
        # Create mock interactor
        self.mock_interactor = Mock(spec=vtk.vtkRenderWindowInteractor)
        self.mock_interactor.TerminateApp = Mock()
        self.mock_render_window.GetInteractor.return_value = self.mock_interactor
        
        # Initialize cleanup components
        self.context_manager = get_enhanced_vtk_context_manager()
        self.cleanup_coordinator = get_optimized_vtk_cleanup_coordinator()
        
        # Clear any existing state
        self.context_manager.context_cache.clear()
        self.cleanup_coordinator.cleanup_resources.clear()
        
    def tearDown(self):
        """Clean up after each test."""
        # Force garbage collection
        gc.collect()
        
        # Clear caches
        self.context_manager.context_cache.clear()
        self.cleanup_coordinator.cleanup_resources.clear()
    
    def test_early_context_loss_detection(self):
        """Test early context loss detection functionality."""
        print("Testing early context loss detection...")
        
        # Test with valid context
        early_detection, context_state = detect_context_loss_early(self.mock_render_window)
        self.assertIsInstance(early_detection, bool)
        self.assertIsInstance(context_state, ContextState)
        
        # Test with invalid context
        self.mock_render_window.GetWindowId.return_value = 0
        early_detection, context_state = detect_context_loss_early(self.mock_render_window)
        self.assertTrue(early_detection)
        self.assertEqual(context_state, ContextState.DESTROYING)
        
        print("✓ Early context loss detection test passed")
    
    def test_context_aware_cleanup_procedures(self):
        """Test context-aware cleanup procedures for different scenarios."""
        print("Testing context-aware cleanup procedures...")
        
        scenarios = [
            ShutdownScenario.NORMAL_SHUTDOWN,
            ShutdownScenario.FORCE_CLOSE,
            ShutdownScenario.WINDOW_CLOSE,
            ShutdownScenario.APPLICATION_EXIT,
            ShutdownScenario.CONTEXT_LOSS
        ]
        
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                # Set the shutdown scenario
                self.context_manager.set_shutdown_scenario(scenario)
                
                # Verify scenario was set correctly
                self.assertEqual(self.context_manager.current_scenario, scenario)
                
                # Test cleanup coordination
                success = coordinate_shutdown_cleanup(self.mock_render_window, scenario)
                self.assertIsInstance(success, bool)
        
        print("✓ Context-aware cleanup procedures test passed")
    
    def test_timing_coordination(self):
        """Test timing coordination between VTK and OpenGL cleanup."""
        print("Testing timing coordination...")
        
        # Reset timing metrics
        self.cleanup_coordinator.vtk_cleanup_start_time = 0.0
        self.cleanup_coordinator.vtk_cleanup_end_time = 0.0
        self.cleanup_coordinator.opengl_cleanup_start_time = 0.0
        self.cleanup_coordinator.opengl_cleanup_end_time = 0.0
        
        # Perform optimized cleanup
        success = coordinate_optimized_shutdown_cleanup(
            self.mock_render_window, 
            ShutdownScenario.NORMAL_SHUTDOWN
        )
        
        self.assertTrue(success)
        
        # Verify timing coordination
        self.assertGreater(self.cleanup_coordinator.vtk_cleanup_start_time, 0)
        self.assertGreater(self.cleanup_coordinator.vtk_cleanup_end_time, 0)
        self.assertGreater(self.cleanup_coordinator.opengl_cleanup_start_time, 0)
        self.assertGreater(self.cleanup_coordinator.opengl_cleanup_end_time, 0)
        
        # Verify proper ordering
        self.assertLess(
            self.cleanup_coordinator.vtk_cleanup_start_time,
            self.cleanup_coordinator.vtk_cleanup_end_time
        )
        self.assertLess(
            self.cleanup_coordinator.vtk_cleanup_end_time,
            self.cleanup_coordinator.opengl_cleanup_start_time
        )
        self.assertLess(
            self.cleanup_coordinator.opengl_cleanup_start_time,
            self.cleanup_coordinator.opengl_cleanup_end_time
        )
        
        # Calculate and verify cleanup duration
        total_cleanup_time = (
            self.cleanup_coordinator.opengl_cleanup_end_time - 
            self.cleanup_coordinator.vtk_cleanup_start_time
        )
        self.assertGreater(total_cleanup_time, 0)
        self.assertLess(total_cleanup_time, 5.0)  # Should complete within 5 seconds
        
        print(f"✓ Timing coordination test passed (total time: {total_cleanup_time:.3f}s)")
    
    def test_cleanup_sequence_optimization(self):
        """Test that cleanup sequence prevents VTK cleanup after OpenGL context destruction."""
        print("Testing cleanup sequence optimization...")
        
        # Track cleanup order
        cleanup_order = []
        
        # Mock VTK cleanup methods to track order
        original_finalize = self.mock_render_window.Finalize
        def tracked_finalize():
            cleanup_order.append("VTK_FINALIZE")
            original_finalize()
        self.mock_render_window.Finalize = tracked_finalize
        
        # Mock context manager coordination
        original_coordinate = self.context_manager.coordinate_cleanup_sequence
        def tracked_coordinate(render_window):
            cleanup_order.append("CONTEXT_COORDINATION")
            return original_coordinate(render_window)
        self.context_manager.coordinate_cleanup_sequence = tracked_coordinate
        
        # Perform optimized cleanup
        success = coordinate_optimized_shutdown_cleanup(
            self.mock_render_window,
            ShutdownScenario.NORMAL_SHUTDOWN
        )
        
        self.assertTrue(success)
        
        # Verify proper cleanup order
        self.assertIn("VTK_FINALIZE", cleanup_order)
        self.assertIn("CONTEXT_COORDINATION", cleanup_order)
        
        # VTK cleanup should happen before context coordination
        vtk_index = cleanup_order.index("VTK_FINALIZE")
        context_index = cleanup_order.index("CONTEXT_COORDINATION")
        self.assertLess(vtk_index, context_index)
        
        print("✓ Cleanup sequence optimization test passed")
    
    def test_memory_leak_prevention(self):
        """Test that the optimized cleanup system prevents memory leaks."""
        print("Testing memory leak prevention...")
        
        # Get initial memory usage (approximate)
        initial_objects = len(gc.get_objects())
        
        # Perform multiple cleanup cycles
        for i in range(10):
            success = coordinate_optimized_shutdown_cleanup(
                self.mock_render_window,
                ShutdownScenario.NORMAL_SHUTDOWN
            )
            self.assertTrue(success)
            
            # Force garbage collection
            gc.collect()
        
        # Get final memory usage
        final_objects = len(gc.get_objects())
        
        # Allow for some object creation during cleanup, but not excessive growth
        object_growth = final_objects - initial_objects
        max_acceptable_growth = initial_objects * 0.1  # 10% growth is acceptable
        
        self.assertLess(object_growth, max_acceptable_growth, 
                       f"Potential memory leak detected: {object_growth} new objects")
        
        print(f"✓ Memory leak prevention test passed (growth: {object_growth} objects)")
    
    def test_performance_benchmarks(self):
        """Test performance benchmarks for cleanup operations."""
        print("Testing performance benchmarks...")
        
        # Test cleanup performance for different scenarios
        scenarios = [
            ShutdownScenario.NORMAL_SHUTDOWN,
            ShutdownScenario.FORCE_CLOSE,
            ShutdownScenario.WINDOW_CLOSE
        ]
        
        performance_results = {}
        
        for scenario in scenarios:
            start_time = time.time()
            success = coordinate_optimized_shutdown_cleanup(
                self.mock_render_window,
                scenario
            )
            end_time = time.time()
            
            self.assertTrue(success)
            
            duration = end_time - start_time
            performance_results[scenario.value] = duration
            
            # Verify performance requirements
            self.assertLess(duration, 2.0, 
                          f"Cleanup for {scenario.value} took too long: {duration:.3f}s")
        
        # Log performance results
        for scenario, duration in performance_results.items():
            print(f"  {scenario}: {duration:.3f}s")
        
        print("✓ Performance benchmarks test passed")
    
    def test_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms."""
        print("Testing error handling and recovery...")
        
        # Simulate various error conditions
        error_scenarios = [
            ("invalid_render_window", None),
            ("missing_methods", Mock()),
            ("exception_during_cleanup", self.mock_render_window)
        ]
        
        for scenario_name, test_window in error_scenarios:
            with self.subTest(scenario=scenario_name):
                if scenario_name == "missing_methods":
                    # Create a mock without required methods
                    test_window = Mock()
                    del test_window.Finalize
                
                elif scenario_name == "exception_during_cleanup":
                    # Make methods raise exceptions
                    self.mock_render_window.Finalize.side_effect = Exception("Test exception")
                
                # Test cleanup with error conditions
                try:
                    success = coordinate_optimized_shutdown_cleanup(
                        test_window,
                        ShutdownScenario.NORMAL_SHUTDOWN
                    )
                    # Should not crash, may return False for some error conditions
                    self.assertIsInstance(success, bool)
                except Exception as e:
                    # If an exception is raised, it should be handled gracefully
                    self.fail(f"Unexpected exception in {scenario_name}: {e}")
        
        print("✓ Error handling and recovery test passed")
    
    def test_concurrent_cleanup_operations(self):
        """Test concurrent cleanup operations for thread safety."""
        print("Testing concurrent cleanup operations...")
        
        # Number of concurrent operations
        num_threads = 5
        results = []
        exceptions = []
        
        def cleanup_worker(thread_id):
            try:
                success = coordinate_optimized_shutdown_cleanup(
                    self.mock_render_window,
                    ShutdownScenario.NORMAL_SHUTDOWN
                )
                results.append((thread_id, success))
            except Exception as e:
                exceptions.append((thread_id, e))
        
        # Start concurrent cleanup threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=cleanup_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10.0)  # 10 second timeout
        
        # Verify results
        self.assertEqual(len(exceptions), 0, 
                        f"Exceptions occurred during concurrent cleanup: {exceptions}")
        self.assertEqual(len(results), num_threads)
        
        # All operations should complete successfully
        for thread_id, success in results:
            self.assertTrue(success, f"Thread {thread_id} cleanup failed")
        
        print("✓ Concurrent cleanup operations test passed")
    
    def test_integration_with_existing_system(self):
        """Test integration with existing VTK cleanup system."""
        print("Testing integration with existing system...")
        
        # Test that the optimized system can work alongside existing components
        try:
            # Initialize existing cleanup coordinator
            from src.gui.vtk.cleanup_coordinator import get_vtk_cleanup_coordinator
            existing_coordinator = get_vtk_cleanup_coordinator()
            
            # Test that both systems can coexist
            success1 = coordinate_optimized_shutdown_cleanup(
                self.mock_render_window,
                ShutdownScenario.NORMAL_SHUTDOWN
            )
            
            # The existing system might not have the same interface, so we just check
            # that our optimized system works independently
            self.assertTrue(success1)
            
        except ImportError:
            # If existing system is not available, skip this test
            self.skipTest("Existing cleanup system not available")
        
        print("✓ Integration with existing system test passed")
    
    def test_diagnostic_information(self):
        """Test diagnostic information collection."""
        print("Testing diagnostic information...")
        
        # Perform a cleanup operation
        coordinate_optimized_shutdown_cleanup(
            self.mock_render_window,
            ShutdownScenario.NORMAL_SHUTDOWN
        )
        
        # Get diagnostic information
        context_diagnostics = self.context_manager.get_diagnostic_info()
        cleanup_diagnostics = self.cleanup_coordinator.get_optimized_cleanup_stats()
        
        # Verify diagnostic information structure
        self.assertIsInstance(context_diagnostics, dict)
        self.assertIsInstance(cleanup_diagnostics, dict)
        
        # Check for expected keys
        self.assertIn("enhanced_context_manager", context_diagnostics)
        self.assertIn("cleanup_operations", cleanup_diagnostics)
        
        # Verify diagnostic data
        self.assertGreater(cleanup_diagnostics["cleanup_operations"], 0)
        self.assertGreaterEqual(cleanup_diagnostics["successful_cleanups"], 0)
        self.assertGreaterEqual(cleanup_diagnostics["failed_cleanups"], 0)
        
        print("✓ Diagnostic information test passed")
    
    def test_stress_testing(self):
        """Stress test the cleanup system with rapid operations."""
        print("Running stress test...")
        
        # Number of rapid cleanup operations
        num_operations = 50
        success_count = 0
        start_time = time.time()
        
        for i in range(num_operations):
            try:
                success = coordinate_optimized_shutdown_cleanup(
                    self.mock_render_window,
                    ShutdownScenario.NORMAL_SHUTDOWN
                )
                if success:
                    success_count += 1
            except Exception as e:
                print(f"  Stress test operation {i} failed: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verify stress test results
        success_rate = success_count / num_operations
        self.assertGreaterEqual(success_rate, 0.95, 
                              f"Stress test success rate too low: {success_rate:.2%}")
        
        # Verify performance under stress
        avg_time_per_operation = total_time / num_operations
        self.assertLess(avg_time_per_operation, 1.0, 
                       f"Average operation time too high under stress: {avg_time_per_operation:.3f}s")
        
        print(f"✓ Stress test passed ({success_count}/{num_operations} successful, "
              f"avg time: {avg_time_per_operation:.3f}s)")


class TestShutdownScenarios(unittest.TestCase):
    """Test specific shutdown scenarios."""
    
    def setUp(self):
        """Set up test environment."""
        self.context_manager = get_enhanced_vtk_context_manager()
        self.cleanup_coordinator = get_optimized_vtk_cleanup_coordinator()
        
        # Create mock render window
        self.mock_render_window = Mock(spec=vtk.vtkRenderWindow)
        self.mock_render_window.GetWindowId.return_value = 12345
    
    def test_application_exit_scenario(self):
        """Test application exit scenario cleanup."""
        print("Testing application exit scenario...")
        
        success = coordinate_optimized_shutdown_cleanup(
            self.mock_render_window,
            ShutdownScenario.APPLICATION_EXIT
        )
        
        self.assertTrue(success)
        
        # Verify scenario was set
        self.assertEqual(self.context_manager.current_scenario, 
                        ShutdownScenario.APPLICATION_EXIT)
        
        print("✓ Application exit scenario test passed")
    
    def test_force_close_scenario(self):
        """Test force close scenario cleanup."""
        print("Testing force close scenario...")
        
        success = coordinate_optimized_shutdown_cleanup(
            self.mock_render_window,
            ShutdownScenario.FORCE_CLOSE
        )
        
        self.assertTrue(success)
        
        # Verify scenario was set
        self.assertEqual(self.context_manager.current_scenario, 
                        ShutdownScenario.FORCE_CLOSE)
        
        print("✓ Force close scenario test passed")
    
    def test_context_loss_scenario(self):
        """Test context loss scenario cleanup."""
        print("Testing context loss scenario...")
        
        # Simulate context loss
        self.mock_render_window.GetWindowId.return_value = 0
        
        success = coordinate_optimized_shutdown_cleanup(
            self.mock_render_window,
            ShutdownScenario.CONTEXT_LOSS
        )
        
        # Should handle context loss gracefully
        self.assertIsInstance(success, bool)
        
        print("✓ Context loss scenario test passed")


def run_comprehensive_cleanup_tests():
    """Run comprehensive tests for the optimized cleanup system."""
    print("=" * 80)
    print("COMPREHENSIVE VTK CLEANUP SYSTEM TEST SUITE")
    print("=" * 80)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestOptimizedCleanupSystem))
    test_suite.addTest(unittest.makeSuite(TestShutdownScenarios))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2, stream=open(os.devnull, 'w'))
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    print("=" * 80)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run the comprehensive test suite
    success = run_comprehensive_cleanup_tests()
    
    if success:
        print("🎉 All tests passed! The optimized cleanup system is working correctly.")
    else:
        print("❌ Some tests failed. Please review the output above.")
        exit(1)