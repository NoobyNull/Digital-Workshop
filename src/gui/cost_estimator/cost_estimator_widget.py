"""Invoice-style cost estimator widget for Digital Workshop projects."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import Qt, QDate, QSettings
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
    QDoubleSpinBox,
    QPlainTextEdit,
    QDateEdit,
    QHeaderView,
)

from src.core.logging_config import get_logger
from src.core.database_manager import get_database_manager
from .invoice_data_service import ProjectInvoiceDataService
from .invoice_models import InvoiceDocument, InvoiceHeader, InvoiceLineItem
from .invoice_pdf import InvoicePdfExporter
from .invoice_storage import InvoiceStorageManager

logger = get_logger(__name__)


class CostEstimatorWidget(QWidget):
    """Present project cost data as an invoice-style estimator with PDF/XML export."""

    TABLE_HEADERS = ["Description", "Category", "Qty", "Unit", "Rate", "Total"]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.db_manager = get_database_manager()
        self.storage = InvoiceStorageManager(self.db_manager)
        self.data_service = ProjectInvoiceDataService(self.db_manager)
        self.pdf_exporter = InvoicePdfExporter()

        self.current_project_id: Optional[str] = None
        self.suggestions: Dict[str, List[InvoiceLineItem]] = {}
        self.current_invoice = InvoiceDocument()
        self.logo_path: str = ""
        self._suppress_table_change = False

        self._build_ui()
        self._apply_preferences_defaults()
        self._configure_connections()

    # ------------------------------------------------------------------ #
    # UI setup
    # ------------------------------------------------------------------ #

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout()

        title = QLabel("Project Cost Estimator • Invoice View")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        main_layout.addWidget(title)

        main_layout.addWidget(self._build_header_box())
        main_layout.addWidget(self._build_line_items_box())
        main_layout.addWidget(self._build_totals_box())
        main_layout.addWidget(self._build_terms_box())
        main_layout.addLayout(self._build_actions_row())

        self.setLayout(main_layout)
        self._update_totals()

    def _build_header_box(self) -> QGroupBox:
        box = QGroupBox("Invoice Header")
        grid = QGridLayout()

        self.logo_label = QLabel("No Logo")
        self.logo_label.setFixedSize(140, 80)
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setStyleSheet("border: 1px dashed #888;")

        self.choose_logo_button = QPushButton("Choose Logo…")

        grid.addWidget(self.logo_label, 0, 0, 2, 1)
        grid.addWidget(self.choose_logo_button, 2, 0, 1, 1)

        self.project_name_edit = QLineEdit()
        self.project_reference_edit = QLineEdit()
        self.invoice_number_edit = QLineEdit()
        self.issue_date_edit = QDateEdit(QDate.currentDate())
        self.issue_date_edit.setCalendarPopup(True)
        self.due_date_edit = QDateEdit(QDate.currentDate().addDays(14))
        self.due_date_edit.setCalendarPopup(True)

        self.issuer_name_edit = QLineEdit()
        self.issuer_address_edit = QPlainTextEdit()
        self.issuer_contact_edit = QLineEdit()

        self.client_name_edit = QLineEdit()
        self.client_address_edit = QPlainTextEdit()

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Project summary or scope notes…")
        self.notes_edit.setFixedHeight(80)

        grid.addWidget(QLabel("Project Name"), 0, 1)
        grid.addWidget(self.project_name_edit, 0, 2)
        grid.addWidget(QLabel("Project Reference"), 0, 3)
        grid.addWidget(self.project_reference_edit, 0, 4)

        grid.addWidget(QLabel("Invoice #"), 1, 1)
        grid.addWidget(self.invoice_number_edit, 1, 2)
        grid.addWidget(QLabel("Issue Date"), 1, 3)
        grid.addWidget(self.issue_date_edit, 1, 4)

        grid.addWidget(QLabel("Due Date"), 2, 3)
        grid.addWidget(self.due_date_edit, 2, 4)

        grid.addWidget(QLabel("Issuer Name"), 3, 0)
        grid.addWidget(self.issuer_name_edit, 3, 1, 1, 2)
        grid.addWidget(QLabel("Issuer Address"), 4, 0)
        grid.addWidget(self.issuer_address_edit, 4, 1, 2, 2)
        grid.addWidget(QLabel("Issuer Contact"), 6, 0)
        grid.addWidget(self.issuer_contact_edit, 6, 1, 1, 2)

        grid.addWidget(QLabel("Client Name"), 3, 3)
        grid.addWidget(self.client_name_edit, 3, 4)
        grid.addWidget(QLabel("Client Address"), 4, 3)
        grid.addWidget(self.client_address_edit, 4, 4, 3, 1)

        grid.addWidget(QLabel("Header Notes"), 7, 0)
        grid.addWidget(self.notes_edit, 7, 1, 1, 4)

        box.setLayout(grid)
        return box

    def _build_line_items_box(self) -> QGroupBox:
        box = QGroupBox("Line Items")
        layout = QVBoxLayout()

        toolbar = QHBoxLayout()
        self.add_item_button = QPushButton("Add Item")
        self.remove_item_button = QPushButton("Remove Selected")
        self.import_button = QToolButton()
        self.import_button.setText("Import from Project ▼")
        self.import_menu = QMenu(self.import_button)
        self.import_button.setMenu(self.import_menu)
        self.import_button.setPopupMode(QToolButton.InstantPopup)
        self.refresh_button = QPushButton("Refresh Project Data")

        toolbar.addWidget(self.add_item_button)
        toolbar.addWidget(self.remove_item_button)
        toolbar.addWidget(self.import_button)
        toolbar.addStretch()
        toolbar.addWidget(self.refresh_button)

        self.items_table = QTableWidget(0, len(self.TABLE_HEADERS))
        self.items_table.setHorizontalHeaderLabels(self.TABLE_HEADERS)
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.items_table.verticalHeader().setVisible(False)

        layout.addLayout(toolbar)
        layout.addWidget(self.items_table)
        box.setLayout(layout)
        return box

    def _build_totals_box(self) -> QGroupBox:
        box = QGroupBox("Totals")
        grid = QGridLayout()

        self.tax_spin = QDoubleSpinBox()
        self.tax_spin.setSuffix(" %")
        self.tax_spin.setRange(0.0, 100.0)
        self.tax_spin.setValue(0.0)

        self.shipping_spin = QDoubleSpinBox()
        self.shipping_spin.setPrefix("$")
        self.shipping_spin.setRange(0.0, 1_000_000.0)

        self.discount_spin = QDoubleSpinBox()
        self.discount_spin.setPrefix("$")
        self.discount_spin.setRange(0.0, 1_000_000.0)

        self.subtotal_value = QLabel("$0.00")
        self.total_value = QLabel("$0.00")
        bold_font = QFont()
        bold_font.setBold(True)
        self.total_value.setFont(bold_font)

        grid.addWidget(QLabel("Tax"), 0, 0)
        grid.addWidget(self.tax_spin, 0, 1)
        grid.addWidget(QLabel("Shipping / Logistics"), 1, 0)
        grid.addWidget(self.shipping_spin, 1, 1)
        grid.addWidget(QLabel("Discount"), 2, 0)
        grid.addWidget(self.discount_spin, 2, 1)
        grid.addWidget(QLabel("Subtotal"), 0, 2)
        grid.addWidget(self.subtotal_value, 0, 3)
        grid.addWidget(QLabel("Grand Total"), 1, 2)
        grid.addWidget(self.total_value, 1, 3)

        box.setLayout(grid)
        return box

    def _build_terms_box(self) -> QGroupBox:
        box = QGroupBox("Terms & Notes")
        layout = QVBoxLayout()
        self.custom_terms_edit = QTextEdit()
        self.custom_terms_edit.setPlaceholderText(
            "Payment terms, delivery expectations, warranty notes…"
        )
        layout.addWidget(self.custom_terms_edit)
        box.setLayout(layout)
        return box

    def _build_actions_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        self.save_project_button = QPushButton("Save to Project (XML + PDF)")
        self.export_pdf_button = QPushButton("Export PDF As…")
        self.load_invoice_button = QPushButton("Load Saved Invoice…")
        row.addWidget(self.save_project_button)
        row.addWidget(self.export_pdf_button)
        row.addWidget(self.load_invoice_button)
        row.addStretch()
        return row

    def _configure_connections(self) -> None:
        self.add_item_button.clicked.connect(self._add_blank_item)
        self.remove_item_button.clicked.connect(self._remove_selected_items)
        self.refresh_button.clicked.connect(self._refresh_seed_data)
        self.choose_logo_button.clicked.connect(self._choose_logo)
        self.save_project_button.clicked.connect(self._save_invoice_to_project)
        self.export_pdf_button.clicked.connect(self._export_pdf_dialog)
        self.load_invoice_button.clicked.connect(self._load_invoice_dialog)
        self.tax_spin.valueChanged.connect(self._update_totals)
        self.discount_spin.valueChanged.connect(self._update_totals)
        self.shipping_spin.valueChanged.connect(self._update_totals)
        self.items_table.itemChanged.connect(self._on_table_item_changed)

        self.import_sources = {
            "Project Resources": "Resources",
            "G-code Runtime": "G-code Runtime",
            "Cut List": "Cut List",
            "Tools": "Tools",
        }
        for label, key in self.import_sources.items():
            action = self.import_menu.addAction(label)
            action.triggered.connect(
                lambda _=None, origin=key: self._apply_suggestions(origin)
            )

    def _load_invoice_preferences(self) -> Dict[str, object]:
        """Read persisted invoice defaults from QSettings."""
        try:
            settings = QSettings()
            settings.beginGroup("invoice")
            prefs = {
                "logo_path": settings.value("logo_path", "", type=str),
                "issuer_name": settings.value("issuer_name", "", type=str),
                "issuer_address": settings.value("issuer_address", "", type=str),
                "issuer_contact": settings.value("issuer_contact", "", type=str),
                "invoice_prefix": settings.value("invoice_prefix", "INV-", type=str),
                "due_days": settings.value("due_days", 14, type=int),
                "default_tax_pct": settings.value("default_tax_pct", 0.0, type=float),
                "default_notes": settings.value("default_notes", "", type=str),
                "default_terms": settings.value("default_terms", "", type=str),
            }
            settings.endGroup()
            return prefs
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load invoice preferences: %s", exc)
            return {}

    def _apply_preferences_to_header(
        self, header: InvoiceHeader, prefs: Optional[Dict[str, object]]
    ) -> InvoiceHeader:
        """Fill missing header fields from preferences."""
        prefs = prefs or {}
        header.issuer_name = header.issuer_name or prefs.get("issuer_name", "")
        header.issuer_address = header.issuer_address or prefs.get("issuer_address", "")
        header.issuer_contact = header.issuer_contact or prefs.get("issuer_contact", "")
        header.logo_path = header.logo_path or prefs.get("logo_path", "")
        header.notes = header.notes or prefs.get("default_notes", "")

        prefix = prefs.get("invoice_prefix") or "INV-"
        if not header.invoice_number:
            header.invoice_number = (
                f"{prefix}{QDate.currentDate().toString('yyyyMMdd-HHmm')}"
            )

        due_days = prefs.get("due_days")
        if (not header.due_date) and due_days is not None:
            try:
                offset = int(due_days)
            except (TypeError, ValueError):
                offset = 14
            header.due_date = QDate.currentDate().addDays(offset).toString("yyyy-MM-dd")
        return header

    def _apply_preferences_to_controls(
        self, prefs: Optional[Dict[str, object]]
    ) -> None:
        """Update UI controls (tax, terms) if user hasn't overridden them."""
        prefs = prefs or {}
        if (
            prefs.get("default_terms")
            and not self.custom_terms_edit.toPlainText().strip()
        ):
            self.custom_terms_edit.setPlainText(prefs["default_terms"])
        if prefs.get("default_tax_pct") is not None:
            try:
                self.tax_spin.setValue(float(prefs["default_tax_pct"]))
            except (TypeError, ValueError):
                pass
        if prefs.get("default_notes") and not self.notes_edit.toPlainText().strip():
            self.notes_edit.setPlainText(prefs["default_notes"])
        if prefs.get("logo_path") and not self.logo_path:
            self.logo_path = prefs["logo_path"]
            self._update_logo_label()

    def _apply_preferences_defaults(self) -> None:
        prefs = self._load_invoice_preferences()
        if not prefs:
            return
        header = self._apply_preferences_to_header(InvoiceHeader(), prefs)
        self._populate_header(header)
        self._apply_preferences_to_controls(prefs)

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def set_current_project(self, project_id: str) -> None:
        """Pass the selected project so we can query project data."""
        if project_id == self.current_project_id:
            return
        self.current_project_id = project_id
        self._refresh_seed_data()

    # ------------------------------------------------------------------ #
    # Data binding helpers
    # ------------------------------------------------------------------ #

    def _refresh_seed_data(self) -> None:
        if not self.current_project_id:
            QMessageBox.information(
                self, "Select Project", "Please select a project first."
            )
            return
        seed = self.data_service.collect_seed(self.current_project_id)
        self.suggestions = seed.suggestions or {}
        prefs = self._load_invoice_preferences()
        header = self._apply_preferences_to_header(seed.header, prefs)
        self._populate_header(header)
        self._populate_line_items([])
        if header.notes:
            self.notes_edit.setPlainText(header.notes)
        self._apply_preferences_to_controls(prefs)
        QMessageBox.information(
            self,
            "Project Data Loaded",
            "Project resources, G-code runtimes, cut lists, and tools are ready in the import menu.",
        )

    def _populate_header(self, header: InvoiceHeader) -> None:
        self.project_name_edit.setText(header.project_name)
        self.project_reference_edit.setText(header.project_reference)
        self.invoice_number_edit.setText(header.invoice_number)
        issue_date = QDate.fromString(header.issue_date or "", "yyyy-MM-dd")
        if not issue_date.isValid():
            issue_date = QDate.currentDate()
        due_date = QDate.fromString(header.due_date or "", "yyyy-MM-dd")
        if not due_date.isValid():
            due_date = QDate.currentDate()
        self.issue_date_edit.setDate(issue_date)
        self.due_date_edit.setDate(due_date)
        self.issuer_name_edit.setText(header.issuer_name)
        self.issuer_address_edit.setPlainText(header.issuer_address)
        self.issuer_contact_edit.setText(header.issuer_contact)
        self.client_name_edit.setText(header.client_name)
        self.client_address_edit.setPlainText(header.client_address)
        self.logo_path = header.logo_path or ""
        self.notes_edit.setPlainText(header.notes or "")
        self._update_logo_label()

    def _populate_line_items(self, items: List[InvoiceLineItem]) -> None:
        self._suppress_table_change = True
        self.items_table.setRowCount(0)
        for item in items:
            self._insert_table_row(item)
        self._suppress_table_change = False
        self._update_totals()

    def _insert_table_row(self, item: InvoiceLineItem) -> None:
        item.recalc()
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        self._set_table_item(row, 0, item.description)
        self._set_table_item(row, 1, item.category)
        self._set_table_item(row, 2, item.quantity, numeric=True)
        self._set_table_item(row, 3, item.unit)
        self._set_table_item(row, 4, item.rate, numeric=True)
        self._set_table_item(row, 5, item.total, numeric=True, editable=False)

    def _set_table_item(
        self,
        row: int,
        column: int,
        value,
        *,
        numeric: bool = False,
        editable: bool = True,
    ) -> None:
        widget_item = QTableWidgetItem()
        if numeric:
            widget_item.setData(Qt.EditRole, float(value))
        else:
            widget_item.setText(str(value) if value is not None else "")
        flags = widget_item.flags()
        if not editable:
            flags &= ~Qt.ItemIsEditable
        widget_item.setFlags(flags)
        self.items_table.setItem(row, column, widget_item)

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #

    def _add_blank_item(self) -> None:
        self._insert_table_row(
            InvoiceLineItem(
                description="New line item",
                category="General",
                quantity=1.0,
                unit="qty",
                rate=0.0,
            )
        )
        self._update_totals()

    def _remove_selected_items(self) -> None:
        rows = sorted(
            {index.row() for index in self.items_table.selectedIndexes()}, reverse=True
        )
        for row in rows:
            self.items_table.removeRow(row)
        self._update_totals()

    def _apply_suggestions(self, prefix: str) -> None:
        suggestions = self.suggestions.get(prefix) or []
        if not suggestions:
            QMessageBox.information(
                self, "No Data", f"No {prefix.lower()} data available."
            )
            return
        for item in suggestions:
            self._insert_table_row(item)
        self._update_totals()

    def _choose_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Logo",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)",
        )
        if path:
            self.logo_path = path
            self._update_logo_label()

    def _update_logo_label(self) -> None:
        if self.logo_path and Path(self.logo_path).exists():
            pixmap = QPixmap(self.logo_path)
            self.logo_label.setPixmap(
                pixmap.scaled(
                    self.logo_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
        else:
            self.logo_label.setPixmap(QPixmap())
            self.logo_label.setText("No Logo")

    # ------------------------------------------------------------------ #
    # Serialization helpers
    # ------------------------------------------------------------------ #

    def _build_invoice(self) -> InvoiceDocument:
        header = InvoiceHeader(
            project_name=self.project_name_edit.text().strip(),
            project_reference=self.project_reference_edit.text().strip(),
            invoice_number=self.invoice_number_edit.text().strip(),
            issue_date=self.issue_date_edit.date().toString("yyyy-MM-dd"),
            due_date=self.due_date_edit.date().toString("yyyy-MM-dd"),
            issuer_name=self.issuer_name_edit.text().strip(),
            issuer_address=self.issuer_address_edit.toPlainText().strip(),
            issuer_contact=self.issuer_contact_edit.text().strip(),
            client_name=self.client_name_edit.text().strip(),
            client_address=self.client_address_edit.toPlainText().strip(),
            logo_path=self.logo_path,
            notes=self.notes_edit.toPlainText().strip(),
        )

        items: List[InvoiceLineItem] = []
        for row in range(self.items_table.rowCount()):
            description = self._table_text(row, 0)
            if not description:
                continue
            items.append(
                InvoiceLineItem(
                    description=description,
                    category=self._table_text(row, 1) or "General",
                    quantity=self._table_float(row, 2),
                    unit=self._table_text(row, 3) or "",
                    rate=self._table_float(row, 4),
                    total=self._table_float(row, 5),
                )
            )

        invoice = InvoiceDocument(
            header=header,
            line_items=items,
            tax_percentage=self.tax_spin.value(),
            discount_amount=self.discount_spin.value(),
            shipping_amount=self.shipping_spin.value(),
            custom_terms=self.custom_terms_edit.toPlainText().strip(),
        )
        return invoice

    def _table_text(self, row: int, column: int) -> str:
        item = self.items_table.item(row, column)
        return item.text().strip() if item else ""

    def _table_float(self, row: int, column: int) -> float:
        item = self.items_table.item(row, column)
        try:
            return float(item.text()) if item else 0.0
        except (ValueError, TypeError):
            return 0.0

    def _populate_from_invoice(self, invoice: InvoiceDocument) -> None:
        self._populate_header(invoice.header)
        self.tax_spin.setValue(invoice.tax_percentage)
        self.discount_spin.setValue(invoice.discount_amount)
        self.shipping_spin.setValue(invoice.shipping_amount)
        self.custom_terms_edit.setPlainText(invoice.custom_terms)
        self._populate_line_items(invoice.line_items)

    # ------------------------------------------------------------------ #
    # File operations
    # ------------------------------------------------------------------ #

    def _sanitize_filename(self, value: str) -> str:
        value = value or "invoice"
        return re.sub(r"[^A-Za-z0-9._-]+", "_", value)

    def _save_invoice_to_project(self) -> None:
        if not self.current_project_id:
            QMessageBox.warning(self, "No Project", "Please select a project first.")
            return

        invoice = self._build_invoice()
        base_name = self._sanitize_filename(invoice.header.invoice_number or "")
        try:
            xml_path = self.storage.save_xml(
                self.current_project_id, invoice, filename=base_name or None
            )
            pdf_path = self.storage.default_pdf_path(
                self.current_project_id, filename=base_name or None
            )
            self.pdf_exporter.export(invoice, pdf_path)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Failed to save invoice: %s", exc)
            QMessageBox.critical(self, "Save Failed", str(exc))
            return

        QMessageBox.information(
            self,
            "Saved",
            f"Invoice saved to:\n• {xml_path}\n• {pdf_path}",
        )

    def _export_pdf_dialog(self) -> None:
        invoice = self._build_invoice()
        default_name = self._sanitize_filename(
            invoice.header.invoice_number or "invoice"
        )
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Invoice PDF",
            f"{default_name}.pdf",
            "PDF Files (*.pdf)",
        )
        if not path:
            return
        try:
            self.pdf_exporter.export(invoice, Path(path))
            QMessageBox.information(
                self, "PDF Exported", f"Invoice exported to:\n{path}"
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Export Failed", str(exc))

    def _load_invoice_dialog(self) -> None:
        invoice_dir = self.storage.get_invoice_directory(self.current_project_id)
        start_dir = str(invoice_dir) if invoice_dir else ""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Invoice XML",
            start_dir,
            "Invoice XML (*.xml)",
        )
        if not path:
            return
        try:
            invoice = self.storage.load_xml(self.current_project_id, Path(path))
            self._populate_from_invoice(invoice)
            QMessageBox.information(self, "Loaded", f"Invoice loaded from {path}")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Load Failed", str(exc))

    # ------------------------------------------------------------------ #
    # Table + totals updates
    # ------------------------------------------------------------------ #

    def _on_table_item_changed(self, item: QTableWidgetItem) -> None:
        if self._suppress_table_change:
            return
        row = item.row()
        if item.column() in (2, 4):
            qty = self._table_float(row, 2)
            rate = self._table_float(row, 4)
            total = qty * rate
            self._suppress_table_change = True
            self._set_table_item(row, 5, total, numeric=True, editable=False)
            self._suppress_table_change = False
        self._update_totals()

    def _update_totals(self) -> None:
        invoice = self._build_invoice()
        self.subtotal_value.setText(f"${invoice.subtotal():.2f}")
        self.total_value.setText(f"${invoice.total():.2f}")

    # Public methods for main window integrations

    def save_to_project(self) -> None:  # pragma: no cover - invoked by menu action
        self._save_invoice_to_project()

    def load_from_project(self) -> None:  # pragma: no cover - invoked by menu action
        self._load_invoice_dialog()
