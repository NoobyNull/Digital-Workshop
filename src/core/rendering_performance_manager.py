"""
3D Rendering Performance Manager for Candy-Cadence.

This module provides advanced 3D rendering optimization with:
- Adaptive rendering quality based on hardware capabilities
- VSync control for tear-free rendering
- Level-of-detail (LOD) system for large models
- Frame rate monitoring and optimization
- GPU memory management
- Performance profiling and metrics
"""

import time
import threading
import psutil
import GPUtil
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import deque
from datetime import datetime

try:
    import vtk
    from vtkmodules.vtkRenderingCore import vtkRenderWindow

    VTK_AVAILABLE = True
except ImportError:
    VTK_AVAILABLE = False

from .logging_config import get_logger

logger = get_logger(__name__)


class RenderingQuality(Enum):
    """Rendering quality levels."""

    ULTRA = "ultra"  # Maximum quality, high-end hardware
    HIGH = "high"  # High quality, good hardware
    MEDIUM = "medium"  # Balanced quality/performance
    LOW = "low"  # Performance focused
    MINIMAL = "minimal"  # Minimal quality, low-end hardware


class HardwareTier(Enum):
    """Hardware performance tiers."""

    ENTRY = "entry"  # Integrated graphics, 4GB RAM
    STANDARD = "standard"  # Dedicated GPU, 8GB RAM
    HIGH_END = "high_end"  # Good GPU, 16GB RAM
    WORKSTATION = "workstation"  # Professional GPU, 32GB+ RAM


class VSyncMode(Enum):
    """VSync modes."""

    OFF = "off"  # No VSync, maximum FPS
    ON = "on"  # VSync enabled, tear-free
    ADAPTIVE = "adaptive"  # Adaptive VSync based on performance


@dataclass
class RenderingMetrics:
    """3D rendering performance metrics."""

    fps: float
    frame_time_ms: float
    triangles_rendered: int
    vertices_rendered: int
    gpu_memory_used_mb: float
    gpu_memory_total_mb: float
    cpu_usage_percent: float
    gpu_usage_percent: float
    quality_level: RenderingQuality
    lod_level: int
    vsync_enabled: bool
    timestamp: datetime


@dataclass
class HardwareCapabilities:
    """System hardware capabilities."""

    cpu_cores: int
    cpu_frequency_mhz: float
    total_memory_gb: float
    available_memory_gb: float
    gpu_count: int
    gpu_memory_gb: float
    gpu_name: str
    gpu_driver_version: str
    opengl_version: str
    hardware_tier: HardwareTier
    recommended_quality: RenderingQuality
    max_triangles: int
    max_vertices: int


@dataclass
class RenderingConfig:
    """Rendering configuration."""

    quality_level: RenderingQuality = RenderingQuality.MEDIUM
    vsync_mode: VSyncMode = VSyncMode.ADAPTIVE
    target_fps: int = 60
    min_fps: int = 30
    max_triangles: int = 1000000
    max_vertices: int = 500000
    lod_levels: int = 4
    lod_distance_factor: float = 1.0
    anti_aliasing: bool = True
    shadows_enabled: bool = True
    texture_quality: int = 2  # 0=low, 1=medium, 2=high
    shader_quality: int = 2  # 0=low, 1=medium, 2=high


