"""
License activation dialog.
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.core.license_manager import LicenseManager


class LicenseDialog(QDialog):
    """Simple dialog to collect a license key and activate against the server."""

    def __init__(
        self, license_manager: LicenseManager, parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Activate AI Access")
        self.setModal(True)
        self.license_manager = license_manager
        self._build_ui()
        self._refresh_status()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.system_id_label = QLabel(self.license_manager.system_id)
        self.system_id_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        form.addRow("System ID:", self.system_id_label)

        self.key_edit = QLineEdit()
        self.key_edit.setPlaceholderText("Enter license key")
        form.addRow("License Key:", self.key_edit)

        layout.addLayout(form)

        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        button_row = QHBoxLayout()
        self.activate_button = QPushButton("Check & Activate")
        self.activate_button.clicked.connect(self._on_activate_clicked)
        button_row.addWidget(self.activate_button)

        layout.addLayout(button_row)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _refresh_status(self, message: Optional[str] = None) -> None:
        msg = message or self.license_manager.activation_message()
        self.status_label.setText(msg)

    def _on_activate_clicked(self) -> None:
        key = self.key_edit.text()
        self.activate_button.setEnabled(False)
        try:
            ok, msg = self.license_manager.activate(key)
            self._refresh_status(msg)
            if ok:
                self.accept()
        finally:
            self.activate_button.setEnabled(True)
