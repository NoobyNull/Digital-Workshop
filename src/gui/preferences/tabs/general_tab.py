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

from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


class GeneralTab(QWidget):
    """General settings tab: window, layout, and performance settings combined."""

    def __init__(
        self,
        on_reset_layout: Callable | None = None,
        on_save_layout_default: Callable | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.on_reset_layout = on_reset_layout
        self.on_save_layout_default = on_save_layout_default
        self.theme_service = None
        self.logger = None
        try:
            from src.core.logging_config import get_logger

            self.logger = get_logger(__name__)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
            pass

        # Initialize theme service
        try:
            from src.gui.theme.simple_service import ThemeService

            self.theme_service = ThemeService.instance()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError):
            pass

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Setup the combined general settings UI."""
        # Create scroll area for all content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        header = QLabel("General Application Settings")
        header.setStyleSheet("font-weight: bold; font-size: 13pt;")
        layout.addWidget(header)

        desc = QLabel(
            "Configure window behavior, layout management, theme, and system performance."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # === Visual Style Section ===
        theme_section = QFrame()
        theme_layout = QVBoxLayout(theme_section)

        theme_label = QLabel("<b>Visual Style</b>")
        theme_label.setStyleSheet("font-size: 11pt;")
        theme_layout.addWidget(theme_label)

        theme_desc = QLabel("Select your preferred theme mode.")
        theme_desc.setWordWrap(True)
        theme_layout.addWidget(theme_desc)

        # Theme mode selector
        theme_form = QFormLayout()
        self.theme_mode_combo = QComboBox()
        self.theme_mode_combo.addItem("Dark", "dark")
        self.theme_mode_combo.addItem("Light", "light")
        self.theme_mode_combo.addItem("Auto (System)", "auto")
        theme_form.addRow("Theme Mode:", self.theme_mode_combo)
        theme_layout.addLayout(theme_form)

        layout.addWidget(theme_section)

        # Separator line
        line1 = QFrame()
        line1.setFrameShape(QFrame.HLine)
        line1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line1)

        # === Window Settings Section ===
        window_section = QFrame()
        window_layout = QVBoxLayout(window_section)

        window_label = QLabel("<b>Window & Layout</b>")
        window_label.setStyleSheet("font-size: 11pt;")
        window_layout.addWidget(window_label)

        # Window dimensions
        dim_form = QFormLayout()

        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(800, 3840)
        self.window_width_spin.setValue(1200)
        self.window_width_spin.setSuffix(" px")
        dim_form.addRow("Default width:", self.window_width_spin)

        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(600, 2160)
        self.window_height_spin.setValue(800)
        self.window_height_spin.setSuffix(" px")
        dim_form.addRow("Default height:", self.window_height_spin)

        self.min_width_spin = QSpinBox()
        self.min_width_spin.setRange(400, 1200)
        self.min_width_spin.setValue(800)
        self.min_width_spin.setSuffix(" px")
        dim_form.addRow("Minimum width:", self.min_width_spin)

        self.min_height_spin = QSpinBox()
        self.min_height_spin.setRange(300, 1000)
        self.min_height_spin.setValue(600)
        self.min_height_spin.setSuffix(" px")
        dim_form.addRow("Minimum height:", self.min_height_spin)

        window_layout.addLayout(dim_form)

        # Startup behavior
        self.maximize_startup_check = QCheckBox("Maximize window on startup")
        self.remember_size_check = QCheckBox("Remember window size on exit")
        self.remember_location_check = QCheckBox("Remember window position on exit")
        window_layout.addWidget(self.maximize_startup_check)
        window_layout.addWidget(self.remember_size_check)
        window_layout.addWidget(self.remember_location_check)

        workspace_section = QFrame()
        workspace_layout = QVBoxLayout(workspace_section)

        workspace_label = QLabel("<b>Workspace Behavior</b>")
        workspace_label.setStyleSheet("font-size: 11pt;")
        workspace_layout.addWidget(workspace_label)

        workspace_desc = QLabel(
            "Control how the project sidebars behave and which page appears when the app starts."
        )
        workspace_desc.setWordWrap(True)
        workspace_layout.addWidget(workspace_desc)

        self.sidebar_sync_check = QCheckBox("Transition sidebars with center tabs")
        workspace_layout.addWidget(self.sidebar_sync_check)

        startup_form = QFormLayout()
        self.startup_page_combo = QComboBox()
        self.startup_page_combo.addItem("Restore last view", "restore_last")
        self.startup_page_combo.addItem("Model Previewer", "model")
        self.startup_page_combo.addItem("G-code Previewer", "gcode")
        self.startup_page_combo.addItem("Cut List Optimizer", "cutlist")
        self.startup_page_combo.addItem("Feed and Speed", "feeds")
        self.startup_page_combo.addItem("Project Cost Estimator", "cost")
        startup_form.addRow("Startup page:", self.startup_page_combo)
        workspace_layout.addLayout(startup_form)

        layout.addWidget(workspace_section)

        # Layout reset
        reset_row = QHBoxLayout()
        reset_row.addWidget(QLabel("Manage window and dock layout defaults."))
        reset_row.addStretch(1)
        self.btn_save_default_layout = QPushButton("Use Current Layout as Default")
        reset_row.addWidget(self.btn_save_default_layout)
        self.btn_reset_layout = QPushButton("Reset Layout")
        reset_row.addWidget(self.btn_reset_layout)
        window_layout.addLayout(reset_row)

        # Dock tab positions
        tab_pos_label = QLabel("<b>Dock Tab Positions</b>")
        tab_pos_label.setStyleSheet("font-size: 10pt; margin-top: 12px;")
        window_layout.addWidget(tab_pos_label)

        tab_pos_desc = QLabel("Configure where tabs appear for each dock area.")
        tab_pos_desc.setWordWrap(True)
        window_layout.addWidget(tab_pos_desc)

        tab_pos_form = QFormLayout()

        self.left_tab_position_combo = QComboBox()
        self.left_tab_position_combo.addItem("Bottom", "bottom")
        self.left_tab_position_combo.addItem("Top", "top")
        tab_pos_form.addRow("Left Dock Tabs:", self.left_tab_position_combo)

        self.right_tab_position_combo = QComboBox()
        self.right_tab_position_combo.addItem("Bottom", "bottom")
        self.right_tab_position_combo.addItem("Top", "top")
        tab_pos_form.addRow("Right Dock Tabs:", self.right_tab_position_combo)

        window_layout.addLayout(tab_pos_form)

        layout.addWidget(window_section)

        # Separator line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)

        # === Performance Settings Section ===
        perf_section = QFrame()
        perf_layout = QVBoxLayout(perf_section)

        perf_label = QLabel("<b>Performance & Memory</b>")
        perf_label.setStyleSheet("font-size: 11pt;")
        perf_layout.addWidget(perf_label)

        perf_desc = QLabel(
            "Configure memory allocation. Smart calculation: min(doubled_minimum, 50% available, total - 20%)"
        )
        perf_desc.setWordWrap(True)
        perf_layout.addWidget(perf_desc)

        # Memory mode
        self.auto_radio = QCheckBox("Auto (Smart Calculation)")
        self.auto_radio.setChecked(True)
        perf_layout.addWidget(self.auto_radio)

        self.manual_radio = QCheckBox("Manual Override")
        perf_layout.addWidget(self.manual_radio)

        # Manual override slider
        slider_form = QFormLayout()
        slider_layout = QHBoxLayout()

        self.memory_slider = QSlider(Qt.Horizontal)
        self.memory_slider.setMinimum(10)
        self.memory_slider.setMaximum(95)
        self.memory_slider.setValue(80)
        self.memory_slider.setTickPosition(QSlider.TicksBelow)
        self.memory_slider.setTickInterval(5)
        slider_layout.addWidget(self.memory_slider)

        self.memory_value_label = QLabel("80%")
        self.memory_value_label.setMinimumWidth(80)
        slider_layout.addWidget(self.memory_value_label)

        slider_form.addRow("Cache limit (% of RAM):", slider_layout)
        perf_layout.addLayout(slider_form)

        # System info
        self.system_info_label = QLabel()
        self.system_info_label.setWordWrap(True)
        self.system_info_label.setStyleSheet(
            "padding: 8px; background-color: rgba(0, 0, 0, 0.05); border-radius: 4px;"
        )
        perf_layout.addWidget(self.system_info_label)

        layout.addWidget(perf_section)

        layout.addStretch(1)

        scroll.setWidget(container)

        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(scroll)

        # Connect signals
        self.btn_reset_layout.clicked.connect(self._handle_reset)
        self.btn_save_default_layout.clicked.connect(self._handle_save_layout_default)
        self.auto_radio.toggled.connect(self._on_mode_changed)
        self.manual_radio.toggled.connect(self._on_mode_changed)
        self.memory_slider.valueChanged.connect(self._on_slider_changed)

        # Update system info
        self._update_system_info()

    def _load_settings(self) -> None:
        """Load current settings from config."""
        try:
            from PySide6.QtCore import QSettings

            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()
            settings = QSettings()

            # Theme settings
            if self.theme_service:
                current_theme, _ = self.theme_service.get_current_theme()
                theme_index = {"dark": 0, "light": 1, "auto": 2}.get(current_theme, 0)
                self.theme_mode_combo.setCurrentIndex(theme_index)

            # Window settings
            self.window_width_spin.setValue(config.default_window_width)
            self.window_height_spin.setValue(config.default_window_height)
            self.min_width_spin.setValue(config.minimum_window_width)
            self.min_height_spin.setValue(config.minimum_window_height)
            self.maximize_startup_check.setChecked(config.maximize_on_startup)
            remember_size = settings.value(
                "window/remember_window_size", config.remember_window_size, type=bool
            )
            self.remember_size_check.setChecked(bool(remember_size))
            self.remember_location_check.setChecked(
                settings.value(
                    "window/remember_location",
                    config.remember_window_location,
                    type=bool,
                )
            )
            sidebar_sync = settings.value("ui/sidebar_sync_enabled", True, type=bool)
            self.sidebar_sync_check.setChecked(bool(sidebar_sync))
            startup_mode = (
                settings.value("ui/startup_tab_mode", "restore_last", type=str)
                or "restore_last"
            )
            startup_index = self.startup_page_combo.findData(startup_mode)
            if startup_index >= 0:
                self.startup_page_combo.setCurrentIndex(startup_index)
            else:
                self.startup_page_combo.setCurrentIndex(0)

            # Dock tab positions
            left_pos = settings.value("dock_tabs/left_position", "bottom", type=str)
            right_pos = settings.value("dock_tabs/right_position", "bottom", type=str)

            # Set combo box selections
            left_index = self.left_tab_position_combo.findData(left_pos)
            if left_index >= 0:
                self.left_tab_position_combo.setCurrentIndex(left_index)

            right_index = self.right_tab_position_combo.findData(right_pos)
            if right_index >= 0:
                self.right_tab_position_combo.setCurrentIndex(right_index)

            # Performance settings
            if config.use_manual_memory_override:
                self.manual_radio.setChecked(True)
                self.auto_radio.setChecked(False)
                if config.manual_cache_limit_percent:
                    self.memory_slider.setValue(config.manual_cache_limit_percent)
            else:
                self.auto_radio.setChecked(True)
                self.manual_radio.setChecked(False)

            self._on_mode_changed()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to load general settings: %s", e)

    def save_settings(self) -> None:
        """Save all general settings to config."""
        try:
            from PySide6.QtCore import QSettings

            from src.core.application_config import ApplicationConfig

            config = ApplicationConfig.get_default()
            settings = QSettings()

            # Save theme settings
            if self.theme_service:
                theme_mode = self.theme_mode_combo.currentData()
                if theme_mode:
                    self.theme_service.apply_theme(theme_mode)

            # Save window settings
            config.default_window_width = self.window_width_spin.value()
            config.default_window_height = self.window_height_spin.value()
            config.minimum_window_width = self.min_width_spin.value()
            config.minimum_window_height = self.min_height_spin.value()
            config.maximize_on_startup = self.maximize_startup_check.isChecked()
            config.remember_window_size = self.remember_size_check.isChecked()
            config.remember_window_location = self.remember_location_check.isChecked()
            settings.setValue(
                "window/remember_window_size", self.remember_size_check.isChecked()
            )
            settings.setValue(
                "ui/sidebar_sync_enabled", self.sidebar_sync_check.isChecked()
            )
            startup_data = self.startup_page_combo.currentData() or "restore_last"
            settings.setValue("ui/startup_tab_mode", startup_data)
            settings.setValue(
                "window/remember_location", self.remember_location_check.isChecked()
            )

            # Save dock tab positions
            left_pos = self.left_tab_position_combo.currentData()
            right_pos = self.right_tab_position_combo.currentData()
            settings.setValue("dock_tabs/left_position", left_pos)
            settings.setValue("dock_tabs/right_position", right_pos)

            # Save performance settings
            config.use_manual_memory_override = self.manual_radio.isChecked()
            if self.manual_radio.isChecked():
                config.manual_cache_limit_percent = self.memory_slider.value()

            if self.logger:
                self.logger.info("General settings saved")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            if self.logger:
                self.logger.error("Failed to save general settings: %s", e)

    def _handle_reset(self) -> None:
        """Handle layout reset."""
        try:
            if callable(self.on_reset_layout):
                self.on_reset_layout()
                QMessageBox.information(
                    self, "Layout Reset", "Window layout has been reset to defaults."
                )
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            QMessageBox.warning(self, "Reset Failed", f"Failed to reset layout:\n{e}")

    def _handle_save_layout_default(self) -> None:
        """Save current layout as the default layout."""
        try:
            if callable(self.on_save_layout_default):
                self.on_save_layout_default()
                QMessageBox.information(
                    self,
                    "Default Layout Updated",
                    "Current window and dock layout will be used as the reset default.",
                )
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            QMessageBox.warning(
                self,
                "Save Failed",
                f"Failed to save current layout as default:\n{e}",
            )

    def _on_mode_changed(self) -> None:
        """Handle memory mode change."""
        is_manual = self.manual_radio.isChecked()
        self.memory_slider.setEnabled(is_manual)
        self._update_system_info()

    def _on_slider_changed(self, value: int) -> None:
        """Handle slider change."""
        self.memory_value_label.setText(f"{value}%")
        self._update_system_info()

    def _update_system_info(self) -> None:
        """Update system information display."""
        try:
            import psutil

            from src.core.application_config import ApplicationConfig

            memory = psutil.virtual_memory()
            total_mb = int(memory.total / (1024**2))
            available_mb = int(memory.available / (1024**2))

            config = ApplicationConfig.get_default()

            if self.manual_radio.isChecked():
                percent = self.memory_slider.value()
                limit_mb = int(total_mb * (percent / 100))
                info_text = (
                    f"<b>Manual Mode:</b> {percent}% of {total_mb} MB = <b>{limit_mb} MB</b><br>"
                    f"System Total: {total_mb} MB | Available: {available_mb} MB"
                )
            else:
                limit_mb = config.get_effective_memory_limit_mb(available_mb, total_mb)
                hard_max = int(
                    total_mb * (100 - config.system_memory_reserve_percent) / 100
                )
                fifty_percent = available_mb // 2
                doubled_min = config.min_memory_specification_mb * 2

                info_text = (
                    f"<b>Smart Calculation:</b> <b>{limit_mb} MB</b><br>"
                    f"System Total: {total_mb} MB | Available: {available_mb} MB<br>"
                    f"Calculated from: min({doubled_min}, {fifty_percent}, {hard_max})"
                )

            self.system_info_label.setText(info_text)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.system_info_label.setText(f"Error: {e}")
