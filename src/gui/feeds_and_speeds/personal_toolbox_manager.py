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
    FOLDERS_KEY = "feeds_and_speeds/tool_folders"

    def __init__(self) -> None:
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
                self.logger.info("Tool %s already in toolbox", tool.description)
                return False

            toolbox.append(tool.to_dict())
            self._save_toolbox(toolbox)
            self.logger.info("Added tool to toolbox: %s", tool.description)
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to add tool to toolbox: %s", e)
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
            self.logger.info("Removed tool from toolbox: %s", tool_guid)
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to remove tool from toolbox: %s", e)
            return False

    def get_toolbox(self) -> List[Tool]:
        """Get all tools in personal toolbox."""
        try:
            toolbox_data = self._load_toolbox()
            return [Tool.from_dict(t) for t in toolbox_data]
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to load toolbox: %s", e)
            return []

    def get_all_tools(self) -> List[Tool]:
        """Compatibility wrapper for retrieving all tools."""
        return self.get_toolbox()

    def get_all_presets(self) -> List[Tool]:
        """Personal toolbox does not distinguish presets; return tools."""
        return self.get_toolbox()

    def has_tool(self, tool_guid: str) -> bool:
        """Check if tool is in personal toolbox."""
        toolbox = self._load_toolbox()
        return any(t["guid"] == tool_guid for t in toolbox)

    def update_tool(self, updated_tool: Tool) -> bool:
        """Replace an existing tool entry by GUID."""
        try:
            toolbox = self._load_toolbox()
            found = False
            for idx, tool in enumerate(toolbox):
                if tool.get("guid") == updated_tool.guid:
                    toolbox[idx] = updated_tool.to_dict()
                    found = True
                    break
            if not found:
                return False
            self._save_toolbox(toolbox)
            return True
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Failed to update tool: %s", exc)
            return False

    def list_folders(self) -> List[str]:
        """Return user-defined folder names."""
        try:
            raw = self.settings.value(self.FOLDERS_KEY, "[]", type=str)
            folders = json.loads(raw)
            if isinstance(folders, list):
                return [str(f) for f in folders if isinstance(f, str)]
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.debug("Failed to load folders: %s", exc)
        return []

    def add_folder(self, name: str) -> bool:
        """Add a folder name if it does not already exist."""
        name = (name or "").strip()
        if not name:
            return False
        folders = self.list_folders()
        if name in folders:
            return False
        folders.append(name)
        self._save_folders(folders)
        return True

    def rename_folder(self, old: str, new: str) -> bool:
        """Rename a folder and update tools referencing it."""
        old = (old or "").strip()
        new = (new or "").strip()
        if not old or not new:
            return False
        folders = self.list_folders()
        if old not in folders:
            return False
        if new in folders:
            return False
        folders = [new if f == old else f for f in folders]
        self._save_folders(folders)
        # Update tools
        toolbox = self._load_toolbox()
        changed = False
        for tool in toolbox:
            if tool.get("folder") == old:
                tool["folder"] = new
                changed = True
        if changed:
            self._save_toolbox(toolbox)
        return True

    def delete_folder(self, name: str) -> bool:
        """Delete a folder (tools move to no-folder)."""
        name = (name or "").strip()
        if not name:
            return False
        folders = self.list_folders()
        if name not in folders:
            return False
        folders = [f for f in folders if f != name]
        self._save_folders(folders)
        toolbox = self._load_toolbox()
        changed = False
        for tool in toolbox:
            if tool.get("folder") == name:
                tool["folder"] = ""
                changed = True
        if changed:
            self._save_toolbox(toolbox)
        return True

    def set_tool_folder(self, tool_guid: str, folder: str) -> bool:
        """Assign a folder to a tool."""
        folder = (folder or "").strip()
        toolbox = self._load_toolbox()
        changed = False
        for tool in toolbox:
            if tool.get("guid") == tool_guid:
                tool["folder"] = folder
                changed = True
                break
        if changed:
            self._save_toolbox(toolbox)
        return changed

    def set_auto_convert_to_metric(self, enabled: bool) -> None:
        """
        Set auto-convert to metric setting.

        Args:
            enabled: True to enable auto-conversion
        """
        self.settings.setValue(self.UNIT_CONVERSION_KEY, enabled)
        self.logger.info("Auto-convert to metric: %s", enabled)

    def get_auto_convert_to_metric(self) -> bool:
        """Get auto-convert to metric setting."""
        return self.settings.value(self.UNIT_CONVERSION_KEY, False, type=bool)

    def _load_toolbox(self) -> List[Dict[str, Any]]:
        """Load toolbox from settings."""
        try:
            toolbox_json = self.settings.value(self.SETTINGS_KEY, "[]", type=str)
            return json.loads(toolbox_json)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.debug("Failed to load toolbox from settings: %s", e)
            return []

    def _save_toolbox(self, toolbox: List[Dict[str, Any]]) -> None:
        """Save toolbox to settings."""
        try:
            toolbox_json = json.dumps(toolbox)
            self.settings.setValue(self.SETTINGS_KEY, toolbox_json)
            self.settings.sync()
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to save toolbox to settings: %s", e)

    def _save_folders(self, folders: List[str]) -> None:
        """Persist folder list."""
        try:
            self.settings.setValue(self.FOLDERS_KEY, json.dumps(folders))
            self.settings.sync()
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.debug("Failed to save folders: %s", exc)
