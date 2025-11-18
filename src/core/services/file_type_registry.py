"""Central file type registry for UI behavior and consolidation.

This module provides a single source of truth for how file extensions are
handled across the application:

* Which tab should open on double-click.
* Which category name to use in tree widgets.
* Which logical folder name to use during consolidation.

It also integrates with :class:`FileTypeFilter` to respect security rules
and high-level categories while still allowing UI-specific labels.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from src.core.services.file_type_filter import FileTypeFilter


@dataclass(frozen=True)
class FileTypeInfo:
    """Describes behavior for a single file extension.

    Attributes:
        tab_name: Name of the UI tab to open on double-click, if any.
        tree_category: Category label for tree widgets (e.g. "Models").
        consolidation_folder: Target logical folder for consolidation
            (e.g. "Models", "Gcode", "Cut Lists", "Misc").
    """

    tab_name: Optional[str] = None
    tree_category: Optional[str] = None
    consolidation_folder: Optional[str] = None


class FileTypeRegistry:
    """Central registry for file type behavior.

    Resolution follows a "telephone hunt group" strategy:

    1. Look for an explicit registry entry for the extension.
    2. Fall back to :class:`FileTypeFilter` categorization.
    3. Fall back to generic categories like "Misc".

    Security-sensitive decisions (what may be moved) are delegated to
    :class:`FileTypeFilter` and callers. If a file is blocked by
    :class:`FileTypeFilter`, consolidation helpers in this module will
    return ``None`` so callers can skip those files entirely.
    """

    def __init__(self) -> None:
        self._filter = FileTypeFilter()
        # Registry keys must be lowercase extensions including the leading dot.
        self._registry: Dict[str, FileTypeInfo] = {
            # 3D models
            ".stl": FileTypeInfo(
                tab_name="Model Previewer",
                tree_category="Models",
                consolidation_folder="Models",
            ),
            ".obj": FileTypeInfo(
                tab_name="Model Previewer",
                tree_category="Models",
                consolidation_folder="Models",
            ),
            ".step": FileTypeInfo(
                tab_name="Model Previewer",
                tree_category="Models",
                consolidation_folder="Models",
            ),
            ".stp": FileTypeInfo(
                tab_name="Model Previewer",
                tree_category="Models",
                consolidation_folder="Models",
            ),
            ".3mf": FileTypeInfo(
                tab_name="Model Previewer",
                tree_category="Models",
                consolidation_folder="Models",
            ),
            ".ply": FileTypeInfo(
                tab_name="Model Previewer",
                tree_category="Models",
                consolidation_folder="Models",
            ),
            # G-code
            ".nc": FileTypeInfo(
                tab_name="G Code Previewer",
                tree_category="Gcode",
                consolidation_folder="Gcode",
            ),
            ".gcode": FileTypeInfo(
                tab_name="G Code Previewer",
                tree_category="Gcode",
                consolidation_folder="Gcode",
            ),
            # Cut lists
            ".csv": FileTypeInfo(
                tree_category="Cut Lists",
                consolidation_folder="Cut Lists",
            ),
            ".xlsx": FileTypeInfo(
                tree_category="Cut Lists",
                consolidation_folder="Cut Lists",
            ),
            ".xls": FileTypeInfo(
                tree_category="Cut Lists",
                consolidation_folder="Cut Lists",
            ),
            # Cost sheets
            ".pdf": FileTypeInfo(
                tree_category="Cost Sheets",
                consolidation_folder="Cost Sheets",
            ),
            ".docx": FileTypeInfo(
                tree_category="Cost Sheets",
                consolidation_folder="Cost Sheets",
            ),
            ".doc": FileTypeInfo(
                tree_category="Cost Sheets",
                consolidation_folder="Cost Sheets",
            ),
            # Other documents
            ".txt": FileTypeInfo(
                tree_category="Documents",
                consolidation_folder="Documents",
            ),
            ".md": FileTypeInfo(
                tree_category="Documents",
                consolidation_folder="Documents",
            ),
        }

    @staticmethod
    def _normalize_extension(extension: str) -> str:
        ext = extension.lower()
        if not ext.startswith("."):
            ext = f".{ext}"
        return ext

    def get_info_for_extension(self, extension: str) -> Optional[FileTypeInfo]:
        """Get registry info for an extension, if present."""

        ext = self._normalize_extension(extension)
        return self._registry.get(ext)

    def get_tab_for_extension(self, extension: str) -> Optional[str]:
        """Return the tab name for a file extension, if any.

        Args:
            extension: File extension with or without leading dot.
        """

        info = self.get_info_for_extension(extension)
        return info.tab_name if info else None

    def get_tree_category_for_extension(self, extension: str) -> str:
        """Return the tree category label for a file extension.

        Uses explicit registry values first, then falls back to
        :class:`FileTypeFilter` categories, then to "Misc".
        """

        ext = self._normalize_extension(extension)
        info = self._registry.get(ext)
        if info and info.tree_category:
            return info.tree_category

        category = self._filter._categorize_file(ext)  # type: ignore[attr-defined]
        # Map filter categories to tree categories used by the UI.
        mapping = {
            "3D Models": "Models",
            "Documents": "Documents",
            "Images": "Images",
            "Metadata": "Documents",
            "Archives": "Misc",
            "Video": "Misc",
            "Audio": "Misc",
            "Other": "Misc",
        }
        return mapping.get(category, "Misc")

    def get_consolidation_folder_for_path(self, file_path: str) -> Optional[str]:
        """Return the logical consolidation folder for a file path.

        Security is respected: if :class:`FileTypeFilter` marks the file as
        blocked, this method returns ``None`` so callers can skip it.
        """

        result = self._filter.filter_file(file_path)
        if not result.is_allowed:
            # Caller must not move this file.
            return None

        ext = Path(file_path).suffix.lower()
        info = self._registry.get(ext)
        if info and info.consolidation_folder:
            return info.consolidation_folder

        # Fall back to category-based mapping.
        mapping = {
            "3D Models": "Models",
            "Documents": "Documents",
            "Images": "Images",
            "Metadata": "Documents",
            "Archives": "Misc",
            "Video": "Misc",
            "Audio": "Misc",
            "Other": "Misc",
        }
        return mapping.get(result.category, "Misc")


# Module-level singleton and convenience functions for easy import.
_REGISTRY = FileTypeRegistry()


def get_tab_for_extension(extension: str) -> Optional[str]:
    """Convenience wrapper for :meth:`FileTypeRegistry.get_tab_for_extension`."""

    return _REGISTRY.get_tab_for_extension(extension)


def get_tree_category_for_extension(extension: str) -> str:
    """Convenience wrapper for tree category lookup."""

    return _REGISTRY.get_tree_category_for_extension(extension)


def get_consolidation_folder_for_path(file_path: str) -> Optional[str]:
    """Convenience wrapper for consolidation folder lookup."""

    return _REGISTRY.get_consolidation_folder_for_path(file_path)

