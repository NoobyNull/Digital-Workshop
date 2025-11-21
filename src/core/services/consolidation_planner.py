"""Consolidation planner for moving/copying a library into a managed root.

This module does not perform any UI. It builds a plan of operations that
callers can execute and resume, and it integrates with security filtering,
file type registry, and extra-files policy.
"""

from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

from src.core.cancellation_token import CancellationToken
from src.core.logging_config import get_logger
from src.core.security import PathValidator
from src.core.services.extra_files_policy import ExtraFileDecision, ExtraFilesPolicy
from src.core.services.file_type_filter import FileTypeFilter
from src.core.services.file_type_registry import get_consolidation_folder_for_path
from src.core.import_thumbnail_service import ImportThumbnailService


logger = get_logger(__name__)


class ConsolidationOperation(str, Enum):
    """Supported consolidation operations."""

    MOVE = "move"
    COPY = "copy"
    SKIP = "skip"


@dataclass
class ConsolidationItem:
    """Single file operation in a consolidation plan."""

    source_path: str
    dest_path: str
    operation: ConsolidationOperation
    category: str
    is_extra: bool = False
    is_thumbnail: bool = False
    primary_model_source: Optional[str] = None
    completed: bool = False
    error: Optional[str] = None


@dataclass
class ConsolidationPlan:
    """Full consolidation plan from a source root to a destination root."""

    source_root: str
    dest_root: str
    items: List[ConsolidationItem] = field(default_factory=list)

    def pending_items(self) -> Iterable[ConsolidationItem]:
        """Iterate over items that still need work."""

        return (
            item
            for item in self.items
            if not item.completed and item.operation != ConsolidationOperation.SKIP
        )

    def to_json(self) -> str:
        """Serialize plan to JSON for debugging or persistence."""

        return json.dumps(
            {
                "source_root": self.source_root,
                "dest_root": self.dest_root,
                "items": [item.__dict__ for item in self.items],
            }
        )


