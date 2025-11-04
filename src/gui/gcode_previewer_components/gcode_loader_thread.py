"""Background G-code file loader with progressive rendering."""

from typing import List, Optional
from PySide6.QtCore import QThread, Signal
from src.core.logging_config import get_logger
from .gcode_parser import GcodeParser, GcodeMove


class GcodeLoaderThread(QThread):
    """Load G-code file in background and emit moves progressively."""

    # Signals
    progress = Signal(int, int)  # (current_line, total_lines)
    moves_loaded = Signal(list)  # Emits batch of moves
    finished_loading = Signal(list)  # Emits all moves when complete
    error_occurred = Signal(str)  # Emits error message

    def __init__(self, filepath: str, batch_size: int = 5000):
        """
        Initialize the loader thread.

        Args:
            filepath: Path to G-code file
            batch_size: Number of moves to batch before emitting signal
        """
        super().__init__()
        self.filepath = filepath
        self.batch_size = batch_size
        self.logger = get_logger(__name__)
        self.parser = GcodeParser()
        self.all_moves: List[GcodeMove] = []
        self._stop_requested = False

    def run(self) -> None:
        """Run the loader in background thread."""
        try:
            with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            total_lines = len(lines)
            self.logger.info(
                f"Starting to load {total_lines:,} lines from {self.filepath}"
            )

            # Parse lines and emit batches
            batch = []
            for line_num, line in enumerate(lines, 1):
                if self._stop_requested:
                    self.logger.info("Loading cancelled by user")
                    return

                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith(";") or line.startswith("%"):
                    continue

                # Remove inline comments
                if ";" in line:
                    line = line.split(";")[0].strip()

                move = self.parser._parse_line(line, line_num)
                if move:
                    batch.append(move)
                    self.all_moves.append(move)
                    self.parser._update_bounds(move)

                # Emit progress every 10000 lines
                if line_num % 10000 == 0:
                    self.progress.emit(line_num, total_lines)

                # Emit batch when it reaches batch_size
                if len(batch) >= self.batch_size:
                    self.moves_loaded.emit(batch)
                    batch = []

            # Emit remaining moves
            if batch:
                self.moves_loaded.emit(batch)

            # Emit completion signal with all moves
            self.finished_loading.emit(self.all_moves)
            self.logger.info(f"Finished loading {len(self.all_moves):,} moves")

        except Exception as e:
            self.logger.error(f"Error loading G-code file: {e}")
            self.error_occurred.emit(str(e))

    def stop(self) -> None:
        """Request the loader to stop."""
        self._stop_requested = True