class HardwareDetector:
    """Detect system hardware capabilities for rendering."""

    @staticmethod
    def detect_capabilities() -> HardwareCapabilities:
        """Detect comprehensive hardware capabilities."""
        try:
            # CPU detection
            cpu_count = psutil.cpu_count()
            try:
                cpu_freq = psutil.cpu_freq()
                cpu_frequency_mhz = cpu_freq.max if cpu_freq else 2000
            except:
                cpu_frequency_mhz = 2000

            # Memory detection
            memory_info = psutil.virtual_memory()
            total_memory_gb = memory_info.total / (1024**3)
            available_memory_gb = memory_info.available / (1024**3)

            # GPU detection
            gpu_count = 0
            gpu_memory_gb = 0
            gpu_name = "Unknown"
            gpu_driver_version = "Unknown"
            gpu_usage_percent = 0

            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]  # Use primary GPU
                    gpu_count = len(gpus)
                    gpu_memory_gb = gpu.memoryTotal / 1024
                    gpu_name = gpu.name
                    gpu_driver_version = gpu.driver
                    gpu_usage_percent = gpu.load * 100
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                logger.warning("GPU detection failed: %s", str(e))

            # OpenGL detection (if VTK available)
            opengl_version = "Unknown"
            if VTK_AVAILABLE:
                try:
                    ren_win = vtkRenderWindow()
                    if hasattr(ren_win, "GetOpenGLVersion"):
                        opengl_version = ren_win.GetOpenGLVersion()
                    ren_win.Finalize()
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.warning("OpenGL detection failed: %s", str(e))

            # Determine hardware tier
            hardware_tier = HardwareDetector._determine_hardware_tier(
                cpu_count, cpu_frequency_mhz, total_memory_gb, gpu_memory_gb
            )

            # Determine recommended quality
            recommended_quality = HardwareDetector._determine_recommended_quality(
                hardware_tier, gpu_memory_gb
            )

            # Calculate limits
            max_triangles, max_vertices = HardwareDetector._calculate_limits(
                hardware_tier, gpu_memory_gb, total_memory_gb
            )

            return HardwareCapabilities(
                cpu_cores=cpu_count,
                cpu_frequency_mhz=cpu_frequency_mhz,
                total_memory_gb=total_memory_gb,
                available_memory_gb=available_memory_gb,
                gpu_count=gpu_count,
                gpu_memory_gb=gpu_memory_gb,
                gpu_name=gpu_name,
                gpu_driver_version=gpu_driver_version,
                opengl_version=opengl_version,
                hardware_tier=hardware_tier,
                recommended_quality=recommended_quality,
                max_triangles=max_triangles,
                max_vertices=max_vertices,
            )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Hardware detection failed: %s", str(e))
            # Return default capabilities
            return HardwareCapabilities(
                cpu_cores=4,
                cpu_frequency_mhz=2000,
                total_memory_gb=8,
                available_memory_gb=4,
                gpu_count=0,
                gpu_memory_gb=0,
                gpu_name="Unknown",
                gpu_driver_version="Unknown",
                opengl_version="Unknown",
                hardware_tier=HardwareTier.STANDARD,
                recommended_quality=RenderingQuality.MEDIUM,
                max_triangles=500000,
                max_vertices=250000,
            )

    @staticmethod
    def _determine_hardware_tier(
        """TODO: Add docstring."""
        cpu_cores: int, cpu_freq: float, memory_gb: float, gpu_memory_gb: float
    ) -> HardwareTier:
        """Determine hardware tier based on specifications."""
        # Workstation tier
        if cpu_cores >= 16 and memory_gb >= 32 and gpu_memory_gb >= 8:
            return HardwareTier.WORKSTATION
        # High-end tier
        elif cpu_cores >= 8 and memory_gb >= 16 and gpu_memory_gb >= 4:
            return HardwareTier.HIGH_END
        # Standard tier
        elif cpu_cores >= 4 and memory_gb >= 8 and gpu_memory_gb >= 2:
            return HardwareTier.STANDARD
        # Entry tier
        else:
            return HardwareTier.ENTRY

    @staticmethod
    def _determine_recommended_quality(
        """TODO: Add docstring."""
        hardware_tier: HardwareTier, gpu_memory_gb: float
    ) -> RenderingQuality:
        """Determine recommended rendering quality."""
        quality_mapping = {
            HardwareTier.WORKSTATION: RenderingQuality.ULTRA,
            HardwareTier.HIGH_END: RenderingQuality.HIGH,
            HardwareTier.STANDARD: RenderingQuality.MEDIUM,
            HardwareTier.ENTRY: RenderingQuality.LOW,
        }

        quality = quality_mapping.get(hardware_tier, RenderingQuality.MEDIUM)

        # Adjust for low GPU memory
        if gpu_memory_gb < 2 and quality in [
            RenderingQuality.HIGH,
            RenderingQuality.ULTRA,
        ]:
            quality = RenderingQuality.MEDIUM
        elif gpu_memory_gb < 1 and quality == RenderingQuality.MEDIUM:
            quality = RenderingQuality.LOW

        return quality

    @staticmethod
    def _calculate_limits(
        """TODO: Add docstring."""
        hardware_tier: HardwareTier, gpu_memory_gb: float, system_memory_gb: float
    ) -> Tuple[int, int]:
        """Calculate rendering limits based on hardware."""
        base_limits = {
            HardwareTier.WORKSTATION: (5000000, 2500000),
            HardwareTier.HIGH_END: (2000000, 1000000),
            HardwareTier.STANDARD: (1000000, 500000),
            HardwareTier.ENTRY: (500000, 250000),
        }

        max_triangles, max_vertices = base_limits.get(hardware_tier, (500000, 250000))

        # Adjust for GPU memory
        if gpu_memory_gb < 1:
            max_triangles //= 4
            max_vertices //= 4
        elif gpu_memory_gb < 2:
            max_triangles //= 2
            max_vertices //= 2
        elif gpu_memory_gb > 8:
            max_triangles *= 2
            max_vertices *= 2

        # Adjust for system memory
        if system_memory_gb < 4:
            max_triangles //= 2
            max_vertices //= 2
        elif system_memory_gb > 16:
            max_triangles *= 2
            max_vertices *= 2

        return max_triangles, max_vertices


