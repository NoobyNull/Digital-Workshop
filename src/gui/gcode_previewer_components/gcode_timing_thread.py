"""
Background timing thread extracted from gcode_previewer_main for modularity.
"""

from __future__ import annotations

from typing import Optional, Dict

from PySide6.QtCore import Signal

from src.core.logging_config import get_logger
from src.core.kinematics.gcode_timing import analyze_gcode_moves
from src.gui.workers.base_worker import BaseWorker


class GcodeTimingThread(BaseWorker):
    """Compute aggregate timing for a set of moves off the GUI thread."""

    finished = Signal(dict)
    error_occurred = Signal(str)

    def __init__(
        self,
        moves: list,
        *,
        max_feed_mm_min: float,
        accel_mm_s2: float,
        feed_override_pct: float,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.moves = moves
        self.max_feed_mm_min = max_feed_mm_min
        self.accel_mm_s2 = accel_mm_s2
        self.feed_override_pct = feed_override_pct
        self.logger = get_logger(__name__)

    def run(self) -> None:
        """Compute timing metrics and emit results."""
        try:
            timing = analyze_gcode_moves(
                self.moves,
                max_feed_mm_min=self.max_feed_mm_min,
                accel_mm_s2=self.accel_mm_s2,
                feed_override_pct=self.feed_override_pct,
            )
            result: Dict[str, float]
            if isinstance(timing, dict):
                result = timing
            elif hasattr(timing, "_asdict"):
                result = timing._asdict()  # type: ignore[assignment]
            else:
                result = dict(timing)
            self.finished.emit(result)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("G-code timing failed: %s", exc, exc_info=True)
            self.error_occurred.emit(str(exc))
