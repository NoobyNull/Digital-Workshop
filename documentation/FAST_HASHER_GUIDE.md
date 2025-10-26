# Fast Hashing System Guide

## Overview

The Fast Hashing System provides high-performance, non-cryptographic hashing for 3D model files using the xxHash128 algorithm. It's designed specifically for the import process to enable:

- **Fast duplicate detection** during import
- **Hash-based thumbnail naming** for efficient storage
- **File identification** in the database
- **Change detection** for file monitoring

## Performance Characteristics

### Speed Targets (Verified by Benchmarks)

- Files under 100MB: **< 1 second**
- Files 100-500MB: **< 3 seconds**  
- Files over 500MB: **< 5 seconds**

### Why xxHash128?

- **10-20x faster than MD5** for large files
- **Excellent collision resistance** (128-bit output)
- **Non-cryptographic** - optimized for speed, not security
- **Well-tested** - used by major projects (Linux kernel, Hadoop, etc.)

## Architecture

### Core Components

```
FastHasher (src/core/fast_hasher.py)
├── hash_file() - Single file hashing with progress
├── hash_chunk() - Stream-based chunk hashing
├── hash_files_batch() - Batch processing
├── verify_hash() - Hash verification
└── get_performance_stats() - Performance metrics

BackgroundHasher (src/gui/background_hasher.py)
└── Integrates FastHasher for UI background processing

file_hash module (src/utils/file_hash.py)
└── Backward-compatible wrapper for existing code
```

### Key Features

1. **Stream-Based Processing**
   - Constant memory usage regardless of file size
   - Adaptive chunk sizing based on file size
   - No need to load entire file into memory

2. **Progress Tracking**
   - Callback support for UI updates
   - Reports every 5% to minimize overhead
   - Includes estimated completion messages

3. **Cancellation Support**
   - Integrates with CancellationToken system
   - Clean cancellation without file corruption
   - Immediate response to cancel requests

4. **Comprehensive Logging**
   - JSON-formatted logs for analysis
   - Performance metrics for every operation
   - Error tracking with full context

## Usage Examples

### Basic File Hashing

```python
from src.core.fast_hasher import FastHasher

hasher = FastHasher()
result = hasher.hash_file("model.stl")

if result.success:
    print(f"Hash: {result.hash_value}")
    print(f"Time: {result.hash_time:.2f}s")
    print(f"Size: {result.file_size / (1024*1024):.1f} MB")
else:
    print(f"Error: {result.error}")
```

### With Progress Callback

```python
def progress_callback(percent, message):
    print(f"{percent:.1f}% - {message}")

result = hasher.hash_file(
    "large_model.stl",
    progress_callback=progress_callback
)
```

### With Cancellation Support

```python
from src.core.cancellation_token import CancellationToken

token = CancellationToken()

# Start hashing in background thread
result = hasher.hash_file(
    "model.stl",
    cancellation_token=token
)

# Cancel if needed
token.cancel()
```

### Batch Processing

```python
files = ["model1.stl", "model2.stl", "model3.stl"]

def batch_progress(completed, total, current_file):
    print(f"{completed}/{total}: {current_file}")

results = hasher.hash_files_batch(
    files,
    progress_callback=batch_progress
)

# Get statistics
stats = hasher.get_performance_stats(results)
print(f"Total time: {stats['total_time_seconds']:.2f}s")
print(f"Throughput: {stats['avg_throughput_mbps']:.1f} MB/s")
```

### Hash Verification

```python
file_path = "model.stl"
expected_hash = "a1b2c3d4..."

if hasher.verify_hash(file_path, expected_hash):
    print("Hash verified!")
else:
    print("Hash mismatch - file may have changed")
```

### Stream-Based Hashing

```python
# For streaming scenarios where data comes in chunks
h = hasher.hash_chunk(chunk1)
h = hasher.hash_chunk(chunk2, h)  # Continue from previous state
h = hasher.hash_chunk(chunk3, h)
final_hash = h.hexdigest()
```

## Integration with Existing Code

### BackgroundHasher Integration

The existing `BackgroundHasher` has been enhanced to use `FastHasher`:

```python
from src.gui.background_hasher import BackgroundHasher

# Create and start background hasher
bg_hasher = BackgroundHasher(parent_window)
bg_hasher.hash_progress.connect(on_progress)
bg_hasher.model_hashed.connect(on_hashed)
bg_hasher.duplicate_found.connect(on_duplicate)
bg_hasher.start()

# Pause/resume
bg_hasher.pause()
bg_hasher.resume()

# Stop
bg_hasher.stop()
bg_hasher.wait()
```

### Backward Compatibility

The `file_hash` module provides backward compatibility:

```python
from src.utils.file_hash import calculate_file_hash, verify_file_hash

# Existing code continues to work
hash_value = calculate_file_hash("model.stl")

# Verification
if verify_file_hash("model.stl", expected_hash):
    print("Verified!")
```

## Performance Optimization

### Adaptive Chunk Sizing

The hasher automatically selects optimal chunk sizes:

- **Small files** (< 10MB): 64KB chunks
- **Medium files** (10-100MB): 256KB chunks
- **Large files** (> 100MB): 1MB chunks

This balances:
- Memory efficiency (smaller chunks)
- I/O efficiency (larger chunks reduce syscalls)
- Progress reporting granularity

### Memory Management

- **Constant memory usage**: Only one chunk in memory at a time
- **Explicit cleanup**: Hash objects properly disposed
- **No leaks**: Verified through 20+ iteration testing
- **Efficient**: < 10MB memory growth over 20 operations

### Progress Reporting Overhead

Progress callbacks are called every 5% to minimize overhead while providing smooth feedback:

```python
# Progress is reported at: 0%, 5%, 10%, 15%, ..., 95%, 100%
# This provides good UX without performance impact
```

## Testing

### Unit Tests

Run comprehensive unit tests:

```bash
python -m pytest tests/test_fast_hasher.py -v
```

Tests cover:
- Basic hashing functionality
- Progress callbacks
- Cancellation support
- Batch processing
- Hash verification
- Error handling
- Memory leak prevention
- Consistency checks

### Performance Benchmarks

Run performance benchmarks:

```bash
python tests/benchmark_fast_hasher.py
```

Benchmarks verify:
- **Performance targets** met for all file sizes
- **Memory stability** over repeated operations
- **Batch efficiency** compared to sequential
- **Cancellation overhead** is minimal

Example output:
```
============================================================
Benchmark: Small File (50MB)
File Size: 50 MB
Target Time: < 1.0s
============================================================
  Creating 50MB test file...
  Running warm-up...
  Running benchmark (3 iterations)...
    Run 1: 0.45s
    Run 2: 0.43s
    Run 3: 0.44s

  Results:
    Average: 0.44s
    Min: 0.43s
    Max: 0.45s
    Throughput: 113.6 MB/s
    Status: ✓ PASS
```

## Troubleshooting

### Slow Performance

**Symptom**: Hashing takes longer than expected

**Possible Causes**:
1. **Disk I/O bottleneck**: Check disk usage and health
2. **Antivirus scanning**: Exclude temp directories
3. **Low memory**: Close other applications
4. **Network drives**: Copy files locally first

**Solutions**:
```python
# Check actual performance
result = hasher.hash_file("slow_file.stl")
throughput = (result.file_size / (1024*1024)) / result.hash_time
print(f"Throughput: {throughput:.1f} MB/s")

# Expected: > 100 MB/s on SSD, > 50 MB/s on HDD
```

### Memory Issues

**Symptom**: High memory usage during hashing

**Diagnosis**:
```python
import tracemalloc

tracemalloc.start()
result = hasher.hash_file("file.stl")
current, peak = tracemalloc.get_traced_memory()
print(f"Peak memory: {peak / (1024*1024):.1f} MB")
tracemalloc.stop()

# Expected: < 10MB for any file size
```

### Inconsistent Hashes

**Symptom**: Same file produces different hashes

**Possible Causes**:
1. **File is changing**: Check for write operations
2. **Concurrent access**: Ensure exclusive access
3. **Disk errors**: Run disk check utility

**Verification**:
```python
# Hash file multiple times
hashes = [hasher.hash_file("file.stl").hash_value for _ in range(3)]
if len(set(hashes)) > 1:
    print("WARNING: Inconsistent hashes detected!")
    print(f"Hashes: {hashes}")
```

### Cancellation Not Working

**Symptom**: Cancellation doesn't stop hashing immediately

**Expected Behavior**:
- Cancellation is checked every chunk
- Response time depends on chunk size
- Maximum delay: time to process one chunk

