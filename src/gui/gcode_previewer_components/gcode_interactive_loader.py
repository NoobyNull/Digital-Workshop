"""Interactive G-code Loader - Progressive loading with real-time visualization."""

import os
from typing import List, Optional
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QProgressBar,
    QLabel,
    QPushButton,
    QHBoxLayout,
)

from src.core.logging_config import get_logger
from .gcode_parser import GcodeParser, GcodeMove
from .gcode_renderer import GcodeRenderer


class GcodeLoaderWorker(QThread):
    """Worker thread for loading G-code files progressively."""

    # Signals
    progress_updated = Signal(int, str)  # (percentage, message)
    chunk_loaded = Signal(list)  # Emits list of moves
    loading_complete = Signal(list)  # Emits all moves
    error_occurred = Signal(str)  # Emits error message

    def __init__(self, filepath: str, chunk_size: int = 100) -> None:
        """Initialize the loader worker.

        Args:
            filepath: Path to G-code file
            chunk_size: Number of lines to process per chunk
        """
        super().__init__()
        self.filepath = filepath
        self.chunk_size = chunk_size
        self._is_cancelled = False
        self.parser = GcodeParser()
        self.logger = get_logger(__name__)
        self._process_events_counter = 0

    def _maybe_process_events(self) -> None:
        """No-op placeholder; UI responsiveness is handled on the main thread."""
        self._process_events_counter += 1

    def cancel(self) -> None:
        """Cancel loading."""
        self._is_cancelled = True
        # Log cancellation request (safe even if logger was not initialized for some reason)
        if hasattr(self, "logger"):
            self.logger.info(
                "Interactive G-code load cancel requested for %s", self.filepath
            )

    def run(self) -> None:
        """Run the loading process with true streaming."""
        try:
            # Get file size for progress calculation
            file_size = os.path.getsize(self.filepath)
            self.logger.info(
                "Interactive G-code load started for %s (%s bytes)",
                self.filepath,
                file_size,
            )

            # For validation
            if file_size == 0:
                self.error_occurred.emit("File is empty")
                return

            # Stream file and process in chunks
            all_moves = []
            lines_buffer = []
            bytes_processed = 0
            ui_last_progress = -1
            log_last_progress = -10

            with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if self._is_cancelled:
                        self.logger.info(
                            "Interactive G-code load cancelled while reading %s",
                            self.filepath,
                        )
                        return

                    bytes_processed += len(line.encode("utf-8"))
                    lines_buffer.append(line)

                    # Update progress based on bytes read so the bar moves smoothly
                    progress = int((bytes_processed / file_size) * 100)
                    if progress != ui_last_progress:
                        ui_last_progress = progress
                        self.progress_updated.emit(
                            progress, f"Loading G-code ({progress}%)"
                        )

                        # Log coarse-grained progress (every ~10%)
                        if progress - log_last_progress >= 10:
                            self.logger.info(
                                "Interactive G-code load progress: %d%%",
                                progress,
                            )
                            log_last_progress = progress

                    # Lightweight placeholder; UI responsiveness handled on main thread
                    self._maybe_process_events()

                    # Process when buffer reaches chunk size
                    if len(lines_buffer) >= self.chunk_size:
                        try:
                            moves = self.parser.parse_lines(lines_buffer)
                            all_moves.extend(moves)

                            # Emit chunk for incremental visualization
                            if moves:
                                self.chunk_loaded.emit(moves)
                        except Exception as exc:  # pragma: no cover - defensive
                            self.logger.warning(
                                "Chunk parse failed, continuing: %s", exc
                            )

                        # Clear buffer
                        lines_buffer.clear()

                # Process remaining lines
                if lines_buffer and not self._is_cancelled:
                    try:
                        moves = self.parser.parse_lines(lines_buffer)
                        all_moves.extend(moves)
                        if moves:
                            self.chunk_loaded.emit(moves)
                    except Exception as exc:  # pragma: no cover - defensive
                        self.logger.warning(
                            "Final chunk parse failed, continuing: %s", exc
                        )

            # Final progress
            self.progress_updated.emit(100, "Loading complete")
            self.loading_complete.emit(all_moves)
            self.logger.info(
                "Interactive G-code load complete: %s moves from %s",
                f"{len(all_moves):,}",
                self.filepath,
            )

        except Exception as e:  # pragma: no cover - defensive catch-all
            self.logger.error(
                "Interactive G-code load failed for %s: %s",
                self.filepath,
                e,
            )
            self.error_occurred.emit(f"Failed to load G-code: {str(e)}")


