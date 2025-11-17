"""
File system proxy model for filtering hidden files and network paths.

Provides filtering for file system models to hide hidden files,
network paths, and other unwanted entries.
"""

from pathlib import Path

from PySide6.QtCore import QSortFilterProxyModel


class FileSystemProxyModel(QSortFilterProxyModel):
    """
    Proxy model that filters out hidden folders and handles network paths.

    Filters:
    - Hidden files and folders
    - Files/folders starting with '.'
    - Network paths (UNC paths starting with \\)
    - R drives outside home directory
    """

    def __init__(self, parent=None) -> None:
        """
        Initialize the proxy model.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self.home_drive = str(Path.home().drive) if hasattr(Path.home(), "drive") else ""

    def filterAcceptsRow(self, source_row, source_parent) -> None:
        """
        Override to filter out hidden folders and network paths.

        Args:
            source_row: Row index in source model
            source_parent: Parent index in source model

        Returns:
            bool: True if row should be shown, False otherwise
        """
        # Get the source model index
        source_model = self.sourceModel()
        if not source_model:
            return True

        index = source_model.index(source_row, 0, source_parent)
        if not index.isValid():
            return True

        # Get file info
        file_info = source_model.fileInfo(index)

        # Skip hidden files and folders
        if file_info.isHidden():
            return False

        # Skip files/folders starting with '.'
        file_name = file_info.fileName()
        if file_name.startswith("."):
            return False

        # Skip network paths (UNC paths starting with \\)
        file_path = file_info.absoluteFilePath()
        if file_path.startswith("\\\\"):
            return False

        # Skip R drives that are not in home directory
        if (
            self.home_drive
            and file_path.startswith("R:")
            and not file_path.startswith(self.home_drive + "\\")
        ):
            return False

        return True
