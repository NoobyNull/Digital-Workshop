"""
Model Analyzer Dialog - Analyzes models for errors and offers fixing.

Provides:
- Error detection and status display
- Before/after statistics comparison
- Automatic error fixing
- Save or replace options
"""

import tempfile
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt

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

        # Single text display for all information
        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMinimumHeight(400)
        layout.addWidget(self.info_text)

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

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _analyze_model(self) -> None:
        """Analyze the model for errors."""
        try:
            # Check if model has triangles
            if not self.model:
                self.logger.warning("Model is None")
                self.info_text.setText("⚠️ Model is None")
                self.fix_btn.setEnabled(False)
                return

            # Check if triangles exist (handle both list and numpy array)
            has_triangles = False
            if self.model.triangles is not None:
                try:
                    has_triangles = len(self.model.triangles) > 0
                except (TypeError, ValueError):
                    has_triangles = False

            if not has_triangles:
                self.logger.warning("Model has no triangles to analyze")
                self.info_text.setText("⚠️ Model has no triangles to analyze")
                self.fix_btn.setEnabled(False)
                return

            # Detect errors
            detector = ModelErrorDetector(self.model)
            errors = detector.detect_all_errors()

            # Display all information in single text
            self._display_analysis_results(errors)

        except Exception as e:
            self.logger.error(f"Failed to analyze model: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to analyze model: {e}")

    def _display_analysis_results(self, errors) -> None:
        """Display all analysis results in a single text display."""
        stats = self.model.stats
        error_types = {
            "non_manifold": "Non-Manifold Edges",
            "hole": "Holes",
            "overlap": "Overlapping Triangles",
            "self_intersect": "Self-Intersecting Triangles",
            "hollow": "Hollow Areas"
        }

        detected_map = {error.error_type: error for error in errors}

        # Build complete analysis text
        text = "═" * 60 + "\n"
        text += "ORIGINAL MODEL STATISTICS\n"
        text += "═" * 60 + "\n"
        text += f"Triangles: {len(self.model.triangles):,}\n"
        text += f"Vertices: {stats.vertex_count:,}\n"
        text += f"File Size: {stats.file_size_bytes:,} bytes\n"
        text += f"Format: {stats.format_type.value}\n\n"

        text += "═" * 60 + "\n"
        text += "ERROR DETECTION RESULTS\n"
        text += "═" * 60 + "\n"

        if not errors:
            text += "✅ No errors detected!\n"
            self.fix_btn.setEnabled(False)
        else:
            text += f"Found {len(errors)} error type(s):\n\n"

        # Show status for all error types
        for error_key, error_name in error_types.items():
            if error_key in detected_map:
                error = detected_map[error_key]
                icon = "🔴" if error.severity == "critical" else "🟡" if error.severity == "warning" else "🔵"
                text += f"{icon} {error_name}: {error.count} found\n"
                text += f"   {error.description}\n"
            else:
                text += f"✅ {error_name}: None\n"

        self.info_text.setText(text)

    def _fix_errors(self) -> None:
        """Fix all detected errors."""
        try:
            fixer = ModelErrorFixer(self.model)
            self.fixed_model, self.fixes_applied = fixer.fix_all_errors()

            # Display all results in single text
            self._display_fix_results()

            # Show save/replace buttons
            self.fix_btn.setVisible(False)
            self.save_btn.setVisible(True)
            self.replace_btn.setVisible(True)

        except Exception as e:
            self.logger.error(f"Failed to fix errors: {e}")
            QMessageBox.critical(self, "Error", f"Failed to fix errors: {e}")

    def _display_fix_results(self) -> None:
        """Display fix results in single text display."""
        fixed_stats = self.fixed_model.stats
        original_triangles = len(self.model.triangles)
        fixed_triangles = len(self.fixed_model.triangles)
        removed = original_triangles - fixed_triangles

        # Get current text and append fix results
        current_text = self.info_text.toPlainText()

        text = current_text + "\n"
        text += "═" * 60 + "\n"
        text += "FIXED MODEL STATISTICS\n"
        text += "═" * 60 + "\n"
        text += f"Triangles: {fixed_triangles:,} (removed: {removed})\n"
        text += f"Vertices: {fixed_stats.vertex_count:,}\n"
        text += f"File Size: {fixed_stats.file_size_bytes:,} bytes\n\n"

        text += "═" * 60 + "\n"
        text += "FIXES APPLIED\n"
        text += "═" * 60 + "\n"
        for fix_type, count in self.fixes_applied.items():
            if count > 0:
                text += f"✓ {fix_type}: {count}\n"

        self.info_text.setText(text)

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
        """Replace original file with fixed model using temp storage."""
        try:
            reply = QMessageBox.warning(
                self,
                "Replace Original",
                f"Replace original file?\n{self.file_path}\n\n"
                "This will unload the model, replace the file, and reload it.",
                QMessageBox.Yes | QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

            original_path = Path(self.file_path)

            # Step 1: Write to temp file first
            with tempfile.NamedTemporaryFile(
                suffix=original_path.suffix,
                delete=False,
                dir=original_path.parent
            ) as temp_file:
                temp_path = temp_file.name

            try:
                # Write fixed model to temp file
                success = STLWriter.write(self.fixed_model, temp_path, binary=True)
                if not success:
                    QMessageBox.critical(self, "Error", "Failed to write fixed model to temp file")
                    Path(temp_path).unlink(missing_ok=True)
                    return

                # Step 2: Replace original file with temp file
                # Remove original and rename temp to original
                original_path.unlink()
                Path(temp_path).rename(original_path)

                QMessageBox.information(
                    self,
                    "Success",
                    f"Original file replaced successfully.\n\n"
                    f"File: {self.file_path}\n"
                    f"Triangles: {len(self.fixed_model.triangles):,}\n"
                    f"Removed: {len(self.model.triangles) - len(self.fixed_model.triangles)}"
                )
                self.accept()

            except Exception:
                # Clean up temp file if something went wrong
                Path(temp_path).unlink(missing_ok=True)
                raise

        except Exception as e:
            self.logger.error(f"Failed to replace file: {e}", exc_info=True)
            QMessageBox.critical(self, "Error", f"Failed to replace file: {e}")