"""G-code Previewer Widget - Main UI for CNC toolpath visualization."""

# pylint: disable=too-many-lines

from typing import Optional, Dict, Any
from pathlib import Path
import json
import os
import sqlite3

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStackedLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QSplitter,
    QProgressBar,
    QComboBox,
    QMessageBox,
    QCheckBox,
)
from PySide6.QtCore import Qt, Signal, QThread

from src.core.logging_config import get_logger
from src.core.database_manager import get_database_manager
from src.core.services.tab_data_manager import TabDataManager
from src.core.kinematics.gcode_timing import analyze_gcode_moves
from src.gui.widgets.add_tool_dialog import AddToolDialog
from .gcode_parser import GcodeParser
from .gcode_renderer import GcodeRenderer
from .vtk_widget import VTKWidget
from .animation_controller import AnimationController, PlaybackState
from .layer_analyzer import LayerAnalyzer
from .feed_speed_visualizer import FeedSpeedVisualizer
from .gcode_editor import GcodeEditorWidget
from .gcode_loader_thread import GcodeLoaderThread
from .gcode_timeline import GcodeTimeline
from .gcode_interactive_loader import InteractiveGcodeLoader
from .gcode_tools_widget import GcodeToolsWidget


MAX_GCODE_FILE_SIZE_BYTES = 500 * 1024 * 1024  # 500MB
MAX_EDITOR_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10MB


