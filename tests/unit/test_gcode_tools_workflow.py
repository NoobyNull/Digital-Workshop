"""Tests for G-code tools save/link flow and snapshot CSV IO."""

from __future__ import annotations

from typing import List

import pytest
from PySide6.QtWidgets import QFileDialog, QMessageBox

from src.gui.gcode_previewer_components.gcode_previewer_main import (
    link_gcode_file_to_project,
)
from src.gui.gcode_previewer_components.gcode_tools_widget import ToolSnapshotsWidget


class DummyDbManager:
    """Simple stand-in for DatabaseManager used in unit tests."""

    def __init__(self) -> None:
        self.calls: List[dict] = []

    def add_file(
        self,
        project_id: str,
        file_path: str,
        file_name: str,
        file_size=None,
        file_hash=None,
        status: str = "pending",
        link_type: str | None = None,
        original_path: str | None = None,
    ) -> int:
        self.calls.append(
            {
                "project_id": project_id,
                "file_path": file_path,
                "file_name": file_name,
                "file_size": file_size,
                "status": status,
                "link_type": link_type,
                "original_path": original_path,
            }
        )
        return len(self.calls)


def test_link_gcode_file_to_project_records_file(tmp_path, caplog):
    """Saving edited G-code should register a file record on the active project."""
    db = DummyDbManager()
    gcode_file = tmp_path / "edited.nc"
    gcode_file.write_text("G0 X0 Y0\nG1 X10 Y10\n")

    assert link_gcode_file_to_project(db, "proj-001", str(gcode_file), None)
    assert db.calls, "Expected add_file to be called"
    record = db.calls[0]
    assert record["project_id"] == "proj-001"
    assert record["file_path"] == str(gcode_file)
    assert record["file_name"] == "edited.nc"
    assert record["status"] == "gcode-editor"
    assert record["link_type"] == "gcode-editor"


def test_snapshot_csv_round_trip(tmp_path, qt_app, monkeypatch):
    """Snapshots exported to CSV should be parseable for later import."""
    widget = ToolSnapshotsWidget()
    rows = [
        {
            "tool_number": "T1",
            "diameter": "0.250",
            "material": "Maple",
            "feed_rate": "120",
            "plunge_rate": "30",
            "notes": "Roughing pass",
        },
        {
            "tool_number": "T2",
            "diameter": "0.125",
            "material": "Walnut",
            "feed_rate": "90",
            "plunge_rate": "15",
            "notes": "Finish",
        },
    ]
    widget.set_snapshots(rows)

    export_path = tmp_path / "snapshots.csv"
    monkeypatch.setattr(
        QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(export_path), "csv")
    )
    monkeypatch.setattr(QMessageBox, "information", lambda *args, **kwargs: None)
    monkeypatch.setattr(QMessageBox, "warning", lambda *args, **kwargs: None)

    widget._export_csv()
    assert export_path.exists(), "Export file was not created"

    imported: List[dict] = []
    widget.snapshots_imported.connect(lambda data: imported.extend(data))
    monkeypatch.setattr(
        QFileDialog, "getOpenFileName", lambda *args, **kwargs: (str(export_path), "csv")
    )

    widget._import_csv()
    assert imported == [
        {
            "tool_number": "T1",
            "diameter": "0.25",
            "material": "Maple",
            "feed_rate": "120",
            "plunge_rate": "30",
            "notes": "Roughing pass",
        },
        {
            "tool_number": "T2",
            "diameter": "0.125",
            "material": "Walnut",
            "feed_rate": "90",
            "plunge_rate": "15",
            "notes": "Finish",
        },
    ]

    widget.deleteLater()
