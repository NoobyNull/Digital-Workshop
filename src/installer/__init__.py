"""
Digital Workshop Modular Installer Package

This package provides the core installer functionality for Digital Workshop,
supporting multiple installation modes:
- Full Install: Fresh installation with all modules
- Patching: Update existing installation
- Reinstall: Fresh app installation with data preservation
- Clean Install: Complete removal and fresh start (DESTRUCTIVE)

Each module is compiled separately and can be updated independently.
"""

from .installer import Installer

__version__ = "1.0.0"
__all__ = ["Installer"]
