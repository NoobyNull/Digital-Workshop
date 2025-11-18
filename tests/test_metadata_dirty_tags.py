from pathlib import Path

from src.core.database.database_manager import DatabaseManager
from src.core.model_tags import TAG_DIRTY


def test_mark_model_dirty_and_clean_preserves_user_tags(tmp_path) -> None:
    """mark_model_dirty/clean should toggle TAG_DIRTY without clobbering tags."""
    db_path = tmp_path / "dirty_tags.db"
    manager = DatabaseManager(str(db_path))

    # Create a dummy model entry
    model_file = tmp_path / "model.stl"
    model_file.write_text("dummy")

    model_id = manager.add_model(
        filename="model.stl",
        model_format="stl",
        file_path=str(model_file),
        file_size=model_file.stat().st_size,
    )

    # Seed metadata with existing user tags
    manager.add_model_metadata(
        model_id,
        title="Test Model",
        description="Desc",
        keywords="user, tag",
        category="Demo",
        source="Test",
        rating=3,
    )

    # Mark dirty: TAG_DIRTY should be added alongside existing tags
    assert manager.mark_model_dirty(model_id)
    metadata = manager.get_model_metadata(model_id)
    keywords = [k.strip() for k in (metadata.get("keywords") or "").split(",") if k.strip()]
    assert "user" in keywords
    assert "tag" in keywords
    assert TAG_DIRTY in keywords

    # Mark clean: TAG_DIRTY should be removed, other tags preserved
    assert manager.mark_model_clean(model_id)
    metadata = manager.get_model_metadata(model_id)
    keywords = [k.strip() for k in (metadata.get("keywords") or "").split(",") if k.strip()]
    assert "user" in keywords
    assert "tag" in keywords
    assert TAG_DIRTY not in keywords

