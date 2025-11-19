"""Utility helpers for loading Qt Designer UI files at runtime."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Union

from PySide6.QtCore import QFile, QIODevice
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QWidget


class UILoader:
    """Small wrapper around :class:`QUiLoader` with path handling helpers."""

    def __init__(self, base_path: Optional[Union[str, Path]] = None) -> None:
        self.base_path = Path(base_path).resolve() if base_path else None
        self._loader = QUiLoader()

    def load(self, ui_file: Union[str, Path]) -> QWidget:
        """
        Load a .ui file and return the root widget.

        Args:
            ui_file: Path to the Qt Designer file.

        Returns:
            QWidget that was declared in the .ui file.
        """
        path = self._resolve(ui_file)
        qfile = QFile(str(path))
        if not qfile.open(QIODevice.ReadOnly):
            raise OSError(f"Unable to open UI file: {path}")

        try:
            widget = self._loader.load(qfile)
        finally:
            qfile.close()

        if widget is None:
            raise ValueError(f"Failed to load UI definition from {path}")

        if not widget.objectName():
            widget.setObjectName(path.stem)
        return widget

    def _resolve(self, ui_file: Union[str, Path]) -> Path:
        path = Path(ui_file)
        if not path.is_absolute() and self.base_path:
            path = self.base_path / path
        path = path.resolve()
        if not path.exists():
            raise FileNotFoundError(path)
        return path

