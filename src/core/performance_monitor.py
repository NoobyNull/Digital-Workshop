"""
Performance monitoring system for Digital Workshop.

This module provides comprehensive performance monitoring capabilities including
memory usage tracking, operation timing, bottleneck identification, and
adaptive performance optimization based on system capabilities.
"""

import gc
import logging
import os
import psutil
import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
import json

from .logging_config import get_logger


class PerformanceLevel(Enum):
    """Performance levels for adaptive optimization."""
    MINIMAL = "minimal"      # Low-end systems
    STANDARD = "standard"    # Mid-range systems
    HIGH = "high"           # High-end systems
    ULTRA = "ultra"         # High-end systems with plenty of resources


@dataclass
class MemoryStats:
    """Memory usage statistics."""
    total_mb: float
    used_mb: float
    available_mb: float
    percent_used: float
    process_mb: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class OperationMetrics:
    """Metrics for a specific operation."""
    operation_name: str
    start_time: float
    end_time: float
    duration_ms: float
    memory_before_mb: float
    memory_after_mb: float
    memory_peak_mb: float
    success: bool
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceProfile:
    """Performance profile for system capabilities."""
    performance_level: PerformanceLevel
    max_memory_mb: float
    recommended_cache_size_mb: float
    max_triangles_for_full_quality: int
    adaptive_quality_enabled: bool
    background_thread_count: int
    chunk_size: int


