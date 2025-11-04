"""
Run Mode Setup Dialog for first-run configuration.

Displays run mode explanation and allows storage location customization.
"""

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFileDialog,
    QGroupBox,
    QTextEdit,
)
from PySide6.QtCore import Signal

from ...core.services.run_mode_manager import RunModeManager
from ...core.logging_config import get_logger

logger = get_logger(__name__)


class RunModeSetupDialog(QDialog):
    """Dialog for first-run setup and run mode configuration."""

    setup_complete = Signal()

    def __init__(self, parent=None) -> None:
        """
        Initialize run mode setup dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.run_mode_manager = RunModeManager()
        self.setWindowTitle("Digital Workshop - First Run Setup")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setModal(True)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup UI components."""
        layout = QVBoxLayout()

        # Title
        title = QLabel("Welcome to Digital Workshop")
        title_font = title.font()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)

        # Description
        description = QTextEdit()
        description.setReadOnly(True)
        description.setText(
            "Digital Workshop is a 3D model management system that helps you organize, "
            "track, and manage your 3D model files.\n\n"
            "This setup wizard will help you configure the storage location for your projects "
            "and model files.\n\n"
            "You can change these settings later in the preferences."
        )
        description.setMaximumHeight(100)
        layout.addWidget(description)

        # Storage location group
        storage_group = QGroupBox("Storage Location")
        storage_layout = QVBoxLayout()

        storage_label = QLabel("Choose where to store your projects and model files:")
        storage_layout.addWidget(storage_label)

        # Storage path input
        path_layout = QHBoxLayout()
        self.storage_path_input = QLineEdit()
        self.storage_path_input.setText(self.run_mode_manager.get_storage_location())
        self.storage_path_input.setReadOnly(True)
        path_layout.addWidget(self.storage_path_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_storage_location)
        path_layout.addWidget(browse_btn)

        storage_layout.addLayout(path_layout)
        storage_group.setLayout(storage_layout)
        layout.addWidget(storage_group)

        # Info group
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout()

        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setText(
            "Storage Location:\n"
            "  • Projects: Stores project metadata and file references\n"
            "  • Database: Stores project and file information\n"
            "  • Imports: Stores imported library information\n\n"
            "You can use any accessible folder on your computer. "
            "Make sure you have write permissions."
        )
        info_text.setMaximumHeight(120)
        info_layout.addWidget(info_text)
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        finish_btn = QPushButton("Finish Setup")
        finish_btn.clicked.connect(self._finish_setup)
        button_layout.addWidget(finish_btn)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _browse_storage_location(self) -> None:
        """Browse for storage location."""
        try:
            current_path = self.storage_path_input.text()
            folder = QFileDialog.getExistingDirectory(
                self, "Select Storage Location", current_path, QFileDialog.ShowDirsOnly
            )

            if folder:
                if self.run_mode_manager.set_storage_location(folder):
                    self.storage_path_input.setText(folder)
                    logger.info("Storage location set to: %s", folder)
                else:
                    logger.error("Failed to set storage location: %s", folder)

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to browse storage location: %s", str(e))

    def _finish_setup(self) -> None:
        """Finish setup and close dialog."""
        try:
            # Mark first run as complete
            self.run_mode_manager.mark_first_run_complete()
            logger.info("First run setup complete")
            self.setup_complete.emit()
            self.accept()

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to finish setup: %s", str(e))
            self.reject()

    def get_storage_location(self) -> str:
        """Get configured storage location."""
        return self.storage_path_input.text()