class LevelOfDetailManager:
    """Manage level-of-detail for 3D models."""

    def __init__(self, config: RenderingConfig) -> None:
        """
        Initialize LOD manager.

        Args:
            config: Rendering configuration
        """
        self.config = config
        self._model_lods: Dict[str, List[Any]] = {}  # model_id -> LOD levels
        self._current_lod_cache: Dict[str, int] = {}  # model_id -> current LOD
        self._lock = threading.Lock()

    def create_lod_levels(
        """TODO: Add docstring."""
        self, model_id: str, high_detail_mesh: Any, triangle_count: int
    ) -> List[Any]:
        """
        Create LOD levels for a model.

        Args:
            model_id: Model identifier
            high_detail_mesh: High-detail mesh object
            triangle_count: Number of triangles in high-detail mesh

        Returns:
            List of LOD level meshes
        """
        lod_levels = []

        # Calculate LOD reduction factors
        lod_factors = self._calculate_lod_factors(triangle_count)

        for i, factor in enumerate(lod_factors):
            if VTK_AVAILABLE and hasattr(high_detail_mesh, "GetPoints"):
                # Create simplified mesh using VTK decimation
                lod_mesh = self._create_decimated_mesh(high_detail_mesh, factor)
            else:
                # Fallback: use original mesh for all LODs
                lod_mesh = high_detail_mesh

            lod_levels.append(lod_mesh)

        with self._lock:
            self._model_lods[model_id] = lod_levels

        logger.debug("Created %s LOD levels for model {model_id}", len(lod_levels))
        return lod_levels

    def _calculate_lod_factors(self, triangle_count: int) -> List[float]:
        """Calculate LOD reduction factors."""
        lod_count = self.config.lod_levels

        if triangle_count < 10000:
            # Small models: fewer LOD levels
            lod_count = min(2, lod_count)
        elif triangle_count > 1000000:
            # Large models: more LOD levels
            lod_count = max(4, lod_count)

        # Generate reduction factors (1.0 = full detail, 0.1 = minimal detail)
        factors = []
        for i in range(lod_count):
            factor = 1.0 - (i * 0.3)  # 30% reduction per level
            factor = max(0.1, factor)  # Minimum 10% detail
            factors.append(factor)

        return factors

    def _create_decimated_mesh(self, mesh: Any, reduction_factor: float) -> Any:
        """Create decimated mesh using VTK."""
        try:
            # This is a simplified implementation
            # In practice, you'd use VTK's vtkDecimatePro or vtkQuadricDecimation
            decimator = vtk.vtkDecimatePro()
            decimator.SetInputData(mesh)
            decimator.SetTargetReduction(1.0 - reduction_factor)
            decimator.Update()
            return decimator.GetOutput()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.warning("Mesh decimation failed: %s", str(e))
            return mesh  # Return original mesh

    def get_optimal_lod(self, model_id: str, camera_distance: float, screen_size: float) -> int:
        """
        Get optimal LOD level based on distance and screen size.

        Args:
            model_id: Model identifier
            camera_distance: Distance from camera to model
            screen_size: Screen size in pixels

        Returns:
            Optimal LOD level (0 = highest detail)
        """
        with self._lock:
            if model_id not in self._model_lods:
                return 0  # Default to highest detail

            lod_levels = self._model_lods[model_id]
            lod_count = len(lod_levels)

            if lod_count <= 1:
                return 0

            # Calculate LOD based on distance and screen size
            distance_factor = min(1.0, camera_distance / 1000.0)  # Normalize distance
            size_factor = min(1.0, screen_size / 1920.0)  # Normalize screen size

            # Combined factor (closer and larger = higher detail)
            detail_factor = (1.0 - distance_factor) * size_factor

            # Map to LOD level
            lod_level = int(detail_factor * (lod_count - 1))
            lod_level = max(0, min(lod_level, lod_count - 1))

            self._current_lod_cache[model_id] = lod_level
            return lod_level

    def get_current_lod(self, model_id: str) -> int:
        """Get current LOD level for a model."""
        with self._lock:
            return self._current_lod_cache.get(model_id, 0)

    def cleanup_model_lods(self, model_id: str) -> None:
        """Clean up LOD data for a model."""
        with self._lock:
            self._model_lods.pop(model_id, None)
            self._current_lod_cache.pop(model_id, None)


