"""
Deduplication dialog for handling duplicate model resolution.

Allows user to choose how to deduplicate:
- Keep largest
- Keep smallest
- Keep newest
- Keep oldest
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QButtonGroup,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
)
from PySide6.QtGui import QFont

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class DeduplicationDialog(QDialog):
    """Dialog for choosing deduplication strategy."""

    deduplication_confirmed = Signal(str)  # keep_strategy

    def __init__(self, duplicate_models: List[Dict], parent=None) -> None:
        """
        Initialize deduplication dialog.

        Args:
            duplicate_models: List of duplicate model dicts
            parent: Parent widget
        """
        super().__init__(parent)
        self.duplicate_models = duplicate_models
        self.logger = get_logger(__name__)
        self.keep_strategy = None

        self.setWindowTitle("Resolve Duplicate Models")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup dialog UI."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Duplicate Models Found")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Description
        desc = QLabel(
            f"Found {len(self.duplicate_models)} duplicate models with the same content.\n"
            "Choose which one to keep:"
        )
        layout.addWidget(desc)

        # Models table
        self._setup_models_table()
        layout.addWidget(self.models_table)

        # Strategy selection
        layout.addSpacing(20)
        strategy_label = QLabel("Keep Strategy:")
        strategy_font = QFont()
        strategy_font.setBold(True)
        strategy_label.setFont(strategy_font)
        layout.addWidget(strategy_label)

        self.strategy_group = QButtonGroup()
        strategies = [
            ("Largest", "largest"),
            ("Smallest", "smallest"),
            ("Newest", "newest"),
            ("Oldest", "oldest"),
        ]

        for i, (label, value) in enumerate(strategies):
            radio = QRadioButton(label)
            radio.setProperty("strategy_value", value)
            if i == 0:
                radio.setChecked(True)
            self.strategy_group.addButton(radio, i)
            layout.addWidget(radio)

        # Buttons
        layout.addSpacing(20)
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        dedupe_btn = QPushButton("Deduplicate")
        dedupe_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        dedupe_btn.clicked.connect(self._on_deduplicate)
        button_layout.addWidget(dedupe_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def _setup_models_table(self) -> None:
        """Setup models table."""
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(4)
        self.models_table.setHorizontalHeaderLabels(["Filename", "Size (MB)", "Modified", "Path"])

        for i, model in enumerate(self.duplicate_models):
            self.models_table.insertRow(i)

            # Filename
            filename = Path(model["file_path"]).name
            self.models_table.setItem(i, 0, QTableWidgetItem(filename))

            # Size
            try:
                size_mb = Path(model["file_path"]).stat().st_size / (1024 * 1024)
                size_text = f"{size_mb:.2f}"
            except:
                size_text = "N/A"
            self.models_table.setItem(i, 1, QTableWidgetItem(size_text))

            # Modified
            try:
                mtime = Path(model["file_path"]).stat().st_mtime
                modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
            except:
                modified = "N/A"
            self.models_table.setItem(i, 2, QTableWidgetItem(modified))

            # Path
            self.models_table.setItem(i, 3, QTableWidgetItem(model["file_path"]))

        # Resize columns
        header = self.models_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

    def _on_deduplicate(self) -> None:
        """Handle deduplicate button click."""
        checked_button = self.strategy_group.checkedButton()
        if checked_button:
            self.keep_strategy = checked_button.property("strategy_value")
            self.deduplication_confirmed.emit(self.keep_strategy)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Please select a strategy")

    def get_keep_strategy(self) -> Optional[str]:
        """Get selected keep strategy."""
        return self.keep_strategy
