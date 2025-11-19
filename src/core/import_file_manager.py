"""
File management system for 3D model import process.

Handles two file management modes:
1. "Keep Organized" - Application manages file locations with organized directory structure
2. "Leave in Place" - Files remain in their original locations

Provides file copying/moving with progress tracking, duplicate detection,
and rollback capability for failed imports.
"""

import json
import shutil
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Optional, Callable, List, Dict, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

from src.core.logging_config import get_logger
from src.core.fast_hasher import FastHasher
from src.core.root_folder_manager import RootFolderManager
from src.core.cancellation_token import CancellationToken
from src.core.security import PathValidator, SecurityEventLogger
from src.core.services.file_type_filter import FileTypeFilter


class FileManagementMode(Enum):
    """File management modes for import."""

    KEEP_ORGANIZED = "keep_organized"
    LEAVE_IN_PLACE = "leave_in_place"


class DuplicateAction(Enum):
    """Actions to take when duplicate is detected."""

    SKIP = "skip"
    REPLACE = "replace"
    KEEP_BOTH = "keep_both"
    PROMPT = "prompt"


@dataclass
class ImportFileInfo:
    """Information about a file being imported."""

    original_path: str
    file_size: int
    file_hash: Optional[str] = None
    managed_path: Optional[str] = None
    import_status: str = "pending"
    error_message: Optional[str] = None
    progress_percent: int = 0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    source_origin: Optional[str] = None  # Archive or download origin


@dataclass
class ImportSession:
    """Tracks an import session for rollback support."""

    session_id: str
    mode: FileManagementMode
    root_directory: Optional[str] = None
    files: List[ImportFileInfo] = field(default_factory=list)
    copied_files: List[str] = field(default_factory=list)  # For rollback
    created_directories: List[str] = field(default_factory=list)  # For rollback
    temporary_paths: List[str] = field(default_factory=list)  # Extracted archives
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    status: str = "pending"


@dataclass
class ImportResult:
    """Result of import operation."""

    success: bool
    session: ImportSession
    total_files: int
    processed_files: int
    failed_files: int
    skipped_files: int
    duplicate_count: int
    total_size_bytes: int
    duration_seconds: float
    error_message: Optional[str] = None


