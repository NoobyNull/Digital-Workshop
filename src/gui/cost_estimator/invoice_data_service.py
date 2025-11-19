"""Aggregate project data for invoice seeds."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PySide6.QtCore import QDate

from src.core.logging_config import get_logger
from .invoice_models import InvoiceHeader, InvoiceLineItem, InvoiceSeed

logger = get_logger(__name__)


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


@dataclass
class GcodeMetrics:
    runtime_hours: float = 0.0
    machine_rate: float = 0.0


class ProjectInvoiceDataService:
    """Collects project metadata to pre-populate invoice line items."""

    def __init__(self, db_manager) -> None:
        self.db_manager = db_manager

    def collect_seed(self, project_id: Optional[str]) -> InvoiceSeed:
        """Build initial header defaults and suggested line items."""
        if not project_id or not self.db_manager:
            logger.warning("No project ID provided for invoice seed collection")
            return InvoiceSeed()

        project = self.db_manager.get_project(project_id)
        if not project:
            logger.warning("Project %s not found for invoice seed", project_id)
            return InvoiceSeed()

        header = InvoiceHeader(
            project_name=project.get("name", "Untitled Project"),
            project_reference=project.get("structure_type") or project.get("import_tag") or "",
            invoice_number=f"INV-{datetime.now().strftime('%Y%m%d-%H%M')}",
            issue_date=QDate.currentDate().toString("yyyy-MM-dd"),
            issuer_name="Digital Workshop",
            issuer_address="",
            issuer_contact="",
            client_name="",
            client_address="",
            logo_path="",
            notes="",
        )
        header.due_date = (
            QDate.currentDate().addDays(14).toString("yyyy-MM-dd")
        )  # default 2 weeks

        suggestions = {
            "Resources": self._collect_resources(project_id),
            "G-code Runtime": self._collect_gcode_runtime(project_id),
            "Cut List": self._collect_cutlist(project_id),
            "Tools": self._collect_tools(project_id),
        }

        project_folder = project.get("base_path")
        project_path = Path(project_folder) if project_folder else None
        return InvoiceSeed(header=header, suggestions=suggestions, project_folder=project_path)

    # ------------------------------------------------------------------ #
    # Collectors
    # ------------------------------------------------------------------ #

    def _collect_resources(self, project_id: str) -> List[InvoiceLineItem]:
        """Translate project resource links into suggested line items."""
        items: List[InvoiceLineItem] = []
        try:
            rows = self.db_manager.list_project_models(project_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to collect project resources: %s", exc)
            return items

        for row in rows or []:
            label = row.get("role") or "Resource"
            model_id = row.get("model_id") or row.get("id")
            desc = f"{label} #{model_id}"
            metadata = {}
            if row.get("material_tag"):
                metadata["material_tag"] = row["material_tag"]
            if row.get("version"):
                metadata["version"] = row["version"]

            items.append(
                InvoiceLineItem(
                    description=f"Project resource - {desc}",
                    category="Project Resources",
                    quantity=1,
                    unit="lot",
                    rate=0.0,
                    metadata=metadata,
                )
            )
        return items

    def _collect_gcode_runtime(self, project_id: str) -> List[InvoiceLineItem]:
        """Use stored G-code metrics to create machine-time suggestions."""
        items: List[InvoiceLineItem] = []
        try:
            operations = self.db_manager.list_gcode_operations(project_id=project_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to list gcode operations: %s", exc)
            return items

        for operation in operations or []:
            operation_id = operation.get("id")
            if not operation_id:
                continue

            try:
                versions = self.db_manager.list_gcode_versions(operation_id)
            except Exception as exc:  # noqa: BLE001
                logger.debug("Could not list versions for op %s: %s", operation_id, exc)
                continue

            if not versions:
                continue

            latest_version = max(
                versions,
                key=lambda row: row.get("updated_at") or row.get("created_at") or "",
            )
            version_id = latest_version.get("id")
            metrics = None
            if version_id is not None:
                try:
                    metrics = self.db_manager.get_gcode_metrics(version_id)
                except Exception as exc:  # noqa: BLE001
                    logger.debug("No metrics for version %s: %s", version_id, exc)

            runtime = 0.0
            if metrics:
                runtime = (
                    _safe_float(metrics.get("best_case_time_seconds"))
                    or _safe_float(metrics.get("rough_time_seconds"))
                    or _safe_float(metrics.get("simulated_time_seconds"))
                )
            runtime_hours = runtime / 3600.0 if runtime else 0.0
            if runtime_hours <= 0:
                continue

            hourly_rate = _safe_float(metrics.get("machine_hourly_rate"), 85.0)
            desc = operation.get("name") or f"G-code Op {operation_id}"
            metadata = {
                "operation_id": str(operation_id),
                "version_id": str(version_id or ""),
                "runtime_seconds": f"{runtime:.2f}",
            }
            items.append(
                InvoiceLineItem(
                    description=f"CNC runtime - {desc}",
                    category="Machine Time",
                    quantity=round(runtime_hours, 2),
                    unit="hrs",
                    rate=hourly_rate,
                    metadata=metadata,
                )
            )
        return items

    def _collect_cutlist(self, project_id: str) -> List[InvoiceLineItem]:
        """Create summary lines for material usage from the cut list."""
        items: List[InvoiceLineItem] = []
        try:
            scenarios = self.db_manager.list_cutlist_scenarios(project_id, status=None)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Cut list scenarios unavailable: %s", exc)
            return items

        if not scenarios:
            return items

        scenario = scenarios[0]
        scenario_id = scenario.get("id")
        scenario_name = scenario.get("name") or "Cut List"

        try:
            pieces = self.db_manager.list_cutlist_pieces(scenario_id)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Could not list cutlist pieces: %s", exc)
            pieces = []

        total_qty = 0
        total_area = 0.0
        for piece in pieces or []:
            qty = int(piece.get("quantity") or 0)
            total_qty += qty
            width = _safe_float(piece.get("width"))
            height = _safe_float(piece.get("height"))
            if width and height:
                total_area += width * height * max(qty, 1)

        description = f"Material allocation - {scenario_name}"
        metadata = {
            "scenario_id": str(scenario_id),
            "piece_count": str(len(pieces or [])),
            "total_area": f"{total_area:.2f}",
        }
        items.append(
            InvoiceLineItem(
                description=description,
                category="Materials",
                quantity=max(total_qty, 1),
                unit="pcs",
                rate=0.0,
                metadata=metadata,
            )
        )
        return items

    def _collect_tools(self, project_id: str) -> List[InvoiceLineItem]:
        """Summarize tool usage from G-code snapshots."""
        items: List[InvoiceLineItem] = []
        try:
            operations = self.db_manager.list_gcode_operations(project_id=project_id)
        except Exception:
            operations = []

        for operation in operations or []:
            op_id = operation.get("id")
            if not op_id:
                continue
            try:
                versions = self.db_manager.list_gcode_versions(op_id)
            except Exception:
                continue

            for version in versions or []:
                version_id = version.get("id")
                if version_id is None:
                    continue
                try:
                    snapshots = self.db_manager.list_gcode_tool_snapshots(version_id)
                except Exception:
                    continue
                for snapshot in snapshots or []:
                    tool_label = snapshot.get("tool_number") or snapshot.get("tool_id") or "Tool"
                    metadata = {
                        "version_id": str(version_id),
                        "tool_number": str(snapshot.get("tool_number") or ""),
                        "provider": snapshot.get("provider_name") or "",
                    }
                    items.append(
                        InvoiceLineItem(
                            description=f"Tool wear allowance - {tool_label}",
                            category="Tools & Consumables",
                            quantity=1,
                            unit="ea",
                            rate=0.0,
                            metadata=metadata,
                        )
                    )
        return items
