"""
Model Editor Dialog - UI for model editing and transformation.

Provides:
- Interactive model rotation controls
- Z-up orientation detection and correction
- Manual and automatic verification
- Model preview and integrity checking
"""

from typing import Optional
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QPushButton, QLabel,
    QSpinBox, QComboBox, QMessageBox, QProgressBar, QTextEdit, QFrame
)
from PySide6.QtGui import QIcon

from src.core.logging_config import get_logger
from src.parsers.stl_parser import STLModel
from .model_editor_core import ModelEditor, RotationAxis
from .stl_writer import STLWriter


logger = get_logger(__name__)


class ModelEditorDialog(QDialog):
    """Dialog for editing 3D models with rotation and transformation."""

    model_saved = Signal(str)  # Emitted with path to saved model

    def __init__(self, model: STLModel, parent=None):
        """
        Initialize model editor dialog.

        Args:
            model: STLModel to edit
            parent: Parent widget
        """
        super().__init__(parent)
        self.model = model
        self.editor = ModelEditor(model)
        self.logger = logger
        self.saved_path: Optional[str] = None

        self.setWindowTitle("Model Editor - Rotation & Transformation")
        self.setMinimumWidth(600)
        self.setMinimumHeight(700)

        self._setup_ui()
        self._apply_auto_z_up_detection()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(12, 12, 12, 12)

        # Title
        title = QLabel("Model Editor - Rotation & Transformation")
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        # Rotation Controls Group
        rotation_group = self._create_rotation_controls()
        layout.addWidget(rotation_group)

        # Z-Up Detection Group
        zup_group = self._create_zup_detection_group()
        layout.addWidget(zup_group)

        # Verification Group
        verify_group = self._create_verification_group()
        layout.addWidget(verify_group)

        # Status/Info Group
        info_group = self._create_info_group()
        layout.addWidget(info_group)

        # Action Buttons
        button_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Reset to Original")
        reset_btn.clicked.connect(self._reset_model)
        button_layout.addWidget(reset_btn)

        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save Model")
        save_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        save_btn.clicked.connect(self._save_model)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _create_rotation_controls(self) -> QGroupBox:
        """Create rotation control group."""
        group = QGroupBox("Rotation Controls (90° increments)")
        layout = QVBoxLayout(group)

        # X-axis rotation
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("Rotate X:"))
        self.x_spin = QSpinBox()
        self.x_spin.setRange(-360, 360)
        self.x_spin.setSingleStep(90)
        self.x_spin.setValue(0)
        x_layout.addWidget(self.x_spin)
        x_btn = QPushButton("Apply")
        x_btn.clicked.connect(lambda: self._apply_rotation(RotationAxis.X))
        x_layout.addWidget(x_btn)
        x_layout.addStretch()
        layout.addLayout(x_layout)

        # Y-axis rotation
        y_layout = QHBoxLayout()
        y_layout.addWidget(QLabel("Rotate Y:"))
        self.y_spin = QSpinBox()
        self.y_spin.setRange(-360, 360)
        self.y_spin.setSingleStep(90)
        self.y_spin.setValue(0)
        y_layout.addWidget(self.y_spin)
        y_btn = QPushButton("Apply")
        y_btn.clicked.connect(lambda: self._apply_rotation(RotationAxis.Y))
        y_layout.addWidget(y_btn)
        y_layout.addStretch()
        layout.addLayout(y_layout)

        # Z-axis rotation
        z_layout = QHBoxLayout()
        z_layout.addWidget(QLabel("Rotate Z:"))
        self.z_spin = QSpinBox()
        self.z_spin.setRange(-360, 360)
        self.z_spin.setSingleStep(90)
        self.z_spin.setValue(0)
        z_layout.addWidget(self.z_spin)
        z_btn = QPushButton("Apply")
        z_btn.clicked.connect(lambda: self._apply_rotation(RotationAxis.Z))
        z_layout.addWidget(z_btn)
        z_layout.addStretch()
        layout.addLayout(z_layout)

        return group

    def _create_zup_detection_group(self) -> QGroupBox:
        """Create Z-up detection group."""
        group = QGroupBox("Z-Up Orientation")
        layout = QVBoxLayout(group)

        # Auto-detect button
        auto_btn = QPushButton("Auto-Detect Z-Up")
        auto_btn.clicked.connect(self._apply_auto_z_up_detection)
        layout.addWidget(auto_btn)

        # Add solid plane checkbox
        self.add_plane_btn = QPushButton("Add Solid Plane at Z=0")
        self.add_plane_btn.clicked.connect(self._add_solid_plane)
        layout.addWidget(self.add_plane_btn)

        return group

    def _create_verification_group(self) -> QGroupBox:
        """Create verification group."""
        group = QGroupBox("Verification")
        layout = QVBoxLayout(group)

        # Manual verification
        manual_layout = QHBoxLayout()
        manual_btn = QPushButton("Manual Verify")
        manual_btn.clicked.connect(self._manual_verify)
        manual_layout.addWidget(manual_btn)
        manual_layout.addStretch()
        layout.addLayout(manual_layout)

        # Auto verification
        auto_layout = QHBoxLayout()
        auto_btn = QPushButton("Auto Verify")
        auto_btn.clicked.connect(self._auto_verify)
        auto_layout.addWidget(auto_btn)
        auto_layout.addStretch()
        layout.addLayout(auto_layout)

        return group

    def _create_info_group(self) -> QGroupBox:
        """Create information display group."""
        group = QGroupBox("Model Information")
        layout = QVBoxLayout(group)

        self.info_text = QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(150)
        layout.addWidget(self.info_text)

        self._update_info_display()
        return group

    def _apply_rotation(self, axis: RotationAxis) -> None:
        """Apply rotation to model."""
        try:
            if axis == RotationAxis.X:
                degrees = self.x_spin.value()
            elif axis == RotationAxis.Y:
                degrees = self.y_spin.value()
            else:
                degrees = self.z_spin.value()

            self.editor.rotate_model(axis, degrees)
            self._update_info_display()
            QMessageBox.information(self, "Success", f"Rotated {degrees}° around {axis.value} axis")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to rotate model: {e}")
            self.logger.error(f"Rotation failed: {e}")

    def _apply_auto_z_up_detection(self) -> None:
        """Apply automatic Z-up detection."""
        try:
            axis, degrees = self.editor.analyzer.get_z_up_recommendation()
            if degrees != 0:
                self.editor.rotate_model(RotationAxis[axis], degrees)
                self._update_info_display()
                QMessageBox.information(self, "Z-Up Applied", 
                                      f"Applied {degrees}° rotation around {axis} axis")
            else:
                QMessageBox.information(self, "Already Z-Up", "Model is already oriented with Z-up")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to detect Z-up: {e}")

    def _add_solid_plane(self) -> None:
        """Add solid plane at Z=0."""
        try:
            self.editor.add_solid_plane_at_z_zero()
            self._update_info_display()
            QMessageBox.information(self, "Success", "Solid plane added at Z=0")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add solid plane: {e}")

    def _manual_verify(self) -> None:
        """Perform manual verification."""
        try:
            is_valid, message = self.editor.verify_model_integrity()
            if is_valid:
                QMessageBox.information(self, "Verification Passed", message)
            else:
                QMessageBox.warning(self, "Verification Failed", message)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Verification failed: {e}")

    def _auto_verify(self) -> None:
        """Perform automatic verification."""
        try:
            is_valid, message = self.editor.verify_model_integrity()
            if is_valid:
                QMessageBox.information(self, "Auto Verification Passed", message)
            else:
                QMessageBox.warning(self, "Auto Verification Failed", message)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Auto verification failed: {e}")

    def _reset_model(self) -> None:
        """Reset model to original state."""
        reply = QMessageBox.question(self, "Reset Model", 
                                    "Reset all changes and return to original model?",
                                    QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.editor.reset_to_original()
            self.x_spin.setValue(0)
            self.y_spin.setValue(0)
            self.z_spin.setValue(0)
            self._update_info_display()

    def _save_model(self) -> None:
        """Save edited model."""
        try:
            # Verify before saving
            is_valid, message = self.editor.verify_model_integrity()
            if not is_valid:
                reply = QMessageBox.question(self, "Verification Warning",
                                           f"{message}\n\nContinue saving anyway?",
                                           QMessageBox.Yes | QMessageBox.No)
                if reply != QMessageBox.Yes:
                    return

            # Generate output path
            original_path = Path(self.model.header) if hasattr(self.model, 'header') else Path("model.stl")
            output_path = original_path.parent / f"{original_path.stem}_edited.stl"

            # Save model using STL writer
            success = STLWriter.write(self.editor.current_model, str(output_path), binary=True)

            if success:
                self.saved_path = str(output_path)
                self.model_saved.emit(self.saved_path)
                QMessageBox.information(self, "Success", f"Model saved to:\n{output_path}")
                self.accept()
            else:
                QMessageBox.critical(self, "Error", "Failed to write STL file")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save model: {e}")

    def _update_info_display(self) -> None:
        """Update information display."""
        info = f"""
Model Information:
- Triangles: {len(self.editor.current_model.triangles)}
- Faces: {len(self.editor.analyzer.faces)}
- Hollow Faces: {len(self.editor.analyzer.get_hollow_faces())}

Rotations Applied:
{self.editor.get_rotation_summary()}

Model Status:
- Original triangles: {len(self.model.triangles)}
- Current triangles: {len(self.editor.current_model.triangles)}
        """
        self.info_text.setText(info.strip())

