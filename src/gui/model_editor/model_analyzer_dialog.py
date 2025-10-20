"""
Model Analyzer Dialog - Analyzes models for errors and offers fixing.

Provides:
- Error detection and status display
- Before/after statistics comparison
- Automatic error fixing
- Save or replace options
"""

from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel,
    QMessageBox, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QColor

from src.core.logging_config import get_logger
from src.parsers.stl_parser import STLModel
from .model_error_detector import ModelErrorDetector
from .model_error_fixer import ModelErrorFixer
from .stl_writer import STLWriter

logger = get_logger(__name__)


class ModelAnalyzerDialog(QDialog):
    """Dialog for analyzing models and fixing errors."""

    def __init__(self, model: STLModel, file_path: str, parent=None):
        """
        Initialize model analyzer dialog.

        Args:
            model: STLModel to analyze
            file_path: Path to the model file
            parent: Parent widget
        """
        super().__init__(parent)
        self.model = model
        self.file_path = file_path
        self.fixed_model = None
        self.fixes_applied = None
        self.logger = logger

        self.setWindowTitle("Model Analyzer")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self._setup_ui()
        self._analyze_model()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("🔍 Model Analysis")
        title_font = title.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_content = QVBoxLayout()

        # Original model stats
        stats_group = QGroupBox("Original Model Statistics")
        stats_layout = QVBoxLayout()
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(100)
        stats_layout.addWidget(self.stats_text)
        stats_group.setLayout(stats_layout)
        scroll_content.addWidget(stats_group)

        # Error detection results
        error_group = QGroupBox("Error Detection Results")
        error_layout = QVBoxLayout()
        self.error_text = QTextEdit()
        self.error_text.setReadOnly(True)
        self.error_text.setMaximumHeight(150)
        error_layout.addWidget(self.error_text)
        error_group.setLayout(error_layout)
        scroll_content.addWidget(error_group)

        # Fixed model stats (hidden initially)
        self.fixed_stats_group = QGroupBox("Fixed Model Statistics")
        fixed_stats_layout = QVBoxLayout()
        self.fixed_stats_text = QTextEdit()
        self.fixed_stats_text.setReadOnly(True)
        self.fixed_stats_text.setMaximumHeight(100)
        fixed_stats_layout.addWidget(self.fixed_stats_text)
        self.fixed_stats_group.setLayout(fixed_stats_layout)
        self.fixed_stats_group.setVisible(False)
        scroll_content.addWidget(self.fixed_stats_group)

        # Fixes applied (hidden initially)
        self.fixes_group = QGroupBox("Fixes Applied")
        fixes_layout = QVBoxLayout()
        self.fixes_text = QTextEdit()
        self.fixes_text.setReadOnly(True)
        self.fixes_text.setMaximumHeight(100)
        fixes_layout.addWidget(self.fixes_text)
        self.fixes_group.setLayout(fixes_layout)
        self.fixes_group.setVisible(False)
        scroll_content.addWidget(self.fixes_group)

        scroll.setLayout(scroll_content)
        layout.addWidget(scroll)

        # Buttons
        button_layout = QHBoxLayout()

        self.fix_btn = QPushButton("🔧 Fix All Errors")
        self.fix_btn.clicked.connect(self._fix_errors)
        button_layout.addWidget(self.fix_btn)

        self.save_btn = QPushButton("💾 Save As...")
        self.save_btn.clicked.connect(self._save_as)
        self.save_btn.setVisible(False)
        button_layout.addWidget(self.save_btn)

        self.replace_btn = QPushButton("🔄 Replace Original")
        self.replace_btn.clicked.connect(self._replace_original)
        self.replace_btn.setVisible(False)
        button_layout.addWidget(self.replace_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _analyze_model(self) -> None:
        """Analyze the model for errors."""
        try:
            # Display original stats
            self._display_original_stats()

            # Detect errors
            detector = ModelErrorDetector(self.model)
            errors = detector.detect_all_errors()

            # Display error results
            self._display_error_results(errors)

        except Exception as e:
            self.logger.error(f"Failed to analyze model: {e}")
            QMessageBox.critical(self, "Error", f"Failed to analyze model: {e}")

    def _display_original_stats(self) -> None:
        """Display original model statistics."""
        stats = self.model.stats
        text = f"""
Triangles: {len(self.model.triangles):,}
Vertices: {stats.vertex_count:,}
File Size: {stats.file_size_bytes:,} bytes
Format: {stats.format_type.value}
        """.strip()
        self.stats_text.setText(text)

    def _display_error_results(self, errors) -> None:
        """Display error detection results."""
        if not errors:
            text = "✅ No errors detected!"
            self.fix_btn.setEnabled(False)
        else:
            text = f"Found {len(errors)} error type(s):\n\n"
            for error in errors:
                icon = "🔴" if error.severity == "critical" else "🟡" if error.severity == "warning" else "🔵"
                text += f"{icon} {error.error_type.upper()}\n"
                text += f"   {error.description}\n"
                if error.affected_triangles:
                    text += f"   Count: {len(error.affected_triangles)}\n"
                text += "\n"

        self.error_text.setText(text)

    def _fix_errors(self) -> None:
        """Fix all detected errors."""
        try:
            fixer = ModelErrorFixer(self.model)
            self.fixed_model, self.fixes_applied = fixer.fix_all_errors()

            # Display fixed stats
            self._display_fixed_stats()

            # Display fixes applied
            self._display_fixes_applied()

            # Show save/replace buttons
            self.fix_btn.setVisible(False)
            self.save_btn.setVisible(True)
            self.replace_btn.setVisible(True)
            self.fixed_stats_group.setVisible(True)
            self.fixes_group.setVisible(True)

        except Exception as e:
            self.logger.error(f"Failed to fix errors: {e}")
            QMessageBox.critical(self, "Error", f"Failed to fix errors: {e}")

    def _display_fixed_stats(self) -> None:
        """Display fixed model statistics."""
        stats = self.fixed_model.stats
        original_triangles = len(self.model.triangles)
        fixed_triangles = len(self.fixed_model.triangles)
        removed = original_triangles - fixed_triangles

        text = f"""
Triangles: {fixed_triangles:,} (removed: {removed})
Vertices: {stats.vertex_count:,}
File Size: {stats.file_size_bytes:,} bytes
        """.strip()
        self.fixed_stats_text.setText(text)

    def _display_fixes_applied(self) -> None:
        """Display summary of fixes applied."""
        text = "Fixes Applied:\n\n"
        for fix_type, count in self.fixes_applied.items():
            if count > 0:
                text += f"✓ {fix_type}: {count}\n"

        self.fixes_text.setText(text)

    def _save_as(self) -> None:
        """Save fixed model as new file."""
        try:
            from PySide6.QtWidgets import QFileDialog
            
            original_path = Path(self.file_path)
            default_name = f"{original_path.stem} - Fixed{original_path.suffix}"
            
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Fixed Model",
                str(original_path.parent / default_name),
                "STL Files (*.stl);;All Files (*)"
            )

            if file_path:
                success = STLWriter.write(self.fixed_model, file_path, binary=True)
                if success:
                    QMessageBox.information(self, "Success", f"Model saved to:\n{file_path}")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to save model")

        except Exception as e:
            self.logger.error(f"Failed to save model: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save model: {e}")

    def _replace_original(self) -> None:
        """Replace original file with fixed model."""
        try:
            reply = QMessageBox.warning(
                self,
                "Replace Original",
                f"Replace original file?\n{self.file_path}",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply == QMessageBox.Yes:
                success = STLWriter.write(self.fixed_model, self.file_path, binary=True)
                if success:
                    QMessageBox.information(self, "Success", "Original file replaced with fixed model")
                    self.accept()
                else:
                    QMessageBox.critical(self, "Error", "Failed to replace file")

        except Exception as e:
            self.logger.error(f"Failed to replace file: {e}")
            QMessageBox.critical(self, "Error", f"Failed to replace file: {e}")