class VSyncManager:
    """Manage VSync settings for tear-free rendering."""

    def __init__(self, config: RenderingConfig) -> None:
        """
        Initialize VSync manager.

        Args:
            config: Rendering configuration
        """
        self.config = config
        self._vsync_enabled = config.vsync_mode != VSyncMode.OFF
        self._adaptive_threshold = 0.8  # 80% of target FPS
        self._performance_history = deque(maxlen=60)  # Last 60 frames
        self._last_adjustment_time = time.time()
        self._adjustment_cooldown = 2.0  # 2 seconds between adjustments

    def should_enable_vsync(self, current_fps: float, target_fps: float) -> bool:
        """
        Determine if VSync should be enabled.

        Args:
            current_fps: Current frame rate
            target_fps: Target frame rate

        Returns:
            True if VSync should be enabled
        """
        if self.config.vsync_mode == VSyncMode.OFF:
            return False
        elif self.config.vsync_mode == VSyncMode.ON:
            return True
        elif self.config.vsync_mode == VSyncMode.ADAPTIVE:
            return self._should_adaptive_vsync(current_fps, target_fps)

        return False

    def _should_adaptive_vsync(self, current_fps: float, target_fps: float) -> bool:
        """Determine adaptive VSync behavior."""
        current_time = time.time()

        # Record performance
        self._performance_history.append({"fps": current_fps, "timestamp": current_time})

        # Only adjust every few seconds
        if current_time - self._last_adjustment_time < self._adjustment_cooldown:
            return self._vsync_enabled

        # Calculate average FPS over recent history
        if len(self._performance_history) < 10:
            return self._vsync_enabled

        recent_fps = [p["fps"] for p in list(self._performance_history)[-10:]]
        avg_fps = sum(recent_fps) / len(recent_fps)

        # Adjust VSync based on performance
        if avg_fps < self.config.min_fps * 0.9:  # Below minimum FPS
            if self._vsync_enabled:
                self._vsync_enabled = False
                logger.info("Disabling VSync due to low performance")
        elif avg_fps > target_fps * 0.95:  # Consistently above target
            if not self._vsync_enabled:
                self._vsync_enabled = True
                logger.info("Enabling VSync for tear-free rendering")

        self._last_adjustment_time = current_time
        return self._vsync_enabled

    def set_vsync_enabled(self, enabled: bool) -> None:
        """Manually set VSync enabled state."""
        self._vsync_enabled = enabled
        logger.info("VSync %s", 'enabled' if enabled else 'disabled')

    def get_vsync_enabled(self) -> bool:
        """Get current VSync state."""
        return self._vsync_enabled


