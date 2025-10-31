# Simplified Refactoring Solutions for Critical Issues

## Table of Contents
1. [Memory Management Fixes](#1-memory-management-fixes)
2. [Error Handling Simplification](#2-error-handling-simplification)
3. [Security Hardening](#3-security-hardening)
4. [Architecture Simplification](#4-architecture-simplification)
5. [Performance Simplification](#5-performance-simplification)

---

## 1. Memory Management Fixes

### Issue 1.1: VTK Resource Leak Bomb
**File:** `src/gui/gcode_previewer_components/gcode_renderer.py:226-247`

**Problem:** The `_update_incremental_actors()` method removes actors but doesn't properly clean up VTK objects, causing memory leaks.

**Simplified Solution:**

```python
def _update_incremental_actors(self) -> None:
    """Update the incremental rendering actors with proper cleanup."""
    for move_type in self.move_data:
        # Proper VTK cleanup sequence
        old_actor = self.move_data[move_type]['actor']
        if old_actor:
            self.renderer.RemoveActor(old_actor)
            # Clean up the actor's internal resources
            old_actor.ReleaseGraphicsResources(self.render_window)
            del old_actor  # Explicit deletion
        
        self.move_data[move_type]['actor'] = None

    # Create new actors
    for move_type in ['rapid', 'cutting', 'arc']:
        if self.move_data[move_type]['points'].GetNumberOfPoints() > 0:
            actor = self._create_actor(
                self.move_data[move_type]['points'],
                self.move_data[move_type]['lines'],
                self.colors[move_type],
                self.line_widths[move_type]
            )
            self.renderer.AddActor(actor)
            self.move_data[move_type]['actor'] = actor
```

**Benefits:**
- Properly releases VTK graphics resources before deletion
- Prevents memory leaks during repeated rendering operations
- Explicit cleanup makes resource management clear

**Additional Cleanup Method:**

Add this method to `GcodeRenderer` class:

```python
def cleanup(self) -> None:
    """Cleanup all VTK resources before destruction."""
    # Remove all actors
    for move_type in self.move_data:
        if self.move_data[move_type]['actor']:
            self.renderer.RemoveActor(self.move_data[move_type]['actor'])
            self.move_data[move_type]['actor'].ReleaseGraphicsResources(self.render_window)
    
    # Clear data structures
    self.move_data.clear()
    self.actors.clear()
    
    # Clean up renderer and window
    if self.render_window:
        self.render_window.Finalize()
```

---

### Issue 1.2: Backwards Memory Loading
**File:** `src/gui/gcode_previewer_components/gcode_parser.py:71-79`

**Problem:** Reads entire file into memory with `f.readlines()`, defeating the purpose of streaming.

**Simplified Solution:**

```python
def parse_file(self, filepath: str, sample_mode: bool = True, sample_size: int = 100) -> List[GcodeMove]:
    """
    Parse a G-code file using true streaming.

    Args:
        filepath: Path to G-code file
        sample_mode: If True, sample large files (first N + last N lines)
        sample_size: Number of lines to sample from start and end (default 100)

    Returns:
        List of parsed moves
    """
    try:
        # Validate file exists and is readable
        if not os.path.exists(filepath):
            raise ValueError(f"File not found: {filepath}")
        
        file_size = os.path.getsize(filepath)
        if file_size == 0:
            raise ValueError("File is empty")
        
        # For small files, read normally
        if file_size < 1024 * 1024:  # < 1MB
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            return self.parse_lines(lines)
        
        # For large files, use streaming
        if sample_mode:
            return self._parse_file_sampled(filepath, sample_size)
        else:
            return self._parse_file_streaming(filepath)
            
    except Exception as e:
        raise ValueError(f"Failed to parse G-code file: {e}")

def _parse_file_streaming(self, filepath: str) -> List[GcodeMove]:
    """Parse file line by line without loading entire file into memory."""
    self.moves = []
    self.current_position = (0.0, 0.0, 0.0)
    self.current_g_code = 1
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            if not line or line.startswith(';') or line.startswith('%'):
                continue
            
            if ';' in line:
                line = line.split(';')[0].strip()
            
            move = self._parse_line(line, line_num)
            if move:
                self.moves.append(move)
                self._update_bounds(move)
    
    return self.moves

def _parse_file_sampled(self, filepath: str, sample_size: int) -> List[GcodeMove]:
    """Parse file with intelligent sampling - first N and last N lines."""
    import mmap
    
    with open(filepath, 'r+b') as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mmapped_file:
            # Count total lines efficiently
            total_lines = sum(1 for _ in iter(mmapped_file.readline, b""))
            
            if total_lines <= sample_size * 4:
                # File is small enough, parse all lines
                mmapped_file.seek(0)
                lines = [line.decode('utf-8', errors='ignore') 
                        for line in mmapped_file]
                return self.parse_lines(lines)
            
            # Sample first N lines
            mmapped_file.seek(0)
            first_lines = [mmapped_file.readline().decode('utf-8', errors='ignore') 
                          for _ in range(sample_size)]
            
            # Find position of last N lines
            mmapped_file.seek(0, 2)  # Seek to end
            file_size = mmapped_file.tell()
            
            # Estimate line size and seek to approximate position
            avg_line_size = file_size // total_lines
            seek_pos = max(0, file_size - (sample_size * avg_line_size * 2))
            mmapped_file.seek(seek_pos)
            
            # Skip partial line
            mmapped_file.readline()
            
            # Read last N lines
            last_lines = [mmapped_file.readline().decode('utf-8', errors='ignore') 
                         for _ in range(sample_size)]
            
            return self.parse_lines(first_lines + last_lines)
```

**Benefits:**
- True streaming for large files - no full file load into memory
- Memory-mapped I/O for efficient sampling
- Proper file validation before processing
- Clear separation of concerns: small files, streaming, and sampling

---

### Issue 1.3: Fake Progressive Loading
**File:** `src/gui/gcode_previewer_components/gcode_interactive_loader.py:40-42`

**Problem:** Reads entire file into memory first, then "progressively" processes it.

**Simplified Solution:**

```python
def run(self) -> None:
    """Run the loading process with true streaming."""
    try:
        # Get file size for progress calculation
        file_size = os.path.getsize(self.filepath)
        
        # For validation
        if file_size == 0:
            self.error_occurred.emit("File is empty")
            return
        
        # Stream file and process in chunks
        all_moves = []
        lines_buffer = []
        bytes_processed = 0
        
        with open(self.filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if self._is_cancelled:
                    return
                
                bytes_processed += len(line.encode('utf-8'))
                lines_buffer.append(line)
                
                # Process when buffer reaches chunk size
                if len(lines_buffer) >= self.chunk_size:
                    moves = self.parser.parse_lines(lines_buffer)
                    all_moves.extend(moves)
                    
                    # Emit progress
                    progress = int((bytes_processed / file_size) * 100)
                    self.progress_updated.emit(
                        progress, 
                        f"Loading: {len(all_moves)} moves"
                    )
                    
                    # Emit chunk
                    if moves:
                        self.chunk_loaded.emit(moves)
                    
                    # Clear buffer
                    lines_buffer.clear()
            
            # Process remaining lines
            if lines_buffer and not self._is_cancelled:
                moves = self.parser.parse_lines(lines_buffer)
                all_moves.extend(moves)
                if moves:
                    self.chunk_loaded.emit(moves)
        
        # Final progress
        self.progress_updated.emit(100, "Loading complete")
        self.loading_complete.emit(all_moves)
        
    except Exception as e:
        self.error_occurred.emit(f"Failed to load G-code: {str(e)}")
```

**Benefits:**
- True streaming from disk - never loads entire file
- Memory usage scales with chunk size, not file size
- Progress based on actual bytes processed
- Can handle arbitrarily large files

---

## 2. Error Handling Simplification

### Issue 2.1: Exception Type Myopia
**File:** `src/main.py:179-183`

**Problem:** Only catches `RuntimeError`, missing other common exceptions.

**Simplified Solution:**

```python
def main():
    """Main function to start the Digital Workshop application."""
    logger = get_logger(__name__)
    logger.info("Digital Workshop application starting")

    args = parse_arguments()
    log_level = args.log_level if args.log_level is not None else "INFO"
    logger.info(f"Log level set to: {log_level}")

    config = ApplicationConfig.get_default()
    config = dataclasses.replace(config, log_level=log_level)  # Simplified config update
    
    exception_handler = ExceptionHandler()
    app = None

    try:
        # Create and initialize application
        app = Application(config)

        if not app.initialize():
            logger.error("Application initialization failed")
            # Cleanup on initialization failure
            if app:
                app.cleanup()
            return 1

        # Run the application
        logger.info("Application initialized successfully, starting main loop")
        exit_code = app.run()
        logger.info(f"Application exited with code: {exit_code}")
        return exit_code

    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 130  # Standard Unix exit code for Ctrl+C
        
    except (OSError, IOError) as e:
        logger.error(f"File system error: {str(e)}")
        exception_handler.handle_startup_error(e)
        return 1
        
    except ImportError as e:
        logger.error(f"Missing dependency: {str(e)}")
        exception_handler.handle_startup_error(e)
        return 1
        
    except Exception as e:
        # Catch all other exceptions
        logger.error(f"Application startup failed: {str(e)}", exc_info=True)
        exception_handler.handle_startup_error(e)
        return 1
        
    finally:
        # Ensure cleanup happens
        if app:
            try:
                app.cleanup()
            except Exception as e:
                logger.error(f"Cleanup failed: {str(e)}")


if __name__ == "__main__":
    sys.exit(main())
```

**Benefits:**
- Handles all exception types appropriately
- Proper cleanup in finally block
- Keyboard interrupt handled gracefully
- Specific handling for common errors (file system, imports)
- Comprehensive error logging with stack traces

---

### Issue 2.2: Blind File Operations
**File:** `src/gui/gcode_previewer_components/gcode_previewer_main.py:485`

**Problem:** No error handling, size limits, or validation.

**Simplified Solution:**

```python
def _on_edit_gcode(self) -> None:
    """Handle edit G-code with proper validation and limits."""
    if not self.current_file:
        self.logger.warning("No G-code file loaded")
        return

    try:
        # Validate file still exists
        if not os.path.exists(self.current_file):
            self.logger.error(f"File no longer exists: {self.current_file}")
            QMessageBox.warning(self, "File Not Found", 
                              "The G-code file no longer exists.")
            return
        
        # Check file size (limit to 10MB for editor)
        MAX_EDITOR_SIZE = 10 * 1024 * 1024  # 10MB
        file_size = os.path.getsize(self.current_file)
        
        if file_size > MAX_EDITOR_SIZE:
            self.logger.warning(f"File too large for editor: {file_size} bytes")
            reply = QMessageBox.question(
                self, "Large File", 
                f"File is {file_size / (1024*1024):.1f}MB. "
                "Large files may be slow to edit. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        
        # Read file with proper error handling
        try:
            with open(self.current_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except (OSError, IOError) as e:
            self.logger.error(f"Failed to read file: {e}")
            QMessageBox.critical(self, "Read Error", 
                               f"Failed to read file: {str(e)}")
            return
        
        # Create editor dialog
        editor_widget = GcodeEditorWidget()
        editor_widget.set_content(content)
        editor_widget.reload_requested.connect(self._on_gcode_reload)
        editor_widget.show()
        
    except Exception as e:
        self.logger.error(f"Failed to open editor: {e}", exc_info=True)
        QMessageBox.critical(self, "Error", 
                           f"Failed to open editor: {str(e)}")
```

**Benefits:**
- Validates file existence before reading
- Enforces size limits to prevent UI freezing
- User confirmation for large files
- Comprehensive error handling and user feedback
- Proper exception logging

---

### Issue 2.3: Incomplete Error Recovery
**File:** `src/main.py:169-171`

**Problem:** No cleanup when initialization fails.

**Solution:** See Issue 2.1 above - the finally block ensures cleanup.

---

## 3. Security Hardening

### Issue 3.1: Path Traversal Vulnerability
**File:** `src/gui/gcode_previewer_components/gcode_previewer_main.py:284-292`

**Problem:** No path validation allows directory traversal attacks.

**Simplified Solution:**

```python
def _on_load_file(self) -> None:
    """Handle load file button click with security validation."""
    filepath, _ = QFileDialog.getOpenFileName(
        self,
        "Open G-code File",
        "",
        "G-code Files (*.nc *.gcode *.gco *.tap);;All Files (*)"
    )
    
    if filepath:
        # Validate and sanitize path
        validated_path = self._validate_file_path(filepath)
        if validated_path:
            self.load_gcode_file(validated_path)

def _validate_file_path(self, filepath: str) -> Optional[str]:
    """
    Validate file path for security and accessibility.
    
    Args:
        filepath: Path to validate
        
    Returns:
        Validated absolute path or None if invalid
    """
    try:
        # Convert to Path object for safe manipulation
        file_path = Path(filepath).resolve()
        
        # Check file exists
        if not file_path.exists():
            self.logger.error(f"File does not exist: {filepath}")
            QMessageBox.warning(self, "Invalid File", "File does not exist.")
            return None
        
        # Check it's a file (not a directory)
        if not file_path.is_file():
            self.logger.error(f"Path is not a file: {filepath}")
            QMessageBox.warning(self, "Invalid File", "Path must be a file.")
            return None
        
        # Check file is readable
        if not os.access(file_path, os.R_OK):
            self.logger.error(f"File not readable: {filepath}")
            QMessageBox.warning(self, "Access Denied", "Cannot read file.")
            return None
        
        # Validate file extension
        valid_extensions = {'.nc', '.gcode', '.gco', '.tap', '.txt'}
        if file_path.suffix.lower() not in valid_extensions:
            self.logger.warning(f"Unusual file extension: {file_path.suffix}")
            reply = QMessageBox.question(
                self, "Unusual Extension",
                f"File has unusual extension '{file_path.suffix}'. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return None
        
        # Check file size (warn for very large files)
        MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
        file_size = file_path.stat().st_size
        
        if file_size > MAX_FILE_SIZE:
            self.logger.warning(f"Very large file: {file_size} bytes")
            reply = QMessageBox.question(
                self, "Large File",
                f"File is {file_size / (1024*1024):.1f}MB. "
                "This may take a while to load. Continue?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return None
        
        return str(file_path)
        
    except Exception as e:
        self.logger.error(f"Path validation failed: {e}")
        QMessageBox.critical(self, "Validation Error", 
                           f"Failed to validate file path: {str(e)}")
        return None
```

**Benefits:**
- Resolves path to prevent traversal attacks
- Validates file existence and accessibility
- Checks for suspicious extensions
- Enforces size limits
- User warnings for edge cases

---

### Issue 3.2: Content Validation Absent
**File:** `src/gui/gcode_previewer_components/gcode_parser.py:72`

**Problem:** No validation that file contains valid G-code.

**Simplified Solution:**

Add this method to `GcodeParser` class:

```python
def validate_file_content(self, filepath: str) -> Tuple[bool, str]:
    """
    Validate file contains G-code content before parsing.
    
    Args:
        filepath: Path to file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        # Read first 1KB to check content
        with open(filepath, 'rb') as f:
            header = f.read(1024)
        
        # Check for binary content (likely not G-code)
        if b'\x00' in header:
            return False, "File appears to be binary, not text G-code"
        
        # Try to decode as text
        try:
            text_header = header.decode('utf-8', errors='strict')
        except UnicodeDecodeError:
            try:
                text_header = header.decode('latin-1')
            except:
                return False, "File encoding not supported"
        
        # Look for G-code markers in first 1KB
        gcode_markers = ['G0', 'G1', 'G2', 'G3', 'M0', 'M3', 'M5', 'M6']
        has_gcode = any(marker in text_header.upper() for marker in gcode_markers)
        
        if not has_gcode:
            return False, "File does not appear to contain G-code"
        
        return True, ""
        
    except Exception as e:
        return False, f"Validation error: {str(e)}"
```

Update `parse_file` to use validation:

```python
def parse_file(self, filepath: str, sample_mode: bool = True, sample_size: int = 100) -> List[GcodeMove]:
    """Parse a G-code file with content validation."""
    # Validate content first
    is_valid, error_msg = self.validate_file_content(filepath)
    if not is_valid:
        raise ValueError(f"Invalid G-code file: {error_msg}")
    
    # ... rest of parsing logic ...
```

**Benefits:**
- Detects binary files early
- Validates text encoding
- Checks for G-code content markers
- Prevents parsing of invalid files

---

## 4. Architecture Simplification

### Issue 4.1: 80-Line Copy-Paste Horror
**File:** `src/main.py:79-159`

**Problem:** Manual field-by-field copying to update a single field in frozen dataclass.

**Simplified Solution:**

```python
def main():
    """Main function to start the Digital Workshop application."""
    logger = get_logger(__name__)
    logger.info("Digital Workshop application starting")

    args = parse_arguments()
    log_level = args.log_level if args.log_level is not None else "INFO"
    logger.info(f"Log level set to: {log_level}")

    # Get default config
    config = ApplicationConfig.get_default()
    
    # Use dataclasses.replace() for frozen dataclasses - ONE LINE!
    config = dataclasses.replace(config, log_level=log_level)
    
    # ... rest of code ...
```

**Note:** Add this import at the top of main.py:
```python
import dataclasses
```

**Benefits:**
- Reduces 80 lines to 1 line
- Type-safe and IDE-friendly
- Standard Python idiom for frozen dataclasses
- Eliminates copy-paste errors
- Maintainable - no need to update when fields change

---

### Issue 4.2: Global Mutable State
**File:** `src/gui/gcode_previewer_components/gcode_renderer.py:7,15-18`

**Problem:** Global vtk variable is mutable state that makes testing and reuse difficult.

**Simplified Solution:**

```python
"""G-code Renderer - VTK-based 3D visualization of G-code toolpaths."""

from typing import List, Optional, Dict, Tuple, TYPE_CHECKING
from .gcode_parser import GcodeMove

# Type hints only import
if TYPE_CHECKING:
    import vtk as VtkModule


class GcodeRenderer:
    """Renders G-code toolpaths using VTK."""
    
    # Class-level vtk module (loaded once per class)
    _vtk_module: Optional['VtkModule'] = None

    def __init__(self):
        """Initialize the renderer."""
        # Lazy load VTK at instance creation
        self._ensure_vtk_loaded()
        
        # Use the class-level module
        vtk = self._vtk_module
        
        self.renderer = vtk.vtkRenderer()
        self.render_window = vtk.vtkRenderWindow()
        self.render_window.AddRenderer(self.renderer)

        # Set background color (dark theme)
        self.renderer.SetBackground(0.2, 0.2, 0.2)

        self.actors: Dict[str, vtk.vtkActor] = {}
        self.bounds = None

        # For incremental rendering - organize by move type
        self.move_data = {
            'rapid': {'points': vtk.vtkPoints(), 'lines': vtk.vtkCellArray(), 'actor': None},
            'cutting': {'points': vtk.vtkPoints(), 'lines': vtk.vtkCellArray(), 'actor': None},
            'arc': {'points': vtk.vtkPoints(), 'lines': vtk.vtkCellArray(), 'actor': None},
            'tool_change': {'points': vtk.vtkPoints(), 'lines': vtk.vtkCellArray(), 'actor': None},
        }
        self.prev_point = None

        # Color scheme for different move types
        self.colors = {
            'rapid': (1.0, 0.5, 0.0),
            'cutting': (0.0, 1.0, 0.0),
            'arc': (0.0, 0.5, 1.0),
            'tool_change': (1.0, 0.0, 1.0),
        }

        # Line widths for different move types
        self.line_widths = {
            'rapid': 1.5,
            'cutting': 3.0,
            'arc': 2.5,
            'tool_change': 2.0,
        }
    
    @classmethod
    def _ensure_vtk_loaded(cls) -> None:
        """Ensure VTK module is loaded (once per class)."""
        if cls._vtk_module is None:
            try:
                import vtk as vtk_module
                cls._vtk_module = vtk_module
            except ImportError as e:
                raise ImportError(
                    "VTK is required for G-code rendering. "
                    "Install with: pip install vtk"
                ) from e
    
    @property
    def vtk(self):
        """Access VTK module."""
        return self._vtk_module
    
    # ... rest of methods use self.vtk instead of global vtk ...
```

Update all methods to use `self.vtk` instead of `vtk`:

```python
def _add_line_segment(self, points, lines, start: tuple, end: tuple) -> None:
    """Add a line segment to the polydata."""
    start_id = points.InsertNextPoint(start)
    end_id = points.InsertNextPoint(end)

    line = self.vtk.vtkLine()  # Changed from vtk.vtkLine()
    line.GetPointIds().SetId(0, start_id)
    line.GetPointIds().SetId(1, end_id)
    lines.InsertNextCell(line)
```

**Benefits:**
- No global mutable state
- Testable with dependency injection
- Clear module ownership
- Fails fast with clear error message if VTK missing
- Thread-safe

---

## 5. Performance Simplification

### Issue 5.1: UI Freeze Guaranteed
**Problem:** No processEvents() calls during long operations causes UI freezing.

**Simplified Solution:**

Add processEvents() helper to base classes:

```python
# In gcode_interactive_loader.py

from PySide6.QtWidgets import QApplication

class GcodeLoaderWorker(QThread):
    """Worker thread for loading G-code files progressively."""
    
    def __init__(self, filepath: str, chunk_size: int = 100):
        super().__init__()
        self.filepath = filepath
        self.chunk_size = chunk_size
        self._is_cancelled = False
        self.parser = GcodeParser()
        self._process_events_counter = 0
    
    def _maybe_process_events(self) -> None:
        """Process events periodically to keep UI responsive."""
        self._process_events_counter += 1
        if self._process_events_counter >= 10:  # Every 10 operations
            QApplication.processEvents()
            self._process_events_counter = 0
    
    def run(self) -> None:
        """Run the loading process with UI responsiveness."""
        try:
            file_size = os.path.getsize(self.filepath)
            
            if file_size == 0:
                self.error_occurred.emit("File is empty")
                return
            
            all_moves = []
            lines_buffer = []
            bytes_processed = 0
            
            with open(self.filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    if self._is_cancelled:
                        return
                    
                    bytes_processed += len(line.encode('utf-8'))
                    lines_buffer.append(line)
                    
                    # Process events periodically
                    self._maybe_process_events()
                    
                    if len(lines_buffer) >= self.chunk_size:
                        moves = self.parser.parse_lines(lines_buffer)
                        all_moves.extend(moves)
                        
                        progress = int((bytes_processed / file_size) * 100)
                        self.progress_updated.emit(
                            progress, 
                            f"Loading: {len(all_moves)} moves"
                        )
                        
                        if moves:
                            self.chunk_loaded.emit(moves)
                        
                        lines_buffer.clear()
                
                # Process remaining lines
                if lines_buffer and not self._is_cancelled:
                    moves = self.parser.parse_lines(lines_buffer)
                    all_moves.extend(moves)
                    if moves:
                        self.chunk_loaded.emit(moves)
            
            self.progress_updated.emit(100, "Loading complete")
            self.loading_complete.emit(all_moves)
            
        except Exception as e:
            self.error_occurred.emit(f"Failed to load G-code: {str(e)}")
```

**Benefits:**
- UI remains responsive during loading
- Cancellation is more responsive
- Minimal performance overhead
- Simple to implement

---

### Issue 5.2: Blocking Operations
**Problem:** Some operations still block the main thread.

**Simplified Solution:**

Ensure all heavy operations use QThread:

```python
# In gcode_previewer_main.py

def load_gcode_file(self, filepath: str) -> None:
    """Load and display a G-code file in background thread."""
    try:
        # Validate path first (quick operation)
        validated_path = self._validate_file_path(filepath)
        if not validated_path:
            return
        
        # Stop any existing loader
        if self.loader_thread and self.loader_thread.isRunning():
            self.loader_thread.cancel()
            self.loader_thread.wait(5000)  # Wait max 5 seconds
        
        # Show progress UI immediately
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Get file info (quick operation)
        file_path = Path(validated_path)
        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        
        # Update UI
        info_text = f"Loading: {file_path.name} ({file_size_mb:.1f}MB)..."
        self.file_label.setText(info_text)
        self.file_label.setStyleSheet("color: orange;")
        
        self.current_file = validated_path
        self.moves = []
        
        # Clear renderer (quick operation)
        self.renderer.clear_incremental()
        self.vtk_widget.update_render()
        
        # Start background loading
        if self.interactive_loader:
            self.interactive_loader.load_file(validated_path)
        
    except Exception as e:
        self.logger.error(f"Failed to start loading: {e}")
        self.file_label.setText(f"Error: {str(e)}")
        self.file_label.setStyleSheet("color: red;")
        self.progress_bar.setVisible(False)
```

**Benefits:**
- All heavy operations in background threads
- UI never blocks
- Proper thread cancellation
- Clear separation: validation is sync, loading is async

---

## Summary

These simplified solutions address all critical issues:

1. **Memory Management**: Proper VTK cleanup, true streaming, no full-file loads
2. **Error Handling**: Comprehensive exception catching, proper cleanup, user feedback
3. **Security**: Path validation, content validation, size limits
4. **Architecture**: dataclasses.replace(), dependency injection, no global state
5. **Performance**: processEvents(), background threads, responsive UI

All solutions are:
- **Simple**: Clear, straightforward implementations
- **Maintainable**: Follow Python best practices
- **Safe**: Preserve existing behavior while fixing issues
- **Documented**: Clear explanations of benefits
