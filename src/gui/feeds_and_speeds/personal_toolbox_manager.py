"""Personal toolbox management using QSettings."""

import json
from typing import List, Dict, Any
from PySide6.QtCore import QSettings

from src.core.logging_config import get_logger
from .tool_library_manager import Tool

logger = get_logger(__name__)


class PersonalToolboxManager:
    """Manages user's personal tool library using QSettings."""

    SETTINGS_KEY = "feeds_and_speeds/personal_toolbox"
    UNIT_CONVERSION_KEY = "feeds_and_speeds/auto_convert_to_metric"

    def __init__(self):
        """Initialize personal toolbox manager."""
        self.settings = QSettings()
        self.logger = logger

    def add_tool(self, tool: Tool) -> bool:
        """
        Add a tool to personal toolbox.

        Args:
            tool: Tool to add

        Returns:
            True if successful
        """
        try:
            toolbox = self._load_toolbox()

            # Check if tool already exists
            if any(t["guid"] == tool.guid for t in toolbox):
                self.logger.info(f"Tool {tool.description} already in toolbox")
                return False

            toolbox.append(tool.to_dict())
            self._save_toolbox(toolbox)
            self.logger.info(f"Added tool to toolbox: {tool.description}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to add tool to toolbox: {e}")
            return False

    def remove_tool(self, tool_guid: str) -> bool:
        """
        Remove a tool from personal toolbox.

        Args:
            tool_guid: GUID of tool to remove

        Returns:
            True if successful
        """
        try:
            toolbox = self._load_toolbox()
            toolbox = [t for t in toolbox if t["guid"] != tool_guid]
            self._save_toolbox(toolbox)
            self.logger.info(f"Removed tool from toolbox: {tool_guid}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to remove tool from toolbox: {e}")
            return False

    def get_toolbox(self) -> List[Tool]:
        """Get all tools in personal toolbox."""
        try:
            toolbox_data = self._load_toolbox()
            return [Tool.from_dict(t) for t in toolbox_data]
        except Exception as e:
            self.logger.error(f"Failed to load toolbox: {e}")
            return []

    def has_tool(self, tool_guid: str) -> bool:
        """Check if tool is in personal toolbox."""
        toolbox = self._load_toolbox()
        return any(t["guid"] == tool_guid for t in toolbox)

    def set_auto_convert_to_metric(self, enabled: bool) -> None:
        """
        Set auto-convert to metric setting.

        Args:
            enabled: True to enable auto-conversion
        """
        self.settings.setValue(self.UNIT_CONVERSION_KEY, enabled)
        self.logger.info(f"Auto-convert to metric: {enabled}")

    def get_auto_convert_to_metric(self) -> bool:
        """Get auto-convert to metric setting."""
        return self.settings.value(self.UNIT_CONVERSION_KEY, False, type=bool)

    def _load_toolbox(self) -> List[Dict[str, Any]]:
        """Load toolbox from settings."""
        try:
            toolbox_json = self.settings.value(self.SETTINGS_KEY, "[]", type=str)
            return json.loads(toolbox_json)
        except Exception as e:
            self.logger.debug(f"Failed to load toolbox from settings: {e}")
            return []

    def _save_toolbox(self, toolbox: List[Dict[str, Any]]) -> None:
        """Save toolbox to settings."""
        try:
            toolbox_json = json.dumps(toolbox)
            self.settings.setValue(self.SETTINGS_KEY, toolbox_json)
            self.settings.sync()
        except Exception as e:
            self.logger.error(f"Failed to save toolbox to settings: {e}")
