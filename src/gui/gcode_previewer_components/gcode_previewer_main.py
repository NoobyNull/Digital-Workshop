"""G-code Previewer Widget - Main UI for CNC toolpath visualization."""

from typing import Optional
from pathlib import Path
import os

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QStackedLayout,
    QPushButton,
    QLabel,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QSplitter,
    QProgressBar,
    QSlider,
    QSpinBox,
    QComboBox,
    QTabWidget,
    QMessageBox,
    QCheckBox,
)
from PySide6.QtCore import Qt, Signal

from src.core.logging_config import get_logger
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
        self.viz_mode_combo: Optional[QComboBox] = None
        self.camera_controls_checkbox: Optional[QCheckBox] = None
        self.layer_combo: Optional[QComboBox] = None
        self.show_all_layers_btn: Optional[QPushButton] = None
        self.progress_bar: Optional[QProgressBar] = None

        self.current_file = None
        self.moves = []
        self.current_layer = 0
        self.visualization_mode = "default"  # "default", "feed_rate", "spindle_speed"
        self.total_file_lines = 0

        self._init_ui()
        self._connect_signals()
        self.logger.info("G-code Previewer Widget initialized")

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

        if getattr(self, "tools_widget", None) is not None and getattr(
            self.tools_widget, "edit_gcode_button", None
        ):
            self.tools_widget.edit_gcode_button.clicked.connect(self._on_edit_gcode)

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
        except Exception:
            # Never allow status-bar issues to break the previewer
            self.logger.debug(
                "Failed to show status message in main window status bar",
                exc_info=True,
            )

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
                    return None

            # Check file size (warn for very large files)
            MAX_FILE_SIZE = 500 * 1024 * 1024  # 500MB
            file_size = file_path.stat().st_size

            if file_size > MAX_FILE_SIZE:
                self.logger.warning("Very large file: %s bytes", file_size)
                reply = QMessageBox.question(
                    self,
                    "Large File",
                    f"File is {file_size / (1024*1024):.1f}MB. "
                    "This may take a while to load. Continue?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply != QMessageBox.Yes:
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

    def _update_statistics(self) -> None:
        """Update statistics display."""
        stats = self.parser.get_statistics()
        bounds = stats["bounds"]

        stats_text = f"""
        <b>Toolpath Statistics</b><br>
        Total Moves: {stats['total_moves']}<br>
        Rapid Moves: {stats['rapid_moves']}<br>
        Cutting Moves: {stats['cutting_moves']}<br>
        Arc Moves: {stats['arc_moves']}<br>
        <br>
        <b>Bounds</b><br>
        X: {bounds['min_x']:.2f} to {bounds['max_x']:.2f}<br>
        Y: {bounds['min_y']:.2f} to {bounds['max_y']:.2f}<br>
        Z: {bounds['min_z']:.2f} to {bounds['max_z']:.2f}
        """

        self.stats_label.setText(stats_text)

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
            MAX_EDITOR_SIZE = 10 * 1024 * 1024  # 10MB
            file_size = os.path.getsize(self.current_file)

            if file_size > MAX_EDITOR_SIZE:
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

            # Update statistics and table
            self._update_statistics()
            self._update_moves_table()

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

        # Update UI - detailed text in the status bar
        file_name = Path(self.current_file).name
        file_size_mb = Path(self.current_file).stat().st_size / (1024 * 1024)
        info_text = (
            f"Loaded G-code: {file_name} ({file_size_mb:.1f}MB, {self.total_file_lines:,} lines, {len(self.moves):,} moves)"
        )
        self._show_status_message(info_text, 5000)

        # Update moves table
        self._update_moves_table()

        # Add axes
        self.renderer._add_axes()
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
            self.animation_controller.set_current_frame(frame_index)

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

        # Update moves table
        self._update_moves_table()

        # Ensure final incremental actors are built before we adjust camera/axes
        self.renderer._update_incremental_actors()

        # Add axes and fit view
        self.renderer._add_axes()
        self.renderer.reset_camera()
        self.vtk_widget.update_render()

        self.gcode_loaded.emit(self.current_file)
        self.logger.info("Interactive loader finished: %s moves", f"{len(self.moves):,}")

    def _on_interactive_loader_chunk_loaded(self, chunk_moves: list) -> None:
        """Handle chunk loaded from interactive loader."""
        # Add moves to renderer incrementally
        self.renderer.add_moves_incremental(chunk_moves)
        self.vtk_widget.update_render()

        # Update statistics
        self._update_statistics()
