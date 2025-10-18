"""G-code Previewer Widget - Main UI for CNC toolpath visualization."""

from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QSplitter, QGroupBox, QProgressBar,
    QSlider, QSpinBox, QComboBox, QCheckBox, QTabWidget
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


class GcodePreviewerWidget(QWidget):
    """Main widget for G-code preview and visualization."""
    
    gcode_loaded = Signal(str)  # Emits filepath when G-code is loaded
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the G-code previewer widget."""
        super().__init__(parent)
        self.logger = get_logger(__name__)

        self.parser = GcodeParser()
        self.renderer = GcodeRenderer()
        self.animation_controller = AnimationController()
        self.layer_analyzer = LayerAnalyzer()
        self.feed_speed_visualizer = FeedSpeedVisualizer()
        self.export_manager = ExportManager()
        self.loader_thread: Optional[GcodeLoaderThread] = None

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
        
        # Main content: splitter with 3D view and info panel
        splitter = QSplitter(Qt.Horizontal)
        
        # 3D VTK viewer
        self.vtk_widget = VTKWidget(self.renderer)
        splitter.addWidget(self.vtk_widget)
        
        # Right panel with statistics and moves table
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(8)
        
        # Statistics group
        stats_group = QGroupBox("Toolpath Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        self.stats_label = QLabel("Load a G-code file to see statistics")
        self.stats_label.setWordWrap(True)
        stats_layout.addWidget(self.stats_label)
        
        right_layout.addWidget(stats_group)
        
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
        
        right_layout.addWidget(moves_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        right_layout.addStretch()

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
    
    def _on_load_file(self) -> None:
        """Handle load file button click."""
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open G-code File",
            "",
            "G-code Files (*.nc *.gcode *.gco *.tap);;All Files (*)"
        )
        
        if filepath:
            self.load_gcode_file(filepath)
    
    def load_gcode_file(self, filepath: str) -> None:
        """Load and display a G-code file in background."""
        try:
            # Stop any existing loader
            if self.loader_thread and self.loader_thread.isRunning():
                self.loader_thread.stop()
                self.loader_thread.wait()

            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)

            # Get file info
            file_size_mb = Path(filepath).stat().st_size / (1024 * 1024)
            self.total_file_lines = self.parser.get_file_line_count(filepath)

            # Update UI with file info
            file_name = Path(filepath).name
            info_text = f"Loading: {file_name} ({file_size_mb:.1f}MB, {self.total_file_lines:,} lines)..."
            self.file_label.setText(info_text)
            self.file_label.setStyleSheet("color: orange;")

            self.current_file = filepath
            self.moves = []

            # Clear renderer for incremental rendering
            self.renderer.clear_incremental()
            self.vtk_widget.update_render()

            # Start background loader
            self.loader_thread = GcodeLoaderThread(filepath, batch_size=5000)
            self.loader_thread.progress.connect(self._on_loader_progress)
            self.loader_thread.moves_loaded.connect(self._on_moves_batch_loaded)
            self.loader_thread.finished_loading.connect(self._on_loader_finished)
            self.loader_thread.error_occurred.connect(self._on_loader_error)
            self.loader_thread.start()

        except Exception as e:
            self.logger.error(f"Failed to start loading G-code file: {e}")
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
        """Handle edit G-code."""
        if not self.current_file:
            self.logger.warning("No G-code file loaded")
            return

        # Create editor dialog
        editor_widget = GcodeEditorWidget()
        with open(self.current_file, 'r', encoding='utf-8', errors='ignore') as f:
            editor_widget.set_content(f.read())

        editor_widget.reload_requested.connect(self._on_gcode_reload)
        editor_widget.show()

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

