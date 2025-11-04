from __future__ import annotations

from pathlib import Path
from typing import Dict, Optional

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

from src.core.database_manager import get_database_manager
from src.core.logging_config import get_logger
from src.gui.material_manager import MaterialManager


class MaterialPickerWidget(QDialog):
    """Dialog for selecting wood materials"""

    # Signals
    material_selected = Signal(str)  # species name

    def __init__(
        """TODO: Add docstring."""
        self,
        db_manager=None,
        material_manager: Optional[MaterialManager] = None,
        model_format=None,  # Add model format parameter
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Material Picker")
        self.setObjectName("MaterialPickerWidget")
        self.setModal(True)

        # Use native title bar (removed frameless window flag)
        # This allows the OS to handle the title bar and window controls

        self.db = db_manager or get_database_manager()
        self.material_manager = material_manager or MaterialManager(self.db)
        self.model_format = model_format  # Store model format

        # Initialize logger
        self.logger = get_logger(__name__)

        self._species_records: Dict[str, Dict] = {}

        self._build_ui()
        self._apply_theme_styles()

        # Load species and update UI
        self._load_species()
        if self.species_combo.count() > 0:
            self.species_combo.setCurrentIndex(0)
            self._update_preview_and_properties()

    def _toggle_maximize(self) -> None:
        """Toggle window maximize/restore state."""
        try:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        except Exception:
            pass

    # ---- UI construction ----
    def _build_ui(self) -> None:
        """TODO: Add docstring."""
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
        self.preview_label.setScaledContents(True)
        prev_layout.addWidget(self.preview_label, alignment=Qt.AlignCenter)

        # Material info group (replaces properties for MTL files)
        self.info_group = QGroupBox("Material Information")
        info_layout = QVBoxLayout(self.info_group)
        info_layout.setContentsMargins(10, 10, 10, 10)
        info_layout.setSpacing(8)

        self.material_info_label = QLabel("Select a material to view texture information.")
        self.material_info_label.setWordWrap(True)
        info_layout.addWidget(self.material_info_label)

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
        layout.addWidget(self.info_group)
        layout.addWidget(self.buttons)

    # ---- Data loading and updates ----
    def _load_species(self) -> None:
        """Load only MTL file-based materials, not database wood species."""
        self._species_records.clear()
        self.species_combo.blockSignals(True)
        self.species_combo.clear()

        try:
            # Get MTL file-based materials only (not database wood species)
            mtl_materials = self.material_manager.material_provider.get_available_materials()

            if not mtl_materials:
                self.species_combo.addItem("No MTL materials found", userData=None)
                self.species_combo.blockSignals(False)
                return

            valid_materials = 0
            for material in mtl_materials:
                name = material["name"]
                texture_path = material.get("texture_path")
                mtl_path = material.get("mtl_path")

                # Only show materials that have both MTL file and texture
                if mtl_path and texture_path and mtl_path.exists() and texture_path.exists():
                    # Store material info for later use
                    self.species_combo.addItem(name, userData=name)
                    self._species_records[name] = material
                    valid_materials += 1
                    self.logger.debug(
                        f"Added MTL material '{name}' with texture {texture_path.name}"
                    )
                else:
                    self.logger.debug(f"Skipping material '{name}' - missing MTL or texture file")

            self.logger.info(
                f"Loaded {valid_materials} valid MTL materials (from {len(mtl_materials)} total)"
            )

            if valid_materials == 0:
                self.species_combo.addItem("No valid MTL materials found", userData=None)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to load MTL materials: %s", e)
            self.species_combo.addItem("Error loading materials", userData=None)

        self.species_combo.blockSignals(False)

    def _current_species_name(self) -> Optional[str]:
        """TODO: Add docstring."""
        idx = self.species_combo.currentIndex()
        if idx < 0:
            return None
        return self.species_combo.itemData(idx)

    def get_selected_species(self) -> Optional[str]:
        """Get the currently selected species name."""
        return self._current_species_name()

    def _update_preview_and_properties(self) -> None:
        """TODO: Add docstring."""
        name = self._current_species_name()
        if not name:
            self.preview_label.clear()
            self.material_info_label.setText("Select a material to view texture information.")
            return

        # Update material info for MTL files
        try:
            if self.model_format:
                from src.core.data_structures import ModelFormat

                if self.model_format == ModelFormat.STL:
                    # STL files: Show MTL material properties
                    material = self._species_records.get(name)
                    if material and material.get("mtl_path"):
                        mtl_path = material["mtl_path"]
                        # Parse MTL to show properties
                        mtl_props = self._parse_mtl_for_display(mtl_path)

                        info_text = f"""
                        <b>Material:</b> {name}<br>
                        <b>Model Format:</b> <span style='color: blue;'>STL</span><br>
                        <b>MTL File:</b> {Path(mtl_path).name}<br>
                        <b>Diffuse Color:</b> <span style='color: rgb{mtl_props.get('Kd', (0.8, 0.8, 0.8))}; background-color: rgb{mtl_props.get('Kd', (0.8, 0.8, 0.8))};'>#{int(mtl_props['Kd'][0]*255):02x}{int(mtl_props['Kd'][1]*255):02x}{int(mtl_props['Kd'][2]*255):02x}</span><br>
                        <b>Specular:</b> {mtl_props.get('Ks', (0,0,0))}<br>
                        <b>Shininess:</b> {mtl_props.get('Ns', 10)}<br>
                        <b>Status:</b> <span style='color: green;'>MTL properties applied</span>
                        """
                    else:
                        info_text = f"""
                        <b>Material:</b> {name}<br>
                        <b>Model Format:</b> <span style='color: blue;'>STL</span><br>
                        <b>Status:</b> <span style='color: red;'>No MTL file found</span><br>
                        <i>STL files require MTL files for material properties.</i>
                        """
                else:
                    # OBJ files: Show MTL texture information
                    material = self._species_records.get(name)
                    if material and material.get("texture_path"):
                        texture_path = material["texture_path"]
                        mtl_path = material.get("mtl_path", "N/A")

                        info_text = f"""
                        <b>Material:</b> {name}<br>
                        <b>Model Format:</b> <span style='color: blue;'>OBJ</span><br>
                        <b>Texture File:</b> {texture_path.name}<br>
                        <b>MTL File:</b> {Path(mtl_path).name if mtl_path != 'N/A' else 'N/A'}<br>
                        <b>Status:</b> <span style='color: green;'>Full MTL texture support</span>
                        """
                    else:
                        info_text = f"""
                        <b>Material:</b> {name}<br>
                        <b>Model Format:</b> <span style='color: blue;'>OBJ</span><br>
                        <b>Status:</b> <span style='color: orange;'>No MTL texture found</span><br>
                        <i>OBJ files support full MTL textures with UV mapping.</i>
                        """
            else:
                # Unknown format
                info_text = f"""
                <b>Material:</b> {name}<br>
                <b>Model Format:</b> <span style='color: gray;'>Unknown</span><br>
                <b>Status:</b> <span style='color: orange;'>Cannot determine format</span>
                """

            self.material_info_label.setText(info_text)

            # Update preview (256x256) - this will load the actual MTL texture
            img = self.material_manager.generate_wood_texture(name, size=(256, 256))
            h, w, ch = img.shape
            qimg = QImage(img.data, w, h, ch * w, QImage.Format_RGB888)
            pix = QPixmap.fromImage(qimg)
            self.preview_label.setPixmap(pix)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.preview_label.clear()
            error_text = f"""
            <b>Material:</b> {name}<br>
            <b>Status:</b> <span style='color: red;'>Error loading texture</span><br>
            <b>Error:</b> {str(e)}
            """
            self.material_info_label.setText(error_text)

    def _parse_mtl_for_display(self, mtl_path) -> dict:
        """Parse MTL file to extract properties for display in the UI."""
        material = {
            "Kd": (0.8, 0.8, 0.8),  # diffuse color default
            "Ks": (0.0, 0.0, 0.0),  # specular color default
            "Ns": 10.0,  # shininess default
            "d": 1.0,  # opacity default
        }

        try:
            with open(mtl_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    if line.startswith("Kd "):  # diffuse color
                        parts = line.split()
                        if len(parts) >= 4:
                            material["Kd"] = tuple(map(float, parts[1:4]))
                    elif line.startswith("Ks "):  # specular color
                        parts = line.split()
                        if len(parts) >= 4:
                            material["Ks"] = tuple(map(float, parts[1:4]))
                    elif line.startswith("Ns "):  # shininess
                        parts = line.split()
                        if len(parts) >= 2:
                            material["Ns"] = float(parts[1])
                    elif line.startswith("d "):  # opacity
                        parts = line.split()
                        if len(parts) >= 2:
                            material["d"] = float(parts[1])

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to parse MTL file for display %s: {e}", mtl_path)

        return material

    # ---- Actions ----
    def _on_apply(self) -> None:
        """TODO: Add docstring."""
        name = self._current_species_name()
        if not name:
            QMessageBox.information(self, "No Selection", "Please select a material species.")
            return
        self.material_selected.emit(name)
        self.accept()

    def _open_add_custom_dialog(self) -> None:
        """TODO: Add docstring."""
        dlg = QDialog(self)
        dlg.setWindowTitle("Add Custom Species")
        v = QVBoxLayout(dlg)
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)

        name_edit = QLineEdit()
        base_btn = QPushButton("Pick Base Color")
        grain_btn = QPushButton("Pick Grain Color")

        base_color = QColor(193, 154, 107)  # Oak-ish default
        grain_color = QColor(139, 115, 85)

        def _pick_base() -> None:
            """TODO: Add docstring."""
            nonlocal base_color
            c = QColorDialog.getColor(base_color, self, "Pick Base Color")
            if c.isValid():
                base_color = c

        def _pick_grain() -> None:
            """TODO: Add docstring."""
            nonlocal grain_color
            c = QColorDialog.getColor(grain_color, self, "Pick Grain Color")
            if c.isValid():
                grain_color = c

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

        def _save() -> None:
            """TODO: Add docstring."""
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
            except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                QMessageBox.warning(dlg, "Save Failed", f"Could not save species:\n{e}")

        btns.accepted.connect(_save)
        btns.rejected.connect(dlg.reject)

        dlg.exec_()

    def _style_button(self, button: QPushButton) -> None:
        """Apply qt-material styling to a button."""
        # Qt-material handles styling automatically, no custom stylesheet needed

    def _apply_theme_styles(self) -> None:
        """Apply theme styles to the dialog."""
        # Qt-material handles all styling automatically
