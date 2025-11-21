"""
Thumbnail Settings Tab

This tab allows users to configure thumbnail generation settings including:
- Background images (with add/remove functionality)
- Materials (with add/remove functionality)
- Background colors

All settings are saved to QSettings for persistence and automatically synced
to AppData and loaded on next startup.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QColorDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class ThumbnailSettingsTab(QWidget):
    """Thumbnail generation settings tab."""

    def __init__(self, parent=None) -> None:
        """Initialize thumbnail settings tab."""
        super().__init__(parent)
        self.logger = None
        try:
            from src.core.logging_config import get_logger

            self.logger = get_logger(__name__)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
            # Logger initialization is best-effort only; the UI must still function.
            pass

        # Initialize state before building the UI so population helpers can use it safely.
        self._bg_color = "#404658"  # Default background color
        self.selected_bg_button = None
        self.selected_mat_button = None
        self.bg_buttons = {}
        self.mat_buttons = {}
        self.hidden_backgrounds = set()
        self.hidden_materials = set()

        # Load any hidden/default state and then build the UI.
        self._load_hidden_items()
        self._setup_ui()
        self._load_settings()
        self._sync_selection_checks()

    def _apply_selection_style(self, button: QPushButton, selected: bool) -> None:
        """Visual cue for selection without reliance on focus ring."""
        if selected:
            button.setStyleSheet("border: 2px solid #4fa3ff;")
            button.setChecked(True)
        else:
            button.setStyleSheet("")
            button.setChecked(False)

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("Thumbnail Generation Settings")
        header.setWordWrap(True)
        layout.addWidget(header)

        desc = QLabel(
            "Choose background image and material for all generated thumbnails. "
            "These settings apply to all thumbnail generation operations."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Background selection group
        bg_group = QFrame()
        bg_layout = QVBoxLayout(bg_group)

        bg_label = QLabel("<b>Background</b>")
        bg_layout.addWidget(bg_label)

        # Background color selection
        color_desc = QLabel("Background Color:")
        color_desc.setWordWrap(True)
        bg_layout.addWidget(color_desc)

        color_h_layout = QHBoxLayout()
        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self._on_color_picker_clicked)
        self.color_preview = QLabel()
        self.color_preview.setMinimumWidth(40)
        self.color_preview.setMinimumHeight(30)
        # Use native Qt theming; no custom stylesheet.
        color_h_layout.addWidget(self.color_button)
        color_h_layout.addWidget(self.color_preview)
        color_h_layout.addStretch()
        bg_layout.addLayout(color_h_layout)

        # Background image selection
        bg_header_layout = QHBoxLayout()
        img_desc = QLabel("Background Image (optional - click to select):")
        img_desc.setWordWrap(True)
        bg_header_layout.addWidget(img_desc)
        bg_header_layout.addStretch()

        # Add/Remove buttons for backgrounds
        self.add_bg_button = QPushButton("+")
        self.add_bg_button.setFixedSize(30, 30)
        self.add_bg_button.setToolTip("Add new background image")
        self.add_bg_button.clicked.connect(self._on_add_background)
        bg_header_layout.addWidget(self.add_bg_button)

        self.remove_bg_button = QPushButton("-")
        self.remove_bg_button.setFixedSize(30, 30)
        self.remove_bg_button.setToolTip("Remove selected background")
        self.remove_bg_button.clicked.connect(self._on_remove_background)
        bg_header_layout.addWidget(self.remove_bg_button)

        bg_layout.addLayout(bg_header_layout)

        # Background grid with scroll area
        bg_scroll = QScrollArea()
        bg_scroll.setWidgetResizable(True)
        bg_scroll.setMaximumHeight(200)
        bg_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        bg_grid_widget = QWidget()
        self.bg_grid = QGridLayout(bg_grid_widget)
        self.bg_grid.setSpacing(8)
        self._populate_backgrounds()

        bg_scroll.setWidget(bg_grid_widget)
        bg_layout.addWidget(bg_scroll)

        layout.addWidget(bg_group)

        # Material selection group
        mat_group = QFrame()
        mat_layout = QVBoxLayout(mat_group)

        mat_label = QLabel("<b>Material</b>")
        mat_layout.addWidget(mat_label)

        # Material header with add/remove buttons
        mat_header_layout = QHBoxLayout()
        mat_desc = QLabel(
            "Select a material to apply to all thumbnails (click to select):"
        )
        mat_desc.setWordWrap(True)
        mat_header_layout.addWidget(mat_desc)
        mat_header_layout.addStretch()

        # Add/Remove buttons for materials
        self.add_mat_button = QPushButton("+")
        self.add_mat_button.setFixedSize(30, 30)
        self.add_mat_button.setToolTip("Add new material")
        self.add_mat_button.clicked.connect(self._on_add_material)
        mat_header_layout.addWidget(self.add_mat_button)

        self.remove_mat_button = QPushButton("-")
        self.remove_mat_button.setFixedSize(30, 30)
        self.remove_mat_button.setToolTip("Remove selected material")
        self.remove_mat_button.clicked.connect(self._on_remove_material)
        mat_header_layout.addWidget(self.remove_mat_button)

        mat_layout.addLayout(mat_header_layout)

        # Material grid with scroll area
        mat_scroll = QScrollArea()
        mat_scroll.setWidgetResizable(True)
        mat_scroll.setMaximumHeight(200)
        mat_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        mat_grid_widget = QWidget()
        self.mat_grid = QGridLayout(mat_grid_widget)
        self.mat_grid.setSpacing(8)
        self._populate_materials()

        mat_scroll.setWidget(mat_grid_widget)
        mat_layout.addWidget(mat_scroll)

        layout.addWidget(mat_group)

        layout.addStretch()

    def _load_hidden_items(self) -> None:
        """Load hidden backgrounds and materials from settings."""
        try:
            from PySide6.QtCore import QSettings

            settings = QSettings()

            # Load hidden backgrounds
            hidden_bg = settings.value("thumbnail/hidden_backgrounds", [])
            if isinstance(hidden_bg, list):
                self.hidden_backgrounds = set(hidden_bg)

            # Load hidden materials
            hidden_mat = settings.value("thumbnail/hidden_materials", [])
            if isinstance(hidden_mat, list):
                self.hidden_materials = set(hidden_mat)

            if self.logger:
                self.logger.info(
                    "Loaded hidden items: %d backgrounds, %d materials",
                    len(self.hidden_backgrounds),
                    len(self.hidden_materials),
                )
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to load hidden items: %s", e)

    def _save_hidden_items(self) -> None:
        """Save hidden backgrounds and materials to settings."""
        try:
            from PySide6.QtCore import QSettings

            settings = QSettings()

            settings.setValue(
                "thumbnail/hidden_backgrounds", list(self.hidden_backgrounds)
            )
            settings.setValue("thumbnail/hidden_materials", list(self.hidden_materials))

            if self.logger:
                self.logger.info(
                    "Saved hidden items: %d backgrounds, %d materials",
                    len(self.hidden_backgrounds),
                    len(self.hidden_materials),
                )
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to save hidden items: %s", e)

    def _populate_backgrounds(self) -> None:
        """Populate background grid with clickable image buttons."""
        try:
            # Navigate from src/gui/preferences/tabs to src/resources
            bg_dir = (
                Path(__file__).parent.parent.parent.parent / "resources" / "backgrounds"
            )
            if bg_dir.exists():
                row, col = 0, 0
                max_cols = 4  # 4 images per row

                for bg_file in sorted(bg_dir.glob("*.png")):
                    bg_name = bg_file.stem

                    # Skip hidden backgrounds
                    if bg_name in self.hidden_backgrounds:
                        continue

                    # Create button with image
                    btn = QPushButton()
                    btn.setFixedSize(100, 100)
                    btn.setToolTip(bg_name)
                    btn.setCheckable(True)
                    btn.setProperty("bg_name", bg_name)
                    btn.setProperty(
                        "is_default", True
                    )  # Mark as default (shipped with app)
                    btn.setFocusPolicy(Qt.NoFocus)

                    # Load and scale image
                    pixmap = QPixmap(str(bg_file))
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(
                            90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation
                        )
                        btn.setIcon(QIcon(scaled))
                        btn.setIconSize(QSize(90, 90))

                    # Use native Qt theming; no custom stylesheet.

                    # Connect click handler
                    btn.clicked.connect(
                        lambda checked, b=btn: self._on_background_clicked(b)
                    )

                    # Add to grid
                    self.bg_grid.addWidget(btn, row, col)
                    self.bg_buttons[bg_name] = btn
                    # Initial visual state
                    self._apply_selection_style(btn, False)

                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to populate backgrounds: %s", e)

    def _populate_materials(self) -> None:
        """Populate material grid with clickable image buttons."""
        try:
            row, col = 0, 0
            max_cols = 4  # 4 images per row

            # Add "None" option first
            none_btn = QPushButton("None\n(Default)")
            none_btn.setFixedSize(100, 100)
            none_btn.setCheckable(True)
            none_btn.setProperty("mat_name", None)
            none_btn.setFocusPolicy(Qt.NoFocus)
            # Use native Qt theming; no custom stylesheet.
            none_btn.clicked.connect(
                lambda checked, b=none_btn: self._on_material_clicked(b)
            )
            self.mat_grid.addWidget(none_btn, row, col)
            self.mat_buttons[None] = none_btn
            self._apply_selection_style(none_btn, False)
            col += 1

            # Navigate from src/gui/preferences/tabs to src/resources
            mat_dir = (
                Path(__file__).parent.parent.parent.parent / "resources" / "materials"
            )
            if mat_dir.exists():
                for mat_file in sorted(mat_dir.glob("*.mtl")):
                    material_name = mat_file.stem

                    # Skip hidden materials
                    if material_name in self.hidden_materials:
                        continue

                    # Create button with image
                    btn = QPushButton()
                    btn.setFixedSize(100, 100)
                    btn.setToolTip(material_name)
                    btn.setCheckable(True)
                    btn.setProperty("mat_name", material_name)
                    btn.setProperty(
                        "is_default", True
                    )  # Mark as default (shipped with app)
                    btn.setFocusPolicy(Qt.NoFocus)

                    # Look for material texture image
                    mat_image_path = mat_dir / f"{material_name}.png"
                    if mat_image_path.exists():
                        pixmap = QPixmap(str(mat_image_path))
                        if not pixmap.isNull():
                            scaled = pixmap.scaled(
                                90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation
                            )
                            btn.setIcon(QIcon(scaled))
                            btn.setIconSize(QSize(90, 90))
                    else:
                        # No preview image, show text
                        btn.setText(material_name)

                    # Use native Qt theming; no custom stylesheet.

                    # Connect click handler
                    btn.clicked.connect(
                        lambda checked, b=btn: self._on_material_clicked(b)
                    )

                    # Add to grid
                    self.mat_grid.addWidget(btn, row, col)
                    self.mat_buttons[material_name] = btn
                    self._apply_selection_style(btn, False)

                    col += 1
                    if col >= max_cols:
                        col = 0
                        row += 1

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to populate materials: %s", e)

    def _load_settings(self) -> None:
        """Load current settings from QSettings with fallback to
        ApplicationConfig."""
        try:
            from PySide6.QtCore import QSettings

            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()
            settings = QSettings()

            if self.logger:
                self.logger.info("=== THUMBNAIL SETTINGS LOAD ===")

            # Load from QSettings with fallback to ApplicationConfig
            bg_image = settings.value(
                "thumbnail/background_image", config.thumbnail_bg_image, type=str
            )
            material = settings.value(
                "thumbnail/material", config.thumbnail_material, type=str
            )
            bg_color = settings.value("thumbnail/background_color", "#404658", type=str)

            if self.logger:
                self.logger.info(
                    "Loaded from QSettings: bg={bg_image}, material={material}, color=%s",
                    bg_color,
                )

            # Update ApplicationConfig for runtime compatibility
            if bg_image:
                config.thumbnail_bg_image = bg_image
            if material:
                config.thumbnail_material = material

            # Set background color
            self._bg_color = bg_color
            self._update_color_preview()

            # Load background into UI
            if bg_image:
                # Handle both old format (full path) and new format (name only)
                # Extract name from path if it's a full path
                if "/" in bg_image or "\\" in bg_image:
                    # Old format: full path like "D:\...\Brick.png"
                    bg_name = Path(bg_image).stem
                    if self.logger:
                        self.logger.info(
                            "Converting old path format to name: %s -> %s",
                            bg_image,
                            bg_name,
                        )
                else:
                    # New format: just the name like "Brick"
                    bg_name = bg_image

                # Find and select the button
                if bg_name in self.bg_buttons:
                    btn = self.bg_buttons[bg_name]
                    btn.setChecked(True)
                    self.selected_bg_button = btn
                    if self.logger:
                        self.logger.info("✓ Set background to: %s", bg_name)

            # Load material into UI
            if material:
                if material in self.mat_buttons:
                    btn = self.mat_buttons[material]
                    btn.setChecked(True)
                    self.selected_mat_button = btn
                    if self.logger:
                        self.logger.info("✓ Set material to: %s", material)
            else:
                # Select "None" by default
                if None in self.mat_buttons:
                    btn = self.mat_buttons[None]
                    btn.setChecked(True)
                    self.selected_mat_button = btn

            if self.logger:
                self.logger.info("=== THUMBNAIL SETTINGS LOAD COMPLETE ===")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error(
                    "Failed to load thumbnail settings: %s", e, exc_info=True
                )

    def _on_background_clicked(self, button: QPushButton) -> None:
        """Handle background button click."""
        try:
            # Uncheck previous selection
            if self.selected_bg_button and self.selected_bg_button != button:
                self._apply_selection_style(self.selected_bg_button, False)

            # Update selection
            self.selected_bg_button = button
            self._sync_selection_checks()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to handle background click: %s", e)

    def _on_material_clicked(self, button: QPushButton) -> None:
        """Handle material button click."""
        try:
            # Uncheck previous selection
            if self.selected_mat_button and self.selected_mat_button != button:
                self._apply_selection_style(self.selected_mat_button, False)

            # Update selection
            self.selected_mat_button = button
            self._sync_selection_checks()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to handle material click: %s", e)

    def _on_add_background(self) -> None:
        """Handle adding a new background image."""
        try:
            from PySide6.QtWidgets import QFileDialog

            # Open file dialog to select image
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Select Background Image", "", "Images (*.png *.jpg *.jpeg *.bmp)"
            )

            if file_path:
                # Copy to backgrounds directory
                bg_dir = (
                    Path(__file__).parent.parent.parent.parent
                    / "resources"
                    / "backgrounds"
                )
                bg_dir.mkdir(parents=True, exist_ok=True)

                source = Path(file_path)
                dest = bg_dir / source.name

                # Check if file already exists
                if dest.exists():
                    reply = QMessageBox.question(
                        self,
                        "File Exists",
                        f"Background '{source.stem}' already exists. Replace it?",
                        QMessageBox.Yes | QMessageBox.No,
                    )
                    if reply == QMessageBox.No:
                        return

                # Copy file
                import shutil

                shutil.copy2(source, dest)

                # Refresh the grid
                self._refresh_backgrounds()

                if self.logger:
                    self.logger.info("Added background: %s", source.stem)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to add background: %s", e)

    def _on_remove_background(self) -> None:
        """Handle removing/hiding a background."""
        try:
            if not self.selected_bg_button:
                QMessageBox.information(
                    self, "No Selection", "Please select a background to remove."
                )
                return

            bg_name = self.selected_bg_button.property("bg_name")
            is_default = self.selected_bg_button.property("is_default")

            if is_default:
                # Hide default backgrounds (don't delete)
                self.hidden_backgrounds.add(bg_name)
                self._save_hidden_items()

                if self.logger:
                    self.logger.info("Hidden default background: %s", bg_name)
            else:
                # Delete user-added backgrounds
                reply = QMessageBox.question(
                    self,
                    "Delete Background",
                    f"Permanently delete background '{bg_name}'?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    bg_dir = (
                        Path(__file__).parent.parent.parent.parent
                        / "resources"
                        / "backgrounds"
                    )
                    bg_file = bg_dir / f"{bg_name}.png"
                    if bg_file.exists():
                        bg_file.unlink()

                    if self.logger:
                        self.logger.info("Deleted background: %s", bg_name)

            # Refresh the grid
            self._refresh_backgrounds()
            self.selected_bg_button = None
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to remove background: %s", e)

    def _on_add_material(self) -> None:
        """Handle adding a new material."""
        try:
            from PySide6.QtWidgets import QFileDialog

            # Open file dialog to select MTL file
            mtl_path, _ = QFileDialog.getOpenFileName(
                self, "Select Material File (.mtl)", "", "Material Files (*.mtl)"
            )

            if not mtl_path:
                return

            # Ask for optional texture image
            QMessageBox.information(
                self,
                "Select Texture",
                "Now select an optional texture image (PNG) for the material preview.\n\n"
                "Click Cancel if you don't have a texture image.",
            )

            texture_path, _ = QFileDialog.getOpenFileName(
                self, "Select Texture Image (optional)", "", "Images (*.png)"
            )

            # Copy to materials directory
            mat_dir = (
                Path(__file__).parent.parent.parent.parent / "resources" / "materials"
            )
            mat_dir.mkdir(parents=True, exist_ok=True)

            source_mtl = Path(mtl_path)
            dest_mtl = mat_dir / source_mtl.name

            # Check if material already exists
            if dest_mtl.exists():
                reply = QMessageBox.question(
                    self,
                    "File Exists",
                    f"Material '{source_mtl.stem}' already exists. Replace it?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.No:
                    return

            # Copy MTL file
            import shutil

            shutil.copy2(source_mtl, dest_mtl)

            # Copy texture if provided
            if texture_path:
                source_texture = Path(texture_path)
                dest_texture = mat_dir / f"{source_mtl.stem}.png"
                shutil.copy2(source_texture, dest_texture)

            # Refresh the grid
            self._refresh_materials()

            if self.logger:
                self.logger.info("Added material: %s", source_mtl.stem)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to add material: %s", e)

    def _on_remove_material(self) -> None:
        """Handle removing/hiding a material."""
        try:
            if not self.selected_mat_button:
                QMessageBox.information(
                    self, "No Selection", "Please select a material to remove."
                )
                return

            mat_name = self.selected_mat_button.property("mat_name")

            # Can't remove "None" option
            if mat_name is None:
                QMessageBox.information(
                    self, "Cannot Remove", "The 'None' option cannot be removed."
                )
                return

            is_default = self.selected_mat_button.property("is_default")

            if is_default:
                # Hide default materials (don't delete)
                self.hidden_materials.add(mat_name)
                self._save_hidden_items()

                if self.logger:
                    self.logger.info("Hidden default material: %s", mat_name)
            else:
                # Delete user-added materials
                reply = QMessageBox.question(
                    self,
                    "Delete Material",
                    f"Permanently delete material '{mat_name}'?",
                    QMessageBox.Yes | QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    mat_dir = (
                        Path(__file__).parent.parent.parent.parent
                        / "resources"
                        / "materials"
                    )
                    mtl_file = mat_dir / f"{mat_name}.mtl"
                    png_file = mat_dir / f"{mat_name}.png"

                    if mtl_file.exists():
                        mtl_file.unlink()
                    if png_file.exists():
                        png_file.unlink()

                    if self.logger:
                        self.logger.info("Deleted material: %s", mat_name)

            # Refresh the grid
            self._refresh_materials()
            self.selected_mat_button = None
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to remove material: %s", e)

    def _refresh_backgrounds(self) -> None:
        """Refresh the background grid."""
        try:
            # Clear existing buttons
            for i in reversed(range(self.bg_grid.count())):
                widget = self.bg_grid.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            self.bg_buttons.clear()
            self.selected_bg_button = None

            # Repopulate
            self._populate_backgrounds()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to refresh backgrounds: %s", e)

    def _refresh_materials(self) -> None:
        """Refresh the material grid."""
        try:
            # Clear existing buttons
            for i in reversed(range(self.mat_grid.count())):
                widget = self.mat_grid.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            self.mat_buttons.clear()
            self.selected_mat_button = None

            # Repopulate
            self._populate_materials()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to refresh materials: %s", e)

    def _on_color_picker_clicked(self) -> None:
        """Handle color picker button click."""
        try:
            current_color = QColor(self._bg_color)
            color = QColorDialog.getColor(
                current_color,
                self,
                "Choose Background Color",
                QColorDialog.ShowAlphaChannel,
            )
            if color.isValid():
                self._bg_color = color.name()
                self._update_color_preview()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to pick color: %s", e)

    def _update_color_preview(self) -> None:
        """Update the color preview button."""
        try:
            # Use native Qt theming only; avoid custom stylesheet strings.
            # We still reflect the chosen color via QPalette so users get feedback
            # without hard-coding full widget styles.
            palette = self.color_preview.palette()
            palette.setColor(
                self.color_preview.backgroundRole(), QColor(self._bg_color)
            )
            self.color_preview.setAutoFillBackground(True)
            self.color_preview.setPalette(palette)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to update color preview: %s", e)

    def _sync_selection_checks(self) -> None:
        """Ensure current selections stay visually checked."""
        if self.selected_bg_button:
            self._apply_selection_style(self.selected_bg_button, True)
        if self.selected_mat_button:
            self._apply_selection_style(self.selected_mat_button, True)

    def get_settings(self) -> dict:
        """Get current thumbnail settings."""
        settings = {
            "background_image": None,
            "material": None,
            "background_color": "#404658",
        }

        try:
            if self.selected_bg_button:
                settings["background_image"] = self.selected_bg_button.property(
                    "bg_name"
                )

            if self.selected_mat_button:
                settings["material"] = self.selected_mat_button.property("mat_name")

            settings["background_color"] = self._bg_color
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to get settings: %s", e)

        return settings

    def save_settings(self) -> None:
        """Save thumbnail settings to QSettings for persistence."""
        try:
            from PySide6.QtCore import QSettings

            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()
            settings = QSettings()  # Use QSettings for persistence
            settings_dict = self.get_settings()

            if self.logger:
                self.logger.info("=== THUMBNAIL SETTINGS SAVE ===")
                self.logger.info(
                    "Attempting to save: bg=%s, material=%s",
                    settings_dict["background_image"],
                    settings_dict["material"],
                )

            # Save to QSettings (persistent storage). We intentionally avoid an
            # explicit sync() call here to keep the UI responsive even when the
            # backing store is slow (e.g. network paths). QSettings will flush
            # changes automatically.
            settings.setValue(
                "thumbnail/background_image", settings_dict["background_image"]
            )
            settings.setValue("thumbnail/material", settings_dict["material"])
            settings.setValue(
                "thumbnail/background_color", settings_dict["background_color"]
            )

            # Also update ApplicationConfig for runtime compatibility
            config.thumbnail_bg_image = settings_dict["background_image"]
            config.thumbnail_material = settings_dict["material"]
            config.thumbnail_bg_color = settings_dict["background_color"]

            if self.logger:
                self.logger.info("✓ Content settings saved to QSettings (persistent)")
                self.logger.info(
                    "QSettings thumbnail/background_image = %s",
                    settings_dict["background_image"],
                )
                self.logger.info(
                    "QSettings thumbnail/material = %s", settings_dict["material"]
                )
                self.logger.info(
                    "QSettings thumbnail/background_color = %s",
                    settings_dict["background_color"],
                )
                self.logger.info(
                    "ApplicationConfig also updated for runtime compatibility"
                )
                self.logger.info("=== THUMBNAIL SETTINGS SAVE COMPLETE ===")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to save settings: %s", e, exc_info=True)
