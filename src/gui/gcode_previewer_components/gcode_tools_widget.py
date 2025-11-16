"""G-code tools panel widget.

Right-hand tools widget for the G-code previewer, responsible for:
- Timeline playback controls
- Interactive loader panel
- Visualization controls (mode, camera controls, layers)
- Statistics summary
- Moves table
- Embedded G-code editor
- Per-file progress bar at the bottom
"""

from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QGroupBox,
    QTableWidget,
    QTabWidget,
    QProgressBar,
    QComboBox,
    QPushButton,
    QCheckBox,
)

from src.core.logging_config import get_logger
from .gcode_renderer import GcodeRenderer
from .gcode_timeline import GcodeTimeline
from .gcode_interactive_loader import InteractiveGcodeLoader
from .gcode_editor import GcodeEditorWidget


class GcodeToolsWidget(QWidget):
    """Composite tools widget used on the right-hand side of the previewer.

    This widget is intentionally self-contained so it can be docked or reused
    in other contexts (similar to the metadata editor and project details
    widgets), while still exposing child widgets that the main previewer
    drives (timeline, loader, editor, etc.).
    """

    def __init__(self, renderer: Optional[GcodeRenderer], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.renderer = renderer

        # Child widgets that the previewer will interact with directly
        self.timeline: Optional[GcodeTimeline] = None
        self.interactive_loader: Optional[InteractiveGcodeLoader] = None
        self.editor: Optional[GcodeEditorWidget] = None

        self.stats_label: Optional[QLabel] = None
        self.moves_table: Optional[QTableWidget] = None

        self.viz_mode_combo: Optional[QComboBox] = None
        self.camera_controls_checkbox: Optional[QCheckBox] = None
        self.layer_combo: Optional[QComboBox] = None
        self.show_all_layers_btn: Optional[QPushButton] = None
        self.edit_gcode_button: Optional[QPushButton] = None

        self.progress_bar: Optional[QProgressBar] = None

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        tabs = QTabWidget()

        # Tab 1: Timeline and Loader + visualization controls
        timeline_loader_widget = QWidget()
        timeline_loader_layout = QVBoxLayout(timeline_loader_widget)
        timeline_loader_layout.setContentsMargins(0, 0, 0, 0)
        timeline_loader_layout.setSpacing(8)

        self.timeline = GcodeTimeline()
        timeline_loader_layout.addWidget(self.timeline)

        if self.renderer is not None:
            self.interactive_loader = InteractiveGcodeLoader(self.renderer)
            timeline_loader_layout.addWidget(self.interactive_loader)
        else:
            placeholder = QLabel("Interactive loader unavailable")
            timeline_loader_layout.addWidget(placeholder)

        self._init_visualization_controls(timeline_loader_layout)
        tabs.addTab(timeline_loader_widget, "Timeline & Loader")

        # Tab 2: Statistics and Moves
        stats_moves_widget = QWidget()
        stats_moves_layout = QVBoxLayout(stats_moves_widget)
        stats_moves_layout.setContentsMargins(0, 0, 0, 0)
        stats_moves_layout.setSpacing(8)

        stats_group = QGroupBox("Toolpath Statistics")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_label = QLabel("Load a G-code file to see statistics")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        stats_moves_layout.addWidget(stats_group)

        moves_group = QGroupBox("G-code Moves")
        moves_layout = QVBoxLayout(moves_group)

        self.moves_table = QTableWidget()
        self.moves_table.setColumnCount(7)
        self.moves_table.setHorizontalHeaderLabels(
            ["Line", "Type", "X", "Y", "Z", "Feed", "Speed"]
        )
        self.moves_table.setMaximumHeight(200)
        moves_layout.addWidget(self.moves_table)

        stats_moves_layout.addWidget(moves_group)
        stats_moves_layout.addStretch()

        tabs.addTab(stats_moves_widget, "Statistics")

        # Tab 3: G-code Editor
        self.editor = GcodeEditorWidget()
        tabs.addTab(self.editor, "Editor")

        layout.addWidget(tabs)

        # Bottom progress bar (used by the background loader in the main widget)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def _init_visualization_controls(self, parent_layout: QVBoxLayout) -> None:
        """Create the visualization controls group.

        The main previewer connects the signals on these controls.
        """
        viz_group = QGroupBox("Visualization")
        viz_layout = QGridLayout(viz_group)

        # Row 0: visualization mode + view controls
        viz_layout.addWidget(QLabel("Visualization:"), 0, 0)
        self.viz_mode_combo = QComboBox()
        self.viz_mode_combo.addItems(["Default", "Feed Rate", "Spindle Speed"])
        viz_layout.addWidget(self.viz_mode_combo, 0, 1)

        self.camera_controls_checkbox = QCheckBox("View Controls")
        self.camera_controls_checkbox.setChecked(True)
        viz_layout.addWidget(self.camera_controls_checkbox, 0, 2)

        # Row 1: layer selection + actions
        viz_layout.addWidget(QLabel("Layers:"), 1, 0)
        self.layer_combo = QComboBox()
        viz_layout.addWidget(self.layer_combo, 1, 1)

        self.show_all_layers_btn = QPushButton("Show All")
        viz_layout.addWidget(self.show_all_layers_btn, 1, 2)

        self.edit_gcode_button = QPushButton("✏️ Edit G-code")
        viz_layout.addWidget(self.edit_gcode_button, 1, 3)

        viz_layout.setColumnStretch(1, 1)
        parent_layout.addWidget(viz_group)