class GcodeToolsPanelContainer(QWidget):
    """Container for the right-hand tools panel.

    This lets us "hide" the tools content without removing the splitter
    widget itself, which avoids jumpy splitter snapping when the tools
    are toggled on and off.
    """

    def __init__(self, tools_widget: QWidget, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._tools_widget = tools_widget
        self._empty_widget = QWidget(self)

        self._stack = QStackedLayout(self)
        self._stack.addWidget(self._tools_widget)
        self._stack.addWidget(self._empty_widget)
        self._stack.setCurrentWidget(self._tools_widget)

    def set_tools_visible(self, visible: bool) -> None:
        self._stack.setCurrentWidget(self._tools_widget if visible else self._empty_widget)


class GcodeTimingThread(QThread):
    """Background worker that computes aggregate timing for a set of moves.

    This runs a single pass of ``analyze_gcode_moves`` off the GUI thread and
    returns the aggregated metrics as a plain dictionary.
    """

    finished = Signal(dict)
    error_occurred = Signal(str)

    def __init__(
        self,
        moves: list,
        *,
        max_feed_mm_min: float,
        accel_mm_s2: float,
        feed_override_pct: float,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        # Copy the moves list so that subsequent UI actions (such as clearing
        # or reloading) do not race with the timing computation.
        self._moves = list(moves)
        self._max_feed_mm_min = float(max_feed_mm_min)
        self._accel_mm_s2 = float(accel_mm_s2)
        self._feed_override_pct = float(feed_override_pct)
        self._logger = get_logger(__name__)

    def run(self) -> None:  # pragma: no cover - UI thread helper
        try:
            timing = analyze_gcode_moves(
                self._moves,
                max_feed_mm_min=self._max_feed_mm_min,
                accel_mm_s2=self._accel_mm_s2,
                feed_override_pct=self._feed_override_pct,
            )
            self.finished.emit(timing)
        except (ValueError, ZeroDivisionError, OverflowError, TypeError) as exc:
            # Numerical or data-related issues in timing analysis: log and report
            # to the UI so the user can adjust machine parameters or toolpath.
            self._logger.warning("Timing computation failed: %s", exc)
            self.error_occurred.emit(str(exc))


class GcodePreviewerWidget(QWidget):
    """Main widget for G-code preview and visualization."""

    gcode_loaded = Signal(str)  # Emits filepath when G-code is loaded

    def __init__(self, parent: Optional[QWidget] = None, use_external_tools: bool = False) -> None:
        """Initialize the G-code previewer widget.

        Args:
            parent: Optional parent widget.
            use_external_tools: When True, the right-hand tools panel lives
                in its own dock widget. In that mode this widget only
                creates the VTK viewer and expects ``attach_tools_widget``
                to be called later to wire up the tools side.
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)

        self.use_external_tools = use_external_tools

        # Database access for machine configuration and project-level
        # settings such as feed override.
        self.db_manager = get_database_manager()
        self.tab_data_manager = TabDataManager(self.db_manager)

        self.parser = GcodeParser()
        self.renderer = None  # Defer VTK initialization
        self.animation_controller = AnimationController()
        self.layer_analyzer = LayerAnalyzer()
        self.feed_speed_visualizer = FeedSpeedVisualizer()
        self.loader_thread: Optional[GcodeLoaderThread] = None

        # New VTK viewer components
        self.timeline: Optional[GcodeTimeline] = None
        self.interactive_loader: Optional[InteractiveGcodeLoader] = None
        self.editor: Optional[GcodeEditorWidget] = None
        self.vtk_widget: Optional[VTKWidget] = None

        # Tools-side widgets; these may be created internally or provided
        # externally when the tools live in their own dock widget.
        self.tools_widget: Optional[GcodeToolsWidget] = None
        self.tools_panel_container: Optional[GcodeToolsPanelContainer] = None
        self.stats_label: Optional[QLabel] = None
        self.moves_table: Optional[QTableWidget] = None
        # Per-path tool selection UI (lives in the Statistics tab of the tools widget)
        self.tool_label: Optional[QLabel] = None
        self.select_tool_button: Optional[QPushButton] = None
        self.viz_mode_combo: Optional[QComboBox] = None
        self.camera_controls_checkbox: Optional[QCheckBox] = None
        self.layer_combo: Optional[QComboBox] = None
        self.show_all_layers_btn: Optional[QPushButton] = None
        self.progress_bar: Optional[QProgressBar] = None

        self.current_file: Optional[str] = None
        self.moves = []
        self.current_layer = 0
        self.visualization_mode = "default"  # "default", "feed_rate", "spindle_speed"
        self.total_file_lines = 0
        self.current_project_id: Optional[str] = None

        # Background timing worker and cached timing for the currently
        # loaded toolpath.
        self.timing_thread: Optional[GcodeTimingThread] = None
        self.current_timing: Optional[Dict[str, float]] = None

        # Optional links into the G-code operations/versions tables so that
        # timing results can be cached per-project and per-file.
        self.current_operation_id: Optional[str] = None
        self.current_version_id: Optional[int] = None

        self._init_ui()
        self._connect_signals()
        self.logger.info("G-code Previewer Widget initialized")

    def set_current_project(self, project_id: str) -> None:
        """Attach a project to the previewer for machine-aware timing.

        The project identifier is used to resolve the active machine and
        feed override when computing cutting-time estimates for the
        currently loaded toolpath.
        """
        self.current_project_id = project_id

        # If a file is already loaded, refresh statistics so that the
        # timing summary reflects the newly selected project.
        if self.moves:
            self._update_statistics(include_timing=True)

    def save_to_project(self) -> None:
        """Save G-code timing summary and tool selection to the current project."""
        if not self.current_project_id:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        if not self.current_file:
            QMessageBox.warning(self, "No G-code Loaded", "Load a G-code file before saving.")
            return

        if not self.current_timing:
            QMessageBox.warning(
                self,
                "No Timing Data",
                "No timing results are available yet. Run a timing analysis before saving.",
            )
            return

        timing_summary = {
            "total_time_seconds": self.current_timing.get("total_time_seconds"),
            "cutting_time_seconds": self.current_timing.get("cutting_time_seconds"),
            "rapid_time_seconds": self.current_timing.get("rapid_time_seconds"),
        }

        tool_label_text = ""
        if self.tool_label is not None:
            tool_label_text = self.tool_label.text()

        # Persist only the timing summary and tool label per requirements
        payload: Dict[str, Any] = {
            "timing": timing_summary,
            "tool_label": tool_label_text,
        }

        success, message = self.tab_data_manager.save_tab_data_to_project(
            project_id=self.current_project_id,
            tab_name="G Code Previewer",
            data=payload,
            filename="gcode_timing.json",
            category="G-code Timing",
        )

        if success:
            QMessageBox.information(self, "Saved", message)
        else:
            QMessageBox.critical(self, "Error", message)

    def _init_ui(self) -> None:
        """Initialize the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # If the tools live in their own dock widget, only create the VTK
        # viewer here and let the main window own the tools side.
        if self.use_external_tools:
            try:
                if self.renderer is None:
                    self.renderer = GcodeRenderer()

                self.vtk_widget = VTKWidget(self.renderer)
                layout.addWidget(self.vtk_widget)
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                self.logger.error("Failed to initialize VTK viewer: %s", e)
                placeholder = QLabel("VTK Viewer unavailable")
                layout.addWidget(placeholder)

            return

        # Default embedded layout: splitter with 3D view and right-hand tools panel
        self.splitter = QSplitter(Qt.Horizontal)

        # Initialize VTK renderer lazily
        try:
            if self.renderer is None:
                self.renderer = GcodeRenderer()

            # 3D VTK viewer
            self.vtk_widget = VTKWidget(self.renderer)
            self.splitter.addWidget(self.vtk_widget)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to initialize VTK viewer: %s", e)
            # Create a placeholder label
            placeholder = QLabel("VTK Viewer unavailable")
            self.splitter.addWidget(placeholder)

        # Right panel: dedicated tools widget (timeline, loader, stats, editor, viz controls)
        self.tools_widget = GcodeToolsWidget(self.renderer, self)

        # Expose key child widgets so existing logic can continue to use
        # self.timeline, self.interactive_loader, etc. without major refactors.
        self.timeline = self.tools_widget.timeline
        self.interactive_loader = self.tools_widget.interactive_loader
        self.editor = self.tools_widget.editor
        self.progress_bar = self.tools_widget.progress_bar
        self.stats_label = self.tools_widget.stats_label
        self.moves_table = self.tools_widget.moves_table
        # Per-path tool selection UI
        self.tool_label = self.tools_widget.tool_label
        self.select_tool_button = self.tools_widget.select_tool_button
        self.viz_mode_combo = self.tools_widget.viz_mode_combo
        self.camera_controls_checkbox = self.tools_widget.camera_controls_checkbox
        self.layer_combo = self.tools_widget.layer_combo
        self.show_all_layers_btn = self.tools_widget.show_all_layers_btn

        # Wrap the tools widget in a dedicated container so that we can switch
        # between the real tools UI and an empty page without removing the
        # splitter widget itself. This avoids jumpy snapping when the tools
        # are toggled.
        self.tools_panel_container = GcodeToolsPanelContainer(self.tools_widget)
        self.splitter.addWidget(self.tools_panel_container)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 1)
        # Let Qt distribute initial sizes based on stretch factors so the VTK viewer
        # naturally starts wider than the tools panel without forcing pixel sizes.
        layout.addWidget(self.splitter)

    def attach_tools_widget(self, tools_widget: GcodeToolsWidget) -> None:
        """Attach an externally created tools widget.

        This is used when the tools live in a separate dock widget owned by
        the main window. It updates our references and connects all relevant
        signals so the rest of the previewer can interact with the tools
        in exactly the same way as when they are embedded.
        """
        self.tools_widget = tools_widget

        # Expose key child widgets for the rest of the class.
        self.timeline = tools_widget.timeline
        self.interactive_loader = tools_widget.interactive_loader
        self.editor = tools_widget.editor
        self.progress_bar = tools_widget.progress_bar
        self.stats_label = tools_widget.stats_label
        self.moves_table = tools_widget.moves_table
        # Per-path tool selection UI
        self.tool_label = tools_widget.tool_label
        self.select_tool_button = tools_widget.select_tool_button
        self.viz_mode_combo = tools_widget.viz_mode_combo
        self.camera_controls_checkbox = tools_widget.camera_controls_checkbox
        self.layer_combo = tools_widget.layer_combo
        self.show_all_layers_btn = tools_widget.show_all_layers_btn

        # Now that tools widgets are available, wire up their signals.
        self._connect_tools_signals()

    def _on_camera_controls_toggled(self, checked: bool) -> None:
        """Show or hide the camera toolbar in the VTK viewer."""
        if self.vtk_widget is not None:
            self.vtk_widget.set_toolbar_visible(checked)

    def _connect_signals(self) -> None:
        """Connect animation controller and core UI signals."""
        self.animation_controller.frame_changed.connect(self._on_animation_frame_changed)
        self.animation_controller.state_changed.connect(self._on_animation_state_changed)

        # Ensure initial camera controls visibility matches checkbox state
        if self.vtk_widget is not None:
            self.vtk_widget.set_toolbar_visible(True)

        # Connect signals for timeline/loader/editor/controls if they are
        # available. When the tools live in an external dock, this method is
        # called once during construction and then ``_connect_tools_signals``
        # is invoked again from ``attach_tools_widget`` after the dock widget
        # has been created.
        self._connect_tools_signals()

    def _connect_tools_signals(self) -> None:
        """Connect signals for the tools-side widgets.

        This is split out so that tools can be provided either by the
        embedded splitter layout or by an external dock widget.
        """
        # Connect timeline signals
        if self.timeline:
            self.timeline.frame_changed.connect(self._on_timeline_frame_changed)
            self.timeline.playback_requested.connect(self._on_timeline_playback_requested)
            self.timeline.pause_requested.connect(self._on_timeline_pause_requested)
            self.timeline.stop_requested.connect(self._on_timeline_stop_requested)
            self.timeline.speed_spinbox.valueChanged.connect(self._on_speed_changed)

        # Connect interactive loader signals
        if self.interactive_loader:
            # The Load G-code button in the right-hand loader panel should behave
            # like the main "Load" action and use the central validation logic.
            self.interactive_loader.load_button.clicked.connect(self._on_load_file)
            self.interactive_loader.loading_complete.connect(self._on_interactive_loader_complete)
            self.interactive_loader.chunk_loaded.connect(self._on_interactive_loader_chunk_loaded)
            self.interactive_loader.progress_updated.connect(self._on_loader_progress_updated)
            self.interactive_loader.error_occurred.connect(self._on_loader_error)

        # Connect editor signals
        if self.editor:
            self.editor.reload_requested.connect(self._on_gcode_reload)

        # Connect visualization controls
        if self.viz_mode_combo is not None:
            self.viz_mode_combo.currentTextChanged.connect(self._on_viz_mode_changed)

        if self.camera_controls_checkbox is not None:
            self.camera_controls_checkbox.toggled.connect(self._on_camera_controls_toggled)

        if self.layer_combo is not None:
            self.layer_combo.currentIndexChanged.connect(self._on_layer_changed)

        if self.show_all_layers_btn is not None:
            self.show_all_layers_btn.clicked.connect(self._on_show_all_layers)

        # Per-path tool selection
        if self.select_tool_button is not None:
            self.select_tool_button.clicked.connect(self._on_select_tool_for_current_path)

        if getattr(self, "tools_widget", None) is not None and getattr(
            self.tools_widget, "edit_gcode_button", None
        ):
            self.tools_widget.edit_gcode_button.clicked.connect(self._on_edit_gcode)

    def _on_loader_progress_updated(self, progress: int, message: str) -> None:
        """Update the tools-panel progress bar and status message during load."""
        if self.progress_bar is not None:
            self.progress_bar.setMaximum(100)
            if not self.progress_bar.isVisible():
                self.progress_bar.setVisible(True)
            self.progress_bar.setValue(progress)
        # Keep the main window status bar in sync with loader status text.
        self._show_status_message(message)

    def _on_loader_error(self, message: str) -> None:
        """Handle loader errors and reset the tools-panel progress UI."""
        if self.progress_bar is not None:
            self.progress_bar.setVisible(False)
        self._show_status_message(f"G-code load error: {message}", 5000)

    def _show_status_message(self, message: str, timeout_ms: int = 0) -> None:
        """Show a message in the main window status bar, if available.

        This keeps transient loading/status text in the bottom status bar instead
        of the top info strip, which is reserved for stable file context.
        """
        try:
            window = self.window()
            if window is not None and hasattr(window, "statusBar"):
                status_bar = window.statusBar()
                if status_bar is not None:
                    status_bar.showMessage(message, timeout_ms)
        except (RuntimeError, AttributeError):
            # Never allow status-bar issues (e.g. window already deleted) to break the previewer
            self.logger.debug(
                "Failed to show status message in main window status bar",
                exc_info=True,
            )

    def _on_select_tool_for_current_path(self) -> None:
        """Allow the user to pick a tool for the currently loaded G-code.

        The selected tool is persisted against the current G-code version so it
        can be restored when the file is re-opened.
        """
        if self.current_file is None:
            QMessageBox.information(
                self,
                "No G-code Loaded",
                "Load a G-code file before selecting a tool.",
            )
            return

        if self.db_manager is None or not self.current_project_id:
            QMessageBox.information(
                self,
                "No Project Selected",
                "Select a project in the main window before attaching a tool.",
            )
            return

        # Make sure we have an operation/version pair to attach the tool to.
        self._ensure_gcode_version_for_current_file()
        if self.current_version_id is None:
            QMessageBox.warning(
                self,
                "Tool Selection Unavailable",
                "Could not prepare a database record for this G-code file.",
            )
            return

        # Reuse the existing AddToolDialog so the same tool libraries and
        # personal toolbox are available here.
        tools_db_path = Path.home() / ".digital_workshop" / "tools.db"
        dialog = AddToolDialog(str(tools_db_path), self)
        if dialog.exec() != dialog.Accepted:
            return

        tool_data = dialog.get_selected_tool()
        if not tool_data:
            return

        # Normalise fields used by the label and snapshot.
        if "vendor" not in tool_data and tool_data.get("provider_name"):
            tool_data["vendor"] = tool_data["provider_name"]

        self._update_tool_label(tool_data)
        self._persist_tool_snapshot_for_current_version(tool_data)

    def _on_load_file(self) -> None:
        """Handle load file button click with security validation."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open G-code File",
            "",
            "G-code Files (*.nc *.gcode *.gco *.tap);;All Files (*)",
        )

        if filepath:
            # Validate and sanitize path
            validated_path = self._validate_file_path(filepath)
            if validated_path:
                self.load_gcode_file(validated_path)

    def _validate_file_path(self, filepath: str) -> Optional[str]:
        """Validate file path for security and accessibility.

        Args:
            filepath: Path to validate.

        Returns:
            Validated absolute path or ``None`` if invalid.
        """
        try:
            # Convert to Path object for safe manipulation
            file_path = Path(filepath).resolve()

            # Check file exists
            if not file_path.exists():
                self.logger.error("File does not exist: %s", filepath)
                QMessageBox.warning(self, "Invalid File", "File does not exist.")
                return None

            # Check it's a file (not a directory)
            if not file_path.is_file():
                self.logger.error("Path is not a file: %s", filepath)
                QMessageBox.warning(self, "Invalid File", "Path must be a file.")
                return None

            # Check file is readable
            if not os.access(file_path, os.R_OK):
                self.logger.error("File not readable: %s", filepath)
                QMessageBox.warning(self, "Access Denied", "Cannot read file.")
                return None

            user_cancelled = False

            # Validate file extension
            valid_extensions = {".nc", ".gcode", ".gco", ".tap", ".txt"}
            if file_path.suffix.lower() not in valid_extensions:
                self.logger.warning("Unusual file extension: %s", file_path.suffix)
                reply = QMessageBox.question(
                    self,
                    "Unusual Extension",
                    f"File has unusual extension '{file_path.suffix}'. Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    user_cancelled = True

            if not user_cancelled:
                # Check file size (warn for very large files)
                file_size = file_path.stat().st_size

                if file_size > MAX_GCODE_FILE_SIZE_BYTES:
                    self.logger.warning("Very large file: %s bytes", file_size)
                    reply = QMessageBox.question(
                        self,
                        "Large File",
                        f"File is {file_size / (1024*1024):.1f}MB. "
                        "This may take a while to load. Continue?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply != QMessageBox.Yes:
                        user_cancelled = True

            if user_cancelled:
                return None

            return str(file_path)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Path validation failed: %s", e)
            QMessageBox.critical(
                self, "Validation Error", f"Failed to validate file path: {str(e)}"
            )
            return None

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

            # Update UI - transient "Loading" message goes to the main status bar
            info_text = f"Loading G-code: {file_path.name} ({file_size_mb:.1f}MB)..."
            self._show_status_message(info_text)

            self.current_file = validated_path
            self.moves = []

            # Clear renderer (quick operation)
            self.renderer.clear_incremental()
            self.vtk_widget.update_render()

            # Start background loading
            if self.interactive_loader:
                self.interactive_loader.load_file(validated_path)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to start loading: %s", e)
            self._show_status_message(f"Error starting load: {e}", 5000)
            self.progress_bar.setVisible(False)

    def _compute_file_fingerprint(self) -> str:
        """Return a lightweight fingerprint for the currently loaded file.

        We deliberately avoid hashing the full contents and instead combine
        modification time and size. This is fast, stable, and sufficient for
        deciding when cached timing metrics are stale.
        """
        if not self.current_file:
            return ""

        try:
            file_path = Path(self.current_file)
            stat_result = file_path.stat()
        except (OSError, IOError):  # pragma: no cover - defensive
            return ""

        return f"{stat_result.st_mtime_ns}:{stat_result.st_size}"

    def _resolve_machine_and_override(self):
        """Resolve machine kinematics and feed override for the current project.

        Returns a tuple ``(machine, feed_override_pct)`` where ``machine`` is a
        mapping with at least ``max_feed_mm_min`` and ``accel_mm_s2`` keys, or
        ``None`` if no machine configuration is available.
        """
        if self.db_manager is None:
            return None, 100.0

        machine = None
        feed_override_pct = 100.0

        # Prefer the project-specific configuration when a project is attached
        # to the previewer.
        if self.current_project_id:
            try:
                machine_id = self.db_manager.get_project_active_machine(self.current_project_id)
            except (sqlite3.Error, OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:  # pragma: no cover - defensive
                self.logger.warning(
                    "Failed to get active machine for project %s: %s",
                    self.current_project_id,
                    exc,
                )
                machine_id = None

            if machine_id is not None:
                try:
                    machine = self.db_manager.get_machine(machine_id)
                except (sqlite3.Error, OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:  # pragma: no cover - defensive
                    self.logger.warning("Failed to load machine %s: %s", machine_id, exc)
                    machine = None

            try:
                feed_override_pct = float(
                    self.db_manager.get_project_feed_override(self.current_project_id)
                )
            except (sqlite3.Error, OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:  # pragma: no cover - defensive
                self.logger.warning(
                    "Failed to get feed override for project %s: %s",
                    self.current_project_id,
                    exc,
                )

        # Fall back to the default machine when none is configured for this
        # project.
        if machine is None:
            try:
                machine = self.db_manager.get_default_machine()
            except (sqlite3.Error, OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:  # pragma: no cover - defensive
                self.logger.warning("Failed to get default machine: %s", exc)
                machine = None

        if machine is None:
            return None, feed_override_pct

        try:
            max_feed_mm_min = float(machine.get("max_feed_mm_min", 600.0))
        except (TypeError, ValueError):  # pragma: no cover - defensive
            max_feed_mm_min = 600.0

        try:
            accel_mm_s2 = float(machine.get("accel_mm_s2", 100.0))
        except (TypeError, ValueError):  # pragma: no cover - defensive
            accel_mm_s2 = 100.0

        return {"max_feed_mm_min": max_feed_mm_min, "accel_mm_s2": accel_mm_s2}, feed_override_pct

    def _ensure_gcode_version_for_current_file(self) -> None:
        """Ensure there is an operation/version row for the current file.

        On success, ``current_operation_id`` and ``current_version_id`` are
        populated. On failure, the method logs and leaves them as ``None``.
        """
        # Reset any previously associated identifiers; these belong to the
        # currently loaded file only.
        self.current_operation_id = None
        self.current_version_id = None

        if self.db_manager is None or not self.current_project_id or not self.current_file:
            return

        file_path_str = str(self.current_file)

        # First, try to find an existing version whose file_path matches the
        # current file.
        try:
            operations = self.db_manager.list_gcode_operations(project_id=self.current_project_id)
        except (sqlite3.Error, OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:  # pragma: no cover - defensive
            self.logger.warning(
                "Failed to list G-code operations for project %s: %s",
                self.current_project_id,
                exc,
            )
            return

        for op in operations:
            op_id = op.get("id")
            if not op_id:
                continue

            try:
                versions = self.db_manager.list_gcode_versions(op_id)
            except (sqlite3.Error, OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:  # pragma: no cover - defensive
                self.logger.warning(
                    "Failed to list G-code versions for operation %s: %s",
                    op_id,
                    exc,
                )
                continue

            for version in versions:
                if version.get("file_path") == file_path_str:
                    self.current_operation_id = op_id
                    try:
                        self.current_version_id = int(version["id"])
                    except (KeyError, TypeError, ValueError):  # pragma: no cover - defensive
                        self.current_version_id = None
                    break

            if self.current_version_id is not None:
                break

        # If there is no existing version, create a minimal operation/version
        # pair so that timing metrics can be cached.
        if self.current_operation_id is None:
            try:
                op_name = Path(file_path_str).name
            except (TypeError, ValueError):  # pragma: no cover - defensive
                op_name = file_path_str

            try:
                self.current_operation_id = self.db_manager.create_gcode_operation(
                    project_id=self.current_project_id,
                    name=op_name,
                    status="draft",
                    notes="Auto-created by G-code Previewer",
                )
            except (sqlite3.Error, OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:  # pragma: no cover - defensive
                self.logger.warning(
                    "Failed to create G-code operation for project %s: %s",
                    self.current_project_id,
                    exc,
                )
                self.current_operation_id = None
                return

        if self.current_version_id is None:
            try:
                version_id = self.db_manager.create_gcode_version(
                    operation_id=self.current_operation_id,
                    file_path=file_path_str,
                    file_hash=self._compute_file_fingerprint(),
                    status="draft",
                )
                self.current_version_id = version_id
            except (sqlite3.Error, OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:  # pragma: no cover - defensive
                self.logger.warning(
                    "Failed to create G-code version for operation %s: %s",
                    self.current_operation_id,
                    exc,
                )
                self.current_version_id = None

    def _update_tool_label(self, tool_data: Dict[str, Any]) -> None:
        """Update the per-path tool label in the tools panel.

        The label is intentionally compact so it works both when the tools
        panel is docked and when it is floating.
        """
        if self.tool_label is None:
            return

        description = tool_data.get("description") or "Tool selected"
        diameter = tool_data.get("diameter")
        unit = (tool_data.get("unit") or "").strip()
        vendor = tool_data.get("vendor") or tool_data.get("provider_name")

        parts = [str(description)]

        try:
            if isinstance(diameter, (int, float)):
                diameter_value = float(diameter)
                if diameter_value > 0:
                    dim_text = f"Ø {diameter_value:.3f}"
                    if unit:
                        dim_text += f" {unit}"
                    parts.append(dim_text)
        except (TypeError, ValueError):  # pragma: no cover - defensive
            # If diameter is not numeric, we simply omit it from the label.
            pass

        if vendor:
            parts.append(str(vendor))

        self.tool_label.setText(" - ".join(parts))

    def _refresh_tool_label_for_current_version(self) -> None:
        """Refresh tool label from any persisted snapshot for current version."""
        if self.tool_label is None:
            return

        if self.db_manager is None or self.current_version_id is None:
            self.tool_label.setText("No tool selected")
            return

        try:
            snapshots = self.db_manager.list_gcode_tool_snapshots(self.current_version_id)
        except (sqlite3.Error, OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:  # pragma: no cover - defensive
            self.logger.warning(
                "Failed to list tool snapshots for version %s: %s",
                self.current_version_id,
                exc,
            )
            self.tool_label.setText("No tool selected")
            return

        if not snapshots:
            self.tool_label.setText("No tool selected")
            return

        snapshot = snapshots[0]
        metadata_raw = snapshot.get("metadata_json") or snapshot.get("metadata")
        tool_data: Dict[str, Any] = {}

        if metadata_raw:
            try:
                if isinstance(metadata_raw, str):
                    tool_data = json.loads(metadata_raw)
                elif isinstance(metadata_raw, dict):
                    tool_data = metadata_raw
            except (json.JSONDecodeError, TypeError, ValueError) as exc:  # pragma: no cover - defensive
                self.logger.warning(
                    "Failed to parse tool snapshot metadata for version %s: %s",
                    self.current_version_id,
                    exc,
                )

        if not tool_data:
            tool_data = {
                "description": snapshot.get("notes") or "Tool selected",
                "vendor": snapshot.get("provider_name"),
            }

        self._update_tool_label(tool_data)

    def _persist_tool_snapshot_for_current_version(self, tool_data: Dict[str, Any]) -> None:
        """Persist selected tool metadata for the current version.

        The full tool data dictionary is stored as JSON in the metadata field so
        it can evolve without requiring schema changes.
        """
        if self.db_manager is None or self.current_version_id is None:
            return

        try:
            # Clear any previous tool snapshots for this version so we keep one
            # current selection.
            self.db_manager.delete_gcode_tool_snapshots(self.current_version_id)
        except (sqlite3.Error, OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:  # pragma: no cover - defensive
            self.logger.warning(
                "Failed to clear existing tool snapshots for version %s: %s",
                self.current_version_id,
                exc,
            )

        try:
            metadata = dict(tool_data)
            self.db_manager.add_gcode_tool_snapshot(
                version_id=self.current_version_id,
                tool_number=None,
                tool_id=tool_data.get("id"),
                provider_name=tool_data.get("vendor") or tool_data.get("provider_name"),
                tool_db_source=tool_data.get("tool_db_source", "tool_database"),
                feed_rate=None,
                plunge_rate=None,
                spindle_speed=None,
                stepdown=None,
                stepover=None,
                notes=tool_data.get("description"),
                metadata=metadata,
            )
        except (sqlite3.Error, OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:  # pragma: no cover - defensive
            self.logger.warning(
                "Failed to persist tool snapshot for version %s: %s",
                self.current_version_id,
                exc,
            )

    def _load_cached_timing_if_available(self) -> bool:
        """Load cached timing metrics from the database when still valid.

        Returns True when ``current_timing`` was populated from cache.
        """
        if self.db_manager is None or self.current_version_id is None or not self.current_file:
            return False

        try:
            metrics = self.db_manager.get_gcode_metrics(self.current_version_id)
        except (sqlite3.Error, OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:  # pragma: no cover - defensive
            self.logger.warning(
                "Failed to load cached metrics for version %s: %s",
                self.current_version_id,
                exc,
            )
            return False

        if not metrics:
            return False

        # Ensure that the cached metrics were computed for the same machine
        # and feed override that are currently configured for this project.
        machine, feed_override_pct = self._resolve_machine_and_override()
        current_machine_id = machine.get("id") if machine is not None else None

        fingerprint = self._compute_file_fingerprint()
        if not fingerprint:
            return False

        try:
            version_row = self.db_manager.get_gcode_version(self.current_version_id)
        except (sqlite3.Error, OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:  # pragma: no cover - defensive
            self.logger.warning(
                "Failed to load version %s when validating metrics: %s",
                self.current_version_id,
                exc,
            )
            return False

        if not version_row:
            return False

        stored_hash = str(version_row.get("file_hash") or "").strip()
        if stored_hash != fingerprint:
            self.logger.info(
                "Ignoring cached timing for version %s because file hash changed",
                self.current_version_id,
            )
            return False

        stored_machine_id = metrics.get("machine_id")
        stored_override = metrics.get("feed_override_pct")

        if stored_machine_id is not None and current_machine_id is not None:
            try:
                stored_machine_id_int = int(stored_machine_id)
            except (TypeError, ValueError):  # pragma: no cover - defensive
                stored_machine_id_int = None
            if stored_machine_id_int is not None and stored_machine_id_int != current_machine_id:
                self.logger.info(
                    "Ignoring cached timing for version %s because machine changed",
                    self.current_version_id,
                )
                return False

        if stored_override is not None:
            try:
                stored_override_val = float(stored_override)
            except (TypeError, ValueError):  # pragma: no cover - defensive
                stored_override_val = None
            if (
                stored_override_val is not None
                and abs(stored_override_val - feed_override_pct) > 1e-3
            ):
                self.logger.info(
                    "Ignoring cached timing for version %s because feed override changed",
                    self.current_version_id,
                )
                return False

        timing_keys = (
            "total_time_seconds",
            "cutting_time_seconds",
            "rapid_time_seconds",
            "distance_cut",
            "distance_rapid",
            "best_case_time_seconds",
            "time_correction_factor",
        )
        timing: Dict[str, float] = {}
        for key in timing_keys:
            value = metrics.get(key)
            if value is None:
                continue
            try:
                timing[key] = float(value)
            except (TypeError, ValueError):  # pragma: no cover - defensive
                continue

        if not timing:
            return False

        self.current_timing = timing
        self.logger.info(
            "Loaded cached timing for version %s (k=%.3f)",
            self.current_version_id,
            timing.get("time_correction_factor", 1.0),
        )
        return True

    def _start_timing_job(self) -> None:
        """Kick off a background timing computation for the current moves."""
        if not self.moves:
            return

        machine, feed_override_pct = self._resolve_machine_and_override()
        if machine is None:
            # No machine configured; we still keep geometric statistics.
            return

        worker = GcodeTimingThread(
            self.moves,
            max_feed_mm_min=machine["max_feed_mm_min"],
            accel_mm_s2=machine["accel_mm_s2"],
            feed_override_pct=feed_override_pct,
            parent=self,
        )
        worker.finished.connect(self._on_timing_finished)
        worker.error_occurred.connect(self._on_timing_error)
        self.timing_thread = worker
        worker.start()

    def _on_timing_finished(self, timing: Dict[str, float]) -> None:
        """Handle completion of the background timing computation."""
        sender = self.sender()
        if sender is not None and sender is not self.timing_thread:
            # Result from an obsolete worker; ignore it.
            return

        self.timing_thread = None
        self.current_timing = timing

        if self.db_manager is not None and self.current_version_id is not None:
            try:
                machine, feed_override_pct = self._resolve_machine_and_override()
                machine_id = machine.get("id") if machine is not None else None

                metrics_payload: Dict[str, Any] = dict(timing)
                metrics_payload.update(
                    machine_id=machine_id,
                    feed_override_pct=feed_override_pct,
                )

                self.db_manager.upsert_gcode_metrics(self.current_version_id, **metrics_payload)
                fingerprint = self._compute_file_fingerprint()
                if fingerprint:
                    self.db_manager.update_gcode_version(
                        self.current_version_id,
                        file_hash=fingerprint,
                    )
            except (sqlite3.Error, OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:  # pragma: no cover - defensive
                self.logger.warning(
                    "Failed to persist timing metrics for version %s: %s",
                    self.current_version_id,
                    exc,
                )

        self._update_statistics(include_timing=True)
        self._show_status_message("Cutting-time estimate updated", 3000)

    def _on_timing_error(self, message: str) -> None:
        """Handle timing worker errors without disrupting the UI."""
        sender = self.sender()
        if sender is not None and sender is not self.timing_thread:
            return

        self.timing_thread = None
        self.logger.warning("Timing worker reported an error: %s", message)
        self._show_status_message(f"Timing calculation failed: {message}", 5000)

    def _update_statistics(self, include_timing: bool = False) -> None:
        """Update statistics display.

        Geometric statistics are always shown. When ``include_timing`` is
        True and ``current_timing`` is populated, a timing summary based on
        the most recent background calculation or cached metrics is appended.
        """
        stats = self.parser.get_statistics()
        bounds = stats["bounds"]

        stats_text = (
            "<b>Toolpath Statistics</b><br>"
            f"Total Moves: {stats['total_moves']}<br>"
            f"Rapid Moves: {stats['rapid_moves']}<br>"
            f"Cutting Moves: {stats['cutting_moves']}<br>"
            f"Arc Moves: {stats['arc_moves']}<br>"
            "<br>"
            "<b>Bounds</b><br>"
            f"X: {bounds['min_x']:.2f} to {bounds['max_x']:.2f}<br>"
            f"Y: {bounds['min_y']:.2f} to {bounds['max_y']:.2f}<br>"
            f"Z: {bounds['min_z']:.2f} to {bounds['max_z']:.2f}"
        )

        timing = self.current_timing if include_timing and self.current_timing else None

        if timing:
            try:
                stats_text += (
                    "<br><br>"
                    "<b>Path Length</b><br>"
                    f"Cutting: {timing['distance_cut']:.2f} mm<br>"
                    f"Rapid: {timing['distance_rapid']:.2f} mm<br>"
                    "<br>"
                    "<b>Timing</b><br>"
                    f"Best-case (no accel): {self._format_duration(timing['best_case_time_seconds'])}<br>"
                    f"Kinematic (accel): {self._format_duration(timing['total_time_seconds'])}<br>"
                    f"Rapid time: {self._format_duration(timing['rapid_time_seconds'])}<br>"
                    f"Cutting time: {self._format_duration(timing['cutting_time_seconds'])}<br>"
                    f"Time correction factor k: {timing['time_correction_factor']:.3f}"
                )
            except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - defensive
                self.logger.warning("Failed to format timing summary: %s", exc)

        if self.stats_label is not None:
            self.stats_label.setText(stats_text)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format a duration in seconds as a compact H:MM:SS string.

        This keeps the statistics panel readable even for long jobs while
        still making it easy to compare best-case and kinematic times.
        """
        try:
            total_seconds = max(0, int(round(float(seconds))))
        except (TypeError, ValueError):  # pragma: no cover - defensive
            total_seconds = 0

        hours, remainder = divmod(total_seconds, 3600)
        minutes, secs = divmod(remainder, 60)

        if hours > 0:
            return f"{hours:d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:d}:{secs:02d}"

    def _update_moves_table(self) -> None:
        """Update moves table with first 50 moves."""
        self.moves_table.setRowCount(0)

        for move in self.moves[:50]:
            row = self.moves_table.rowCount()
            self.moves_table.insertRow(row)

            move_type = "Rapid" if move.is_rapid else "Cut" if move.is_cutting else "Arc"

            self.moves_table.setItem(row, 0, QTableWidgetItem(str(move.line_number)))
            self.moves_table.setItem(row, 1, QTableWidgetItem(move_type))
            self.moves_table.setItem(row, 2, QTableWidgetItem(f"{move.x:.2f}" if move.x else "-"))
            self.moves_table.setItem(row, 3, QTableWidgetItem(f"{move.y:.2f}" if move.y else "-"))
            self.moves_table.setItem(row, 4, QTableWidgetItem(f"{move.z:.2f}" if move.z else "-"))
            self.moves_table.setItem(
                row,
                5,
                QTableWidgetItem(f"{move.feed_rate:.1f}" if move.feed_rate else "-"),
            )
            self.moves_table.setItem(
                row,
                6,
                QTableWidgetItem(f"{move.spindle_speed:.0f}" if move.spindle_speed else "-"),
            )

    def _on_play(self) -> None:
        """Handle play button click."""
        self.animation_controller.play()

    def _on_pause(self) -> None:
        """Handle pause button click."""
        self.animation_controller.pause()

    def _on_stop(self) -> None:
        """Handle stop button click."""
        self.animation_controller.stop()

    def _on_speed_changed(self, value: int) -> None:
        """Handle speed change from the timeline control."""
        speed = value / 100.0
        self.animation_controller.set_speed(speed)

    def _on_animation_frame_changed(self, frame: int) -> None:
        """Handle animation frame change."""
        # Keep the timeline in sync with the animation controller
        if self.timeline:
            self.timeline.set_current_frame(frame)

        # Update visualization to show moves up to current frame
        moves_to_show = self.animation_controller.get_moves_up_to_frame(frame)
        self.renderer.render_toolpath(moves_to_show)
        self.vtk_widget.update_render()

    def _on_animation_state_changed(self, state: PlaybackState) -> None:
        """Handle animation state change and reflect it in the timeline UI."""
        is_playing = state == PlaybackState.PLAYING
        if self.timeline:
            self.timeline.is_playing = is_playing
            # When running, disable the Run Simulation button and enable Pause.
            # When paused or stopped, enable Run Simulation and disable Pause.
            self.timeline.play_button.setEnabled(not is_playing)
            self.timeline.pause_button.setEnabled(is_playing)

    def _on_viz_mode_changed(self, mode: str) -> None:
        """Handle visualization mode change."""
        if mode == "Feed Rate":
            actor = self.feed_speed_visualizer.create_feed_rate_visualization(self.moves)
            self.visualization_mode = "feed_rate"
        elif mode == "Spindle Speed":
            actor = self.feed_speed_visualizer.create_spindle_speed_visualization(self.moves)
            self.visualization_mode = "spindle_speed"
        else:
            self.renderer.render_toolpath(self.moves)
            self.visualization_mode = "default"
            self.vtk_widget.update_render()
            return

        # Replace actor in renderer
        self.renderer.renderer.RemoveAllViewProps()
        self.renderer.renderer.AddActor(actor)
        self.renderer.renderer.ResetCamera()
        self.vtk_widget.update_render()

    def _on_layer_changed(self, index: int) -> None:
        """Handle layer selection change."""
        if index < 0 or not self.layer_analyzer.get_layers():
            return

        layer = self.layer_analyzer.get_layers()[index]
        moves = self.layer_analyzer.get_moves_for_layer(layer.layer_number, self.moves)
        self.renderer.render_toolpath(moves)
        self.vtk_widget.update_render()

    def _on_show_all_layers(self) -> None:
        """Show all layers."""
        self.layer_combo.setCurrentIndex(-1)
        self.renderer.render_toolpath(self.moves)
        self.vtk_widget.update_render()

    def _on_edit_gcode(self) -> None:
        """Handle edit G-code with proper validation and limits."""
        if not self.current_file:
            self.logger.warning("No G-code file loaded")
            return

        try:
            # Validate file still exists
            if not os.path.exists(self.current_file):
                self.logger.error("File no longer exists: %s", self.current_file)
                QMessageBox.warning(self, "File Not Found", "The G-code file no longer exists.")
                return

            # Check file size (limit to 10MB for editor)
            file_size = os.path.getsize(self.current_file)

            if file_size > MAX_EDITOR_FILE_SIZE_BYTES:
                self.logger.warning("File too large for editor: %s bytes", file_size)
                reply = QMessageBox.question(
                    self,
                    "Large File",
                    f"File is {file_size / (1024*1024):.1f}MB. "
                    "Large files may be slow to edit. Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
                    return

            # Read file with proper error handling
            try:
                with open(self.current_file, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
            except (OSError, IOError) as e:
                self.logger.error("Failed to read file: %s", e)
                QMessageBox.critical(self, "Read Error", f"Failed to read file: {str(e)}")
                return

            # Create editor dialog
            editor_widget = GcodeEditorWidget()
            editor_widget.set_content(content)
            editor_widget.reload_requested.connect(self._on_gcode_reload)
            editor_widget.show()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to open editor: %s", e, exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to open editor: {str(e)}")

    def _on_gcode_reload(self, content: str) -> None:
        """Handle G-code reload from editor."""
        try:
            # Parse the edited content
            self.moves = self.parser.parse_lines(content.split("\n"))

            # Update animation controller
            self.animation_controller.set_moves(self.moves)

            # Update layer analyzer
            self.layer_analyzer.analyze(self.moves)
            self._update_layer_combo()

            # Re-render
            self.renderer.render_toolpath(self.moves)
            self.vtk_widget.update_render()

            # Reset timing and either use cache or kick off a new job.
            self.current_timing = None
            from_cache = False
            if self.db_manager is not None and self.current_project_id:
                self._ensure_gcode_version_for_current_file()
                # Editing the file typically invalidates the hash; this will
                # normally return False, but we keep the call for completeness.
                from_cache = self._load_cached_timing_if_available()

            self._update_statistics(include_timing=from_cache)
            self._update_moves_table()

            if not from_cache and self.db_manager is not None:
                self._start_timing_job()

            self.logger.info("G-code reloaded and re-rendered")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to reload G-code: %s", e)

    def _update_layer_combo(self) -> None:
        """Update layer combo box with detected layers."""
        self.layer_combo.blockSignals(True)
        self.layer_combo.clear()

        layers = self.layer_analyzer.get_layers()
        for layer in layers:
            self.layer_combo.addItem(f"Layer {layer.layer_number} (Z={layer.z_height:.2f})")

        self.layer_combo.blockSignals(False)

    def _on_loader_progress(self, current_line: int, total_lines: int) -> None:
        """Handle loader progress update."""
        if total_lines > 0:
            progress = int((current_line / total_lines) * 100)
            self.progress_bar.setValue(progress)

    def _on_moves_batch_loaded(self, moves: list) -> None:
        """Handle batch of moves loaded from background thread."""
        self.moves.extend(moves)

        # Add moves to renderer incrementally
        self.renderer.add_moves_incremental(moves)
        self.vtk_widget.update_render()

        # Update statistics
        self._update_statistics()

    def _on_loader_finished(self, all_moves: list) -> None:
        """Handle loader finished."""
        self.moves = all_moves

        # Initialize animation controller
        self.animation_controller.set_moves(self.moves)

        # Analyze layers
        self.layer_analyzer.analyze(self.moves)
        self._update_layer_combo()

        # Prepare DB linkage for timing cache if we have a project context.
        self.current_timing = None
        if self.db_manager is not None and self.current_project_id:
            self._ensure_gcode_version_for_current_file()
            # Refresh tool selection label from any stored snapshots for this version.
            self._refresh_tool_label_for_current_version()
            from_cache = self._load_cached_timing_if_available()
        else:
            from_cache = False
            # Without a project/version context we cannot persist tool selection.
            if self.tool_label is not None:
                self.tool_label.setText("No tool selected")

        # Update UI - detailed text in the status bar
        file_name = Path(self.current_file).name
        file_size_mb = Path(self.current_file).stat().st_size / (1024 * 1024)
        info_text = (
            f"Loaded G-code: {file_name} ({file_size_mb:.1f}MB, "
            f"{self.total_file_lines:,} lines, {len(self.moves):,} moves)"
        )
        self._show_status_message(info_text, 5000)

        # Update statistics; include timing only when we have cached results.
        self._update_statistics(include_timing=from_cache)

        # Kick off background timing computation when no valid cache exists.
        if not from_cache and self.db_manager is not None:
            self._start_timing_job()

        # Update moves table
        self._update_moves_table()

        # Add axes
        self.renderer.add_axes()
        self.renderer.reset_camera()
        self.vtk_widget.update_render()

        self.gcode_loaded.emit(self.current_file)
        self.logger.info("Finished loading G-code: %s moves", f"{len(self.moves):,}")
        self.progress_bar.setVisible(False)

    def _on_loader_error(self, error_msg: str) -> None:
        """Handle loader error."""
        self.logger.error("Loader error: %s", error_msg)
        self._show_status_message(f"G-code load error: {error_msg}", 5000)
        self.progress_bar.setVisible(False)

    def _on_timeline_frame_changed(self, frame_index: int) -> None:
        """Handle frame change from timeline."""
        if frame_index < len(self.moves):
            # Update animation controller
            self.animation_controller.set_frame(frame_index)

            self.logger.debug("Timeline frame changed to %s", frame_index)

    def _on_timeline_playback_requested(self) -> None:
        """Handle playback request from timeline."""
        self._on_play()

    def _on_timeline_pause_requested(self) -> None:
        """Handle pause request from timeline."""
        self._on_pause()

    def _on_timeline_stop_requested(self) -> None:
        """Handle stop request from timeline."""
        self._on_stop()

    def _on_interactive_loader_complete(self, all_moves: list) -> None:
        """Handle interactive loader completion."""
        self.moves = all_moves

        # Initialize animation controller
        self.animation_controller.set_moves(self.moves)

        # Update timeline
        if self.timeline:
            self.timeline.set_moves(self.moves)

        # Analyze layers
        self.layer_analyzer.analyze(self.moves)
        self._update_layer_combo()

        # Prepare DB linkage for timing cache and tool snapshots when we have
        # a project context.
        self.current_timing = None
        if self.db_manager is not None and self.current_project_id:
            self._ensure_gcode_version_for_current_file()
            self._refresh_tool_label_for_current_version()
            from_cache = self._load_cached_timing_if_available()
        else:
            from_cache = False
            if self.tool_label is not None:
                self.tool_label.setText("No tool selected")

        # Update statistics; include timing only when we have cached results.
        self._update_statistics(include_timing=from_cache)

        # Kick off background timing computation when no valid cache exists.
        if not from_cache and self.db_manager is not None:
            self._start_timing_job()

        # Update moves table
        self._update_moves_table()

        # Ensure final incremental actors are built before we adjust camera/axes
        self.renderer.update_incremental_actors()

        # Add axes and fit view
        self.renderer.add_axes()
        self.renderer.reset_camera()
        self.vtk_widget.update_render()

        if self.progress_bar is not None:
            self.progress_bar.setValue(100)
            self.progress_bar.setVisible(False)

        self._show_status_message("G-code load complete", 3000)

        self.gcode_loaded.emit(self.current_file)
        self.logger.info("Interactive loader finished: %s moves", f"{len(self.moves):,}")

    def _on_interactive_loader_chunk_loaded(self, chunk_moves: list) -> None:
        """Handle chunk loaded from interactive loader."""
        # Add moves to renderer incrementally
        self.renderer.add_moves_incremental(chunk_moves)
        self.vtk_widget.update_render()

        # Update statistics
        self._update_statistics()
