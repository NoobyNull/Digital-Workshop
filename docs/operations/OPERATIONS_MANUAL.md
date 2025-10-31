
# Candy-Cadence Operations Manual

## Overview

This operations manual provides comprehensive procedures for monitoring, maintaining, and operating Candy-Cadence in production environments. It covers system monitoring, health checks, performance benchmarking, quality assurance, and continuous integration processes.

## Table of Contents

1. [Operations Overview](#operations-overview)
2. [System Monitoring](#system-monitoring)
3. [Health Check Procedures](#health-check-procedures)
4. [Performance Benchmarking](#performance-benchmarking)
5. [Quality Assurance Procedures](#quality-assurance-procedures)
6. [Continuous Integration](#continuous-integration)
7. [Operational Dashboards](#operational-dashboards)
8. [Alert Management](#alert-management)
9. [Incident Response](#incident-response)
10. [Capacity Planning](#capacity-planning)

## Operations Overview

### Operational Philosophy

Candy-Cadence operations follow these core principles:

- **Proactive Monitoring**: Continuous monitoring to detect issues before they impact users
- **Data-Driven Decisions**: All operational decisions based on metrics and performance data
- **Automation First**: Automated processes for routine operations and monitoring
- **Documentation**: Comprehensive documentation of all operational procedures
- **Continuous Improvement**: Regular review and optimization of operational processes

### Operational Team Structure

| Role | Responsibilities | Skills Required |
|------|------------------|-----------------|
| Operations Manager | Overall operations oversight, incident coordination | System administration, project management |
| DevOps Engineer | CI/CD pipeline, infrastructure automation | Python, Docker, CI/CD tools |
| QA Engineer | Quality assurance, testing procedures | Testing frameworks, automation |
| Performance Engineer | Performance monitoring, optimization | Performance analysis, benchmarking |
| Security Engineer | Security monitoring, compliance | Security tools, compliance frameworks |

### Operational Metrics

#### Key Performance Indicators (KPIs)

| Metric | Target | Measurement Frequency |
|--------|--------|----------------------|
| Application Uptime | 99.9% | Continuous |
| Average Response Time | < 2 seconds | Real-time |
| Memory Usage | < 80% of available | Every 5 minutes |
| Disk Usage | < 85% of available | Every hour |
| Error Rate | < 0.1% | Real-time |
| User Satisfaction | > 4.5/5 | Monthly |

#### Service Level Objectives (SLOs)

- **Availability**: 99.9% uptime (8.76 hours downtime per year)
- **Performance**: 95% of requests complete within 5 seconds
- **Reliability**: < 1 critical error per month
- **User Experience**: > 4.0/5 user satisfaction rating

## System Monitoring

### Monitoring Architecture

Candy-Cadence uses a multi-layered monitoring approach:

```
┌─────────────────────────────────────────────────────────────┐
│                    Monitoring Layers                        │
├─────────────────────────────────────────────────────────────┤
│ Application Layer: Performance, Errors, User Activity       │
├─────────────────────────────────────────────────────────────┤
│ System Layer: CPU, Memory, Disk, Network                    │
├─────────────────────────────────────────────────────────────┤
│ Infrastructure Layer: Server Health, Database Performance   │
├─────────────────────────────────────────────────────────────┤
│ Business Layer: User Metrics, Feature Usage, Satisfaction   │
└─────────────────────────────────────────────────────────────┘
```

### Application Monitoring

#### Performance Monitoring
```python
import time
import psutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json

class ApplicationMonitor:
    """Monitor application performance and health."""
    
    def __init__(self, config_file: str = "monitor_config.json"):
        self.config = self._load_config(config_file)
        self.logger = logging.getLogger(__name__)
        self.metrics_history = []
        self.alert_thresholds = self.config.get('alert_thresholds', {})
    
    def collect_metrics(self) -> Dict:
        """Collect current application metrics."""
        timestamp = datetime.now()
        
        # Application-specific metrics
        app_metrics = {
            'timestamp': timestamp.isoformat(),
            'application': {
                'status': self._check_application_status(),
                'response_time': self._measure_response_time(),
                'active_sessions': self._get_active_sessions(),
                'models_loaded': self._get_models_loaded(),
                'cache_hit_rate': self._get_cache_hit_rate()
            },
            'system': {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('.').percent,
                'network_io': dict(psutil.net_io_counters()._asdict())
            },
            'database': {
                'connection_count': self._get_db_connections(),
                'query_performance': self._measure_db_performance(),
                'cache_size': self._get_db_cache_size()
            }
        }
        
        # Store metrics
        self.metrics_history.append(app_metrics)
        
        # Keep only recent history (last 24 hours)
        cutoff_time = timestamp - timedelta(hours=24)
        self.metrics_history = [
            m for m in self.metrics_history 
            if datetime.fromisoformat(m['timestamp']) > cutoff_time
        ]
        
        return app_metrics
    
    def _check_application_status(self) -> str:
        """Check if application is responding."""
        try:
            # This would be specific to your application
            # For example, checking if the GUI is responsive
            import subprocess
            
            # Check if main process is running
            result = subprocess.run([
                'tasklist', '/FI', 'IMAGENAME eq python.exe'
            ], capture_output=True, text=True)
            
            if 'candy_cadence' in result.stdout.lower():
                return 'healthy'
            else:
                return 'unhealthy'
                
        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            return 'unknown'
    
    def _measure_response_time(self) -> float:
        """Measure application response time."""
        start_time = time.time()
        try:
            # Simulate a simple operation to measure response
            # This would be replaced with actual application health check
            time.sleep(0.1)  # Simulated operation
            return time.time() - start_time
        except Exception as e:
            self.logger.error(f"Response time measurement failed: {e}")
            return 999.0
    
    def _get_active_sessions(self) -> int:
        """Get number of active user sessions."""
        # This would query your application state
        # For now, return a placeholder
        return 1
    
    def _get_models_loaded(self) -> int:
        """Get number of models currently loaded in memory."""
        # This would query your application state
        return 0
    
    def _get_cache_hit_rate(self) -> float:
        """Get cache hit rate percentage."""
        # This would query your cache statistics
        return 85.5
    
    def _get_db_connections(self) -> int:
        """Get number of active database connections."""
        try:
            import sqlite3
            conn = sqlite3.connect('data/candy_cadence.db')
            cursor = conn.cursor()
            
            # This is a simplified check - in production you'd have better metrics
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            conn.close()
            return table_count
        except Exception as e:
            self.logger.error(f"Database connection check failed: {e}")
            return 0
    
    def _measure_db_performance(self) -> Dict:
        """Measure database performance."""
        try:
            import sqlite3
            start_time = time.time()
            
            conn = sqlite3.connect('data/candy_cadence.db')
            cursor = conn.cursor()
            
            # Simple query to measure performance
            cursor.execute("SELECT COUNT(*) FROM models")
            result = cursor.fetchone()
            
            query_time = time.time() - start_time
            conn.close()
            
            return {
                'query_time': query_time,
                'status': 'healthy' if query_time < 1.0 else 'slow'
            }
        except Exception as e:
            self.logger.error(f"Database performance check failed: {e}")
            return {'query_time': 999.0, 'status': 'error'}
    
    def _get_db_cache_size(self) -> int:
        """Get database cache size in bytes."""
        try:
            import os
            db_path = 'data/candy_cadence.db'
            if os.path.exists(db_path):
                return os.path.getsize(db_path)
            return 0
        except Exception as e:
            self.logger.error(f"Database cache size check failed: {e}")
            return 0
    
    def analyze_trends(self) -> Dict:
        """Analyze metrics trends over time."""
        if len(self.metrics_history) < 2:
            return {'status': 'insufficient_data'}
        
        recent_metrics = self.metrics_history[-10:]  # Last 10 measurements
        
        trends = {
            'cpu_trend': self._calculate_trend([m['system']['cpu_percent'] for m in recent_metrics]),
            'memory_trend': self._calculate_trend([m['system']['memory_percent'] for m in recent_metrics]),
            'response_time_trend': self._calculate_trend([m['application']['response_time'] for m in recent_metrics]),
            'error_rate': self._calculate_error_rate(recent_metrics)
        }
        
        return trends
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend direction for a series of values."""
        if len(values) < 2:
            return 'stable'
        
        # Simple linear trend calculation
        n = len(values)
        sum_x = sum(range(n))
        sum_y = sum(values)
        sum_xy = sum(i * values[i] for i in range(n))
        sum_x2 = sum(i * i for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
        
        if slope > 0.1:
            return 'increasing'
        elif slope < -0.1:
            return 'decreasing'
        else:
            return 'stable'
    
    def _calculate_error_rate(self, metrics: List[Dict]) -> float:
        """Calculate error rate from metrics."""
        total_operations = len(metrics)
        error_operations = sum(1 for m in metrics if m['application']['status'] != 'healthy')
        
        return (error_operations / total_operations) * 100 if total_operations > 0 else 0
    
    def _load_config(self, config_file: str) -> Dict:
        """Load monitoring configuration."""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default monitoring configuration."""
        return {
            'collection_interval': 60,  # seconds
            'retention_period': 24,  # hours
            'alert_thresholds': {
                'cpu_percent': 80,
                'memory_percent': 85,
                'disk_percent': 90,
                'response_time': 5.0,
                'error_rate': 5.0
            },
            'notification_channels': {
                'email': ['admin@example.com'],
                'webhook': ['https://hooks.slack.com/...']
            }
        }

# Run monitoring
if __name__ == "__main__":
    monitor = ApplicationMonitor()
    
    # Collect metrics
    metrics = monitor.collect_metrics()
    print(f"Current metrics: {json.dumps(metrics, indent=2)}")
    
    # Analyze trends
    trends = monitor.analyze_trends()
    print(f"Trends: {json.dumps(trends, indent=2)}")
```

#### Error Monitoring
```python
import logging
import traceback
from datetime import datetime
from typing import Dict, List, Optional
import json

class ErrorMonitor:
    """Monitor and track application errors."""
    
    def __init__(self, log_file: str = "logs/error_monitor.log"):
        self.log_file = log_file
        self.error_history = []
        self.error_patterns = {}
        
        # Setup error logging
        self.logger = logging.getLogger('error_monitor')
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.ERROR)
    
    def log_error(self, error: Exception, context: Dict = None):
        """Log an error with context."""
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        # Store error
        self.error_history.append(error_info)
        
        # Log to file
        self.logger.error(f"Error: {error_info['error_type']} - {error_info['error_message']}")
        self.logger.error(f"Context: {json.dumps(error_info['context'])}")
        
        # Analyze error patterns
        self._analyze_error_pattern(error_info)
        
        # Check if alert should be triggered
        self._check_error_alerts(error_info)
    
    def _analyze_error_pattern(self, error_info: Dict):
        """Analyze error patterns for insights."""
        error_key = f"{error_info['error_type']}:{error_info['error_message'][:50]}"
        
        if error_key not in self.error_patterns:
            self.error_patterns[error_key] = {
                'count': 0,
                'first_occurrence': error_info['timestamp'],
                'last_occurrence': error_info['timestamp'],
                'contexts': []
            }
        
        pattern = self.error_patterns[error_key]
        pattern['count'] += 1
        pattern['last_occurrence'] = error_info['timestamp']
        pattern['contexts'].append(error_info['context'])
        
        # Keep only recent contexts
        if len(pattern['contexts']) > 10:
            pattern['contexts'] = pattern['contexts'][-10:]
    
    def _check_error_alerts(self, error_info: Dict):
        """Check if error should trigger an alert."""
        error_key = f"{error_info['error_type']}:{error_info['error_message'][:50]}"
        pattern = self.error_patterns.get(error_key, {})
        
        # Alert on frequent errors
        if pattern.get('count', 0) >= 5:
            self._send_alert('high_error_frequency', {
                'error_key': error_key,
                'count': pattern['count'],
                'recent_contexts': pattern.get('contexts', [])[-3:]
            })
        
        # Alert on critical errors
        if error_info['error_type'] in ['MemoryError', 'DatabaseError', 'SystemError']:
            self._send_alert('critical_error', error_info)
    
    def _send_alert(self, alert_type: str, data: Dict):
        """Send error alert."""
        alert = {
            'type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        
        # Log alert
        self.logger.critical(f"ALERT: {alert_type} - {json.dumps(data)}")
        
        # In production, this would send to monitoring system
        # email, Slack, PagerDuty, etc.
        print(f"ALERT SENT: {alert}")
    
    def get_error_summary(self) -> Dict:
        """Get summary of recent errors."""
        if not self.error_history:
            return {'total_errors': 0, 'error_types': {}, 'recent_errors': []}
        
        # Count errors by type
        error_types = {}
        for error in self.error_history:
            error_type = error['error_type']
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Get recent errors (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        recent_errors = [
            error for error in self.error_history
            if datetime.fromisoformat(error['timestamp']) > cutoff_time
        ]
        
        return {
            'total_errors': len(self.error_history),
            'recent_errors_count': len(recent_errors),
            'error_types': error_types,
            'top_error_patterns': sorted(
                self.error_patterns.items(),
                key=lambda x: x[1]['count'],
                reverse=True
            )[:5],
            'recent_errors': recent_errors[-10:]  # Last 10 errors
        }
```

### System Resource Monitoring

#### Resource Usage Tracking
```python
import psutil
import time
import threading
from datetime import datetime, timedelta
from collections import deque

class ResourceMonitor:
    """Monitor system resource usage."""
    
    def __init__(self, history_size: int = 1000):
        self.history_size = history_size
        self.cpu_history = deque(maxlen=history_size)
        self.memory_history = deque(maxlen=history_size)
        self.disk_history = deque(maxlen=history_size)
        self.network_history = deque(maxlen=history_size)
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, interval: int = 30):
        """Start resource monitoring."""
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitoring_loop,
            args=(interval,)
        )
        self.monitor_thread.start()
        print("Resource monitoring started")
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("Resource monitoring stopped")
    
    def _monitoring_loop(self, interval: int):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                timestamp = datetime.now()
                
                # CPU usage
                cpu_percent = psutil.cpu_percent(interval=1)
                self.cpu_history.append({
                    'timestamp': timestamp,
                    'value': cpu_percent
                })
                
                # Memory usage
                memory = psutil.virtual_memory()
                self.memory_history.append({
                    'timestamp': timestamp,
                    'total': memory.total,
                    'available': memory.available,
                    'percent': memory.percent,
                    'used': memory.used,
                    'free': memory.free
                })
                
                # Disk usage
                disk = psutil.disk_usage('.')
                self.disk_history.append({
                    'timestamp': timestamp,
                    'total': disk.total,
                    'used': disk.used,
                    'free': disk.free,
                    'percent': (disk.used / disk.total) * 100
                })
                
                # Network I/O
                network = psutil.net_io_counters()
                self.network_history.append({
                    'timestamp': timestamp,
                    'bytes_sent': network.bytes_sent,
                    'bytes_recv': network.bytes_recv,
                    'packets_sent': network.packets_sent,
                    'packets_recv': network.packets_recv
                })
                
                time.sleep(interval)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                time.sleep(interval)
    
    def get_current_status(self) -> Dict:
        """Get current resource status."""
        status = {
            'timestamp': datetime.now().isoformat(),
            'cpu': {},
            'memory': {},
            'disk': {},
            'network': {}
        }
        
        # Current CPU
        if self.cpu_history:
            latest_cpu = self.cpu_history[-1]
            status['cpu'] = {
                'percent': latest_cpu['value'],
                'trend': self._calculate_trend([x['value'] for x in list(self.cpu_history)[-10:]])
            }
        
        # Current Memory
        if self.memory_history:
            latest_memory = self.memory_history[-1]
            status['memory'] = {
                'percent': latest_memory['percent'],
                'total_gb': latest_memory['total'] / (1024**3),
                'available_gb': latest_memory['available'] / (1024**3),
                'used_gb': latest_memory['used'] / (1024**3),
                'trend': self._calculate_trend([x['percent'] for x in list(self.memory_history)[-10:]])
            }
        
        # Current Disk
        if self.disk_history:
            latest_disk = self.disk_history[-1]
            status['disk'] = {
                'percent': latest_disk['percent'],
                'total_gb': latest_disk['total'] / (1024**3),
                'used_gb': latest_disk['used'] / (1024**3),
                'free_gb': latest_disk['free'] / (1024**3),
                'trend': self._calculate_trend([x['percent'] for x in list(self.disk_history)[-10:]])
            }
        
        # Current Network
        if self.network_history:
            latest_network = self.network_history[-1]
            status['network'] = {
                'bytes_sent': latest_network['bytes_sent'],
                'bytes_recv': latest_network['bytes_recv'],
                'packets_sent': latest_network['packets_sent'],
                'packets_recv': latest_network['packets_recv']
            }
        
        return status
    
    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend for a series of values."""
        if len(values) < 2:
            return 'stable'
        
        # Simple trend calculation
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        if second_half > first_half * 1.1:
            return 'increasing'
        elif second_half < first_half * 0.9:
            return 'decreasing'
        else:
            return 'stable'
    
    def get_resource_report(self, hours: int = 24) -> Dict:
        """Get resource usage report for specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter data by time range
        cpu_data = [x for x in self.cpu_history if x['timestamp'] > cutoff_time]
        memory_data = [x for x in self.memory_history if x['timestamp'] > cutoff_time]
        disk_data = [x for x in self.disk_history if x['timestamp'] > cutoff_time]
        
        report = {
            'period_hours': hours,
            'cpu': self._analyze_resource_data(cpu_data, 'percent'),
            'memory': self._analyze_resource_data(memory_data, 'percent'),
            'disk': self._analyze_resource_data(disk_data, 'percent'),
            'summary': {}
        }
        
        # Generate summary
        if cpu_data and memory_data and disk_data:
            report['summary'] = {
                'average_cpu': sum(x['value'] for x in cpu_data) / len(cpu_data),
                'peak_cpu': max(x['value'] for x in cpu_data),
                'average_memory': sum(x['percent'] for x in memory_data) / len(memory_data),
                'peak_memory': max(x['percent'] for x in memory_data),
                'average_disk': sum(x['percent'] for x in disk_data) / len(disk_data),
                'peak_disk': max(x['percent'] for x in disk_data)
            }
        
        return report
    
    def _analyze_resource_data(self, data: List[Dict], value_key: str) -> Dict:
        """Analyze resource data for trends and statistics."""
        if not data:
            return {}
        
        values = [x[value_key] for x in data]
        
        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'average': sum(values) / len(values),
            'trend': self._calculate_trend(values)
        }
```

## Health Check Procedures

### Automated Health Checks

#### Comprehensive Health Check Script
```python
import sqlite3
import psutil
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

class HealthChecker:
    """Comprehensive health check system for Candy-Cadence."""
    
    def __init__(self):
        self.checks = [
            self._check_application_status,
            self._check_database_health,
            self._check_system_resources,
            self._check_file_permissions,
            self._check_dependencies,
            self._check_configuration,
            self._check_logs,
            self._check_performance
        ]
    
    def run_full_health_check(self) -> Dict:
        """Run comprehensive health check."""
        results = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {},
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        for check_func in self.checks:
            try:
                check_name = check_func.__name__.replace('_check_', '').replace('_', ' ').title()
                check_result = check_func()
                results['checks'][check_name] = check_result
                
                # Categorize issues
                if check_result['status'] == 'critical':
                    results['overall_status'] = 'critical'
                    results['issues'].extend(check_result.get('issues', []))
                elif