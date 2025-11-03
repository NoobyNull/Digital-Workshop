"""
Float Cache Performance Analyzer

This module provides performance measurement and validation capabilities
for the float caching system. It measures the actual performance
bottlenecks and validates improvement assumptions.
"""

import logging
import time
import threading
from dataclasses import dataclass
from typing import Dict, List, Any
from pathlib import Path
import psutil

from .logging_config import get_logger


@dataclass
class FloatParsingMetrics:
    """Metrics for float parsing performance analysis."""
    file_path: str
    file_size_bytes: int
    triangle_count: int
    
    # Timing metrics
    total_parse_time: float = 0.0
    float_decode_time: float = 0.0
    struct_unpack_time: float = 0.0
    object_creation_time: float = 0.0
    array_creation_time: float = 0.0
    
    # Memory metrics
    peak_memory_mb: float = 0.0
    baseline_memory_mb: float = 0.0
    final_memory_mb: float = 0.0
    
    # Cache metrics
    cache_hit: bool = False
    cache_load_time: float = 0.0
    
    # System metrics
    cpu_usage_percent: float = 0.0
    io_read_mb_per_sec: float = 0.0


@dataclass
class CachePerformanceStats:
    """Aggregate cache performance statistics."""
    total_files_processed: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    
    total_parse_time_saved: float = 0.0
    average_parse_time_reduction: float = 0.0
    
    total_memory_overhead_mb: float = 0.0
    cache_disk_usage_mb: float = 0.0
    
    hit_ratio: float = 0.0
    
    def update_hit_ratio(self) -> None:
        """Update cache hit ratio."""
        total = self.cache_hits + self.cache_misses
        if total > 0:
            self.hit_ratio = self.cache_hits / total


