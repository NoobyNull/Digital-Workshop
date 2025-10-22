"""
GPU-Accelerated STL Parsing Tests.

Comprehensive test suite for GPU-accelerated STL parsing functionality,
including performance benchmarks, error handling, and validation tests.
"""

import time
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np  # type: ignore

from src.parsers.stl_gpu_parser import STLGPUParser, GPUParseConfig, STLGPUParseError
from src.parsers.stl_progressive_loader import ProgressiveSTLLoader, LODConfig, LODLevel
from src.core.gpu_acceleration import get_gpu_accelerator
from src.core.gpu_memory_manager import get_gpu_memory_manager
from src.core.hardware_acceleration import get_acceleration_manager, AccelBackend
from src.parsers.base_parser import Model, ModelFormat, LoadingState
# Helper functions for creating test STL files
def create_sample_stl_binary(filepath: str, triangle_count: int = 100):
    """Create a sample binary STL file with specified triangle count."""
    import struct
    from pathlib import Path

    filepath = Path(filepath)

    # Generate simple geometry (sphere approximation)
    triangles = []
    for i in range(triangle_count):
        # Simple triangle vertices
        angle = (i / triangle_count) * 2 * 3.14159
        v1 = (0.5 * (i % 3), 0.5 * ((i + 1) % 3), 0.5 * ((i + 2) % 3))
        v2 = (0.5 * ((i + 1) % 3), 0.5 * ((i + 2) % 3), 0.5 * (i % 3))
        v3 = (0.5 * ((i + 2) % 3), 0.5 * (i % 3), 0.5 * ((i + 1) % 3))

        # Simple normal (pointing outward)
        normal = (0, 0, 1)

        triangles.append((normal, v1, v2, v3))

    with open(filepath, 'wb') as f:
        # Write header (80 bytes)
        header = b"Test Binary STL File"
        f.write(header.ljust(80, b'\x00'))

        # Write triangle count (4 bytes)
        f.write(struct.pack('<I', len(triangles)))

        # Write triangles
        for normal, v1, v2, v3 in triangles:
            # Normal vector (3 floats)
            f.write(struct.pack('<fff', *normal))

            # Vertices (3 floats each)
            f.write(struct.pack('<fff', *v1))
            f.write(struct.pack('<fff', *v2))
            f.write(struct.pack('<fff', *v3))

            # Attribute byte count (2 bytes)
            f.write(struct.pack('<H', 0))


def create_large_sample_stl(filepath: str, triangle_count: int = 50000):
    """Create a large sample STL file for performance testing."""
    create_sample_stl_binary(filepath, triangle_count)


class TestGPUParserInitialization:
    """Test GPU parser initialization and configuration."""

    def test_parser_initialization(self):
        """Test basic parser initialization."""
        parser = STLGPUParser()
        assert parser is not None
        assert parser.config is not None
        assert isinstance(parser.config, GPUParseConfig)

    def test_parser_with_custom_config(self):
        """Test parser with custom configuration."""
        config = GPUParseConfig(
            use_memory_mapping=True,
            chunk_size_triangles=50000,
            enable_progressive_loading=True
        )
        parser = STLGPUParser(config)
        assert parser.config.chunk_size_triangles == 50000
        assert parser.config.enable_progressive_loading is True

    def test_parser_supported_extensions(self):
        """Test supported file extensions."""
        parser = STLGPUParser()
        extensions = parser.get_supported_extensions()
        assert '.stl' in extensions


class TestGPUHardwareDetection:
    """Test GPU hardware detection and capability assessment."""

    def test_hardware_detection(self):
        """Test hardware acceleration detection."""
        manager = get_acceleration_manager()
        caps = manager.get_capabilities()
        # Should always have at least CPU fallback
        assert AccelBackend.CPU in caps.available_backends

    def test_gpu_accelerator_initialization(self):
        """Test GPU accelerator initialization."""
        accelerator = get_gpu_accelerator()
        assert accelerator is not None

        device_info = accelerator.get_device_info()
        assert 'available' in device_info

    def test_memory_manager_initialization(self):
        """Test GPU memory manager initialization."""
        manager = get_gpu_memory_manager()
        assert manager is not None

        stats = manager.get_memory_stats()
        assert 'allocated_bytes' in stats


