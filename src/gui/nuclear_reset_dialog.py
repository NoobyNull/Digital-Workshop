"""
Nuclear Reset Dialog - GUI for complete application data destruction.

Provides a user interface for the NUCLEAR RESET feature with:
- Preview of what will be deleted
- Size calculations
- Backup option
- Multiple confirmation steps
- Progress tracking
"""

import os
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QCheckBox,
    QTextEdit,
    QProgressBar,
    QMessageBox,
    QGroupBox,
    QInputDialog,
)

from src.core.logging_config import get_logger
from src.core.nuclear_reset import NuclearReset
from src.gui.theme import SPACING_16

logger = get_logger(__name__)


class NuclearResetWorker(QThread):
    """Worker thread for executing nuclear reset."""

    progress_updated = Signal(str)  # Status message
    reset_completed = Signal(dict)  # Results dictionary
    reset_failed = Signal(str)  # Error message

    def __init__(self, create_backup: bool):
        """
        Initialize worker.

        Args:
            create_backup: Whether to create backup before reset
        """
        super().__init__()
        self.create_backup = create_backup
        self.reset_handler = NuclearReset()

    def run(self):
        """Execute the nuclear reset."""
        try:
            self.progress_updated.emit("Initializing nuclear reset...")

            # Execute reset
            results = self.reset_handler.execute_nuclear_reset(create_backup=self.create_backup)

            if results["success"]:
                self.reset_completed.emit(results)
            else:
                error_msg = "\n".join(results.get("errors", ["Unknown error"]))
                self.reset_failed.emit(error_msg)

        except Exception as e:
            logger.error("Nuclear reset worker failed: %s", e, exc_info=True)
            self.reset_failed.emit(str(e))


