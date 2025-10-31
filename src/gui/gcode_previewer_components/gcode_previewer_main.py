"""G-code Previewer Widget - Main UI for CNC toolpath visualization."""

from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QSplitter, QGroupBox, QProgressBar,
    QSlider, QSpinBox, QComboBox, QCheckBox, QTabWidget, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont

from src.core.logging_config import get_logger
from .gcode_parser import GcodeParser
from .gcode_renderer import GcodeRenderer
from .vtk_widget import VTKWidget
from .animation_controller import AnimationController, PlaybackState
from .layer_analyzer import LayerAnalyzer
from .feed_speed_visualizer import FeedSpeedVisualizer
from .export_manager import ExportManager
from .gcode_editor import GcodeEditorWidget
from .gcode_loader_thread import GcodeLoaderThread
from .gcode_timeline import GcodeTimeline
from .gcode_interactive_loader import InteractiveGcodeLoader


class GcodePreviewerWidget(QWidget):
    """Main widget for G-code preview and visualization."""
    
    gcode_loaded = Signal(str)  # Emits filepath when G-code is loaded
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the G-code previewer widget."""
        super().__init__(parent)
        self.logger = get_logger(__name__)

        self.parser = GcodeParser()
        self.renderer = None  # Defer VTK initialization
        self.animation_controller = AnimationController()
        self.layer_analyzer = LayerAnalyzer()
        self.feed_speed_visualizer = FeedSpeedVisualizer()
        self.export_manager = ExportManager()
        self.loader_thread: Optional[GcodeLoaderThread] = None

        # New VTK viewer components
        self.timeline: Optional[GcodeTimeline] = None
        self.interactive_loader: Optional[InteractiveGcodeLoader] = None
        self.editor: Optional[GcodeEditorWidget] = None
        self.vtk_widget: Optional[VTKWidget] = None

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

        # Top toolbar
        toolbar_layout = QHBoxLayout()

        load_btn = QPushButton("Load G-code File")
        load_btn.clicked.connect(self._on_load_file)
        toolbar_layout.addWidget(load_btn)

        self.file_label = QLabel("No file loaded")
        self.file_label.setStyleSheet("color: gray; font-style: italic;")
        toolbar_layout.addWidget(self.file_label)

        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)

        # Main content: splitter with 3D view and right panel
        splitter = QSplitter(Qt.Horizontal)

        # Initialize VTK renderer lazily
        try:
            if self.renderer is None:
                self.renderer = GcodeRenderer()

            # 3D VTK viewer
            self.vtk_widget = VTKWidget(self.renderer)
            splitter.addWidget(self.vtk_widget)
        except Exception as e:
            self.logger.error(f"Failed to initialize VTK viewer: {e}")
            # Create a placeholder label
            placeholder = QLabel("VTK Viewer unavailable")
            splitter.addWidget(placeholder)

        # Right panel with tabs for different views
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)

        # Create tab widget for right panel
        right_tabs = QTabWidget()

        # Tab 1: Timeline and Loader
        timeline_loader_widget = QWidget()
        timeline_loader_layout = QVBoxLayout(timeline_loader_widget)
        timeline_loader_layout.setContentsMargins(0, 0, 0, 0)
        timeline_loader_layout.setSpacing(8)

        # Timeline
        self.timeline = GcodeTimeline()
        timeline_loader_layout.addWidget(self.timeline)

        # Interactive loader
        self.interactive_loader = InteractiveGcodeLoader(self.renderer)
        timeline_loader_layout.addWidget(self.interactive_loader)

        right_tabs.addTab(timeline_loader_widget, "Timeline & Loader")

        # Tab 2: Statistics and Moves
        stats_moves_widget = QWidget()
        stats_moves_layout = QVBoxLayout(stats_moves_widget)
        stats_moves_layout.setContentsMargins(0, 0, 0, 0)
        stats_moves_layout.setSpacing(8)

        # Statistics group
        stats_group = QGroupBox("Toolpath Statistics")
        stats_layout = QVBoxLayout(stats_group)

        self.stats_label = QLabel("Load a G-code file to see statistics")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)

        stats_moves_layout.addWidget(stats_group)

        # Moves table
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

        right_tabs.addTab(stats_moves_widget, "Statistics")

        # Tab 3: G-code Editor
        self.editor = GcodeEditorWidget()
        right_tabs.addTab(self.editor, "Editor")

        right_layout.addWidget(right_tabs)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        layout.addWidget(splitter)

        # Bottom panel with playback and visualization controls
        self._init_playback_controls(layout)
        self._init_visualization_controls(layout)

    def _init_playback_controls(self, parent_layout: QVBoxLayout) -> None:
        """Initialize playback control panel."""
        playback_group = QGroupBox("Playback Controls")
        playback_layout = QHBoxLayout(playback_group)

        self.play_btn = QPushButton("▶ Play")
        self.play_btn.clicked.connect(self._on_play)
        playback_layout.addWidget(self.play_btn)

        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.clicked.connect(self._on_pause)
        self.pause_btn.setEnabled(False)
        playback_layout.addWidget(self.pause_btn)

        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.clicked.connect(self._on_stop)
        playback_layout.addWidget(self.stop_btn)

        playback_layout.addSpacing(20)

        playback_layout.addWidget(QLabel("Speed:"))
        self.speed_spinbox = QSpinBox()
        self.speed_spinbox.setRange(10, 500)
        self.speed_spinbox.setValue(100)
        self.speed_spinbox.setSuffix("%")
        self.speed_spinbox.valueChanged.connect(self._on_speed_changed)
        playback_layout.addWidget(self.speed_spinbox)

        playback_layout.addSpacing(20)

        playback_layout.addWidget(QLabel("Frame:"))
        self.frame_slider = QSlider(Qt.Horizontal)
        self.frame_slider.setMinimum(0)
        self.frame_slider.sliderMoved.connect(self._on_frame_slider_moved)
        playback_layout.addWidget(self.frame_slider)

        self.frame_label = QLabel("0/0")
        playback_layout.addWidget(self.frame_label)

        playback_layout.addStretch()

        parent_layout.addWidget(playback_group)

    def _init_visualization_controls(self, parent_layout: QVBoxLayout) -> None:
        """Initialize visualization control panel."""
        viz_group = QGroupBox("Visualization & Export")
        viz_layout = QHBoxLayout(viz_group)

        viz_layout.addWidget(QLabel("Visualization:"))
        self.viz_mode_combo = QComboBox()
        self.viz_mode_combo.addItems(["Default", "Feed Rate", "Spindle Speed"])
        self.viz_mode_combo.currentTextChanged.connect(self._on_viz_mode_changed)
        viz_layout.addWidget(self.viz_mode_combo)

        viz_layout.addSpacing(20)

        viz_layout.addWidget(QLabel("Layers:"))
        self.layer_combo = QComboBox()
        self.layer_combo.currentIndexChanged.connect(self._on_layer_changed)
        viz_layout.addWidget(self.layer_combo)

        self.show_all_layers_btn = QPushButton("Show All")
        self.show_all_layers_btn.clicked.connect(self._on_show_all_layers)
        viz_layout.addWidget(self.show_all_layers_btn)

        viz_layout.addSpacing(20)

        export_btn = QPushButton("📸 Export Screenshot")
        export_btn.clicked.connect(self._on_export_screenshot)
        viz_layout.addWidget(export_btn)

        video_btn = QPushButton("🎬 Export Video")
        video_btn.clicked.connect(self._on_export_video)
        viz_layout.addWidget(video_btn)

        edit_btn = QPushButton("✏️ Edit G-code")
        edit_btn.clicked.connect(self._on_edit_gcode)
        viz_layout.addWidget(edit_btn)

        viz_layout.addStretch()

        parent_layout.addWidget(viz_group)

    def _connect_signals(self) -> None:
        """Connect animation controller signals."""
        self.animation_controller.frame_changed.connect(self._on_animation_frame_changed)
        self.animation_controller.state_changed.connect(self._on_animation_state_changed)

        # Connect timeline signals
        if self.timeline:
            self.timeline.frame_changed.connect(self._on_timeline_frame_changed)
            self.timeline.playback_requested.connect(self._on_timeline_playback_requested)
            self.timeline.pause_requested.connect(self._on_timeline_pause_requested)
            self.timeline.stop_requested.connect(self._on_timeline_stop_requested)

        # Connect interactive loader signals
        if self.interactive_loader:
            self.interactive_loader.loading_complete.connect(self._on_interactive_loader_complete)
            self.interactive_loader.chunk_loaded.connect(self._on_interactive_loader_chunk_loaded)

        # Connect editor signals
        if self.editor:
            self.editor.reload_requested.connect(self._on_gcode_reload)
    
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
    
    def _update_statistics(self) -> None:
        """Update statistics display."""
        stats = self.parser.get_statistics()
        bounds = stats['bounds']
        
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
            self.moves_table.setItem(row, 5, QTableWidgetItem(f"{move.feed_rate:.1f}" if move.feed_rate else "-"))
            self.moves_table.setItem(row, 6, QTableWidgetItem(f"{move.spindle_speed:.0f}" if move.spindle_speed else "-"))

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
        """Handle speed change."""
        speed = value / 100.0
        self.animation_controller.set_speed(speed)

    def _on_frame_slider_moved(self, value: int) -> None:
        """Handle frame slider movement."""
        self.animation_controller.set_frame(value)

    def _on_animation_frame_changed(self, frame: int) -> None:
        """Handle animation frame change."""
        self.frame_slider.blockSignals(True)
        self.frame_slider.setValue(frame)
        self.frame_slider.blockSignals(False)

        total = self.animation_controller.get_total_frames()
        self.frame_label.setText(f"{frame}/{total}")

        # Update visualization to show moves up to current frame
        moves_to_show = self.animation_controller.get_moves_up_to_frame(frame)
        self.renderer.render_toolpath(moves_to_show)
        self.vtk_widget.update_render()

    def _on_animation_state_changed(self, state: PlaybackState) -> None:
        """Handle animation state change."""
        is_playing = state == PlaybackState.PLAYING
        self.play_btn.setEnabled(not is_playing)
        self.pause_btn.setEnabled(is_playing)

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

    def _on_export_screenshot(self) -> None:
        """Handle export screenshot."""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Screenshot", "", "PNG Files (*.png);;JPEG Files (*.jpg)"
        )
        if filepath:
            self.export_manager.set_render_window(self.renderer.get_render_window())
            if self.export_manager.export_screenshot(filepath):
                self.logger.info(f"Screenshot exported to {filepath}")

    def _on_export_video(self) -> None:
        """Handle export video."""
        if not self.export_manager.is_video_export_available():
            self.logger.warning("Video export requires OpenCV. Install with: pip install opencv-python")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Export Video", "", "MP4 Files (*.mp4);;AVI Files (*.avi)"
        )
        if filepath:
            self.logger.info("Video export not yet fully implemented")

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

    def _on_gcode_reload(self, content: str) -> None:
        """Handle G-code reload from editor."""
        try:
            # Parse the edited content
            self.moves = self.parser.parse_lines(content.split('\n'))

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

            # Update frame slider
            self.frame_slider.setMaximum(len(self.moves) - 1)

            self.logger.info("G-code reloaded and re-rendered")
        except Exception as e:
            self.logger.error(f"Failed to reload G-code: {e}")

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

        # Update UI
        file_name = Path(self.current_file).name
        file_size_mb = Path(self.current_file).stat().st_size / (1024 * 1024)
        info_text = f"Loaded: {file_name} ({file_size_mb:.1f}MB, {self.total_file_lines:,} lines, {len(self.moves):,} moves)"
        self.file_label.setText(info_text)
        self.file_label.setStyleSheet("color: green;")

        # Update frame slider
        self.frame_slider.setMaximum(len(self.moves) - 1)
        self.frame_slider.setValue(0)

        # Update moves table
        self._update_moves_table()

        # Add axes
        self.renderer._add_axes()
        self.renderer.reset_camera()
        self.vtk_widget.update_render()

        self.gcode_loaded.emit(self.current_file)
        self.logger.info(f"Finished loading G-code: {len(self.moves):,} moves")
        self.progress_bar.setVisible(False)

    def _on_loader_error(self, error_msg: str) -> None:
        """Handle loader error."""
        self.logger.error(f"Loader error: {error_msg}")
        self.file_label.setText(f"Error: {error_msg}")
        self.file_label.setStyleSheet("color: red;")
        self.progress_bar.setVisible(False)

    def _on_timeline_frame_changed(self, frame_index: int) -> None:
        """Handle frame change from timeline."""
        if frame_index < len(self.moves):
            # Update animation controller
            self.animation_controller.set_current_frame(frame_index)

            # Update frame slider
            self.frame_slider.blockSignals(True)
            self.frame_slider.setValue(frame_index)
            self.frame_slider.blockSignals(False)

            # Update frame label
            self.frame_label.setText(f"{frame_index}/{len(self.moves) - 1}")

            self.logger.debug(f"Timeline frame changed to {frame_index}")

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

        # Update frame slider
        self.frame_slider.setMaximum(len(self.moves) - 1)
        self.frame_slider.setValue(0)

        # Update moves table
        self._update_moves_table()

        # Add axes
        self.renderer._add_axes()
        self.renderer.reset_camera()
        self.vtk_widget.update_render()

        self.gcode_loaded.emit(self.current_file)
        self.logger.info(f"Interactive loader finished: {len(self.moves):,} moves")

    def _on_interactive_loader_chunk_loaded(self, chunk_moves: list) -> None:
        """Handle chunk loaded from interactive loader."""
        # Add moves to renderer incrementally
        self.renderer.add_moves_incremental(chunk_moves)
        self.vtk_widget.update_render()

        # Update statistics
        self._update_statistics()

