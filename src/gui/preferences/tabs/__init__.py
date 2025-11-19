"""Preferences tab modules."""

from src.gui.preferences.tabs.advanced_tab import AdvancedTab
from src.gui.preferences.tabs.ai_tab import AITab
from src.gui.preferences.tabs.general_tab import GeneralTab
from src.gui.preferences.tabs.theming_tab import ThemingTab
from src.gui.preferences.tabs.thumbnail_settings_tab import ThumbnailSettingsTab
from src.gui.preferences.tabs.viewer_settings_tab import ViewerSettingsTab
from src.gui.preferences.tabs.invoice_tab import InvoicePreferencesTab

__all__ = [
    'GeneralTab',
    'ThemingTab',
    'ViewerSettingsTab',
    'ThumbnailSettingsTab',
    'AdvancedTab',
    'AITab',
    'InvoicePreferencesTab',
]
