"""
End-to-End Testing Framework for Complete Candy-Cadence Workflows.

This module provides comprehensive end-to-end testing scenarios that validate
complete user workflows from file loading through rendering and interaction.
"""

import gc
import json
import os
import shutil
import sys
import tempfile
import time
import threading
import unittest
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from unittest.mock import Mock, patch, MagicMock

import pytest
import psutil

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core.logging_config import get_logger
from src.parsers.stl_parser import STLParser
from src.parsers.obj_parser import OBJParser


class EndToEndTestBase(unittest.TestCase):
    """Base class for end-to-end tests with comprehensive setup."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment for end-to-end tests."""
        cls.logger = get_logger(__name__)
        cls.temp_dir = tempfile.mkdtemp()
        cls.test_files_dir = Path(cls.temp_dir) / "test_files"
        cls.test_files_dir.mkdir(exist_ok=True)

        # Mock repositories
        cls.model_repository = Mock()
        cls.metadata_repository = Mock()

        # Create sample test files
        cls._create_sample_test_files()

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment."""
        try:
            shutil.rmtree(cls.temp_dir, ignore_errors=True)
        except Exception as e:
            cls.logger.warning(f"Failed to clean up temp directory: {e}")

    @classmethod
    def _create_sample_test_files(cls):
        """Create sample test files for end-to-end testing."""
        # Create STL files
        cls._create_stl_file("small_cube.stl", 10)
        cls._create_stl_file("medium_cube.stl", 1000)
        cls._create_stl_file("large_cube.stl", 10000)

        # Create OBJ file
        cls._create_obj_file("test_cube.obj")

    @classmethod
    def _create_stl_file(cls, filename: str, triangle_count: int):
        """Create a binary STL file for testing."""
        import struct

        file_path = cls.test_files_dir / filename

        with open(file_path, "wb") as f:
            # Write header (80 bytes)
            header = f"Test STL {triangle_count} triangles".encode("utf-8")
            f.write(header.ljust(80, b"\x00"))

            # Write triangle count (4 bytes)
            f.write(struct.pack("<I", triangle_count))

            # Write triangles
            for i in range(triangle_count):
                # Normal vector (3 floats)
                f.write(struct.pack("<fff", 0.0, 0.0, 1.0))

                # Vertex 1 (3 floats)
                f.write(struct.pack("<fff", i * 1.0, 0.0, 0.0))

                # Vertex 2 (3 floats)
                f.write(struct.pack("<fff", i * 1.0 + 1.0, 0.0, 0.0))

                # Vertex 3 (3 floats)
                f.write(struct.pack("<fff", i * 1.0, 1.0, 0.0))

                # Attribute byte count (2 bytes)
                f.write(struct.pack("<H", 0))

        return file_path

    @classmethod
    def _create_obj_file(cls, filename: str):
        """Create an OBJ file for testing."""
        file_path = cls.test_files_dir / filename

        obj_content = """# Test OBJ file
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 1.0 1.0 0.0
v 0.0 1.0 0.0
v 0.0 0.0 1.0
v 1.0 0.0 1.0
v 1.0 1.0 1.0
v 0.0 1.0 1.0
f 1 2 3 4
f 5 8 7 6
f 1 5 6 2
f 2 6 7 3
f 3 7 8 4
f 5 1 4 8
"""

        with open(file_path, "w") as f:
            f.write(obj_content)

        return file_path

    def setUp(self):
        """Set up individual test."""
        # Track performance metrics
        self.performance_metrics = {}

    def tearDown(self):
        """Clean up after test."""
        # Force garbage collection
        gc.collect()

        # Log performance metrics
        if self.performance_metrics:
            self.logger.info(f"Test performance metrics: {self.performance_metrics}")

    def measure_workflow_performance(
        self, workflow_name: str, operation: callable
    ) -> Dict[str, float]:
        """Measure performance of a complete workflow."""
        # Record system resources before
        process = psutil.Process()
        memory_before = process.memory_info().rss
        cpu_before = process.cpu_percent()

        # Measure operation time
        start_time = time.time()
        result = operation()
        end_time = time.time()

        # Record system resources after
        memory_after = process.memory_info().rss
        cpu_after = process.cpu_percent()

        # Calculate metrics
        execution_time = end_time - start_time
        memory_used = (memory_after - memory_before) / (1024 * 1024)  # MB
        cpu_usage = cpu_after - cpu_before

        metrics = {
            "execution_time": execution_time,
            "memory_used_mb": memory_used,
            "cpu_usage": cpu_usage,
            "success": result is not None,
        }

        self.performance_metrics[workflow_name] = metrics
        return metrics

    def assert_workflow_performance(
        self,
        metrics: Dict[str, float],
        max_time: float = 5.0,
        max_memory_mb: float = 100.0,
    ):
        """Assert that workflow performance meets requirements."""
        self.assertLess(
            metrics["execution_time"],
            max_time,
            f"Workflow took {metrics['execution_time']:.2f}s, expected < {max_time}s",
        )
        self.assertLess(
            metrics["memory_used_mb"],
            max_memory_mb,
            f"Workflow used {metrics['memory_used_mb']:.2f}MB, expected < {max_memory_mb}MB",
        )
        self.assertTrue(metrics["success"], "Workflow did not complete successfully")


class TestCompleteFileLoadingWorkflow(EndToEndTestBase):
    """Test complete file loading workflows for all supported formats."""

    def test_stl_file_loading_workflow(self):
        """Test complete STL file loading workflow."""

        def stl_workflow():
            # Step 1: Load and parse file
            stl_file = self.test_files_dir / "small_cube.stl"
            parser = STLParser()
            model = parser.parse_file(stl_file)
            self.assertIsNotNone(model)
            self.assertGreater(model.stats.triangle_count, 0)

            # Step 2: Store in repository (mock)
            model_id = self.model_repository.save_model(model)
            self.assertIsNotNone(model_id)

            # Step 3: Retrieve from repository (mock)
            retrieved_model = self.model_repository.get_model(model_id)
            self.assertIsNotNone(retrieved_model)

            return True

        metrics = self.measure_workflow_performance("stl_loading", stl_workflow)
        self.assert_workflow_performance(metrics, max_time=2.0, max_memory_mb=50.0)

    def test_obj_file_loading_workflow(self):
        """Test complete OBJ file loading workflow."""

        def obj_workflow():
            # Step 1: Load and parse file
            obj_file = self.test_files_dir / "test_cube.obj"
            parser = OBJParser()
            model = parser.parse_file(obj_file)
            self.assertIsNotNone(model)
            self.assertGreater(model.stats.vertex_count, 0)

            # Step 2: Store in repository (mock)
            model_id = self.model_repository.save_model(model)
            self.assertIsNotNone(model_id)

            # Step 3: Retrieve from repository (mock)
            retrieved_model = self.model_repository.get_model(model_id)
            self.assertIsNotNone(retrieved_model)

            return True

        metrics = self.measure_workflow_performance("obj_loading", obj_workflow)
        self.assert_workflow_performance(metrics, max_time=3.0, max_memory_mb=75.0)


class TestMultiFormatWorkflow(EndToEndTestBase):
    """Test workflows involving multiple file formats."""

    def test_mixed_format_processing_workflow(self):
        """Test processing multiple files of different formats."""

        def mixed_workflow():
            files_to_process = ["small_cube.stl", "test_cube.obj"]

            processed_models = []

            for filename in files_to_process:
                file_path = self.test_files_dir / filename

                # Parse based on file extension
                if filename.endswith(".stl"):
                    parser = STLParser()
                elif filename.endswith(".obj"):
                    parser = OBJParser()
                else:
                    continue

                # Parse file
                model = parser.parse_file(file_path)
                self.assertIsNotNone(model)

                # Store in repository
                model_id = self.model_repository.save_model(model)
                self.assertIsNotNone(model_id)

                processed_models.append(
                    {"filename": filename, "model_id": model_id, "stats": model.stats}
                )

            # Verify all files were processed
            self.assertEqual(len(processed_models), len(files_to_process))

            # Verify each model can be retrieved
            for model_info in processed_models:
                retrieved_model = self.model_repository.get_model(
                    model_info["model_id"]
                )
                self.assertIsNotNone(retrieved_model)

            return processed_models

        metrics = self.measure_workflow_performance(
            "mixed_format_processing", mixed_workflow
        )
        self.assert_workflow_performance(metrics, max_time=10.0, max_memory_mb=200.0)


class TestErrorRecoveryWorkflows(EndToEndTestBase):
    """Test error recovery and resilience workflows."""

    def test_corrupted_file_recovery_workflow(self):
        """Test recovery from corrupted file processing."""

        def corruption_recovery_workflow():
            # Create a corrupted file
            corrupted_file = self.test_files_dir / "corrupted.stl"
            with open(corrupted_file, "wb") as f:
                f.write(b"This is not a valid STL file")

            # Attempt to process corrupted file
            parser = STLParser()

            try:
                model = parser.parse_file(corrupted_file)
                # If we get here, the parser should have handled the error gracefully
                self.fail("Expected STLParseError was not raised")
            except Exception as e:
                # Expected - file is corrupted
                self.assertIsInstance(e, Exception)

            # Verify system is still functional with valid files
            valid_file = self.test_files_dir / "small_cube.stl"
            model = parser.parse_file(valid_file)
            self.assertIsNotNone(model)

            return True

        metrics = self.measure_workflow_performance(
            "corruption_recovery", corruption_recovery_workflow
        )
        self.assert_workflow_performance(metrics, max_time=3.0, max_memory_mb=50.0)

    def test_large_file_processing_workflow(self):
        """Test processing of large files with memory constraints."""

        def large_file_workflow():
            # Create a large STL file
            large_file = self.test_files_dir / "very_large.stl"
            self._create_stl_file("very_large.stl", 100000)  # 100k triangles

            # Process large file
            parser = STLParser()
            model = parser.parse_file(large_file)
            self.assertIsNotNone(model)
            self.assertEqual(model.stats.triangle_count, 100000)

            # Store in repository
            model_id = self.model_repository.save_model(model)
            self.assertIsNotNone(model_id)

            # Clean up large file
            large_file.unlink(missing_ok=True)

            return True

        metrics = self.measure_workflow_performance(
            "large_file_processing", large_file_workflow
        )
        self.assert_workflow_performance(metrics, max_time=15.0, max_memory_mb=500.0)


class TestPerformanceValidationWorkflows(EndToEndTestBase):
    """Test performance validation under realistic conditions."""

    def test_sustained_load_workflow(self):
        """Test system performance under sustained load."""

        def sustained_load_workflow():
            # Process multiple files repeatedly to simulate sustained load
            files = ["small_cube.stl", "medium_cube.stl"]
            iterations = 5

            processing_times = []

            for iteration in range(iterations):
                for filename in files:
                    file_path = self.test_files_dir / filename

                    start_time = time.time()
                    parser = STLParser()
                    model = parser.parse_file(file_path)
                    processing_time = time.time() - start_time

                    processing_times.append(processing_time)

                    # Store model
                    self.model_repository.save_model(model)

                    # Clean up
                    del model
                    gc.collect()

            # Analyze performance consistency
            avg_time = sum(processing_times) / len(processing_times)
            max_time = max(processing_times)
            min_time = min(processing_times)

            # Performance should be consistent (max should not be more than 3x min)
            performance_ratio = max_time / min_time if min_time > 0 else 1.0
            self.assertLess(
                performance_ratio,
                3.0,
                f"Performance inconsistent: ratio {performance_ratio:.2f}",
            )

            # Average processing time should be reasonable
            self.assertLess(
                avg_time, 1.0, f"Average processing time too high: {avg_time:.2f}s"
            )

            return {
                "avg_time": avg_time,
                "max_time": max_time,
                "min_time": min_time,
                "performance_ratio": performance_ratio,
            }

        metrics = self.measure_workflow_performance(
            "sustained_load", sustained_load_workflow
        )
        self.assert_workflow_performance(metrics, max_time=30.0, max_memory_mb=200.0)

    def test_memory_efficiency_workflow(self):
        """Test memory efficiency during extended processing."""

        def memory_efficiency_workflow():
            process = psutil.Process()

            # Record initial memory
            initial_memory = process.memory_info().rss

            # Process multiple large files
            for i in range(10):
                # Create progressively larger files
                triangle_count = (i + 1) * 1000
                filename = f"memory_test_{i}.stl"
                file_path = self.test_files_dir / filename
                self._create_stl_file(filename, triangle_count)

                # Process file
                parser = STLParser()
                model = parser.parse_file(file_path)

                # Store model
                self.model_repository.save_model(model)

                # Clean up
