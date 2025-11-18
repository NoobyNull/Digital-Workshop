"""Helpers for managing the recent-model MRU list."""

from __future__ import annotations

from typing import Dict, List, Optional

from src.core.database_manager import DatabaseManager, get_database_manager
from src.core.model_tags import TAG_FAVORITE, TAG_RECENT
from src.core.services.library_settings import (
    LibrarySettings,
    RECENT_MAX_ENTRIES_DEFAULT,
)


def _get_manager(db_manager: Optional[DatabaseManager]) -> DatabaseManager:
    return db_manager or get_database_manager()


def get_recent_limit() -> int:
    """Return the configured MRU length."""

    try:
        settings = LibrarySettings()
        return settings.get_recent_max_entries()
    except Exception:
        return RECENT_MAX_ENTRIES_DEFAULT


def set_recent_limit(limit: int) -> None:
    """Persist the MRU length preference and trim existing entries."""

    settings = LibrarySettings()
    settings.set_recent_max_entries(limit)
    enforce_recent_limit(limit)


def record_model_access(
    model_id: int,
    *,
    db_manager: Optional[DatabaseManager] = None,
    mru_limit: Optional[int] = None,
) -> bool:
    """Record a model access, ensuring MRU order and tag sync."""

    manager = _get_manager(db_manager)
    limit = mru_limit if mru_limit is not None else get_recent_limit()

    trimmed_ids = manager.record_recent_model_access(model_id, limit)
    entry = manager.get_recent_model_entry(model_id)
    is_favorite = bool(entry["is_favorite"]) if entry else False

    _sync_recent_tags(manager, model_id, is_recent=True, is_favorite=is_favorite)
    for trimmed_id in trimmed_ids:
        _sync_recent_tags(manager, trimmed_id, is_recent=False, is_favorite=False)

    return True


def set_recent_favorite(
    model_id: int,
    is_favorite: bool,
    *,
    db_manager: Optional[DatabaseManager] = None,
) -> bool:
    """Toggle the favorite flag for a model in the MRU list."""

    manager = _get_manager(db_manager)
    updated = manager.set_recent_model_favorite(model_id, is_favorite)

    if not updated:
        return False

    entry = manager.get_recent_model_entry(model_id)
    is_recent = bool(entry)
    _sync_recent_tags(manager, model_id, is_recent=is_recent, is_favorite=is_favorite)
    return True


def get_recent_models(
    limit: Optional[int] = None,
    *,
    db_manager: Optional[DatabaseManager] = None,
) -> List[Dict[str, object]]:
    """Return recent models for display."""

    manager = _get_manager(db_manager)
    effective_limit = limit if limit is not None else get_recent_limit()
    return manager.get_recent_models(effective_limit)


def enforce_recent_limit(
    limit: Optional[int] = None, *, db_manager: Optional[DatabaseManager] = None
) -> List[int]:
    """Trim the MRU table to the requested limit and clean up tags."""

    manager = _get_manager(db_manager)
    effective_limit = limit if limit is not None else get_recent_limit()
    trimmed = manager.trim_recent_models(effective_limit)

    for model_id in trimmed:
        _sync_recent_tags(manager, model_id, is_recent=False, is_favorite=False)

    return trimmed


def _sync_recent_tags(
    manager: DatabaseManager, model_id: int, *, is_recent: bool, is_favorite: bool
) -> None:
    """Ensure TAG_RECENT and TAG_FAVORITE reflect MRU state."""

    add_tags: List[str] = []
    remove_tags: List[str] = []

    if is_recent:
        add_tags.append(TAG_RECENT)
    else:
        remove_tags.append(TAG_RECENT)

    if is_favorite:
        add_tags.append(TAG_FAVORITE)
    else:
        remove_tags.append(TAG_FAVORITE)

    # Remove duplicates
    add_tags = list(dict.fromkeys(add_tags))
    remove_tags = [tag for tag in remove_tags if tag not in add_tags]

    if add_tags or remove_tags:
        manager.update_model_keywords_tags(model_id, add_tags=add_tags, remove_tags=remove_tags)
