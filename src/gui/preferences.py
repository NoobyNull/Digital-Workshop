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
from typing import Dict, List, Callable
from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QIcon, QPixmap
from PySide6.QtWidgets import (
    QDialog, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QLineEdit, QColorDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QSpacerItem, QSizePolicy, QMessageBox, QCheckBox,
    QComboBox, QListWidget, QListWidgetItem, QScrollArea, QSlider, QInputDialog
)

from src.gui.theme import (
    COLORS,
    set_theme, save_theme_to_settings, theme_to_dict, color as color_hex, hex_to_rgb
)
from src.gui.files_tab import FilesTab


class PreferencesDialog(QDialog):
    """
    Application preferences dialog with multiple tabs.
    Emits theme_changed whenever the Theming tab applies updates.
    """
    theme_changed = Signal()

    def __init__(self, parent=None, on_reset_layout=None):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setModal(True)
        self.setMinimumWidth(560)
        self.on_reset_layout = on_reset_layout

        # Remove native title bar and frame - we'll use custom title bar
        # Use native title bar (removed frameless window flag)
        # This allows the OS to handle the title bar and window controls

        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        # Create tabs in logical order
        self.window_layout_tab = WindowLayoutTab(on_reset_layout=self.on_reset_layout)
        self.theming_tab = ThemingTab(on_live_apply=self._on_theme_live_applied)
        self.thumbnail_settings_tab = ThumbnailSettingsTab()
        self.performance_tab = PerformanceSettingsTab()
        self.files_tab = FilesTab()
        self.advanced_tab = AdvancedTab()

        # Add tabs in logical order: UI → Content → System → Advanced
        self.tabs.addTab(self.window_layout_tab, "Window & Layout")
        self.tabs.addTab(self.theming_tab, "Theming")
        self.tabs.addTab(self.thumbnail_settings_tab, "Thumbnail Settings")
        self.tabs.addTab(self.performance_tab, "Performance")
        self.tabs.addTab(self.files_tab, "Files")
        self.tabs.addTab(self.advanced_tab, "Advanced")

        # Dialog action buttons
        buttons_row = QHBoxLayout()
        buttons_row.addStretch(1)

        self.btn_reset = QPushButton("Reset to Defaults")
        self.btn_save = QPushButton("Save")
        self.btn_close = QPushButton("Close")

        buttons_row.addWidget(self.btn_reset)
        buttons_row.addWidget(self.btn_save)
        buttons_row.addWidget(self.btn_close)

        layout.addLayout(buttons_row)

        # Wire actions
        self.btn_close.clicked.connect(self.reject)
        self.btn_save.clicked.connect(self._save_and_notify)
        self.btn_reset.clicked.connect(self._reset_to_defaults)

    def _toggle_maximize(self) -> None:
        """Toggle window maximize/restore state."""
        try:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        except Exception:
            pass

    def _on_theme_live_applied(self):
        # Bubble up to MainWindow so it can re-render stylesheets on key widgets
        self.theme_changed.emit()

    def _save_and_notify(self):
        try:
            save_theme_to_settings()

            # Save thumbnail settings
            if hasattr(self, 'thumbnail_settings_tab'):
                self.thumbnail_settings_tab.save_settings()

            # Save performance settings
            if hasattr(self, 'performance_tab'):
                self.performance_tab.save_settings()

            QMessageBox.information(self, "Saved", "All settings saved successfully.")
        except Exception as e:
            QMessageBox.warning(self, "Save Failed", f"Failed to save settings:\n{e}")

    def _reset_to_defaults(self):
        # Build defaults from the dataclass defaults
        try:
            # Get default values from the ThemeDefaults dataclass
            from src.gui.theme import ThemeDefaults
            default_map = asdict(ThemeDefaults())
        except Exception:
            # Fallback: if introspection doesn't work cross-runtime, use initial theme_to_dict()
            default_map = theme_to_dict()
        set_theme(default_map)
        self.theming_tab.reload_from_current()
        self._on_theme_live_applied()


