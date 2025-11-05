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

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QFormLayout,
    QFrame,
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
        img_desc = QLabel("Background Image (optional):")
        img_desc.setWordWrap(True)
        bg_layout.addWidget(img_desc)

        # Background list
        self.bg_list = QListWidget()
        self.bg_list.setMaximumHeight(150)
        self._populate_backgrounds()
        bg_layout.addWidget(self.bg_list)

        layout.addWidget(bg_group)

        # Material selection group
        mat_group = QFrame()
        mat_layout = QVBoxLayout(mat_group)

        mat_label = QLabel("<b>Material</b>")
        mat_layout.addWidget(mat_label)

        mat_desc = QLabel("Select a material to apply to all thumbnails:")
        mat_desc.setWordWrap(True)
        mat_layout.addWidget(mat_desc)

        # Material combo
        self.material_combo = QComboBox()
        self._populate_materials()
        mat_layout.addWidget(self.material_combo)

        layout.addWidget(mat_group)

        # Preview group - side by side layout
        preview_group = QFrame()
        preview_layout = QVBoxLayout(preview_group)

        preview_label = QLabel("<b>Preview</b>")
        preview_layout.addWidget(preview_label)

        # Horizontal layout for side-by-side previews
        preview_h_layout = QHBoxLayout()

        # Background preview
        bg_preview_container = QVBoxLayout()
        bg_preview_title = QLabel("Background")
        bg_preview_title.setAlignment(Qt.AlignCenter)
        bg_preview_container.addWidget(bg_preview_title)

        self.preview_label = QLabel()
        self.preview_label.setMinimumHeight(120)
        self.preview_label.setMinimumWidth(120)
        self.preview_label.setAlignment(Qt.AlignCenter)
        # Use theme-aware colors for background and border
        bg_color = get_theme_color('canvas_bg') or '#1E1E1E'
        border_color = get_theme_color('border') or '#444444'
        self.preview_label.setStyleSheet(f"""
            QLabel {{
                border: 1px solid {border_color};
                border-radius: 4px;
                background-color: {bg_color};
            }}
        """)
        bg_preview_container.addWidget(self.preview_label)

        # Material preview
        mat_preview_container = QVBoxLayout()
        mat_preview_title = QLabel("Material")
        mat_preview_title.setAlignment(Qt.AlignCenter)
        mat_preview_container.addWidget(mat_preview_title)

        self.material_preview_label = QLabel()
        self.material_preview_label.setMinimumHeight(120)
        self.material_preview_label.setMinimumWidth(120)
        self.material_preview_label.setAlignment(Qt.AlignCenter)
        self.material_preview_label.setStyleSheet(f"""
            QLabel {{
                border: 1px solid {border_color};
                border-radius: 4px;
                background-color: {bg_color};
            }}
        """)
        mat_preview_container.addWidget(self.material_preview_label)

        preview_h_layout.addLayout(bg_preview_container)
        preview_h_layout.addLayout(mat_preview_container)
        preview_layout.addLayout(preview_h_layout)

        layout.addWidget(preview_group)

        layout.addStretch()

        # Connect signals
        self.bg_list.itemSelectionChanged.connect(self._on_background_selected)
        self.material_combo.currentIndexChanged.connect(self._update_preview)

        # Initialize color to default
        self._bg_color = "#404658"  # Professional dark teal-gray

    def _populate_backgrounds(self) -> None:
        """Populate background list from resources/backgrounds."""
        try:
            # Navigate from src/gui/preferences/tabs to src/resources
            bg_dir = Path(__file__).parent.parent.parent.parent / "resources" / "backgrounds"
            if bg_dir.exists():
                for bg_file in sorted(bg_dir.glob("*.png")):
                    item = QListWidgetItem(bg_file.stem)
                    # Store only the NAME, not the full path
                    item.setData(Qt.UserRole, bg_file.stem)
                    self.bg_list.addItem(item)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to populate backgrounds: %s", e)

    def _populate_materials(self) -> None:
        """Populate material combo from resources/materials."""
        try:
            self.material_combo.addItem("None (Default)", None)

            # Navigate from src/gui/preferences/tabs to src/resources
            mat_dir = Path(__file__).parent.parent.parent.parent / "resources" / "materials"
            if mat_dir.exists():
                for mat_file in sorted(mat_dir.glob("*.mtl")):
                    material_name = mat_file.stem
                    self.material_combo.addItem(material_name, material_name)
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

                for i in range(self.bg_list.count()):
                    item = self.bg_list.item(i)
                    if item.data(Qt.UserRole) == bg_name:
                        self.bg_list.setCurrentItem(item)
                        if self.logger:
                            self.logger.info("✓ Set background to: %s", bg_name)
                        break

            # Load material into UI
            if material:
                idx = self.material_combo.findData(material)
                if idx >= 0:
                    self.material_combo.setCurrentIndex(idx)
                    if self.logger:
                        self.logger.info("✓ Set material to: %s", material)

            self._update_preview()

            if self.logger:
                self.logger.info("=== THUMBNAIL SETTINGS LOAD COMPLETE ===")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to load thumbnail settings: %s", e, exc_info=True)

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

    def _on_background_selected(self) -> None:
        """Handle background selection."""
        self._update_preview()

    def _update_preview(self) -> None:
        """Update preview images for both background and material."""
        try:
            # Update background preview
            current_item = self.bg_list.currentItem()
            if current_item:
                bg_name = current_item.data(Qt.UserRole)
                # Resolve background name to full path
                from src.core.background_provider import BackgroundProvider
                bg_provider = BackgroundProvider()
                try:
                    bg_path = bg_provider.get_background_by_name(bg_name)
                    pixmap = QPixmap(str(bg_path))
                    if not pixmap.isNull():
                        scaled = pixmap.scaledToHeight(120, Qt.SmoothTransformation)
                        self.preview_label.setPixmap(scaled)
                    else:
                        self.preview_label.setText("Error loading\nbackground")
                except FileNotFoundError:
                    self.preview_label.setText("Background\nnot found")
            else:
                self.preview_label.setText("No background\nselected")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to update background preview: %s", e)
            self.preview_label.setText("Error loading\npreview")

        # Update material preview
        try:
            material_name = self.material_combo.currentData()
            if material_name:
                # Look for material texture image
                # Navigate from src/gui/preferences/tabs to src/resources
                mat_dir = Path(__file__).parent.parent.parent.parent / "resources" / "materials"
                mat_image_path = mat_dir / f"{material_name}.png"

                if mat_image_path.exists():
                    pixmap = QPixmap(str(mat_image_path))
                    if not pixmap.isNull():
                        scaled = pixmap.scaledToHeight(120, Qt.SmoothTransformation)
                        self.material_preview_label.setPixmap(scaled)
                        return

                self.material_preview_label.setText(f"{material_name}\n(no preview)")
            else:
                self.material_preview_label.setText("No material\nselected")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to update material preview: %s", e)
            self.material_preview_label.setText("Error loading\nmaterial")

    def get_settings(self) -> dict:
        """Get current thumbnail settings."""
        settings = {"background_image": None, "material": None, "background_color": "#404658"}

        try:
            current_item = self.bg_list.currentItem()
            if current_item:
                settings["background_image"] = current_item.data(Qt.UserRole)

            settings["material"] = self.material_combo.currentData()
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


