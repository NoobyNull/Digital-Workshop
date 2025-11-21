"""Dialog used to capture a structured tool snapshot."""

from __future__ import annotations

from typing import Any, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)


class ToolSnapshotDialog(QDialog):
    """Collects tool metadata and feed parameters for a snapshot row."""

    def __init__(
        self,
        defaults: Optional[Dict[str, Any]] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Capture Tool Snapshot")
        self.setMinimumWidth(420)

        defaults = defaults or {}

        layout = QVBoxLayout(self)
        layout.addWidget(
            QLabel("Review the captured settings before saving them to the project.")
        )

        form_layout = QFormLayout()
        form_layout.setLabelAlignment(Qt.AlignRight)

        self.tool_number_edit = QLineEdit(self._format(defaults.get("tool_number")))
        self.tool_number_edit.setPlaceholderText("T1")
        form_layout.addRow("Tool #", self.tool_number_edit)

        self.diameter_edit = QLineEdit(self._format(defaults.get("diameter")))
        self.diameter_edit.setPlaceholderText("0.250")
        form_layout.addRow("Diameter", self.diameter_edit)

        self.material_edit = QLineEdit(self._format(defaults.get("material")))
        self.material_edit.setPlaceholderText("Maple")
        form_layout.addRow("Material", self.material_edit)

        self.feed_edit = QLineEdit(self._format(defaults.get("feed_rate")))
        self.feed_edit.setPlaceholderText("120.0")
        form_layout.addRow("Feed", self.feed_edit)

        self.plunge_edit = QLineEdit(self._format(defaults.get("plunge_rate")))
        self.plunge_edit.setPlaceholderText("45.0")
        form_layout.addRow("Plunge", self.plunge_edit)

        self.notes_edit = QPlainTextEdit()
        self.notes_edit.setPlainText(
            self._format(defaults.get("notes"), allow_dash=False)
        )
        self.notes_edit.setPlaceholderText(
            "Describe why this toolpath snapshot matters."
        )
        form_layout.addRow("Notes", self.notes_edit)

        layout.addLayout(form_layout)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _format(self, value: Optional[Any], *, allow_dash: bool = True) -> str:
        if value is None:
            return "-" if allow_dash else ""
        text = str(value).strip()
        return text if text else ("-" if allow_dash else "")

    def _to_float(self, text: str) -> Optional[float]:
        stripped = text.strip()
        if not stripped or stripped == "-":
            return None
        try:
            return float(stripped)
        except ValueError:
            return None

    def get_snapshot_data(self) -> Dict[str, Any]:
        """Return the sanitized values entered by the user."""
        return {
            "tool_number": self.tool_number_edit.text().strip() or None,
            "diameter": self._to_float(self.diameter_edit.text()),
            "material": self.material_edit.text().strip() or None,
            "feed_rate": self._to_float(self.feed_edit.text()),
            "plunge_rate": self._to_float(self.plunge_edit.text()),
            "notes": self.notes_edit.toPlainText().strip() or None,
        }
