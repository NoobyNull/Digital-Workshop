from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QImage, QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QGroupBox,
    QDialogButtonBox,
    QMessageBox,
    QDoubleSpinBox,
    QColorDialog,
)

from core.database_manager import get_database_manager
from gui.material_manager import MaterialManager
from gui.theme import COLORS


def _rgbf_to_hex(rgb: Tuple[float, float, float]) -> str:
    r = max(0, min(255, int(round(float(rgb[0]) * 255.0))))
    g = max(0, min(255, int(round(float(rgb[1]) * 255.0))))
    b = max(0, min(255, int(round(float(rgb[2]) * 255.0))))
    return f"#{r:02x}{g:02x}{b:02x}"


class MaterialPickerWidget(QDialog):
    """Dialog for selecting wood materials"""

    # Signals
    material_selected = Signal(str)  # species name

    def __init__(
        self,
        db_manager=None,
        material_manager: Optional[MaterialManager] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Material Picker")
        self.setObjectName("MaterialPickerWidget")
        self.setModal(True)

        self.db = db_manager or get_database_manager()
        self.material_manager = material_manager or MaterialManager(self.db)

        self._species_records: Dict[str, Dict] = {}

        self._build_ui()
        self._apply_theme_styles()

        # Load species and update UI
        self._load_species()
        if self.species_combo.count() > 0:
            self.species_combo.setCurrentIndex(0)
            self._update_preview_and_properties()

    # ---- UI construction ----
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Selection group
        self.selection_group = QGroupBox("Species Selection")
        sel_layout = QHBoxLayout(self.selection_group)
        sel_layout.setContentsMargins(10, 10, 10, 10)
        sel_layout.setSpacing(8)

        self.species_label = QLabel("Species:")
        self.species_combo = QComboBox()
        self.species_combo.currentIndexChanged.connect(self._update_preview_and_properties)

        self.add_custom_button = QPushButton("Add Custom Species")
        self._style_button(self.add_custom_button)
        self.add_custom_button.clicked.connect(self._open_add_custom_dialog)

        sel_layout.addWidget(self.species_label)
        sel_layout.addWidget(self.species_combo, 1)
        sel_layout.addWidget(self.add_custom_button)

        # Preview group
        self.preview_group = QGroupBox("Preview")
        prev_layout = QVBoxLayout(self.preview_group)
        prev_layout.setContentsMargins(10, 10, 10, 10)
        prev_layout.setSpacing(8)

        self.preview_label = QLabel()
        self.preview_label.setFixedSize(256, 256)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(f"border: 1px solid {COLORS.border}; background-color: {COLORS.surface};")
        self.preview_label.setScaledContents(True)
        prev_layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)

        # Properties group
        self.props_group = QGroupBox("Material Properties")
        props_form = QFormLayout(self.props_group)
        props_form.setLabelAlignment(Qt.AlignRight)

        self.base_color_edit = QLineEdit()
        self.grain_color_edit = QLineEdit()
        self.grain_pattern_edit = QLineEdit()
        self.grain_scale_edit = QLineEdit()
        self.roughness_edit = QLineEdit()
        self.specular_edit = QLineEdit()
        for w in [
            self.base_color_edit,
            self.grain_color_edit,
            self.grain_pattern_edit,
            self.grain_scale_edit,
            self.roughness_edit,
            self.specular_edit,
        ]:
            w.setReadOnly(True)

        props_form.addRow("Base Color (hex):", self.base_color_edit)
        props_form.addRow("Grain Color (hex):", self.grain_color_edit)
        props_form.addRow("Grain Pattern:", self.grain_pattern_edit)
        props_form.addRow("Grain Scale:", self.grain_scale_edit)
        props_form.addRow("Roughness:", self.roughness_edit)
        props_form.addRow("Specular:", self.specular_edit)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self)
        ok_btn = self.buttons.button(QDialogButtonBox.Ok)
        cancel_btn = self.buttons.button(QDialogButtonBox.Cancel)
        self._style_button(ok_btn)
        self._style_button(cancel_btn)

        self.buttons.accepted.connect(self._on_apply)
        self.buttons.rejected.connect(self.reject)

        # Assemble
        layout.addWidget(self.selection_group)
        layout.addWidget(self.preview_group)
        layout.addWidget(self.props_group)
        layout.addWidget(self.buttons)

    def _apply_theme_styles(self) -> None:
        # Minimal theme-aware styling
        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {COLORS.groupbox_border};
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 10px;
                background-color: {COLORS.groupbox_bg};
                color: {COLORS.groupbox_text};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: {COLORS.groupbox_title_text};
            }}
            QLabel {{
                color: {COLORS.label_text};
                background-color: transparent;
            }}
            QComboBox, QLineEdit {{
                background-color: {COLORS.input_bg};
                color: {COLORS.input_text};
                border: 1px solid {COLORS.input_border};
                padding: 6px;
                border-radius: 3px;
            }}
            QComboBox:focus, QLineEdit:focus {{
                border: 1px solid {COLORS.input_focus_border};
            }}
            """
        )

    def _style_button(self, button: QPushButton) -> None:
        button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {COLORS.button_bg};
                color: {COLORS.button_text};
                border: 1px solid {COLORS.button_border};
                padding: 6px 12px;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {COLORS.button_hover_bg};
                border-color: {COLORS.button_hover_border};
            }}
            """
        )

    # ---- Data loading and updates ----
    def _load_species(self) -> None:
        self._species_records.clear()
        self.species_combo.blockSignals(True)
        self.species_combo.clear()
        try:
            rows = self.db.get_wood_materials()
        except Exception as e:
            QMessageBox.warning(self, "Database Error", f"Failed to load materials:\n{e}")
            rows = []

        for rec in rows:
            name = str(rec.get("name", "Unknown"))
            is_default = int(rec.get("is_default", 0)) == 1
            label = f"{name} (Default)" if is_default else name
            # Store real name in userData for clean emission
            self.species_combo.addItem(label, userData=name)
            self._species_records[name] = rec

        self.species_combo.blockSignals(False)

    def _current_species_name(self) -> Optional[str]:
        idx = self.species_combo.currentIndex()
        if idx < 0:
            return None
        return self.species_combo.itemData(idx)

    def _update_preview_and_properties(self) -> None:
        name = self._current_species_name()
        if not name:
            self.preview_label.clear()
            for w in [
                self.base_color_edit,
                self.grain_color_edit,
                self.grain_pattern_edit,
                self.grain_scale_edit,
                self.roughness_edit,
                self.specular_edit,
            ]:
                w.clear()
            return

        rec = self._species_records.get(name, {})
        # Update properties
        base = (
            float(rec.get("base_color_r", 0.7)),
            float(rec.get("base_color_g", 0.55)),
            float(rec.get("base_color_b", 0.4)),
        )
        grain = (
            float(rec.get("grain_color_r", 0.5)),
            float(rec.get("grain_color_g", 0.4)),
            float(rec.get("grain_color_b", 0.3)),
        )
        grain_pattern = str(rec.get("grain_pattern", "ring"))
        grain_scale = float(rec.get("grain_scale", 1.0))
        roughness = float(rec.get("roughness", 0.5))
        specular = float(rec.get("specular", 0.3))

        self.base_color_edit.setText(_rgbf_to_hex(base))
        self.grain_color_edit.setText(_rgbf_to_hex(grain))
        self.grain_pattern_edit.setText(grain_pattern)
        self.grain_scale_edit.setText(f"{grain_scale:.2f}")
        self.roughness_edit.setText(f"{roughness:.2f}")
        self.specular_edit.setText(f"{specular:.2f}")

        # Update preview (256x256)
        try:
            img = self.material_manager.generate_wood_texture(name, size=(256, 256))
            h, w, ch = img.shape
            qimg = QImage(img.data, w, h, ch * w, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qimg)
            self.preview_label.setPixmap(pix)
        except Exception as e:
            self.preview_label.clear()
            QMessageBox.warning(self, "Preview Error", f"Failed to generate preview:\n{e}")

    # ---- Actions ----
    def _on_apply(self) -> None:
        name = self._current_species_name()
        if not name:
            QMessageBox.information(self, "No Selection", "Please select a material species.")
            return
        self.material_selected.emit(name)
        self.accept()

    def _open_add_custom_dialog(self) -> None:
        dlg = QDialog(self)
        dlg.setWindowTitle("Add Custom Species")
        v = QVBoxLayout(dlg)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        name_edit = QLineEdit()
        base_btn = QPushButton("Pick Base Color")
        grain_btn = QPushButton("Pick Grain Color")
        self._style_button(base_btn)
        self._style_button(grain_btn)

        base_color = QColor(193, 154, 107)  # Oak-ish default
        grain_color = QColor(139, 115, 85)

        def _apply_color_style(btn: QPushButton, qc: QColor) -> None:
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {qc.name()};
                    color: {COLORS.button_text};
                    border: 1px solid {COLORS.button_border};
                    padding: 6px 12px;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    border-color: {COLORS.button_hover_border};
                }}
                """
            )

        _apply_color_style(base_btn, base_color)
        _apply_color_style(grain_btn, grain_color)

        def _pick_base():
            nonlocal base_color
            c = QColorDialog.getColor(base_color, self, "Pick Base Color")
            if c.isValid():
                base_color = c
                _apply_color_style(base_btn, base_color)

        def _pick_grain():
            nonlocal grain_color
            c = QColorDialog.getColor(grain_color, self, "Pick Grain Color")
            if c.isValid():
                grain_color = c
                _apply_color_style(grain_btn, grain_color)

        base_btn.clicked.connect(_pick_base)
        grain_btn.clicked.connect(_pick_grain)

        pattern_combo = QComboBox()
        pattern_combo.addItems(["ring", "straight"])

        scale_spin = QDoubleSpinBox()
        scale_spin.setRange(0.1, 10.0)
        scale_spin.setSingleStep(0.1)
        scale_spin.setValue(1.0)

        rough_spin = QDoubleSpinBox()
        rough_spin.setRange(0.0, 1.0)
        rough_spin.setSingleStep(0.05)
        rough_spin.setValue(0.5)

        spec_spin = QDoubleSpinBox()
        spec_spin.setRange(0.0, 1.0)
        spec_spin.setSingleStep(0.05)
        spec_spin.setValue(0.3)

        form.addRow("Species Name:", name_edit)
        form.addRow("Base Color:", base_btn)
        form.addRow("Grain Color:", grain_btn)
        form.addRow("Grain Pattern:", pattern_combo)
        form.addRow("Grain Scale:", scale_spin)
        form.addRow("Roughness:", rough_spin)
        form.addRow("Specular:", spec_spin)

        v.addLayout(form)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, parent=dlg)
        save_btn = btns.button(QDialogButtonBox.Save)
        cancel_btn = btns.button(QDialogButtonBox.Cancel)
        self._style_button(save_btn)
        self._style_button(cancel_btn)
        v.addWidget(btns)

        def _save():
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(dlg, "Validation", "Species name is required.")
                return
            # Convert QColor to normalized floats
            base = (base_color.redF(), base_color.greenF(), base_color.blueF())
            grain = (grain_color.redF(), grain_color.greenF(), grain_color.blueF())
            pattern = pattern_combo.currentText().strip()
            scale = float(scale_spin.value())
            roughness = float(rough_spin.value())
            specular = float(spec_spin.value())
            try:
                self.db.add_wood_material(
                    name=name,
                    base_color=base,
                    grain_color=grain,
                    grain_scale=scale,
                    grain_pattern=pattern,
                    roughness=roughness,
                    specular=specular,
                )
                # Refresh species and select new one
                self._load_species()
                # Find index by userData match
                for i in range(self.species_combo.count()):
                    if self.species_combo.itemData(i) == name:
                        self.species_combo.setCurrentIndex(i)
                        break
                self._update_preview_and_properties()
                dlg.accept()
            except Exception as e:
                QMessageBox.warning(dlg, "Save Failed", f"Could not save species:\n{e}")

        btns.accepted.connect(_save)
        btns.rejected.connect(dlg.reject)

        # Theme for the dialog
        dlg.setStyleSheet(
            f"""
            QDialog {{
                background-color: {COLORS.window_bg};
                color: {COLORS.text};
            }}
            QLineEdit, QComboBox, QDoubleSpinBox {{
                background-color: {COLORS.input_bg};
                color: {COLORS.input_text};
                border: 1px solid {COLORS.input_border};
                padding: 6px;
                border-radius: 3px;
            }}
            QDoubleSpinBox:focus, QLineEdit:focus, QComboBox:focus {{
                border: 1px solid {COLORS.input_focus_border};
            }}
            QLabel {{
                color: {COLORS.label_text};
                background-color: transparent;
            }}
            """
        )

        dlg.exec_()