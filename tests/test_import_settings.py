"""Tests for import concurrency settings service."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from src.core.services.import_settings import ImportSettings


@pytest.fixture
def isolated_settings(tmp_path) -> ImportSettings:
    config_file = tmp_path / "import_settings.ini"
    qsettings = QSettings(str(config_file), QSettings.IniFormat)
    return ImportSettings(qsettings)


def test_import_settings_roundtrip(isolated_settings: ImportSettings) -> None:
    isolated_settings.set_concurrency(prep_workers=3, thumbnail_workers=2, queue_limit=10)
    updated = isolated_settings.get_concurrency()
    assert updated.prep_workers == 3
    assert updated.thumbnail_workers == 2
    assert updated.queue_limit == 10


def test_import_settings_reset_defaults(isolated_settings: ImportSettings) -> None:
    isolated_settings.set_concurrency(7, 5, 12)
    isolated_settings.reset_defaults()
    current = isolated_settings.get_concurrency()

    assert current.prep_workers >= 1
    assert current.thumbnail_workers >= 1
    assert current.queue_limit >= 2
