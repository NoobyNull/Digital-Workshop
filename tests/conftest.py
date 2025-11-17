"""Shared pytest fixtures for the Digital Workshop test suite.

This module centralizes common fixtures so tests can depend on them
without re-implementing boilerplate in each file.
"""

from __future__ import annotations

import os
import sys
from typing import Generator

import pytest
from PySide6.QtWidgets import QApplication

# Ensure the project root (with the ``src`` package) is on sys.path.
# When pytest is executed from a different working directory, this helps
# Python locate the application modules reliably.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(scope="session")
def qt_app() -> QApplication:
    """Provide a shared QApplication instance for tests.

    Many components (including QSettings) expect a Qt application
    instance to exist. We create one once per test session if it does
    not already exist.
    """

    app = QApplication.instance()
    if app is None:
        # Use a minimal argv list to avoid picking up pytest's arguments.
        app = QApplication(["pytest"])
    return app


@pytest.fixture
def service(qt_app: QApplication):
    """Fixture that provides an AIDescriptionService instance.

    The AI description tests expect a ``service`` fixture that returns
    a fully constructed :class:`AIDescriptionService`. Centralising it
    here keeps the individual test files focused on behaviour rather
    than setup details.
    """

    from src.gui.services.ai_description_service import AIDescriptionService

    return AIDescriptionService()

