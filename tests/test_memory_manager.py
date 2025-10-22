"""
Unit tests for memory management system.

This module tests the memory management components including monitoring,
pool allocation, and adaptive memory management.
"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from src.core.memory_manager import (
    MemoryManager, MemoryMonitor, MemoryPool, MemoryStats, MemoryPressure,
    get_memory_manager
)


class TestMemoryStats:
    """Test memory statistics functionality."""

    def test_memory_stats_creation(self):
        """Test creating memory statistics."""
        stats = MemoryStats(
            total_memory_gb=16.0,
            available_memory_gb=8.0,
            used_memory_gb=8.0,
            memory_percent=50.0,
            gpu_memory_used_gb=2.0,
            gpu_memory_total_gb=8.0,
            pressure_level=MemoryPressure.MEDIUM
        )

        assert stats.total_memory_gb == 16.0
        assert stats.available_memory_gb == 8.0
        assert stats.used_memory_gb == 8.0
        assert stats.memory_percent == 50.0
        assert stats.gpu_memory_used_gb == 2.0
        assert stats.gpu_memory_total_gb == 8.0
        assert stats.pressure_level == MemoryPressure.MEDIUM
        assert stats.available_ratio == 0.5
        assert stats.is_memory_constrained is False

    def test_memory_pressure_detection(self):
        """Test memory pressure level detection."""
        low_pressure = MemoryStats(16, 12, 4, 25)
        assert low_pressure.pressure_level == MemoryPressure.LOW
        assert not low_pressure.is_memory_constrained

        high_pressure = MemoryStats(16, 3, 13, 81)
        assert high_pressure.pressure_level == MemoryPressure.HIGH
        assert high_pressure.is_memory_constrained

        critical_pressure = MemoryStats(16, 1, 15, 94)
        assert critical_pressure.pressure_level == MemoryPressure.CRITICAL
        assert critical_pressure.is_memory_constrained


class TestMemoryPool:
    """Test memory pool allocation."""

    def test_pool_creation(self):
        """Test creating a memory pool."""
        pool = MemoryPool(block_size_mb=32, max_blocks=5)
        assert pool.block_size_bytes == 32 * 1024 * 1024
        assert pool.max_blocks == 5
        assert len(pool.allocated_blocks) == 0
        assert len(pool.available_blocks) == 0

    def test_pool_allocation(self):
        """Test allocating from memory pool."""
        pool = MemoryPool(block_size_mb=1, max_blocks=3)  # Small blocks for testing

        # First allocation
        block1 = pool.allocate(1024)
        assert block1 is not None
        assert len(block1) >= 1024
        assert len(pool.allocated_blocks) == 1
        assert len(pool.available_blocks) == 0

        # Second allocation
        block2 = pool.allocate(1024)
        assert block2 is not None
        assert len(pool.allocated_blocks) == 2

        # Free first block
        pool.free(block1)
        assert len(pool.allocated_blocks) == 2
        assert len(pool.available_blocks) == 1

        # Allocate again (should reuse)
        block3 = pool.allocate(1024)
        assert block3 is block1  # Should reuse freed block
        assert len(pool.available_blocks) == 0

    def test_pool_limit(self):
        """Test memory pool limits."""
        pool = MemoryPool(block_size_mb=1, max_blocks=2)

        # Allocate up to limit
        block1 = pool.allocate(1024)
        block2 = pool.allocate(1024)
        assert block1 is not None
        assert block2 is not None

        # Try to allocate beyond limit
        block3 = pool.allocate(1024)
        assert block3 is None

        # Free one and try again
        pool.free(block1)
        block4 = pool.allocate(1024)
        assert block4 is block1

    def test_pool_cleanup(self):
        """Test pool cleanup."""
        pool = MemoryPool(block_size_mb=1, max_blocks=3)

        # Allocate some blocks
        block1 = pool.allocate(1024)
        block2 = pool.allocate(1024)

        assert len(pool.allocated_blocks) == 2

        pool.cleanup()

        assert len(pool.allocated_blocks) == 0
        assert len(pool.available_blocks) == 0


class TestMemoryMonitor:
    """Test memory monitoring functionality."""

    @patch('psutil.virtual_memory')
    def test_memory_update(self, mock_virtual_memory):
        """Test memory statistics updates."""
        # Mock psutil response
        mock_mem = Mock()
        mock_mem.total = 16 * 1024**3  # 16GB
        mock_mem.available = 8 * 1024**3  # 8GB
        mock_mem.used = 8 * 1024**3  # 8GB
        mock_mem.percent = 50.0
        mock_virtual_memory.return_value = mock_mem

        monitor = MemoryMonitor(update_interval_seconds=0.1)

        # Manually trigger update
        monitor._update_stats()

        stats = monitor.get_memory_stats()
        assert stats.total_memory_gb == 16.0
        assert stats.available_memory_gb == 8.0
        assert stats.used_memory_gb == 8.0
        assert stats.memory_percent == 50.0
        assert stats.pressure_level == MemoryPressure.MEDIUM

    def test_pressure_callbacks(self):
        """Test memory pressure callbacks."""
        monitor = MemoryMonitor(update_interval_seconds=0.1)

        callback_called = []

        def test_callback(stats):
            callback_called.append(stats.pressure_level)

        monitor.add_pressure_callback(test_callback)

        # Simulate pressure change
        monitor._stats.pressure_level = MemoryPressure.HIGH
        monitor._check_pressure_levels()

        # Callback should be called during next update
        monitor._update_stats()
        assert len(callback_called) > 0

        monitor.remove_pressure_callback(test_callback)

    def test_monitor_lifecycle(self):
        """Test monitor start/stop."""
        monitor = MemoryMonitor(update_interval_seconds=0.1)

        assert not monitor._monitoring

        monitor.start_monitoring()
        assert monitor._monitoring
        assert monitor._monitor_thread is not None
        assert monitor._monitor_thread.is_alive()

        monitor.stop_monitoring()
        assert not monitor._monitoring
        # Thread should be stopped


class TestMemoryManager:
    """Test comprehensive memory management."""

    def test_manager_creation(self):
        """Test creating memory manager."""
        manager = MemoryManager(max_memory_gb=4.0)

        assert manager.max_memory_gb == 4.0
        assert isinstance(manager.monitor, MemoryMonitor)
        assert isinstance(manager.memory_pool, MemoryPool)

    @patch('src.core.memory_manager.MemoryManager._detect_system_memory')
    def test_system_memory_detection(self, mock_detect):
        """Test system memory detection."""
        mock_detect.return_value = 32.0

        manager = MemoryManager()
        assert manager.system_memory_gb == 32.0

    def test_memory_allocation(self):
        """Test memory allocation through manager."""
        manager = MemoryManager(max_memory_gb=1.0)  # 1GB limit

        # Allocate small block
        block = manager.allocate_memory(1024, "test")
        assert block is not None
        assert len(block) >= 1024

        # Check tracking
        summary = manager.get_allocation_summary()
        assert summary["total_allocated_bytes"] >= 1024
        assert "test" in summary["owners"]

        # Free memory
        manager.free_memory(block, "test")

        # Check tracking updated
        summary2 = manager.get_allocation_summary()
        assert summary2["total_allocated_bytes"] < summary["total_allocated_bytes"]

    def test_memory_limits(self):
        """Test memory allocation limits."""
        manager = MemoryManager(max_memory_gb=0.001)  # Very small limit (~1MB)

        # Try to allocate large block
        large_block = manager.allocate_memory(2 * 1024 * 1024, "large")  # 2MB
        assert large_block is None  # Should fail due to limit

    def test_maintenance_cleanup(self):
        """Test maintenance cleanup."""
        manager = MemoryManager()

        # Allocate some memory
        block1 = manager.allocate_memory(1024, "test1")
        block2 = manager.allocate_memory(1024, "test2")

        initial_allocated = manager.get_allocation_summary()["total_allocated_bytes"]

        # Run maintenance cleanup
        cleanup_count = manager.maintenance_cleanup()

        # Memory should still be allocated (maintenance doesn't free user memory)
        final_allocated = manager.get_allocation_summary()["total_allocated_bytes"]
        assert final_allocated == initial_allocated

        # Clean up
        manager.free_memory(block1, "test1")
        manager.free_memory(block2, "test2")

    def test_force_cleanup(self):
        """Test force cleanup under pressure."""
        manager = MemoryManager()

        # Simulate memory pressure
        manager.monitor._stats.pressure_level = MemoryPressure.CRITICAL

        cleanup_count = manager.force_cleanup()
        # Force cleanup should perform garbage collection
        assert cleanup_count >= 0

    def test_memory_limit_checks(self):
        """Test memory limit validation."""
        manager = MemoryManager(max_memory_gb=2.0)

        # Should allow allocation within limits
        assert manager.check_memory_limits(1.0) is True

        # Should reject allocation over limits
        assert manager.check_memory_limits(3.0) is False


class TestGlobalFunctions:
    """Test global memory manager functions."""

    def test_get_memory_manager(self):
        """Test getting the global memory manager instance."""
        manager1 = get_memory_manager()
        manager2 = get_memory_manager()

        # Should return the same instance
        assert manager1 is manager2
        assert isinstance(manager1, MemoryManager)


if __name__ == "__main__":
    pytest.main([__file__])