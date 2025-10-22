"""
Model error dialog for 3D-MM Model Editor.

Shows detected errors and offers fixing options:
- Preview then save
- Trust mode (auto-fix and save)
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt
from typing import List, Optional
from .model_error_detector import MeshError


class ModelErrorDialog(QDialog):
    """Dialog for displaying and fixing model errors."""

    def __init__(self, errors: List[MeshError], parent=None):
        """Initialize error dialog."""
        super().__init__(parent)
        self.errors = errors
        self.fix_mode = None  # "preview" or "trust"
        self.setWindowTitle("Model Errors Detected")
        self.setGeometry(100, 100, 600, 500)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("⚠️ Model Errors Detected")
        title_font = title.font()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Error list
        error_text = QTextEdit()
        error_text.setReadOnly(True)
        error_text.setPlainText(self._format_errors())
        layout.addWidget(error_text)

        # Fix mode selection
        mode_group = QGroupBox("Fix Mode")
        mode_layout = QVBoxLayout()

        self.mode_buttons = QButtonGroup()

        # Preview mode
        preview_btn = QRadioButton("Preview then Save")
        preview_btn.setChecked(True)
        preview_btn.setToolTip("Show preview of fixes before saving")
        self.mode_buttons.addButton(preview_btn, 0)
        mode_layout.addWidget(preview_btn)

        # Trust mode
        trust_btn = QRadioButton("Trust Mode (Auto-fix and Save)")
        trust_btn.setToolTip("Automatically fix all errors and save")
        self.mode_buttons.addButton(trust_btn, 1)
        mode_layout.addWidget(trust_btn)

        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Buttons
        button_layout = QHBoxLayout()
        
        fix_btn = QPushButton("Fix & Continue")
        fix_btn.clicked.connect(self._on_fix_clicked)
        button_layout.addWidget(fix_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _format_errors(self) -> str:
        """Format errors for display."""
        if not self.errors:
            return "No errors detected."

        text = f"Found {len(self.errors)} error type(s):\n\n"
        
        for error in self.errors:
            severity_icon = {
                "critical": "🔴",
                "warning": "🟡",
                "info": "🔵"
            }.get(error.severity, "⚪")
            
            text += f"{severity_icon} {error.error_type.upper()}\n"
            text += f"   {error.description}\n"
            
            if error.affected_triangles:
                count = len(error.affected_triangles)
                text += f"   Affected triangles: {count}\n"
            
            text += "\n"

        return text

    def _on_fix_clicked(self) -> None:
        """Handle fix button click."""
        checked_id = self.mode_buttons.checkedId()
        self.fix_mode = "preview" if checked_id == 0 else "trust"
        self.accept()

    def get_fix_mode(self) -> str:
        """Get selected fix mode."""
        return self.fix_mode or "preview"

