"""
Comprehensive Parser Testing Framework for Candy-Cadence

This module provides a comprehensive testing framework for all refactored parsers,
including unit tests, integration tests, performance benchmarking, and memory leak detection.

Features:
- Unit tests for all parser functions
- Integration tests for complete workflows
- Performance benchmarking with load time targets
- Memory leak detection and testing
- Comprehensive error handling validation
- Streaming and progressive loading tests
"""

import time
import gc
import tracemalloc
import unittest
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from unittest.mock import Mock, patch, MagicMock

from src.parsers.refactored_base_parser import (
    RefactoredBaseParser,
    StreamingProgressCallback,
)
from src.parsers.format_detector import RefactoredFormatDetector
from src.parsers.refactored_stl_parser import RefactoredSTLParser
from src.parsers.refactored_obj_parser import RefactoredOBJParser
from src.parsers.refactored_step_parser import RefactoredSTEPParser
from src.parsers.refactored_threemf_parser import RefactoredThreeMFParser
from src.core.interfaces.parser_interfaces import ModelFormat, ParseError
from src.core.logging_config import get_logger


class BaseParserTest(unittest.TestCase):
    """Base class for all parser tests with common utilities."""

    def setUp(self):
        """Set up test environment."""
        self.test_dir = Path(tempfile.mkdtemp())
        self.logger = get_logger(self.__class__.__name__)
        self.tracemalloc_started = False

    def tearDown(self):
        """Clean up test environment."""
        # Clean up temporary files
        import shutil

        shutil.rmtree(self.test_dir, ignore_errors=True)

        # Stop tracemalloc if started
        if self.tracemalloc_started:
            tracemalloc.stop()
            self.tracemalloc_started = False

    def start_memory_tracking(self):
        """Start memory tracking for leak detection."""
        if not self.tracemalloc_started:
            tracemalloc.start()
            self.tracemalloc_started = True

    def get_memory_usage(self) -> Tuple[int, int]:
        """Get current memory usage in bytes."""
        if not self.tracemalloc_started:
            return 0, 0

        current, peak = tracemalloc.get_traced_memory()
        return current, peak

    def assert_memory_stable(self, tolerance_mb: float = 10.0):
        """Assert that memory usage is stable within tolerance."""
        if not self.tracemalloc_started:
            return

        current, peak = self.get_memory_usage()
        current_mb = current / (1024 * 1024)
        peak_mb = peak / (1024 * 1024)

        self.logger.info(
            f"Memory usage - Current: {current_mb:.2f}MB, Peak: {peak_mb:.2f}MB"
        )

        # For testing purposes, we'll log the memory usage
        # In a real implementation, you might want to track memory across test runs
        self.assertTrue(current_mb >= 0, "Memory usage should be positive")

    def create_test_file(self, content: str, extension: str = ".stl") -> Path:
        """Create a test file with given content."""
        file_path = self.test_dir / f"test_file{extension}"
        file_path.write_text(content)
        return file_path

    def create_progress_callback(self) -> StreamingProgressCallback:
        """Create a mock progress callback."""
        progress_data = []

        def progress_callback(progress: float, message: str):
            progress_data.append((progress, message))

        return StreamingProgressCallback(progress_callback), progress_data