class ImportFileManager:
    """
    Manages file operations for the 3D model import process.

    Features:
    - Dual mode support: "keep organized" vs "leave in place"
    - Root directory validation for organized mode
    - File copying/moving with progress tracking
    - Duplicate detection using FastHasher
    - Organized directory structure creation
    - Rollback capability for failed operations
    - Comprehensive JSON logging
    - Error handling and recovery
    """

    # Directory structure for organized mode
    ORGANIZED_SUBDIRS = {
        "stl": "Models",
        "obj": "Models",
        "step": "Models",
        "stp": "Models",
        "3mf": "Models",
        "ply": "Models",
        "fbx": "Models",
        "dae": "Models",
        "gltf": "Models",
        "glb": "Models",
        "other": "Other_Files",
    }

    ARCHIVE_EXTENSIONS = {".zip"}

    def __init__(self) -> None:
        """Initialize the import file manager."""
        self.logger = get_logger(__name__)
        self.fast_hasher = FastHasher()
        self.root_folder_manager = RootFolderManager.get_instance()
        self.file_type_filter = FileTypeFilter()
        self._active_session: Optional[ImportSession] = None

        self._log_json(
            "file_manager_initialized",
            {
                "supported_modes": [mode.value for mode in FileManagementMode],
                "organized_subdirs": self.ORGANIZED_SUBDIRS,
            },
        )

    def _log_json(self, event: str, data: dict) -> None:
        """Log event in JSON format as required by quality standards."""
        log_entry = {"event": event, "timestamp": time.time(), **data}
        self.logger.debug(json.dumps(log_entry))

    def _prepare_import_entries(
        self, file_paths: List[str], session: ImportSession
    ) -> List[Tuple[str, Optional[str]]]:
        """Expand provided paths into individual files, extracting archives."""

        entries: List[Tuple[str, Optional[str]]] = []

        for raw_path in file_paths:
            try:
                path = Path(raw_path).resolve()
            except (OSError, ValueError):
                self.logger.warning("Skipping invalid import path: %s", raw_path)
                continue

            if not path.exists():
                self.logger.warning("Import path does not exist: %s", path)
                continue

            if path.is_dir():
                for candidate in path.rglob("*"):
                    if candidate.is_file():
                        entries.append((str(candidate), None))
                continue

            if self._is_archive(path):
                extracted = self._extract_archive(path, session)
                if extracted:
                    for candidate in extracted.rglob("*"):
                        if candidate.is_file():
                            entries.append((str(candidate), str(path)))
                else:
                    self.logger.warning("Failed to extract archive: %s", path)
                continue

            entries.append((str(path), None))

        return entries

    def _is_archive(self, path: Path) -> bool:
        """Return True if the file appears to be an importable archive."""

        return path.suffix.lower() in self.ARCHIVE_EXTENSIONS

    def _extract_archive(self, archive_path: Path, session: ImportSession) -> Optional[Path]:
        """Extract the archive to a temporary staging directory."""

        staging_root = Path(tempfile.gettempdir()) / "digital_workshop_imports"
        staging_root.mkdir(parents=True, exist_ok=True)
        target_dir = staging_root / f"{archive_path.stem}_{session.session_id}"

        try:
            with zipfile.ZipFile(archive_path) as archive:
                archive.extractall(target_dir)
        except (zipfile.BadZipFile, OSError, ValueError) as exc:
            self.logger.error("Unable to extract %s: %s", archive_path, exc)
            return None

        session.temporary_paths.append(str(target_dir))
        return target_dir

    def _generate_session_id(self) -> str:
        """Generate unique session ID for tracking."""
        return f"import_{int(time.time() * 1000)}"

    def validate_root_directory(
        self, root_directory: str, mode: FileManagementMode
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate root directory for the specified management mode.

        Args:
            root_directory: Path to root directory
            mode: File management mode

        Returns:
            Tuple of (is_valid, error_message)
        """
        self._log_json(
            "validating_root_directory",
            {"root_directory": root_directory, "mode": mode.value},
        )

        # Leave in place mode doesn't require root directory validation
        if mode == FileManagementMode.LEAVE_IN_PLACE:
            return True, None

        # Keep organized mode requires root directory
        if not root_directory:
            error = "Root directory is required for 'keep organized' mode"
            self.logger.warning(error)
            return False, error

        try:
            root_path = Path(root_directory).resolve()

            # Check if path exists
            if not root_path.exists():
                error = f"Root directory does not exist: {root_directory}"
                self.logger.warning(error)
                return False, error

            # Check if it's a directory
            if not root_path.is_dir():
                error = f"Path is not a directory: {root_directory}"
                self.logger.warning(error)
                return False, error

            # Check write permissions
            test_file = root_path / f".test_write_{int(time.time())}"
            try:
                test_file.touch()
                test_file.unlink()
            except (PermissionError, OSError) as exc:
                error = f"No write permission for directory: {root_directory}"
                self.logger.warning("%s: %s", error, exc)
                return False, error

            # Ensure this directory is registered as a library root so that
            # the file browser can access it consistently. If it is not yet
            # configured, try to add it automatically instead of failing.
            configured_roots = self.root_folder_manager.get_folder_paths(enabled_only=True)
            normalized_roots = {Path(p).resolve() for p in configured_roots}

            if root_path not in normalized_roots:
                added = self.root_folder_manager.add_folder(str(root_path))
                if not added:
                    error = f"Directory is not a configured root folder: {root_directory}"
                    self.logger.warning(error)
                    return False, error

            self._log_json("root_directory_valid", {"root_directory": str(root_path)})

            return True, None

            self._log_json("root_directory_valid", {"root_directory": str(root_path)})

            return True, None

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
            error = f"Error validating root directory: {exc}"
            self.logger.error(error, exc_info=True)
            return False, error

    def _get_organized_subdir(self, file_path: str) -> str:
        """Get subdirectory name for file based on extension."""
        ext = Path(file_path).suffix.lower().lstrip(".")
        return self.ORGANIZED_SUBDIRS.get(ext, self.ORGANIZED_SUBDIRS["other"])

    def _create_organized_path(
        self, root_directory: str, file_path: str, file_hash: Optional[str] = None
    ) -> Path:
        """
        Create organized file path with directory structure.

        Args:
            root_directory: Root directory for organized storage
            file_path: Original file path
            file_hash: Optional file hash for naming

        Returns:
            Path object for organized file location
        """
        original_path = Path(file_path)
        root_path = Path(root_directory)

        # Determine subdirectory based on file type
        subdir = self._get_organized_subdir(file_path)

        # Create directory structure: root/subdir/filename
        target_dir = root_path / subdir

        # Prefer the original, human-friendly filename when possible
        stem = original_path.stem
        suffix = original_path.suffix

        # First choice: original filename
        filename = original_path.name
        target_path = target_dir / filename
        if not target_path.exists():
            return target_path

        # If there is a conflict and we have a hash, try a hash-based filename next
        if file_hash:
            hash_filename = f"{file_hash}{suffix}"
            hash_path = target_dir / hash_filename
            if not hash_path.exists():
                return hash_path

        # Final fallback: append a numeric suffix to the original stem
        counter = 1
        while True:
            filename = f"{stem}_{counter}{suffix}"
            target_path = target_dir / filename
            if not target_path.exists():
                return target_path
            counter += 1

    def _copy_file_with_progress(
        self,
        source: Path,
        destination: Path,
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> None:
        """
        Copy file with progress tracking.

        Args:
            source: Source file path
            destination: Destination file path
            progress_callback: Optional callback(percent)
        """
        file_size = source.stat().st_size
        copied = 0
        chunk_size = 1024 * 1024  # 1MB chunks

        # Create destination directory
        destination.parent.mkdir(parents=True, exist_ok=True)

        with source.open("rb") as src, destination.open("wb") as dst:
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break

                dst.write(chunk)
                copied += len(chunk)

                if progress_callback and file_size > 0:
                    percent = int((copied / file_size) * 100)
                    progress_callback(percent)

    def start_import_session(
        self,
        file_paths: List[str],
        mode: FileManagementMode,
        root_directory: Optional[str] = None,
        duplicate_action: DuplicateAction = DuplicateAction.SKIP,
    ) -> Tuple[bool, Optional[str], Optional[ImportSession]]:
        """
        Start a new import session.

        Args:
            file_paths: List of file paths to import
            mode: File management mode
            root_directory: Root directory (required for keep_organized mode)
            duplicate_action: Action to take for duplicates

        Returns:
            Tuple of (success, error_message, session)
        """
        self._log_json(
            "starting_import_session",
            {
                "file_count": len(file_paths),
                "mode": mode.value,
                "root_directory": root_directory,
                "duplicate_action": duplicate_action.value,
            },
        )

        # Validate root directory
        is_valid, error = self.validate_root_directory(root_directory, mode)
        if not is_valid:
            return False, error, None

        # Create session
        session = ImportSession(
            session_id=self._generate_session_id(),
            mode=mode,
            root_directory=root_directory,
            start_time=time.time(),
            status="running",
        )

        prepared_entries = self._prepare_import_entries(file_paths, session)

        # Create file info for each file
        security_logger = SecurityEventLogger()

        for file_path, source_origin in prepared_entries:
            try:
                # Check for system files (security check)
                # Note: We don't validate path traversal for imports since users
                # should be able to import files from anywhere on their system
                if PathValidator.is_system_file(file_path):
                    security_logger.log_system_file_blocked(file_path)
                    self.logger.warning("System file blocked: %s", file_path)
                    continue

                # Apply file type filter (additional security layer)
                filter_result = self.file_type_filter.filter_file(file_path)
                if not filter_result.is_allowed:
                    security_logger.log_invalid_file_type(
                        file_path, filter_result.extension or "unknown"
                    )
                    self.logger.warning(
                        "File blocked by type filter (%s): %s",
                        filter_result.reason,
                        file_path,
                    )
                    continue

                path = Path(file_path)
                if path.exists() and path.is_file():
                    file_info = ImportFileInfo(
                        original_path=file_path,
                        file_size=path.stat().st_size,
                        start_time=time.time(),
                        source_origin=source_origin,
                    )
                    session.files.append(file_info)
                else:
                    self.logger.warning("File not found or not accessible: %s", file_path)
            except (OSError, IOError) as e:
                self.logger.error("Error accessing file %s: %s", file_path, e)

        if not session.files:
            return False, "No valid files to import", None

        self._active_session = session

        self._log_json(
            "import_session_started",
            {"session_id": session.session_id, "valid_file_count": len(session.files)},
        )

        return True, None, session

    def process_file(
        self,
        file_info: ImportFileInfo,
        session: ImportSession,
        progress_callback: Optional[Callable[[str, int], None]] = None,
        cancellation_token: Optional[CancellationToken] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Process a single file for import.

        Args:
            file_info: File information
            session: Import session
            progress_callback: Optional callback(message, percent)
            cancellation_token: Optional cancellation token

        Returns:
            Tuple of (success, error_message)
        """
        try:
            source_path = Path(file_info.original_path)

            # Update status
            file_info.import_status = "hashing"
            if progress_callback:
                progress_callback(f"Hashing {source_path.name}", 10)

            # Calculate file hash for duplicate detection
            self._log_json(
                "calculating_file_hash",
                {"file": source_path.name, "size": file_info.file_size},
            )

            hash_result = self.fast_hasher.hash_file(
                file_info.original_path, cancellation_token=cancellation_token
            )

            if not hash_result.success:
                file_info.import_status = "failed"
                file_info.error_message = hash_result.error
                file_info.end_time = time.time()
                return False, f"Failed to hash file: {hash_result.error}"

            file_info.file_hash = hash_result.hash_value

            # Check for cancellation
            if cancellation_token and cancellation_token.is_cancelled():
                return False, "Operation cancelled"

            # Handle file based on management mode
            if session.mode == FileManagementMode.KEEP_ORGANIZED:
                # Copy to organized location
                file_info.import_status = "copying"
                if progress_callback:
                    progress_callback(f"Copying {source_path.name}", 50)

                target_path = self._create_organized_path(
                    session.root_directory, file_info.original_path, file_info.file_hash
                )

                self._log_json(
                    "copying_file",
                    {"source": str(source_path), "destination": str(target_path)},
                )

                # Track directory creation for rollback
                if not target_path.parent.exists():
                    session.created_directories.append(str(target_path.parent))

                # Copy file
                def copy_progress(percent) -> None:
                    """TODO: Add docstring."""
                    if progress_callback:
                        progress_callback(f"Copying {source_path.name}", 50 + (percent // 2))

                self._copy_file_with_progress(source_path, target_path, copy_progress)

                # Track for rollback
                session.copied_files.append(str(target_path))
                file_info.managed_path = str(target_path)

            else:  # LEAVE_IN_PLACE
                # Just track original path
                file_info.managed_path = file_info.original_path

            # Update status
            file_info.import_status = "completed"
            file_info.progress_percent = 100
            file_info.end_time = time.time()

            if progress_callback:
                progress_callback(f"Completed {source_path.name}", 100)

            self._log_json(
                "file_processed",
                {
                    "file": source_path.name,
                    "hash": file_info.file_hash[:16] + "...",
                    "mode": session.mode.value,
                    "managed_path": file_info.managed_path,
                },
            )

            return True, None

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            error_msg = f"Error processing file: {e}"
            self.logger.error(error_msg, exc_info=True)
            file_info.import_status = "failed"
            file_info.error_message = str(e)
            file_info.end_time = time.time()
            return False, error_msg

    def rollback_session(self, session: ImportSession) -> bool:
        """
        Rollback a failed import session.

        Args:
            session: Import session to rollback

        Returns:
            True if rollback successful
        """
        self._log_json(
            "rolling_back_session",
            {
                "session_id": session.session_id,
                "copied_files_count": len(session.copied_files),
                "created_dirs_count": len(session.created_directories),
            },
        )

        rollback_success = True

        try:
            # Remove copied files
            for file_path in reversed(session.copied_files):
                try:
                    path = Path(file_path)
                    if path.exists():
                        path.unlink()
                        self.logger.info("Rolled back copied file: %s", file_path)
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as exc:
                    self.logger.error(
                        "Failed to remove file during rollback: %s: %s", file_path, exc
                    )
                    rollback_success = False

            # Remove created directories (if empty)
            for dir_path in reversed(session.created_directories):
                try:
                    path = Path(dir_path)
                    if path.exists() and path.is_dir():
                        # Only remove if empty
                        if not list(path.iterdir()):
                            path.rmdir()
                            self.logger.info("Rolled back created directory: %s", dir_path)
                except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
                    self.logger.error(
                        f"Failed to remove directory during rollback: {dir_path}: {e}"
                    )
                    rollback_success = False

            self._log_json(
                "rollback_completed",
                {"session_id": session.session_id, "success": rollback_success},
            )

            return rollback_success

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Error during rollback: %s", e, exc_info=True)
            return False

    def complete_import_session(self, session: ImportSession, success: bool = True) -> ImportResult:
        """
        Complete an import session and generate result.

        Args:
            session: Import session to complete
            success: Whether session completed successfully

        Returns:
            ImportResult with session details
        """
        session.end_time = time.time()
        session.status = "completed" if success else "failed"

        # Calculate statistics
        total_files = len(session.files)
        processed_files = sum(1 for f in session.files if f.import_status == "completed")
        failed_files = sum(1 for f in session.files if f.import_status == "failed")
        skipped_files = sum(1 for f in session.files if f.import_status == "skipped")
        total_size = sum(f.file_size for f in session.files)
        duration = session.end_time - session.start_time

        # Count duplicates (files with same hash)
        hash_counts = {}
        for f in session.files:
            if f.file_hash:
                hash_counts[f.file_hash] = hash_counts.get(f.file_hash, 0) + 1
        duplicate_count = sum(1 for count in hash_counts.values() if count > 1)

        result = ImportResult(
            success=success,
            session=session,
            total_files=total_files,
            processed_files=processed_files,
            failed_files=failed_files,
            skipped_files=skipped_files,
            duplicate_count=duplicate_count,
            total_size_bytes=total_size,
            duration_seconds=duration,
        )

        self._log_json(
            "import_session_completed",
            {
                "session_id": session.session_id,
                "success": success,
                "total_files": total_files,
                "processed": processed_files,
                "failed": failed_files,
                "skipped": skipped_files,
                "duplicates": duplicate_count,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "duration_seconds": round(duration, 2),
            },
        )

        self._cleanup_temporary_paths(session)
        self._active_session = None

        return result

    def get_active_session(self) -> Optional[ImportSession]:
        """Get currently active import session."""
        return self._active_session

    def check_duplicate(
        self, file_hash: str, existing_hashes: Dict[str, Any]
    ) -> Tuple[bool, Optional[Any]]:
        """
        Check if file is a duplicate based on hash.

        Args:
            file_hash: Hash of file to check
            existing_hashes: Dictionary mapping hashes to existing file info

        Returns:
            Tuple of (is_duplicate, existing_file_info)
        """
        if file_hash in existing_hashes:
            return True, existing_hashes[file_hash]
        return False, None

    def _cleanup_temporary_paths(self, session: ImportSession) -> None:
        """Remove any temporary directories or files created during import."""

        for temp_path in list(session.temporary_paths):
            path = Path(temp_path)
            try:
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                elif path.exists():
                    path.unlink()
            except (OSError, IOError, ValueError) as exc:
                self.logger.warning("Failed to clean temporary path %s: %s", path, exc)

        session.temporary_paths.clear()
