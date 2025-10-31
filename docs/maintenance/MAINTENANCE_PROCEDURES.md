
# Candy-Cadence Maintenance Procedures

## Overview

This document provides comprehensive maintenance procedures for the Candy-Cadence application. It covers system maintenance, performance monitoring, database management, logging maintenance, and backup/recovery procedures to ensure long-term system reliability and performance.

## Table of Contents

1. [System Maintenance Overview](#system-maintenance-overview)
2. [Database Maintenance](#database-maintenance)
3. [Performance Monitoring](#performance-monitoring)
4. [Logging and Error Handling Maintenance](#logging-and-error-handling-maintenance)
5. [Backup and Recovery Procedures](#backup-and-recovery-procedures)
6. [System Health Checks](#system-health-checks)
7. [Security Maintenance](#security-maintenance)
8. [Update and Upgrade Procedures](#update-and-upgrade-procedures)
9. [Maintenance Scheduling](#maintenance-scheduling)
10. [Emergency Procedures](#emergency-procedures)

## System Maintenance Overview

### Maintenance Philosophy

Candy-Cadence follows a proactive maintenance approach with:
- **Preventive Maintenance**: Regular checks to prevent issues
- **Predictive Maintenance**: Monitoring trends to anticipate problems
- **Corrective Maintenance**: Fixing issues when they occur
- **Adaptive Maintenance**: Adjusting procedures based on usage patterns

### Maintenance Categories

#### Daily Maintenance
- Log file rotation and cleanup
- Performance metrics collection
- Basic system health checks
- User session monitoring

#### Weekly Maintenance
- Database optimization
- Cache cleanup and optimization
- Performance trend analysis
- Security log review

#### Monthly Maintenance
- Full system backup
- Database maintenance and optimization
- Performance benchmarking
- Security audit
- Documentation updates

#### Quarterly Maintenance
- Complete system health assessment
- Performance optimization review
- Security penetration testing
- Disaster recovery testing
- Architecture review

## Database Maintenance

### Database Health Monitoring

#### Connection Pool Monitoring
```python
# Monitor database connections
def check_database_health():
    """Check database connection pool health."""
    try:
        # Check active connections
        active_connections = database.get_active_connections()
        max_connections = database.get_max_connections()
        
        connection_usage = (active_connections / max_connections) * 100
        
        if connection_usage > 80:
            logger.warning(f"High database connection usage: {connection_usage:.1f}%")
        
        # Check for deadlocks
        deadlocks = database.get_deadlock_count()
        if deadlocks > 0:
            logger.error(f"Database deadlocks detected: {deadlocks}")
        
        return {
            'active_connections': active_connections,
            'max_connections': max_connections,
            'usage_percentage': connection_usage,
            'deadlocks': deadlocks
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return None
```

#### Query Performance Monitoring
```python
def analyze_slow_queries():
    """Analyze slow database queries."""
    try:
        # Get slow query log
        slow_queries = database.get_slow_queries(threshold_ms=1000)
        
        for query in slow_queries:
            logger.info(f"Slow query detected: {query['sql'][:100]}... "
                       f"Execution time: {query['execution_time']}ms")
        
        # Analyze query patterns
        query_patterns = {}
        for query in slow_queries:
            pattern = query['sql'][:50]  # First 50 characters
            if pattern not in query_patterns:
                query_patterns[pattern] = 0
            query_patterns[pattern] += 1
        
        # Identify frequently slow queries
        frequent_slow = {k: v for k, v in query_patterns.items() if v > 5}
        if frequent_slow:
            logger.warning(f"Frequently slow queries detected: {frequent_slow}")
        
        return slow_queries
    except Exception as e:
        logger.error(f"Query analysis failed: {e}")
        return []
```

### Database Optimization

#### Index Maintenance
```python
def optimize_database_indexes():
    """Optimize database indexes."""
    try:
        # Analyze index usage
        unused_indexes = database.get_unused_indexes()
        if unused_indexes:
            logger.info(f"Unused indexes found: {unused_indexes}")
        
        # Check for missing indexes
        missing_indexes = database.get_missing_indexes()
        if missing_indexes:
            logger.info(f"Missing indexes recommended: {missing_indexes}")
        
        # Rebuild fragmented indexes
        fragmented_indexes = database.get_fragmented_indexes(threshold=30)
        for index in fragmented_indexes:
            database.rebuild_index(index)
            logger.info(f"Rebuilt fragmented index: {index}")
        
        return {
            'unused_indexes': unused_indexes,
            'missing_indexes': missing_indexes,
            'rebuilt_indexes': len(fragmented_indexes)
        }
    except Exception as e:
        logger.error(f"Index optimization failed: {e}")
        return None
```

#### Table Maintenance
```python
def perform_table_maintenance():
    """Perform database table maintenance."""
    try:
        # Analyze table statistics
        table_stats = database.get_table_statistics()
        
        for table_name, stats in table_stats.items():
            # Check table fragmentation
            if stats['fragmentation_percent'] > 30:
                database.defragment_table(table_name)
                logger.info(f"Defragmented table: {table_name}")
            
            # Check table size growth
            if stats['size_growth_rate'] > 10:  # 10% growth
                logger.warning(f"Rapid table growth detected: {table_name} "
                             f"({stats['size_growth_rate']:.1f}% growth)")
        
        # Update table statistics
        database.update_statistics()
        logger.info("Updated database table statistics")
        
        return table_stats
    except Exception as e:
        logger.error(f"Table maintenance failed: {e}")
        return None
```

### Database Backup Procedures

#### Automated Backup Script
```python
import sqlite3
import shutil
import gzip
from datetime import datetime
from pathlib import Path

def create_database_backup(backup_dir: Path, retention_days: int = 30):
    """Create compressed database backup."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"candy_cadence_backup_{timestamp}.db.gz"
        backup_path = backup_dir / backup_filename
        
        # Ensure backup directory exists
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Create backup with compression
        with open('data/candy_cadence.db', 'rb') as source:
            with gzip.open(backup_path, 'wb') as compressed:
                shutil.copyfileobj(source, compressed)
        
        logger.info(f"Database backup created: {backup_path}")
        
        # Clean up old backups
        cleanup_old_backups(backup_dir, retention_days)
        
        return backup_path
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        return None

def cleanup_old_backups(backup_dir: Path, retention_days: int):
    """Remove backups older than retention period."""
    try:
        cutoff_date = datetime.now().timestamp() - (retention_days * 24 * 60 * 60)
        
        for backup_file in backup_dir.glob("candy_cadence_backup_*.db.gz"):
            if backup_file.stat().st_mtime < cutoff_date:
                backup_file.unlink()
                logger.info(f"Removed old backup: {backup_file}")
    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")
```

#### Backup Verification
```python
def verify_database_backup(backup_path: Path):
    """Verify database backup integrity."""
    try:
        # Test backup file integrity
        with gzip.open(backup_path, 'rb') as f:
            # Try to read the first few bytes
            header = f.read(100)
            if not header:
                raise ValueError("Empty backup file")
        
        # Create temporary database from backup
        temp_db = Path("temp_verify.db")
        with gzip.open(backup_path, 'rb') as source:
            with open(temp_db, 'wb') as dest:
                shutil.copyfileobj(source, dest)
        
        # Test database integrity
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Check table integrity
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        if result[0] != 'ok':
            raise ValueError(f"Database integrity check failed: {result}")
        
        # Check basic queries
        cursor.execute("SELECT COUNT(*) FROM models")
        model_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM metadata")
        metadata_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Clean up temporary file
        temp_db.unlink()
        
        logger.info(f"Backup verification successful: {model_count} models, "
                   f"{metadata_count} metadata records")
        
        return True
    except Exception as e:
        logger.error(f"Backup verification failed: {e}")
        return False
```

## Performance Monitoring

### System Performance Metrics

#### Memory Usage Monitoring
```python
import psutil
import threading
import time
from collections import deque

class MemoryMonitor:
    """Monitor application memory usage."""
    
    def __init__(self, alert_threshold_mb: int = 1500):
        self.alert_threshold_mb = alert_threshold_mb
        self.monitoring = False
        self.memory_history = deque(maxlen=100)
        self.monitor_thread = None
    
    def start_monitoring(self):
        """Start memory monitoring."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.start()
        logger.info("Memory monitoring started")
    
    def stop_monitoring(self):
        """Stop memory monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        logger.info("Memory monitoring stopped")
    
    def _monitor_loop(self):
        """Memory monitoring loop."""
        process = psutil.Process()
        
        while self.monitoring:
            try:
                # Get memory usage
                memory_info = process.memory_info()
                memory_mb = memory_info.rss / 1024 / 1024
                
                # Store in history
                self.memory_history.append({
                    'timestamp': time.time(),
                    'memory_mb': memory_mb,
                    'memory_percent': process.memory_percent()
                })
                
                # Check for alerts
                if memory_mb > self.alert_threshold_mb:
                    logger.warning(f"High memory usage: {memory_mb:.1f} MB "
                                 f"({process.memory_percent():.1f}%)")
                
                # Analyze memory trends
                if len(self.memory_history) >= 10:
                    self._analyze_memory_trends()
                
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                time.sleep(60)  # Wait longer on error
    
    def _analyze_memory_trends(self):
        """Analyze memory usage trends."""
        recent_readings = list(self.memory_history)[-10:]
        
        # Calculate trend
        if len(recent_readings) >= 2:
            first_reading = recent_readings[0]['memory_mb']
            last_reading = recent_readings[-1]['memory_mb']
            trend = (last_reading - first_reading) / len(recent_readings)
            
            # Detect memory leak
            if trend > 5:  # More than 5MB increase per reading
                logger.warning(f"Potential memory leak detected: "
                             f"{trend:.1f} MB increase per reading")
            
            # Calculate average and peak
            avg_memory = sum(r['memory_mb'] for r in recent_readings) / len(recent_readings)
            peak_memory = max(r['memory_mb'] for r in recent_readings)
            
            logger.info(f"Memory stats - Average: {avg_memory:.1f} MB, "
                       f"Peak: {peak_memory:.1f} MB, Trend: {trend:.1f} MB/reading")
    
    def get_memory_report(self):
        """Get current memory usage report."""
        if not self.memory_history:
            return None
        
        latest = self.memory_history[-1]
        return {
            'current_memory_mb': latest['memory_mb'],
            'current_percent': latest['memory_percent'],
            'history_count': len(self.memory_history),
            'peak_memory_mb': max(r['memory_mb'] for r in self.memory_history),
            'average_memory_mb': sum(r['memory_mb'] for r in self.memory_history) / len(self.memory_history)
        }
```

#### Performance Benchmarking
```python
import time
import statistics
from typing import List, Dict, Any

class PerformanceBenchmark:
    """Performance benchmarking and regression detection."""
    
    def __init__(self, baseline_file: str = "performance_baseline.json"):
        self.baseline_file = baseline_file
        self.baseline_data = self._load_baseline()
    
    def benchmark_model_loading(self, test_files: List[Path]) -> Dict[str, Any]:
        """Benchmark model loading performance."""
        results = []
        
        for file_path in test_files:
            try:
                start_time = time.perf_counter()
                
                # Load model
                model_service = ModelService(...)
                success = model_service.load_model(file_path)
                
                end_time = time.perf_counter()
                load_time = end_time - start_time
                
                # Get file size
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                
                results.append({
                    'file_path': str(file_path),
                    'file_size_mb': file_size_mb,
                    'load_time_seconds': load_time,
                    'success': success,
                    'timestamp': time.time()
                })
                
                logger.info(f"Benchmarked {file_path.name}: {load_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Benchmark failed for {file_path}: {e}")
                results.append({
                    'file_path': str(file_path),
                    'error': str(e),
                    'timestamp': time.time()
                })
        
        return self._analyze_benchmark_results(results)
    
    def _analyze_benchmark_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Analyze benchmark results and detect regressions."""
        successful_results = [r for r in results if r.get('success', False)]
        
        if not successful_results:
            return {'error': 'No successful benchmarks'}
        
        # Calculate statistics
        load_times = [r['load_time_seconds'] for r in successful_results]
        file_sizes = [r['file_size_mb'] for r in successful_results]
        
        analysis = {
            'total_tests': len(results),
            'successful_tests': len(successful_results),
            'failed_tests': len(results) - len(successful_results),
            'load_time_stats': {
                'mean': statistics.mean(load_times),
                'median': statistics.median(load_times),
                'min': min(load_times),
                'max': max(load_times),
                'stdev': statistics.stdev(load_times) if len(load_times) > 1 else 0
            },
            'file_size_stats': {
                'mean': statistics.mean(file_sizes),
                'median': statistics.median(file_sizes),
                'min': min(file_sizes),
                'max': max(file_sizes)
            },
            'results': results
        }
        
        # Check for performance regressions
        regressions = self._check_performance_regression(analysis)
        if regressions:
            analysis['regressions'] = regressions
            logger.warning(f"Performance regressions detected: {regressions}")
        
        return analysis
    
    def _check_performance_regression(self, current_results: Dict) -> List[str]:
        """Check for performance regressions against baseline."""
        regressions = []
        
        if not self.baseline_data:
            return regressions
        
        current_mean = current_results['load_time_stats']['mean']
        baseline_mean = self.baseline_data.get('load_time_stats', {}).get('mean')
        
        if baseline_mean:
            regression_threshold = 0.1  # 10% regression threshold
            if current_mean > baseline_mean * (1 + regression_threshold):
                regression_percent = ((current_mean - baseline_mean) / baseline_mean) * 100
                regressions.append(f"Load time regression: {regression_percent:.1f}% slower")
        
        return regressions
    
    def save_baseline(self, results: Dict):
        """Save current results as baseline."""
        try:
            import json
            with open(self.baseline_file, 'w') as f:
                json.dump(results, f, indent=2)
            logger.info(f"Performance baseline saved: {self.baseline_file}")
        except Exception as e:
            logger.error(f"Failed to save baseline: {e}")
    
    def _load_baseline(self) -> Dict:
        """Load performance baseline."""
        try:
            import json
            if Path(self.baseline_file).exists():
                with open(self.baseline_file, 'r') as f:
                    baseline = json.load(f)
                logger.info(f"Performance baseline loaded: {self.baseline_file}")
                return baseline
        except Exception as e:
            logger.error(f"Failed to load baseline: {e}")
        return {}
```

### Performance Optimization

#### Cache Optimization
```python
class CacheOptimizer:
    """Optimize application cache performance."""
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
    
    def analyze_cache_performance(self):
        """Analyze cache hit/miss ratios and optimize."""
        try:
            # Get cache statistics
            stats = self.cache_manager.get_statistics()
            
            hit_ratio = stats['hits'] / (stats['hits'] + stats['misses']) if (stats['hits'] + stats['misses']) > 0 else 0
            
            logger.info(f"Cache performance - Hit ratio: {hit_ratio:.2%}, "
                       f"Hits: {stats['hits']}, Misses: {stats['misses']}")
            
            # Optimize cache size if hit ratio is low
            if hit_ratio < 0.7:  # Less than 70% hit ratio
                logger.warning("Low cache hit ratio detected, optimizing cache size")
                self._optimize_cache_size()
            
            # Clean up expired entries
            expired_count = self.cache_manager.cleanup_expired()
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired cache entries")
            
            return {
                'hit_ratio': hit_ratio,
                'total_requests': stats['hits'] + stats['misses'],
                'expired_cleaned': expired_count
            }
            
        except Exception as e:
            logger.error(f"Cache analysis failed: {e}")
            return None
    
    def _optimize_cache_size(self):
        """Optimize cache size based on usage patterns."""
        try:
            # Analyze cache usage patterns
            usage_patterns = self.cache_manager.analyze_usage_patterns()
            
            # Adjust cache size based on patterns
            if usage_patterns['eviction_rate'] > 0.5:  # High eviction rate
                new_size = int(self.cache_manager.max_size * 1.5)
                self.cache_manager.set_max_size(new_size)
                logger.info(f"Increased cache size to {new_size}")
            elif usage_patterns['low_utilization'] < 0.3:  # Low utilization
                new_size = int(self.cache_manager.max_size * 0.7)
                self.cache_manager.set_max_size(new_size)
                logger.info(f"Decreased cache size to {new_size}")
                
        except Exception as e:
            logger.error(f"Cache size optimization failed: {e}")
```

## Logging and Error Handling Maintenance

### Log File Management

#### Log Rotation
```python
import logging
import gzip
import shutil
from pathlib import Path
from datetime import datetime, timedelta

class LogManager:
    """Manage application log files with rotation and compression."""
    
    def __init__(self, log_dir: Path, max_size_mb: int = 100, backup_count: int = 10):
        self.log_dir = log_dir
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.backup_count = backup_count
    
    def setup_logging(self):
        """Setup logging with rotation."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        from logging.handlers import RotatingFileHandler
        
        log_file = self.log_dir / "candy_cadence.log"
        
        handler = RotatingFileHandler(
            log_file,
            maxBytes=self.max_size_bytes,
            backupCount=self.backup_count,
            encoding='utf-8'
        )
        
        # Setup formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)
        
        logger.info("Logging system initialized with rotation")
    
    def rotate_logs(self):
        """Manually rotate log files."""
        try:
            log_file = self.log_dir / "candy_cadence.log"
            
            if log_file.exists() and log_file.stat().st_size > self.max_size_bytes:
                # Rotate current log
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = self.log_dir / f"candy_cadence_{timestamp}.log"
                
                # Move current log to backup
                shutil.move(str(log_file), str(backup_file))
                
                # Compress old log
                compressed_file = self.log_dir / f"{backup_file.stem}.log.gz"
                with open(backup_file, 'rb') as f_in:
                    with gzip.open(compressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                
                # Remove uncompressed backup
                backup_file.unlink()
                
                logger.info(f"Log rotated: {compressed_file}")
                
                # Clean up old compressed logs
                self._cleanup_old_logs()
                
        except Exception as e:
            logger.error(f"Log rotation failed: {e}")
    
    def _cleanup_old_logs(self):
        """Clean up old log files beyond retention period."""
        try:
            cutoff_date = datetime.now() - timedelta(days=30)  # 30 days retention
            
            for log_file in self.log_dir.glob("*.log.gz"):
                if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                    log_file.unlink()
                    logger.info(f"Removed old log file: {log_file}")
                    
        except Exception as e:
            logger.error(f"Log cleanup failed: {e}")
```

#### Log Analysis
```python
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta

class LogAnalyzer:
    """Analyze application logs for patterns and issues."""
    
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
    
    def analyze_error_patterns(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze error patterns in recent logs."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            error_patterns = Counter()
            error_timeline = defaultdict(int)
            
            # Analyze log files
            for log_file in self._get_recent_log_files(hours):
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if self._is_error_line(line):
                            timestamp = self._extract_timestamp(line)
                            if timestamp and timestamp >= cutoff_time:
                                error_type = self._extract_error_type(line)
                                error_patterns[error_type] += 1
                                error_timeline[timestamp.strftime('%Y-%m-%d %H')] += 1
            
            # Identify frequent errors
            frequent_errors = {k: v for k, v in error_patterns.items() if v > 5}
            
            # Calculate error rate
            total_errors = sum(error_patterns.values())
            error_rate = total_errors / hours if hours > 0 else 0
            
            analysis = {
                'total_errors': total_errors,
                'error_rate_per_hour': error_rate,
                'error_patterns': dict(error_patterns.most_common(10)),
                'frequent_errors': frequent_errors,
                'error_timeline': dict(error_timeline),
                'analysis_period_hours': hours
            }
            
            if frequent_errors:
                logger.warning(f"Frequent errors detected: {frequent_errors}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error pattern analysis failed: {e}")
            return {}
    
    def analyze_performance_logs(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze performance-related log entries."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            performance_issues = []
            slow_operations = []
            
            for log_file in self._get_recent_log_files(hours):
                with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                    for line in f:
                        if self._is_performance_line(line):
                            timestamp = self._extract_timestamp(line)
                            if timestamp and timestamp >= cutoff_time:
                                if 'slow' in line.lower() or 'performance' in line.lower():
                                    slow_operations.append({
                                        'timestamp': timestamp,
                                        'message': line.strip()
                                    })
                                elif 'memory' in line.lower() or 'cpu' in line.lower():
                                    performance_issues.append({
                                        'timestamp': timestamp,
                                        'message': line.strip()
                                    })
            
            return {
                'slow_operations': slow_operations[-20:],  # Last 20
                'performance_issues': performance_issues[-20:],  # Last 20
                'analysis_period_hours': hours
            }
            
        except Exception as e:
            logger.error(f"Performance log analysis failed: {e}")
            return {}
    
    def _get_recent_log_files(self, hours: int) -> List[Path]:
        """Get log files modified within the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        log_files = []
        
        # Check current log file
        current_log = self.log_dir / "candy_cadence.log"
        if current_log.exists():
            file_time = datetime.fromtimestamp(current_log.stat().st_mtime)
            if file_time >= cutoff_time:
                log_files.append(current_log)
        
        # Check rotated log files
        for log_file in self.log_dir.glob("candy_cadence_*.log*"):
            file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_time >= cutoff_time:
                log_files.append(log_file)
        
        return sorted(log_files)
    
    def _is_error_line(self, line: str) -> bool:
        """Check if log line contains an error."""
        return any(level in line.upper() for level in ['ERROR', 'CRITICAL', 'EXCEPTION'])
    
    def _is_performance_line(self, line: str) -> bool:
        """Check if log line contains performance information."""
        performance_keywords = ['slow', 'performance', 'memory', 'cpu', 'timeout', 'latency']
        return any(keyword in line.lower() for keyword in performance_keywords)
    
    def _extract_timestamp(self, line: str) -> datetime:
        """Extract timestamp from log line."""
        try:
            # Common log timestamp patterns
            patterns = [
                r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})',
                r'(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})',
                r'(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, line)
                if match:
                    timestamp_str = match.group(1)
                    # Try different date formats
                    for fmt in ['%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%m-%d-%Y %H:%M:%S']:
                        try:
                            return datetime.strptime(timestamp_str, fmt)
                        except ValueError:
                            continue
        except Exception:
            pass
        return None
    
    def _extract_error_type(self, line: str) -> str:
        """Extract error type from log line."""
        # Common error patterns
        error_patterns = {
            'ParseError': r'ParseError',
            'FileNotFoundError': r'FileNotFoundError',
            'DatabaseError': r'DatabaseError',
            'MemoryError': r'MemoryError',
            'TimeoutError': r'TimeoutError'
        }
        
        for error_type, pattern in error_patterns.items():
            if re.search(pattern, line, re.IGNORECASE):
                return error_type
        
        return 'UnknownError'
```

### Error Handling Maintenance

#### Error Rate Monitoring
```python
class ErrorMonitor:
    """Monitor error rates and patterns."""
    
    def __init__(self, threshold_per_hour: int = 50):
        self.threshold_per_hour = threshold_per_hour
        self.error_counts = defaultdict(int)
        self.last_check = datetime.now()
    
    def check_error_rates(self):
        """Check current error rates against thresholds."""
        try:
            current_time = datetime.now()
            time_diff = (current_time - self.last_check).total_seconds() / 3600  # hours
            
            if time_diff < 0.1:  # Less than 6 minutes since last check
                return
            
            # Calculate error rates
            error_rates = {}
            for error_type, count in self.error_counts.items():
                rate_per_hour = count / time_diff if time_diff > 0 else 0
                error_rates[error_type] = rate_per_hour
            
            # Check for threshold violations
            violations = []
            for error_type, rate in error_rates.items():
                if rate > self.threshold_per_hour:
                    violations.append(f"{error_type}: {rate:.1f}/hour")
            
            if violations:
                logger.warning(f"Error rate violations detected: {violations}")
            
            # Reset counters
            self.error_counts.clear()
            self.last_check = current_time
            
            return {
                'error_rates': error_rates,
                'violations': violations,
                'check_period_hours': time_diff
            }
            
        except Exception as e:
            logger.error(f"Error rate check failed: {e}")
            return None
    
    def record_error(self, error_type: str):
        """Record an error occurrence."""
        self.error_counts[error_type] += 1
```

## Backup and Recovery Procedures

### Comprehensive Backup Strategy

#### Backup Types and Schedule

| Backup Type | Frequency | Retention | Location |
|-------------|-----------|-----------|----------|
| Full System | Weekly | 4 weeks | Primary + Secondary |
| Database | Daily | 30 days | Primary + Secondary |
| Configuration | Weekly | 12 weeks | Primary + Secondary |
| User Data | Daily | 30 days | Primary + Secondary |
| Logs | Daily | 7 days | Archive Storage |

#### Automated Backup Script
```python
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
import json

class BackupManager:
    """Comprehensive backup management system."""
    
    def __init__(self, config_file: str = "backup_config.json"):
        self.config = self._load_config(config_file)
        self.backup_dir = Path(self.config.get('backup_directory', './backups'))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_full_backup(self):
        """Create a complete system backup."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"full_backup_{timestamp}"
            backup_path = self.backup_dir / backup_name
            backup_path.mkdir(exist_ok=True)
            
            logger.info(f"Starting full backup: {backup_name}")
            
            # Backup database
            self._backup_database(backup_path)
            
            # Backup configuration files
            self._backup_configuration(backup_path)
            
            # Backup user data
            self._backup_user_data(backup_path)
            
            # Backup application logs
            self._backup_logs(backup_path)
            
            # Create backup manifest
            self._create_backup_manifest(backup_path)
            
            # Compress backup
            compressed_path = self._compress_backup(backup_path)
            
            # Verify backup
            if self._verify_backup(compressed_path):
                logger.info(f"Full backup completed successfully: {compressed_path}")
                self._cleanup_old_backups('full')
                return compressed_path
            else:
                logger.error("Backup verification failed")
                return None
                
        except Exception as e:
            logger.error(f"Full backup failed: {e}")
            return None
    
    def _backup_database(self, backup_path: Path):
        """Backup database with integrity check."""
        try:
            db_backup_dir = backup_path / "database"
            db_backup_dir.mkdir(exist_ok=True)
            
            # Create database backup
            db_path = Path("data/candy_cadence.db")
            if db_path.exists():
                shutil.copy2(db_path, db_backup_dir / "candy_cadence.db")
                
                # Verify database integrity
                if self._verify_database_integrity(db_backup_dir / "candy_cadence.db"):
                    logger.info("Database backup completed with integrity verification")
                else:
                    raise ValueError("Database integrity check failed")
            else:
                logger.warning("Database file not found, skipping database backup")
                
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            raise
    
    def _backup_configuration(self, backup_path: Path):
        """Backup configuration files."""
        try:
            config_backup_dir = backup_path / "configuration"
            config_backup_dir.mkdir(exist_ok=True)
            
            config_files = [
                "config.json",
                "settings.json",
                ".env",
                "pyinstaller.spec",
                "requirements.txt"
            ]
            
            for config_file in config_files:
                config_path = Path(config_file)
                if config_path.exists():
                    shutil.copy2(config_path, config_backup_dir / config_path.name)
            
            logger.info("Configuration backup completed")
            
        except Exception as e:
            logger.error(f"Configuration backup failed: {e}")
            raise
    
    def _backup_user_data(self, backup_path: Path):
        """Backup user data and custom files."""
        try:
            user_data_backup_dir = backup_path / "user_data"
            user_data_backup_dir.mkdir(exist_ok=True)
            
            user_data_dirs = [
                "data/models",
                "data/thumbnails",
                "data/cache",
                "resources/themes"
            ]
            
            for data_dir in user_data_dirs:
                source_dir = Path(data_dir)
                if source_dir.exists():
                    dest_dir = user_data_backup_dir / source_dir.name
                    shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
            
            logger.info("User data backup completed")
            
        except Exception as e:
            logger.error(f"User data backup failed: {e}")
            raise
    
    def _backup_logs(self, backup_path: Path):
        """Backup application logs."""
        try:
            logs_backup_dir = backup_path / "logs"
            logs_backup_dir.mkdir(exist_ok=True)
            
            logs_dir = Path("logs")
            if logs_dir.exists():
                shutil.copytree(logs_dir, logs_backup_dir / "logs", dirs_exist_ok=True)
            
            logger.info("Logs backup completed")
            
        except Exception as e:
            logger.error(f"Logs backup failed: {e}")
            raise
    
    def _create_backup_manifest(self, backup_path: Path):
        """Create backup manifest with metadata."""
        manifest = {
            'backup_type': 'full',
            'timestamp': datetime.now().isoformat(),
            'version': self._get_application_version(),
            'checksums': self._calculate_checksums(backup_path),
            'file_count': len(list(backup_path.rglob('*'))),
            'total_size_bytes': sum(f.stat().st_size for f in backup_path.rglob('*') if f.is_file())
        }
        
        manifest_path = backup_path / "backup_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        
        logger.info("Backup manifest created")
    
    def _compress_backup(self, backup_path: Path) -> Path:
        """Compress backup directory."""
        try:
            compressed_path = backup_path.with_suffix('.tar.gz')
            
            # Create tar.gz archive
            import tarfile
            with tarfile.open(compressed_path, 'w:gz') as tar:
                tar.add(backup_path, arcname=backup_path.name)
            
            # Remove uncompressed directory
            shutil.rmtree(backup_path)
            
            logger.info(f"Backup compressed: {compressed_path}")
            return compressed_path
            
        except Exception as e:
            logger.error(f"Backup compression failed: {e}")
            raise
    
    def _verify_backup(self, backup_path: Path) -> bool:
        """Verify backup integrity."""
        try:
            # Check file exists and is not empty
            if not backup_path.exists() or backup_path.stat().st_size == 0:
                return False
            
            # Test extraction
            test_dir = backup_path.parent / f"test_{backup_path.stem}"
            test_dir.mkdir(exist_ok=True)
            
            try:
                import tarfile
                with tarfile.open(backup_path, 'r:gz') as tar:
                    tar.extractall(test_dir)
                
                # Check for essential files
                extracted_path = test_dir / backup_path.stem
                essential_files = [
                    extracted_path / "backup_manifest.json",
                    extracted_path / "database" / "candy_cadence.db"
                ]
                
                for essential_file in essential_files:
                    if not essential_file.exists():
                        logger.error(f"Essential file missing in backup: {essential_file}")
                        return False
                
                return True
                
            finally:
                # Clean up test directory
                if test_dir.exists():
                    shutil.rmtree(test_dir)
                    
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False
    
    def _cleanup_old_backups(self, backup_type: str):
        """Clean up old backups based on retention policy."""
        try:
            retention_days = self.config.get('retention_days', {}).get(backup_type, 30)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            pattern = f"{backup_type}_backup_*.tar.gz"
            for backup_file in self.backup_dir.glob(pattern):
                if datetime.fromtimestamp(backup_file.stat().st_mtime) < cutoff_date:
                    backup_file.unlink()
                    logger.info(f"Removed old backup: {backup_file}")
                    
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
    
    def _verify_database_integrity(self, db_path: Path) -> bool:
        """Verify database integrity."""
        try:
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Run integrity check
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            conn.close()
            
            return result[0] == 'ok'
            
        except Exception as e:
            logger.error(f"Database integrity check failed: {e}")
            return False
    
    def _calculate_checksums(self, backup_path: Path) -> Dict[str, str]:
        """Calculate checksums for backup files."""
        import hashlib
        
        checksums = {}
        for file_path in backup_path.rglob('*'):
            if file_path.is_file():
                hasher = hashlib.sha256()
                with open(file_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                checksums[str(file_path.relative_to(backup_path))] = hasher.hexdigest()
        
        return checksums
    
    def _get_application_version(self) -> str:
        """Get application version."""
        try:
            # Try to get version from various sources
            import pkg_resources
            return pkg_resources.get_distribution("candy-cadence").version
        except:
            try:
                from src import __version__
                return __version__
            except:
                return "unknown"
    
    def _load_config(self, config_file: str) -> Dict:
        """Load backup configuration."""
        try:
            if Path(config_file).exists():
                with open(config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load backup config: {e}")
        
        # Default configuration
        return {
            'backup_directory': './backups',
            'retention_days': {
                'full': 30,
                'incremental': 7,
                'database': 30
            },
            'compression': True,
            'verification': True
        }
```

### Recovery Procedures

#### Disaster Recovery Plan
```python
class DisasterRecovery:
    """Disaster recovery procedures."""
    
    def __init__(self, backup_manager: BackupManager):
        self.backup_manager = backup_manager
        self.recovery_log = []
    
    def perform_full_recovery(self, backup_file: Path, target_dir: Path):
        """Perform full system recovery from backup."""
        try:
            logger.info(f"Starting full recovery from: {backup_file}")
            self._log_recovery_step("Starting full recovery")
            
            # Verify backup file
            if not self.backup_manager._verify_backup(backup_file):
                raise ValueError("Backup verification failed")
            
            # Create recovery directory
            recovery_dir = target_dir / f"recovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            recovery_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract backup
            self._extract_backup(backup_file, recovery_dir)
            self._log_recovery_step("Backup extracted")
            
            # Load backup manifest
            manifest = self._load_backup_manifest(recovery_dir)
            self._log_recovery_step("Backup manifest loaded")
            
            # Restore database
            self._restore_database(recovery_dir)
            self._log_recovery_step("Database restored")
            
            # Restore configuration
            self._restore_configuration(recovery_dir)
            self._log_recovery