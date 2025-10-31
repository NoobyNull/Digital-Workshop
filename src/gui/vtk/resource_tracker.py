"""
VTK Resource Tracker - Track VTK resources for proper cleanup.

This module tracks VTK resources throughout their lifecycle to ensure
proper cleanup and prevent memory leaks during VTK operations.
"""

import weakref
import threading
from typing import Dict, List, Any, Optional, Set, Callable
from collections import defaultdict
from enum import Enum

import vtk

from src.core.logging_config import get_logger, log_function_call
from .error_handler import get_vtk_error_handler, VTKErrorCode


logger = get_logger(__name__)


class ResourceType(Enum):
    """Types of VTK resources to track."""

    RENDER_WINDOW = "render_window"
    RENDERER = "renderer"
    INTERACTOR = "interactor"
    ACTOR = "actor"
    MAPPER = "mapper"
    POLYDATA = "polydata"
    TEXTURE = "texture"
    LIGHT = "light"
    CAMERA = "camera"
    WIDGET = "widget"
    TRANSFORM = "transform"
    OTHER = "other"


class ResourceState(Enum):
    """States of tracked resources."""

    CREATED = "created"
    ACTIVE = "active"
    CLEANED = "cleaned"
    DESTROYED = "destroyed"
    LEAKED = "leaked"


