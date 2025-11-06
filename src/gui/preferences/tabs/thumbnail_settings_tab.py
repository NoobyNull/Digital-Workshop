from __future__ import annotations

"""
Preferences dialog with tabbed interface:
- Display
- System
- Files
- Theming (live-apply + persist to AppData)

The Theming tab edits central color variables in gui.theme.COLORS and applies
changes live across the running app. On Save, the current theme is persisted
to AppData and loaded on next startup.
"""

from dataclasses import asdict
from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from src.gui.theme import save_theme_to_settings, set_theme, theme_to_dict
from src.gui.theme.color_helper import get_theme_color


class ThumbnailSettingsTab(QWidget):
    """Thumbnail generation settings tab."""

    def __init__(self, parent=None) -> None:
        """TODO: Add docstring."""
        super().__init__(parent)
        self.logger = None
        try:
            from src.core.logging_config import get_logger

            self.logger = get_logger(__name__)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
            pass
        self._setup_ui()

        self._load_settings()

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
        self.color_preview.setStyleSheet("border: 1px solid #444444; border-radius: 2px;")
        color_h_layout.addWidget(self.color_button)
        color_h_layout.addWidget(self.color_preview)
        color_h_layout.addStretch()
        bg_layout.addLayout(color_h_layout)

        # Background image selection
        img_desc = QLabel("Background Image (optional - click to select):")
        img_desc.setWordWrap(True)
        bg_layout.addWidget(img_desc)

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

        mat_desc = QLabel("Select a material to apply to all thumbnails (click to select):")
        mat_desc.setWordWrap(True)
        mat_layout.addWidget(mat_desc)

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

        # Initialize color to default
        self._bg_color = "#404658"  # Professional dark teal-gray

        # Track selected items
        self.selected_bg_button = None
        self.selected_mat_button = None
        self.bg_buttons = {}
        self.mat_buttons = {}

    def _populate_backgrounds(self) -> None:
        """Populate background grid with clickable image buttons."""
        try:
            # Navigate from src/gui/preferences/tabs to src/resources
            bg_dir = Path(__file__).parent.parent.parent.parent / "resources" / "backgrounds"
            if bg_dir.exists():
                row, col = 0, 0
                max_cols = 4  # 4 images per row

                for bg_file in sorted(bg_dir.glob("*.png")):
                    bg_name = bg_file.stem

                    # Create button with image
                    btn = QPushButton()
                    btn.setFixedSize(100, 100)
                    btn.setToolTip(bg_name)
                    btn.setCheckable(True)
                    btn.setProperty("bg_name", bg_name)

                    # Load and scale image
                    pixmap = QPixmap(str(bg_file))
                    if not pixmap.isNull():
                        scaled = pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                        btn.setIcon(QIcon(scaled))
                        btn.setIconSize(QSize(90, 90))

                    # Style button
                    btn.setStyleSheet("""
                        QPushButton {
                            border: 2px solid #444444;
                            border-radius: 4px;
                            background-color: #2b2b2b;
                        }
                        QPushButton:hover {
                            border: 2px solid #666666;
                        }
                        QPushButton:checked {
                            border: 3px solid #0078d4;
                            background-color: #1e1e1e;
                        }
                    """)

                    # Connect click handler
                    btn.clicked.connect(lambda checked, b=btn: self._on_background_clicked(b))

                    # Add to grid
                    self.bg_grid.addWidget(btn, row, col)
                    self.bg_buttons[bg_name] = btn

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
            none_btn.setStyleSheet("""
                QPushButton {
                    border: 2px solid #444444;
                    border-radius: 4px;
                    background-color: #2b2b2b;
                }
                QPushButton:hover {
                    border: 2px solid #666666;
                }
                QPushButton:checked {
                    border: 3px solid #0078d4;
                    background-color: #1e1e1e;
                }
            """)
            none_btn.clicked.connect(lambda checked, b=none_btn: self._on_material_clicked(b))
            self.mat_grid.addWidget(none_btn, row, col)
            self.mat_buttons[None] = none_btn
            col += 1

            # Navigate from src/gui/preferences/tabs to src/resources
            mat_dir = Path(__file__).parent.parent.parent.parent / "resources" / "materials"
            if mat_dir.exists():
                for mat_file in sorted(mat_dir.glob("*.mtl")):
                    material_name = mat_file.stem

                    # Create button with image
                    btn = QPushButton()
                    btn.setFixedSize(100, 100)
                    btn.setToolTip(material_name)
                    btn.setCheckable(True)
                    btn.setProperty("mat_name", material_name)

                    # Look for material texture image
                    mat_image_path = mat_dir / f"{material_name}.png"
                    if mat_image_path.exists():
                        pixmap = QPixmap(str(mat_image_path))
                        if not pixmap.isNull():
                            scaled = pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                            btn.setIcon(QIcon(scaled))
                            btn.setIconSize(QSize(90, 90))
                    else:
                        # No preview image, show text
                        btn.setText(material_name)

                    # Style button
                    btn.setStyleSheet("""
                        QPushButton {
                            border: 2px solid #444444;
                            border-radius: 4px;
                            background-color: #2b2b2b;
                        }
                        QPushButton:hover {
                            border: 2px solid #666666;
                        }
                        QPushButton:checked {
                            border: 3px solid #0078d4;
                            background-color: #1e1e1e;
                        }
                    """)

                    # Connect click handler
                    btn.clicked.connect(lambda checked, b=btn: self._on_material_clicked(b))

                    # Add to grid
                    self.mat_grid.addWidget(btn, row, col)
                    self.mat_buttons[material_name] = btn

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
            bg_image = settings.value("thumbnail/background_image", config.thumbnail_bg_image, type=str)
            material = settings.value("thumbnail/material", config.thumbnail_material, type=str)
            bg_color = settings.value("thumbnail/background_color", "#404658", type=str)

            if self.logger:
                self.logger.info("Loaded from QSettings: bg={bg_image}, material={material}, color=%s", bg_color)

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
                        self.logger.info("Converting old path format to name: %s -> %s", bg_image, bg_name)
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
                self.logger.error("Failed to load thumbnail settings: %s", e, exc_info=True)

    def _on_background_clicked(self, button: QPushButton) -> None:
        """Handle background button click."""
        try:
            # Uncheck previous selection
            if self.selected_bg_button and self.selected_bg_button != button:
                self.selected_bg_button.setChecked(False)

            # Update selection
            self.selected_bg_button = button
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to handle background click: %s", e)

    def _on_material_clicked(self, button: QPushButton) -> None:
        """Handle material button click."""
        try:
            # Uncheck previous selection
            if self.selected_mat_button and self.selected_mat_button != button:
                self.selected_mat_button.setChecked(False)

            # Update selection
            self.selected_mat_button = button
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to handle material click: %s", e)

    def _on_color_picker_clicked(self) -> None:
        """Handle color picker button click."""
        try:
            current_color = QColor(self._bg_color)
            color = QColorDialog.getColor(
                current_color,
                self,
                "Choose Background Color",
                QColorDialog.ShowAlphaChannel
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
            self.color_preview.setStyleSheet(
                f"background-color: {self._bg_color}; border: 1px solid #444444; border-radius: 2px;"
            )
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to update color preview: %s", e)

    def get_settings(self) -> dict:
        """Get current thumbnail settings."""
        settings = {"background_image": None, "material": None, "background_color": "#404658"}

        try:
            if self.selected_bg_button:
                settings["background_image"] = self.selected_bg_button.property("bg_name")

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
                    f"Attempting to save: bg={settings_dict['background_image']}, material={settings_dict['material']}"
                )

            # Save to QSettings (persistent storage)
            settings.setValue("thumbnail/background_image", settings_dict["background_image"])
            settings.setValue("thumbnail/material", settings_dict["material"])
            settings.setValue("thumbnail/background_color", settings_dict["background_color"])
            settings.sync()  # Force immediate write to disk

            # Also update ApplicationConfig for runtime compatibility
            config.thumbnail_bg_image = settings_dict["background_image"]
            config.thumbnail_material = settings_dict["material"]
            config.thumbnail_bg_color = settings_dict["background_color"]

            if self.logger:
                self.logger.info("✓ Content settings saved to QSettings (persistent)")
                self.logger.info("QSettings thumbnail/background_image = %s", settings_dict['background_image'])
                self.logger.info("QSettings thumbnail/material = %s", settings_dict['material'])
                self.logger.info("QSettings thumbnail/background_color = %s", settings_dict['background_color'])
                self.logger.info("ApplicationConfig also updated for runtime compatibility")
                self.logger.info("=== THUMBNAIL SETTINGS SAVE COMPLETE ===")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to save settings: %s", e, exc_info=True)