class ThemingTab(QWidget):
    """
    Simplified theming tab with Material Design theme selection.

    Provides options to select:
    - Theme mode: Dark, Light, or Auto (system)
    - Material Design color variant
    """

    def __init__(self, on_live_apply=None, parent=None):
        super().__init__(parent)
        self.on_live_apply = on_live_apply
        self.service = None
        self._setup_ui()



    def _setup_ui(self):
        """Setup simplified theming UI with Material Design theme selector."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        hdr = QLabel("Select your preferred theme mode and color variant.")
        hdr.setWordWrap(True)
        layout.addWidget(hdr)

        # Qt-Material theme selector
        self._setup_material_theme_selector(layout)

        # Add stretch to push everything to the top
        layout.addStretch()

        # Apply theme styling
        self._apply_theme_styling()

    def _setup_material_theme_selector(self, parent_layout: QVBoxLayout) -> None:
        """Setup qt-material theme mode and variant selector."""
        try:
            from src.gui.theme.simple_service import ThemeService
            self.service = ThemeService.instance()

            # Material theme group
            mat_group = QFrame()
            mat_layout = QVBoxLayout(mat_group)
            mat_layout.setContentsMargins(0, 0, 0, 0)

            mat_label = QLabel("<b>Qt-Material Theme</b>")
            mat_layout.addWidget(mat_label)

            # Theme mode selector (Dark/Light/Auto)
            mode_layout = QHBoxLayout()
            mode_layout.addWidget(QLabel("Mode:"))

            self.mode_combo = QComboBox()
            self.mode_combo.addItem("Dark", "dark")
            self.mode_combo.addItem("Light", "light")
            self.mode_combo.addItem("Auto (System)", "auto")

            # Set current mode
            current_theme, _ = self.service.get_current_theme()
            self.mode_combo.setCurrentIndex({"dark": 0, "light": 1, "auto": 2}.get(current_theme, 0))
            self.mode_combo.currentIndexChanged.connect(self._on_theme_mode_changed)

            mode_layout.addWidget(self.mode_combo)
            mode_layout.addStretch()
            mat_layout.addLayout(mode_layout)

            # Variant selector
            mat_desc = QLabel("Select a Material Design color variant:")
            mat_desc.setWordWrap(True)
            mat_layout.addWidget(mat_desc)

            variant_layout = QHBoxLayout()
            variant_layout.addWidget(QLabel("Variant:"))

            self.variant_combo = QComboBox()
            self._populate_material_variants()
            self.variant_combo.currentTextChanged.connect(self._on_material_variant_changed)
            variant_layout.addWidget(self.variant_combo)
            variant_layout.addStretch()

            mat_layout.addLayout(variant_layout)
            parent_layout.addWidget(mat_group)

        except Exception as e:
            # Silently fail if ThemeService not available
            pass

    def _populate_material_variants(self) -> None:
        """Populate material variant combo."""
        try:
            if not self.service:
                return

            self.variant_combo.blockSignals(True)
            self.variant_combo.clear()

            # Get current theme type
            theme_type, _ = self.service.get_current_theme()
            variants = self.service.get_qt_material_variants(theme_type)

            for variant in variants:
                # Extract color name from variant (e.g., "dark_blue" -> "blue")
                color_name = variant.split("_", 1)[1] if "_" in variant else variant
                self.variant_combo.addItem(color_name.title(), variant)

            self.variant_combo.blockSignals(False)
        except Exception:
            pass

    def _apply_theme_styling(self) -> None:
        """Apply theme styling (no-op - qt-material handles this)."""
        pass

    def _on_theme_mode_changed(self, index: int) -> None:
        """Handle theme mode change (Dark/Light/Auto)."""
        try:
            if not self.service:
                return

            mode = self.mode_combo.itemData(index)
            if not mode:
                return

            # Apply the new theme mode
            self.service.apply_theme(mode, "qt-material")

            # Update variant selector to show correct variants for new mode
            self._populate_material_variants()

            # Reapply styling to this tab
            self._apply_theme_styling()

            # Notify parent of theme change
            if callable(self.on_live_apply):
                self.on_live_apply()
        except Exception:
            pass

    def _on_material_variant_changed(self, variant_name: str) -> None:
        """Handle material variant change."""
        try:
            if not self.service or not variant_name:
                return

            # Set the variant and apply theme
            self.service.set_qt_material_variant(variant_name.lower())
            current_theme, _ = self.service.get_current_theme()
            self.service.apply_theme(current_theme, "qt-material")

            # Reapply styling to this tab
            self._apply_theme_styling()

            # Notify parent of theme change
            if callable(self.on_live_apply):
                self.on_live_apply()
        except Exception:
            pass




class WindowLayoutTab(QWidget):
    """Window and layout settings tab: reset window/dock layout."""
    def __init__(self, on_reset_layout: Callable | None = None, parent=None):
        super().__init__(parent)
        self.on_reset_layout = on_reset_layout
        layout = QVBoxLayout(self)

        header = QLabel("Window Layout and Docking")
        header.setWordWrap(True)
        layout.addWidget(header)

        desc = QLabel("Layout auto-saves when you move or dock panels. Use 'Reset Window Layout' to restore defaults.")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Actions row
        row = QHBoxLayout()
        row.addStretch(1)
        self.btn_reset_layout = QPushButton("Reset Window Layout")
        row.addWidget(self.btn_reset_layout)
        layout.addLayout(row)

        self.btn_reset_layout.clicked.connect(self._handle_reset)

        layout.addStretch(1)

    def _handle_reset(self):
        try:
            if callable(self.on_reset_layout):
                self.on_reset_layout()
                QMessageBox.information(self, "Layout Reset", "Window layout has been reset to defaults.")
        except Exception as e:
            QMessageBox.warning(self, "Reset Failed", f"Failed to reset layout:\n{e}")


class ThumbnailSettingsTab(QWidget):
    """Thumbnail generation settings tab."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = None
        try:
            from src.core.logging_config import get_logger
            self.logger = get_logger(__name__)
        except Exception:
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

        bg_label = QLabel("<b>Background Image</b>")
        bg_layout.addWidget(bg_label)

        bg_desc = QLabel("Select a background image for thumbnails:")
        bg_desc.setWordWrap(True)
        bg_layout.addWidget(bg_desc)

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

        # Preview group
        preview_group = QFrame()
        preview_layout = QVBoxLayout(preview_group)

        preview_label = QLabel("<b>Preview</b>")
        preview_layout.addWidget(preview_label)

        self.preview_label = QLabel()
        self.preview_label.setMinimumHeight(100)
        self.preview_label.setAlignment(Qt.AlignCenter)
        preview_layout.addWidget(self.preview_label)

        layout.addWidget(preview_group)

        layout.addStretch()

        # Connect signals
        self.bg_list.itemSelectionChanged.connect(self._on_background_selected)
        self.material_combo.currentIndexChanged.connect(self._update_preview)

    def _populate_backgrounds(self) -> None:
        """Populate background list from resources/backgrounds."""
        try:
            bg_dir = Path(__file__).parent.parent / "resources" / "backgrounds"
            if bg_dir.exists():
                for bg_file in sorted(bg_dir.glob("*.png")):
                    item = QListWidgetItem(bg_file.stem)
                    item.setData(Qt.UserRole, str(bg_file))
                    self.bg_list.addItem(item)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to populate backgrounds: {e}")

    def _populate_materials(self) -> None:
        """Populate material combo from resources/materials."""
        try:
            self.material_combo.addItem("None (Default)", None)

            mat_dir = Path(__file__).parent.parent / "resources" / "materials"
            if mat_dir.exists():
                for mat_file in sorted(mat_dir.glob("*.mtl")):
                    material_name = mat_file.stem
                    self.material_combo.addItem(material_name, material_name)
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to populate materials: {e}")

    def _load_settings(self) -> None:
        """Load current settings."""
        try:
            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()

            # Load background
            if config.thumbnail_bg_image:
                for i in range(self.bg_list.count()):
                    item = self.bg_list.item(i)
                    if item.data(Qt.UserRole) == config.thumbnail_bg_image:
                        self.bg_list.setCurrentItem(item)
                        break

            # Load material
            if config.thumbnail_material:
                idx = self.material_combo.findData(config.thumbnail_material)
                if idx >= 0:
                    self.material_combo.setCurrentIndex(idx)

            self._update_preview()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load settings: {e}")

    def _on_background_selected(self) -> None:
        """Handle background selection."""
        self._update_preview()

    def _update_preview(self) -> None:
        """Update preview image."""
        try:
            current_item = self.bg_list.currentItem()
            if current_item:
                bg_path = current_item.data(Qt.UserRole)
                pixmap = QPixmap(bg_path)
                if not pixmap.isNull():
                    scaled = pixmap.scaledToHeight(
                        100, Qt.SmoothTransformation
                    )
                    self.preview_label.setPixmap(scaled)
                    return

            self.preview_label.setText("No background selected")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to update preview: {e}")
            self.preview_label.setText("Error loading preview")

    def get_settings(self) -> dict:
        """Get current thumbnail settings."""
        settings = {
            "background_image": None,
            "material": None
        }

        try:
            current_item = self.bg_list.currentItem()
            if current_item:
                settings["background_image"] = current_item.data(Qt.UserRole)

            settings["material"] = self.material_combo.currentData()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to get settings: {e}")

        return settings

    def save_settings(self) -> None:
        """Save thumbnail settings to application config."""
        try:
            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()
            settings = self.get_settings()

            config.thumbnail_bg_image = settings["background_image"]
            config.thumbnail_material = settings["material"]

            if self.logger:
                self.logger.info(
                    f"Saved thumbnail settings: "
                    f"bg={settings['background_image']}, "
                    f"material={settings['material']}"
                )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save settings: {e}")