class TestGPUParsingBasic:
    """Test basic GPU-accelerated STL parsing functionality."""

    def test_parse_small_binary_stl(self, tmp_path):
        """Test parsing small binary STL file with GPU acceleration."""
        # Create sample STL file
        stl_path = tmp_path / "test_small.stl"
        create_sample_stl_binary(str(stl_path), triangle_count=100)

        parser = STLGPUParser()
        model = parser._parse_file_internal(str(stl_path))

        assert model is not None
        assert model.format_type == ModelFormat.STL
        assert model.stats.triangle_count == 100
        assert model.stats.vertex_count == 300

    def test_parse_large_binary_stl(self, tmp_path):
        """Test parsing large binary STL file."""
        stl_path = tmp_path / "test_large.stl"
        create_large_sample_stl(str(stl_path), triangle_count=50000)

        parser = STLGPUParser()
        start_time = time.time()
        model = parser._parse_file_internal(str(stl_path))
        parse_time = time.time() - start_time

        assert model is not None
        assert model.stats.triangle_count == 50000
        assert model.stats.vertex_count == 150000
        # Should complete within reasonable time (allowing for CPU fallback)
        assert parse_time < 30.0

    def test_parse_ascii_fallback(self, tmp_path):
        """Test that ASCII STL files fall back to CPU parsing."""
        # Create ASCII STL content
        stl_path = tmp_path / "test_ascii.stl"
        ascii_content = """solid test_model
facet normal 0.0 0.0 1.0
outer loop
vertex 0.0 0.0 0.0
vertex 1.0 0.0 0.0
vertex 0.5 1.0 0.0
endloop
endfacet
endsolid test_model
"""
        stl_path.write_text(ascii_content)

        parser = STLGPUParser()
        model = parser._parse_file_internal(str(stl_path))

        assert model is not None
        assert model.stats.triangle_count == 1

    def test_file_validation(self, tmp_path):
        """Test file validation functionality."""
        # Valid file
        stl_path = tmp_path / "test_valid.stl"
        create_sample_stl_binary(str(stl_path), triangle_count=10)

        parser = STLGPUParser()
        is_valid, error_msg = parser.validate_file(str(stl_path))

        assert is_valid is True
        assert error_msg == ""

        # Invalid file
        invalid_path = tmp_path / "nonexistent.stl"
        is_valid, error_msg = parser.validate_file(str(invalid_path))

        assert is_valid is False
        assert "does not exist" in error_msg


class TestGPUProgressiveLoading:
    """Test progressive loading with LOD support."""

    def test_progressive_loader_initialization(self):
        """Test progressive loader initialization."""
        loader = ProgressiveSTLLoader()
        assert loader is not None
        assert loader.config is not None

    def test_lod_configuration(self):
        """Test LOD configuration."""
        config = LODConfig()
        assert len(config.levels) > 0
        assert LODLevel.FULL in config.levels
        assert LODLevel.ULTRA_LOW in config.levels

    def test_progressive_loading_small_file(self, tmp_path):
        """Test progressive loading on small STL file."""
        stl_path = tmp_path / "test_progressive.stl"
        create_sample_stl_binary(str(stl_path), triangle_count=1000)

        loader = ProgressiveSTLLoader()
        lod_model = loader.load_progressive(str(stl_path))

        assert lod_model is not None
        assert len(lod_model.lod_models) > 0
        assert LODLevel.FULL in lod_model.lod_models

        # Check that different LOD levels have different triangle counts
        full_model = lod_model.lod_models[LODLevel.FULL]
        ultra_low_model = lod_model.lod_models[LODLevel.ULTRA_LOW]

        assert full_model.stats.triangle_count >= ultra_low_model.stats.triangle_count

    def test_lod_level_switching(self, tmp_path):
        """Test switching between LOD levels."""
        stl_path = tmp_path / "test_lod_switch.stl"
        create_sample_stl_binary(str(stl_path), triangle_count=1000)

        loader = ProgressiveSTLLoader()
        lod_model = loader.load_progressive(str(stl_path))

        # Test switching to different levels
        original_level = lod_model.current_lod
        lod_model.set_lod_level(LODLevel.ULTRA_LOW)
        assert lod_model.current_lod == LODLevel.ULTRA_LOW

        lod_model.set_lod_level(LODLevel.FULL)
        assert lod_model.current_lod == LODLevel.FULL