class InteractiveGcodeLoader(QWidget):
    """Widget for interactive G-code loading with real-time visualization."""

    # Signals
    loading_started = Signal()
    loading_complete = Signal(list)  # Emits all moves
    chunk_loaded = Signal(list)  # Emits chunk of moves
    progress_updated = Signal(int, str)  # (percentage, message)
    error_occurred = Signal(str)  # Emits error message

    def __init__(
        self, renderer: GcodeRenderer, parent: Optional[QWidget] = None
    ) -> None:
        """Initialize the interactive loader.

        Args:
            renderer: GcodeRenderer instance for visualization
            parent: Parent widget
        """
        super().__init__(parent)

        self.renderer = renderer
        self.loader_thread: Optional[GcodeLoaderWorker] = None
        self.all_moves: List[GcodeMove] = []
        self.logger = get_logger(__name__)

        self._init_ui()
        self._setup_connections()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Status label
        self.status_label = QLabel("Ready to load G-code file")
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Statistics
        self.stats_label = QLabel("")
        self.stats_label.setVisible(False)
        layout.addWidget(self.stats_label)

        # Control buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.load_button = QPushButton("Load G-code")
        button_layout.addWidget(self.load_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_loading)
        button_layout.addWidget(self.cancel_button)

        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _setup_connections(self) -> None:
        """Setup signal/slot connections."""

    def load_file(self, filepath: str) -> None:
        """Start loading a G-code file.

        Args:
            filepath: Path to G-code file
        """
        if self.loader_thread and self.loader_thread.isRunning():
            return

        self.all_moves = []
        self.status_label.setText(f"Loading: {filepath}")
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.load_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        self.loading_started.emit()

        # Create and start loader thread
        self.loader_thread = GcodeLoaderWorker(filepath)
        self.loader_thread.progress_updated.connect(self._on_progress_updated)
        self.loader_thread.chunk_loaded.connect(self._on_chunk_loaded)
        self.loader_thread.loading_complete.connect(self._on_loading_complete)
        self.loader_thread.error_occurred.connect(self._on_error)
        self.loader_thread.start()

    def cancel_loading(self) -> None:
        """Cancel the current loading operation."""
        if self.loader_thread:
            self.loader_thread.cancel()
            self.loader_thread.wait()
            self.loader_thread = None

        self.status_label.setText("Loading cancelled")
        self.progress_bar.setVisible(False)
        self.load_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

    def _on_progress_updated(self, progress: int, message: str) -> None:
        """Handle progress update."""
        self.progress_bar.setValue(progress)
        self.status_label.setText(message)
        # Re-emit for external listeners such as the main previewer widget.
        self.progress_updated.emit(progress, message)

    def _on_chunk_loaded(self, moves: List[GcodeMove]) -> None:
        """Handle chunk loaded - update visualization incrementally."""
        self.all_moves.extend(moves)

        # Update renderer incrementally
        try:
            self.renderer.add_moves_incremental(moves)
        except Exception as exc:
            self.logger.warning("Incremental render skipped a chunk: %s", exc)

        # Emit signal
        self.chunk_loaded.emit(moves)

    def _on_loading_complete(self, all_moves: List[GcodeMove]) -> None:
        """Handle loading complete."""
        self.all_moves = all_moves

        # Update statistics
        stats = self._calculate_statistics(all_moves)
        self.stats_label.setText(
            f"Total: {stats['total']} moves | "
            f"Rapid: {stats['rapid']} | "
            f"Cutting: {stats['cutting']} | "
            f"Arc: {stats['arc']} | "
            f"Tool Changes: {stats['tool_changes']}"
        )
        self.stats_label.setVisible(True)

        self.status_label.setText("Loading complete")
        self.progress_bar.setVisible(False)
        self.load_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        self.loading_complete.emit(all_moves)

    def _on_error(self, error_message: str) -> None:
        """Handle error."""
        self.status_label.setText(f"Error: {error_message}")
        self.progress_bar.setVisible(False)
        self.load_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        # Propagate to any external listeners so they can update their UI.
        self.error_occurred.emit(error_message)

    @staticmethod
    def _calculate_statistics(moves: List[GcodeMove]) -> dict:
        """Calculate statistics from moves."""
        return {
            "total": len(moves),
            "rapid": sum(1 for m in moves if m.is_rapid),
            "cutting": sum(1 for m in moves if m.is_cutting),
            "arc": sum(1 for m in moves if m.is_arc),
            "tool_changes": sum(1 for m in moves if m.is_tool_change),
        }
