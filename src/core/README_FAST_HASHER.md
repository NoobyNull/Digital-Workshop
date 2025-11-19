# FastHasher Service

`src/core/fast_hasher.py` implements the high-speed hashing pipeline used by imports, deduplication, and background analysis.  
It wraps xxHash128 with cancellation, progress callbacks, and thread-friendly streaming so we can fingerprint multi‑GB datasets without blocking the GUI.

---

## Quick Start

```python
from src.core.fast_hasher import FastHasher

hasher = FastHasher(chunk_size=1024 * 1024)  # 1 MB default
result = hasher.hash_file("sample_models/fillet.step")

if result.success:
    print(result.hash_value)        # 128-bit hex string
    print(result.duration_ms)       # precise timing for telemetry
else:
    print(result.error)
```

Key options:
- `chunk_size`: tune when profiling giant STEP assemblies.
- `progress_callback(bytes_read, total_bytes)`: emit UI updates.
- `cancellation_token`: share `threading.Event()` so user cancellations propagate instantly.

---

## Integration Map

| Consumer | Location | Usage |
| --- | --- | --- |
| Import pipeline | `src/core/import_file_manager.py` | Deduplicates incoming files, seeds thumbnail cache, and names managed copies. |
| Background hashing | `src/gui/background_hasher.py` | Keeps the UI responsive while long-running imports finish. |
| Tab data & project services | `src/core/services/tab_data_manager.py` | Uses hashes to detect stale JSON payloads before overwriting. |
| Tests | `tests/test_fast_hasher.py` | Validates perf + checksum accuracy on sample fixtures. |

---

## Performance Targets

| File Size | Target | Notes |
| --- | --- | --- |
| < 100 MB | < 1 s | Typical STL/OBJ imports. |
| 100–500 MB | < 3 s | Dense STEP assemblies. |
| > 500 MB | < 5 s | Rare, but still bounded with streaming I/O. |

Benchmarks live in `tests/benchmark_fast_hasher.py`—run it when tweaking chunk size defaults.

---

## Testing

```bash
pytest tests/test_fast_hasher.py -v
python tests/benchmark_fast_hasher.py --file sample_models/large.step
```

These verify:
- Hash matches xxHash128 reference values.
- Cancellation interrupts within one chunk.
- Progress callbacks fire monotonically.

---

## Troubleshooting

| Symptom | Resolution |
| --- | --- |
| Hashing never completes | Ensure the caller drains the generator—`hash_stream` returns a generator that must be iterated. |
| Duplicate detection misses files | Confirm the database layer normalizes hash casing; FastHasher returns lowercase hex strings. |
| UI freezes | Run hashing inside `QThread` or the background worker (`background_hasher.py`). Direct calls on the GUI thread will block. |
| Hash mismatch across platforms | Verify both ends are using xxHash128 (not xxHash64); tests contain reference values for sanity. |

---

**Owner:** Core services (`core@digitalworkshop.app`)  
**Status:** Production – do not swap hash algorithms without updating every import test.
