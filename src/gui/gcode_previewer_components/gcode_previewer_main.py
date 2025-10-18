"""G-code Previewer Widget - Main UI for CNC toolpath visualization."""

from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog,
    QTableWidget, QTableWidgetItem, QSplitter, QGroupBox, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont

from src.core.logging_config import get_logger
from .gcode_parser import GcodeParser
from .gcode_renderer import GcodeRenderer
from .vtk_widget import VTKWidget


class GcodePreviewerWidget(QWidget):
    """Main widget for G-code preview and visualization."""
    
    gcode_loaded = Signal(str)  # Emits filepath when G-code is loaded
    
    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize the G-code previewer widget."""
        super().__init__(parent)
        self.logger = get_logger(__name__)
        
        self.parser = GcodeParser()
        self.renderer = GcodeRenderer()
        self.current_file = None
        self.moves = []
        
        self._init_ui()
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
        """Load and display a G-code file."""
        try:
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            
            # Parse G-code
            self.moves = self.parser.parse_file(filepath)
            self.current_file = filepath
            
            # Update UI
            self.file_label.setText(f"Loaded: {Path(filepath).name}")
            self.file_label.setStyleSheet("color: green;")
            
            # Render toolpath
            self.renderer.render_toolpath(self.moves)
            self.vtk_widget.update_render()
            
            # Update statistics
            self._update_statistics()
            
            # Update moves table
            self._update_moves_table()
            
            self.gcode_loaded.emit(filepath)
            self.logger.info(f"Loaded G-code file: {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to load G-code file: {e}")
            self.file_label.setText(f"Error: {str(e)}")
            self.file_label.setStyleSheet("color: red;")
        finally:
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
        
        for idx, move in enumerate(self.moves[:50]):
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

