from pathlib import Path
import json

from src.core.database.database_manager import DatabaseManager
from src.core.model_tags import TAG_DIRTY
from src.core.model_sidecar_service import (
    generate_sidecar_for_model,
    regenerate_sidecars_for_dirty_models,
)


def test_generate_sidecar_for_model_includes_metadata_and_tags(tmp_path) -> None:
    """Sidecar JSON should mirror DB state including taxonomy and status."""

    db_path = tmp_path / "sidecar.db"
    manager = DatabaseManager(str(db_path))

    models_dir = tmp_path / "Models"
    models_dir.mkdir()
    model_file = models_dir / "model.stl"
    model_file.write_text("dummy", encoding="utf-8")

    model_id = manager.add_model(
        filename="model.stl",
        model_format="stl",
        file_path=str(model_file),
        file_size=model_file.stat().st_size,
        file_hash="abc123",
    )

    manager.add_model_metadata(
        model_id,
        title="Test Model",
        description="Desc",
        keywords="alpha, beta",
        category="Demo",
        source="UnitTest",
        rating=5,
    )

    # Mark dirty so system tags appear alongside user tags
    assert manager.mark_model_dirty(model_id)

    success, sidecar_path = generate_sidecar_for_model(manager, model_id)
    assert success
    assert sidecar_path is not None
    assert sidecar_path.name == "model.stl.info.json"

    data = json.loads(sidecar_path.read_text(encoding="utf-8"))

    assert data["model_id"] == model_id
    assert data["file_path"] == str(model_file)
    assert data["file_hash"] == "abc123"
    assert data["title"] == "Test Model"
    assert data["category"] == "Demo"

    # Keywords must preserve both user and system tags
    keywords = data["keywords"]
    assert set(keywords) >= {"alpha", "beta", TAG_DIRTY}

    taxonomy = data["taxonomy"]
    assert taxonomy["category"] == "Demo"
    assert TAG_DIRTY in taxonomy["system_tags"]
    assert "alpha" in taxonomy["user_tags"]
    assert "beta" in taxonomy["user_tags"]

    status = data["status"]
    assert status["dirty"] is True


def test_regenerate_sidecars_for_dirty_models_clears_dirty_tag(tmp_path) -> None:
    """Batch regeneration should clean TAG_DIRTY only when sidecar write succeeds."""

    db_path = tmp_path / "sidecar_batch.db"
    manager = DatabaseManager(str(db_path))

    # Dirty model with an existing file
    model_dir = tmp_path / "Models"
    model_dir.mkdir()
    dirty_model_file = model_dir / "dirty_model.stl"
    dirty_model_file.write_text("dummy", encoding="utf-8")

    dirty_id = manager.add_model(
        filename="dirty_model.stl",
        model_format="stl",
        file_path=str(dirty_model_file),
        file_size=dirty_model_file.stat().st_size,
        file_hash="hash_dirty",
    )
    manager.add_model_metadata(
        dirty_id,
        title="Dirty Model",
        description="Dirty",
        keywords="alpha",
        category="Demo",
        source="UnitTest",
        rating=4,
    )
    assert manager.mark_model_dirty(dirty_id)

    # Clean model should be ignored by the regeneration pass
    clean_model_file = model_dir / "clean_model.stl"
    clean_model_file.write_text("dummy", encoding="utf-8")

    clean_id = manager.add_model(
        filename="clean_model.stl",
        model_format="stl",
        file_path=str(clean_model_file),
        file_size=clean_model_file.stat().st_size,
        file_hash="hash_clean",
    )
    manager.add_model_metadata(
        clean_id,
        title="Clean Model",
        description="Clean",
        keywords="gamma",
        category="Demo",
        source="UnitTest",
        rating=3,
    )

    result = regenerate_sidecars_for_dirty_models(manager)

    assert result["processed"] == 1
    assert result["updated"] == 1
    assert result["errors"] == 0

    # Dirty tag must be cleared, user tags preserved
    metadata = manager.get_model_metadata(dirty_id)
    keywords = [
        k.strip() for k in (metadata.get("keywords") or "").split(",") if k.strip()
    ]
    assert TAG_DIRTY not in keywords
    assert "alpha" in keywords

    # Sidecar written only for the dirty model
    dirty_sidecar = Path(str(dirty_model_file) + ".info.json")
    clean_sidecar = Path(str(clean_model_file) + ".info.json")
    assert dirty_sidecar.exists()
    assert not clean_sidecar.exists()
