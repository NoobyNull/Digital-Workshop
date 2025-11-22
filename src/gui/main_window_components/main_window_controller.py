"""
Controller stub for main window orchestration.

Goal: lift non-UI logic out of main_window.py into manageable pieces.
"""

from __future__ import annotations

from typing import Optional

from src.core.logging_config import get_logger


class MainWindowController:
    """Thin controller to manage main window state and services."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)
        self.current_project_id: Optional[str] = None
        self.current_project_name: str = ""

    def set_project(self, project_id: Optional[str], project_name: str = "") -> None:
        """Track the active project selection."""
        self.current_project_id = project_id
        self.current_project_name = project_name or ""
