"""
Qt-Material theme color picker dialog.

Displays Material Design colors from the current qt-material theme.
Shows primaryColor, primaryLightColor, secondaryColor, etc. with visual swatches.

Single Responsibility: Display and allow inspection of qt-material theme colors.
"""

from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


class QtMaterialColorPicker(QDialog):
    """
    Dialog showing Material Design colors from qt-material theme.

    Displays color swatches for:
    - Primary colors (primaryColor, primaryLightColor, primaryDarkColor)
    - Secondary colors (secondaryColor, secondaryLightColor, secondaryDarkColor)
    - Text colors (primaryTextColor, secondaryTextColor)
    """

    theme_changed = Signal(str)  # Emitted when theme variant is changed

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the color picker dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.setWindowTitle("Material Design Colors")
        self.setMinimumWidth(500)
        self.setMinimumHeight(600)

        # Use native title bar (removed frameless window flag)
        # This allows the OS to handle the title bar and window controls

        self.color_swatches: Dict[str, QPushButton] = {}
        self._setup_ui()
        self._load_colors()

    def _setup_ui(self) -> None:
        """Setup the UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Material Design Theme Colors")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Theme variant selector
        variant_layout = QHBoxLayout()
        variant_layout.addWidget(QLabel("Theme Variant:"))

        self.variant_combo = QComboBox()
        self._populate_variants()
        self.variant_combo.currentTextChanged.connect(self._on_variant_changed)
        variant_layout.addWidget(self.variant_combo)
        variant_layout.addStretch()
        layout.addLayout(variant_layout)

        # Color swatches in scrollable area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        color_widget = QWidget()
        color_layout = QVBoxLayout()

        # Define color groups
        self.color_groups = {
            "Primary Colors": [
                "primaryColor",
                "primaryLightColor",
                "primaryDarkColor",
            ],
            "Secondary Colors": [
                "secondaryColor",
                "secondaryLightColor",
                "secondaryDarkColor",
            ],
            "Text Colors": [
                "primaryTextColor",
                "secondaryTextColor",
            ],
        }

        # Create color swatches for each group
        for group_name, colors in self.color_groups.items():
            group_label = QLabel(group_name)
            group_font = QFont()
            group_font.setBold(True)
            group_label.setFont(group_font)
            color_layout.addWidget(group_label)

            # Create grid for colors in this group
            grid = QGridLayout()
            for i, color_name in enumerate(colors):
                # Color swatch button
                swatch = QPushButton()
                swatch.setMinimumHeight(50)
                swatch.setMinimumWidth(200)
                self.color_swatches[color_name] = swatch

                # Label with color name
                label = QLabel(color_name)
                label.setMinimumWidth(150)

                grid.addWidget(label, i, 0)
                grid.addWidget(swatch, i, 1)

            color_layout.addLayout(grid)
            color_layout.addSpacing(10)

        color_layout.addStretch()
        color_widget.setLayout(color_layout)
        scroll.setWidget(color_widget)
        layout.addWidget(scroll)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)

    def _populate_variants(self) -> None:
        """Populate the variant combo box with available qt-material variants."""
        try:
            from src.gui.theme.simple_service import ThemeService

            service = ThemeService.instance()

            # Get current theme type
            theme_type, _ = service.get_current_theme()
            current_variant = service.settings.value("qt_material_variant", "blue")

            # Get available variants
            variants = service.get_qt_material_variants(theme_type)

            for variant in variants:
                # Extract color name from variant (e.g., "dark_blue" -> "blue")
                color_name = variant.split("_", 1)[1] if "_" in variant else variant
                self.variant_combo.addItem(color_name.title(), variant)

            # Set current variant
            index = self.variant_combo.findData(current_variant)
            if index >= 0:
                self.variant_combo.setCurrentIndex(index)
        except Exception as e:
            print(f"Error populating variants: {e}")

    def _load_colors(self) -> None:
        """Load and display colors from current qt-material theme."""
        try:
            import os

            # Get colors from environment (set by qt-material)
            colors = {
                "primaryColor": os.environ.get("QTMATERIAL_PRIMARYCOLOR", "#2196F3"),
                "primaryLightColor": os.environ.get(
                    "QTMATERIAL_PRIMARYLIGHTCOLOR", "#BBDEFB"
                ),
                "primaryDarkColor": os.environ.get(
                    "QTMATERIAL_PRIMARYDARKCOLOR", "#1976D2"
                ),
                "secondaryColor": os.environ.get(
                    "QTMATERIAL_SECONDARYCOLOR", "#FFC107"
                ),
                "secondaryLightColor": os.environ.get(
                    "QTMATERIAL_SECONDARYLIGHTCOLOR", "#FFE082"
                ),
                "secondaryDarkColor": os.environ.get(
                    "QTMATERIAL_SECONDARYDARKCOLOR", "#FFA000"
                ),
                "primaryTextColor": os.environ.get(
                    "QTMATERIAL_PRIMARYTEXTCOLOR", "#212121"
                ),
                "secondaryTextColor": os.environ.get(
                    "QTMATERIAL_SECONDARYTEXTCOLOR", "#757575"
                ),
            }

            # Update swatches
            for color_name, hex_color in colors.items():
                if color_name in self.color_swatches:
                    swatch = self.color_swatches[color_name]

                    # Set background color
                    swatch.setStyleSheet(
                        f"""
                        QPushButton {{
                            background-color: {hex_color};
                            border: 1px solid #cccccc;
                            border-radius: 4px;
                            color: {self._get_text_color(hex_color)};
                            font-weight: bold;
                        }}
                        QPushButton:hover {{
                            border: 2px solid #999999;
                        }}
                    """
                    )

                    # Set button text to hex value
                    swatch.setText(hex_color.upper())
        except Exception as e:
            print(f"Error loading colors: {e}")

    def _get_text_color(self, bg_hex: str) -> str:
        """
        Determine if text should be white or black based on background color.

        Args:
            bg_hex: Background color in hex format

        Returns:
            "#ffffff" for white text, "#000000" for black text
        """
        try:
            color = QColor(bg_hex)
            # Calculate luminance
            r, g, b = color.red(), color.green(), color.blue()
            luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return "#000000" if luminance > 0.5 else "#ffffff"
        except Exception:
            return "#000000"

    def _on_variant_changed(self, variant_name: str) -> None:
        """
        Handle theme variant change.

        Args:
            variant_name: Selected variant name
        """
        try:
            from src.gui.theme.simple_service import ThemeService

            service = ThemeService.instance()

            # Get the full variant name (e.g., "blue" -> "dark_blue" or "light_blue")
            current_theme, _ = service.get_current_theme()
            theme_prefix = "dark" if current_theme == "dark" else "light"
            full_variant = f"{theme_prefix}_{variant_name.lower()}"

            # Set the variant and apply theme
            service.set_qt_material_variant(variant_name.lower())
            service.apply_theme(current_theme, "qt-material")

            # Reload colors
            self._load_colors()
            self.theme_changed.emit(full_variant)
        except Exception as e:
            print(f"Error changing variant: {e}")

    def _toggle_maximize(self) -> None:
        """Toggle window maximize/restore state."""
        try:
            if self.isMaximized():
                self.showNormal()
            else:
                self.showMaximized()
        except Exception:
            pass
