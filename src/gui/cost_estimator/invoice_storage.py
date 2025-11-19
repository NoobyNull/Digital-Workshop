"""Handle persistence of invoice artifacts within project folders."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.core.logging_config import get_logger
from .invoice_models import InvoiceDocument

logger = get_logger(__name__)


class InvoiceStorageManager:
    """Stores invoice XML/PDF files alongside the project without touching the DB."""

    def __init__(self, db_manager) -> None:
        self.db_manager = db_manager

    def _get_project_folder(self, project_id: Optional[str]) -> Optional[Path]:
        if not project_id or not self.db_manager:
            return None
        project = self.db_manager.get_project(project_id)
        if not project:
            return None
        base_path = project.get("base_path")
        if not base_path:
            return None
        return Path(base_path)

    def get_invoice_directory(self, project_id: Optional[str]) -> Optional[Path]:
        project_folder = self._get_project_folder(project_id)
        if not project_folder:
            return None
        invoice_dir = project_folder / "cost_estimator" / "invoices"
        invoice_dir.mkdir(parents=True, exist_ok=True)
        return invoice_dir

    def save_xml(self, project_id: str, invoice: InvoiceDocument, filename: Optional[str] = None) -> Path:
        invoice_dir = self.get_invoice_directory(project_id)
        if not invoice_dir:
            raise FileNotFoundError("Project folder unavailable; cannot save invoice.")
        base_name = filename or datetime.now().strftime("invoice-%Y%m%d-%H%M%S")
        xml_path = invoice_dir / f"{base_name}.xml"
        invoice.write_xml(xml_path)
        logger.info("Saved invoice XML to %s", xml_path)
        return xml_path

    def load_xml(self, project_id: str, xml_path: Path) -> InvoiceDocument:
        if not xml_path.exists():
            raise FileNotFoundError(xml_path)
        return InvoiceDocument.from_xml(xml_path)

    def list_invoices(self, project_id: str) -> List[Path]:
        invoice_dir = self.get_invoice_directory(project_id)
        if not invoice_dir or not invoice_dir.exists():
            return []
        return sorted(invoice_dir.glob("*.xml"))

    def default_pdf_path(self, project_id: str, filename: Optional[str] = None) -> Path:
        invoice_dir = self.get_invoice_directory(project_id)
        if not invoice_dir:
            raise FileNotFoundError("Project folder unavailable; cannot build PDF path.")
        base_name = filename or datetime.now().strftime("invoice-%Y%m%d-%H%M%S")
        return invoice_dir / f"{base_name}.pdf"
