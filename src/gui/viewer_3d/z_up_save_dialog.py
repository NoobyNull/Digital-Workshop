"""
Z-Up Save Dialog - Dialog for saving Z-up oriented models.

Provides options to:
- Save camera view only (database)
- Save and replace original model file
- Save as new model file
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QRadioButton,
    QButtonGroup,
)

from src.core.logging_config import get_logger

logger = get_logger(__name__)


class ZUpSaveDialog(QDialog):
    """Dialog for choosing how to save Z-up oriented model."""

    SAVE_VIEW_ONLY = 0
    SAVE_AND_REPLACE = 1
    SAVE_AS_NEW = 2

    def __init__(self, model_filename: str, parent=None) -> None:
        """
        Initialize Z-up save dialog.

        Args:
            model_filename: Name of the current model file
            parent: Parent widget
        """
        super().__init__(parent)
        self.model_filename = model_filename
        self.selected_option = self.SAVE_VIEW_ONLY
        self.logger = logger

        self.setWindowTitle("Save Z-Up Orientation")
        self.setMinimumWidth(500)
        self.setMinimumHeight(300)

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)

        # Title
        title = QLabel("How would you like to save the Z-up orientation?")
        title.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(title)

        layout.addSpacing(10)

        # Option group
        self.option_group = QButtonGroup()

        # Option 1: Save view only
        option1 = QRadioButton(
            "Save Camera View Only\n"
            "Saves the Z-up camera orientation to the database.\n"
            "Model file remains unchanged."
        )
        option1.setChecked(True)
        self.option_group.addButton(option1, self.SAVE_VIEW_ONLY)
        layout.addWidget(option1)

        layout.addSpacing(10)

        # Option 2: Save and replace
        option2 = QRadioButton(
            f"Save and Replace Original\n"
            f"Rotates model geometry to Z-up and overwrites:\n"
            f"{self.model_filename}"
        )
        self.option_group.addButton(option2, self.SAVE_AND_REPLACE)
        layout.addWidget(option2)

        layout.addSpacing(10)

        # Option 3: Save as new
        new_filename = self._get_new_filename()
        option3 = QRadioButton(
            f"Save as New File\n"
            f"Rotates model geometry to Z-up and saves as:\n"
            f"{new_filename}"
        )
        self.option_group.addButton(option3, self.SAVE_AS_NEW)
        layout.addWidget(option3)

        layout.addSpacing(20)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

    def _get_new_filename(self) -> str:
        """Generate new filename for Z-up model."""
        path = Path(self.model_filename)
        new_name = f"{path.stem}_z-up{path.suffix}"
        return str(path.parent / new_name)

    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        self.selected_option = self.option_group.checkedId()
        self.accept()

    def get_selected_option(self) -> int:
        """Get the selected save option."""
        return self.selected_option

    def get_new_filepath(self) -> str:
        """Get the new file path for save as new option."""
        return self._get_new_filename()
