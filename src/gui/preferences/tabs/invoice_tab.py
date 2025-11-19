"""Preferences tab for invoice defaults used by the Project Cost Estimator."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QVBoxLayout,
    QWidget,
)

from src.core.logging_config import get_logger


class InvoicePreferencesTab(QWidget):
    """Allow users to define default invoice branding/terms."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.logger = get_logger(__name__)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        header = QLabel("Invoice Branding & Defaults")
        header.setStyleSheet("font-weight: bold; font-size: 13pt;")
        layout.addWidget(header)

        desc = QLabel(
            "These values pre-populate every invoice generated in the Project Cost Estimator. "
            "They are stored locally (QSettings) and never pushed to the database."
        )
        desc.setWordWrap(True)
        layout.addWidget(desc)

        branding_frame = QFrame()
        branding_layout = QGridLayout(branding_frame)

        self.logo_path_edit = QLineEdit()
        self.logo_path_edit.setPlaceholderText("Path to logo image (PNG, SVG, JPG)")
        self.browse_logo_button = QPushButton("Browse…")
        self.browse_logo_button.clicked.connect(self._choose_logo)

        branding_layout.addWidget(QLabel("Logo Path"), 0, 0)
        branding_layout.addWidget(self.logo_path_edit, 0, 1)
        branding_layout.addWidget(self.browse_logo_button, 0, 2)

        self.issuer_name_edit = QLineEdit()
        self.issuer_address_edit = QPlainTextEdit()
        self.issuer_address_edit.setPlaceholderText("Street, City, State ZIP")
        self.issuer_contact_edit = QLineEdit()
        self.invoice_prefix_edit = QLineEdit()
        self.invoice_prefix_edit.setPlaceholderText("e.g., INV-")

        branding_layout.addWidget(QLabel("Business Name"), 1, 0)
        branding_layout.addWidget(self.issuer_name_edit, 1, 1, 1, 2)
        branding_layout.addWidget(QLabel("Business Address"), 2, 0)
        branding_layout.addWidget(self.issuer_address_edit, 2, 1, 1, 2)
        branding_layout.addWidget(QLabel("Contact Info"), 3, 0)
        branding_layout.addWidget(self.issuer_contact_edit, 3, 1, 1, 2)
        branding_layout.addWidget(QLabel("Invoice Number Prefix"), 4, 0)
        branding_layout.addWidget(self.invoice_prefix_edit, 4, 1, 1, 2)

        layout.addWidget(branding_frame)

        defaults_frame = QFrame()
        defaults_layout = QFormLayout(defaults_frame)

        self.due_days_spin = QSpinBox()
        self.due_days_spin.setRange(1, 180)
        self.due_days_spin.setSuffix(" days")

        self.tax_spin = QDoubleSpinBox()
        self.tax_spin.setSuffix(" %")
        self.tax_spin.setDecimals(2)
        self.tax_spin.setRange(0.0, 100.0)

        self.default_notes_edit = QPlainTextEdit()
        self.default_notes_edit.setPlaceholderText("Default header notes / summary text.")

        self.default_terms_edit = QPlainTextEdit()
        self.default_terms_edit.setPlaceholderText("Default payment terms shown at the bottom of the invoice.")

        defaults_layout.addRow("Default Due Date Offset", self.due_days_spin)
        defaults_layout.addRow("Default Tax Percentage", self.tax_spin)
        defaults_layout.addRow("Default Header Notes", self.default_notes_edit)
        defaults_layout.addRow("Default Terms", self.default_terms_edit)

        layout.addWidget(defaults_frame)
        layout.addStretch()

    def _choose_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Logo Image",
            "",
            "Images (*.png *.jpg *.jpeg *.svg *.bmp);;All Files (*)",
        )
        if path:
            self.logo_path_edit.setText(path)

    def _settings(self) -> QSettings:
        settings = QSettings()
        settings.beginGroup("invoice")
        return settings

    def _load_settings(self) -> None:
        try:
            settings = self._settings()
            self.logo_path_edit.setText(settings.value("logo_path", "", type=str))
            self.issuer_name_edit.setText(settings.value("issuer_name", "", type=str))
            self.issuer_address_edit.setPlainText(settings.value("issuer_address", "", type=str))
            self.issuer_contact_edit.setText(settings.value("issuer_contact", "", type=str))
            self.invoice_prefix_edit.setText(settings.value("invoice_prefix", "INV-", type=str))
            self.due_days_spin.setValue(settings.value("due_days", 14, type=int))
            self.tax_spin.setValue(settings.value("default_tax_pct", 0.0, type=float))
            self.default_notes_edit.setPlainText(settings.value("default_notes", "", type=str))
            self.default_terms_edit.setPlainText(settings.value("default_terms", "", type=str))
            settings.endGroup()
            self.logger.info("Loaded invoice preferences")
        except Exception as exc:  # noqa: BLE001
            self.logger.warning("Failed to load invoice preferences: %s", exc)

    def save_settings(self) -> None:
        try:
            settings = self._settings()
            settings.setValue("logo_path", self.logo_path_edit.text().strip())
            settings.setValue("issuer_name", self.issuer_name_edit.text().strip())
            settings.setValue("issuer_address", self.issuer_address_edit.toPlainText().strip())
            settings.setValue("issuer_contact", self.issuer_contact_edit.text().strip())
            settings.setValue("invoice_prefix", self.invoice_prefix_edit.text().strip() or "INV-")
            settings.setValue("due_days", self.due_days_spin.value())
            settings.setValue("default_tax_pct", self.tax_spin.value())
            settings.setValue("default_notes", self.default_notes_edit.toPlainText().strip())
            settings.setValue("default_terms", self.default_terms_edit.toPlainText().strip())
            settings.endGroup()
            self.logger.info("Invoice preferences saved.")
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to save invoice preferences: %s", exc)

