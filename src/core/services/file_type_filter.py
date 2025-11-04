"""
File Type Filter for managing supported and blocked file types.

Maintains whitelist of supported files and blacklist of potentially harmful system files.
Provides file classification and filtering capabilities.
"""

from pathlib import Path
from typing import Set, List, Tuple
from dataclasses import dataclass

from ..logging_config import get_logger, log_function_call

logger = get_logger(__name__)


@dataclass
class FileTypeFilterResult:
    """Result of file type filtering."""

    file_path: str
    file_name: str
    extension: str
    is_allowed: bool
    reason: str
    category: str


class FileTypeFilter:
    """Manages file type filtering with whitelist and blacklist."""

    # Supported file types (whitelist)
    SUPPORTED_EXTENSIONS = {
        # 3D Models
        ".stl",
        ".obj",
        ".step",
        ".stp",
        ".3mf",
        ".ply",
        ".fbx",
        ".dae",
        ".gltf",
        ".glb",
        ".blend",
        ".max",
        ".ma",
        ".mb",
        ".c4d",
        ".lwo",
        ".lw",
        ".xsi",
        ".iges",
        ".igs",
        ".brep",
        ".sat",
        ".asm",
        ".prt",
        ".sldprt",
        ".sldasm",
        # Documents
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".txt",
        ".rtf",
        ".odt",
        ".ods",
        ".odp",
        ".pages",
        ".numbers",
        ".keynote",
        # Images
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".svg",
        ".tiff",
        ".tif",
        ".webp",
        ".ico",
        ".psd",
        ".ai",
        ".eps",
        ".heic",
        ".raw",
        # Metadata & Config
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        ".csv",
        ".tsv",
        ".md",
        ".markdown",
        ".txt",
        ".ini",
        ".conf",
        ".config",
        ".properties",
        # Archives (for reference)
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        # Video (for reference)
        ".mp4",
        ".avi",
        ".mov",
        ".mkv",
        ".flv",
        ".wmv",
        ".webm",
        # Audio (for reference)
        ".mp3",
        ".wav",
        ".flac",
        ".aac",
        ".ogg",
        ".m4a",
    }

    # Blocked file types (blacklist) - potentially harmful
    BLOCKED_EXTENSIONS = {
        # Executables
        ".exe",
        ".com",
        ".bat",
        ".cmd",
        ".scr",
        ".vbs",
        ".js",
        ".jse",
        ".ws",
        ".wsf",
        ".msi",
        ".app",
        ".deb",
        ".rpm",
        ".dmg",
        ".pkg",
        # System files
        ".sys",
        ".dll",
        ".so",
        ".dylib",
        ".drv",
        ".device",
        # Scripts (potentially harmful)
        ".ps1",
        ".ps2",
        ".psc1",
        ".psc2",
        ".msh",
        ".msh1",
        ".msh2",
        ".mshxml",
        ".msh1xml",
        ".msh2xml",
        ".sh",
        ".bash",
        ".zsh",
        ".ksh",
        ".csh",
        ".tcsh",
        ".pl",
        ".py",
        ".rb",
        ".php",
        ".asp",
        ".aspx",
        ".jsp",
        ".jspx",
        # Shortcuts
        ".lnk",
        ".url",
        ".desktop",
        # Compressed with scripts
        ".jar",
        ".class",
        # Macro-enabled documents
        ".xlsm",
        ".docm",
        ".pptm",
    }

    # Blocked filenames (case-insensitive)
    BLOCKED_FILENAMES = {
        "autorun.inf",
        "boot.ini",
        "config.sys",
        "io.sys",
        "msdos.sys",
        "ntldr",
        "ntdetect.com",
        "hal.dll",
        "kernel32.dll",
        "thumbs.db",
        "desktop.ini",
        "system.ini",
        "win.ini",
    }

    def __init__(self) -> None:
        """Initialize file type filter."""
        self.logger = logger

    @log_function_call(logger)
    def filter_file(self, file_path: str) -> FileTypeFilterResult:
        """
        Filter a single file for allowed/blocked status.

        Args:
            file_path: Path to file to filter

        Returns:
            FileTypeFilterResult with filtering decision
        """
        try:
            path = Path(file_path)
            file_name = path.name
            extension = path.suffix.lower()

            # Check blocked filenames
            if file_name.lower() in self.BLOCKED_FILENAMES:
                return FileTypeFilterResult(
                    file_path=file_path,
                    file_name=file_name,
                    extension=extension,
                    is_allowed=False,
                    reason="Blocked system filename",
                    category="System",
                )

            # Check blocked extensions
            if extension in self.BLOCKED_EXTENSIONS:
                return FileTypeFilterResult(
                    file_path=file_path,
                    file_name=file_name,
                    extension=extension,
                    is_allowed=False,
                    reason=f"Blocked file type: {extension}",
                    category="Blocked",
                )

            # Check supported extensions
            if extension in self.SUPPORTED_EXTENSIONS:
                category = self._categorize_file(extension)
                return FileTypeFilterResult(
                    file_path=file_path,
                    file_name=file_name,
                    extension=extension,
                    is_allowed=True,
                    reason="Supported file type",
                    category=category,
                )

            # Unknown extension - allow by default
            return FileTypeFilterResult(
                file_path=file_path,
                file_name=file_name,
                extension=extension,
                is_allowed=True,
                reason="Unknown file type (allowed)",
                category="Other",
            )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            logger.error("Failed to filter file: %s", str(e))
            raise

    @log_function_call(logger)
    def filter_files(
        """TODO: Add docstring."""
        self, file_paths: List[str]
    ) -> Tuple[List[FileTypeFilterResult], List[FileTypeFilterResult]]:
        """
        Filter multiple files.

        Args:
            file_paths: List of file paths to filter

        Returns:
            Tuple of (allowed_files, blocked_files)
        """
        allowed = []
        blocked = []

        for file_path in file_paths:
            result = self.filter_file(file_path)
            if result.is_allowed:
                allowed.append(result)
            else:
                blocked.append(result)

        logger.info(
            f"Filtered {len(file_paths)} files: {len(allowed)} allowed, {len(blocked)} blocked"
        )
        return allowed, blocked

    def _categorize_file(self, extension: str) -> str:
        """Categorize file by extension."""
        extension = extension.lower()

        if extension in {
            ".stl",
            ".obj",
            ".step",
            ".stp",
            ".3mf",
            ".ply",
            ".fbx",
            ".dae",
            ".gltf",
            ".glb",
            ".blend",
            ".max",
            ".ma",
            ".mb",
            ".c4d",
            ".lwo",
            ".lw",
            ".xsi",
            ".iges",
            ".igs",
            ".brep",
            ".sat",
            ".asm",
            ".prt",
            ".sldprt",
            ".sldasm",
        }:
            return "3D Models"
        elif extension in {
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            ".ppt",
            ".pptx",
            ".txt",
            ".rtf",
            ".odt",
            ".ods",
            ".odp",
            ".pages",
            ".numbers",
            ".keynote",
        }:
            return "Documents"
        elif extension in {
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".bmp",
            ".svg",
            ".tiff",
            ".tif",
            ".webp",
            ".ico",
            ".psd",
            ".ai",
            ".eps",
            ".heic",
            ".raw",
        }:
            return "Images"
        elif extension in {
            ".json",
            ".xml",
            ".yaml",
            ".yml",
            ".csv",
            ".tsv",
            ".md",
            ".markdown",
            ".ini",
            ".conf",
            ".config",
            ".properties",
        }:
            return "Metadata"
        elif extension in {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"}:
            return "Archives"
        elif extension in {".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"}:
            return "Video"
        elif extension in {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"}:
            return "Audio"
        else:
            return "Other"

    def is_allowed(self, file_path: str) -> bool:
        """Check if file is allowed."""
        result = self.filter_file(file_path)
        return result.is_allowed

    def is_blocked(self, file_path: str) -> bool:
        """Check if file is blocked."""
        result = self.filter_file(file_path)
        return not result.is_allowed

    def get_supported_extensions(self) -> Set[str]:
        """Get set of supported extensions."""
        return self.SUPPORTED_EXTENSIONS.copy()

    def get_blocked_extensions(self) -> Set[str]:
        """Get set of blocked extensions."""
        return self.BLOCKED_EXTENSIONS.copy()
