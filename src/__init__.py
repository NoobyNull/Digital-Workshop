"""
Digital Workshop (3D Model Manager) - A Windows desktop application for organizing and viewing 3D model collections.

This package contains the main source code for the Digital Workshop application.
"""

from .core.version_manager import get_display_version, get_organization_name

__version__ = get_display_version()
__author__ = "Digital Workshop Development Team"


def get_version():
    """Get the current version string."""
    return __version__


def get_author():
    """Get the author information."""
    return __author__


def get_organization():
    """Get the organization name."""
    return get_organization_name()
