"""
Simple license manager for AI Description gating.

Performs a signed-key check against a remote endpoint and persists state
locally via QSettings. Only intended to guard hosted AI functionality.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import socket
import uuid
from dataclasses import dataclass, field
from typing import Optional, Tuple

import requests
from PySide6.QtCore import QSettings


DEFAULT_ENDPOINT = os.getenv(
    "DW_LICENSE_ENDPOINT", "https://reg.yax.family/api/verify"
)


def _compute_system_id() -> str:
    """Compute a stable-ish system fingerprint."""
    node = platform.node() or socket.gethostname()
    mac = uuid.getnode()
    payload = f"{node}|{mac}".encode("utf-8", "ignore")
    return hashlib.sha256(payload).hexdigest()[:16]


@dataclass
class LicenseState:
    key: Optional[str] = None
    system_id: Optional[str] = None
    status: str = "locked"
    token: Optional[str] = None
    message: Optional[str] = None


class LicenseManager:
    """Handles activation and persistence for AI gating."""

    def __init__(self, logger=None, endpoint: Optional[str] = None) -> None:
        self.logger = logger
        self.endpoint = endpoint or DEFAULT_ENDPOINT
        self.system_id = _compute_system_id()
        self.state = LicenseState(system_id=self.system_id)
        self._settings = QSettings()
        self._load_from_settings()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def is_ai_unlocked(self) -> bool:
        return (
            self.state.status == "unlocked"
            and self.state.system_id == self.system_id
            and bool(self.state.token)
        )

    def activation_message(self) -> str:
        if self.state.message:
            return self.state.message
        if self.is_ai_unlocked():
            return "AI access enabled"
        return "AI access locked"

    def activate(self, key: str) -> Tuple[bool, str]:
        """
        Activate against the remote endpoint.

        Returns:
            (success, message)
        """
        key = (key or "").strip()
        if not key:
            return False, "License key is required"

        payload = {"key": key, "system_id": self.system_id}
        try:
            resp = requests.post(self.endpoint, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:  # noqa: BLE001 - user-facing
            msg = f"Activation failed: {exc}"
            self._set_state("locked", key=key, message=msg)
            return False, msg

        status = str(data.get("status", "")).lower()
        unlocked = bool(data.get("unlock") or data.get("unlocked"))
        returned_sys = data.get("system_id")
        token = data.get("token") or data.get("license_token")
        proof = data.get("proof")
        if not unlocked or status not in {"ok", "success"}:
            msg = data.get("message") or "License rejected by server"
            self._set_state("locked", key=key, message=msg)
            return False, msg
        if returned_sys and returned_sys != self.system_id:
            msg = "System ID mismatch; activation denied"
            self._set_state("locked", key=key, message=msg)
            return False, msg
        if not self._verify_proof(key, token, proof):
            msg = "License verification failed (invalid proof)"
            self._set_state("locked", key=key, message=msg)
            return False, msg

        msg = data.get("message") or "License activated"
        self._set_state("unlocked", key=key, token=token, message=msg)
        return True, msg

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #
    def _load_from_settings(self) -> None:
        try:
            key = self._settings.value("license/key", type=str)
            status = self._settings.value("license/status", "locked", type=str)
            token = self._settings.value("license/token", type=str)
            stored_sys = self._settings.value("license/system_id", type=str)
            message = self._settings.value("license/message", type=str)
            self.state = LicenseState(
                key=key,
                status=status or "locked",
                token=token,
                system_id=stored_sys or self.system_id,
                message=message,
            )
        except Exception as exc:  # noqa: BLE001
            if self.logger:
                self.logger.debug("Failed to load license settings: %s", exc)
            self.state = LicenseState(system_id=self.system_id)

    def _save_to_settings(self) -> None:
        self._settings.setValue("license/key", self.state.key or "")
        self._settings.setValue("license/status", self.state.status)
        self._settings.setValue("license/token", self.state.token or "")
        self._settings.setValue("license/system_id", self.state.system_id or "")
        self._settings.setValue("license/message", self.state.message or "")
        self._settings.sync()

    def _set_state(
        self,
        status: str,
        key: Optional[str] = None,
        token: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        self.state.status = status
        if key is not None:
            self.state.key = key
        if token is not None:
            self.state.token = token
        self.state.system_id = self.system_id
        self.state.message = message
        self._save_to_settings()
        if self.logger:
            self.logger.info("License state updated: %s", status)

    def _verify_proof(self, key: str, token: Optional[str], proof: Optional[str]) -> bool:
        """
        Verify server response using a double-salt (system_id + key) hash.

        Expected proof: SHA256( system_id + ":" + key + ":" + token )
        """
        if not (proof and token):
            return False
        try:
            material = f"{self.system_id}:{key}:{token}".encode("utf-8", "ignore")
            digest = hashlib.sha256(material).hexdigest()
            return digest == proof
        except Exception:
            return False