**For immediate response**:
```python
# Use smaller chunk size for faster cancellation
# (Only if absolutely necessary - impacts performance)
token = CancellationToken()
result = hasher.hash_file("file.stl", cancellation_token=token)
```

## Best Practices

### 1. Reuse Hasher Instances

```python
# Good: Reuse hasher
hasher = FastHasher()
for file in files:
    result = hasher.hash_file(file)

# Avoid: Creating new hasher each time
for file in files:
    hasher = FastHasher()  # Unnecessary overhead
    result = hasher.hash_file(file)
```

### 2. Use Batch Processing for Multiple Files

```python
# Good: Use batch method
results = hasher.hash_files_batch(files)

# Less efficient: Loop with individual calls
for file in files:
    result = hasher.hash_file(file)
```

### 3. Handle Errors Gracefully

```python
result = hasher.hash_file(file_path)
if result.success:
    # Store hash in database
    db.update_hash(model_id, result.hash_value)
else:
    # Log error and handle appropriately
    logger.error(f"Failed to hash {file_path}: {result.error}")
    # Don't retry immediately - may be permission/disk issue
```

### 4. Monitor Performance

```python
results = hasher.hash_files_batch(files)
stats = hasher.get_performance_stats(results)

if stats['avg_throughput_mbps'] < 50:
    logger.warning(f"Low throughput: {stats['avg_throughput_mbps']:.1f} MB/s")
    # Investigate: disk I/O, antivirus, network drive, etc.
```

### 5. Use Progress Callbacks Wisely

```python
# Good: Update UI at reasonable intervals
def progress(percent, message):
    if percent % 10 == 0:  # Every 10%
        self.progress_bar.setValue(percent)

# Avoid: Heavy operations in callback
def bad_progress(percent, message):
    self.refresh_entire_ui()  # Too expensive!
    self.write_to_log_file(message)  # I/O in callback!
```

## API Reference

### FastHasher Class

#### `hash_file(file_path, progress_callback=None, cancellation_token=None) -> HashResult`

Hash a single file with optional progress tracking and cancellation.

**Parameters:**
- `file_path` (str): Path to file to hash
- `progress_callback` (callable, optional): Function(percent, message)
- `cancellation_token` (CancellationToken, optional): Cancellation support

**Returns:**
- `HashResult`: Result object with hash value and metadata

#### `hash_files_batch(file_paths, progress_callback=None, cancellation_token=None) -> List[HashResult]`

Hash multiple files in batch with progress tracking.

**Parameters:**
- `file_paths` (List[str]): List of file paths
- `progress_callback` (callable, optional): Function(completed, total, current_file)
- `cancellation_token` (CancellationToken, optional): Cancellation support

**Returns:**
- `List[HashResult]`: List of results for each file

#### `verify_hash(file_path, expected_hash, cancellation_token=None) -> bool`

Verify file hash matches expected value.

**Parameters:**
- `file_path` (str): Path to file
- `expected_hash` (str): Expected hash value
- `cancellation_token` (CancellationToken, optional): Cancellation support

**Returns:**
- `bool`: True if hash matches, False otherwise

#### `get_performance_stats(results) -> Dict`

Calculate performance statistics from hash results.

**Parameters:**
- `results` (List[HashResult]): List of hash results

**Returns:**
- `Dict`: Performance metrics including throughput, times, etc.

### HashResult Class

Dataclass containing hash operation results:

```python
@dataclass
class HashResult:
    file_path: str           # Path to hashed file
    hash_value: Optional[str]  # Hash value (None if failed)
    file_size: int           # File size in bytes
    hash_time: float         # Time taken in seconds
    success: bool            # Whether operation succeeded
    error: Optional[str]     # Error message if failed
```

## Future Enhancements

Potential improvements for future versions:

1. **Parallel Processing**: Use multiple threads for batch operations
2. **GPU Acceleration**: Leverage GPU for very large files
3. **Progressive Hashing**: Start returning partial hashes for early duplicate detection
4. **Smart Caching**: Cache hashes with file modification time
5. **Distributed Hashing**: Support for network/cloud storage

## Support

For issues, questions, or contributions:

1. Check this documentation first
2. Run unit tests and benchmarks
3. Check logs for detailed error information
4. Review troubleshooting section
5. Open an issue with reproduction steps

## License

Part of Digital Workshop - See main project license.