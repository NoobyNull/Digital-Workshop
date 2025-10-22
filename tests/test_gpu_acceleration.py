"""
Unit tests for GPU acceleration framework.

This module tests the GPU acceleration components including device detection,
memory management, and kernel execution.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from src.core.gpu_acceleration import (
    GPUAccelerator, GPUBackend, GPUCapability, GPUDevice,
    GPUBuffer, GPUAccelerationError, TriangleProcessingKernel,
    get_gpu_accelerator
)


class TestGPUDevice:
    """Test GPU device information and capabilities."""

    def test_device_creation(self):
        """Test creating a GPU device."""
        device = GPUDevice(
            backend=GPUBackend.CUDA,
            device_id=0,
            name="Test GPU",
            memory_gb=8.0,
            compute_capability=7.5,
            capability_level=GPUCapability.HIGH_END
        )

        assert device.backend == GPUBackend.CUDA
        assert device.device_id == 0
        assert device.name == "Test GPU"
        assert device.memory_gb == 8.0
        assert device.compute_capability == 7.5
        assert device.capability_level == GPUCapability.HIGH_END
        assert device.is_available is True

    def test_device_availability(self):
        """Test device availability checks."""
        available_device = GPUDevice(
            backend=GPUBackend.CUDA,
            device_id=0,
            name="Available GPU",
            memory_gb=4.0,
            compute_capability=6.0,
            capability_level=GPUCapability.ADVANCED
        )

        unavailable_device = GPUDevice(
            backend=GPUBackend.CUDA,
            device_id=0,
            name="Unavailable GPU",
            memory_gb=2.0,
            compute_capability=0.0,
            capability_level=GPUCapability.NONE
        )

        assert available_device.is_available is True
        assert unavailable_device.is_available is False


class TestGPUBuffer:
    """Test GPU buffer memory management."""

    def test_buffer_creation(self):
        """Test creating a GPU buffer."""
        device = GPUDevice(
            backend=GPUBackend.CUDA,
            device_id=0,
            name="Test GPU",
            memory_gb=8.0,
            compute_capability=7.5,
            capability_level=GPUCapability.HIGH_END
        )

        buffer = GPUBuffer(1024, device)
        assert buffer.size_bytes == 1024
        assert buffer.device == device
        assert buffer._allocated is False

    @patch('src.core.gpu_acceleration.GPUBuffer._allocate_cuda')
    def test_cuda_allocation(self, mock_allocate):
        """Test CUDA buffer allocation."""
        mock_allocate.return_value = None

        device = GPUDevice(
            backend=GPUBackend.CUDA,
            device_id=0,
            name="CUDA GPU",
            memory_gb=8.0,
            compute_capability=7.5,
            capability_level=GPUCapability.HIGH_END
        )

        buffer = GPUBuffer(1024, device)
        result = buffer.allocate()

        assert result is True
        assert buffer._allocated is True
        mock_allocate.assert_called_once()

    def test_cpu_fallback_allocation(self):
        """Test CPU fallback buffer allocation."""
        device = GPUDevice(
            backend=GPUBackend.CPU,
            device_id=0,
            name="CPU Fallback",
            memory_gb=0.0,
            compute_capability=0.0,
            capability_level=GPUCapability.BASIC
        )

        buffer = GPUBuffer(1024, device)
        result = buffer.allocate()

        assert result is True
        assert buffer._allocated is True
        assert isinstance(buffer._buffer, bytearray)
        assert len(buffer._buffer) == 1024

    def test_cpu_buffer_operations(self):
        """Test CPU buffer read/write operations."""
        device = GPUDevice(
            backend=GPUBackend.CPU,
            device_id=0,
            name="CPU Fallback",
            memory_gb=0.0,
            compute_capability=0.0,
            capability_level=GPUCapability.BASIC
        )

        buffer = GPUBuffer(1024, device)
        buffer.allocate()

        # Test copy to device
        test_data = b"Hello GPU"
        result = buffer.copy_to_device(test_data, 0)
        assert result is True

        # Test copy from device
        read_data = buffer.copy_from_device(len(test_data), 0)
        assert read_data == test_data

    def test_buffer_free(self):
        """Test buffer cleanup."""
        device = GPUDevice(
            backend=GPUBackend.CPU,
            device_id=0,
            name="CPU Fallback",
            memory_gb=0.0,
            compute_capability=0.0,
            capability_level=GPUCapability.BASIC
        )

        buffer = GPUBuffer(1024, device)
        buffer.allocate()
        assert buffer._allocated is True

        buffer.free()
        assert buffer._allocated is False
        assert buffer._buffer is None


class TestTriangleProcessingKernel:
    """Test triangle processing GPU kernel."""

    def test_kernel_creation(self):
        """Test creating a triangle processing kernel."""
        device = GPUDevice(
            backend=GPUBackend.CUDA,
            device_id=0,
            name="Test GPU",
            memory_gb=8.0,
            compute_capability=7.5,
            capability_level=GPUCapability.HIGH_END
        )

        kernel = TriangleProcessingKernel(device)
        assert kernel.device == device
        assert kernel._compiled is False

    @patch('src.core.gpu_acceleration.TriangleProcessingKernel._compile_cuda')
    def test_cuda_compilation(self, mock_compile):
        """Test CUDA kernel compilation."""
        mock_compile.return_value = True

        device = GPUDevice(
            backend=GPUBackend.CUDA,
            device_id=0,
            name="CUDA GPU",
            memory_gb=8.0,
            compute_capability=7.5,
            capability_level=GPUCapability.HIGH_END
        )

        kernel = TriangleProcessingKernel(device)
        result = kernel.compile()

        assert result is True
        assert kernel._compiled is True
        mock_compile.assert_called_once()

    def test_cpu_fallback_compilation(self):
        """Test CPU fallback kernel compilation."""
        device = GPUDevice(
            backend=GPUBackend.CPU,
            device_id=0,
            name="CPU Fallback",
            memory_gb=0.0,
            compute_capability=0.0,
            capability_level=GPUCapability.BASIC
        )

        kernel = TriangleProcessingKernel(device)
        result = kernel.compile()

        assert result is True
        assert kernel._compiled is True

    def test_cpu_kernel_execution(self):
        """Test CPU kernel execution."""
        device = GPUDevice(
            backend=GPUBackend.CPU,
            device_id=0,
            name="CPU Fallback",
            memory_gb=0.0,
            compute_capability=0.0,
            capability_level=GPUCapability.BASIC
        )

        kernel = TriangleProcessingKernel(device)
        kernel.compile()

        buffers = []
        params = {"triangle_count": 1000}

        result = kernel.execute(buffers, params)
        assert result is True


class TestGPUAccelerator:
    """Test main GPU accelerator functionality."""

    @patch('src.core.gpu_acceleration.GPUAccelerator._detect_cuda_devices')
    @patch('src.core.gpu_acceleration.GPUAccelerator._detect_opencl_devices')
    def test_device_detection(self, mock_opencl, mock_cuda):
        """Test GPU device detection."""
        mock_cuda.return_value = [
            GPUDevice(
                backend=GPUBackend.CUDA,
                device_id=0,
                name="NVIDIA RTX 3080",
                memory_gb=10.0,
                compute_capability=8.6,
                capability_level=GPUCapability.HIGH_END
            )
        ]
        mock_opencl.return_value = []

        accelerator = GPUAccelerator()

        assert len(accelerator.devices) == 2  # CUDA device + CPU fallback
        assert accelerator.devices[0].backend == GPUBackend.CUDA
        assert accelerator.devices[0].name == "NVIDIA RTX 3080"
        assert accelerator.active_device == accelerator.devices[0]

    @patch('src.core.gpu_acceleration.GPUAccelerator._detect_cuda_devices')
    @patch('src.core.gpu_acceleration.GPUAccelerator._detect_opencl_devices')
    def test_cpu_fallback_only(self, mock_opencl, mock_cuda):
        """Test CPU fallback when no GPU available."""
        mock_cuda.return_value = []
        mock_opencl.return_value = []

        accelerator = GPUAccelerator()

        assert len(accelerator.devices) == 1  # Only CPU fallback
        assert accelerator.devices[0].backend == GPUBackend.CPU
        assert accelerator.active_device == accelerator.devices[0]

    def test_buffer_allocation(self):
        """Test buffer allocation through accelerator."""
        accelerator = GPUAccelerator()

        buffer = accelerator.allocate_buffer(1024)
        assert buffer is not None
        assert buffer.size_bytes == 1024
        assert buffer in accelerator.buffers

    def test_kernel_creation(self):
        """Test kernel creation through accelerator."""
        accelerator = GPUAccelerator()

        kernel = accelerator.create_kernel("triangle_processing")
        assert kernel is not None
        assert isinstance(kernel, TriangleProcessingKernel)
        assert kernel in accelerator.kernels.values()

    def test_kernel_execution(self):
        """Test kernel execution through accelerator."""
        accelerator = GPUAccelerator()

        buffers = []
        params = {"triangle_count": 500}

        result = accelerator.execute_kernel("triangle_processing", buffers, params)
        assert result is True

    def test_device_info(self):
        """Test getting device information."""
        accelerator = GPUAccelerator()

        info = accelerator.get_device_info()
        assert "available" in info
        assert "backend" in info
        assert "name" in info
        assert "memory_gb" in info

    def test_cleanup(self):
        """Test accelerator cleanup."""
        accelerator = GPUAccelerator()

        # Allocate some resources
        buffer = accelerator.allocate_buffer(1024)
        kernel = accelerator.create_kernel("triangle_processing")

        assert len(accelerator.buffers) > 0
        assert len(accelerator.kernels) > 0

        accelerator.cleanup()

        assert len(accelerator.buffers) == 0
        assert len(accelerator.kernels) == 0


class TestGlobalFunctions:
    """Test global GPU accelerator functions."""

    def test_get_gpu_accelerator(self):
        """Test getting the global GPU accelerator instance."""
        accelerator1 = get_gpu_accelerator()
        accelerator2 = get_gpu_accelerator()

        # Should return the same instance
        assert accelerator1 is accelerator2
        assert isinstance(accelerator1, GPUAccelerator)


if __name__ == "__main__":
    pytest.main([__file__])