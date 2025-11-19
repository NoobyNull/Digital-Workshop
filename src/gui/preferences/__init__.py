"""Preferences dialog and tab modules."""

from src.gui.preferences.preferences_dialog import PreferencesDialog
from src.gui.preferences.tabs import (
    AdvancedTab,
    AITab,
    GeneralTab,
    ThemingTab,
    ThumbnailSettingsTab,
    ViewerSettingsTab,
    InvoicePreferencesTab,
)

__all__ = [
    'PreferencesDialog',
    'GeneralTab',
    'ThemingTab',
    'ViewerSettingsTab',
    'ThumbnailSettingsTab',
    'AdvancedTab',
    'AITab',
    'InvoicePreferencesTab',
]
