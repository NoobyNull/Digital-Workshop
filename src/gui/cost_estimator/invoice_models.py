"""Data models for invoice-style project cost estimates."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from xml.etree import ElementTree as ET


def _float(value: Optional[float], default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass
class InvoiceHeader:
    """Top-of-document metadata shown in the invoice layout."""

    project_name: str = ""
    project_reference: str = ""
    invoice_number: str = ""
    issue_date: str = datetime.now().strftime("%Y-%m-%d")
    due_date: str = ""
    issuer_name: str = ""
    issuer_address: str = ""
    issuer_contact: str = ""
    client_name: str = ""
    client_address: str = ""
    logo_path: str = ""
    notes: str = ""

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: Optional[Dict[str, str]]) -> "InvoiceHeader":
        if not payload:
            return cls()
        return cls(**{k: payload.get(k, "") for k in cls().__dataclass_fields__.keys()})


@dataclass
class InvoiceLineItem:
    """Represent a row in the invoice table."""

    description: str
    category: str = "General"
    quantity: float = 1.0
    unit: str = "hrs"
    rate: float = 0.0
    total: float = 0.0
    metadata: Dict[str, str] = field(default_factory=dict)

    def recalc(self) -> None:
        """Update total based on quantity and rate."""
        qty = _float(self.quantity)
        rate = _float(self.rate)
        self.total = qty * rate

    def to_dict(self) -> Dict:
        self.recalc()
        return {
            "description": self.description,
            "category": self.category,
            "quantity": self.quantity,
            "unit": self.unit,
            "rate": self.rate,
            "total": self.total,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, payload: Dict) -> "InvoiceLineItem":
        if not payload:
            return cls(description="")
        item = cls(
            description=payload.get("description", ""),
            category=payload.get("category", "General"),
            quantity=_float(payload.get("quantity"), 0.0),
            unit=payload.get("unit", ""),
            rate=_float(payload.get("rate"), 0.0),
            total=_float(payload.get("total"), 0.0),
            metadata=payload.get("metadata", {}) or {},
        )
        item.recalc()
        return item


@dataclass
class InvoiceDocument:
    """Full invoice document containing header, line items, and totals."""

    header: InvoiceHeader = field(default_factory=InvoiceHeader)
    line_items: List[InvoiceLineItem] = field(default_factory=list)
    tax_percentage: float = 0.0
    discount_amount: float = 0.0
    shipping_amount: float = 0.0
    custom_terms: str = ""

    def subtotal(self) -> float:
        for item in self.line_items:
            item.recalc()
        return sum(item.total for item in self.line_items)

    def tax_amount(self) -> float:
        return self.subtotal() * (_float(self.tax_percentage) / 100.0)

    def total(self) -> float:
        return (
            self.subtotal()
            + self.tax_amount()
            + _float(self.shipping_amount)
            - _float(self.discount_amount)
        )

    def to_dict(self) -> Dict:
        return {
            "header": self.header.to_dict(),
            "line_items": [item.to_dict() for item in self.line_items],
            "tax_percentage": self.tax_percentage,
            "discount_amount": self.discount_amount,
            "shipping_amount": self.shipping_amount,
            "custom_terms": self.custom_terms,
        }

    def to_xml(self) -> ET.Element:
        """Serialize invoice to XML for archival in project folders."""
        root = ET.Element("Invoice")
        header_el = ET.SubElement(root, "Header")
        for key, value in self.header.to_dict().items():
            child = ET.SubElement(header_el, key)
            child.text = value or ""

        items_el = ET.SubElement(root, "LineItems")
        for item in self.line_items:
            item.recalc()
            item_el = ET.SubElement(items_el, "Item")
            for field_name, field_value in item.to_dict().items():
                if field_name == "metadata":
                    metadata_el = ET.SubElement(item_el, "Metadata")
                    for meta_key, meta_value in field_value.items():
                        m_child = ET.SubElement(metadata_el, meta_key)
                        m_child.text = str(meta_value)
                    continue
                child = ET.SubElement(item_el, field_name)
                child.text = str(field_value)

        summary_el = ET.SubElement(root, "Summary")
        ET.SubElement(summary_el, "Subtotal").text = f"{self.subtotal():.2f}"
        ET.SubElement(summary_el, "TaxPercentage").text = f"{self.tax_percentage:.2f}"
        ET.SubElement(summary_el, "TaxAmount").text = f"{self.tax_amount():.2f}"
        ET.SubElement(summary_el, "DiscountAmount").text = f"{self.discount_amount:.2f}"
        ET.SubElement(summary_el, "ShippingAmount").text = f"{self.shipping_amount:.2f}"
        ET.SubElement(summary_el, "GrandTotal").text = f"{self.total():.2f}"
        ET.SubElement(summary_el, "CustomTerms").text = self.custom_terms or ""
        return root

    def write_xml(self, file_path: Path) -> None:
        tree = ET.ElementTree(self.to_xml())
        file_path.parent.mkdir(parents=True, exist_ok=True)
        tree.write(file_path, encoding="utf-8", xml_declaration=True)

    @classmethod
    def from_dict(cls, payload: Optional[Dict]) -> "InvoiceDocument":
        payload = payload or {}
        header = InvoiceHeader.from_dict(payload.get("header"))
        items = [
            InvoiceLineItem.from_dict(item_payload)
            for item_payload in payload.get("line_items", [])
        ]
        doc = cls(
            header=header,
            line_items=items,
            tax_percentage=_float(payload.get("tax_percentage"), 0.0),
            discount_amount=_float(payload.get("discount_amount"), 0.0),
            shipping_amount=_float(payload.get("shipping_amount"), 0.0),
            custom_terms=payload.get("custom_terms", ""),
        )
        return doc

    @classmethod
    def from_xml(cls, xml_path: Path) -> "InvoiceDocument":
        tree = ET.parse(xml_path)
        root = tree.getroot()
        header_payload = {}
        header_el = root.find("Header")
        if header_el is not None:
            for child in header_el:
                header_payload[child.tag] = child.text or ""
        items_payload: List[Dict] = []
        items_el = root.find("LineItems")
        if items_el is not None:
            for item_el in items_el.findall("Item"):
                payload = {}
                metadata = {}
                for child in item_el:
                    if child.tag == "Metadata":
                        for meta_child in child:
                            metadata[meta_child.tag] = meta_child.text or ""
                    else:
                        payload[child.tag] = child.text or ""
                if metadata:
                    payload["metadata"] = metadata
                items_payload.append(payload)

        summary_el = root.find("Summary")
        summary_payload = {}
        if summary_el is not None:
            for child in summary_el:
                summary_payload[child.tag] = child.text or ""

        doc = cls.from_dict(
            {
                "header": header_payload,
                "line_items": items_payload,
                "tax_percentage": summary_payload.get("TaxPercentage"),
                "discount_amount": summary_payload.get("DiscountAmount"),
                "shipping_amount": summary_payload.get("ShippingAmount"),
                "custom_terms": summary_payload.get("CustomTerms"),
            }
        )
        return doc


@dataclass
class InvoiceSeed:
    """Initial data collected from project subsystems."""

    header: InvoiceHeader = field(default_factory=InvoiceHeader)
    suggestions: Dict[str, List[InvoiceLineItem]] = field(default_factory=dict)
    project_folder: Optional[Path] = None
