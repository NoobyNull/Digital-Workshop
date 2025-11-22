"""
Minimal shared UI primitives to reduce per-widget boilerplate.

Helpers here keep status/progress updates consistent across dialogs and loaders.
"""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QProgressBar, QPushButton


def set_progress(
    progress_bar: QProgressBar, status_label: QLabel, value: int, message: str
) -> None:
    """Set progress bar value and accompanying status label text."""
    progress_bar.setValue(value)
    status_label.setText(message)


def set_busy_state(
    load_button: QPushButton, cancel_button: QPushButton, busy: bool
) -> None:
    """Toggle button enabled states for a busy operation."""
    load_button.setEnabled(not busy)
    cancel_button.setEnabled(busy)
