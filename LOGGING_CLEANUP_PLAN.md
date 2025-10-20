# Logging Cleanup Plan - Add Log Level Switches

## Current State

### Logging Configuration
- **File**: `src/core/logging_config.py`
- **Current Setup**:
  - `setup_logging()` function accepts `log_level` parameter
  - Default: "DEBUG" (too verbose)
  - Single global logger: "3D-MM"
  - Child loggers: "3D-MM.{module_name}"
  - JSON formatter for file logs
  - Console output enabled

### Application Config
- **File**: `src/core/application_config.py`
- **Current Settings**:
  - `log_level: str = "DEBUG"` (line 83)
  - `enable_file_logging: bool = True` (line 84)
  - `log_retention_days: int = 30` (line 85)

### System Initialization
- **File**: `src/core/system_initializer.py`
- **Current Setup**:
  - Calls `setup_logging()` with `config.log_level`
  - Always enables console logging

---

## What Needs to Change

### 1. Application Config (`src/core/application_config.py`)
**Add log level switches:**
```python
# Logging Configuration
log_level: str = "INFO"  # Change default from DEBUG to INFO
enable_debug_logging: bool = False
enable_info_logging: bool = True
enable_warning_logging: bool = True
enable_error_logging: bool = True
enable_critical_logging: bool = True
enable_file_logging: bool = True
log_retention_days: int = 30
```

### 2. Logging Config (`src/core/logging_config.py`)
**Add method to determine effective log level:**
```python
def get_effective_log_level(config: ApplicationConfig) -> str:
    """Determine log level based on enabled switches."""
    if config.enable_debug_logging:
        return "DEBUG"
    elif config.enable_info_logging:
        return "INFO"
    elif config.enable_warning_logging:
        return "WARNING"
    elif config.enable_error_logging:
        return "ERROR"
    elif config.enable_critical_logging:
        return "CRITICAL"
    else:
        return "INFO"  # Fallback
```

### 3. System Initializer (`src/core/system_initializer.py`)
**Update logging setup:**
```python
def _setup_logging(self) -> None:
    """Initialize the logging system."""
    from src.core.logging_config import get_effective_log_level
    
    app_data_path = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
    log_dir = os.path.join(app_data_path, "logs")
    
    effective_level = get_effective_log_level(self.config)
    
    setup_logging(
        log_level=effective_level,
        log_dir=log_dir,
        enable_console=True
    )
```

### 4. Preferences Dialog (`src/gui/preferences.py`)
**Add Debug Settings Tab with log level switches:**
- Checkbox: "Enable DEBUG logging"
- Checkbox: "Enable INFO logging" (checked by default)
- Checkbox: "Enable WARNING logging" (checked by default)
- Checkbox: "Enable ERROR logging" (checked by default)
- Checkbox: "Enable CRITICAL logging" (checked by default)
- Checkbox: "Enable file logging"
- Spinbox: "Log retention days"

---

## Implementation Order

1. **Commit current state** (before changes)
2. **Update ApplicationConfig** - Add log level switches
3. **Update logging_config.py** - Add `get_effective_log_level()` function
4. **Update system_initializer.py** - Use effective log level
5. **Update preferences.py** - Add Debug Settings Tab
6. **Test** - Verify log levels work correctly

---

## Files to Modify

| File | Changes | Lines |
|------|---------|-------|
| `src/core/application_config.py` | Add 5 log level switches | ~10 |
| `src/core/logging_config.py` | Add `get_effective_log_level()` | ~15 |
| `src/core/system_initializer.py` | Use effective log level | ~5 |
| `src/gui/preferences.py` | Add Debug Settings Tab | ~100 |

---

## Default Behavior

- **DEBUG**: OFF (verbose, for development)
- **INFO**: ON (normal operation, important events)
- **WARNING**: ON (potential issues)
- **ERROR**: ON (errors that occurred)
- **CRITICAL**: ON (fatal errors)

This means by default, only INFO and above are logged.

---

## Benefits

✅ Users can control verbosity
✅ Cleaner logs by default (INFO only)
✅ Easy debugging when needed (enable DEBUG)
✅ Persistent settings in preferences
✅ No code changes needed to adjust logging

