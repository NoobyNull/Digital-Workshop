"""
Installation modes for Digital Workshop

Provides different installation strategies:
- Full Install: Fresh installation with all modules
- Patching: Update existing installation
- Reinstall: Fresh app installation with data preservation
- Clean Install: Complete removal and fresh start (DESTRUCTIVE)
"""

from .full_install import FullInstallMode
from .patch_mode import PatchMode
from .reinstall_mode import ReinstallMode
from .clean_install import CleanInstallMode

__all__ = [
    "FullInstallMode",
    "PatchMode",
    "ReinstallMode",
    "CleanInstallMode",
]