class PerformanceMonitor:
    """
    Performance monitoring system for tracking and optimizing application performance.

    Features:
    - Real-time memory usage monitoring
    - Operation timing and bottleneck identification
    - Adaptive performance optimization based on hardware capabilities
    - Performance logging and analysis
    - Memory leak detection
    """

    def __init__(self):
        """Initialize the performance monitor."""
        self.logger = get_logger(__name__)
        self.logger.info("Initializing performance monitor")

        # Monitoring state
        self.is_monitoring = False
        self.monitoring_thread = None
        self.monitoring_interval = 1.0  # seconds
        self.memory_history = []
        self.max_history_size = 1000

        # Operation tracking
        self.active_operations = {}
        self.completed_operations = []
        self.max_operations_history = 500

        # Performance profile
        self.performance_profile = self._detect_system_capabilities()

        # Performance thresholds
        self.memory_warning_threshold = 80.0  # percent
        self.memory_critical_threshold = 90.0  # percent
        self.operation_slow_threshold = 5.0  # seconds

        # Callbacks for performance events
        self.memory_warning_callback = None
        self.memory_critical_callback = None
        self.slow_operation_callback = None

        self.logger.info(f"Performance monitor initialized with {self.performance_profile.performance_level.value} profile")

    def _detect_gpu_info(self) -> Dict[str, Any]:
        """
        Detect GPU information including VRAM with improved fallback detection.

        Returns:
            Dictionary with GPU info: has_dedicated_gpu, vram_mb, gpu_name
        """
        try:
            # First try hardware acceleration manager
            from src.core.hardware_acceleration import get_acceleration_manager
            accelerator = get_acceleration_manager()
            caps = accelerator.get_capabilities()

            # Check if we have detected devices from hardware acceleration
            if caps.devices:
                # Use the first detected device
                device = caps.devices[0]
                return {
                    'has_dedicated_gpu': device.backend.value != 'cpu',
                    'vram_mb': device.memory_mb or 0,
                    'gpu_name': f"{device.vendor} {device.name}" if device.vendor else device.name
                }

            # Check for CUDA with PyTorch as fallback
            try:
                import torch
                if torch.cuda.is_available():
                    vram_mb = int(torch.cuda.get_device_properties(0).total_memory / (1024 ** 2))
                    gpu_name = torch.cuda.get_device_name(0)
                    return {
                        'has_dedicated_gpu': True,
                        'vram_mb': vram_mb,
                        'gpu_name': gpu_name
                    }
            except Exception:
                pass

            # Try WMI for Windows GPU detection
            try:
                import wmi
                gpu_list = wmi.WMI().Win32_VideoController()
                for gpu in gpu_list:
                    if gpu.Name and gpu.Name.strip():
                        # Check if it's a dedicated GPU
                        name_lower = gpu.Name.lower()
                        is_dedicated = any(x in name_lower for x in [
                            'nvidia', 'geforce', 'gtx', 'rtx', 'amd', 'radeon', 'rx ', 'vega'
                        ])
                        
                        # Try to get video memory
                        vram_mb = None
                        if hasattr(gpu, 'AdapterRAM') and gpu.AdapterRAM:
                            try:
                                vram_mb = int(gpu.AdapterRAM) // (1024 * 1024)
                            except Exception:
                                pass
                        
                        # If no dedicated memory info, estimate based on system RAM
                        if vram_mb is None:
                            memory = psutil.virtual_memory()
                            if is_dedicated:
                                vram_mb = int(memory.total / (1024 ** 2) * 0.1)  # 10% for dedicated
                            else:
                                vram_mb = int(memory.total / (1024 ** 2) * 0.25)  # 25% for integrated
                        
                        return {
                            'has_dedicated_gpu': is_dedicated,
                            'vram_mb': vram_mb,
                            'gpu_name': gpu.Name.strip()
                        }
            except Exception:
                pass

            # Try system information via registry (Windows)
            try:
                if platform.system() == "Windows":
                    import winreg
                    try:
                        # Try to get GPU info from registry
                        registry = winreg.ConnectRegistry(None, winreg.HKEY_LOCAL_MACHINE)
                        key = winreg.OpenKey(registry, r"SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}")
                        # This is complex, so we'll just fall through to the final fallback
                        winreg.CloseKey(key)
                    except Exception:
                        pass
            except Exception:
                pass

            # Final fallback: use system memory to estimate
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024 ** 3)
            
            # Make educated guess based on system memory
            if total_gb >= 32:
                # High-end system likely has dedicated GPU
                estimated_vram = 8192  # 8GB
                gpu_type = "Dedicated GPU (Estimated)"
            elif total_gb >= 16:
                # Mid-range system, might have dedicated GPU
                estimated_vram = 4096  # 4GB
                gpu_type = "Dedicated GPU (Estimated)"
            else:
                # Lower-end system, likely integrated
                estimated_vram = int(memory.total / (1024 ** 2) * 0.25)
                gpu_type = "Integrated GPU (Estimated)"
            
            return {
                'has_dedicated_gpu': total_gb >= 16,
                'vram_mb': estimated_vram,
                'gpu_name': gpu_type
            }
            
        except Exception as e:
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"Failed to detect GPU info: {e}")
            # Absolute fallback
            memory = psutil.virtual_memory()
            return {
                'has_dedicated_gpu': False,
                'vram_mb': int(memory.total / (1024 ** 2) * 0.25),
                'gpu_name': 'Unknown GPU'
            }

    def _detect_system_capabilities(self) -> PerformanceProfile:
        """
        Detect system capabilities and create appropriate performance profile.

        Returns:
            Performance profile based on system capabilities
        """
        try:
            # Get system memory
            memory = psutil.virtual_memory()
            total_memory_mb = int(memory.total / (1024 ** 2))
            available_memory_mb = int(memory.available / (1024 ** 2))
            total_memory_gb = memory.total / (1024 ** 3)

            # Get CPU info
            cpu_count = psutil.cpu_count()

            # Get GPU info
            gpu_info = self._detect_gpu_info()

            # Use smart memory calculation from ApplicationConfig
            from .application_config import ApplicationConfig
            config = ApplicationConfig.get_default()
            max_memory_mb = config.get_effective_memory_limit_mb(
                available_memory_mb=available_memory_mb,
                total_system_memory_mb=total_memory_mb
            )

            # Determine performance level
            if total_memory_gb < 4 or cpu_count < 4:
                performance_level = PerformanceLevel.MINIMAL
                cache_size_mb = 100
                max_triangles = 50000
                thread_count = 2
                chunk_size = 1000
            elif total_memory_gb < 8 or cpu_count < 8:
                performance_level = PerformanceLevel.STANDARD
                cache_size_mb = 256
                max_triangles = 100000
                thread_count = 4
                chunk_size = 5000
            elif total_memory_gb < 16 or cpu_count < 16:
                performance_level = PerformanceLevel.HIGH
                cache_size_mb = 512
                max_triangles = 500000
                thread_count = 8
                chunk_size = 10000
            else:
                performance_level = PerformanceLevel.ULTRA
                cache_size_mb = 1024
                max_triangles = 1000000
                thread_count = min(16, cpu_count)
                chunk_size = 20000

            profile = PerformanceProfile(
                performance_level=performance_level,
                max_memory_mb=max_memory_mb,
                recommended_cache_size_mb=cache_size_mb,
                max_triangles_for_full_quality=max_triangles,
                adaptive_quality_enabled=performance_level != PerformanceLevel.ULTRA,
                background_thread_count=thread_count,
                chunk_size=chunk_size
            )

            self.logger.info(
                f"Detected system: {total_memory_gb:.1f}GB RAM ({available_memory_mb}MB available), "
                f"{cpu_count} CPU cores, GPU: {gpu_info['gpu_name']} ({gpu_info['vram_mb']}MB VRAM), "
                f"performance level: {performance_level.value}, "
                f"memory limit: {max_memory_mb}MB"
            )

            return profile

        except Exception as e:
            self.logger.error(f"Failed to detect system capabilities: {str(e)}")
            # Return conservative default profile
            return PerformanceProfile(
                performance_level=PerformanceLevel.MINIMAL,
                max_memory_mb=1024,
                recommended_cache_size_mb=100,
                max_triangles_for_full_quality=50000,
                adaptive_quality_enabled=True,
                background_thread_count=2,
                chunk_size=1000
            )

    def start_monitoring(self) -> None:
        """Start performance monitoring in background thread."""
        if self.is_monitoring:
            self.logger.warning("Performance monitoring is already running")
            return

        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("Performance monitoring started")

    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        if not self.is_monitoring:
            return

        self.is_monitoring = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
        self.logger.info("Performance monitoring stopped")

    def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self.is_monitoring:
            try:
                # Record memory stats
                memory_stats = self._get_memory_stats()
                self.memory_history.append(memory_stats)

                # Trim history if needed
                if len(self.memory_history) > self.max_history_size:
                    self.memory_history = self.memory_history[-self.max_history_size:]

                # Check memory thresholds
                if memory_stats.percent_used >= self.memory_critical_threshold:
                    self.logger.critical(
                        f"Critical memory usage: {memory_stats.percent_used:.1f}% "
                        f"({memory_stats.used_mb:.1f}MB used)"
                    )
                    if self.memory_critical_callback:
                        self.memory_critical_callback(memory_stats)
                elif memory_stats.percent_used >= self.memory_warning_threshold:
                    self.logger.warning(
                        f"High memory usage: {memory_stats.percent_used:.1f}% "
                        f"({memory_stats.used_mb:.1f}MB used)"
                    )
                    if self.memory_warning_callback:
                        self.memory_warning_callback(memory_stats)

                # Sleep until next iteration
                time.sleep(self.monitoring_interval)

            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {str(e)}")
                time.sleep(self.monitoring_interval)

    def _get_memory_stats(self) -> MemoryStats:
        """
        Get current memory statistics.

        Returns:
            Current memory statistics
        """
        try:
            # System memory
            memory = psutil.virtual_memory()

            # Process memory
            process = psutil.Process()
            process_memory = process.memory_info().rss / (1024 * 1024)  # MB

            return MemoryStats(
                total_mb=memory.total / (1024 * 1024),
                used_mb=memory.used / (1024 * 1024),
                available_mb=memory.available / (1024 * 1024),
                percent_used=memory.percent,
                process_mb=process_memory
            )

        except Exception as e:
            self.logger.error(f"Failed to get memory stats: {str(e)}")
            return MemoryStats(0, 0, 0, 0, 0)

    def start_operation(self, operation_name: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start tracking an operation.

        Args:
            operation_name: Name of the operation
            metadata: Optional metadata about the operation

        Returns:
            Operation ID for tracking
        """
        operation_id = f"{operation_name}_{int(time.time() * 1000000)}"

        memory_before = self._get_memory_stats().process_mb

        self.active_operations[operation_id] = {
            'operation_name': operation_name,
            'start_time': time.time(),
            'memory_before_mb': memory_before,
            'memory_peak_mb': memory_before,
            'metadata': metadata or {}
        }

        if self.logger.isEnabledFor(logging.DEBUG):
            self.logger.debug(f"Started tracking operation: {operation_name} (ID: {operation_id})")
        return operation_id

    def end_operation(self, operation_id: str, success: bool = True,
                     error_message: Optional[str] = None) -> Optional[OperationMetrics]:
        """
        End tracking an operation and record metrics.

        Args:
            operation_id: ID of the operation to end
            success: Whether the operation was successful
            error_message: Error message if operation failed

        Returns:
            Operation metrics if found, None otherwise
        """
        if operation_id not in self.active_operations:
            self.logger.warning(f"Operation ID not found: {operation_id}")
            return None

        operation = self.active_operations.pop(operation_id)
        end_time = time.time()
        memory_after = self._get_memory_stats().process_mb

        # Calculate metrics
        duration_ms = (end_time - operation['start_time']) * 1000
        memory_peak = max(operation['memory_peak_mb'], memory_after)

        metrics = OperationMetrics(
            operation_name=operation['operation_name'],
            start_time=operation['start_time'],
            end_time=end_time,
            duration_ms=duration_ms,
            memory_before_mb=operation['memory_before_mb'],
            memory_after_mb=memory_after,
            memory_peak_mb=memory_peak,
            success=success,
            error_message=error_message,
            metadata=operation['metadata']
        )

        # Store in completed operations
        self.completed_operations.append(metrics)
        if len(self.completed_operations) > self.max_operations_history:
            self.completed_operations = self.completed_operations[-self.max_operations_history:]

        # Log operation completion
        if success:
            self.logger.info(
                f"Operation completed: {metrics.operation_name} in {duration_ms:.1f}ms, "
                f"memory delta: {memory_after - operation['memory_before_mb']:.1f}MB"
            )
        else:
            self.logger.error(
                f"Operation failed: {metrics.operation_name} after {duration_ms:.1f}ms, "
                f"error: {error_message}"
            )

        # Check for slow operations
        duration_seconds = duration_ms / 1000
        if duration_seconds > self.operation_slow_threshold:
            self.logger.warning(
                f"Slow operation detected: {metrics.operation_name} took {duration_seconds:.2f}s"
            )
            if self.slow_operation_callback:
                self.slow_operation_callback(metrics)

        return metrics

    def update_operation_peak_memory(self, operation_id: str) -> None:
        """
        Update the peak memory usage for an active operation.

        Args:
            operation_id: ID of the operation
        """
        if operation_id in self.active_operations:
            current_memory = self._get_memory_stats().process_mb
            self.active_operations[operation_id]['memory_peak_mb'] = max(
                self.active_operations[operation_id]['memory_peak_mb'],
                current_memory
            )

    def get_current_memory_stats(self) -> MemoryStats:
        """
        Get current memory statistics.

        Returns:
            Current memory statistics
        """
        return self._get_memory_stats()

    def get_performance_profile(self) -> PerformanceProfile:
        """
        Get the current performance profile.

        Returns:
            Current performance profile
        """
        return self.performance_profile

    def get_performance_report(self) -> Dict[str, Any]:
        """
        Get comprehensive performance report for viewer widget integration.
        
        Returns:
            Dictionary containing system information and performance profile
        """
        try:
            # Get current memory stats
            memory_stats = self._get_memory_stats()
            
            # Create system info dictionary
            system_info = {
                'memory_total_gb': memory_stats.total_mb / 1024.0,
                'memory_available_gb': memory_stats.available_mb / 1024.0,
                'memory_used_percent': memory_stats.percent_used,
                'process_memory_mb': memory_stats.process_mb,
                'performance_level': self.performance_profile.performance_level.value,
                'cpu_count': psutil.cpu_count(),
            }
            
            # Create performance report
            report = {
                'system_info': system_info,
                'performance_profile': {
                    'performance_level': self.performance_profile.performance_level.value,
                    'max_memory_mb': self.performance_profile.max_memory_mb,
                    'recommended_cache_size_mb': self.performance_profile.recommended_cache_size_mb,
                    'max_triangles_for_full_quality': self.performance_profile.max_triangles_for_full_quality,
                    'adaptive_quality_enabled': self.performance_profile.adaptive_quality_enabled,
                    'background_thread_count': self.performance_profile.background_thread_count,
                    'chunk_size': self.performance_profile.chunk_size,
                },
                'current_stats': {
                    'memory_percent': memory_stats.percent_used,
                    'process_memory_mb': memory_stats.process_mb,
                    'active_operations': len(self.active_operations),
                    'completed_operations': len(self.completed_operations),
                }
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Failed to generate performance report: {str(e)}")
            # Return fallback report
            return {
                'system_info': {
                    'memory_total_gb': 8.0,
                    'memory_available_gb': 4.0,
                    'memory_used_percent': 50.0,
                    'process_memory_mb': 100.0,
                    'performance_level': 'standard',
                    'cpu_count': 4,
                },
                'performance_profile': {
                    'performance_level': 'standard',
                    'max_memory_mb': 2048,
                    'recommended_cache_size_mb': 256,
                    'max_triangles_for_full_quality': 100000,
                    'adaptive_quality_enabled': True,
                    'background_thread_count': 4,
                    'chunk_size': 5000,
                },
                'current_stats': {
                    'memory_percent': 50.0,
                    'process_memory_mb': 100.0,
                    'active_operations': 0,
                    'completed_operations': 0,
                }
            }

    def get_operation_metrics(self, operation_name: Optional[str] = None,
                            limit: int = 100) -> List[OperationMetrics]:
        """
        Get metrics for completed operations.

        Args:
            operation_name: Filter by operation name (optional)
            limit: Maximum number of metrics to return

        Returns:
            List of operation metrics
        """
        metrics = self.completed_operations

        if operation_name:
            metrics = [m for m in metrics if m.operation_name == operation_name]

        # Return most recent metrics
        return sorted(metrics, key=lambda x: x.end_time, reverse=True)[:limit]

    def get_average_operation_time(self, operation_name: str) -> Optional[float]:
        """
        Get average time for an operation type.

        Args:
            operation_name: Name of the operation

        Returns:
            Average time in milliseconds, or None if no operations found
        """
        metrics = self.get_operation_metrics(operation_name)
        if not metrics:
            return None

        successful_metrics = [m for m in metrics if m.success]
        if not successful_metrics:
            return None

        return sum(m.duration_ms for m in successful_metrics) / len(successful_metrics)

    def detect_memory_leak(self, operation_name: str, threshold_mb: float = 50.0) -> bool:
        """
        Detect potential memory leaks for an operation type.

        Args:
            operation_name: Name of the operation to check
            threshold_mb: Memory increase threshold in MB

        Returns:
            True if potential memory leak detected
        """
        metrics = self.get_operation_metrics(operation_name, limit=10)
        if len(metrics) < 3:
            return False  # Not enough data

        successful_metrics = [m for m in metrics if m.success]
        if len(successful_metrics) < 3:
            return False

        # Calculate memory deltas
        memory_deltas = [
            m.memory_after_mb - m.memory_before_mb
            for m in successful_metrics
        ]

        # Check if memory is consistently increasing
        avg_delta = sum(memory_deltas) / len(memory_deltas)
        if avg_delta > threshold_mb:
            self.logger.warning(
                f"Potential memory leak detected in {operation_name}: "
                f"average memory increase of {avg_delta:.1f}MB per operation"
            )
            return True

        return False

    def force_garbage_collection(self) -> None:
        """Force garbage collection and log memory changes."""
        memory_before = self._get_memory_stats().process_mb
        gc.collect()
        memory_after = self._get_memory_stats().process_mb

        freed_mb = memory_before - memory_after
        if freed_mb > 1.0:  # Only log if significant
            self.logger.info(f"Garbage collection freed {freed_mb:.1f}MB")

    def export_performance_report(self, file_path: str) -> None:
        """
        Export performance report to JSON file.

        Args:
            file_path: Path to save the report
        """
        try:
            report = {
                'timestamp': time.time(),
                'performance_profile': {
                    'performance_level': self.performance_profile.performance_level.value,
                    'max_memory_mb': self.performance_profile.max_memory_mb,
                    'recommended_cache_size_mb': self.performance_profile.recommended_cache_size_mb,
                    'max_triangles_for_full_quality': self.performance_profile.max_triangles_for_full_quality,
                    'adaptive_quality_enabled': self.performance_profile.adaptive_quality_enabled,
                    'background_thread_count': self.performance_profile.background_thread_count,
                    'chunk_size': self.performance_profile.chunk_size
                },
                'current_memory': self._get_memory_stats().__dict__,
                'memory_history': [m.__dict__ for m in self.memory_history[-100:]],  # Last 100 entries
                'operation_summary': {}
            }

            # Add operation summaries
            operation_names = set(m.operation_name for m in self.completed_operations)
            for op_name in operation_names:
                op_metrics = [m for m in self.completed_operations if m.operation_name == op_name]
                successful_ops = [m for m in op_metrics if m.success]

                if successful_ops:
                    report['operation_summary'][op_name] = {
                        'total_operations': len(op_metrics),
                        'successful_operations': len(successful_ops),
                        'average_time_ms': sum(m.duration_ms for m in successful_ops) / len(successful_ops),
                        'min_time_ms': min(m.duration_ms for m in successful_ops),
                        'max_time_ms': max(m.duration_ms for m in successful_ops),
                        'average_memory_delta_mb': sum(
                            m.memory_after_mb - m.memory_before_mb for m in successful_ops
                        ) / len(successful_ops)
                    }

            # Write report
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2)

            self.logger.info(f"Performance report exported to {file_path}")

        except Exception as e:
            self.logger.error(f"Failed to export performance report: {str(e)}")

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_monitoring()
        self.memory_history.clear()
        self.active_operations.clear()
        self.completed_operations.clear()
        self.logger.info("Performance monitor cleaned up")


# Global performance monitor instance
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """
    Get the global performance monitor instance.

    Returns:
        Global performance monitor instance
    """
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def start_performance_monitoring() -> None:
    """Start global performance monitoring."""
    get_performance_monitor().start_monitoring()


def stop_performance_monitoring() -> None:
    """Stop global performance monitoring."""
    if _performance_monitor:
        _performance_monitor.stop_monitoring()


def monitor_operation(operation_name: str):
    """
    Decorator to monitor function performance.

    Args:
        operation_name: Name for the operation

    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            operation_id = monitor.start_operation(operation_name)

            try:
                result = func(*args, **kwargs)
                monitor.end_operation(operation_id, success=True)
                return result
            except Exception as e:
                monitor.end_operation(operation_id, success=False, error_message=str(e))
                raise

        return wrapper
    return decorator
