"""Utilities for per-model sidecar generation.

Sidecars are small JSON files written next to each model file that capture
canonical database metadata (title, description, category, keywords/tags,
status flags, etc.). They are treated as a cache that can always be
regenerated from the database.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.core.logging_config import get_logger
from src.core.model_tags import TAG_DIRTY, TAG_RECENT, TAG_FAVORITE
from src.core.database.database_manager import DatabaseManager

logger = get_logger(__name__)

SYSTEM_TAGS = {TAG_DIRTY, TAG_RECENT, TAG_FAVORITE}


def _parse_keywords(value: Any) -> List[str]:
    """Parse the keywords field into a normalized list of tags."""

    if value is None:
        return []
    if not isinstance(value, str):
        value = str(value)
    return [k.strip() for k in value.split(",") if k.strip()]


def _split_user_and_system_tags(tags: List[str]) -> Tuple[List[str], List[str]]:
    """Split tags into user-defined tags and reserved/system tags."""

    system = [t for t in tags if t in SYSTEM_TAGS]
    user = [t for t in tags if t not in SYSTEM_TAGS]
    return user, system


def _compute_sidecar_path(file_path: str) -> Optional[Path]:
    """Return the sidecar path for a model file, or None if invalid."""

    if not file_path:
        return None
    model_path = Path(file_path)
    if not model_path.name:
        return None
    return model_path.with_name(model_path.name + ".info.json")


def _build_sidecar_payload(model: Dict[str, Any]) -> Dict[str, Any]:
    """Build the JSON-serializable payload for a model sidecar."""

    keywords = _parse_keywords(model.get("keywords"))
    user_tags, system_tags = _split_user_and_system_tags(keywords)

    status = {"dirty": TAG_DIRTY in system_tags}
    taxonomy = {
        "category": model.get("category"),
        "user_tags": user_tags,
        "system_tags": system_tags,
    }

    return {
        "model_id": model.get("id"),
        "filename": model.get("filename"),
        "file_path": model.get("file_path"),
        "file_hash": model.get("file_hash"),
        "file_size": model.get("file_size"),
        "format": model.get("format"),
        "title": model.get("title"),
        "description": model.get("description"),
        "category": model.get("category"),
        "source": model.get("source"),
        "rating": model.get("rating"),
        "keywords": keywords,
        "taxonomy": taxonomy,
        "status": status,
        "view_count": model.get("view_count"),
        "last_viewed": model.get("last_viewed"),
        "triangle_count": model.get("triangle_count"),
        "vertex_count": model.get("vertex_count"),
    }


def generate_sidecar_for_model(
    db_manager: DatabaseManager, model_id: int
) -> Tuple[bool, Optional[Path]]:
    """Generate or update the sidecar file for a single model.

    Returns (success, sidecar_path). On failure, sidecar_path will be None.
    """

    try:
        model = db_manager.get_model(model_id)
        if not model:
            logger.warning("Model %s not found for sidecar generation", model_id)
            return False, None

        file_path = model.get("file_path")
        sidecar_path = _compute_sidecar_path(file_path)
        if sidecar_path is None:
            logger.warning(
                "Model %s has invalid file_path for sidecar generation: %r",
                model_id,
                file_path,
            )
            return False, None

        model_path = Path(file_path)
        if not model_path.exists():
            logger.warning("Model file not found for sidecar: %s", file_path)
            return False, None

        payload = _build_sidecar_payload(model)
        sidecar_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info("Wrote sidecar for model %s to %s", model_id, sidecar_path)
        return True, sidecar_path

    except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
        logger.error(
            "Failed to generate sidecar for model %s: %s", model_id, exc, exc_info=True
        )
        return False, None


def regenerate_sidecars_for_dirty_models(
    db_manager: DatabaseManager,
    progress_callback: Optional[Callable[[int, int, str], None]] = None,
    stop_flag_getter: Optional[Callable[[], bool]] = None,
) -> Dict[str, int]:
    """Regenerate sidecars for all models marked with the dirty tag.

    Returns a result dict with keys: processed, updated, errors.
    """

    models = db_manager.get_all_models()
    dirty_models = []
    for model in models:
        tags = _parse_keywords(model.get("keywords"))
        if TAG_DIRTY in tags:
            dirty_models.append(model)

    total = len(dirty_models)
    result = {"processed": 0, "updated": 0, "errors": 0}

    for index, model in enumerate(dirty_models):
        if stop_flag_getter and stop_flag_getter():
            break

        model_id = model.get("id")
        if progress_callback:
            progress_callback(
                index + 1,
                total,
                f"Regenerating sidecar for model {model_id}",
            )

        success, _ = generate_sidecar_for_model(db_manager, model_id)
        result["processed"] += 1

        if success:
            try:
                db_manager.mark_model_clean(model_id)
                result["updated"] += 1
            except (
                OSError,
                IOError,
                ValueError,
                TypeError,
                KeyError,
                AttributeError,
            ) as exc:
                logger.error(
                    "Failed to clear dirty tag for model %s: %s",
                    model_id,
                    exc,
                    exc_info=True,
                )
                result["errors"] += 1
        else:
            result["errors"] += 1

    return result