class ConsolidationPlanner:
    """Builds and executes consolidation plans.

    This class is intentionally UI-free. Callers are responsible for any
    user prompts (for example extra-files confirmation dialogs).
    """

    def __init__(self, policy: Optional[ExtraFilesPolicy] = None) -> None:
        self._filter = FileTypeFilter()
        self._policy = policy or ExtraFilesPolicy()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def build_plan(self, source_root: str, dest_root: str) -> ConsolidationPlan:
        """Scan source_root and build a consolidation plan into dest_root.

        Security filtering is always applied. Extra files are consulted
        against ExtraFilesPolicy; if there is no stored decision yet, the
        corresponding items are created with operation=SKIP so that callers
        can later update them after obtaining user decisions.
        """

        src = Path(source_root).resolve()
        dst = Path(dest_root).resolve()
        plan = ConsolidationPlan(source_root=str(src), dest_root=str(dst))

        folder_models: Dict[Path, List[Path]] = {}
        folder_images: Dict[Path, List[Path]] = {}
        extra_candidates: Dict[str, List[Path]] = {}

        for path in src.rglob("*"):
            if not path.is_file():
                continue

            if PathValidator.is_system_file(str(path)):
                logger.info("Skipping system file during consolidation: %s", path)
                continue

            filter_result = self._filter.filter_file(str(path))
            if not filter_result.is_allowed:
                logger.info(
                    "Skipping blocked file during consolidation (%s): %s",
                    filter_result.reason,
                    path,
                )
                continue

            category = (filter_result.category or "").strip()
            parent = path.parent
            suffix = path.suffix.lower() or "<noext>"

            if category in {"3D Models", "G-code"}:
                folder_models.setdefault(parent, []).append(path)
            elif category == "Images":
                folder_images.setdefault(parent, []).append(path)
            else:
                # Treat anything else as an extra candidate
                extra_candidates.setdefault(suffix, []).append(path)

        # Match thumbnails: images whose stem matches model stem or obvious variants
        thumbnail_paths = set()
        model_to_thumbs: Dict[Path, List[Path]] = {}
        for folder, models in folder_models.items():
            images = folder_images.get(folder, [])
            for model_path in models:
                stem = model_path.stem.lower()
                for img in images:
                    img_stem = img.stem.lower()
                    if img_stem in {
                        stem,
                        f"{stem}_thumb",
                        f"{stem}-thumb",
                        f"thumb_{stem}",
                    }:
                        thumbnail_paths.add(img)
                        model_to_thumbs.setdefault(model_path, []).append(img)

        # Build plan for models and their thumbnails
        for folder, models in folder_models.items():
            for model_path in models:
                category_folder = (
                    get_consolidation_folder_for_path(str(model_path)) or "Misc"
                )
                op = self._decide_operation(model_path, dst)
                dest = self._build_dest_path(src, dst, model_path, category_folder)
                plan.items.append(
                    ConsolidationItem(
                        source_path=str(model_path),
                        dest_path=str(dest),
                        operation=op,
                        category=category_folder,
                        is_extra=False,
                    )
                )

                for thumb in model_to_thumbs.get(model_path, []):
                    thumb_dest = self._build_dest_path(src, dst, thumb, category_folder)
                    plan.items.append(
                        ConsolidationItem(
                            source_path=str(thumb),
                            dest_path=str(thumb_dest),
                            operation=op,
                            category=category_folder,
                            is_extra=False,
                            is_thumbnail=True,
                            primary_model_source=str(dest),
                        )
                    )

        # Build items for extra files (non-thumbnail images and others)
        for suffix, paths in extra_candidates.items():
            decision_entry = self._policy.get_policy(suffix)
            decision = decision_entry.decision if decision_entry else None

            for p in paths:
                if p in thumbnail_paths:
                    # Already handled above
                    continue

                category_folder = get_consolidation_folder_for_path(str(p)) or "Misc"
                if decision is None:
                    op = ConsolidationOperation.SKIP
                elif decision == ExtraFileDecision.MOVE_TO_MISC:
                    op = self._decide_operation(p, dst)
                else:  # LEAVE_IN_PLACE
                    op = ConsolidationOperation.SKIP

                dest = self._build_dest_path(src, dst, p, category_folder)
                plan.items.append(
                    ConsolidationItem(
                        source_path=str(p),
                        dest_path=str(dest),
                        operation=op,
                        category=category_folder,
                        is_extra=True,
                    )
                )

        logger.info(
            "Consolidation plan built: %s items (source=%s, dest=%s)",
            len(plan.items),
            plan.source_root,
            plan.dest_root,
        )
        return plan

    def execute_plan(
        self,
        plan: ConsolidationPlan,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        cancellation_token: Optional[CancellationToken] = None,
        thumbnail_callback: Optional[Callable[[ConsolidationItem], None]] = None,
    ) -> None:
        """Execute a consolidation plan with basic resume support.

        If the destination file already exists, the item is marked completed and
        skipped. This means re-running execute_plan after an interruption will
        naturally resume where it left off.

        If *thumbnail_callback* is provided, it is called for each thumbnail
        item (``item.is_thumbnail is True``) after the corresponding file is
        confirmed to exist at the destination path.
        """

        actionable = [
            i for i in plan.items if i.operation != ConsolidationOperation.SKIP
        ]
        total = len(actionable)
        completed = 0

        for item in actionable:
            if item.completed:
                completed += 1
                if item.is_thumbnail and thumbnail_callback is not None:
                    thumbnail_callback(item)
                continue

            if cancellation_token is not None and cancellation_token.is_cancelled():
                logger.info(
                    "Consolidation cancelled after %s/%s items", completed, total
                )
                break

            dest_path = Path(item.dest_path)
            if dest_path.exists():
                item.completed = True
                completed += 1
                if item.is_thumbnail and thumbnail_callback is not None:
                    thumbnail_callback(item)
                if progress_callback:
                    progress_callback(completed, total)
                continue

            dest_path.parent.mkdir(parents=True, exist_ok=True)

            try:
                if item.operation == ConsolidationOperation.MOVE:
                    shutil.move(item.source_path, item.dest_path)
                elif item.operation == ConsolidationOperation.COPY:
                    shutil.copy2(item.source_path, item.dest_path)
                item.completed = True
                completed += 1
            except OSError as exc:  # pragma: no cover - depends on filesystem
                item.error = str(exc)
                logger.error(
                    "Failed to %s %s -> %s: %s",
                    item.operation.value,
                    item.source_path,
                    item.dest_path,
                    exc,
                )
            else:
                if item.is_thumbnail and thumbnail_callback is not None:
                    thumbnail_callback(item)

            if progress_callback:
                progress_callback(completed, total)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _decide_operation(
        self, src_path: Path, dest_root: Path
    ) -> ConsolidationOperation:
        """Decide MOVE vs COPY based on drive/anchor (Windows-like semantics)."""

        try:
            src_drive, _ = os.path.splitdrive(str(src_path))
            dst_drive, _ = os.path.splitdrive(str(dest_root))
            if src_drive and dst_drive and src_drive.lower() == dst_drive.lower():
                return ConsolidationOperation.MOVE
            return ConsolidationOperation.COPY
        except OSError:
            return ConsolidationOperation.COPY

    def _build_dest_path(
        self, source_root: Path, dest_root: Path, file_path: Path, category_folder: str
    ) -> Path:
        """Build destination path preserving relative structure under a category."""

        try:
            rel = file_path.relative_to(source_root)
        except ValueError:
            rel = file_path.name
        return dest_root / category_folder / rel


def create_thumbnail_registration_callback(
    thumbnail_service: Optional[ImportThumbnailService] = None,
) -> Callable[[ConsolidationItem], None]:
    """Create a thumbnail_callback for ConsolidationPlanner.execute_plan.

    The returned callable will register each thumbnail item with the
    ImportThumbnailService so that thumbnails discovered during
    consolidation are treated as if the import pipeline had generated
    them.
    """

    service = thumbnail_service or ImportThumbnailService()

    def _callback(item: ConsolidationItem) -> None:
        if not item.is_thumbnail or not item.primary_model_source:
            return

        try:
            service.register_existing_thumbnail(
                model_path=item.primary_model_source,
                thumbnail_path=item.dest_path,
            )
        except (
            OSError,
            IOError,
            ValueError,
            TypeError,
            KeyError,
            AttributeError,
        ) as exc:
            logger.error(
                "Failed to register thumbnail for %s from %s: %s",
                item.primary_model_source,
                item.dest_path,
                exc,
            )

    return _callback