class NuclearResetDialog(QDialog):
    """Dialog for nuclear reset with preview and confirmation."""

    def __init__(self, parent=None):
        """
        Initialize nuclear reset dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self.reset_handler = NuclearReset()
        self.worker: Optional[NuclearResetWorker] = None

        self.setWindowTitle("⚠️ NUCLEAR RESET - Complete Data Destruction")
        self.setMinimumSize(700, 600)
        self.setModal(True)

        self._setup_ui()
        self._scan_targets()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        layout.setSpacing(SPACING_16)

        # Warning header - minimal styling, let qt-material handle most of it
        warning_label = QLabel(
            "⚠️ WARNING: NUCLEAR RESET ⚠️\n\n"
            "This will PERMANENTLY DELETE ALL application data:\n"
            "• Database (all models, metadata, projects)\n"
            "• Settings (window layout, preferences, themes)\n"
            "• Cache (thumbnails, temp files)\n"
            "• Logs (all activity logs)\n"
            "• Everything related to Digital Workshop\n\n"
            "THIS CANNOT BE UNDONE!"
        )
        warning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Emphasize the warning using font only; let Qt handle colors and borders.
        font = warning_label.font()
        font.setBold(True)
        warning_label.setFont(font)
        layout.addWidget(warning_label)

        # Scan results group - let qt-material handle styling
        scan_group = QGroupBox("What Will Be Deleted")
        scan_layout = QVBoxLayout()

        self.scan_text = QTextEdit()
        self.scan_text.setReadOnly(True)
        self.scan_text.setMaximumHeight(200)
        scan_layout.addWidget(self.scan_text)

        scan_group.setLayout(scan_layout)
        layout.addWidget(scan_group)

        # Backup option - let qt-material handle styling
        self.backup_checkbox = QCheckBox("Create backup before deletion (HIGHLY RECOMMENDED)")
        self.backup_checkbox.setChecked(True)
        layout.addWidget(self.backup_checkbox)

        # Backup location label - let qt-material handle colors
        self.backup_location_label = QLabel()
        self.backup_location_label.setWordWrap(True)
        layout.addWidget(self.backup_location_label)

        # Progress bar (hidden initially) - let qt-material handle styling
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label - let qt-material handle styling
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # Buttons - let qt-material handle base styling
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        self.execute_button = QPushButton("⚠️ EXECUTE NUCLEAR RESET")
        self.execute_button.clicked.connect(self._confirm_and_execute)
        button_layout.addWidget(self.execute_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Update backup location
        self._update_backup_location()

    def _update_backup_location(self):
        """Update the backup location label."""
        if self.backup_checkbox.isChecked():
            docs_path = Path(os.environ.get("USERPROFILE", Path.home())) / "Documents"
            backup_path = docs_path / "DigitalWorkshop_Backups"
            self.backup_location_label.setText(f"Backup will be saved to: {backup_path}")
        else:
            self.backup_location_label.setText("⚠️ NO BACKUP - All data will be permanently lost!")

    def _scan_targets(self):
        """Scan and display what will be deleted."""
        try:
            self.scan_text.append("Scanning application data...\n")

            targets = self.reset_handler.scan_all_targets()

            # Display summary
            self.scan_text.append("📊 SUMMARY:")
            self.scan_text.append(f"  • Directories: {len(targets['directories'])}")
            self.scan_text.append(f"  • Files: {targets['file_count']:,}")
            self.scan_text.append(f"  • Total Size: {targets['total_size_mb']:.2f} MB")

            if targets.get("registry_keys"):
                self.scan_text.append(f"  • Registry Keys: {len(targets['registry_keys'])}")

            self.scan_text.append("\n📁 DIRECTORIES TO DELETE:")

            for dir_info in targets["directories"]:
                self.scan_text.append(
                    f"  [{dir_info['type']}] {dir_info['path']}\n"
                    f"    Size: {dir_info['size_mb']:.2f} MB, Files: {dir_info['file_count']}"
                )

            if targets.get("registry_keys"):
                self.scan_text.append("\n🔑 REGISTRY KEYS TO DELETE:")
                for key in targets["registry_keys"]:
                    self.scan_text.append(f"  • {key}")

        except Exception as e:
            self.logger.error("Failed to scan targets: %s", e, exc_info=True)
            self.scan_text.append(f"\n❌ ERROR: {e}")

    def _confirm_and_execute(self):
        """Show final confirmation and execute reset."""
        # First confirmation
        reply = QMessageBox.warning(
            self,
            "⚠️ FINAL WARNING",
            "Are you ABSOLUTELY SURE you want to delete ALL application data?\n\n"
            "This action is IRREVERSIBLE and will:\n"
            "• Delete your entire model library\n"
            "• Delete all settings and preferences\n"
            "• Delete all thumbnails and cache\n"
            "• Delete all logs\n"
            "• Reset everything to factory defaults\n\n"
            "Click YES to proceed with NUCLEAR RESET.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        # Second confirmation (type confirmation)
        text, ok = QInputDialog.getText(
            self,
            "Type to Confirm",
            "Type 'DELETE EVERYTHING' to confirm nuclear reset:",
        )

        if not ok or text != "DELETE EVERYTHING":
            QMessageBox.information(
                self, "Cancelled", "Nuclear reset cancelled. Confirmation text did not match."
            )
            return

        # Execute the reset
        self._execute_reset()

    def _execute_reset(self):
        """Execute the nuclear reset in background thread."""
        self.execute_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        self.backup_checkbox.setEnabled(False)

        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.status_label.setText("Executing nuclear reset...")

        # Create and start worker
        self.worker = NuclearResetWorker(create_backup=self.backup_checkbox.isChecked())
        self.worker.progress_updated.connect(self._on_progress)
        self.worker.reset_completed.connect(self._on_completed)
        self.worker.reset_failed.connect(self._on_failed)
        self.worker.start()

    def _on_progress(self, message: str):
        """Handle progress update."""
        self.status_label.setText(message)

    def _on_completed(self, results: dict):
        """Handle reset completion."""
        self.progress_bar.setVisible(False)

        # Build results message
        message = "✅ NUCLEAR RESET COMPLETE\n\n"
        message += f"Directories deleted: {results['directories_deleted']}\n"
        message += f"Files deleted: {results['files_deleted']}\n"
        message += f"Registry cleared: {'Yes' if results['registry_cleared'] else 'No'}\n"

        if results.get("backup_created"):
            message += f"\n📦 Backup created at:\n{results['backup_path']}"

        if results.get("errors"):
            message += "\n\n⚠️ Some files couldn't be deleted (still in use):\n"
            for error in results["errors"][:3]:  # Show first 3 errors
                message += f"• {error}\n"
            if len(results["errors"]) > 3:
                message += f"• ... and {len(results['errors']) - 3} more\n"
            message += "\nThese will be cleaned up on next restart."

        message += "\n\n⚠️ IMPORTANT: The application will now FORCE CLOSE.\n"
        message += "This is normal - the database has been deleted.\n"
        message += "Simply restart Digital Workshop to use it with fresh settings."

        QMessageBox.information(self, "Reset Complete", message)

        # Force close the application immediately without cleanup
        # (cleanup will fail because database is gone)
        self.accept()

        # Kill the process immediately - no cleanup
        os._exit(0)  # Force exit without cleanup

    def _on_failed(self, error: str):
        """Handle reset failure."""
        self.progress_bar.setVisible(False)
        self.execute_button.setEnabled(True)
        self.cancel_button.setEnabled(True)
        self.backup_checkbox.setEnabled(True)

        QMessageBox.critical(
            self,
            "Reset Failed",
            f"Nuclear reset failed:\n\n{error}\n\n"
            "Some data may have been deleted. Check the logs for details.",
        )