class TestGPUErrorHandling:
    """Test error handling and CPU fallback mechanisms."""

    def test_gpu_unavailable_fallback(self, tmp_path):
        """Test fallback when GPU is unavailable."""
        stl_path = tmp_path / "test_fallback.stl"
        create_sample_stl_binary(str(stl_path), triangle_count=100)

        # Mock GPU as unavailable
        with patch('src.core.hardware_acceleration.get_acceleration_manager') as mock_accel:
            mock_caps = Mock()
            mock_caps.recommended_backend = AccelBackend.CPU
            mock_accel.return_value.get_capabilities.return_value = mock_caps

            parser = STLGPUParser()
            model = parser._parse_file_internal(str(stl_path))

            assert model is not None
            assert model.stats.triangle_count == 100

    def test_corrupted_file_handling(self, tmp_path):
        """Test handling of corrupted STL files."""
        stl_path = tmp_path / "test_corrupted.stl"
        # Create corrupted file
        stl_path.write_bytes(b"corrupted data")

        parser = STLGPUParser()

        with pytest.raises(STLGPUParseError):
            parser._parse_file_internal(str(stl_path))

    def test_empty_file_handling(self, tmp_path):
        """Test handling of empty files."""
        stl_path = tmp_path / "test_empty.stl"
        stl_path.write_bytes(b"")

        parser = STLGPUParser()

        with pytest.raises(STLGPUParseError):
            parser._parse_file_internal(str(stl_path))

    def test_parsing_cancellation(self, tmp_path):
        """Test parsing cancellation."""
        stl_path = tmp_path / "test_cancel.stl"
        create_large_sample_stl(str(stl_path), triangle_count=100000)

        parser = STLGPUParser()

        # Start parsing in background
        import threading
        cancel_event = threading.Event()

        def parse_with_cancel():
            try:
                parser._parse_file_internal(str(stl_path))
            except Exception:
                pass  # Expected when cancelled

        parse_thread = threading.Thread(target=parse_with_cancel)
        parse_thread.start()

        # Cancel after short delay
        time.sleep(0.1)
        parser.cancel_parsing()

        parse_thread.join(timeout=5.0)
        assert not parse_thread.is_alive()


