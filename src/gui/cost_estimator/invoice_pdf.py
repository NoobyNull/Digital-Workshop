"""Render invoice documents to PDF using Qt's rich text engine."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtGui import QFont, QTextDocument
from PySide6.QtPrintSupport import QPrinter

from src.core.logging_config import get_logger
from .invoice_models import InvoiceDocument

logger = get_logger(__name__)


class InvoicePdfExporter:
    """Converts an InvoiceDocument into a PDF with an invoice-style layout."""

    def __init__(self) -> None:
        self.base_font = QFont("Helvetica", 10)

    def export(self, invoice: InvoiceDocument, output_path: Path) -> None:
        """Render invoice as PDF."""
        html = self._render_html(invoice)
        doc = QTextDocument()
        doc.setDefaultFont(self.base_font)
        doc.setHtml(html)

        printer = QPrinter(QPrinter.HighResolution)
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(str(output_path))
        printer.setCreator("Digital Workshop - Project Cost Estimator")
        doc.print(printer)
        logger.info("Exported invoice PDF to %s", output_path)

    # ------------------------------------------------------------------ #
    # HTML Rendering helpers
    # ------------------------------------------------------------------ #

    def _render_html(self, invoice: InvoiceDocument) -> str:
        header = invoice.header
        logo_html = ""
        if header.logo_path:
            logo_path = Path(header.logo_path)
            if logo_path.exists():
                logo_html = f'<img src="{logo_path.as_posix()}" style="max-height:80px;" />'

        address_html = f"""
            <table width="100%" style="margin-bottom: 20px;">
                <tr>
                    <td width="50%">
                        <h2>{header.issuer_name or "Supplier"}</h2>
                        <div>{header.issuer_address or ""}</div>
                        <div>{header.issuer_contact or ""}</div>
                    </td>
                    <td width="50%" style="text-align:right;">
                        {logo_html}
                        <h1>Invoice</h1>
                        <div><b>Invoice #:</b> {header.invoice_number}</div>
                        <div><b>Issue Date:</b> {header.issue_date}</div>
                        <div><b>Due Date:</b> {header.due_date}</div>
                    </td>
                </tr>
            </table>
        """

        client_html = f"""
            <table width="100%" style="margin-bottom: 20px;">
                <tr>
                    <td width="50%">
                        <strong>Bill To:</strong><br/>
                        {header.client_name or "Client"}<br/>
                        {header.client_address or ""}
                    </td>
                    <td width="50%" style="text-align:right;">
                        <strong>Project:</strong> {header.project_name}<br/>
                        <strong>Reference:</strong> {header.project_reference}<br/>
                        <strong>Notes:</strong> {header.notes or ""}
                    </td>
                </tr>
            </table>
        """

        rows_html = "".join(
            f"""
                <tr>
                    <td>{item.description}</td>
                    <td>{item.category}</td>
                    <td style="text-align:right;">{item.quantity:.2f}</td>
                    <td>{item.unit}</td>
                    <td style="text-align:right;">${item.rate:.2f}</td>
                    <td style="text-align:right;">${item.total:.2f}</td>
                </tr>
            """
            for item in invoice.line_items
        )

        if not rows_html:
            rows_html = """
                <tr>
                    <td colspan="6" style="text-align:center; color:#888;">No line items yet</td>
                </tr>
            """

        table_html = f"""
            <table width="100%" cellspacing="0" cellpadding="6" border="1" style="border-collapse:collapse;">
                <thead style="background:#f0f0f0;">
                    <tr>
                        <th>Description</th>
                        <th>Category</th>
                        <th>Qty</th>
                        <th>Unit</th>
                        <th>Rate</th>
                        <th>Total</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        """

        summary_html = f"""
            <table width="100%" style="margin-top: 20px;">
                <tr>
                    <td width="60%">
                        <strong>Terms & Notes</strong><br/>
                        {invoice.custom_terms or "Payment due upon receipt unless otherwise agreed."}
                    </td>
                    <td width="40%">
                        <table width="100%" cellspacing="0" cellpadding="4">
                            <tr>
                                <td>Subtotal:</td>
                                <td style="text-align:right;">${invoice.subtotal():.2f}</td>
                            </tr>
                            <tr>
                                <td>Tax ({invoice.tax_percentage:.2f}%):</td>
                                <td style="text-align:right;">${invoice.tax_amount():.2f}</td>
                            </tr>
                            <tr>
                                <td>Shipping:</td>
                                <td style="text-align:right;">${invoice.shipping_amount:.2f}</td>
                            </tr>
                            <tr>
                                <td>Discount:</td>
                                <td style="text-align:right;">-${invoice.discount_amount:.2f}</td>
                            </tr>
                            <tr style="font-weight:bold;">
                                <td>Total:</td>
                                <td style="text-align:right;">${invoice.total():.2f}</td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        """

        return f"""
            <html>
                <head>
                    <meta charset="utf-8" />
                    <style>
                        body {{ font-family: 'Helvetica', Arial, sans-serif; font-size: 10pt; }}
                        h1 {{ margin: 0; }}
                        h2 {{ margin: 0 0 5px 0; }}
                        table {{ width: 100%; }}
                        th, td {{ padding: 6px; }}
                    </style>
                </head>
                <body>
                    {address_html}
                    {client_html}
                    {table_html}
                    {summary_html}
                </body>
            </html>
        """
