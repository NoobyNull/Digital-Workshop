"""
Resource Cleanup Handler - Specialized handler for system resource cleanup.

This handler is responsible for cleaning up system resources including
memory management, file handles, and temporary files.
"""

from typing import Any, Dict
import gc
import os
import tempfile
import weakref

from .unified_cleanup_coordinator import CleanupHandler, CleanupPhase, CleanupContext


class ResourceCleanupHandler(CleanupHandler):
    """
    Specialized handler for system resource cleanup.

    This handler manages resource-specific cleanup operations including:
    - Memory management
    - File handle cleanup
    - Network connection cleanup
    - Temporary file cleanup
    """

    def __init__(self):
        """Initialize the resource cleanup handler."""
        super().__init__("ResourceCleanupHandler")
        self._temp_files = []
        self._file_handles = []
        self._network_connections = []
        self._tracked_resources = weakref.WeakSet()

    def can_handle(self, phase: CleanupPhase) -> bool:
        """Check if this handler can handle the given phase."""
        return phase == CleanupPhase.RESOURCE_CLEANUP

    def execute(self, phase: CleanupPhase, context: CleanupContext) -> bool:
        """
        Execute resource cleanup for the given phase.

        Args:
            phase: The cleanup phase
            context: The cleanup context state

        Returns:
            True if cleanup completed successfully
        """
        try:
            self.logger.info("Starting resource cleanup")

            # Perform resource cleanup
            success = self._cleanup_resources()

            if success:
                self.logger.info("Resource cleanup completed successfully")
            else:
                self.logger.warning("Resource cleanup completed with some issues")

            return success

        except Exception as e:
            self.logger.error(f"Resource cleanup error: {e}", exc_info=True)
            return False

    def _cleanup_resources(self) -> bool:
        """Cleanup all system resources."""
        try:
            overall_success = True

            # Cleanup temporary files
            success = self._cleanup_temp_files()
            overall_success = overall_success and success

            # Cleanup file handles
            success = self._cleanup_file_handles()
            overall_success = overall_success and success

            # Cleanup network connections
            success = self._cleanup_network_connections()
            overall_success = overall_success and success

            # Cleanup tracked resources
            success = self._cleanup_tracked_resources()
            overall_success = overall_success and success

            # Force garbage collection
            success = self._force_garbage_collection()
            overall_success = overall_success and success

            return overall_success

        except Exception as e:
            self.logger.error(f"Resource cleanup failed: {e}")
            return False

    def _cleanup_temp_files(self) -> bool:
        """Cleanup temporary files."""
        try:
            self.logger.debug(f"Cleaning up {len(self._temp_files)} temporary files")

            files_cleaned = 0
            for temp_file in self._temp_files.copy():
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        files_cleaned += 1
                        self.logger.debug(f"Removed temporary file: {temp_file}")
                    self._temp_files.remove(temp_file)
                except Exception as e:
                    self.logger.warning(f"Failed to remove temporary file {temp_file}: {e}")

            self.logger.debug(f"Cleaned up {files_cleaned} temporary files")
            return True

        except Exception as e:
            self.logger.error(f"Temporary files cleanup failed: {e}")
            return False

    def _cleanup_file_handles(self) -> bool:
        """Cleanup file handles."""
        try:
            self.logger.debug(f"Cleaning up {len(self._file_handles)} file handles")

            handles_cleaned = 0
            for handle in self._file_handles.copy():
                try:
                    if hasattr(handle, "close") and not handle.closed:
                        handle.close()
                        handles_cleaned += 1
                        self.logger.debug("Closed file handle")
                    self._file_handles.remove(handle)
                except Exception as e:
                    self.logger.warning(f"Failed to close file handle: {e}")

            self.logger.debug(f"Cleaned up {handles_cleaned} file handles")
            return True

        except Exception as e:
            self.logger.error(f"File handles cleanup failed: {e}")
            return False

    def _cleanup_network_connections(self) -> bool:
        """Cleanup network connections."""
        try:
            self.logger.debug(f"Cleaning up {len(self._network_connections)} network connections")

            connections_cleaned = 0
            for connection in self._network_connections.copy():
                try:
                    if hasattr(connection, "close"):
                        connection.close()
                        connections_cleaned += 1
                        self.logger.debug("Closed network connection")
                    self._network_connections.remove(connection)
                except Exception as e:
                    self.logger.warning(f"Failed to close network connection: {e}")

            self.logger.debug(f"Cleaned up {connections_cleaned} network connections")
            return True

        except Exception as e:
            self.logger.error(f"Network connections cleanup failed: {e}")
            return False

    def _cleanup_tracked_resources(self) -> bool:
        """Cleanup tracked resources."""
        try:
            self.logger.debug(f"Cleaning up {len(self._tracked_resources)} tracked resources")

            resources_cleaned = 0
            for resource in list(self._tracked_resources):
                try:
                    if hasattr(resource, "cleanup"):
                        resource.cleanup()
                        resources_cleaned += 1
                        self.logger.debug(f"Cleaned up tracked resource: {type(resource).__name__}")
                except Exception as e:
                    self.logger.warning(
                        f"Failed to cleanup tracked resource {type(resource).__name__}: {e}"
                    )

            # Clear the tracked resources set
            self._tracked_resources.clear()

            self.logger.debug(f"Cleaned up {resources_cleaned} tracked resources")
            return True

        except Exception as e:
            self.logger.error(f"Tracked resources cleanup failed: {e}")
            return False

    def _force_garbage_collection(self) -> bool:
        """Force garbage collection to clean up unreferenced objects."""
        try:
            self.logger.debug("Forcing garbage collection")

            # Run garbage collection multiple times to ensure cleanup
            collected = gc.collect()
            collected += gc.collect()
            collected += gc.collect()

            self.logger.debug(f"Garbage collection freed {collected} objects")
            return True

        except Exception as e:
            self.logger.error(f"Garbage collection failed: {e}")
            return False

    def register_temp_file(self, file_path: str) -> None:
        """
        Register a temporary file for cleanup.

        Args:
            file_path: Path to the temporary file
        """
        try:
            if file_path and os.path.exists(file_path):
                self._temp_files.append(file_path)
                self.logger.debug(f"Registered temporary file for cleanup: {file_path}")
            else:
                self.logger.warning(f"Invalid temporary file registration: {file_path}")

        except Exception as e:
            self.logger.warning(f"Failed to register temporary file {file_path}: {e}")

    def register_file_handle(self, handle) -> None:
        """
        Register a file handle for cleanup.

        Args:
            handle: File handle object
        """
        try:
            if handle and hasattr(handle, "close"):
                self._file_handles.append(handle)
                self.logger.debug(f"Registered file handle for cleanup: {type(handle).__name__}")
            else:
                self.logger.warning(f"Invalid file handle registration: {type(handle)}")

        except Exception as e:
            self.logger.warning(f"Failed to register file handle: {e}")

    def register_network_connection(self, connection) -> None:
        """
        Register a network connection for cleanup.

        Args:
            connection: Network connection object
        """
        try:
            if connection and hasattr(connection, "close"):
                self._network_connections.append(connection)
                self.logger.debug(
                    f"Registered network connection for cleanup: {type(connection).__name__}"
                )
            else:
                self.logger.warning(f"Invalid network connection registration: {type(connection)}")

        except Exception as e:
            self.logger.warning(f"Failed to register network connection: {e}")

    def register_resource(self, resource: Any) -> None:
        """
        Register a resource for cleanup tracking.

        Args:
            resource: Resource object
        """
        try:
            if resource:
                self._tracked_resources.add(resource)
                self.logger.debug(f"Registered resource for cleanup: {type(resource).__name__}")
            else:
                self.logger.warning(f"Invalid resource registration: {type(resource)}")

        except Exception as e:
            self.logger.warning(f"Failed to register resource: {e}")

    def create_temp_file(self, suffix: str = "", prefix: str = "cleanup_") -> str:
        """
        Create a temporary file and register it for cleanup.

        Args:
            suffix: File suffix
            prefix: File prefix

        Returns:
            Path to the created temporary file
        """
        try:
            temp_fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix)
            os.close(temp_fd)  # Close the file descriptor, keep the path

            self.register_temp_file(temp_path)
            self.logger.debug(f"Created temporary file: {temp_path}")

            return temp_path

        except Exception as e:
            self.logger.error(f"Failed to create temporary file: {e}")
            return ""

    def get_resource_cleanup_stats(self) -> Dict[str, Any]:
        """Get resource cleanup statistics."""
        try:
            return {
                "handler_name": self.name,
                "enabled": self.enabled,
                "temp_files_count": len(self._temp_files),
                "file_handles_count": len(self._file_handles),
                "network_connections_count": len(self._network_connections),
                "tracked_resources_count": len(self._tracked_resources),
                "temp_files": self._temp_files.copy(),
            }

        except Exception as e:
            self.logger.warning(f"Failed to get resource cleanup stats: {e}")
            return {"handler_name": self.name, "error": str(e)}