class PerformanceSettingsTab(QWidget):
    """Performance settings tab for memory allocation and system optimization."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = None
        try:
            from src.core.logging_config import get_logger
            self.logger = get_logger(__name__)
        except Exception:
            pass
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Set up the performance settings UI."""
        layout = QVBoxLayout(self)

        # Header
        header = QLabel("<b>Memory Allocation Settings</b>")
        layout.addWidget(header)

        desc = QLabel(
            "Configure how much system memory the application can use. "
            "Smart calculation: min(doubled_minimum, 50% available, total - 20%)"
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Mode selection group
        mode_group = QFrame()
        mode_layout = QVBoxLayout(mode_group)

        mode_label = QLabel("<b>Memory Mode</b>")
        mode_layout.addWidget(mode_label)

        self.auto_radio = QCheckBox("Auto (Smart Calculation)")
        self.auto_radio.setChecked(True)
        mode_layout.addWidget(self.auto_radio)

        self.manual_radio = QCheckBox("Manual Override")
        mode_layout.addWidget(self.manual_radio)

        layout.addWidget(mode_group)

        # Manual override group
        override_group = QFrame()
        override_layout = QVBoxLayout(override_group)

        override_label = QLabel("<b>Manual Memory Limit (MB)</b>")
        override_layout.addWidget(override_label)

        slider_layout = QHBoxLayout()
        self.memory_slider = QSlider(Qt.Horizontal)
        self.memory_slider.setMinimum(512)
        self.memory_slider.setMaximum(4096)
        self.memory_slider.setValue(1024)
        self.memory_slider.setTickPosition(QSlider.TicksBelow)
        self.memory_slider.setTickInterval(512)
        slider_layout.addWidget(self.memory_slider)

        self.memory_value_label = QLabel("1024 MB")
        self.memory_value_label.setMinimumWidth(80)
        slider_layout.addWidget(self.memory_value_label)

        override_layout.addLayout(slider_layout)
        layout.addWidget(override_group)

        # System info group
        info_group = QFrame()
        info_layout = QVBoxLayout(info_group)

        info_label = QLabel("<b>System Information</b>")
        info_layout.addWidget(info_label)

        self.system_info_label = QLabel()
        self.system_info_label.setWordWrap(True)
        info_layout.addWidget(self.system_info_label)

        layout.addWidget(info_group)

        layout.addStretch()

        # Connect signals
        self.auto_radio.toggled.connect(self._on_mode_changed)
        self.manual_radio.toggled.connect(self._on_mode_changed)
        self.memory_slider.valueChanged.connect(self._on_slider_changed)

        # Update system info
        self._update_system_info()

    def _on_mode_changed(self) -> None:
        """Handle mode change."""
        is_manual = self.manual_radio.isChecked()
        self.memory_slider.setEnabled(is_manual)
        self._update_system_info()

    def _on_slider_changed(self, value: int) -> None:
        """Handle slider change."""
        self.memory_value_label.setText(f"{value} MB")
        self._update_system_info()

    def _update_system_info(self) -> None:
        """Update system information display."""
        try:
            import psutil
            from src.core.application_config import ApplicationConfig

            memory = psutil.virtual_memory()
            total_mb = int(memory.total / (1024 ** 2))
            available_mb = int(memory.available / (1024 ** 2))

            config = ApplicationConfig.get_default()

            if self.manual_radio.isChecked():
                limit_mb = self.memory_slider.value()
                info_text = (
                    f"Manual Override: {limit_mb} MB\n"
                    f"System Total: {total_mb} MB\n"
                    f"Available: {available_mb} MB\n"
                    f"Reserve: {config.system_memory_reserve_percent}%"
                )
            else:
                limit_mb = config.get_effective_memory_limit_mb(available_mb, total_mb)
                hard_max = int(total_mb * (100 - config.system_memory_reserve_percent) / 100)
                fifty_percent = available_mb // 2
                doubled_min = config.min_memory_specification_mb * 2

                info_text = (
                    f"Smart Calculation: {limit_mb} MB\n"
                    f"System Total: {total_mb} MB | Available: {available_mb} MB\n"
                    f"Candidates: min({doubled_min}, {fifty_percent}, {hard_max})\n"
                    f"Reserve: {config.system_memory_reserve_percent}%"
                )

            self.system_info_label.setText(info_text)
        except Exception as e:
            self.system_info_label.setText(f"Error: {e}")

    def _load_settings(self) -> None:
        """Load current settings."""
        try:
            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()

            if config.use_manual_memory_override:
                self.manual_radio.setChecked(True)
                self.auto_radio.setChecked(False)
                if config.manual_memory_override_mb:
                    self.memory_slider.setValue(config.manual_memory_override_mb)
            else:
                self.auto_radio.setChecked(True)
                self.manual_radio.setChecked(False)

            self._on_mode_changed()
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to load settings: {e}")

    def save_settings(self) -> None:
        """Save performance settings."""
        try:
            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()
            config.use_manual_memory_override = self.manual_radio.isChecked()

            if self.manual_radio.isChecked():
                config.manual_memory_override_mb = self.memory_slider.value()

            if self.logger:
                self.logger.info(
                    f"Saved performance settings: "
                    f"manual={config.use_manual_memory_override}, "
                    f"override_mb={config.manual_memory_override_mb}"
                )
        except Exception as e:
            if self.logger:
                self.logger.error(f"Failed to save settings: {e}")


class AdvancedTab(QWidget):
    """Advanced settings tab with system reset functionality."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the advanced settings UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("Advanced Settings")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)

        # Warning message
        warning = QLabel(
            "⚠️ Complete System Reset\n\n"
            "This will reset all application settings, clear the cache, and restore "
            "the application to its default state. This action cannot be undone."
        )
        warning.setWordWrap(True)
        warning.setStyleSheet("color: #ff6b6b; padding: 8px; background-color: rgba(255, 107, 107, 0.1); border-radius: 4px;")
        layout.addWidget(warning)

        # Reset button
        reset_button = QPushButton("Complete System Reset")
        reset_button.setStyleSheet(
            "QPushButton { background-color: #ff6b6b; color: white; padding: 8px; border-radius: 4px; font-weight: bold; }"
            "QPushButton:hover { background-color: #ff5252; }"
        )
        reset_button.clicked.connect(self._perform_system_reset)
        layout.addWidget(reset_button)

        layout.addStretch(1)

    def _perform_system_reset(self) -> None:
        """Perform complete system reset with triple verification."""
        # First verification: Simple confirmation
        reply1 = QMessageBox.warning(
            self,
            "System Reset - Confirmation 1/3",
            "Are you sure you want to reset the entire system?\n\n"
            "This will delete all settings, cache, and restore defaults.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply1 != QMessageBox.Yes:
            return

        # Second verification: More serious warning
        reply2 = QMessageBox.critical(
            self,
            "System Reset - Confirmation 2/3",
            "⚠️ WARNING ⚠️\n\n"
            "This action will:\n"
            "• Delete all application settings\n"
            "• Clear the model cache\n"
            "• Reset window layout\n"
            "• Reset all preferences\n\n"
            "This CANNOT be undone. Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply2 != QMessageBox.Yes:
            return

        # Third verification: Text input
        text, ok = QInputDialog.getText(
            self,
            "System Reset - Confirmation 3/3",
            "Type 'RESET' to confirm complete system reset:",
            QLineEdit.Normal,
            ""
        )

        if not ok or text.strip().upper() != "RESET":
            QMessageBox.information(
                self,
                "Reset Cancelled",
                "System reset cancelled. No changes were made."
            )
            return

        # All verifications passed - perform reset
        self._execute_system_reset()

    def _execute_system_reset(self) -> None:
        """Execute the actual system reset."""
        try:
            from PySide6.QtCore import QSettings, QStandardPaths
            from pathlib import Path

            # Close database manager to release file locks
            try:
                from src.core.database_manager import close_database_manager
                close_database_manager()
            except Exception as e:
                print(f"Warning: Could not close database manager: {e}")

            # Clear QSettings
            settings = QSettings()
            settings.clear()
            settings.sync()

            # Delete database file
            try:
                app_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
                db_file = app_data / "3dmm.db"
                if db_file.exists():
                    db_file.unlink()
                    print(f"✓ Deleted database: {db_file}")

                # Also delete WAL and SHM files if they exist
                wal_file = app_data / "3dmm.db-wal"
                shm_file = app_data / "3dmm.db-shm"
                if wal_file.exists():
                    wal_file.unlink()
                if shm_file.exists():
                    shm_file.unlink()
            except Exception as e:
                print(f"Warning: Could not delete database file: {e}")

            # Clear model cache
            try:
                from src.core.model_cache import ModelCache
                cache = ModelCache.get_instance()
                cache.clear()
            except Exception as e:
                print(f"Warning: Could not clear model cache: {e}")

            # Show success message
            QMessageBox.information(
                self,
                "System Reset Complete",
                "✓ System reset completed successfully!\n\n"
                "The application will now close and restart."
            )

            # Relaunch the application
            import subprocess
            import sys
            subprocess.Popen([sys.executable, sys.argv[0]])

            # Close the application
            from PySide6.QtWidgets import QApplication
            QApplication.instance().quit()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Reset Failed",
                f"An error occurred during system reset:\n\n{str(e)}"
            )

