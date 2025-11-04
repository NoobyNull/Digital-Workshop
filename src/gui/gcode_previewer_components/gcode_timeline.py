"""G-code Timeline - Interactive timeline for scrubbing through G-code execution."""

from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSlider,
    QLabel,
    QPushButton,
    QSpinBox,
    QProgressBar,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from .gcode_parser import GcodeMove


class GcodeTimeline(QWidget):
    """Interactive timeline for scrubbing through G-code execution."""

    # Signals
    frame_changed = Signal(int)  # Emits frame index when scrubbed
    playback_requested = Signal()  # Emits when play is requested
    pause_requested = Signal()  # Emits when pause is requested
    stop_requested = Signal()  # Emits when stop is requested

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the timeline widget."""
        super().__init__(parent)

        self.moves: List[GcodeMove] = []
        self.current_frame = 0
        self.is_playing = False

        self._init_ui()
        self._setup_connections()

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Title
        title = QLabel("G-code Timeline")
        title_font = QFont()
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Progress bar showing overall progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        # Timeline slider
        slider_layout = QHBoxLayout()
        slider_layout.setSpacing(8)

        self.timeline_slider = QSlider(Qt.Horizontal)
        self.timeline_slider.setMinimum(0)
        self.timeline_slider.setMaximum(100)
        self.timeline_slider.setValue(0)
        self.timeline_slider.setTickPosition(QSlider.TicksBelow)
        self.timeline_slider.setTickInterval(10)
        slider_layout.addWidget(self.timeline_slider)

        # Frame counter
        self.frame_label = QLabel("0 / 0")
        self.frame_label.setMinimumWidth(80)
        slider_layout.addWidget(self.frame_label)

        layout.addLayout(slider_layout)

        # Playback controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(8)

        self.play_button = QPushButton("▶ Play")
        self.play_button.setMaximumWidth(80)
        controls_layout.addWidget(self.play_button)

        self.pause_button = QPushButton("⏸ Pause")
        self.pause_button.setMaximumWidth(80)
        self.pause_button.setEnabled(False)
        controls_layout.addWidget(self.pause_button)

        self.stop_button = QPushButton("⏹ Stop")
        self.stop_button.setMaximumWidth(80)
        controls_layout.addWidget(self.stop_button)

        controls_layout.addStretch()

        # Speed control
        controls_layout.addWidget(QLabel("Speed:"))
        self.speed_spinbox = QSpinBox()
        self.speed_spinbox.setMinimum(10)
        self.speed_spinbox.setMaximum(500)
        self.speed_spinbox.setValue(100)
        self.speed_spinbox.setSuffix("%")
        self.speed_spinbox.setMaximumWidth(80)
        controls_layout.addWidget(self.speed_spinbox)

        layout.addLayout(controls_layout)

        # Statistics frame
        stats_frame = QFrame()
        stats_frame.setStyleSheet("QFrame { border: 1px solid #ccc; border-radius: 4px; }")
        stats_layout = QHBoxLayout(stats_frame)
        stats_layout.setContentsMargins(8, 8, 8, 8)
        stats_layout.setSpacing(16)

        self.stat_rapid = QLabel("Rapid: 0")
        stats_layout.addWidget(self.stat_rapid)

        self.stat_cutting = QLabel("Cutting: 0")
        stats_layout.addWidget(self.stat_cutting)

        self.stat_arc = QLabel("Arc: 0")
        stats_layout.addWidget(self.stat_arc)

        self.stat_tool_changes = QLabel("Tool Changes: 0")
        stats_layout.addWidget(self.stat_tool_changes)

        stats_layout.addStretch()

        layout.addWidget(stats_frame)

    def _setup_connections(self) -> None:
        """Setup signal/slot connections."""
        self.timeline_slider.sliderMoved.connect(self._on_slider_moved)
        self.timeline_slider.valueChanged.connect(self._on_slider_changed)
        self.play_button.clicked.connect(self._on_play_clicked)
        self.pause_button.clicked.connect(self._on_pause_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)

    def set_moves(self, moves: List[GcodeMove]) -> None:
        """Set the G-code moves for the timeline."""
        self.moves = moves
        self.current_frame = 0

        # Update slider range
        max_frame = max(1, len(moves) - 1)
        self.timeline_slider.setMaximum(max_frame)

        # Update statistics
        self._update_statistics()

        # Update frame label
        self._update_frame_label()

    def set_current_frame(self, frame: int) -> None:
        """Set the current frame without emitting signal."""
        self.current_frame = max(0, min(frame, len(self.moves) - 1))
        self.timeline_slider.blockSignals(True)
        self.timeline_slider.setValue(self.current_frame)
        self.timeline_slider.blockSignals(False)
        self._update_frame_label()
        self._update_progress()

    def _on_slider_moved(self, value: int) -> None:
        """Handle slider moved by user."""
        self.current_frame = value
        self._update_frame_label()
        self._update_progress()
        self.frame_changed.emit(value)

    def _on_slider_changed(self, value: int) -> None:
        """Handle slider value changed."""
        self.current_frame = value
        self._update_frame_label()
        self._update_progress()

    def _on_play_clicked(self) -> None:
        """Handle play button clicked."""
        self.is_playing = True
        self.play_button.setEnabled(False)
        self.pause_button.setEnabled(True)
        self.playback_requested.emit()

    def _on_pause_clicked(self) -> None:
        """Handle pause button clicked."""
        self.is_playing = False
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.pause_requested.emit()

    def _on_stop_clicked(self) -> None:
        """Handle stop button clicked."""
        self.is_playing = False
        self.current_frame = 0
        self.play_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.timeline_slider.setValue(0)
        self.stop_requested.emit()

    def _update_frame_label(self) -> None:
        """Update frame counter label."""
        total = len(self.moves)
        self.frame_label.setText(f"{self.current_frame} / {total}")

    def _update_progress(self) -> None:
        """Update progress bar."""
        if len(self.moves) > 0:
            progress = int((self.current_frame / max(1, len(self.moves) - 1)) * 100)
            self.progress_bar.setValue(progress)

    def _update_statistics(self) -> None:
        """Update statistics display."""
        rapid_count = sum(1 for m in self.moves if m.is_rapid)
        cutting_count = sum(1 for m in self.moves if m.is_cutting)
        arc_count = sum(1 for m in self.moves if m.is_arc)
        tool_changes = sum(1 for m in self.moves if m.is_tool_change)

        self.stat_rapid.setText(f"Rapid: {rapid_count}")
        self.stat_cutting.setText(f"Cutting: {cutting_count}")
        self.stat_arc.setText(f"Arc: {arc_count}")
        self.stat_tool_changes.setText(f"Tool Changes: {tool_changes}")

    def get_speed_multiplier(self) -> float:
        """Get playback speed multiplier."""
        return self.speed_spinbox.value() / 100.0
