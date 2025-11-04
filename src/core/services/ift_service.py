"""
IFT (Interaction File Type) Service for managing interaction file types configuration.

Loads, validates, and manages IFT configuration from QSettings.
Provides access to IFT definitions and validation.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from PySide6.QtCore import QSettings

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


@dataclass
class IFTDefinition:
    """Definition of an Interaction File Type."""

    name: str
    extension: str
    description: str
    icon: Optional[str] = None
    color: Optional[str] = None
    enabled: bool = True


class IFTService:
    """Service for managing Interaction File Types."""

    # Default IFT definitions
    DEFAULT_IFTS = {
        "stl": IFTDefinition(
            name="STL Model",
            extension=".stl",
            description="Stereolithography 3D model file",
            color="#FF6B6B",
        ),
        "obj": IFTDefinition(
            name="OBJ Model",
            extension=".obj",
            description="Wavefront OBJ 3D model file",
            color="#4ECDC4",
        ),
        "step": IFTDefinition(
            name="STEP Model",
            extension=".step",
            description="STEP 3D model file",
            color="#45B7D1",
        ),
        "pdf": IFTDefinition(
            name="PDF Document",
            extension=".pdf",
            description="Portable Document Format",
            color="#FFA07A",
        ),
        "png": IFTDefinition(
            name="PNG Image",
            extension=".png",
            description="Portable Network Graphics image",
            color="#98D8C8",
        ),
        "jpg": IFTDefinition(
            name="JPEG Image",
            extension=".jpg",
            description="JPEG image file",
            color="#F7DC6F",
        ),
    }

    def __init__(self):
        """Initialize IFT service."""
        self.logger = logger
        self.settings = QSettings("DigitalWorkshop", "DigitalWorkshop")
        self.ifts: Dict[str, IFTDefinition] = {}
        self._load_ifts()

    @log_function_call(logger)
    def _load_ifts(self) -> None:
        """Load IFT definitions from QSettings."""
        try:
            # Check if IFTs are stored in settings
            self.settings.beginGroup("IFT")
            keys = self.settings.childKeys()

            if keys:
                # Load from settings
                for key in keys:
                    data = self.settings.value(key, {})
                    if isinstance(data, dict):
                        self.ifts[key] = IFTDefinition(**data)
            else:
                # Use defaults and save
                self.ifts = self.DEFAULT_IFTS.copy()
                self._save_ifts()

            self.settings.endGroup()
            logger.info(f"Loaded {len(self.ifts)} IFT definitions")

        except Exception as e:
            logger.error(f"Failed to load IFTs: {str(e)}")
            self.ifts = self.DEFAULT_IFTS.copy()

    @log_function_call(logger)
    def _save_ifts(self) -> None:
        """Save IFT definitions to QSettings."""
        try:
            self.settings.beginGroup("IFT")
            self.settings.remove("")  # Clear existing

            for key, ift in self.ifts.items():
                data = {
                    "name": ift.name,
                    "extension": ift.extension,
                    "description": ift.description,
                    "icon": ift.icon,
                    "color": ift.color,
                    "enabled": ift.enabled,
                }
                self.settings.setValue(key, data)

            self.settings.endGroup()
            logger.info(f"Saved {len(self.ifts)} IFT definitions")

        except Exception as e:
            logger.error(f"Failed to save IFTs: {str(e)}")

    def get_ift(self, key: str) -> Optional[IFTDefinition]:
        """Get IFT definition by key."""
        return self.ifts.get(key)

    def get_ift_by_extension(self, extension: str) -> Optional[IFTDefinition]:
        """Get IFT definition by file extension."""
        extension = extension.lower()
        for ift in self.ifts.values():
            if ift.extension.lower() == extension:
                return ift
        return None

    def list_ifts(self, enabled_only: bool = False) -> List[IFTDefinition]:
        """List all IFT definitions."""
        ifts = list(self.ifts.values())
        if enabled_only:
            ifts = [ift for ift in ifts if ift.enabled]
        return sorted(ifts, key=lambda x: x.name)

    def add_ift(self, key: str, ift: IFTDefinition) -> bool:
        """Add or update IFT definition."""
        try:
            self.ifts[key] = ift
            self._save_ifts()
            logger.info(f"Added IFT: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to add IFT: {str(e)}")
            return False

    def remove_ift(self, key: str) -> bool:
        """Remove IFT definition."""
        try:
            if key in self.ifts:
                del self.ifts[key]
                self._save_ifts()
                logger.info(f"Removed IFT: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove IFT: {str(e)}")
            return False

    def enable_ift(self, key: str) -> bool:
        """Enable IFT definition."""
        try:
            if key in self.ifts:
                self.ifts[key].enabled = True
                self._save_ifts()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to enable IFT: {str(e)}")
            return False

    def disable_ift(self, key: str) -> bool:
        """Disable IFT definition."""
        try:
            if key in self.ifts:
                self.ifts[key].enabled = False
                self._save_ifts()
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to disable IFT: {str(e)}")
            return False

    def reset_to_defaults(self) -> bool:
        """Reset IFT definitions to defaults."""
        try:
            self.ifts = self.DEFAULT_IFTS.copy()
            self._save_ifts()
            logger.info("Reset IFTs to defaults")
            return True
        except Exception as e:
            logger.error(f"Failed to reset IFTs: {str(e)}")
            return False

    def validate_ift(self, ift: IFTDefinition) -> bool:
        """Validate IFT definition."""
        if not ift.name or not ift.extension:
            return False
        if not ift.extension.startswith("."):
            return False
        return True

    def get_ift_count(self) -> int:
        """Get total number of IFT definitions."""
        return len(self.ifts)

    def get_enabled_ift_count(self) -> int:
        """Get number of enabled IFT definitions."""
        return sum(1 for ift in self.ifts.values() if ift.enabled)
