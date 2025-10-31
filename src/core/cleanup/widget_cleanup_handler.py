"""
Widget Cleanup Handler - Specialized handler for Qt widget cleanup.

This handler is responsible for Qt widget cleanup including signal disconnection,
timer cleanup, and child widget cleanup.
"""

from typing import Any, Dict, Optional
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget

from src.core.logging_config import get_logger
from .unified_cleanup_coordinator import CleanupHandler, CleanupPhase, CleanupContext


class WidgetCleanupHandler(CleanupHandler):
    """
    Specialized handler for Qt widget cleanup.
    
    This handler manages Qt-specific cleanup operations including:
    - Signal disconnection
    - Timer cleanup
    - Child widget cleanup
    - Widget hierarchy cleanup
    """
    
    def __init__(self):
        """Initialize the widget cleanup handler."""
        super().__init__("WidgetCleanupHandler")
        self._main_window = None
        self._tracked_widgets = set()
    
    def can_handle(self, phase: CleanupPhase) -> bool:
        """Check if this handler can handle the given phase."""
        return phase == CleanupPhase.WIDGET_CLEANUP
    
    def execute(self, phase: CleanupPhase, context: CleanupContext) -> bool:
        """
        Execute widget cleanup for the given phase.
        
        Args:
            phase: The cleanup phase
            context: The cleanup context state
            
        Returns:
            True if cleanup completed successfully
        """
        try:
            self.logger.info("Starting widget cleanup")
            
            # Get main window from context data
            main_window = getattr(phase, '_context_data', {}).get('main_window')
            if main_window:
                self._main_window = main_window
            
            # Perform widget cleanup
            success = self._cleanup_widgets()
            
            if success:
                self.logger.info("Widget cleanup completed successfully")
            else:
                self.logger.warning("Widget cleanup completed with some issues")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Widget cleanup error: {e}", exc_info=True)
            return False
    
    def _cleanup_widgets(self) -> bool:
        """Cleanup all widgets."""
        try:
            overall_success = True
            
            # Cleanup main window if available
            if self._main_window:
                success = self._cleanup_main_window(self._main_window)
                overall_success = overall_success and success
            
            # Cleanup tracked widgets
            success = self._cleanup_tracked_widgets()
            overall_success = overall_success and success
            
            # Cleanup global widget references
            self._cleanup_global_widgets()
            
            return overall_success
            
        except Exception as e:
            self.logger.error(f"Widget cleanup failed: {e}")
            return False
    
    def _cleanup_main_window(self, main_window) -> bool:
        """Cleanup the main window and its components."""
        try:
            self.logger.debug("Cleaning up main window")
            
            success = True
            
            # Cleanup viewer widget if it exists
            if hasattr(main_window, 'viewer_widget') and main_window.viewer_widget:
                success = self._cleanup_viewer_widget(main_window.viewer_widget) and success
            
            # Cleanup metadata editor if it exists
            if hasattr(main_window, 'metadata_editor') and main_window.metadata_editor:
                success = self._cleanup_metadata_editor(main_window.metadata_editor) and success
            
            # Cleanup model library if it exists
            if hasattr(main_window, 'model_library_widget') and main_window.model_library_widget:
                success = self._cleanup_model_library(main_window.model_library_widget) and success
            
            # Cleanup other window components
            success = self._cleanup_window_components(main_window) and success
            
            return success
            
        except Exception as e:
            self.logger.error(f"Main window cleanup failed: {e}")
            return False
    
    def _cleanup_viewer_widget(self, viewer_widget) -> bool:
        """Cleanup the 3D viewer widget."""
        try:
            self.logger.debug("Cleaning up 3D viewer widget")
            
            if hasattr(viewer_widget, 'cleanup'):
                viewer_widget.cleanup()
                self.logger.debug("3D viewer widget cleanup called")
            else:
                self.logger.warning("3D viewer widget has no cleanup method")
            
            return True
            
        except Exception as e:
            self.logger.error(f"3D viewer widget cleanup failed: {e}")
            return False
    
    def _cleanup_metadata_editor(self, metadata_editor) -> bool:
        """Cleanup the metadata editor."""
        try:
            self.logger.debug("Cleaning up metadata editor")
            
            if hasattr(metadata_editor, 'cleanup'):
                metadata_editor.cleanup()
                self.logger.debug("Metadata editor cleanup called")
            else:
                self.logger.warning("Metadata editor has no cleanup method")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Metadata editor cleanup failed: {e}")
            return False
    
    def _cleanup_model_library(self, model_library) -> bool:
        """Cleanup the model library widget."""
        try:
            self.logger.debug("Cleaning up model library widget")
            
            if hasattr(model_library, 'cleanup'):
                model_library.cleanup()
                self.logger.debug("Model library cleanup called")
            else:
                self.logger.warning("Model library has no cleanup method")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Model library cleanup failed: {e}")
            return False
    
    def _cleanup_window_components(self, main_window) -> bool:
        """Cleanup other window components."""
        try:
            self.logger.debug("Cleaning up window components")
            
            success = True
            
            # Cleanup snapping system if it exists
            if hasattr(main_window, 'snapping_system') and main_window.snapping_system:
                success = self._cleanup_snapping_system(main_window.snapping_system) and success
            
            # Cleanup event coordinator if it exists
            if hasattr(main_window, 'event_coordinator') and main_window.event_coordinator:
                success = self._cleanup_event_coordinator(main_window.event_coordinator) and success
            
            # Cleanup any timers
            success = self._cleanup_timers(main_window) and success
            
            # Disconnect signals
            success = self._disconnect_signals(main_window) and success
            
            return success
            
        except Exception as e:
            self.logger.error(f"Window components cleanup failed: {e}")
            return False
    
    def _cleanup_snapping_system(self, snapping_system) -> bool:
        """Cleanup the snapping system."""
        try:
            self.logger.debug("Cleaning up snapping system")
            
            if hasattr(snapping_system, 'cleanup'):
                snapping_system.cleanup()
                self.logger.debug("Snapping system cleanup called")
            else:
                self.logger.warning("Snapping system has no cleanup method")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Snapping system cleanup failed: {e}")
            return False
    
    def _cleanup_event_coordinator(self, event_coordinator) -> bool:
        """Cleanup the event coordinator."""
        try:
            self.logger.debug("Cleaning up event coordinator")
            
            if hasattr(event_coordinator, 'cleanup'):
                event_coordinator.cleanup()
                self.logger.debug("Event coordinator cleanup called")
            else:
                self.logger.warning("Event coordinator has no cleanup method")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Event coordinator cleanup failed: {e}")
            return False
    
    def _cleanup_timers(self, widget) -> bool:
        """Cleanup timers associated with a widget."""
        try:
            self.logger.debug("Cleaning up timers")
            
            # Find and cleanup any QTimer objects
            timers_cleaned = 0
            
            def cleanup_timer_recursive(obj):
                nonlocal timers_cleaned
                if isinstance(obj, QObject):
                    # Get all children
                    for child in obj.findChildren(QObject):
                        if hasattr(child, 'stop') and hasattr(child, 'isActive'):
                            try:
                                if child.isActive():
                                    child.stop()
                                    timers_cleaned += 1
                            except Exception:
                                pass  # Timer might already be stopped
                        cleanup_timer_recursive(child)
            
            cleanup_timer_recursive(widget)
            
            self.logger.debug(f"Cleaned up {timers_cleaned} timers")
            return True
            
        except Exception as e:
            self.logger.error(f"Timer cleanup failed: {e}")
            return False
    
    def _disconnect_signals(self, widget) -> bool:
        """Disconnect signals associated with a widget."""
        try:
            self.logger.debug("Disconnecting signals")
            
            # Disconnect signals from the widget and its children
            def disconnect_signals_recursive(obj):
                if isinstance(obj, QObject):
                    try:
                        # Disconnect all signals
                        obj.disconnect()
                    except Exception:
                        pass  # Object might not have signals or already disconnected
                    
                    # Recursively disconnect signals from children
                    for child in obj.findChildren(QObject):
                        disconnect_signals_recursive(child)
            
            disconnect_signals_recursive(widget)
            
            self.logger.debug("Signals disconnected")
            return True
            
        except Exception as e:
            self.logger.error(f"Signal disconnection failed: {e}")
            return False
    
    def _cleanup_tracked_widgets(self) -> bool:
        """Cleanup tracked widgets."""
        try:
            self.logger.debug(f"Cleaning up {len(self._tracked_widgets)} tracked widgets")
            
            success = True
            for widget in self._tracked_widgets.copy():
                try:
                    if hasattr(widget, 'cleanup'):
                        widget.cleanup()
                    self._tracked_widgets.discard(widget)
                except Exception as e:
                    self.logger.warning(f"Failed to cleanup tracked widget: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            self.logger.error(f"Tracked widgets cleanup failed: {e}")
            return False
    
    def _cleanup_global_widgets(self) -> bool:
        """Cleanup global widget references."""
        try:
            self.logger.debug("Cleaning up global widget references")
            
            # Clear any global references that might prevent garbage collection
            # This is a fallback cleanup
            
            import gc
            gc.collect()
            
            self.logger.debug("Global widget references cleaned")
            return True
            
        except Exception as e:
            self.logger.error(f"Global widget cleanup failed: {e}")
            return False
    
    def register_widget(self, widget) -> None:
        """
        Register a widget for cleanup tracking.
        
        Args:
            widget: Widget to register for cleanup
        """
        try:
            if widget and isinstance(widget, QWidget):
                self._tracked_widgets.add(widget)
                self.logger.debug(f"Registered widget for cleanup: {type(widget).__name__}")
            else:
                self.logger.warning(f"Invalid widget registration: {type(widget)}")
                
        except Exception as e:
            self.logger.warning(f"Failed to register widget: {e}")
    
    def unregister_widget(self, widget) -> bool:
        """
        Unregister a widget from cleanup tracking.
        
        Args:
            widget: Widget to unregister
            
        Returns:
            True if widget was unregistered
        """
        try:
            if widget in self._tracked_widgets:
                self._tracked_widgets.discard(widget)
                self.logger.debug(f"Unregistered widget from cleanup: {type(widget).__name__}")
                return True
            return False
            
        except Exception as e:
            self.logger.warning(f"Failed to unregister widget: {e}")
            return False
    
    def get_widget_cleanup_stats(self) -> Dict[str, Any]:
        """Get widget cleanup statistics."""
        try:
            return {
                "handler_name": self.name,
                "enabled": self.enabled,
                "main_window_available": self._main_window is not None,
                "tracked_widgets_count": len(self._tracked_widgets),
                "tracked_widgets": [type(w).__name__ for w in self._tracked_widgets]
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to get widget cleanup stats: {e}")
            return {"handler_name": self.name, "error": str(e)}