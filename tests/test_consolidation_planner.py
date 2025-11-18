"""End-to-end style tests for the consolidation planner.

These tests focus on security filtering, extra-files policy defaults,
MOVE vs COPY semantics, and thumbnail registration.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import sys
from types import ModuleType

# Provide a lightweight stub for the VTK-based thumbnail generator during tests.
if "src.core.thumbnail_components.thumbnail_generator_main" not in sys.modules:
    stub_module = ModuleType("src.core.thumbnail_components.thumbnail_generator_main")

    class ThumbnailGenerator:  # pragma: no cover - VTK is tested elsewhere
        def __init__(self, settings_manager=None) -> None:
            self.settings_manager = settings_manager

        def generate_thumbnail(self, *args, **kwargs):
            return None, None

    stub_module.ThumbnailGenerator = ThumbnailGenerator
    sys.modules["src.core.thumbnail_components.thumbnail_generator_main"] = stub_module


import pytest

from src.core.services.consolidation_planner import (
    ConsolidationPlanner,
    ConsolidationOperation,
    create_thumbnail_registration_callback,
)
from src.core.import_thumbnail_service import ImportThumbnailService, StorageLocation


def _create_file(path: Path, content: bytes = b"data") -> None:
    """Create a small file, ensuring parent directories exist."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def test_build_plan_applies_security_and_extra_policy(tmp_path: Path) -> None:
    """Consolidation plan should respect security and extra-file defaults."""

    src_root = tmp_path / "source"
    dst_root = tmp_path / "dest"
    src_root.mkdir()
    dst_root.mkdir()

    _create_file(src_root / "model.stl", b"model")
    _create_file(src_root / "doc.pdf", b"doc")
    _create_file(src_root / "model.png", b"thumb")
    _create_file(src_root / "movie.mp4", b"video")
    _create_file(src_root / "malware.exe", b"exe")

    planner = ConsolidationPlanner()
    plan = planner.build_plan(str(src_root), str(dst_root))

    by_name = {Path(item.source_path).name: item for item in plan.items}

    # Blocked files should never appear in the plan.
    assert "malware.exe" not in by_name

    model_item = by_name["model.stl"]
    thumb_item = by_name["model.png"]
    extra_item = by_name["movie.mp4"]

    # MOVE vs COPY depends on drive; mirror the planner's semantics here.
    src_drive, _ = os.path.splitdrive(model_item.source_path)
    dst_drive, _ = os.path.splitdrive(plan.dest_root)
    if src_drive and dst_drive and src_drive.lower() == dst_drive.lower():
        expected_op = ConsolidationOperation.MOVE
    else:
        expected_op = ConsolidationOperation.COPY

    assert model_item.operation == expected_op
    assert thumb_item.operation == expected_op
    assert thumb_item.is_thumbnail
    assert thumb_item.primary_model_source == model_item.dest_path

    # Extra file types should default to SKIP until a policy is stored.
    assert extra_item.is_extra
    assert extra_item.operation == ConsolidationOperation.SKIP


def test_execute_plan_moves_files_and_registers_thumbnails(tmp_path: Path) -> None:
    """Executing the plan should move files and register thumbnails."""

    src_root = tmp_path / "source2"
    dst_root = tmp_path / "dest2"
    thumbs_root = tmp_path / "thumbs"
    src_root.mkdir()
    dst_root.mkdir()

    _create_file(src_root / "model.stl", b"model")
    _create_file(src_root / "model.png", b"thumb")
    _create_file(src_root / "movie.mp4", b"video")

    planner = ConsolidationPlanner()
    plan = planner.build_plan(str(src_root), str(dst_root))

    service = ImportThumbnailService(
        storage_location=StorageLocation.CUSTOM,
        custom_storage_path=str(thumbs_root),
    )
    # Avoid exercising the real image pipeline here.
    service.thumbnail_resizer = MagicMock()

    callback = create_thumbnail_registration_callback(thumbnail_service=service)

    planner.execute_plan(plan, thumbnail_callback=callback)

    # Model and thumbnail should have been moved; extra video left in place.
    assert not (src_root / "model.stl").exists()
    assert not (src_root / "model.png").exists()
    assert (src_root / "movie.mp4").exists()

    model_item = next(
        item for item in plan.items if item.source_path.endswith("model.stl")
    )
    dest_model = Path(model_item.dest_path)
    assert dest_model.exists()

    hash_result = service.hasher.hash_file(str(dest_model))
    assert hash_result.success
    file_hash = hash_result.hash_value
    registered_thumb = service.get_thumbnail_path(file_hash)
    assert registered_thumb.exists()