class TestGPUPerformanceBenchmarks:
    """Performance benchmarking tests for GPU acceleration."""

    @pytest.mark.benchmark
    def test_small_file_performance(self, tmp_path, benchmark):
        """Benchmark small file parsing performance."""
        stl_path = tmp_path / "bench_small.stl"
        create_sample_stl_binary(str(stl_path), triangle_count=1000)

        parser = STLGPUParser()

        def parse_small():
            return parser._parse_file_internal(str(stl_path))

        result = benchmark(parse_small)
        assert result is not None
        assert result.stats.triangle_count == 1000

    @pytest.mark.benchmark
    def test_medium_file_performance(self, tmp_path, benchmark):
        """Benchmark medium file parsing performance."""
        stl_path = tmp_path / "bench_medium.stl"
        create_sample_stl_binary(str(stl_path), triangle_count=10000)

        parser = STLGPUParser()

        def parse_medium():
            return parser._parse_file_internal(str(stl_path))

        result = benchmark(parse_medium)
        assert result is not None
        assert result.stats.triangle_count == 10000

    def test_memory_usage_stability(self, tmp_path):
        """Test memory usage stability during repeated parsing."""
        stl_path = tmp_path / "test_memory.stl"
        create_sample_stl_binary(str(stl_path), triangle_count=5000)

        parser = STLGPUParser()
        memory_manager = get_gpu_memory_manager()

        initial_stats = memory_manager.get_memory_stats()

        # Parse multiple times
        for i in range(10):
            model = parser._parse_file_internal(str(stl_path))
            assert model is not None

        final_stats = memory_manager.get_memory_stats()

        # Memory usage should be stable (no significant growth)
        growth = final_stats.allocated_bytes - initial_stats.allocated_bytes
        assert growth < 10 * 1024 * 1024  # Less than 10MB growth

    def test_gpu_memory_cleanup(self, tmp_path):
        """Test GPU memory cleanup after parsing."""
        stl_path = tmp_path / "test_cleanup.stl"
        create_sample_stl_binary(str(stl_path), triangle_count=10000)

        parser = STLGPUParser()
        memory_manager = get_gpu_memory_manager()

        # Parse file
        model = parser._parse_file_internal(str(stl_path))
        assert model is not None

        # Force cleanup
        memory_manager.cleanup()

        stats = memory_manager.get_memory_stats()
        assert stats.allocated_bytes == 0


class TestGPUIntegration:
    """Integration tests for GPU acceleration with existing systems."""

    def test_integration_with_original_parser(self, tmp_path):
        """Test that GPU parser integrates properly with original parser interface."""
        from src.parsers.stl_parser_original import STLParser

        stl_path = tmp_path / "test_integration.stl"
        create_sample_stl_binary(str(stl_path), triangle_count=500)

        # Test original parser
        original_parser = STLParser()
        original_model = original_parser._parse_file_internal(str(stl_path))

        # Test GPU parser
        gpu_parser = STLGPUParser()
        gpu_model = gpu_parser._parse_file_internal(str(stl_path))

        # Both should produce valid models with same triangle count
        assert original_model is not None
        assert gpu_model is not None
        assert original_model.stats.triangle_count == gpu_model.stats.triangle_count == 500

    def test_progress_callback_integration(self, tmp_path):
        """Test progress callback integration."""
        stl_path = tmp_path / "test_progress.stl"
        create_large_sample_stl(str(stl_path), triangle_count=50000)

        parser = STLGPUParser()

        progress_calls = []
        def progress_callback(progress: float, message: str):
            progress_calls.append((progress, message))

        model = parser._parse_file_internal(str(stl_path), progress_callback)

        assert model is not None
        assert len(progress_calls) > 0
        assert progress_calls[-1][0] == 100.0  # Should end at 100%

    def test_performance_stats_tracking(self, tmp_path):
        """Test performance statistics tracking."""
        stl_path = tmp_path / "test_stats.stl"
        create_sample_stl_binary(str(stl_path), triangle_count=1000)

        parser = STLGPUParser()
        model = parser._parse_file_internal(str(stl_path))

        stats = parser.performance_stats
        assert 'total_time' in stats
        assert 'gpu_time' in stats
        assert 'cpu_time' in stats
        assert stats['total_time'] > 0


# Helper fixtures and utilities
@pytest.fixture
def sample_stl_file(tmp_path):
    """Create a sample STL file for testing."""
    stl_path = tmp_path / "sample.stl"
    create_sample_stl_binary(str(stl_path), triangle_count=100)
    return str(stl_path)


@pytest.fixture
def large_stl_file(tmp_path):
    """Create a large STL file for testing."""
    stl_path = tmp_path / "large.stl"
    create_large_sample_stl(str(stl_path), triangle_count=50000)
    return str(stl_path)