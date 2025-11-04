"""
Database Health Monitoring and Performance Tracking System.

This module provides comprehensive monitoring of database health, performance metrics,
query analysis, connection monitoring, and automated alerting for database issues.
"""

import sqlite3
import threading
import time
import psutil
import os
import hashlib
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque, defaultdict

from ..logging_config import get_logger

logger = get_logger(__name__)


class HealthStatus(Enum):
    """Database health status enumeration."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class MetricType(Enum):
    """Metric type enumeration."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class HealthMetric:
    """Individual health metric."""

    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    unit: str
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class HealthAlert:
    """Health alert information."""

    alert_id: str
    metric_name: str
    status: HealthStatus
    message: str
    value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class QueryPerformance:
    """Query performance metrics."""

    query_hash: str
    query_text: str
    execution_count: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    last_execution: datetime
    error_count: int
    cache_hit_rate: float


@dataclass
class DatabaseHealthReport:
    """Comprehensive database health report."""

    timestamp: datetime
    overall_status: HealthStatus
    metrics: Dict[str, HealthMetric]
    alerts: List[HealthAlert]
    query_performance: List[QueryPerformance]
    connection_stats: Dict[str, Any]
    system_resources: Dict[str, Any]
    recommendations: List[str]


class DatabaseHealthMonitor:
    """Comprehensive database health monitoring system."""

    def __init__(self, db_path: str, monitoring_interval: int = 30):
        """
        Initialize database health monitor.

        Args:
            db_path: Database file path
            monitoring_interval: Monitoring interval in seconds
        """
        self.db_path = db_path
        self.monitoring_interval = monitoring_interval

        # Metrics storage
        self._metrics_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self._current_metrics: Dict[str, HealthMetric] = {}
        self._alerts: Dict[str, HealthAlert] = {}

        # Query performance tracking
        self._query_performance: Dict[str, QueryPerformance] = {}
        self._query_times: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # Connection monitoring
        self._connection_stats = {
            "active_connections": 0,
            "total_connections": 0,
            "connection_errors": 0,
            "avg_connection_time": 0.0,
        }

        # System monitoring
        self._system_baseline = {}
        self._monitoring_active = False
        self._monitoring_thread = None
        self._lock = threading.RLock()

        # Alert callbacks
        self._alert_callbacks: List[Callable] = []

        # Performance thresholds
        self._thresholds = {
            "query_time_warning": 1.0,  # seconds
            "query_time_critical": 5.0,  # seconds
            "connection_count_warning": 20,
            "connection_count_critical": 50,
            "disk_usage_warning": 0.80,  # 80%
            "disk_usage_critical": 0.95,  # 95%
            "memory_usage_warning": 0.80,  # 80%
            "memory_usage_critical": 0.95,  # 95%
            "error_rate_warning": 0.05,  # 5%
            "error_rate_critical": 0.10,  # 10%
        }

        # Start monitoring
        self.start_monitoring()

    def start_monitoring(self) -> None:
        """Start background health monitoring."""
        if self._monitoring_active:
            return

        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self._monitoring_thread.start()
        logger.info("Database health monitoring started")

    def stop_monitoring(self) -> None:
        """Stop background health monitoring."""
        self._monitoring_active = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5.0)
        logger.info("Database health monitoring stopped")

    def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._monitoring_active:
            try:
                self._collect_system_metrics()
                self._collect_database_metrics()
                self._check_thresholds()
                self._cleanup_old_data()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Health monitoring error: {str(e)}")
                time.sleep(5)  # Brief pause on error

    def _collect_system_metrics(self) -> None:
        """Collect system resource metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self._record_metric(
                "system.cpu.usage",
                cpu_percent,
                MetricType.GAUGE,
                "%",
                threshold_warning=80,
                threshold_critical=95,
            )

            # Memory usage
            memory = psutil.virtual_memory()
            self._record_metric(
                "system.memory.usage",
                memory.percent,
                MetricType.GAUGE,
                "%",
                threshold_warning=80,
                threshold_critical=95,
            )
            self._record_metric(
                "system.memory.available",
                memory.available / (1024**3),
                MetricType.GAUGE,
                "GB",
            )

            # Disk usage
            disk_usage = psutil.disk_usage(os.path.dirname(self.db_path))
            disk_percent = disk_usage.used / disk_usage.total
            self._record_metric(
                "system.disk.usage",
                disk_percent * 100,
                MetricType.GAUGE,
                "%",
                threshold_warning=80,
                threshold_critical=95,
            )
            self._record_metric(
                "system.disk.free", disk_usage.free / (1024**3), MetricType.GAUGE, "GB"
            )

            # Database file size
            if os.path.exists(self.db_path):
                db_size_mb = os.path.getsize(self.db_path) / (1024 * 1024)
                self._record_metric(
                    "database.file.size", db_size_mb, MetricType.GAUGE, "MB"
                )

        except Exception as e:
            logger.error(f"Failed to collect system metrics: {str(e)}")

    def _collect_database_metrics(self) -> None:
        """Collect database-specific metrics."""
        try:
            with self._create_connection() as conn:
                cursor = conn.cursor()

                # Database integrity
                cursor.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()
                integrity_status = 1.0 if integrity_result[0] == "ok" else 0.0
                self._record_metric(
                    "database.integrity", integrity_status, MetricType.GAUGE, "boolean"
                )

                # Database page count and size
                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                cursor.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]

                self._record_metric(
                    "database.pages.count", page_count, MetricType.GAUGE, "pages"
                )
                self._record_metric(
                    "database.pages.size", page_size, MetricType.GAUGE, "bytes"
                )

                # Database statistics
                cursor.execute("SELECT COUNT(*) FROM models")
                model_count = cursor.fetchone()[0]
                self._record_metric(
                    "database.models.count", model_count, MetricType.GAUGE, "count"
                )

                cursor.execute("SELECT COUNT(*) FROM model_metadata")
                metadata_count = cursor.fetchone()[0]
                self._record_metric(
                    "database.metadata.count", metadata_count, MetricType.GAUGE, "count"
                )

                # Connection statistics
                cursor.execute("PRAGMA database_list")
                databases = cursor.fetchall()
                self._record_metric(
                    "database.connections", len(databases), MetricType.GAUGE, "count"
                )

                # WAL mode status
                cursor.execute("PRAGMA journal_mode")
                journal_mode = cursor.fetchone()[0]
                self._record_metric(
                    "database.journal_mode",
                    1.0 if journal_mode.upper() == "WAL" else 0.0,
                    MetricType.GAUGE,
                    "boolean",
                )

        except Exception as e:
            logger.error(f"Failed to collect database metrics: {str(e)}")

    def _record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        unit: str,
        threshold_warning: Optional[float] = None,
        threshold_critical: Optional[float] = None,
        tags: Dict[str, str] = None,
    ) -> None:
        """
        Record a health metric.

        Args:
            name: Metric name
            value: Metric value
            type: Metric type
            unit: Unit of measurement
            threshold_warning: Warning threshold
            threshold_critical: Critical threshold
            tags: Additional tags
        """
        metric = HealthMetric(
            name=name,
            value=value,
            metric_type=metric_type,
            timestamp=datetime.now(),
            unit=unit,
            threshold_warning=threshold_warning,
            threshold_critical=threshold_critical,
            tags=tags or {},
        )

        with self._lock:
            self._current_metrics[name] = metric
            self._metrics_history[name].append(metric)

    def _check_thresholds(self) -> None:
        """Check metric thresholds and generate alerts."""
        with self._lock:
            for metric in self._current_metrics.values():
                self._check_metric_threshold(metric)

    def _check_metric_threshold(self, metric: HealthMetric) -> None:
        """
        Check a single metric against thresholds.

        Args:
            metric: Health metric to check
        """
        alert_key = f"{metric.name}_alert"

        # Determine status
        status = HealthStatus.HEALTHY
        threshold = None

        if (
            metric.threshold_critical is not None
            and metric.value >= metric.threshold_critical
        ):
            status = HealthStatus.CRITICAL
            threshold = metric.threshold_critical
        elif (
            metric.threshold_warning is not None
            and metric.value >= metric.threshold_warning
        ):
            status = HealthStatus.WARNING
            threshold = metric.threshold_warning

        # Create or update alert
        if status != HealthStatus.HEALTHY:
            if alert_key not in self._alerts or not self._alerts[alert_key].resolved:
                # Create new alert
                alert = HealthAlert(
                    alert_id=alert_key,
                    metric_name=metric.name,
                    status=status,
                    message=f"{metric.name} is {status.value}: {metric.value:.2f} {metric.unit} (threshold: {threshold})",
                    value=metric.value,
                    threshold=threshold,
                    timestamp=datetime.now(),
                    tags=metric.tags,
                )
                self._alerts[alert_key] = alert

                # Notify callbacks
                self._notify_alert_callbacks(alert)

                # Log alert
                if status == HealthStatus.CRITICAL:
                    logger.critical(f"CRITICAL: {alert.message}")
                else:
                    logger.warning(f"WARNING: {alert.message}")
            else:
                # Update existing alert
                self._alerts[alert_key].value = metric.value
                self._alerts[alert_key].timestamp = datetime.now()
        else:
            # Resolve alert if it exists
            if alert_key in self._alerts and not self._alerts[alert_key].resolved:
                self._alerts[alert_key].resolved = True
                self._alerts[alert_key].resolved_at = datetime.now()
                logger.info(f"Alert resolved: {metric.name}")

    def _notify_alert_callbacks(self, alert: HealthAlert) -> None:
        """Notify registered alert callbacks."""
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"Alert callback failed: {str(e)}")

    def _cleanup_old_data(self) -> None:
        """Clean up old metrics and alerts."""
        cutoff_time = datetime.now() - timedelta(hours=24)

        with self._lock:
            # Clean up old alerts
            resolved_alerts = [
                alert_id
                for alert_id, alert in self._alerts.items()
                if alert.resolved
                and alert.resolved_at
                and alert.resolved_at < cutoff_time
            ]

            for alert_id in resolved_alerts:
                del self._alerts[alert_id]

    def _create_connection(self) -> sqlite3.Connection:
        """Create a database connection for monitoring."""
        conn = sqlite3.connect(self.db_path, timeout=5.0, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def record_query_execution(
        self,
        query: str,
        execution_time: float,
        success: bool = True,
        cache_hit: bool = False,
    ) -> None:
        """
        Record query execution for performance tracking.

        Args:
            query: SQL query text
            execution_time: Execution time in seconds
            success: Whether query was successful
            cache_hit: Whether result came from cache
        """
        # Create query hash for tracking
        query_hash = hashlib.md5(query.encode()).hexdigest()

        with self._lock:
            # Record execution time
            self._query_times[query_hash].append(execution_time)

            # Update or create performance record
            if query_hash in self._query_performance:
                perf = self._query_performance[query_hash]
                perf.execution_count += 1
                perf.total_time += execution_time
                perf.avg_time = perf.total_time / perf.execution_count
                perf.min_time = min(perf.min_time, execution_time)
                perf.max_time = max(perf.max_time, execution_time)
                perf.last_execution = datetime.now()

                if not success:
                    perf.error_count += 1

                # Update cache hit rate
                if cache_hit:
                    perf.cache_hit_rate = (
                        perf.cache_hit_rate * (perf.execution_count - 1) + 1
                    ) / perf.execution_count
                else:
                    perf.cache_hit_rate = (
                        perf.cache_hit_rate * (perf.execution_count - 1)
                    ) / perf.execution_count
            else:
                # Create new performance record
                self._query_performance[query_hash] = QueryPerformance(
                    query_hash=query_hash,
                    query_text=query[:100] + "..." if len(query) > 100 else query,
                    execution_count=1,
                    total_time=execution_time,
                    avg_time=execution_time,
                    min_time=execution_time,
                    max_time=execution_time,
                    last_execution=datetime.now(),
                    error_count=0 if success else 1,
                    cache_hit_rate=1.0 if cache_hit else 0.0,
                )

            # Check for slow queries
            if execution_time > self._thresholds["query_time_critical"]:
                logger.critical(
                    f"Critical slow query detected: {execution_time:.2f}s - {query[:100]}"
                )
            elif execution_time > self._thresholds["query_time_warning"]:
                logger.warning(
                    f"Slow query detected: {execution_time:.2f}s - {query[:100]}"
                )

    def get_current_health_status(self) -> HealthStatus:
        """
        Get current overall health status.

        Returns:
            Overall health status
        """
        with self._lock:
            if not self._alerts:
                return HealthStatus.HEALTHY

            # Check for critical alerts
            critical_alerts = [
                a
                for a in self._alerts.values()
                if a.status == HealthStatus.CRITICAL and not a.resolved
            ]
            if critical_alerts:
                return HealthStatus.CRITICAL

            # Check for warning alerts
            warning_alerts = [
                a
                for a in self._alerts.values()
                if a.status == HealthStatus.WARNING and not a.resolved
            ]
            if warning_alerts:
                return HealthStatus.WARNING

            return HealthStatus.HEALTHY

    def get_health_metrics(
        self, metric_name: Optional[str] = None, time_range: Optional[timedelta] = None
    ) -> List[HealthMetric]:
        """
        Get health metrics.

        Args:
            metric_name: Specific metric name to retrieve
            time_range: Time range for metrics

        Returns:
            List of health metrics
        """
        with self._lock:
            if metric_name:
                if metric_name in self._metrics_history:
                    metrics = list(self._metrics_history[metric_name])
                else:
                    metrics = []
            else:
                metrics = []
                for history in self._metrics_history.values():
                    metrics.extend(list(history))

            # Filter by time range if specified
            if time_range:
                cutoff_time = datetime.now() - time_range
                metrics = [m for m in metrics if m.timestamp > cutoff_time]

            return metrics

    def get_active_alerts(self) -> List[HealthAlert]:
        """
        Get active (unresolved) alerts.

        Returns:
            List of active alerts
        """
        with self._lock:
            return [alert for alert in self._alerts.values() if not alert.resolved]

    def get_all_alerts(self) -> List[HealthAlert]:
        """
        Get all alerts (resolved and unresolved).

        Returns:
            List of all alerts
        """
        with self._lock:
            return list(self._alerts.values())

    def get_slow_queries(self, limit: int = 10) -> List[QueryPerformance]:
        """
        Get slowest queries.

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of slowest queries
        """
        with self._lock:
            queries = list(self._query_performance.values())
            queries.sort(key=lambda q: q.avg_time, reverse=True)
            return queries[:limit]

    def get_frequent_queries(self, limit: int = 10) -> List[QueryPerformance]:
        """
        Get most frequently executed queries.

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of most frequent queries
        """
        with self._lock:
            queries = list(self._query_performance.values())
            queries.sort(key=lambda q: q.execution_count, reverse=True)
            return queries[:limit]

    def get_error_prone_queries(self, limit: int = 10) -> List[QueryPerformance]:
        """
        Get queries with highest error rates.

        Args:
            limit: Maximum number of queries to return

        Returns:
            List of error-prone queries
        """
        with self._lock:
            queries = [
                q for q in self._query_performance.values() if q.execution_count > 0
            ]
            queries.sort(key=lambda q: q.error_count / q.execution_count, reverse=True)
            return queries[:limit]

    def generate_health_report(self) -> DatabaseHealthReport:
        """
        Generate comprehensive health report.

        Returns:
            Database health report
        """
        with self._lock:
            # Get current metrics
            current_metrics = dict(self._current_metrics)

            # Get active alerts
            active_alerts = self.get_active_alerts()

            # Get query performance
            query_performance = list(self._query_performance.values())

            # Get connection stats
            connection_stats = dict(self._connection_stats)

            # Get system resources
            system_resources = {
                "cpu_percent": self._current_metrics.get(
                    "system.cpu.usage",
                    HealthMetric("", 0, MetricType.GAUGE, "", datetime.now()),
                ).value,
                "memory_percent": self._current_metrics.get(
                    "system.memory.usage",
                    HealthMetric("", 0, MetricType.GAUGE, "", datetime.now()),
                ).value,
                "disk_percent": self._current_metrics.get(
                    "system.disk.usage",
                    HealthMetric("", 0, MetricType.GAUGE, "", datetime.now()),
                ).value,
            }

            # Generate recommendations
            recommendations = self._generate_recommendations(
                current_metrics, active_alerts, query_performance
            )

            return DatabaseHealthReport(
                timestamp=datetime.now(),
                overall_status=self.get_current_health_status(),
                metrics=current_metrics,
                alerts=active_alerts,
                query_performance=query_performance,
                connection_stats=connection_stats,
                system_resources=system_resources,
                recommendations=recommendations,
            )

    def _generate_recommendations(
        self,
        metrics: Dict[str, HealthMetric],
        alerts: List[HealthAlert],
        query_performance: List[QueryPerformance],
    ) -> List[str]:
        """
        Generate health improvement recommendations.

        Args:
            metrics: Current metrics
            alerts: Active alerts
            query_performance: Query performance data

        Returns:
            List of recommendations
        """
        recommendations = []

        # Check for performance issues
        slow_queries = [q for q in query_performance if q.avg_time > 1.0]
        if slow_queries:
            recommendations.append(
                f"Consider optimizing {len(slow_queries)} slow queries (avg time > 1s)"
            )

        # Check for high error rates
        error_prone = [
            q
            for q in query_performance
            if q.execution_count > 0 and q.error_count / q.execution_count > 0.05
        ]
        if error_prone:
            recommendations.append(
                f"Review {len(error_prone)} queries with high error rates (>5%)"
            )

        # Check system resources
        cpu_metric = metrics.get("system.cpu.usage")
        if cpu_metric and cpu_metric.value > 80:
            recommendations.append(
                "High CPU usage detected - consider optimizing queries or upgrading hardware"
            )

        memory_metric = metrics.get("system.memory.usage")
        if memory_metric and memory_metric.value > 80:
            recommendations.append(
                "High memory usage detected - consider increasing system memory"
            )

        disk_metric = metrics.get("system.disk.usage")
        if disk_metric and disk_metric.value > 80:
            recommendations.append(
                "High disk usage detected - consider cleaning up old data or expanding storage"
            )

        # Check database integrity
        integrity_metric = metrics.get("database.integrity")
        if integrity_metric and integrity_metric.value < 1.0:
            recommendations.append(
                "Database integrity issues detected - run integrity check and repair if necessary"
            )

        # Check connection count
        conn_metric = metrics.get("database.connections")
        if conn_metric and conn_metric.value > 20:
            recommendations.append(
                "High number of database connections - consider connection pooling"
            )
