"""
Compatibility wrapper for the file system proxy model.

Re-exports the proxy model from ``src.gui.model_library.file_system_proxy`` to
avoid duplication.
"""

from src.gui.model_library.file_system_proxy import FileSystemProxyModel

__all__ = ["FileSystemProxyModel"]