class FrameRateMonitor:
    """Monitor and optimize frame rate performance."""

    def __init__(self, config: RenderingConfig) -> None:
        """
        Initialize frame rate monitor.

        Args:
            config: Rendering configuration
        """
        self.config = config
        self._frame_times = deque(maxlen=120)  # Last 120 frames
        self._fps_history = deque(maxlen=60)  # Last 60 seconds
        self._last_frame_time = time.time()
        self._frame_count = 0
        self._lock = threading.Lock()

    def record_frame(self) -> None:
        """Record frame timing information."""
        current_time = time.time()
        frame_time = current_time - self._last_frame_time

        with self._lock:
            self._frame_times.append(frame_time)
            self._fps_history.append(1.0 / frame_time if frame_time > 0 else 0)

        self._last_frame_time = current_time
        self._frame_count += 1

    def get_current_fps(self) -> float:
        """Get current FPS based on recent frames."""
        with self._lock:
            if not self._fps_history:
                return 0.0
            return sum(list(self._fps_history)[-10:]) / min(10, len(self._fps_history))

    def get_average_fps(self, seconds: int = 5) -> float:
        """Get average FPS over specified time period."""
        with self._lock:
            cutoff_time = time.time() - seconds
            recent_fps = [
                fps
                for fps, timestamp in [
                    (fps, time.time() - i / 60) for i, fps in enumerate(reversed(self._fps_history))
                ]
                if time.time() - timestamp <= seconds
            ]

            if not recent_fps:
                return 0.0
            return sum(recent_fps) / len(recent_fps)

    def get_frame_time_stats(self) -> Dict[str, float]:
        """Get frame time statistics."""
        with self._lock:
            if not self._frame_times:
                return {}

            frame_times = list(self._frame_times)
            return {
                "min_frame_time_ms": min(frame_times) * 1000,
                "max_frame_time_ms": max(frame_times) * 1000,
                "avg_frame_time_ms": sum(frame_times) / len(frame_times) * 1000,
                "frame_time_std_ms": self._calculate_std(frame_times) * 1000,
            }

    def _calculate_std(self, values: List[float]) -> float:
        """Calculate standard deviation."""
        if len(values) < 2:
            return 0.0
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance**0.5

    def is_performance_acceptable(self) -> bool:
        """Check if current performance meets requirements."""
        current_fps = self.get_current_fps()
        return current_fps >= self.config.min_fps

    def should_reduce_quality(self) -> bool:
        """Determine if rendering quality should be reduced."""
        current_fps = self.get_current_fps()
        return current_fps < self.config.min_fps * 0.9

    def can_increase_quality(self) -> bool:
        """Determine if rendering quality can be increased."""
        current_fps = self.get_current_fps()
        return current_fps > self.config.target_fps * 0.95