class FloatCacheAnalyzer:
    """
    Analyzes float parsing performance and validates caching improvements.
    
    This class provides comprehensive measurement capabilities to:
    1. Identify actual performance bottlenecks
    2. Measure cache effectiveness
    3. Validate performance improvement assumptions
    4. Monitor memory usage patterns
    """
    
    def __init__(self):
        """Initialize the float cache analyzer."""
        self.logger = get_logger(__name__)
        self.metrics: List[FloatParsingMetrics] = []
        self.aggregate_stats = CachePerformanceStats()
        self._lock = threading.RLock()
        self._process = psutil.Process()
        
    def start_analysis(self, file_path: str) -> Dict[str, Any]:
        """
        Start performance analysis for a file.
        
        Args:
            file_path: Path to the file being analyzed
            
        Returns:
            Analysis context dictionary
        """
        context = {
            'file_path': file_path,
            'start_time': time.time(),
            'start_memory': self._get_memory_mb(),
            'baseline_cpu': self._get_cpu_usage(),
            'float_decode_start': None,
            'struct_unpack_start': None,
            'object_creation_start': None,
            'array_creation_start': None
        }
        
        self.logger.info(
            "Starting float cache analysis",
            extra={
                "file_path": file_path,
                "file_size_mb": Path(file_path).stat().st_size / (1024*1024),
                "start_memory_mb": context['start_memory']
            }
        )
        
        return context
    
    def mark_float_decode_start(self, context: Dict[str, Any]) -> None:
        """Mark the start of float decoding."""
        context['float_decode_start'] = time.time()
        
    def mark_float_decode_end(self, context: Dict[str, Any]) -> None:
        """Mark the end of float decoding."""
        if context['float_decode_start']:
            decode_time = time.time() - context['float_decode_start']
            context['float_decode_time'] = decode_time
            self.logger.debug(f"Float decode completed in {decode_time:.3f}s")
    
    def mark_struct_unpack_start(self, context: Dict[str, Any]) -> None:
        """Mark the start of struct unpack operations."""
        context['struct_unpack_start'] = time.time()
        
    def mark_struct_unpack_end(self, context: Dict[str, Any]) -> None:
        """Mark the end of struct unpack operations."""
        if context['struct_unpack_start']:
            unpack_time = time.time() - context['struct_unpack_start']
            context['struct_unpack_time'] = unpack_time
            self.logger.debug(f"Struct unpack completed in {unpack_time:.3f}s")
    
    def mark_object_creation_start(self, context: Dict[str, Any]) -> None:
        """Mark the start of Vector3D object creation."""
        context['object_creation_start'] = time.time()
        
    def mark_object_creation_end(self, context: Dict[str, Any]) -> None:
        """Mark the end of Vector3D object creation."""
        if context['object_creation_start']:
            creation_time = time.time() - context['object_creation_start']
            context['object_creation_time'] = creation_time
            if self.logger.isEnabledFor(logging.DEBUG):
                self.logger.debug(f"Object creation completed in {creation_time:.3f}s")
    
    def mark_array_creation_start(self, context: Dict[str, Any]) -> None:
        """Mark the start of NumPy array creation."""
        context['array_creation_start'] = time.time()
        
    def mark_array_creation_end(self, context: Dict[str, Any]) -> None:
        """Mark the end of NumPy array creation."""
        if context['array_creation_start']:
            array_time = time.time() - context['array_creation_start']
            context['array_creation_time'] = array_time
            self.logger.debug(f"Array creation completed in {array_time:.3f}s")
    
    def mark_cache_hit(self, context: Dict[str, Any], load_time: float) -> None:
        """Mark a cache hit with load time."""
        context['cache_hit'] = True
        context['cache_load_time'] = load_time
        self.logger.debug(f"Cache hit loaded in {load_time:.3f}s")
    
    def end_analysis(self, context: Dict[str, Any], triangle_count: int) -> FloatParsingMetrics:
        """
        End performance analysis and generate metrics.
        
        Args:
            context: Analysis context from start_analysis
            triangle_count: Number of triangles parsed
            
        Returns:
            Complete metrics for this analysis
        """
        end_time = time.time()
        end_memory = self._get_memory_mb()
        end_cpu = self._get_cpu_usage()
        
        file_path = context['file_path']
        file_size = Path(file_path).stat().st_size
        
        metrics = FloatParsingMetrics(
            file_path=file_path,
            file_size_bytes=file_size,
            triangle_count=triangle_count,
            total_parse_time=end_time - context['start_time'],
            float_decode_time=context.get('float_decode_time', 0.0),
            struct_unpack_time=context.get('struct_unpack_time', 0.0),
            object_creation_time=context.get('object_creation_time', 0.0),
            array_creation_time=context.get('array_creation_time', 0.0),
            baseline_memory_mb=context['start_memory'],
            peak_memory_mb=max(context['start_memory'], end_memory),
            final_memory_mb=end_memory,
            cache_hit=context.get('cache_hit', False),
            cache_load_time=context.get('cache_load_time', 0.0),
            cpu_usage_percent=end_cpu - context['baseline_cpu']
        )
        
        # Calculate IO throughput
        if metrics.total_parse_time > 0:
            metrics.io_read_mb_per_sec = (file_size / (1024*1024)) / metrics.total_parse_time
        
        with self._lock:
            self.metrics.append(metrics)
            
            # Update aggregate statistics
            self.aggregate_stats.total_files_processed += 1
            if metrics.cache_hit:
                self.aggregate_stats.cache_hits += 1
            else:
                self.aggregate_stats.cache_misses += 1
            
            self.aggregate_stats.update_hit_ratio()
        
        # Log comprehensive metrics
        self.logger.info(
            "Float cache analysis completed",
            extra={
                "file_path": file_path,
                "file_size_mb": file_size / (1024*1024),
                "triangle_count": triangle_count,
                "total_parse_time": metrics.total_parse_time,
                "float_decode_time": metrics.float_decode_time,
                "struct_unpack_time": metrics.struct_unpack_time,
                "object_creation_time": metrics.object_creation_time,
                "array_creation_time": metrics.array_creation_time,
                "cache_hit": metrics.cache_hit,
                "cache_load_time": metrics.cache_load_time,
                "memory_peak_mb": metrics.peak_memory_mb,
                "memory_delta_mb": metrics.final_memory_mb - metrics.baseline_memory_mb,
                "io_throughput_mb_per_sec": metrics.io_read_mb_per_sec,
                "cache_hit_ratio": self.aggregate_stats.hit_ratio
            }
        )
        
        return metrics
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive performance summary.
        
        Returns:
            Performance summary dictionary
        """
        with self._lock:
            if not self.metrics:
                return {"error": "No metrics available"}
            
            # Calculate averages and totals
            total_triangles = sum(m.triangle_count for m in self.metrics)
            total_file_size = sum(m.file_size_bytes for m in self.metrics)
            avg_parse_time = sum(m.total_parse_time for m in self.metrics) / len(self.metrics)
            avg_float_decode_time = sum(m.float_decode_time for m in self.metrics) / len(self.metrics)
            avg_struct_unpack_time = sum(m.struct_unpack_time for m in self.metrics) / len(self.metrics)
            
            # Calculate time breakdown percentages
            avg_decode_percentage = (avg_float_decode_time / avg_parse_time * 100) if avg_parse_time > 0 else 0
            avg_unpack_percentage = (avg_struct_unpack_time / avg_parse_time * 100) if avg_parse_time > 0 else 0
            
            # Cache performance
            cache_files = [m for m in self.metrics if m.cache_hit]
            non_cache_files = [m for m in self.metrics if not m.cache_hit]
            
            avg_cache_time = sum(m.cache_load_time for m in cache_files) / len(cache_files) if cache_files else 0
            avg_non_cache_time = sum(m.total_parse_time for m in non_cache_files) / len(non_cache_files) if non_cache_files else 0
            
            time_savings = avg_non_cache_time - avg_cache_time if avg_non_cache_time > 0 else 0
            time_savings_percentage = (time_savings / avg_non_cache_time * 100) if avg_non_cache_time > 0 else 0
            
            return {
                "summary": {
                    "total_files_processed": len(self.metrics),
                    "total_triangles_processed": total_triangles,
                    "total_file_size_mb": total_file_size / (1024*1024),
                    "cache_hit_ratio": self.aggregate_stats.hit_ratio,
                    "cache_hits": self.aggregate_stats.cache_hits,
                    "cache_misses": self.aggregate_stats.cache_misses
                },
                "timing": {
                    "average_total_parse_time": avg_parse_time,
                    "average_float_decode_time": avg_float_decode_time,
                    "average_struct_unpack_time": avg_struct_unpack_time,
                    "float_decode_percentage": avg_decode_percentage,
                    "struct_unpack_percentage": avg_unpack_percentage
                },
                "cache_performance": {
                    "average_cache_load_time": avg_cache_time,
                    "average_non_cache_parse_time": avg_non_cache_time,
                    "time_savings_per_file": time_savings,
                    "time_savings_percentage": time_savings_percentage
                },
                "memory": {
                    "average_peak_memory_mb": sum(m.peak_memory_mb for m in self.metrics) / len(self.metrics),
                    "average_memory_delta_mb": sum(m.final_memory_mb - m.baseline_memory_mb for m in self.metrics) / len(self.metrics)
                },
                "throughput": {
                    "average_io_mb_per_sec": sum(m.io_read_mb_per_sec for m in self.metrics) / len(self.metrics),
                    "triangles_per_second": total_triangles / sum(m.total_parse_time for m in self.metrics) if sum(m.total_parse_time for m in self.metrics) > 0 else 0
                }
            }
    
    def validate_performance_assumptions(self) -> Dict[str, bool]:
        """
        Validate key performance improvement assumptions.
        
        Returns:
            Dictionary of validation results
        """
        summary = self.get_performance_summary()
        
        validations = {}
        
        # Assumption 1: Float decoding is a significant bottleneck (>20% of parse time)
        if "timing" in summary:
            validations["float_decode_is_bottleneck"] = summary["timing"]["float_decode_percentage"] > 20
        
        # Assumption 2: Struct unpack is significant portion of float decode (>50%)
        if "timing" in summary and summary["timing"].get("average_float_decode_time", 0) > 0:
            unpack_percentage = summary["timing"]["average_struct_unpack_time"] / summary["timing"]["average_float_decode_time"] * 100
            validations["struct_unpack_is_major_component"] = unpack_percentage > 50
        
        # Assumption 3: Cache provides significant time savings (>30%)
        if "cache_performance" in summary:
            validations["cache_provides_significant_savings"] = summary["cache_performance"]["time_savings_percentage"] > 30
        
        # Assumption 4: Cache hit ratio is reasonable (>50% for repeated files)
        if "summary" in summary:
            validations["cache_hit_ratio_is_reasonable"] = summary["summary"]["cache_hit_ratio"] > 0.5
        
        # Assumption 5: Memory overhead is acceptable (<2x file size)
        if "memory" in summary and "summary" in summary:
            avg_file_mb = summary["summary"]["total_file_size_mb"] / summary["summary"]["total_files_processed"]
            avg_memory_mb = summary["memory"]["average_peak_memory_mb"]
            validations["memory_overhead_is_acceptable"] = avg_memory_mb < (avg_file_mb * 2)
        
        self.logger.info(
            "Performance assumption validation completed",
            extra={
                "validations": validations,
                "summary": summary
            }
        )
        
        return validations
    
    def _get_memory_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            return self._process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            return self._process.cpu_percent()
        except Exception:
            return 0.0
    
    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        with self._lock:
            self.metrics.clear()
            self.aggregate_stats = CachePerformanceStats()
        self.logger.info("Float cache analyzer metrics reset")


# Global analyzer instance
_float_cache_analyzer = None


def get_float_cache_analyzer() -> FloatCacheAnalyzer:
    """Get the global float cache analyzer instance."""
    _float_cache_analyzer = None
    if _float_cache_analyzer is None:
        _float_cache_analyzer = FloatCacheAnalyzer()
    return _float_cache_analyzer