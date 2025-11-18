from pathlib import Path

from src.core.database.database_manager import DatabaseManager
from src.core.model_recent_service import (
    get_recent_models,
    record_model_access,
    set_recent_favorite,
    enforce_recent_limit,
)
from src.core.model_tags import TAG_FAVORITE, TAG_RECENT


def _create_model(db: DatabaseManager, tmp_path: Path, name: str) -> int:
    file_path = tmp_path / f"{name}.stl"
    file_path.write_text("dummy", encoding="utf-8")
    model_id = db.add_model(
        filename=file_path.name,
        model_format="stl",
        file_path=str(file_path),
        file_size=file_path.stat().st_size,
    )
    db.add_model_metadata(
        model_id,
        title=name,
        description="sample",
        keywords="user_tag",
        category="Demo",
        source="Test",
        rating=3,
    )
    return model_id


def _get_keywords(db: DatabaseManager, model_id: int) -> str:
    metadata = db.get_model_metadata(model_id)
    return metadata.get("keywords") or ""


def test_record_model_access_orders_and_trims_and_tags(tmp_path) -> None:
    db = DatabaseManager(str(tmp_path / "mru.db"))

    ids = [_create_model(db, tmp_path, f"model_{idx}") for idx in range(4)]

    record_model_access(ids[0], db_manager=db, mru_limit=3)
    record_model_access(ids[1], db_manager=db, mru_limit=3)
    record_model_access(ids[2], db_manager=db, mru_limit=3)

    recent = get_recent_models(db_manager=db, limit=3)
    assert [entry["model_id"] for entry in recent] == [ids[2], ids[1], ids[0]]
    assert TAG_RECENT in _get_keywords(db, ids[0])

    # Access model_1 again to move it to the top
    record_model_access(ids[1], db_manager=db, mru_limit=3)
    recent = get_recent_models(db_manager=db, limit=3)
    assert [entry["model_id"] for entry in recent] == [ids[1], ids[2], ids[0]]

    # Access a new model which should trim the oldest entry (ids[0])
    record_model_access(ids[3], db_manager=db, mru_limit=3)
    recent = get_recent_models(db_manager=db, limit=3)
    assert [entry["model_id"] for entry in recent] == [ids[3], ids[1], ids[2]]

    # Trimmed entry should lose the recent tag
    assert TAG_RECENT not in _get_keywords(db, ids[0])


def test_set_recent_favorite_toggles_tag(tmp_path) -> None:
    db = DatabaseManager(str(tmp_path / "favorite.db"))
    model_id = _create_model(db, tmp_path, "fav")

    record_model_access(model_id, db_manager=db, mru_limit=5)
    assert TAG_RECENT in _get_keywords(db, model_id)
    assert TAG_FAVORITE not in _get_keywords(db, model_id)

    assert set_recent_favorite(model_id, True, db_manager=db)
    assert TAG_FAVORITE in _get_keywords(db, model_id)

    assert set_recent_favorite(model_id, False, db_manager=db)
    keywords = _get_keywords(db, model_id)
    assert TAG_FAVORITE not in keywords
    assert TAG_RECENT in keywords  # recent tag remains while entry is tracked


def test_recent_tags_preserve_user_keywords(tmp_path) -> None:
    db = DatabaseManager(str(tmp_path / "preserve.db"))
    model_id = _create_model(db, tmp_path, "preserve")

    record_model_access(model_id, db_manager=db, mru_limit=1)
    keywords = _get_keywords(db, model_id)
    assert "user_tag" in keywords
    assert TAG_RECENT in keywords

    # Lower the limit to zero (treated as 1) and force a trim to clear entries.
    enforce_recent_limit(0, db_manager=db)
    keywords_after = _get_keywords(db, model_id)
    assert "user_tag" in keywords_after
    assert TAG_RECENT not in keywords_after
