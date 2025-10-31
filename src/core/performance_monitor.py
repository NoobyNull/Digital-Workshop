"""
Real-Time Performance Monitoring System for Candy-Cadence.

This module provides comprehensive performance monitoring with:
- Real-time metrics collection from all subsystems
- Performance alerting and notifications
- Adaptive performance adjustments
- Performance profiling and analysis
- Historical performance data tracking
- Integration with memory, loading, and rendering managers
"""

import time
import threading
import json
import psutil
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import deque, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager
import weakref

from PySide6.QtCore import QObject, QTimer, Signal

from .logging_config import get_logger, log_function_call
from .memory_manager import get_memory_manager, MemoryAlert
from .progressive_loader import get_progressive_loader, LoadingProgress
from .rendering_performance_manager import get_rendering_manager, RenderingMetrics

logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Performance metric types."""
    MEMORY = "memory"
    LOADING = "loading"
    RENDERING = "rendering"
    DATABASE = "database"
    SYSTEM = "system"
    APPLICATION = "application"
class MetricType(Enum):
    """Performance metric types."""
    MEMORY = "memory"
    LOADING = "loading"
    RENDERING = "rendering"
    DATABASE = "database"
    SYSTEM = "system"
    APPLICATION = "application"


class PerformanceLevel(Enum):
    """Performance level enumeration for system optimization."""
    MINIMAL = "minimal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"


@dataclass
class PerformanceAlert:
    """Performance alert information."""
    id: str
    severity: AlertSeverity
    metric_type: MetricType
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None


@dataclass
class PerformanceMetric:
    """Individual performance metric."""
    name: str
    value: float
    unit: str
    metric_type: MetricType
    timestamp: datetime
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """Complete performance snapshot."""
    timestamp: datetime
    metrics: List[PerformanceMetric]
    alerts: List[PerformanceAlert]
    system_info: Dict[str, Any]
    application_state: Dict[str, Any]


@dataclass
class PerformanceThresholds:
    """Performance threshold configuration."""
    # Memory thresholds (MB)
    memory_warning_mb: float = 1500
    memory_critical_mb: float = 1800
    memory_leak_threshold_mb: float = 100
    
    # Loading thresholds (seconds)
    loading_warning_seconds: float = 10
    loading_critical_seconds: float = 30
    
    # Rendering thresholds (FPS)
    rendering_warning_fps: float = 25
    rendering_critical_fps: float = 20
    
    # System thresholds (%)
    cpu_warning_percent: float = 80
    cpu_critical_percent: float = 95
    disk_warning_percent: float = 85
    disk_critical_percent: float = 95


class PerformanceProfiler:
    """Advanced performance profiling and analysis."""

    def __init__(self, history_size: int = 10000):
        """
        Initialize performance profiler.

        Args:
            history_size: Maximum number of metrics to keep in history
        """
        self.history_size = history_size
        self._metric_history: deque = deque(maxlen=history_size)
        self._operation_profiles: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def record_metric(self, metric: PerformanceMetric) -> None:
        """Record a performance metric."""
        with self._lock:
            self._metric_history.append(metric)

    def profile_operation(self, operation_name: str, duration: float) -> None:
        """Profile an operation duration."""
        with self._lock:
            self._operation_profiles[operation_name].append(duration)
            
            # Keep only recent profiles
            if len(self._operation_profiles[operation_name]) > 1000:
                self._operation_profiles[operation_name] = self._operation_profiles[operation_name][-500:]

    def get_metric_trend(self, metric_name: str, duration_minutes: int = 60) -> Dict[str, float]:
        """Get metric trend over specified duration."""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
        
        with self._lock:
            recent_metrics = [
                m for m in self._metric_history 
                if m.name == metric_name and m.timestamp >= cutoff_time
            ]
            
            if not recent_metrics:
                return {}
                
            values = [m.value for m in recent_metrics]
            
            return {
                'current': values[-1] if values else 0,
                'min': min(values),
                'max': max(values),
                'average': sum(values) / len(values),
                'count': len(values),
                'trend': self._calculate_trend(values)
            }

    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate trend slope for values."""
        if len(values) < 2:
            return 0.0
            
        # Simple linear regression
        n = len(values)
        x_values = list(range(n))
        
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
        sum_x2 = sum(x * x for x in x_values)
        
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return 0.0
            
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        return slope

    def get_operation_stats(self, operation_name: str) -> Dict[str, float]:
        """Get statistics for a profiled operation."""
        with self._lock:
            durations = self._operation_profiles.get(operation_name, [])
            
            if not durations:
                return {}
                
            return {
                'count': len(durations),
                'min': min(durations),
                'max': max(durations),
                'average': sum(durations) / len(durations),
                'recent': durations[-1] if durations else 0
            }

    def detect_anomalies(self, metric_name: str, threshold_std: float = 2.0) -> List[PerformanceMetric]:
        """Detect anomalous metric values."""
        with self._lock:
            recent_metrics = [
                m for m in list(self._metric_history)[-1000:] 
                if m.name == metric_name
            ]
            
            if len(recent_metrics) < 10:
                return []
                
            values = [m.value for m in recent_metrics]
            mean = sum(values) / len(values)
            variance = sum((x - mean) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
            
            anomalies = []
            for metric in recent_metrics[-20:]:  # Check recent values
                if abs(metric.value - mean) > threshold_std * std_dev:
                    anomalies.append(metric)
                    
            return anomalies


class AlertManager:
    """Manage performance alerts and notifications."""

    def __init__(self, thresholds: PerformanceThresholds):
        """
        Initialize alert manager.

        Args:
            thresholds: Performance thresholds
        """
        self.thresholds = thresholds
        self._active_alerts: Dict[str, PerformanceAlert] = {}
        self._alert_history: deque = deque(maxlen=1000)
        self._alert_callbacks: List[Callable[[PerformanceAlert], None]] = []
        self._suppressed_alerts: Dict[str, float] = {}  # alert_id -> suppression_until
        self._lock = threading.Lock()

    def register_alert_callback(self, callback: Callable[[PerformanceAlert], None]) -> None:
        """Register callback for alert notifications."""
        self._alert_callbacks.append(callback)

    def check_threshold(self, metric_name: str, value: float, metric_type: MetricType,
                       details: Dict[str, Any] = None) -> Optional[PerformanceAlert]:
        """Check if metric value exceeds thresholds."""
        alert = None
        
        if metric_type == MetricType.MEMORY:
            alert = self._check_memory_threshold(metric_name, value, details or {})
        elif metric_type == MetricType.LOADING:
            alert = self._check_loading_threshold(metric_name, value, details or {})
        elif metric_type == MetricType.RENDERING:
            alert = self._check_rendering_threshold(metric_name, value, details or {})
        elif metric_type == MetricType.SYSTEM:
            alert = self._check_system_threshold(metric_name, value, details or {})
            
        if alert:
            self._process_alert(alert)
            
        return alert

    def _check_memory_threshold(self, metric_name: str, value: float, details: Dict[str, Any]) -> Optional[PerformanceAlert]:
        """Check memory-related thresholds."""
        if "memory_usage_mb" in metric_name.lower():
            if value >= self.thresholds.memory_critical_mb:
                return PerformanceAlert(
                    id=f"memory_critical_{int(time.time())}",
                    severity=AlertSeverity.CRITICAL,
                    metric_type=MetricType.MEMORY,
                    message=f"Critical memory usage: {value:.1f}MB",
                    details=details,
                    timestamp=datetime.now()
                )
            elif value >= self.thresholds.memory_warning_mb:
                return PerformanceAlert(
                    id=f"memory_warning_{int(time.time())}",
                    severity=AlertSeverity.WARNING,
                    metric_type=MetricType.MEMORY,
                    message=f"High memory usage: {value:.1f}MB",
                    details=details,
                    timestamp=datetime.now()
                )
        return None

    def _check_loading_threshold(self, metric_name: str, value: float, details: Dict[str, Any]) -> Optional[PerformanceAlert]:
        """Check loading-related thresholds."""
        if "load_time" in metric_name.lower():
            if value >= self.thresholds.loading_critical_seconds:
                return PerformanceAlert(
                    id=f"loading_critical_{int(time.time())}",
                    severity=AlertSeverity.CRITICAL,
                    metric_type=MetricType.LOADING,
                    message=f"Critical loading time: {value:.1f}s",
                    details=details,
                    timestamp=datetime.now()
                )
            elif value >= self.thresholds.loading_warning_seconds:
                return PerformanceAlert(
                    id=f"loading_warning_{int(time.time())}",
                    severity=AlertSeverity.WARNING,
                    metric_type=MetricType.LOADING,
                    message=f"Slow loading time: {value:.1f}s",
                    details=details,
                    timestamp=datetime.now()
                )
        return None

    def _check_rendering_threshold(self, metric_name: str, value: float, details: Dict[str, Any]) -> Optional[PerformanceAlert]:
        """Check rendering-related thresholds."""
        if "fps" in metric_name.lower():
            if value <= self.thresholds.rendering_critical_fps:
                return PerformanceAlert(
                    id=f"rendering_critical_{int(time.time())}",
                    severity=AlertSeverity.CRITICAL,
                    metric_type=MetricType.RENDERING,
                    message=f"Critical frame rate: {value:.1f} FPS",
                    details=details,
                    timestamp=datetime.now()
                )
            elif value <= self.thresholds.rendering_warning_fps:
                return PerformanceAlert(
                    id=f"rendering_warning_{int(time.time())}",
                    severity=AlertSeverity.WARNING,
                    metric_type=MetricType.RENDERING,
                    message=f"Low frame rate: {value:.1f} FPS",
                    details=details,
                    timestamp=datetime.now()
                )
        return None

    def _check_system_threshold(self, metric_name: str, value: float, details: Dict[str, Any]) -> Optional[PerformanceAlert]:
        """Check system-related thresholds."""
        if "cpu_usage" in metric_name.lower():
            if value >= self.thresholds.cpu_critical_percent:
                return PerformanceAlert(
                    id=f"cpu_critical_{int(time.time())}",
                    severity=AlertSeverity.CRITICAL,
                    metric_type=MetricType.SYSTEM,
                    message=f"Critical CPU usage: {value:.1f}%",
                    details=details,
                    timestamp=datetime.now()
                )
            elif value >= self.thresholds.cpu_warning_percent:
                return PerformanceAlert(
                    id=f"cpu_warning_{int(time.time())}",
                    severity=AlertSeverity.WARNING,
                    metric_type=MetricType.SYSTEM,
                    message=f"High CPU usage: {value:.1f}%",
                    details=details,
                    timestamp=datetime.now()
                )
        return None

    def _process_alert(self, alert: PerformanceAlert) -> None:
        """Process a performance alert."""
        # Check if alert is suppressed
        if alert.id in self._suppressed_alerts:
            if time.time() < self._suppressed_alerts[alert.id]:
                return  # Still suppressed
            else:
                del self._suppressed_alerts[alert.id]  # Suppression expired

        with self._lock:
            # Check if similar alert is already active
            similar_alert = self._find_similar_active_alert(alert)
            if similar_alert:
                return  # Don't create duplicate alerts

            self._active_alerts[alert.id] = alert
            self._alert_history.append(alert)

        # Notify callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {str(e)}")

        # Log alert
        if alert.severity == AlertSeverity.CRITICAL:
            logger.critical(f"PERFORMANCE ALERT: {alert.message}")
        elif alert.severity == AlertSeverity.ERROR:
            logger.error(f"PERFORMANCE ALERT: {alert.message}")
        elif alert.severity == AlertSeverity.WARNING:
            logger.warning(f"PERFORMANCE ALERT: {alert.message}")
        else:
            logger.info(f"PERFORMANCE ALERT: {alert.message}")

    def _find_similar_active_alert(self, alert: PerformanceAlert) -> Optional[PerformanceAlert]:
        """Find similar active alert to avoid duplicates."""
        for active_alert in self._active_alerts.values():
            if (active_alert.metric_type == alert.metric_type and
                active_alert.severity == alert.severity and
                active_alert.message.split(':')[0] == alert.message.split(':')[0]):
                return active_alert
        return None

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert."""
        with self._lock:
            if alert_id in self._active_alerts:
                self._active_alerts[alert_id].acknowledged = True
                return True
        return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        with self._lock:
            if alert_id in self._active_alerts:
                alert = self._active_alerts[alert_id]
                alert.resolved = True
                alert.resolved_at = datetime.now()
                
                # Move to history
                self._alert_history.append(alert)
                del self._active_alerts[alert_id]
                return True
        return False

    def suppress_alert(self, alert_id: str, duration_seconds: int) -> None:
        """Suppress an alert for specified duration."""
        self._suppressed_alerts[alert_id] = time.time() + duration_seconds

    def get_active_alerts(self) -> List[PerformanceAlert]:
        """Get all active alerts."""
        with self._lock:
            return list(self._active_alerts.values())

    def get_recent_alerts(self, count: int = 50) -> List[PerformanceAlert]:
        """Get recent alerts from history."""
        with self._lock:
            return list(self._alert_history)[-count:]


class RealTimePerformanceMonitor(QObject):
    """Main real-time performance monitoring system."""

    # Signals
    metric_recorded = Signal(PerformanceMetric)
    alert_triggered = Signal(PerformanceAlert)
    snapshot_captured = Signal(PerformanceSnapshot)

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize real-time performance monitor.

        Args:
            config: Custom configuration
        """
        super().__init__()
        
        # Configuration
        self.config = config or {}
        self.monitoring_interval = self.config.get('monitoring_interval', 5)  # seconds
        self.snapshot_interval = self.config.get('snapshot_interval', 60)    # seconds
        self.enable_profiling = self.config.get('enable_profiling', True)
        self.enable_alerting = self.config.get('enable_alerting', True)
        
        # Initialize components
        self.thresholds = PerformanceThresholds()
        self.profiler = PerformanceProfiler()
        self.alert_manager = AlertManager(self.thresholds)
        
        # Performance managers
        self.memory_manager = get_memory_manager()
        self.progressive_loader = get_progressive_loader()
        self.rendering_manager = get_rendering_manager()
        
        # State tracking
        self._monitoring_active = False
        self._monitoring_timer = QTimer()
        self._snapshot_timer = QTimer()
        self._last_metrics: Dict[str, float] = {}
        self._operation_start_times: Dict[str, float] = {}
        
        # Connect signals
        self.alert_manager.register_alert_callback(self._on_alert)
        
        # Setup timers
        self._monitoring_timer.timeout.connect(self._collect_metrics)
        self._snapshot_timer.timeout.connect(self._capture_snapshot)

        logger.info("Real-time performance monitor initialized")

    def start_monitoring(self) -> None:
        """Start performance monitoring."""
        if self._monitoring_active:
            return
            
        self._monitoring_active = True
        self._monitoring_timer.start(self.monitoring_interval * 1000)
        self._snapshot_timer.start(self.snapshot_interval * 1000)
        
        logger.info("Performance monitoring started")

    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        if not self._monitoring_active:
            return
            
        self._monitoring_active = False
        self._monitoring_timer.stop()
        self._snapshot_timer.stop()
        
        logger.info("Performance monitoring stopped")

    def _collect_metrics(self) -> None:
        """Collect performance metrics from all subsystems."""
        try:
            # Collect memory metrics
            self._collect_memory_metrics()
            
            # Collect loading metrics
            self._collect_loading_metrics()
            
            # Collect rendering metrics
            self._collect_rendering_metrics()
            
            # Collect system metrics
            self._collect_system_metrics()
            
            # Collect application metrics
            self._collect_application_metrics()
            
        except Exception as e:
            logger.error(f"Metric collection failed: {str(e)}")

    def _collect_memory_metrics(self) -> None:
        """Collect memory performance metrics."""
        try:
            memory_status = self.memory_manager.get_memory_status()
            
            # Record memory usage
            memory_metric = PerformanceMetric(
                name="memory_usage_mb",
                value=memory_status['process_memory_mb'],
                unit="MB",
                metric_type=MetricType.MEMORY,
                timestamp=datetime.now(),
                tags={'source': 'memory_manager'}
            )
            self._record_metric(memory_metric)
            
            # Check for memory alerts
            if self.enable_alerting:
                self.alert_manager.check_threshold(
                    "memory_usage_mb", 
                    memory_status['process_memory_mb'],
                    MetricType.MEMORY,
                    memory_status
                )
                
        except Exception as e:
            logger.error(f"Memory metrics collection failed: {str(e)}")

    def _collect_loading_metrics(self) -> None:
        """Collect loading performance metrics."""
        try:
            # Get cache statistics
            cache_stats = self.progressive_loader.get_cache_stats()
            
            # Record cache hit ratio
            if cache_stats['cached_entries'] > 0:
                cache_metric = PerformanceMetric(
                    name="cache_hit_ratio",
                    value=0.8,  # This would be calculated from actual cache hits
                    unit="ratio",
                    metric_type=MetricType.LOADING,
                    timestamp=datetime.now(),
                    tags={'source': 'progressive_loader'}
                )
                self._record_metric(cache_metric)
                
        except Exception as e:
            logger.error(f"Loading metrics collection failed: {str(e)}")

    def _collect_rendering_metrics(self) -> None:
        """Collect rendering performance metrics."""
        try:
            # Get rendering metrics
            rendering_metrics = self.rendering_manager._current_metrics
            
            if rendering_metrics:
                # Record FPS
                fps_metric = PerformanceMetric(
                    name="rendering_fps",
                    value=rendering_metrics.fps,
                    unit="FPS",
                    metric_type=MetricType.RENDERING,
                    timestamp=datetime.now(),
                    tags={'source': 'rendering_manager'}
                )
                self._record_metric(fps_metric)
                
                # Record GPU memory usage
                gpu_memory_metric = PerformanceMetric(
                    name="gpu_memory_usage_mb",
                    value=rendering_metrics.gpu_memory_used_mb,
                    unit="MB",
                    metric_type=MetricType.RENDERING,
                    timestamp=datetime.now(),
                    tags={'source': 'rendering_manager'}
                )
                self._record_metric(gpu_memory_metric)
                
                # Check for rendering alerts
                if self.enable_alerting:
                    self.alert_manager.check_threshold(
                        "rendering_fps",
                        rendering_metrics.fps,
                        MetricType.RENDERING,
                        asdict(rendering_metrics)
                    )
                    
        except Exception as e:
            logger.error(f"Rendering metrics collection failed: {str(e)}")

    def _collect_system_metrics(self) -> None:
        """Collect system performance metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_metric = PerformanceMetric(
                name="cpu_usage_percent",
                value=cpu_percent,
                unit="%",
                metric_type=MetricType.SYSTEM,
                timestamp=datetime.now(),
                tags={'source': 'psutil'}
            )
            self._record_metric(cpu_metric)
            
            # Memory usage
            memory = psutil.virtual_memory()
            system_memory_metric = PerformanceMetric(
                name="system_memory_percent",
                value=memory.percent,
                unit="%",
                metric_type=MetricType.SYSTEM,
                timestamp=datetime.now(),
                tags={'source': 'psutil'}
            )
            self._record_metric(system_memory_metric)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            disk_metric = PerformanceMetric(
                name="disk_usage_percent",
                value=disk_percent,
                unit="%",
                metric_type=MetricType.SYSTEM,
                timestamp=datetime.now(),
                tags={'source': 'psutil'}
            )
            self._record_metric(disk_metric)
            
            # Check for system alerts
            if self.enable_alerting:
                self.alert_manager.check_threshold(
                    "cpu_usage_percent",
                    cpu_percent,
                    MetricType.SYSTEM,
                    {'cpu_count': psutil.cpu_count()}
                )
                
        except Exception as e:
            logger.error(f"System metrics collection failed: {str(e)}")

    def _collect_application_metrics(self) -> None:
        """Collect application-specific metrics."""
        try:
            # Active file loads
            active_loads = len(self.progressive_loader._active_loads)
            loads_metric = PerformanceMetric(
                name="active_file_loads",
                value=active_loads,
                unit="count",
                metric_type=MetricType.APPLICATION,
                timestamp=datetime.now(),
                tags={'source': 'application'}
            )
            self._record_metric(loads_metric)
            
            # Active alerts count
            active_alerts = len(self.alert_manager.get_active_alerts())
            alerts_metric = PerformanceMetric(
                name="active_alerts_count",
                value=active_alerts,
                unit="count",
                metric_type=MetricType.APPLICATION,
                timestamp=datetime.now(),
                tags={'source': 'alert_manager'}
            )
            self._record_metric(alerts_metric)
            
        except Exception as e:
            logger.error(f"Application metrics collection failed: {str(e)}")

    def _record_metric(self, metric: PerformanceMetric) -> None:
        """Record a performance metric."""
        self._last_metrics[metric.name] = metric.value
        
        if self.enable_profiling:
            self.profiler.record_metric(metric)
            
        self.metric_recorded.emit(metric)

    def _capture_snapshot(self) -> None:
        """Capture comprehensive performance snapshot."""
        try:
            # Collect all recent metrics
            recent_metrics = []
            if self.enable_profiling:
                with self.profiler._lock:
                    recent_metrics = list(self.profiler._metric_history)[-100:]
            
            # Get active alerts
            active_alerts = self.alert_manager.get_active_alerts()
            
            # Get system information
            system_info = {
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'platform': psutil.os.name,
                'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
            }
            
            # Get application state
            application_state = {
                'monitoring_active': self._monitoring_active,
                'config': self.config,
                'thresholds': asdict(self.thresholds)
            }
            
            # Create snapshot
            snapshot = PerformanceSnapshot(
                timestamp=datetime.now(),
                metrics=recent_metrics,
                alerts=active_alerts,
                system_info=system_info,
                application_state=application_state
            )
            
            self.snapshot_captured.emit(snapshot)
            
            # Log snapshot summary
            logger.debug(f"Performance snapshot captured: {len(recent_metrics)} metrics, "
                        f"{len(active_alerts)} active alerts")
            
        except Exception as e:
            logger.error(f"Snapshot capture failed: {str(e)}")

    def _on_alert(self, alert: PerformanceAlert) -> None:
        """Handle performance alert."""
        self.alert_triggered.emit(alert)

    def profile_operation_start(self, operation_name: str) -> None:
        """Start profiling an operation."""
        self._operation_start_times[operation_name] = time.time()

    def profile_operation_end(self, operation_name: str) -> None:
        """End profiling an operation."""
        start_time = self._operation_start_times.pop(operation_name, None)
        if start_time:
            duration = time.time() - start_time
            if self.enable_profiling:
                self.profiler.profile_operation(operation_name, duration)

    def start_operation(self, operation_id: str, metadata: Dict[str, Any] = None) -> str:
        """Start profiling an operation (alias for profile_operation_start).
        
        Args:
            operation_id: Unique identifier for the operation
            metadata: Optional metadata dictionary
            
        Returns:
            The operation_id for tracking
        """
        self.profile_operation_start(operation_id)
        return operation_id

    def end_operation(self, operation_id: str, success: bool = True, error_message: str = None) -> None:
        """End profiling an operation (alias for profile_operation_end).
        
        Args:
            operation_id: Unique identifier for the operation
            success: Whether the operation completed successfully
            error_message: Optional error message if operation failed
        """
        self.profile_operation_end(operation_id)
        # Could log success/failure here if needed
        if not success and error_message:
            logger.error(f"Operation {operation_id} failed: {error_message}")

    def get_current_metrics(self) -> Dict[str, float]:
        """Get current metric values."""
        return self._last_metrics.copy()

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        try:
            # Get trends for key metrics
            trends = {}
            key_metrics = ['memory_usage_mb', 'rendering_fps', 'cpu_usage_percent']
            
            for metric in key_metrics:
                trends[metric] = self.profiler.get_metric_trend(metric)
            
            # Get operation statistics
            operation_stats = {}
            if self.enable_profiling:
                with self.profiler._lock:
                    for operation_name in self.profiler._operation_profiles:
                        operation_stats[operation_name] = self.profiler.get_operation_stats(operation_name)
            
            # Get active alerts
            active_alerts = self.alert_manager.get_active_alerts()
            
            return {
                'current_metrics': self._last_metrics,
                'metric_trends': trends,
                'operation_statistics': operation_stats,
                'active_alerts': [asdict(alert) for alert in active_alerts],
                'monitoring_status': {
                    'active': self._monitoring_active,
                    'interval_seconds': self.monitoring_interval,
                    'profiling_enabled': self.enable_profiling,
                    'alerting_enabled': self.enable_alerting
                },
                'system_info': {
                    'cpu_count': psutil.cpu_count(),
                    'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                    'platform': psutil.os.name
                }
            }
            
        except Exception as e:
            logger.error(f"Performance report generation failed: {str(e)}")
            return {'error': str(e)}

    def export_metrics(self, file_path: str, duration_hours: int = 24) -> None:
        """Export performance metrics to file."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=duration_hours)
            
            with self.profiler._lock:
                relevant_metrics = [
                    asdict(metric) for metric in self.profiler._metric_history
                    if metric.timestamp >= cutoff_time
                ]
            
            export_data = {
                'export_time': datetime.now().isoformat(),
                'duration_hours': duration_hours,
                'metrics': relevant_metrics,
                'system_info': {
                    'cpu_count': psutil.cpu_count(),
                    'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                    'platform': psutil.os.name
                }
            }
            
            with open(file_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
                
            logger.info(f"Performance metrics exported to {file_path}")
            
        except Exception as e:
            logger.error(f"Metrics export failed: {str(e)}")

    def shutdown(self) -> None:
        """Shutdown the performance monitor."""
        self.stop_monitoring()
        logger.info("Performance monitor shutdown completed")


# Global performance monitor instance
_performance_monitor: Optional[RealTimePerformanceMonitor] = None


def get_performance_monitor() -> RealTimePerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = RealTimePerformanceMonitor()
    return _performance_monitor


def start_performance_monitoring() -> None:
    """Start global performance monitoring."""
    monitor = get_performance_monitor()
    monitor.start_monitoring()


def stop_performance_monitoring() -> None:
    """Stop global performance monitoring."""
    monitor = get_performance_monitor()
    monitor.stop_monitoring()


def get_performance_report() -> Dict[str, Any]:
    """Get comprehensive performance report."""
    monitor = get_performance_monitor()
    return monitor.get_performance_report()


@contextmanager
def profile_operation(operation_name: str):
    """Context manager for profiling operations."""
    monitor = get_performance_monitor()
    monitor.profile_operation_start(operation_name)
    try:
        yield
    finally:
        monitor.profile_operation_end(operation_name)


def monitor_operation(operation_name: str):
    """Decorator for profiling operations."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_performance_monitor()
            monitor.profile_operation_start(operation_name)
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                monitor.profile_operation_end(operation_name)
        return wrapper
    return decorator
