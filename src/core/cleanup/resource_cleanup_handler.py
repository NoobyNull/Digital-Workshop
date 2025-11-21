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

    def __init__(self) -> None:
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

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Resource cleanup error: %s", e, exc_info=True)
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

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Resource cleanup failed: %s", e)
            return False

    def _cleanup_temp_files(self) -> bool:
        """Cleanup temporary files."""
        try:
            self.logger.debug("Cleaning up %s temporary files", len(self._temp_files))

            files_cleaned = 0
            for temp_file in self._temp_files.copy():
                try:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                        files_cleaned += 1
                        self.logger.debug("Removed temporary file: %s", temp_file)
                    self._temp_files.remove(temp_file)
                except (
                    OSError,
                    IOError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                ) as e:
                    self.logger.warning(
                        "Failed to remove temporary file %s: {e}", temp_file
                    )

            self.logger.debug("Cleaned up %s temporary files", files_cleaned)
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Temporary files cleanup failed: %s", e)
            return False

    def _cleanup_file_handles(self) -> bool:
        """Cleanup file handles."""
        try:
            self.logger.debug("Cleaning up %s file handles", len(self._file_handles))

            handles_cleaned = 0
            for handle in self._file_handles.copy():
                try:
                    if hasattr(handle, "close") and not handle.closed:
                        handle.close()
                        handles_cleaned += 1
                        self.logger.debug("Closed file handle")
                    self._file_handles.remove(handle)
                except (
                    OSError,
                    IOError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                ) as e:
                    self.logger.warning("Failed to close file handle: %s", e)

            self.logger.debug("Cleaned up %s file handles", handles_cleaned)
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("File handles cleanup failed: %s", e)
            return False

    def _cleanup_network_connections(self) -> bool:
        """Cleanup network connections."""
        try:
            self.logger.debug(
                "Cleaning up %s network connections", len(self._network_connections)
            )

            connections_cleaned = 0
            for connection in self._network_connections.copy():
                try:
                    if hasattr(connection, "close"):
                        connection.close()
                        connections_cleaned += 1
                        self.logger.debug("Closed network connection")
                    self._network_connections.remove(connection)
                except (
                    OSError,
                    IOError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                ) as e:
                    self.logger.warning("Failed to close network connection: %s", e)

            self.logger.debug("Cleaned up %s network connections", connections_cleaned)
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Network connections cleanup failed: %s", e)
            return False

    def _cleanup_tracked_resources(self) -> bool:
        """Cleanup tracked resources."""
        try:
            self.logger.debug(
                "Cleaning up %s tracked resources", len(self._tracked_resources)
            )

            resources_cleaned = 0
            for resource in list(self._tracked_resources):
                try:
                    if hasattr(resource, "cleanup"):
                        resource.cleanup()
                        resources_cleaned += 1
                        self.logger.debug(
                            "Cleaned up tracked resource: %s", type(resource).__name__
                        )
                except (
                    OSError,
                    IOError,
                    ValueError,
                    TypeError,
                    KeyError,
                    AttributeError,
                ) as e:
                    self.logger.warning(
                        f"Failed to cleanup tracked resource {type(resource).__name__}: {e}"
                    )

            # Clear the tracked resources set
            self._tracked_resources.clear()

            self.logger.debug("Cleaned up %s tracked resources", resources_cleaned)
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Tracked resources cleanup failed: %s", e)
            return False

    def _force_garbage_collection(self) -> bool:
        """Force garbage collection to clean up unreferenced objects."""
        try:
            self.logger.debug("Forcing garbage collection")

            # Run garbage collection multiple times to ensure cleanup
            collected = gc.collect()
            collected += gc.collect()
            collected += gc.collect()

            self.logger.debug("Garbage collection freed %s objects", collected)
            return True

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Garbage collection failed: %s", e)
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
                self.logger.debug(
                    "Registered temporary file for cleanup: %s", file_path
                )
            else:
                self.logger.warning(
                    "Invalid temporary file registration: %s", file_path
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to register temporary file %s: {e}", file_path)

    def register_file_handle(self, handle) -> None:
        """
        Register a file handle for cleanup.

        Args:
            handle: File handle object
        """
        try:
            if handle and hasattr(handle, "close"):
                self._file_handles.append(handle)
                self.logger.debug(
                    "Registered file handle for cleanup: %s", type(handle).__name__
                )
            else:
                self.logger.warning(
                    "Invalid file handle registration: %s", type(handle)
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to register file handle: %s", e)

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
                self.logger.warning(
                    "Invalid network connection registration: %s", type(connection)
                )

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to register network connection: %s", e)

    def register_resource(self, resource: Any) -> None:
        """
        Register a resource for cleanup tracking.

        Args:
            resource: Resource object
        """
        try:
            if resource:
                self._tracked_resources.add(resource)
                self.logger.debug(
                    "Registered resource for cleanup: %s", type(resource).__name__
                )
            else:
                self.logger.warning("Invalid resource registration: %s", type(resource))

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to register resource: %s", e)

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
            self.logger.debug("Created temporary file: %s", temp_path)

            return temp_path

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to create temporary file: %s", e)
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

        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.warning("Failed to get resource cleanup stats: %s", e)
            return {"handler_name": self.name, "error": str(e)}
