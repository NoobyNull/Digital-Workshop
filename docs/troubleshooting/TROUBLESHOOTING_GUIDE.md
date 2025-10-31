# Candy-Cadence Troubleshooting Guide

## Overview

This comprehensive troubleshooting guide provides solutions to common issues, performance problems, and error conditions that may occur when using or maintaining Candy-Cadence. The guide is organized by problem category with step-by-step solutions and preventive measures.

## Table of Contents

1. [Quick Diagnosis](#quick-diagnosis)
2. [Installation Issues](#installation-issues)
3. [Performance Troubleshooting](#performance-troubleshooting)
4. [Memory Issues](#memory-issues)
5. [Database Troubleshooting](#database-troubleshooting)
6. [GUI Issues](#gui-issues)
7. [File Parsing Problems](#file-parsing-problems)
8. [Error Code Reference](#error-code-reference)
9. [System Recovery](#system-recovery)
10. [Preventive Maintenance](#preventive-maintenance)

## Quick Diagnosis

### System Health Check Script

Run this script first to identify common issues:

```python
import sys
import platform
import psutil
import sqlite3
from pathlib import Path
import logging

def quick_health_check():
    """Perform quick system health check."""
    issues = []
    warnings = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append(f"Python {sys.version} is too old. Requires 3.8+")
    else:
        print(f"✓ Python version: {sys.version}")
    
    # Check available memory
    memory = psutil.virtual_memory()
    if memory.available < 1024 * 1024 * 1024:  # Less than 1GB
        issues.append(f"Low memory: {memory.available / 1024**3:.1f}GB available")
    else:
        print(f"✓ Memory: {memory.available / 1024**3:.1f}GB available")
    
    # Check disk space
    disk = psutil.disk_usage('.')
    if disk.free < 1024 * 1024 * 1024:  # Less than 1GB
        issues.append(f"Low disk space: {disk.free / 1024**3:.1f}GB free")
    else:
        print(f"✓ Disk space: {disk.free / 1024**3:.1f}GB free")
    
    # Check database
    try:
        db_path = Path("data/candy_cadence.db")
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            conn.execute("PRAGMA integrity_check")
            print("✓ Database integrity check passed")
        else:
            warnings.append("Database file not found")
    except Exception as e:
        issues.append(f"Database error: {e}")
    finally:
        try:
            conn.close()
        except:
            pass
    
    # Check graphics drivers
    try:
        import OpenGL.GL as gl
        version = gl.glGetString(gl.GL_VERSION)
        print(f"✓ OpenGL version: {version.decode() if version else 'Unknown'}")
    except Exception:
        warnings.append("OpenGL not available or drivers may be outdated")
    
    return issues, warnings

if __name__ == "__main__":
    print("Running Candy-Cadence Health Check...")
    print("=" * 50)
    
    issues, warnings = quick_health_check()
    
    if issues:
        print("\n❌ Critical Issues Found:")
        for issue in issues:
            print(f"  • {issue}")
    
    if warnings:
        print("\n⚠️ Warnings:")
        for warning in warnings:
            print(f"  • {warning}")
    
    if not issues and not warnings:
        print("\n✅ System Health Check Passed - No Issues Found")
```

### Log File Locations

Important log files for troubleshooting:

| Log Type | Location | Purpose |
|----------|----------|---------|
| Application Log | `logs/candy_cadence.log` | Main application events |
| Error Log | `logs/error.log` | Error details and stack traces |
| Performance Log | `logs/performance.log` | Performance metrics and benchmarks |
| Database Log | `logs/database.log` | Database operations and queries |
| Parser Log | `logs/parser.log` | File parsing operations |

## Installation Issues

### Problem: "ModuleNotFoundError: No module named 'PySide6'"

**Symptoms:**
- Application fails to start
- ImportError messages during startup
- GUI components not loading

**Solutions:**

#### Solution 1: Install PySide6
```bash
# Install PySide6
pip install PySide6>=6.0.0

# If issues persist, try:
pip install --upgrade pip
pip install PySide6 --force-reinstall
```

#### Solution 2: Check Python Environment
```bash
# Verify you're in the correct environment
which python
python --version

# Create new virtual environment if needed
python -m venv candy_env
candy_env\Scripts\activate  # Windows
source candy_env/bin/activate  # Linux/macOS
pip install PySide6
```

#### Solution 3: Check System Dependencies (Linux)
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-dev python3-pip
sudo apt-get install libegl1-mesa-dev libgl1-mesa-dev libglu1-mesa-dev
sudo apt-get install libxkbcommon-x11-0 libxcb-icccm4 libxcb-image0
sudo apt-get install libxcb-keysyms1 libxcb-randr0 libxcb-render-util0
sudo apt-get install libxcb-xinerama0 libxcb-xfixes0

pip install PySide6
```

### Problem: "VTK library not found"

**Symptoms:**
- 3D viewer not working
- ImportError for vtk modules
- Black or blank 3D viewports

**Solutions:**

#### Solution 1: Install VTK
```bash
pip install VTK>=9.2.0
```

#### Solution 2: Alternative VTK Installation
```bash
# If pip install fails, try conda
conda install vtk

# Or from wheel files
pip install https://download.lfd.uci.edu/pythonlibs/archived/VTK-9.2.0-cp38-cp38-win_amd64.whl
```

#### Solution 3: Check VTK Python Path
```python
import sys
print(sys.path)
# Add VTK Python modules to path if needed
```

### Problem: Database "database is locked"

**Symptoms:**
- Application freezes during database operations
- SQLite busy errors in logs
- Model import/export failures

**Solutions:**

#### Solution 1: Close All Application Instances
1. Close all Candy-Cadence windows
2. Check Task Manager for remaining processes
3. End any python.exe processes related to Candy-Cadence
4. Restart the application

#### Solution 2: Check Database Permissions
```bash
# Windows
icacls data\candy_cadence.db /grant Users:F

# Linux/macOS
chmod 664 data/candy_cadence.db
```

#### Solution 3: Database Recovery
```python
import sqlite3
import shutil
from datetime import datetime

def recover_database():
    """Attempt to recover corrupted database."""
    db_path = Path("data/candy_cadence.db")
    backup_path = db_path.with_suffix(f".corrupted.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    try:
        # Backup corrupted database
        shutil.copy2(db_path, backup_path)
        
        # Try to open and repair
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check integrity
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        if result[0] == 'ok':
            print("Database integrity check passed")
        else:
            # Attempt repair
            cursor.execute("PRAGMA quick_check")
            cursor.execute("VACUUM")
            print("Database repair attempted")
        
        conn.close()
        
    except Exception as e:
        print(f"Database recovery failed: {e}")
        print(f"Backup available at: {backup_path}")
```

## Performance Troubleshooting

### Problem: Slow Model Loading

**Symptoms:**
- Files take longer than expected to load
- Progress bars stuck or very slow
- Application unresponsive during loading

**Diagnosis:**

#### Step 1: Check Performance Logs
```python
# Analyze recent performance logs
import re
from datetime import datetime, timedelta

def analyze_loading_performance():
    """Analyze model loading performance."""
    log_file = Path("logs/performance.log")
    if not log_file.exists():
        print("Performance log not found")
        return
    
    # Read recent entries
    recent_loads = []
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    with open(log_file, 'r') as f:
        for line in f:
            if "model_loaded" in line:
                # Extract timestamp and load time
                match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*?load_time:([\d.]+)', line)
                if match:
                    timestamp = datetime.strptime(match.group(1), '%Y-%m-%d %H:%M:%S')
                    if timestamp >= cutoff_time:
                        load_time = float(match.group(2))
                        recent_loads.append(load_time)
    
    if recent_loads:
        avg_time = sum(recent_loads) / len(recent_loads)
        max_time = max(recent_loads)
        min_time = min(recent_loads)
        
        print(f"Loading Performance (Last 24 hours):")
        print(f"  Average: {avg_time:.2f}s")
        print(f"  Min: {min_time:.2f}s")
        print(f"  Max: {max_time:.2f}s")
        print(f"  Samples: {len(recent_loads)}")
        
        # Performance targets
        if avg_time > 5.0:
            print("⚠️ Average loading time exceeds target (>5s)")
        if max_time > 30.0:
            print("⚠️ Maximum loading time exceeds target (>30s)")
```

**Solutions:**

#### Solution 1: Optimize File Processing
```python
# Enable progressive loading
def optimize_loading():
    """Configure optimal loading settings."""
    config = {
        'progressive_loading': True,
        'lazy_loading': True,
        'cache_enabled': True,
        'max_cache_size': 100,  # MB
        'background_loading': True,
        'compression_enabled': True
    }
    
    # Apply settings
    with open('config.json', 'w') as f:
        import json
        json.dump(config, f, indent=2)
    
    print("Loading optimization applied")
```

#### Solution 2: Hardware Detection and Adaptation
```python
import psutil
import platform

def detect_hardware_capabilities():
    """Detect system capabilities and suggest optimizations."""
    capabilities = {
        'cpu_cores': psutil.cpu_count(),
        'memory_gb': psutil.virtual_memory().total / (1024**3),
        'has_ssd': self._detect_ssd(),
        'gpu_acceleration': self._detect_gpu()
    }
    
    suggestions = []
    
    if capabilities['memory_gb'] < 4:
        suggestions.append("Consider reducing cache size due to low RAM")
        suggestions.append("Enable memory-mapped file loading")
    
    if not capabilities['has_ssd']:
        suggestions.append("SSD recommended for better performance")
        suggestions.append("Enable aggressive caching")
    
    if capabilities['cpu_cores'] >= 4:
        suggestions.append("Enable parallel processing for large files")
    
    return capabilities, suggestions
```

### Problem: High Memory Usage

**Symptoms:**
- System becomes slow or unresponsive
- Out of memory errors
- High RAM usage in Task Manager

**Diagnosis:**

#### Step 1: Memory Usage Analysis
```python
import psutil
import tracemalloc
import gc
from datetime import datetime

def analyze_memory_usage():
    """Analyze current memory usage patterns."""
    process = psutil.Process()
    memory_info = process.memory_info()
    
    print(f"Current Memory Usage:")
    print(f"  RSS: {memory_info.rss / 1024**2:.1f} MB")
    print(f"  VMS: {memory_info.vms / 1024**2:.1f} MB")
    print(f"  Percent: {process.memory_percent():.1f}%")
    
    # Get memory breakdown by object type
    gc.collect()  # Force garbage collection
    stats = gc.get_stats()
    print(f"\nGC Stats: {stats}")
    
    # Check for memory leaks with tracemalloc
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    
    print(f"\nTop Memory Consumers:")
    for stat in top_stats[:10]:
        print(f"  {stat}")
```

#### Step 2: Memory Leak Detection
```python
def detect_memory_leaks():
    """Detect potential memory leaks."""
    tracemalloc.start()
    
    # Take initial snapshot
    snapshot1 = tracemalloc.take_snapshot()
    
    # Simulate some operations
    models = []
    for i in range(100):
        # Load and process models
        model_data = f"model_data_{i}" * 1000  # Large strings
        models.append(model_data)
        
        if i % 20 == 0:
            gc.collect()
    
    # Take second snapshot
    snapshot2 = tracemalloc.take_snapshot()
    
    # Compare snapshots
    top_stats = snapshot2.compare_to(snapshot1, 'lineno')
    
    print("Top memory differences (potential leaks):")
    for stat in top_stats[:5]:
        print(f"  {stat}")
    
    tracemalloc.stop()
```

**Solutions:**

#### Solution 1: Memory Optimization
```python
class MemoryOptimizer:
    """Optimize memory usage in the application."""
    
    def __init__(self):
        self.max_cache_size = 100 * 1024 * 1024  # 100MB
        self.cache_size = 0
        self.cache_items = []
    
    def optimize_memory(self):
        """Apply memory optimizations."""
        # Force garbage collection
        collected = gc.collect()
        print(f"Garbage collected: {collected} objects")
        
        # Clear cache if over limit
        while self.cache_size > self.max_cache_size and self.cache_items:
            oldest_item = self.cache_items.pop(0)
            self.cache_size -= oldest_item['size']
            del oldest_item['data']
        
        # Enable memory mapping for large files
        import mmap
        import contextlib
        
        @contextlib.contextmanager
        def memory_mapped_file(file_path):
            with open(file_path, 'rb') as f:
                with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
                    yield mmapped_file
        
        print("Memory optimization applied")
```

#### Solution 2: Cache Management
```python
class SmartCache:
    """Memory-aware caching system."""
    
    def __init__(self, max_size_mb=100):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache = {}
        self.access_times = {}
        self.size_tracker = 0
    
    def get(self, key):
        """Get item from cache with LRU eviction."""
        if key in self.cache:
            # Update access time
            self.access_times[key] = time.time()
            return self.cache[key]
        return None
    
    def put(self, key, value):
        """Put item in cache with automatic eviction."""
        import sys
        
        # Estimate size
        size = sys.getsizeof(value)
        
        # Evict items if necessary
        while self.size_tracker + size > self.max_size_bytes and self.cache:
            self._evict_lru()
        
        # Add new item
        self.cache[key] = value
        self.access_times[key] = time.time()
        self.size_tracker += size
    
    def _evict_lru(self):
        """Evict least recently used item."""
        if not self.cache:
            return
        
        # Find LRU item
        lru_key = min(self.access_times.keys(), key=lambda k: self.access_times[k])
        
        # Remove it
        del self.cache[lru_key]
        del self.access_times[lru_key]
        # Note: In a real implementation, you'd track sizes per item
    
    def clear(self):
        """Clear all cache items."""
        self.cache.clear()
        self.access_times.clear()
        self.size_tracker = 0
```

### Problem: Database Performance Issues

**Symptoms:**
- Slow search operations
- Database queries taking too long
- Application freezing during database operations

**Diagnosis:**

#### Step 1: Database Performance Analysis
```python
import sqlite3
import time
import logging
from collections import defaultdict

class DatabaseAnalyzer:
    """Analyze database performance and suggest optimizations."""
    
    def __init__(self, db_path="data/candy_cadence.db"):
        self.db_path = db_path
    
    def analyze_database(self):
        """Perform comprehensive database analysis."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check database size
            cursor.execute("PRAGMA page_size")
            page_size = cursor.fetchone()[0]
            
            cursor.execute("PRAGMA page_count")
            page_count = cursor.fetchone()[0]
            
            db_size_mb = (page_size * page_count) / (1024 * 1024)
            print(f"Database size: {db_size_mb:.1f} MB")
            
            # Check for missing indexes
            self._check_indexes(cursor)
            
            # Analyze query performance
            self._analyze_slow_queries(cursor)
            
            # Check table fragmentation
            self._check_fragmentation(cursor)
            
            conn.close()
            
        except Exception as e:
            print(f"Database analysis failed: {e}")
    
    def _check_indexes(self, cursor):
        """Check for missing indexes."""
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND sql IS NOT NULL
        """)
        existing_indexes = [row[0] for row in cursor.fetchall()]
        
        # Check for common missing indexes
        recommended_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_models_name ON models(name)",
            "CREATE INDEX IF NOT EXISTS idx_models_file_size ON models(file_size)",
            "CREATE INDEX IF NOT EXISTS idx_metadata_model_id ON metadata(model_id)",
            "CREATE INDEX IF NOT EXISTS idx_models_created_date ON models(created_date)"
        ]
        
        print("Index recommendations:")
        for index_sql in recommended_indexes:
            index_name = index_sql.split()[5]  # Extract index name
            if index_name not in existing_indexes:
                print(f"  • Consider creating: {index_name}")
                print(f"    {index_sql}")
    
    def _analyze_slow_queries(self, cursor):
        """Analyze potentially slow queries."""
        # Enable query planning analysis
        cursor.execute("EXPLAIN QUERY PLAN SELECT * FROM models WHERE name LIKE '%test%'")
        plan = cursor.fetchall()
        print("Query plan analysis (example):")
        for row in plan:
            print(f"  {row}")
    
    def _check_fragmentation(self, cursor):
        """Check table fragmentation."""
        cursor.execute("PRAGMA freelist_count")
        free_pages = cursor.fetchone()[0]
        
        cursor.execute("PRAGMA page_count")
        total_pages = cursor.fetchone()[0]
        
        if total_pages > 0:
            fragmentation_percent = (free_pages / total_pages) * 100
            print(f"Database fragmentation: {fragmentation_percent:.1f}%")
            
            if fragmentation_percent > 30:
                print("  • Consider running VACUUM to reduce fragmentation")
```

**Solutions:**

#### Solution 1: Database Optimization
```python
def optimize_database():
    """Optimize database performance."""
    db_path = "data/candy_cadence.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Enable WAL mode for better concurrency
        cursor.execute("PRAGMA journal_mode=WAL")
        
        # Increase cache size
        cursor.execute("PRAGMA cache_size=10000")  # 10MB cache
        
        # Set synchronous mode
        cursor.execute("PRAGMA synchronous=NORMAL")
        
        # Create recommended indexes
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_models_name ON models(name)",
            "CREATE INDEX IF NOT EXISTS idx_models_file_size ON models(file_size)",
            "CREATE INDEX IF NOT EXISTS idx_metadata_model_id ON metadata(model_id)",
            "CREATE INDEX IF NOT EXISTS idx_models_created_date ON models(created_date)"
        ]
        
        for index_sql in indexes:
            try:
                cursor.execute(index_sql)
                print(f"Created index: {index_sql.split()[5]}")
            except sqlite3.Error as e:
                print(f"Failed to create index: {e}")
        
        # Analyze database for query optimization
        cursor.execute("ANALYZE")
        
        # Vacuum to reclaim space
        cursor.execute("VACUUM")
        
        conn.commit()
        conn.close()
        
        print("Database optimization completed")
        
    except Exception as e:
        print(f"Database optimization failed: {e}")
```

#### Solution 2: Query Optimization
```python
def optimize_queries():
    """Optimize database queries for better performance."""
    
    # Instead of:
    # SELECT * FROM models WHERE name LIKE '%search_term%'
    
    # Use:
    optimized_search = """
    SELECT id, name, file_size, created_date 
    FROM models 
    WHERE name LIKE ? 
    ORDER BY created_date DESC 
    LIMIT 100
    """
    
    # Use indexed queries
    indexed_queries = {
        'by_name': "SELECT * FROM models WHERE name = ?",
        'by_size_range': "SELECT * FROM models WHERE file_size BETWEEN ? AND ?",
        'by_date': "SELECT * FROM models WHERE created_date >= ?",
        'recent_models': "SELECT * FROM models ORDER BY created_date DESC LIMIT 50"
    }
    
    print("Optimized query patterns:")
    for pattern_name, query in indexed_queries.items():
        print(f"  {pattern_name}: {query}")
```

## GUI Issues

### Problem: Application Window Not Rendering Properly

**Symptoms:**
- Blank or black application window
- UI elements not visible
- Window doesn't appear or is minimized
- Graphics corruption or artifacts

**Diagnosis:**

#### Step 1: Graphics System Check
```python
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QOpenGLWidget
from OpenGL.GL import glGetString, GL_VERSION

def check_graphics_system():
    """Check graphics system compatibility."""
    print("Graphics System Check")
    print("=" * 30)
    
    # Check Qt backend
    print(f"Qt Backend: {QApplication.instance().platformName()}")
    
    # Check OpenGL availability
    try:
        app = QApplication.instance()
        if not app:
            app = QApplication(sys.argv)
        
        # Create test OpenGL widget
        class TestWidget(QOpenGLWidget):
            def initializeGL(self):
                version = glGetString(GL_VERSION)
                print(f"OpenGL Version: {version.decode() if version else 'Unknown'}")
                
                renderer = glGetString(GL_RENDERER)
                print(f"GPU Renderer: {renderer.decode() if renderer else 'Unknown'}")
        
        test_widget = TestWidget()
        test_widget.show()
        test_widget.hide()
        
    except Exception as e:
        print(f"OpenGL check failed: {e}")
        return False
    
    return True
```

**Solutions:**

#### Solution 1: Software Rendering Fallback
```python
def enable_software_rendering():
    """Enable software rendering as fallback."""
    import os
    
    # Force software rendering
    os.environ['QT_OPENGL'] = 'software'
    os.environ['QT_SCALE_FACTOR'] = '1.0'
    
    # For older Qt versions
    os.environ['QT_LOGGING_RULES'] = '*.debug=false'
    
    print("Software rendering enabled")
```

#### Solution 2: GPU Driver Update
```python
def check_gpu_drivers():
    """Check and provide GPU driver information."""
    import platform
    
    system = platform.system()
    
    if system == "Windows":
        print("Windows GPU Driver Check:")
        print("1. Right-click 'This PC' → Properties")
        print("2. Click 'Device Manager'")
        print("3. Expand 'Display adapters'")
        print("4. Right-click your GPU → Update driver")
        print("5. Select 'Search automatically for drivers'")
    
    elif system == "Linux":
        print("Linux GPU Driver Check:")
        print("1. Check current driver: lspci | grep VGA")
        print("2. Install drivers:")
        print("   NVIDIA: sudo apt install nvidia-driver-470")
        print("   AMD: sudo apt install xserver-xorg-video-amdgpu")
        print("   Intel: sudo apt install xserver-xorg-video-intel")
    
    elif system == "Darwin":  # macOS
        print("macOS GPU Driver Check:")
        print("1. Check System Report → Graphics/Displays")
        print("2. Update macOS through System Preferences")
```

### Problem: 3D Viewer Not Working

**Symptoms:**
- 3D view shows black screen
- Models not rendering
- VTK errors in logs
- Viewer widget crashes

**Solutions:**

#### Solution 1: VTK Context Sharing
```python
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

def setup_vtk_context():
    """Setup VTK with proper context sharing."""
    
    # Ensure proper OpenGL context
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    
    # Create VTK widget
    class VTKWidget(QVTKRenderWindowInteractor):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.GetRenderWindow().SetMultiSamples(0)  # Disable multisampling if causing issues
            self.GetRenderWindow().SetLineSmoothing(1)
            self.GetRenderWindow().SetPolygonSmoothing(1)
    
    return VTKWidget
```

#### Solution 2: Alternative Rendering Backend
```python
def fallback_rendering():
    """Implement fallback rendering when VTK fails."""
    
    class FallbackViewer:
        def __init__(self):
            self.fallback_mode = True
        
        def display_model_info(self, model_data):
            """Display model information when 3D rendering fails."""
            return f"""
            3D Viewer Unavailable - Fallback Mode
            
            Model Information:
            • Vertices: {len(model_data.get('vertices', []))}
            • Triangles: {len(model_data.get('triangles', []))}
            • File Size: {model_data.get('file_size', 0)} bytes
            • Format: {model_data.get('format', 'Unknown')}
            """
        
        def enable_2d_preview(self, model_data):
            """Show 2D preview as fallback."""
            # Generate simple 2D visualization
            pass
```

## File Parsing Problems

### Problem: Model Files Not Loading

**Symptoms:**
- "Unsupported file format" errors
- Parser crashes or hangs
- Incomplete model loading
- Memory errors during parsing

**Diagnosis:**

#### Step 1: File Format Validation
```python
import os
from pathlib import Path

def validate_model_file(file_path):
    """Validate model file format and integrity."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False, "File does not exist"
    
    # Check file size
    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > 500:
        return False, f"File too large ({size_mb:.1f}MB)"
    
    # Check file extension
    supported_extensions = {'.stl', '.obj', '.3mf', '.step', '.stp'}
    if file_path.suffix.lower() not in supported_extensions:
        return False, f"Unsupported file extension: {file_path.suffix}"
    
    # Basic file format validation
    try:
        with open(file_path, 'rb') as f:
            header = f.read(100)
            
            # STL validation
            if file_path.suffix.lower() == '.stl':
                if not header.startswith(b'solid') and header[0:5] != b'\x00\x00\x00\x00':
                    return False, "Invalid STL file header"
            
            # OBJ validation
            elif file_path.suffix.lower() == '.obj':
                # Check for common OBJ keywords
                content = header.decode('ascii', errors='ignore')
                if not any(keyword in content for keyword in ['v ', 'f ', 'vn ', 'vt ']):
                    return False, "Invalid OBJ file format"
    
    except Exception as e:
        return False, f"File read error: {e}"
    
    return True, "File validation passed"
```

**Solutions:**

#### Solution 1: Parser Error Recovery
```python
from typing import Optional, Dict, Any
import logging

class RobustParser:
    """Parser with error recovery and fallback mechanisms."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.retry_count = 3
    
    def parse_with_recovery(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Parse file with error recovery."""
        
        # Try primary parsing method
        for attempt in range(self.retry_count):
            try:
                return self._attempt_parse(file_path)
            except Exception as e:
                self.logger.warning(f"Parse attempt {attempt + 1} failed: {e}")
                
                if attempt < self.retry_count - 1:
                    # Wait before retry
                    time.sleep(0.5 * (attempt + 1))
                else:
                    # All attempts failed, try fallback parsing
                    return self._fallback_parse(file_path)
        
        return None
    
    def _attempt_parse(self, file_path: Path) -> Dict[str, Any]:
        """Primary parsing method."""
        # Determine file format
        format_type = self._detect_format(file_path)
        
        if format_type == 'stl':
            return self._parse_stl(file_path)
        elif format_type == 'obj':
            return self._parse_obj(file_path)
        elif format_type == '3mf':
            return self._parse_3mf(file_path)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _fallback_parse(self, file_path: Path) -> Dict[str, Any]:
        """Fallback parsing with minimal information extraction."""
        self.logger.info(f"Using fallback parsing for: {file_path}")
        
        return {
            'format': 'unknown',
            'file_path': str(file_path),
            'file_size': file_path.stat().st_size,
            'vertices': [],
            'triangles': [],
            'metadata': {
                'parsed_with_fallback': True,
                'fallback_reason': 'Primary parsing failed'
            }
        }
    
    def _detect_format(self, file_path: Path) -> str:
        """Detect file format."""
        extension = file_path.suffix.lower()
        
        format_map = {
            '.stl': 'stl',
            '.obj': 'obj',
            '.3mf': '3mf',
            '.step': 'step',
            '.stp': 'step'
        }
        
        return format_map.get(extension, 'unknown')
```

#### Solution 2: Memory-Efficient Parsing
```python
def parse_large_file_efficiently(file_path: Path):
    """Parse large files with memory efficiency."""
    
    def chunk_reader(file_path, chunk_size=1024*1024):  # 1MB chunks
        with open(file_path, 'rb') as file:
            while True:
                chunk = file.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    
    # For very large files, process in chunks
    if file_path.stat().st_size > 100 * 1024 * 1024:  # 100MB
        print("Processing large file in chunks...")
        
        vertices = []
        triangles = []
        chunk_count = 0
        
        for chunk in chunk_reader(file_path):
            chunk_count += 1
            print(f"Processing chunk {chunk_count}...")
            
            # Process chunk
            processed_vertices, processed_triangles = process_chunk(chunk)
            
            vertices.extend(processed_vertices)
            triangles.extend(processed_triangles)
            
            # Periodically save intermediate results
            if chunk_count % 10 == 0:
                save_intermediate_results(vertices, triangles)
        
        return vertices, triangles
    
    else:
        # Normal parsing for smaller files
        return parse_file_normal(file_path)
```

## Error Code Reference

### Common Error Codes

| Error Code | Category | Description | Solution |
|------------|----------|-------------|----------|
| ERR001 | Database | Database connection failed | Check database file permissions and disk space |
| ERR002 | Parsing | File format not supported | Check file extension and format compatibility |
| ERR003 | Memory | Out of memory during processing | Reduce cache size or increase system memory |
| ERR004 | Graphics | OpenGL context creation failed | Update graphics drivers or enable software rendering |
| ERR005 | File | File not found | Check file path and permissions |
| ERR006 | Network | Download failed (future feature) | Check internet connection and firewall settings |
| ERR007 | Configuration | Invalid configuration file | Reset to default configuration |
| ERR008 | Plugin | Plugin loading failed | Check plugin compatibility and dependencies |
| ERR009 | Performance | Performance threshold exceeded | Optimize system or increase performance limits |
| ERR010 | Security | File security validation failed | Check file integrity and permissions |

### Database Error Codes

| Error Code | SQLite Error | Description | Resolution |
|------------|--------------|-------------|------------|
| DB001 | SQLITE_BUSY | Database is locked | Close other instances, wait and retry |
| DB002 | SQLITE_CORRUPT | Database corruption detected | Run database repair or restore from backup |
| DB003 | SQLITE_CANTOPEN | Cannot open database file | Check file permissions and path |
| DB004 | SQLITE_FULL | Database is full | Clean up old data or increase disk space |
| DB005 | SQLITE_CONSTRAINT | Constraint violation | Check data integrity and constraints |

### Parser Error Codes

| Error Code | Description | Common Causes | Solutions |
|------------|-------------|---------------|-----------|
| PAR001 | Invalid file header | Corrupted or unsupported file | Check file integrity |
| PAR002 | Parse timeout | Large file or complex geometry | Increase timeout or use chunked parsing |
| PAR003 | Memory allocation failed | Insufficient memory | Reduce file size or increase system memory |
| PAR004 | Format validation failed | Incorrect file format | Verify file format with external tools |
| PAR005 | Geometry calculation error | Invalid mesh data | Check geometry validity and repair if possible |

### Performance Error Codes

| Error Code | Description | Trigger Conditions | Solutions |
|------------|-------------|-------------------|-----------|
| PERF001 | Load time exceeded | File load > 30 seconds | Optimize file format or system performance |
| PERF002 | Memory usage critical | Memory usage > 2GB | Clear cache or increase system memory |
| PERF003 | Frame rate below target | FPS < 30 during interaction | Reduce model complexity or update graphics drivers |
| PERF004 | Cache overflow | Cache size exceeds limit | Increase cache size or optimize caching strategy |

## System Recovery

### Application Won't Start

**Step-by-Step Recovery:**

#### Step 1: Basic Recovery
```python
def basic_recovery():
    """Attempt basic application recovery."""
    import shutil
    from pathlib import Path
    import json
    
    # Backup current configuration
    config_files = ['config.json', 'settings.json']
    backup_dir = Path('recovery_backup')
    backup_dir.mkdir(exist_ok=True)
    
    for config_file in config_files:
        config_path = Path(config_file)
        if config_path.exists():
            shutil.copy2(config_path, backup_dir / config_path.name)
    
    # Reset to default configuration
    default_config = {
        'cache_size_mb': 100,
        'max_memory_mb': 2048,
        'enable_progressive_loading': True,
        'enable_caching': True,
        'log_level': 'INFO'
    }
    
    with open('config.json', 'w') as f:
        json.dump(default_config, f, indent=2)
    
    print("Basic recovery completed - configuration reset to defaults")
```

#### Step 2: Database Recovery
```python
def database_recovery():
    """Recover corrupted database."""
    import sqlite3
    from datetime import datetime
    
    db_path = Path("data/candy_cadence.db")
    backup_path = db_path.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    
    if db_path.exists():
        # Create backup
        shutil.copy2(db_path, backup_path)
        print(f"Database backup created: {backup_path}")
        
        try:
            # Try to repair
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check integrity
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            
            if result[0] == 'ok':
                print("Database integrity check passed")
            else:
                print(f"Database corruption detected: {result[0]}")
                
                # Attempt repair
                cursor.execute("PRAGMA quick_check")
                cursor.execute("VACUUM")
                cursor.execute("ANALYZE")
                
                print("Database repair attempted")
            
            conn.close()
            
        except Exception as e:
            print(f"Database repair failed: {e}")
            print(f"Backup available at: {backup_path}")
```

#### Step 3: Complete Reset
```python
def complete_reset():
    """Complete application reset."""
    import shutil
    from pathlib import Path
    
    # Files to preserve
    preserve_files = [
        'installer/',
        'logs/',
        'README.md',
        'LICENSE'
    ]
    
    # Files and directories to remove
    remove_items = [
        'data/',
        'cache/',
        'config.json',
        'settings.json',
        '*.pyc',
        '__pycache__/'
    ]
    
    print("Starting complete application reset...")
    
    # Create backup directory
    backup_dir = Path("pre_reset_backup")
    backup_dir.mkdir(exist_ok=True)
    
    # Preserve important data
    for item in preserve_files:
        item_path = Path(item)
        if item_path.exists():
            if item_path.is_dir():
                shutil.copytree(item_path, backup_dir / item_path.name, dirs_exist_ok=True)
            else:
                shutil.copy2(item_path, backup_dir / item_path.name)
    
    # Remove application data
    for item in remove_items:
        item_path = Path(item)
        if item_path.exists():
            if item_path.is_dir():
                shutil.rmtree(item_path)
            else:
                item_path.unlink()
    
    print("Complete reset finished")
    print(f"Backup preserved in: {backup_dir}")
```

### Data Recovery Procedures

#### Recover Models from Backup
```python
def recover_models_from_backup():
    """Recover models from backup files."""
    import zipfile
    import tempfile
    from pathlib import Path
    
    backup_files = list(Path("backups/").glob("*.zip"))
    
    if not backup_files:
        print("No backup files found")
        return
    
    # Sort by modification time (newest first)
    backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    latest_backup = backup_files[0]
    
    print(f"Using backup: {latest_backup}")
    
    # Extract backup
    extract_dir = Path("recovery_extracted")
    extract_dir.mkdir(exist_ok=True)
    
    with zipfile.ZipFile(latest_backup, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    
    # Copy model files back
    backup_models = extract_dir / "models"
    if backup_models.exists():
        target_models = Path("data/models")
        target_models.mkdir(parents=True, exist_ok=True)
        
        for model_file in backup_models.rglob("*"):
            if model_file.is_file():
                target_file = target_models / model_file.name
                shutil.copy2(model_file, target_file)
        
        print(f"Recovered models from {latest_backup}")
    
    # Clean up
    shutil.rmtree(extract_dir)
```

## Preventive Maintenance

### Regular Maintenance Schedule

#### Daily Tasks (Automated)
```python
def daily_maintenance():
    """Perform daily maintenance tasks."""
    import logging
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    logger.info("Starting daily maintenance tasks")
    
    try:
        # Clean temporary files
        clean_temp_files()
        
        # Rotate logs
        rotate_logs()
        
        # Check disk space
        check_disk_space()
        
        # Monitor performance
        record_performance_metrics()
        
        logger.info("Daily maintenance completed successfully")
        
    except Exception as e:
        logger.error(f"Daily maintenance failed: {e}")

def clean_temp_files():
    """Clean temporary files and cache."""
    import tempfile
    import glob
    from pathlib import Path
    
    # Clean application temp directory
    temp_dir = Path("temp")
    if temp_dir.exists():
        for temp_file in temp_dir.rglob("*"):
            if temp_file.is_file():
                temp_file.unlink()
    
    # Clean Python cache
    for pycache in Path(".").rglob("__pycache__"):
        shutil.rmtree(pycache)
    
    # Clean .pyc files
    for pyc_file in Path(".").rglob("*.pyc"):
        pyc_file.unlink()

def rotate_logs():
    """Rotate log files."""
    import gzip
    import shutil
    from datetime import datetime
    
    log_dir = Path("logs")
    if not log_dir.exists():
        return
    
    current_date = datetime.now().strftime("%Y%m%d")
    
    for log_file in log_dir.glob("*.log"):
        if log_file.stat().st_size > 10 * 1024 * 1024:  # 10MB
            # Compress old log
            compressed_file = log_file.with_suffix(f".{current_date}.log.gz")
            with open(log_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Clear current log
            log_file.write_text("")
            
            print(f"Rotated log: {compressed_file}")

def check_disk_space():
    """Check available disk space."""
    import shutil
    disk_usage = shutil.disk_usage(".")
    free_gb = disk_usage.free / (1024**3)
    
    if free_gb < 1.0:  # Less than 1GB free
        print(f"WARNING: Low disk space: {free_gb:.1f}GB free")
        # Perform additional cleanup if needed
```

#### Weekly Tasks
```python
def weekly_maintenance():
    """Perform weekly maintenance tasks."""
    logger = logging.getLogger(__name__)
    logger.info("Starting weekly maintenance tasks")
    
    try:
        # Database optimization
        optimize_database()
        
        # Performance analysis
        analyze_performance_trends()
        
        # Cache cleanup
        cleanup_cache()
        
        # Security scan
        run_security_scan()
        
        logger.info("Weekly maintenance completed successfully")
        
    except Exception as e:
        logger.error(f"Wearly maintenance failed: {e}")

def optimize_database():
    """Optimize database weekly."""
    conn = sqlite3.connect("data/candy_cadence.db")
    cursor = conn.cursor()
    
    # Vacuum database
    cursor.execute("VACUUM")
    
    # Analyze for query optimization
    cursor.execute("ANALYZE")
    
    # Update statistics
    cursor.execute("PRAGMA optimize")
    
    conn.commit()
    conn.close()
    
    print("Database optimization completed")

def analyze_performance_trends():
    """Analyze weekly performance trends."""
    # Read performance logs and generate trends
    pass

def cleanup_cache():
    """Clean and optimize cache."""
    cache_dir = Path("cache")
    if cache_dir.exists():
        # Remove old cache files
        cutoff_time = time.time() - (7 * 24 * 60 * 60)  # 7 days
        for cache_file in cache_dir.rglob("*"):
            if cache_file.is_file() and cache_file.stat().st_mtime < cutoff_time:
                cache_file.unlink()
    
    print("Cache cleanup completed")

def run_security_scan():
    """Run basic security checks."""
    # Check file permissions
    # Validate configuration files
    # Scan for suspicious files
    print("Security scan completed")
```

### Monitoring and Alerting

#### Health Monitoring System
```python
import time
import psutil
import logging
from datetime import datetime, timedelta
from pathlib import Path

class HealthMonitor:
    """Monitor system health and generate alerts."""
    
    def __init__(self, config_file="health_monitor.json"):
        self.config = self._load_config(config_file)
        self.alert_history = []
    
    def check_system_health(self):
        """Perform comprehensive health check."""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'status': 'healthy',
            'issues': [],
            'warnings': [],
            'metrics': {}
        }
        
        # Check memory usage
        memory = psutil.virtual_memory()
        health_status['metrics']['memory_usage'] = memory.percent
        
        if memory.percent > self.config.get('memory_threshold', 90):
            health_status['issues'].append(f"High memory usage: {memory.percent:.1f}%")
            health_status['status'] = 'critical'
        
        # Check disk space
        disk = psutil.disk_usage('.')
        free_percent = (disk.free / disk.total) * 100
        health_status['metrics']['disk_free_percent'] = free_percent
        
        if free_percent < self.config.get('disk_threshold', 10):
            health_status['issues'].append(f"Low disk space: {free_percent:.1f}% free")
            health_status['status'] = 'critical'
        
        # Check application responsiveness
        response_time = self._check_application_response()
        health_status['metrics']['response_time'] = response_time
        
        if response_time > self.config.get('response_threshold', 5.0):
            health_status['warnings'].append(f"Slow response time: {response_time:.2f}s")
        
        # Check database connectivity
        db_health = self._check_database_health()
        health_status['metrics']['database_healthy'] = db_healthy
        
        if not db_healthy:
            health_status['issues'].append("Database connectivity issues")
            health_status['status'] = 'critical'
        
        # Generate alerts if needed
        self._generate_alerts(health_status)
        
        return health_status
    
    def _check_application_response(self):
        """Check application response time."""
        start_time = time.time()
        try:
            # Simple health check endpoint or operation
            # This would be specific to your application
            return time.time() - start_time
        except:
            return 999.0  # Indicates failure
    
    def _check_database_health(self):
        """Check database health."""
        try:
            conn = sqlite3.connect("data/candy_cadence.db")
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()
            return result[0] == 'ok'
        except:
            return False
    
    def _generate_alerts(self, health_status):
        """Generate alerts based on health status."""
        if health_status['status'] == 'critical':
            self._send_alert("CRITICAL", health_status['issues'])
        elif health_status['warnings']:
            self._send_alert("WARNING", health_status['warnings'])
    
    def _send_alert(self, level, messages):
        """Send alert notification."""
        alert = {
            'level': level,
            'messages': messages,
            'timestamp': datetime.now().isoformat()
        }
        
        self.alert_history.append(alert)
        
        # Log alert
        logger = logging.getLogger(__name__)
        logger.critical(f"Health Alert [{level}]: {'; '.join(messages)}")
        
        # Send to notification system (email, webhook, etc.)
        self._send_notification(alert)
    
    def _send_notification(self, alert):
        """Send notification (implement based on your needs)."""
        # Email notification
        # Webhook notification
        # SMS notification
        # etc.
        pass
    
    def _load_config(self, config_file):
        """Load health monitor configuration."""
        try:
            import json
            with open(config_file, 'r') as f:
                return json.load(f)
        except:
            return {
                'memory_threshold': 90,
                'disk_threshold': 10,
                'response_threshold': 5.0,
                'check_interval': 300  # 5 minutes
            }

# Run health monitoring
if __name__ == "__main__":
    monitor = HealthMonitor()
    health = monitor.check_system_health()
    print(f"System Health: {health['status']}")
    for issue in health['issues']:
        print(f"  ❌ {issue}")
    for warning in health['warnings']:
        print(f"  ⚠️ {warning}")
```

## Conclusion

This troubleshooting guide provides comprehensive solutions to common Candy-Cadence issues. For additional support:

1. Check the logs directory for detailed error information
2. Run the health check script for quick diagnosis
3. Follow the systematic troubleshooting approach
4. Implement preventive maintenance to avoid issues
5. Keep backups of important data

For issues not covered in this guide:
- Check the application logs for detailed error messages
- Review the developer documentation for technical details
- Create support tickets with relevant log files and system information

Regular monitoring and maintenance will help prevent most common issues and ensure optimal application performance.