class RenderingPerformanceManager:
    """Main 3D rendering performance management system."""

    def __init__(self, config: Optional[RenderingConfig] = None) -> None:
        """
        Initialize rendering performance manager.

        Args:
            config: Custom rendering configuration
        """
        # Detect hardware capabilities
        self.hardware_capabilities = HardwareDetector.detect_capabilities()

        # Initialize configuration
        if config is None:
            config = RenderingConfig()
            config.quality_level = self.hardware_capabilities.recommended_quality
            config.max_triangles = self.hardware_capabilities.max_triangles
            config.max_vertices = self.hardware_capabilities.max_vertices

        self.config = config

        # Initialize components
        self.lod_manager = LevelOfDetailManager(config)
        self.vsync_manager = VSyncManager(config)
        self.frame_monitor = FrameRateMonitor(config)

        # Performance callbacks
        self._quality_change_callbacks: List[Callable[[RenderingQuality], None]] = []
        self._performance_alert_callbacks: List[Callable[[str], None]] = []

        # Performance state
        self._current_metrics: Optional[RenderingMetrics] = None
        self._last_optimization_time = time.time()
        self._optimization_interval = 5.0  # 5 seconds

        logger.info(
            f"Rendering performance manager initialized with {config.quality_level.value} quality "
            f"for {self.hardware_capabilities.hardware_tier.value} hardware"
        )

    def register_quality_change_callback(
        """TODO: Add docstring."""
        self, callback: Callable[[RenderingQuality], None]
    ) -> None:
        """Register callback for quality level changes."""
        self._quality_change_callbacks.append(callback)

    def register_performance_alert_callback(self, callback: Callable[[str], None]) -> None:
        """Register callback for performance alerts."""
        self._performance_alert_callbacks.append(callback)

    def update_rendering_metrics(
        """TODO: Add docstring."""
        self, triangles_rendered: int = 0, vertices_rendered: int = 0
    ) -> RenderingMetrics:
        """
        Update rendering performance metrics.

        Args:
            triangles_rendered: Number of triangles rendered in last frame
            vertices_rendered: Number of vertices rendered in last frame

        Returns:
            Current rendering metrics
        """
        # Record frame timing
        self.frame_monitor.record_frame()

        # Get current performance data
        current_fps = self.frame_monitor.get_current_fps()
        frame_time_ms = 1000.0 / current_fps if current_fps > 0 else 0

        # Get GPU memory usage
        gpu_memory_used = 0
        gpu_memory_total = 0
        gpu_usage = 0

        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]
                gpu_memory_used = gpu.memoryUsed
                gpu_memory_total = gpu.memoryTotal
                gpu_usage = gpu.load * 100
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.debug("GPU metrics unavailable: %s", str(e))

        # Get CPU usage
        cpu_usage = psutil.cpu_percent(interval=0.1)

        # Determine VSync state
        vsync_enabled = self.vsync_manager.should_enable_vsync(current_fps, self.config.target_fps)

        # Get current LOD level (simplified)
        current_lod = 0  # This would be calculated based on active models

        # Create metrics
        metrics = RenderingMetrics(
            fps=current_fps,
            frame_time_ms=frame_time_ms,
            triangles_rendered=triangles_rendered,
            vertices_rendered=vertices_rendered,
            gpu_memory_used_mb=gpu_memory_used,
            gpu_memory_total_mb=gpu_memory_total,
            cpu_usage_percent=cpu_usage,
            gpu_usage_percent=gpu_usage,
            quality_level=self.config.quality_level,
            lod_level=current_lod,
            vsync_enabled=vsync_enabled,
            timestamp=datetime.now(),
        )

        self._current_metrics = metrics

        # Check if optimization is needed
        self._check_optimization_needed()

        return metrics

    def _check_optimization_needed(self) -> None:
        """Check if rendering optimization is needed."""
        current_time = time.time()

        # Only optimize every few seconds
        if current_time - self._last_optimization_time < self._optimization_interval:
            return

        self._last_optimization_time = current_time

        if not self._current_metrics:
            return

        # Check for performance issues
        if self.frame_monitor.should_reduce_quality():
            self._reduce_rendering_quality()
        elif self.frame_monitor.can_increase_quality():
            self._increase_rendering_quality()

        # Check for memory pressure
        if (
            self._current_metrics.gpu_memory_used_mb
            > self._current_metrics.gpu_memory_total_mb * 0.9
        ):
            self._handle_gpu_memory_pressure()

    def _reduce_rendering_quality(self) -> None:
        """Reduce rendering quality to improve performance."""
        current_quality = self.config.quality_level

        quality_reduction_map = {
            RenderingQuality.ULTRA: RenderingQuality.HIGH,
            RenderingQuality.HIGH: RenderingQuality.MEDIUM,
            RenderingQuality.MEDIUM: RenderingQuality.LOW,
            RenderingQuality.LOW: RenderingQuality.MINIMAL,
            RenderingQuality.MINIMAL: RenderingQuality.MINIMAL,
        }

        new_quality = quality_reduction_map.get(current_quality, current_quality)

        if new_quality != current_quality:
            self.config.quality_level = new_quality
            logger.info(
                f"Reducing rendering quality from {current_quality.value} to {new_quality.value}"
            )

            # Notify callbacks
            for callback in self._quality_change_callbacks:
                try:
                    callback(new_quality)
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.error("Quality change callback failed: %s", str(e))

            # Alert callbacks
            for callback in self._performance_alert_callbacks:
                try:
                    callback(f"Rendering quality reduced to {new_quality.value} due to performance")
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.error("Performance alert callback failed: %s", str(e))

    def _increase_rendering_quality(self) -> None:
        """Increase rendering quality if performance allows."""
        current_quality = self.config.quality_level

        quality_increase_map = {
            RenderingQuality.MINIMAL: RenderingQuality.LOW,
            RenderingQuality.LOW: RenderingQuality.MEDIUM,
            RenderingQuality.MEDIUM: RenderingQuality.HIGH,
            RenderingQuality.HIGH: RenderingQuality.ULTRA,
            RenderingQuality.ULTRA: RenderingQuality.ULTRA,
        }

        new_quality = quality_increase_map.get(current_quality, current_quality)

        if new_quality != current_quality:
            self.config.quality_level = new_quality
            logger.info("Increasing rendering quality to %s", new_quality.value)

            # Notify callbacks
            for callback in self._quality_change_callbacks:
                try:
                    callback(new_quality)
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    logger.error("Quality change callback failed: %s", str(e))

    def _handle_gpu_memory_pressure(self) -> None:
        """Handle GPU memory pressure situation."""
        logger.warning("GPU memory pressure detected")

        # Reduce texture quality
        if self.config.texture_quality > 0:
            self.config.texture_quality -= 1
            logger.info("Reducing texture quality due to GPU memory pressure")

        # Disable shadows if enabled
        if self.config.shadows_enabled:
            self.config.shadows_enabled = False
            logger.info("Disabling shadows due to GPU memory pressure")

        # Alert callbacks
        for callback in self._performance_alert_callbacks:
            try:
                callback("GPU memory pressure - reduced texture quality and disabled shadows")
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                logger.error("Performance alert callback failed: %s", str(e))

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        current_metrics = self._current_metrics
        frame_stats = self.frame_monitor.get_frame_time_stats()

        return {
            "hardware_capabilities": {
                "cpu_cores": self.hardware_capabilities.cpu_cores,
                "cpu_frequency_mhz": self.hardware_capabilities.cpu_frequency_mhz,
                "total_memory_gb": self.hardware_capabilities.total_memory_gb,
                "gpu_memory_gb": self.hardware_capabilities.gpu_memory_gb,
                "gpu_name": self.hardware_capabilities.gpu_name,
                "hardware_tier": self.hardware_capabilities.hardware_tier.value,
                "recommended_quality": self.hardware_capabilities.recommended_quality.value,
            },
            "current_metrics": (
                {
                    "fps": current_metrics.fps if current_metrics else 0,
                    "frame_time_ms": (current_metrics.frame_time_ms if current_metrics else 0),
                    "triangles_rendered": (
                        current_metrics.triangles_rendered if current_metrics else 0
                    ),
                    "gpu_memory_used_mb": (
                        current_metrics.gpu_memory_used_mb if current_metrics else 0
                    ),
                    "gpu_usage_percent": (
                        current_metrics.gpu_usage_percent if current_metrics else 0
                    ),
                    "cpu_usage_percent": (
                        current_metrics.cpu_usage_percent if current_metrics else 0
                    ),
                    "quality_level": (
                        current_metrics.quality_level.value if current_metrics else "unknown"
                    ),
                    "vsync_enabled": (current_metrics.vsync_enabled if current_metrics else False),
                }
                if current_metrics
                else {}
            ),
            "frame_statistics": frame_stats,
            "configuration": {
                "quality_level": self.config.quality_level.value,
                "vsync_mode": self.config.vsync_mode.value,
                "target_fps": self.config.target_fps,
                "min_fps": self.config.min_fps,
                "max_triangles": self.config.max_triangles,
                "max_vertices": self.config.max_vertices,
                "anti_aliasing": self.config.anti_aliasing,
                "shadows_enabled": self.config.shadows_enabled,
                "texture_quality": self.config.texture_quality,
            },
            "performance_status": {
                "is_acceptable": self.frame_monitor.is_performance_acceptable(),
                "should_reduce_quality": self.frame_monitor.should_reduce_quality(),
                "can_increase_quality": self.frame_monitor.can_increase_quality(),
            },
        }

    def optimize_for_model(self, model_id: str, triangle_count: int) -> None:
        """Optimize rendering settings for a specific model."""
        # Create LOD levels if needed
        if triangle_count > self.config.max_triangles // 2:
            # This would typically be called with the actual mesh object
            logger.info("Creating LOD levels for model %s with {triangle_count} triangles", model_id)

    def shutdown(self) -> None:
        """Shutdown the rendering performance manager."""
        logger.info("Rendering performance manager shutdown")


# Global rendering performance manager instance
_rendering_manager: Optional[RenderingPerformanceManager] = None


def get_rendering_manager() -> RenderingPerformanceManager:
    """Get global rendering performance manager instance."""
    global _rendering_manager
    if _rendering_manager is None:
        _rendering_manager = RenderingPerformanceManager()
    return _rendering_manager


def get_rendering_metrics() -> Optional[RenderingMetrics]:
    """Get current rendering metrics."""
    manager = get_rendering_manager()
    return manager._current_metrics


def optimize_rendering_performance() -> Dict[str, Any]:
    """Get rendering performance report."""
    manager = get_rendering_manager()
    return manager.get_performance_report()
