"""
Controller stub for feeds and speeds widget to separate logic from UI.
"""

from __future__ import annotations

from src.core.logging_config import get_logger


class FeedsAndSpeedsController:
    """Thin controller placeholder for feeds/speeds logic."""

    def __init__(self) -> None:
        self.logger = get_logger(__name__)

    # TODO: move non-UI logic from feeds_and_speeds_widget here
