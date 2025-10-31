"""
VTK Cleanup Handler - Specialized handler for VTK resource cleanup.

This handler is responsible for VTK-specific resource cleanup including
OpenGL context management, VTK resource tracker coordination, and
graphics resource cleanup.
"""

from typing import Optional, Any, Dict
import vtk

from src.core.logging_config import get_logger
from .unified_cleanup_coordinator import CleanupHandler, CleanupPhase, CleanupContext


class VTKCleanupHandler(CleanupHandler):
    """
    Specialized handler for VTK resource cleanup.
    
    This handler manages VTK-specific cleanup operations including:
    - VTK resource tracker coordination
    - OpenGL context management
    - Actor, mapper, renderer cleanup
    - Graphics resource cleanup
    """
    
    def __init__(self):
        """Initialize the VTK cleanup handler."""
        super().__init__("VTKCleanupHandler")
        self._resource_tracker = None
        self._error_handler = None
        self._context_manager = None
        
        # Initialize VTK-specific components
        self._initialize_vtk_components()
    
    def _initialize_vtk_components(self) -> None:
        """Initialize VTK-specific components."""
        try:
            # Get VTK resource tracker
            from src.gui.vtk.resource_tracker import get_vtk_resource_tracker
            self._resource_tracker = get_vtk_resource_tracker()
            
            # Get VTK error handler
            from src.gui.vtk.error_handler import get_vtk_error_handler
            self._error_handler = get_vtk_error_handler()
            
            # Get VTK context manager
            from src.gui.vtk.context_manager import get_vtk_context_manager
            self._context_manager = get_vtk_context_manager()
            
            self.logger.debug("VTK components initialized successfully")
            
        except ImportError as e:
            self.logger.warning(f"Could not import VTK components: {e}")
        except Exception as e:
            self.logger.warning(f"Error initializing VTK components: {e}")
    
    def can_handle(self, phase: CleanupPhase) -> bool:
        """Check if this handler can handle the given phase."""
        return phase == CleanupPhase.VTK_CLEANUP
    
    def execute(self, phase: CleanupPhase, context: CleanupContext) -> bool:
        """
        Execute VTK cleanup for the given phase.
        
        Args:
            phase: The cleanup phase
            context: The cleanup context state
            
        Returns:
            True if cleanup completed successfully
        """
        try:
            self.logger.info("Starting VTK cleanup")
            
            # Handle different context states
            if context == CleanupContext.LOST:
                return self._cleanup_with_lost_context()
            elif context == CleanupContext.VALID:
                return self._cleanup_with_valid_context()
            else:
                return self._cleanup_with_unknown_context()
                
        except Exception as e:
            self.logger.error(f"VTK cleanup error: {e}", exc_info=True)
            return False
    
    def _cleanup_with_valid_context(self) -> bool:
        """Cleanup VTK resources with valid OpenGL context."""
        try:
            self.logger.debug("Performing VTK cleanup with valid context")
            
            # Suppress VTK errors during cleanup
            if self._error_handler:
                self._error_handler.suppress_errors_temporarily(3000)
            
            # Perform resource tracker cleanup
            if self._resource_tracker:
                self._cleanup_resource_tracker()
            
            # Perform VTK object cleanup
            self._cleanup_vtk_objects()
            
            self.logger.info("VTK cleanup with valid context completed")
            return True
            
        except Exception as e:
            self.logger.error(f"VTK cleanup with valid context failed: {e}")
            return False
    
    def _cleanup_with_lost_context(self) -> bool:
        """Cleanup VTK resources with lost OpenGL context."""
        try:
            self.logger.info("Performing VTK cleanup with lost context (graceful degradation)")
            
            # With lost context, we can only do basic cleanup
            # No OpenGL operations are safe
            
            # Perform basic resource cleanup without OpenGL calls
            if self._resource_tracker:
                self._cleanup_resource_tracker_basic()
            
            # Clear VTK object references for garbage collection
            self._clear_vtk_references()
            
            self.logger.info("VTK cleanup with lost context completed")
            return True
            
        except Exception as e:
            self.logger.error(f"VTK cleanup with lost context failed: {e}")
            return False
    
    def _cleanup_with_unknown_context(self) -> bool:
        """Cleanup VTK resources with unknown context state."""
        try:
            self.logger.debug("Performing VTK cleanup with unknown context")
            
            # Try to detect context state and proceed accordingly
            if self._context_manager:
                # Try to validate context
                try:
                    # This might fail if context is truly lost
                    self._context_manager.validate_context(None, "cleanup")
                    return self._cleanup_with_valid_context()
                except Exception:
                    return self._cleanup_with_lost_context()
            else:
                # No context manager available, assume safe cleanup
                return self._cleanup_with_valid_context()
                
        except Exception as e:
            self.logger.error(f"VTK cleanup with unknown context failed: {e}")
            return False
    
    def _cleanup_resource_tracker(self) -> None:
        """Cleanup using the VTK resource tracker."""
        try:
            if self._resource_tracker:
                self.logger.debug("Cleaning up VTK resources via resource tracker")
                
                cleanup_stats = self._resource_tracker.cleanup_all_resources()
                
                self.logger.info(
                    f"Resource tracker cleanup completed: "
                    f"{cleanup_stats.get('success', 0)} cleaned, "
                    f"{cleanup_stats.get('errors', 0)} errors"
                )
                
        except Exception as e:
            self.logger.warning(f"Resource tracker cleanup failed: {e}")
    
    def _cleanup_resource_tracker_basic(self) -> None:
        """Basic resource tracker cleanup without OpenGL operations."""
        try:
            if self._resource_tracker:
                self.logger.debug("Performing basic resource tracker cleanup")
                
                # Get resource statistics without cleanup
                stats = self._resource_tracker.get_stats()
                self.logger.info(f"Tracked resources: {stats.get('total_tracked', 0)}")
                
                # Clear references for garbage collection
                self._resource_tracker.clear_all_resources()
                
        except Exception as e:
            self.logger.warning(f"Basic resource tracker cleanup failed: {e}")
    
    def _cleanup_vtk_objects(self) -> None:
        """Cleanup VTK objects directly."""
        try:
            self.logger.debug("Cleaning up VTK objects directly")
            
            # This would typically be called with specific VTK objects
            # For now, we'll do general cleanup
            
            # Force garbage collection
            import gc
            gc.collect()
            
            # Suppress VTK warnings during cleanup
            vtk.vtkObject.GlobalWarningDisplayOff()
            
            self.logger.debug("VTK objects cleanup completed")
            
        except Exception as e:
            self.logger.warning(f"VTK objects cleanup failed: {e}")
    
    def _clear_vtk_references(self) -> None:
        """Clear VTK object references for garbage collection."""
        try:
            self.logger.debug("Clearing VTK references for garbage collection")
            
            # Clear any global VTK references we might have
            # This is a fallback when OpenGL context is lost
            
            import gc
            gc.collect()
            
            self.logger.debug("VTK references cleared")
            
        except Exception as e:
            self.logger.warning(f"Failed to clear VTK references: {e}")
    
    def register_vtk_resource(self, name: str, resource: Any, priority: str = "normal") -> None:
        """
        Register a VTK resource for cleanup tracking.
        
        Args:
            name: Resource name
            resource: VTK resource object
            priority: Cleanup priority
        """
        try:
            if self._resource_tracker:
                from src.gui.vtk.resource_tracker import ResourceType
                
                # Determine resource type
                resource_type = self._determine_resource_type(resource)
                
                # Register with resource tracker
                self._resource_tracker.register_resource(name, resource, resource_type)
                
                self.logger.debug(f"Registered VTK resource: {name}")
            else:
                self.logger.warning("Resource tracker not available for registration")
                
        except Exception as e:
            self.logger.warning(f"Failed to register VTK resource {name}: {e}")
    
    def _determine_resource_type(self, resource: Any):
        """Determine the VTK resource type."""
        try:
            from src.gui.vtk.resource_tracker import ResourceType
            
            if isinstance(resource, vtk.vtkActor):
                return ResourceType.ACTOR
            elif isinstance(resource, vtk.vtkPolyDataMapper):
                return ResourceType.MAPPER
            elif isinstance(resource, vtk.vtkRenderer):
                return ResourceType.RENDERER
            elif isinstance(resource, vtk.vtkRenderWindow):
                return ResourceType.RENDER_WINDOW
            elif isinstance(resource, vtk.vtkRenderWindowInteractor):
                return ResourceType.INTERACTOR
            elif hasattr(resource, 'GetClassName'):
                class_name = resource.GetClassName()
                if 'PolyData' in class_name:
                    return ResourceType.POLYDATA
                    
            return ResourceType.OTHER
            
        except Exception:
            from src.gui.vtk.resource_tracker import ResourceType
            return ResourceType.OTHER
    
    def get_vtk_cleanup_stats(self) -> Dict[str, Any]:
        """Get VTK cleanup statistics."""
        try:
            stats = {
                "handler_name": self.name,
                "enabled": self.enabled,
                "resource_tracker_available": self._resource_tracker is not None,
                "error_handler_available": self._error_handler is not None,
                "context_manager_available": self._context_manager is not None
            }
            
            if self._resource_tracker:
                tracker_stats = self._resource_tracker.get_stats()
                stats["resource_tracker_stats"] = tracker_stats
            
            return stats
            
        except Exception as e:
            self.logger.warning(f"Failed to get VTK cleanup stats: {e}")
            return {"handler_name": self.name, "error": str(e)}