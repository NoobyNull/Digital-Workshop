#!/usr/bin/env python3
"""
License stub GUI for testing registration with reg.yax.family.

- Computes the same system_id fingerprint as the app (hostname + MAC, SHA256).
- Can POST a key/system_id to an endpoint (default: https://reg.yax.family/api/verify).
- Can simulate a server response locally by generating the expected proof hash.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import socket
import sys
import uuid
from typing import Dict, Tuple

import requests
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGridLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QWidget,
)


def compute_system_id() -> str:
    """Compute system fingerprint (hostname + MAC, SHA256)."""
    node = platform.node() or socket.gethostname()
    mac = uuid.getnode()
    payload = f"{node}|{mac}".encode("utf-8", "ignore")
    return hashlib.sha256(payload).hexdigest()[:16]


def compute_proof(system_id: str, key: str, token: str) -> str:
    """Compute expected proof: SHA256(system_id:key:token)."""
    material = f"{system_id}:{key}:{token}".encode("utf-8", "ignore")
    return hashlib.sha256(material).hexdigest()


def build_payload(key: str, system_id: str) -> Dict[str, str]:
    return {"key": key, "system_id": system_id}


def post_license(endpoint: str, payload: Dict[str, str]) -> Tuple[int, Dict]:
    resp = requests.post(endpoint, json=payload, timeout=10)
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}
    return resp.status_code, data


class LicenseWorker(QThread):
    finished = Signal(int, dict, str)

    def __init__(self, endpoint: str, key: str, system_id: str) -> None:
        super().__init__()
        self.endpoint = endpoint
        self.key = key
        self.system_id = system_id

    def run(self) -> None:
        try:
            status, data = post_license(
                self.endpoint, {"key": self.key, "system_id": self.system_id}
            )
            msg = ""
        except Exception as exc:
            status, data, msg = -1, {}, str(exc)
        self.finished.emit(status, data, msg)


class LicenseStubDialog(QDialog):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("License Stub Client")
        self.setMinimumWidth(640)
        self.system_id = compute_system_id()
        self._worker: LicenseWorker | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QGridLayout(self)

        layout.addWidget(QLabel("System ID:"), 0, 0)
        self.system_id_label = QLabel(self.system_id)
        self.system_id_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.system_id_label, 0, 1, 1, 2)

        layout.addWidget(QLabel("License Key:"), 1, 0)
        self.key_edit = QLineEdit()
        layout.addWidget(self.key_edit, 1, 1, 1, 2)

        layout.addWidget(QLabel("Endpoint:"), 2, 0)
        self.endpoint_edit = QLineEdit(
            os.getenv("DW_LICENSE_ENDPOINT", "https://reg.yax.family/api/verify")
        )
        layout.addWidget(self.endpoint_edit, 2, 1, 1, 2)

        self.simulate_btn = QPushButton("Simulate (local)")
        self.simulate_btn.clicked.connect(self._simulate)
        self.send_btn = QPushButton("Send to Server")
        self.send_btn.clicked.connect(self._send)
        layout.addWidget(self.simulate_btn, 3, 1)
        layout.addWidget(self.send_btn, 3, 2)

        layout.addWidget(QLabel("Output:"), 4, 0)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output, 5, 0, 1, 3)

        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons, 6, 0, 1, 3)

    def _simulate(self) -> None:
        key = self.key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "License Stub", "Please enter a license key.")
            return
        token = "TEST_TOKEN"
        proof = compute_proof(self.system_id, key, token)
        mock = {
            "status": "ok",
            "unlock": True,
            "system_id": self.system_id,
            "token": token,
            "proof": proof,
            "message": "Mock activation",
        }
        self._append_output("=== Simulated Response ===")
        self._append_output(json.dumps(mock, indent=2))

    def _send(self) -> None:
        key = self.key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "License Stub", "Please enter a license key.")
            return
        endpoint = self.endpoint_edit.text().strip()
        self._append_output(f"POST {endpoint} with key/system_id...")
        self.send_btn.setEnabled(False)
        self.simulate_btn.setEnabled(False)
        self._worker = LicenseWorker(endpoint, key, self.system_id)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()

    def _on_finished(self, status: int, data: dict, error: str) -> None:
        self.send_btn.setEnabled(True)
        self.simulate_btn.setEnabled(True)
        if error:
            self._append_output(f"Request failed: {error}")
            return
        self._append_output(f"Status: {status}")
        self._append_output(json.dumps(data, indent=2))
        token = data.get("token") or data.get("license_token")
        proof = data.get("proof")
        if token:
            expected = compute_proof(
                self.system_id, self.key_edit.text().strip(), token
            )
            self._append_output(f"Expected proof for returned token: {expected}")
            if proof:
                self._append_output(f"Matches server proof: {proof == expected}")

    def _append_output(self, text: str) -> None:
        self.output.append(text)
        self.output.append("")


def main(argv=None) -> int:
    app = QApplication(argv or sys.argv)
    dlg = LicenseStubDialog()
    dlg.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