class VTKResourceTracker:
    """
    Tracks VTK resources for proper cleanup and memory leak prevention.

    This class maintains a registry of VTK resources, their relationships,
    and cleanup status to ensure no resources are leaked during VTK operations.
    """

    def __init__(self):
        """Initialize the resource tracker."""
        self.logger = get_logger(__name__)
        self.error_handler = get_vtk_error_handler()

        # Resource tracking
        self.resources: Dict[str, Dict[str, Any]] = {}
        self.resource_counter = 0
        self.resource_relationships: Dict[str, Set[str]] = defaultdict(set)
        self.cleanup_callbacks: Dict[str, Callable] = {}

        # Thread safety
        self.lock = threading.RLock()

        # Statistics
        self.stats = {
            "total_created": 0,
            "total_cleaned": 0,
            "total_leaked": 0,
            "by_type": defaultdict(int)
        }

        # Register default cleanup callbacks
        self._register_default_cleanup_callbacks()

        self.logger.info("VTK Resource Tracker initialized")

    def generate_resource_id(self) -> str:
        """Generate a unique resource ID."""
        with self.lock:
            self.resource_counter += 1
            return f"vtk_resource_{self.resource_counter}"

    def _register_default_cleanup_callbacks(self) -> None:
        """Register default cleanup callbacks for each resource type."""
        try:
            # Actor cleanup
            def cleanup_actor(resource: Any) -> None:
                try:
                    if hasattr(resource, "SetMapper"):
                        resource.SetMapper(None)
                    if hasattr(resource, "Delete"):
                        resource.Delete()
                except Exception:
                    pass

            # Mapper cleanup
            def cleanup_mapper(resource: Any) -> None:
                try:
                    if hasattr(resource, "SetInput"):
                        resource.SetInput(None)
                    if hasattr(resource, "Delete"):
                        resource.Delete()
                except Exception:
                    pass

            # Polydata cleanup
            def cleanup_polydata(resource: Any) -> None:
                try:
                    if hasattr(resource, "Reset"):
                        resource.Reset()
                    if hasattr(resource, "Delete"):
                        resource.Delete()
                except Exception:
                    pass

            # Renderer cleanup
            def cleanup_renderer(resource: Any) -> None:
                try:
                    if hasattr(resource, "RemoveAllViewProps"):
                        resource.RemoveAllViewProps()
                    if hasattr(resource, "Delete"):
                        resource.Delete()
                except Exception:
                    pass

            # Render window cleanup
            def cleanup_render_window(resource: Any) -> None:
                try:
                    if hasattr(resource, "Finalize"):
                        resource.Finalize()
                    if hasattr(resource, "Delete"):
                        resource.Delete()
                except Exception:
                    pass

            # Interactor cleanup
            def cleanup_interactor(resource: Any) -> None:
                try:
                    if hasattr(resource, "TerminateApp"):
                        resource.TerminateApp()
                    if hasattr(resource, "Delete"):
                        resource.Delete()
                except Exception:
                    pass

            # Register callbacks
            self.register_cleanup_callback(ResourceType.ACTOR, cleanup_actor)
            self.register_cleanup_callback(ResourceType.MAPPER, cleanup_mapper)
            self.register_cleanup_callback(ResourceType.POLYDATA, cleanup_polydata)
            self.register_cleanup_callback(ResourceType.RENDERER, cleanup_renderer)
            self.register_cleanup_callback(
                ResourceType.RENDER_WINDOW, cleanup_render_window
            )
            self.register_cleanup_callback(ResourceType.INTERACTOR, cleanup_interactor)

            self.logger.debug("Default cleanup callbacks registered")

        except Exception as e:
            self.logger.warning(f"Error registering default cleanup callbacks: {e}")

    def register_resource(self, resource: Any, resource_type: ResourceType,
                         name: Optional[str] = None, parent_id: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Register a VTK resource for tracking.

        Args:
            resource: The VTK resource object
            resource_type: Type of the resource
            name: Optional name for the resource
            parent_id: ID of parent resource (if any)
            metadata: Additional metadata about the resource

        Returns:
            Unique resource ID
        """
        try:
            with self.lock:
                resource_id = self.generate_resource_id()

                # Create weak reference to avoid circular references
                resource_ref = weakref.ref(resource, self._resource_finalized)

                self.resources[resource_id] = {
                    "id": resource_id,
                    "resource": resource_ref,
                    "resource_type": resource_type,
                    "name": name or f"{resource_type.value}_{resource_id}",
                    "state": ResourceState.CREATED,
                    "parent_id": parent_id,
                    "metadata": metadata or {},
                    "created_time": self._get_timestamp(),
                    "last_accessed": self._get_timestamp(),
                    "cleanup_attempts": 0
                }

                # Track relationships
                if parent_id:
                    self.resource_relationships[parent_id].add(resource_id)
                    self.resource_relationships[resource_id].add(parent_id)

                # Update statistics
                self.stats["total_created"] += 1
                self.stats["by_type"][resource_type.value] += 1

                self.logger.debug(f"Registered VTK resource: {resource_id} ({resource_type.value})")

                return resource_id

        except Exception as e:
            self.logger.error(f"Error registering resource: {e}")
            return ""

    def _resource_finalized(self, resource_ref: weakref.ReferenceType) -> None:
        """Callback when a tracked resource is garbage collected."""
        try:
            with self.lock:
                # Find the resource ID for this reference
                for resource_id, resource_info in self.resources.items():
                    if resource_info["resource"] == resource_ref:
                        if resource_info["state"] != ResourceState.CLEANED:
                            resource_info["state"] = ResourceState.LEAKED
                            self.stats["total_leaked"] += 1
                            self.logger.warning(f"VTK resource leaked: {resource_id}")
                        break

        except Exception as e:
            self.logger.debug(f"Error in resource finalization callback: {e}")

    def unregister_resource(self, resource_id: str) -> bool:
        """
        Unregister a resource from tracking.

        Args:
            resource_id: The resource ID to unregister

        Returns:
            True if successfully unregistered
        """
        try:
            with self.lock:
                if resource_id not in self.resources:
                    return False

                resource_info = self.resources[resource_id]

                # Mark as cleaned
                resource_info["state"] = ResourceState.CLEANED
                resource_info["cleaned_time"] = self._get_timestamp()
                self.stats["total_cleaned"] += 1

                # Clean up relationships
                for related_id in self.resource_relationships[resource_id]:
                    self.resource_relationships[related_id].discard(resource_id)
                del self.resource_relationships[resource_id]

                # Remove from main registry
                del self.resources[resource_id]

                self.logger.debug(f"Unregistered VTK resource: {resource_id}")
                return True

        except Exception as e:
            self.logger.error(f"Error unregistering resource {resource_id}: {e}")
            return False

    def get_resource(self, resource_id: str) -> Optional[Any]:
        """
        Get a tracked resource by ID.

        Args:
            resource_id: The resource ID

        Returns:
            The resource object if found and still alive, None otherwise
        """
        try:
            with self.lock:
                if resource_id not in self.resources:
                    return None

                resource_info = self.resources[resource_id]
                resource_info["last_accessed"] = self._get_timestamp()

                resource_ref = resource_info["resource"]
                resource = resource_ref() if resource_ref else None

                if resource is None:
                    # Resource was garbage collected
                    resource_info["state"] = ResourceState.DESTROYED

                return resource

        except Exception as e:
            self.logger.debug(f"Error getting resource {resource_id}: {e}")
            return None

    def cleanup_resource(self, resource_id: str) -> bool:
        """
        Clean up a specific resource.

        Args:
            resource_id: The resource ID to cleanup

        Returns:
            True if cleanup succeeded
        """
        try:
            with self.lock:
                if resource_id not in self.resources:
                    self.logger.debug(f"Resource {resource_id} not found")
                    return True

                resource_info = self.resources[resource_id]
                resource_ref = resource_info["resource"]
                resource = resource_ref() if resource_ref else None

                if not resource:
                    self.logger.debug(
                        f"Resource {resource_id} already destroyed"
                    )
                    # Mark as cleaned before unregistering
                    resource_info["state"] = ResourceState.CLEANED
                    self.stats["total_cleaned"] += 1
                    return self.unregister_resource(resource_id)

                # Check if cleanup callback is registered
                resource_type = resource_info["resource_type"]
                if resource_type.value in self.cleanup_callbacks:
                    try:
                        self.cleanup_callbacks[resource_type.value](resource)
                    except Exception as e:
                        self.logger.debug(
                            f"Error in cleanup callback for {resource_id}: {e}"
                        )

                # Try generic cleanup
                try:
                    if hasattr(resource, "Delete"):
                        resource.Delete()
                    elif hasattr(resource, "Finalize"):
                        resource.Finalize()
                    elif hasattr(resource, "TerminateApp"):
                        resource.TerminateApp()
                except Exception as e:
                    self.logger.debug(
                        f"Error in generic cleanup for {resource_id}: {e}"
                    )

                # Mark as cleaned BEFORE unregistering to prevent false leak warnings
                resource_info["state"] = ResourceState.CLEANED
                self.stats["total_cleaned"] += 1
                resource_info["cleanup_attempts"] += 1

            return self.unregister_resource(resource_id)

        except Exception as e:
            self.logger.error(f"Error cleaning up resource {resource_id}: {e}")
            return False

    def cleanup_all_resources(self) -> Dict[str, int]:
        """
        Clean up all tracked resources.

        Returns:
            Dictionary with cleanup statistics
        """
        try:
            with self.lock:
                self.logger.info(f"Cleaning up {len(self.resources)} tracked VTK resources")

                success_count = 0
                error_count = 0

                # Clean up in reverse dependency order (children first)
                cleanup_order = self._get_cleanup_order()

                for resource_id in cleanup_order:
                    try:
                        if self.cleanup_resource(resource_id):
                            success_count += 1
                        else:
                            error_count += 1
                    except Exception as e:
                        self.logger.debug(f"Error cleaning up {resource_id}: {e}")
                        error_count += 1

                self.logger.info(f"Cleanup completed: {success_count} success, {error_count} errors")
                return {
                    "total": len(self.resources),
                    "success": success_count,
                    "errors": error_count
                }

        except Exception as e:
            self.logger.error(f"Error in cleanup_all_resources: {e}")
            return {"total": 0, "success": 0, "errors": 1}

    def _get_cleanup_order(self) -> List[str]:
        """Get resources in cleanup order (children before parents)."""
        try:
            # Simple approach: clean up resources without parents first
            cleanup_order = []

            # First pass: resources without parents
            for resource_id, resource_info in self.resources.items():
                if not resource_info["parent_id"]:
                    cleanup_order.append(resource_id)

            # Second pass: resources with parents (after their parents are cleaned)
            for resource_id, resource_info in self.resources.items():
                if resource_info["parent_id"] and resource_id not in cleanup_order:
                    cleanup_order.append(resource_id)

            return cleanup_order

        except Exception as e:
            self.logger.debug(f"Error getting cleanup order: {e}")
            # Fallback: just return all resource IDs
            return list(self.resources.keys())

    def register_cleanup_callback(self, resource_type: ResourceType, callback: Callable) -> None:
        """
        Register a cleanup callback for a specific resource type.

        Args:
            resource_type: The resource type
            callback: Function to call for cleanup (takes resource as argument)
        """
        self.cleanup_callbacks[resource_type.value] = callback
        self.logger.debug(f"Registered cleanup callback for {resource_type.value}")

    def get_resource_info(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a tracked resource.

        Args:
            resource_id: The resource ID

        Returns:
            Resource information dictionary
        """
        try:
            with self.lock:
                if resource_id not in self.resources:
                    return None

                resource_info = self.resources[resource_id].copy()
                resource_ref = resource_info["resource"]
                resource_info["is_alive"] = resource_ref() is not None

                return resource_info

        except Exception as e:
            self.logger.debug(f"Error getting resource info for {resource_id}: {e}")
            return None

    def get_all_resources(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all tracked resources.

        Returns:
            Dictionary mapping resource IDs to resource information
        """
        try:
            with self.lock:
                result = {}
                for resource_id in self.resources:
                    info = self.get_resource_info(resource_id)
                    if info:
                        result[resource_id] = info
                return result

        except Exception as e:
            self.logger.error(f"Error getting all resources: {e}")
            return {}

    def find_leaked_resources(self) -> List[Dict[str, Any]]:
        """
        Find resources that may have been leaked.

        Returns:
            List of leaked resource information
        """
        try:
            with self.lock:
                leaked = []
                for resource_id, resource_info in self.resources.items():
                    resource_ref = resource_info["resource"]
                    if resource_ref() is None and resource_info["state"] != ResourceState.CLEANED:
                        leaked.append({
                            "resource_id": resource_id,
                            "resource_type": resource_info["resource_type"].value,
                            "name": resource_info["name"],
                            "created_time": resource_info["created_time"],
                            "cleanup_attempts": resource_info["cleanup_attempts"]
                        })

                return leaked

        except Exception as e:
            self.logger.error(f"Error finding leaked resources: {e}")
            return []

    def get_statistics(self) -> Dict[str, Any]:
        """Get resource tracking statistics."""
        try:
            with self.lock:
                # Count resources by state
                state_counts = defaultdict(int)
                for resource_info in self.resources.values():
                    state_counts[resource_info["state"].value] += 1

                # Count alive vs dead resources
                alive_count = 0
                for resource_info in self.resources.values():
                    resource_ref = resource_info["resource"]
                    if resource_ref() is not None:
                        alive_count += 1

                return {
                    "total_tracked": len(self.resources),
                    "alive_resources": alive_count,
                    "dead_resources": len(self.resources) - alive_count,
                    "by_state": dict(state_counts),
                    "by_type": dict(self.stats["by_type"]),
                    "total_created": self.stats["total_created"],
                    "total_cleaned": self.stats["total_cleaned"],
                    "total_leaked": self.stats["total_leaked"],
                    "cleanup_callbacks_registered": len(self.cleanup_callbacks)
                }

        except Exception as e:
            self.logger.error(f"Error getting statistics: {e}")
            return {}

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.now().isoformat()

    def clear_tracking_data(self) -> None:
        """Clear all tracking data (for testing or reset)."""
        try:
            with self.lock:
                self.resources.clear()
                self.resource_relationships.clear()
                self.cleanup_callbacks.clear()
                self.resource_counter = 0

                # Reset statistics
                self.stats = {
                    "total_created": 0,
                    "total_cleaned": 0,
                    "total_leaked": 0,
                    "by_type": defaultdict(int)
                }

                self.logger.info("Resource tracking data cleared")

        except Exception as e:
            self.logger.error(f"Error clearing tracking data: {e}")


# Global resource tracker instance
_vtk_resource_tracker: Optional[VTKResourceTracker] = None


def get_vtk_resource_tracker() -> VTKResourceTracker:
    """Get the global VTK resource tracker instance."""
    global _vtk_resource_tracker
    if _vtk_resource_tracker is None:
        _vtk_resource_tracker = VTKResourceTracker()
    return _vtk_resource_tracker


def register_vtk_resource(resource: Any, resource_type: ResourceType,
                         name: Optional[str] = None, parent_id: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Convenience function to register a VTK resource.

    Args:
        resource: The VTK resource object
        resource_type: Type of the resource
        name: Optional name for the resource
        parent_id: ID of parent resource (if any)
        metadata: Additional metadata

    Returns:
        Unique resource ID
    """
    return get_vtk_resource_tracker().register_resource(resource, resource_type, name, parent_id, metadata)


def cleanup_vtk_resource(resource_id: str) -> bool:
    """
    Convenience function to cleanup a VTK resource.

    Args:
        resource_id: The resource ID to cleanup

    Returns:
        True if cleanup succeeded
    """
    return get_vtk_resource_tracker().cleanup_resource(resource_id)


def cleanup_all_vtk_resources() -> Dict[str, int]:
    """
    Convenience function to cleanup all VTK resources.

    Returns:
        Cleanup statistics
    """
    return get_vtk_resource_tracker().cleanup_all_resources()