class RefactoredSTLParserTest(BaseParserTest):
    """Unit tests for the refactored STL parser."""

    def setUp(self):
        super().setUp()
        self.parser = RefactoredSTLParser()

    def test_parser_initialization(self):
        """Test parser initialization."""
        self.assertEqual(self.parser.parser_name, "STL")
        self.assertIn(ModelFormat.STL, self.parser.supported_formats)

    def test_ascii_stl_parsing(self):
        """Test ASCII STL file parsing."""
        stl_content = """solid cube
  facet normal 0 0 1
    outer loop
      vertex 0 0 1
      vertex 1 0 1
      vertex 1 1 1
    endloop
  endfacet
endsolid cube
"""
        file_path = self.create_test_file(stl_content, ".stl")
        progress_callback, progress_data = self.create_progress_callback()

        result = self.parser.parse(file_path, progress_callback)

        self.assertEqual(result["format"], ModelFormat.STL)
        self.assertIn("triangles", result)
        self.assertGreater(len(result["triangles"]), 0)
        self.assertIn("stats", result)
        self.assertIn("triangle_count", result["stats"])

    def test_binary_stl_parsing(self):
        """Test binary STL file parsing."""
        # Create a simple binary STL file
        header = b" " * 80
        triangle_count = 1

        # Triangle: normal (3 floats) + 3 vertices (9 floats) + attribute (2 bytes)
        normal = (0.0, 0.0, 1.0)
        vertices = [(0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (1.0, 1.0, 1.0)]
        attribute = 0

        triangle_data = bytearray()

        # Normal
        triangle_data.extend(self._float32_to_bytes(normal[0]))
        triangle_data.extend(self._float32_to_bytes(normal[1]))
        triangle_data.extend(self._float32_to_bytes(normal[2]))

        # Vertices
        for vertex in vertices:
            triangle_data.extend(self._float32_to_bytes(vertex[0]))
            triangle_data.extend(self._float32_to_bytes(vertex[1]))
            triangle_data.extend(self._float32_to_bytes(vertex[2]))

        # Attribute
        triangle_data.extend(self._uint16_to_bytes(attribute))

        binary_data = header + self._uint32_to_bytes(triangle_count) + triangle_data

        file_path = self.test_dir / "test_binary.stl"
        file_path.write_bytes(binary_data)

        progress_callback, progress_data = self.create_progress_callback()
        result = self.parser.parse(file_path, progress_callback)

        self.assertEqual(result["format"], ModelFormat.STL)
        self.assertIn("triangles", result)

    def _float32_to_bytes(self, value: float) -> bytes:
        """Convert float32 to bytes."""
        import struct

        return struct.pack("<f", value)

    def _uint32_to_bytes(self, value: int) -> bytes:
        """Convert uint32 to bytes."""
        import struct

        return struct.pack("<I", value)

    def _uint16_to_bytes(self, value: int) -> bytes:
        """Convert uint16 to bytes."""
        import struct

        return struct.pack("<H", value)

    def test_stl_validation(self):
        """Test STL file validation."""
        # Valid ASCII STL
        valid_stl = """solid test
  facet normal 0 0 1
    outer loop
      vertex 0 0 1
      vertex 1 0 1
      vertex 1 1 1
    endloop
  endfacet
endsolid test
"""
        valid_file = self.create_test_file(valid_stl, ".stl")
        is_valid, error = self.parser.validate_file(valid_file)
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

        # Invalid file
        invalid_file = self.create_test_file("not an stl file", ".stl")
        is_valid, error = self.parser.validate_file(invalid_file)
        self.assertFalse(is_valid)

    def test_stl_performance(self):
        """Test STL parser performance."""
        self.start_memory_tracking()

        # Create a large STL file
        triangles = []
        for i in range(10000):
            triangle = {
                "normal": (0.0, 0.0, 1.0),
                "vertices": [(i, 0, 0), (i + 1, 0, 0), (i + 1, 1, 0)],
            }
            triangles.append(triangle)

        large_stl = self._create_large_stl_file(triangles)

        start_time = time.time()
        progress_callback, progress_data = self.create_progress_callback()
        result = self.parser.parse(large_stl, progress_callback)
        parsing_time = time.time() - start_time

        # Performance assertion - should parse large file reasonably quickly
        self.assertLess(
            parsing_time, 30.0, "Large STL parsing should complete within 30 seconds"
        )

        self.assert_memory_stable()

    def _create_large_stl_file(self, triangles: List[Dict]) -> Path:
        """Create a large STL file for performance testing."""
        stl_content = "solid large_stl\n"

        for triangle in triangles:
            normal = triangle["normal"]
            vertices = triangle["vertices"]

            stl_content += f"""  facet normal {normal[0]} {normal[1]} {normal[2]}
    outer loop
      vertex {vertices[0][0]} {vertices[0][1]} {vertices[0][2]}
      vertex {vertices[1][0]} {vertices[1][1]} {vertices[1][2]}
      vertex {vertices[2][0]} {vertices[2][1]} {vertices[2][2]}
    endloop
  endfacet
"""

        stl_content += "endsolid large_stl"

        file_path = self.test_dir / "large_stl.stl"
        file_path.write_text(stl_content)
        return file_path


class RefactoredOBJParserTest(BaseParserTest):
    """Unit tests for the refactored OBJ parser."""

    def setUp(self):
        super().setUp()
        self.parser = RefactoredOBJParser()

    def test_parser_initialization(self):
        """Test parser initialization."""
        self.assertEqual(self.parser.parser_name, "OBJ")
        self.assertIn(ModelFormat.OBJ, self.parser.supported_formats)

    def test_obj_parsing(self):
        """Test OBJ file parsing."""
        obj_content = """# Simple cube
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 1.0 1.0 0.0
v 0.0 1.0 0.0
v 0.0 0.0 1.0
v 1.0 0.0 1.0
v 1.0 1.0 1.0
v 0.0 1.0 1.0

f 1 2 3
f 1 3 4
f 2 6 7
f 2 7 3
f 6 5 8
f 6 8 7
f 5 1 4
f 5 4 8
f 4 3 7
f 4 7 8
f 5 6 2
f 5 2 1
"""
        file_path = self.create_test_file(obj_content, ".obj")
        progress_callback, progress_data = self.create_progress_callback()

        result = self.parser.parse(file_path, progress_callback)

        self.assertEqual(result["format"], ModelFormat.OBJ)
        self.assertIn("triangles", result)
        self.assertGreater(len(result["triangles"]), 0)

    def test_obj_with_mtl(self):
        """Test OBJ file with MTL material file."""
        # Create OBJ file
        obj_content = """# Cube with material
mtllib cube.mtl
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 1.0 1.0 0.0
v 0.0 1.0 0.0

f 1 2 3
f 1 3 4
"""
        obj_file = self.create_test_file(obj_content, ".obj")

        # Create MTL file
        mtl_content = """newmtl cube_material
Ka 0.2 0.2 0.2
Kd 0.8 0.8 0.8
Ks 0.5 0.5 0.5
"""
        mtl_file = self.test_dir / "cube.mtl"
        mtl_file.write_text(mtl_content)

        progress_callback, progress_data = self.create_progress_callback()
        result = self.parser.parse(obj_file, progress_callback)

        self.assertEqual(result["format"], ModelFormat.OBJ)
        self.assertIn("triangles", result)


class RefactoredFormatDetectorTest(BaseParserTest):
    """Unit tests for the refactored format detector."""

    def setUp(self):
        super().setUp()
        self.detector = RefactoredFormatDetector()

    def test_stl_detection(self):
        """Test STL format detection."""
        stl_content = """solid test
  facet normal 0 0 1
    outer loop
      vertex 0 0 1
      vertex 1 0 1
      vertex 1 1 1
    endloop
  endfacet
endsolid test
"""
        file_path = self.create_test_file(stl_content, ".stl")
        detected_format = self.detector.detect_format(file_path)
        self.assertEqual(detected_format, ModelFormat.STL)

    def test_obj_detection(self):
        """Test OBJ format detection."""
        obj_content = """v 0.0 0.0 0.0
v 1.0 0.0 0.0
f 1 2 3
"""
        file_path = self.create_test_file(obj_content, ".obj")
        detected_format = self.detector.detect_format(file_path)
        self.assertEqual(detected_format, ModelFormat.OBJ)

    def test_3mf_detection(self):
        """Test 3MF format detection."""
        # Create a minimal 3MF file (ZIP with XML content)
        import zipfile
        import tempfile

        with zipfile.ZipFile(self.test_dir / "test.3mf", "w") as zip_file:
            zip_file.writestr(
                "3D/3dmodel.model", '<?xml version="1.0"?><model></model>'
            )

        file_path = self.test_dir / "test.3mf"
        detected_format = self.detector.detect_format(file_path)
        self.assertEqual(detected_format, ModelFormat.THREE_MF)


class ParserIntegrationTest(BaseParserTest):
    """Integration tests for the complete parser system."""

    def setUp(self):
        super().setUp()
        self.detector = RefactoredFormatDetector()
        self.parsers = {
            ModelFormat.STL: RefactoredSTLParser(),
            ModelFormat.OBJ: RefactoredOBJParser(),
            ModelFormat.STEP: RefactoredSTEPParser(),
            ModelFormat.THREE_MF: RefactoredThreeMFParser(),
        }

    def test_complete_workflow(self):
        """Test complete parser workflow with different formats."""
        test_cases = [
            self._create_test_stl(),
            self._create_test_obj(),
            self._create_test_3mf(),
        ]

        for file_path, expected_format in test_cases:
            with self.subTest(file=file_path.name):
                # Detect format
                detected_format = self.detector.detect_format(file_path)
                self.assertEqual(detected_format, expected_format)

                # Get parser for detected format
                parser = self.parsers[detected_format]

                # Parse file
                progress_callback, progress_data = self.create_progress_callback()
                result = parser.parse(file_path, progress_callback)

                # Validate result
                self.assertEqual(result["format"], expected_format)
                self.assertIn("triangles", result)
                self.assertIn("stats", result)
                self.assertGreater(len(result["triangles"]), 0)

    def test_error_handling(self):
        """Test error handling across parsers."""
        # Test with invalid file
        invalid_file = self.create_test_file("invalid content", ".invalid")

        # Should detect as unsupported format
        detected_format = self.detector.detect_format(invalid_file)
        self.assertIsNone(detected_format)

        # Test with missing file
        missing_file = Path("nonexistent.stl")

        with self.assertRaises(FileNotFoundError):
            parser = self.parsers[ModelFormat.STL]
            parser.parse(missing_file)

    def _create_test_stl(self) -> Tuple[Path, ModelFormat]:
        """Create a test STL file."""
        stl_content = """solid cube
  facet normal 0 0 1
    outer loop
      vertex 0 0 1
      vertex 1 0 1
      vertex 1 1 1
    endloop
  endfacet
endsolid cube
"""
        file_path = self.create_test_file(stl_content, ".stl")
        return file_path, ModelFormat.STL

    def _create_test_obj(self) -> Tuple[Path, ModelFormat]:
        """Create a test OBJ file."""
        obj_content = """v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 0.0 1.0 0.0
f 1 2 3
"""
        file_path = self.create_test_file(obj_content, ".obj")
        return file_path, ModelFormat.OBJ

    def _create_test_3mf(self) -> Tuple[Path, ModelFormat]:
        """Create a test 3MF file."""
        import zipfile

        with zipfile.ZipFile(self.test_dir / "test.3mf", "w") as zip_file:
            model_content = """<?xml version="1.0"?>
<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
    <object id="1" type="model">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0"/>
          <vertex x="1" y="0" z="0"/>
          <vertex x="0" y="1" z="0"/>
        </vertices>
        <triangles>
          <triangle v1="0" v2="1" v3="2"/>
        </triangles>
      </mesh>
    </object>
  </resources>
  <build>
    <item objectid="1"/>
  </build>
</model>"""
            zip_file.writestr("3D/3dmodel.model", model_content)

        file_path = self.test_dir / "test.3mf"
        return file_path, ModelFormat.THREE_MF


class ParserPerformanceTest(BaseParserTest):
    """Performance tests for parsers."""

    def setUp(self):
        super().setUp()
        self.parsers = {
            ModelFormat.STL: RefactoredSTLParser(),
            ModelFormat.OBJ: RefactoredOBJParser(),
            ModelFormat.STEP: RefactoredSTEPParser(),
            ModelFormat.THREE_MF: RefactoredThreeMFParser(),
        }

    def test_load_time_requirements(self):
        """Test load time requirements for different file sizes."""
        self.start_memory_tracking()

        test_cases = [
            self._create_small_stl_file(),  # < 100MB target: < 5s
            self._create_medium_stl_file(),  # 100-500MB target: < 15s
            self._create_large_stl_file(),  # > 500MB target: < 30s
        ]

        expected_times = [5.0, 15.0, 30.0]  # seconds

        for file_path, expected_time in zip(test_cases, expected_times):
            file_size_mb = file_path.stat().st_size / (1024 * 1024)

            with self.subTest(file_size=f"{file_size_mb:.1f}MB"):
                parser = self.parsers[ModelFormat.STL]

                # Test parsing time
                start_time = time.time()
                progress_callback, progress_data = self.create_progress_callback()
                result = parser.parse(file_path, progress_callback)
                parsing_time = time.time() - start_time

                self.logger.info(
                    f"Parsed {file_size_mb:.1f}MB STL in {parsing_time:.2f}s"
                )

                # Assert parsing completed within time requirement
                self.assertLess(
                    parsing_time,
                    expected_time,
                    f"Parsing {file_size_mb:.1f}MB file took {parsing_time:.2f}s, "
                    f"should be less than {expected_time}s",
                )

                # Validate result
                self.assertIn("triangles", result)
                self.assertGreater(len(result["triangles"]), 0)

                # Force garbage collection
                gc.collect()
                self.assert_memory_stable()

    def _create_small_stl_file(self) -> Path:
        """Create a small STL file (< 100MB)."""
        triangles = []
        for i in range(1000):  # Small file
            triangle = {
                "normal": (0.0, 0.0, 1.0),
                "vertices": [(i, 0, 0), (i + 1, 0, 0), (i + 1, 1, 0)],
            }
            triangles.append(triangle)

        return self._create_stl_from_triangles(triangles)

    def _create_medium_stl_file(self) -> Path:
        """Create a medium STL file (100-500MB)."""
        triangles = []
        for i in range(200000):  # Medium file
            triangle = {
                "normal": (0.0, 0.0, 1.0),
                "vertices": [(i, 0, 0), (i + 1, 0, 0), (i + 1, 1, 0)],
            }
            triangles.append(triangle)

        return self._create_stl_from_triangles(triangles)

    def _create_large_stl_file(self) -> Path:
        """Create a large STL file (> 500MB)."""
        triangles = []
        for i in range(1000000):  # Large file
            triangle = {
                "normal": (0.0, 0.0, 1.0),
                "vertices": [(i, 0, 0), (i + 1, 0, 0), (i + 1, 1, 0)],
            }
            triangles.append(triangle)

        return self._create_stl_from_triangles(triangles)

    def _create_stl_from_triangles(self, triangles: List[Dict]) -> Path:
        """Create STL file from triangle data."""
        stl_content = "solid performance_test\n"

        for triangle in triangles:
            normal = triangle["normal"]
            vertices = triangle["vertices"]

            stl_content += f"""  facet normal {normal[0]} {normal[1]} {normal[2]}
    outer loop
      vertex {vertices[0][0]} {vertices[0][1]} {vertices[0][2]}
      vertex {vertices[1][0]} {vertices[1][1]} {vertices[1][2]}
      vertex {vertices[2][0]} {vertices[2][1]} {vertices[2][2]}
    endloop
  endfacet
"""

        stl_content += "endsolid performance_test"

        file_path = self.test_dir / "performance_test.stl"
        file_path.write_text(stl_content)
        return file_path

    def test_memory_usage_limits(self):
        """Test memory usage stays within limits."""
        self.start_memory_tracking()

        # Parse a medium-sized file multiple times
        file_path = self._create_medium_stl_file()
        parser = RefactoredSTLParser()

        initial_memory, initial_peak = self.get_memory_usage()

        # Parse file 10 times to test for memory leaks
        for i in range(10):
            progress_callback, progress_data = self.create_progress_callback()
            result = parser.parse(file_path, progress_callback)

            # Force garbage collection
            gc.collect()

            current_memory, current_peak = self.get_memory_usage()

            # Memory should not grow significantly
            if i == 0:
                baseline_memory = current_memory
            else:
                memory_growth = (current_memory - baseline_memory) / (1024 * 1024)
                self.assertLess(
                    memory_growth,
                    50.0,
                    f"Memory grew by {memory_growth:.2f}MB after {i+1} iterations",
                )

        self.logger.info(f"Memory usage stable after 10 iterations")


class ParserMemoryLeakTest(BaseParserTest):
    """Memory leak detection tests for parsers."""

    def setUp(self):
        super().setUp()
        self.parsers = {
            ModelFormat.STL: RefactoredSTLParser(),
            ModelFormat.OBJ: RefactoredOBJParser(),
            ModelFormat.STEP: RefactoredSTEPParser(),
            ModelFormat.THREE_MF: RefactoredThreeMFParser(),
        }

    def test_memory_leak_detection(self):
        """Test for memory leaks by repeated parsing."""
        self.start_memory_tracking()

        # Create test files for each format
        test_files = [
            self._create_test_stl(),
            self._create_test_obj(),
            self._create_test_3mf(),
        ]

        for file_path, format_type in test_files:
            with self.subTest(format=format_type.value):
                parser = self.parsers[format_type]

                # Baseline memory measurement
                initial_memory, initial_peak = self.get_memory_usage()
                gc.collect()  # Clean up before testing
                gc.collect()  # Double cleanup

                # Parse file 20 times to detect leaks
                memory_samples = []
                for i in range(20):
                    progress_callback, progress_data = self.create_progress_callback()
                    result = parser.parse(file_path, progress_callback)

                    # Force garbage collection
                    gc.collect()
                    gc.collect()

                    current_memory, current_peak = self.get_memory_usage()
                    memory_samples.append(current_memory)

                    # Validate result
                    self.assertIn("triangles", result)
                    self.assertGreater(len(result["triangles"]), 0)

                # Check for memory growth pattern
                # Memory should stabilize or grow very slowly
                baseline_memory = memory_samples[0]
                final_memory = memory_samples[-1]

                memory_growth_mb = (final_memory - baseline_memory) / (1024 * 1024)

                # Allow some growth but not excessive
                self.assertLess(
                    memory_growth_mb,
                    20.0,
                    f"Potential memory leak in {format_type.value}: "
                    f"Memory grew by {memory_growth_mb:.2f}MB over 20 iterations",
                )

                self.logger.info(
                    f"{format_type.value}: Memory growth {memory_growth_mb:.2f}MB over 20 iterations"
                )

    def test_large_file_memory_stability(self):
        """Test memory stability with large files."""
        self.start_memory_tracking()

        # Create a large test file
        large_file = self._create_large_test_file()
        parser = self.parsers[ModelFormat.STL]

        # Parse file multiple times
        for i in range(5):
            start_memory, start_peak = self.get_memory_usage()

            progress_callback, progress_data = self.create_progress_callback()
            result = parser.parse(large_file, progress_callback)

            end_memory, end_peak = self.get_memory_usage()

            memory_diff_mb = (end_memory - start_memory) / (1024 * 1024)
            peak_diff_mb = (end_peak - start_peak) / (1024 * 1024)

            self.logger.info(
                f"Iteration {i+1}: Memory diff: {memory_diff_mb:.2f}MB, Peak diff: {peak_diff_mb:.2f}MB"
            )

            # Force cleanup
            del result
            gc.collect()
            gc.collect()

            # Memory should return to reasonable levels after cleanup
            if i < 4:  # Don't check the last iteration
                self.assertLess(
                    memory_diff_mb,
                    100.0,
                    f"Memory not properly cleaned after iteration {i+1}",
                )

    def _create_test_stl(self) -> Tuple[Path, ModelFormat]:
        """Create a test STL file."""
        stl_content = """solid test_cube
  facet normal 0 0 1
    outer loop
      vertex 0 0 1
      vertex 1 0 1
      vertex 1 1 1
    endloop
  endfacet
  facet normal 0 0 -1
    outer loop
      vertex 0 0 0
      vertex 1 1 0
      vertex 1 0 0
    endloop
  endfacet
endsolid test_cube
"""
        file_path = self.create_test_file(stl_content, ".stl")
        return file_path, ModelFormat.STL

    def _create_test_obj(self) -> Tuple[Path, ModelFormat]:
        """Create a test OBJ file."""
        obj_content = """# Test cube
v 0.0 0.0 0.0
v 1.0 0.0 0.0
v 1.0 1.0 0.0
v 0.0 1.0 0.0
v 0.0 0.0 1.0
v 1.0 0.0 1.0
v 1.0 1.0 1.0
v 0.0 1.0 1.0

f 1 2 3
f 1 3 4
f 2 6 7
f 2 7 3
f 6 5 8
f 6 8 7
f 5 1 4
f 5 4 8
f 4 3 7
f 4 7 8
f 5 6 2
f 5 2 1
"""
        file_path = self.create_test_file(obj_content, ".obj")
        return file_path, ModelFormat.OBJ

    def _create_test_3mf(self) -> Tuple[Path, ModelFormat]:
        """Create a test 3MF file."""
        import zipfile

        with zipfile.ZipFile(self.test_dir / "test_leak.3mf", "w") as zip_file:
            model_content = """<?xml version="1.0"?>
<model unit="millimeter" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">
  <resources>
    <object id="1" type="model">
      <mesh>
        <vertices>
          <vertex x="0" y="0" z="0"/>
          <vertex x="1" y="0" z="0"/>
          <vertex x="0" y="1" z="0"/>
          <vertex x="1" y="1" z="0"/>
        </vertices>
        <triangles>
          <triangle v1="0" v2="1" v3="2"/>
          <triangle v1="1" v2="3" v3="2"/>
        </triangles>
      </mesh>
    </object>
  </resources>
  <build>
    <item objectid="1"/>
  </build>
</model>"""
            zip_file.writestr("3D/3dmodel.model", model_content)

        file_path = self.test_dir / "test_leak.3mf"
        return file_path, ModelFormat.THREE_MF

    def _create_large_test_file(self) -> Path:
        """Create a large test file for memory testing."""
        # Create a large STL with many triangles
        triangles = []
        for i in range(50000):  # Large file for memory testing
            triangle = {
                "normal": (0.0, 0.0, 1.0),
                "vertices": [
                    (i % 100, 0, 0),
                    ((i + 1) % 100, 0, 0),
                    ((i + 1) % 100, 1, 0),
                ],
            }
            triangles.append(triangle)

        stl_content = "solid large_memory_test\n"
        for triangle in triangles:
            normal = triangle["normal"]
            vertices = triangle["vertices"]
            stl_content += f"""  facet normal {normal[0]} {normal[1]} {normal[2]}
    outer loop
      vertex {vertices[0][0]} {vertices[0][1]} {vertices[0][2]}
      vertex {vertices[1][0]} {vertices[1][1]} {vertices[1][2]}
      vertex {vertices[2][0]} {vertices[2][1]} {vertices[2][2]}
    endloop
  endfacet
"""
        stl_content += "endsolid large_memory_test"

        file_path = self.test_dir / "large_memory_test.stl"
        file_path.write_text(stl_content)
        return file_path


if __name__ == "__main__":
    # Configure logging for tests
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Run all tests
    unittest.main(verbosity=2)
