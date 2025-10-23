"""
Event Processor Module

This module provides efficient event handling for the widget snapping system without conflicts.
It manages mouse events, debouncing, and coordination between different event sources while
maintaining high performance and avoiding event filter conflicts.

Classes:
    EventProcessor: Efficient event handling without conflicts
    EventDebouncer: Debounces rapid events for performance
    SnapEvent: Represents a snapping-related event
    EventFilter: High-performance event filtering
"""

import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Deque
from weakref import WeakKeyDictionary

from PySide6.QtCore import QEvent, QPointF, QTimer, QObject, QPoint
from PySide6.QtWidgets import QWidget, QMainWindow, QDockWidget

from src.core.logging_config import get_logger
from src.gui.layout.snapping.coordinate_manager import CoordinateManager, CoordinateSystem
from src.gui.layout.snapping.snap_engine import SnapEngine, SnapResult
from src.gui.layout.snapping.snap_configuration import SnapConfiguration


class EventType(Enum):
    """
    Types of events handled by the snapping system.

    Defines different categories of events that can trigger snapping behavior.
    """
    MOUSE_PRESS = "mouse_press"
    MOUSE_MOVE = "mouse_move"
    MOUSE_RELEASE = "mouse_release"
    MOUSE_DOUBLE_CLICK = "mouse_double_click"
    WIDGET_RESIZE = "widget_resize"
    WIDGET_MOVE = "widget_move"
    LAYOUT_CHANGE = "layout_change"
    SNAP_REQUEST = "snap_request"


@dataclass
class SnapEvent:
    """
    Represents a snapping-related event.

    Contains event data and metadata for processing by the snapping system.

    Attributes:
        event_type: Type of event
        position: Event position in unified coordinates
        source_widget: Widget that generated the event
        target_widget: Widget being snapped (if applicable)
        timestamp: When the event occurred
        original_event: Original Qt event object
        metadata: Additional event-specific data
    """
    event_type: EventType
    position: QPointF
    source_widget: Optional[QWidget]
    target_widget: Optional[QWidget]
    timestamp: float
    original_event: Optional[QEvent] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate snap event after initialization."""
        if self.timestamp < 0:
            raise ValueError(f"Timestamp must be non-negative, got {self.timestamp}")


class EventDebouncer:
    """
    Debounces rapid events to maintain performance.

    Prevents event flooding while ensuring responsive interaction.
    Uses time-based and movement-based debouncing strategies.
    """

    def __init__(self, time_threshold_ms: int = 16, movement_threshold: int = 2):
        """
        Initialize the event debouncer.

        Args:
            time_threshold_ms: Minimum time between events (16ms ≈ 60 FPS)
            movement_threshold: Minimum movement before processing move events
        """
        self.time_threshold_ms = time_threshold_ms
        self.movement_threshold = movement_threshold
        self._last_event_time: float = 0.0
        self._last_position: Optional[QPointF] = None
        self._pending_events: Deque[SnapEvent] = deque()

    def should_process_event(self, event: SnapEvent) -> bool:
        """
        Check if an event should be processed immediately.

        Args:
            event: Event to check

        Returns:
            True if event should be processed, False if should be debounced
        """
        current_time = time.time()

        # Always process non-movement events immediately
        if event.event_type != EventType.MOUSE_MOVE:
            return True

        # Check time threshold
        if (current_time - self._last_event_time) * 1000 < self.time_threshold_ms:
            return False

        # Check movement threshold
        if self._last_position is not None:
            distance = abs(event.position.x() - self._last_position.x()) + abs(event.position.y() - self._last_position.y())
            if distance < self.movement_threshold:
                return False

        # Update tracking
        self._last_event_time = current_time
        self._last_position = QPointF(event.position)

        return True

    def add_pending_event(self, event: SnapEvent) -> None:
        """
        Add an event to the pending queue.

        Args:
            event: Event to add to pending queue
        """
        self._pending_events.append(event)

        # Limit queue size to prevent memory issues
        if len(self._pending_events) > 50:
            self._pending_events.popleft()

    def get_pending_events(self) -> List[SnapEvent]:
        """
        Get all pending events.

        Returns:
            List of pending events
        """
        events = list(self._pending_events)
        self._pending_events.clear()
        return events

    def reset(self) -> None:
        """Reset the debouncer state."""
        self._last_event_time = 0.0
        self._last_position = None
        self._pending_events.clear()


class EventFilter(QObject):
    """
    High-performance event filtering for snapping operations.

    Filters Qt events and converts them to SnapEvents for processing.
    Optimized to avoid conflicts with other event filters.
    """

    def __init__(self, event_processor: 'EventProcessor'):
        """
        Initialize the event filter.

        Args:
            event_processor: Parent event processor
        """
        super().__init__()
        self.event_processor = event_processor
        self.logger = get_logger(__name__)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """
        Filter events for snapping processing.

        Args:
            obj: Object that received the event
            event: Qt event

        Returns:
            True if event was handled (stop propagation), False otherwise
        """
        try:
            # Only process events for widgets we're interested in
            if not isinstance(obj, QWidget):
                return False

            # Convert Qt event to SnapEvent
            snap_event = self._convert_qt_event(obj, event)
            if snap_event is None:
                return False

            # Process the event
            self.event_processor.process_event(snap_event)

            # Don't block the original event
            return False

        except Exception as e:
            self.logger.error(f"Error in event filter: {e}")
            return False

    def _convert_qt_event(self, widget: QWidget, event: QEvent) -> Optional[SnapEvent]:
        """
        Convert a Qt event to a SnapEvent.

        Args:
            widget: Widget that received the event
            event: Qt event

        Returns:
            SnapEvent or None if event type is not supported
        """
        try:
            event_type = event.type()

            # Map Qt event types to our event types
            if event_type == QEvent.MouseButtonPress:
                return self._create_mouse_event(EventType.MOUSE_PRESS, widget, event)
            elif event_type == QEvent.MouseMove:
                return self._create_mouse_event(EventType.MOUSE_MOVE, widget, event)
            elif event_type == QEvent.MouseButtonRelease:
                return self._create_mouse_event(EventType.MOUSE_RELEASE, widget, event)
            elif event_type == QEvent.MouseButtonDblClick:
                return self._create_mouse_event(EventType.MOUSE_DOUBLE_CLICK, widget, event)
            elif event_type == QEvent.Resize:
                return self._create_resize_event(widget, event)
            elif event_type == QEvent.Move:
                return self._create_move_event(widget, event)

            return None

        except Exception as e:
            self.logger.error(f"Failed to convert Qt event: {e}")
            return None

    def _create_mouse_event(self, event_type: EventType, widget: QWidget, event: QEvent) -> Optional[SnapEvent]:
        """Create a mouse-related SnapEvent."""
        try:
            # Get mouse position in global coordinates
            global_pos = event.pos() if hasattr(event, 'pos') else QPoint(0, 0)

            # Convert to unified coordinates
            unified_pos = self.event_processor.coordinate_manager.transform_point(
                QPointF(global_pos),
                CoordinateSystem.SCREEN,
                CoordinateSystem.UNIFIED,
                widget
            ).point

            return SnapEvent(
                event_type=event_type,
                position=unified_pos,
                source_widget=widget,
                target_widget=self._find_target_widget(widget),
                timestamp=time.time(),
                original_event=event,
                metadata={
                    "global_position": global_pos,
                    "mouse_buttons": int(event.buttons()) if hasattr(event, 'buttons') else 0,
                    "keyboard_modifiers": int(event.modifiers()) if hasattr(event, 'modifiers') else 0
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to create mouse event: {e}")
            return None

    def _create_resize_event(self, widget: QWidget, event: QEvent) -> Optional[SnapEvent]:
        """Create a resize SnapEvent."""
        try:
            # Get widget center position
            center_pos = QPointF(widget.rect().center())

            # Convert to unified coordinates
            unified_pos = self.event_processor.coordinate_manager.transform_point(
                center_pos,
                CoordinateSystem.WIDGET,
                CoordinateSystem.UNIFIED,
                widget
            ).point

            return SnapEvent(
                event_type=EventType.WIDGET_RESIZE,
                position=unified_pos,
                source_widget=widget,
                target_widget=widget,
                timestamp=time.time(),
                original_event=event,
                metadata={
                    "old_size": getattr(event, 'oldSize', lambda: None)(),
                    "new_size": widget.size(),
                    "resize_handles": 0  # Could be enhanced to track which handles were used
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to create resize event: {e}")
            return None

    def _create_move_event(self, widget: QWidget, event: QEvent) -> Optional[SnapEvent]:
        """Create a move SnapEvent."""
        try:
            # Get widget position
            widget_pos = QPointF(widget.pos())

            # Convert to unified coordinates
            unified_pos = self.event_processor.coordinate_manager.transform_point(
                widget_pos,
                CoordinateSystem.WIDGET,
                CoordinateSystem.UNIFIED,
                widget
            ).point

            return SnapEvent(
                event_type=EventType.WIDGET_MOVE,
                position=unified_pos,
                source_widget=widget,
                target_widget=widget,
                timestamp=time.time(),
                original_event=event,
                metadata={
                    "old_position": getattr(event, 'oldPos', lambda: None)(),
                    "new_position": widget.pos()
                }
            )
        except Exception as e:
            self.logger.error(f"Failed to create move event: {e}")
            return None

    def _find_target_widget(self, source_widget: QWidget) -> Optional[QWidget]:
        """
        Find the target widget for snapping operations.

        Args:
            source_widget: Source widget that generated the event

        Returns:
            Target widget for snapping or None
        """
        try:
            # For dock widgets, the target is usually the dock itself
            if isinstance(source_widget, QDockWidget):
                return source_widget

            # For other widgets, find the parent dock if any
            parent = source_widget.parent()
            while parent:
                if isinstance(parent, QDockWidget):
                    return parent
                parent = parent.parent()

            # Fallback to main window
            return self.event_processor.main_window
        except Exception:
            return None


class EventProcessor:
    """
    Efficient event handling for the widget snapping system without conflicts.

    This processor manages all snapping-related events, providing debouncing,
    filtering, and coordination while maintaining high performance and avoiding
    conflicts with other event handlers.

    The processor supports different widget types and their specific event handling
    requirements, ensuring smooth 30+ FPS interaction during snapping operations.

    Attributes:
        main_window: Main window instance
        config: Snap configuration settings
        coordinate_manager: Coordinate system manager
        snap_engine: Snap calculation engine
        debouncer: Event debouncing system
        event_filter: Qt event filter
        logger: Logger instance for debugging and monitoring
        _active_widgets: Currently active widgets for snapping
        _event_handlers: Registered event handlers
        _performance_stats: Performance monitoring data
    """

    def __init__(
        self,
        main_window: QMainWindow,
        config: SnapConfiguration,
        coordinate_manager: CoordinateManager,
        snap_engine: SnapEngine
    ):
        """
        Initialize the event processor.

        Args:
            main_window: Main window instance
            config: Snap configuration settings
            coordinate_manager: Coordinate system manager
            snap_engine: Snap calculation engine
        """
        self.logger = get_logger(__name__)
        self.logger.info("Initializing event processor")

        self.main_window = main_window
        self.config = config
        self.coordinate_manager = coordinate_manager
        self.snap_engine = snap_engine

        # Event processing components
        self.debouncer = EventDebouncer(
            time_threshold_ms=config.performance.update_debounce_ms,
            movement_threshold=config.performance.hysteresis_threshold
        )
        self.event_filter = EventFilter(self)

        # State tracking
        self._active_widgets: Dict[int, QWidget] = WeakKeyDictionary()
        self._event_handlers: Dict[EventType, List[Callable]] = {}
        self._processing_enabled = True

        # Performance monitoring
        self._performance_stats = {
            "total_events": 0,
            "processed_events": 0,
            "debounced_events": 0,
            "avg_processing_time_ms": 0.0,
            "max_processing_time_ms": 0.0
        }

        # Setup periodic cleanup
        self._setup_cleanup_timer()

        self.logger.info("Event processor initialized successfully")

    def _setup_cleanup_timer(self) -> None:
        """Setup timer for periodic cleanup of resources."""
        try:
            self._cleanup_timer = QTimer(self.main_window)
            self._cleanup_timer.setSingleShot(False)
            self._cleanup_timer.setInterval(5000)  # Clean up every 5 seconds
            self._cleanup_timer.timeout.connect(self._periodic_cleanup)
            self._cleanup_timer.start()
        except Exception as e:
            self.logger.error(f"Failed to setup cleanup timer: {e}")

    def _periodic_cleanup(self) -> None:
        """Periodic cleanup of resources and stale data."""
        try:
            # Clean up dead weak references
            self._active_widgets = {k: v for k, v in self._active_widgets.items() if v is not None}

            # Clear old performance stats
            if self._performance_stats["total_events"] > 10000:
                self._performance_stats = {
                    "total_events": 0,
                    "processed_events": 0,
                    "debounced_events": 0,
                    "avg_processing_time_ms": 0.0,
                    "max_processing_time_ms": 0.0
                }

            # Update coordinate systems if main window geometry changed
            if self.main_window:
                self.coordinate_manager.update_main_window_geometry()

        except Exception as e:
            self.logger.error(f"Error in periodic cleanup: {e}")

    def install_event_filter(self, widget: QWidget) -> bool:
        """
        Install event filter on a widget for snapping.

        Args:
            widget: Widget to install event filter on

        Returns:
            True if installation was successful, False otherwise
        """
        try:
            if widget is None:
                return False

            # Check if already installed
            if widget in self._active_widgets.values():
                return True

            # Install the event filter
            success = widget.installEventFilter(self.event_filter)
            if success:
                self._active_widgets[id(widget)] = widget
                self.logger.debug(f"Installed event filter on widget {widget.objectName() or type(widget).__name__}")
                return True
            else:
                self.logger.warning(f"Failed to install event filter on widget {widget.objectName() or type(widget).__name__}")
                return False

        except Exception as e:
            self.logger.error(f"Error installing event filter on widget: {e}")
            return False

    def remove_event_filter(self, widget: QWidget) -> bool:
        """
        Remove event filter from a widget.

        Args:
            widget: Widget to remove event filter from

        Returns:
            True if removal was successful, False otherwise
        """
        try:
            if widget is None:
                return False

            # Remove from active widgets
            widget_id = id(widget)
            if widget_id in self._active_widgets:
                del self._active_widgets[widget_id]

            # Remove event filter
            success = widget.removeEventFilter(self.event_filter)
            if success:
                self.logger.debug(f"Removed event filter from widget {widget.objectName() or type(widget).__name__}")
                return True
            else:
                self.logger.warning(f"Failed to remove event filter from widget {widget.objectName() or type(widget).__name__}")
                return False

        except Exception as e:
            self.logger.error(f"Error removing event filter from widget: {e}")
            return False

    def process_event(self, event: SnapEvent) -> bool:
        """
        Process a snapping event.

        Args:
            event: Snap event to process

        Returns:
            True if event was processed, False if debounced or ignored
        """
        start_time = time.time()

        try:
            # Check if processing is enabled
            if not self._processing_enabled:
                return False

            # Update performance stats
            self._performance_stats["total_events"] += 1

            # Check if event should be debounced
            if not self.debouncer.should_process_event(event):
                self.debouncer.add_pending_event(event)
                self._performance_stats["debounced_events"] += 1
                return False

            # Process pending events first
            pending_events = self.debouncer.get_pending_events()
            for pending_event in pending_events:
                self._process_event_immediate(pending_event)

            # Process current event
            processed = self._process_event_immediate(event)
            if processed:
                self._performance_stats["processed_events"] += 1

            # Update performance timing
            processing_time = (time.time() - start_time) * 1000
            self._update_performance_timing(processing_time)

            return processed

        except Exception as e:
            self.logger.error(f"Error processing event {event.event_type}: {e}")
            return False

    def _process_event_immediate(self, event: SnapEvent) -> bool:
        """
        Process an event immediately without debouncing.

        Args:
            event: Event to process

        Returns:
            True if event was handled, False otherwise
        """
        try:
            # Call registered event handlers
            if event.event_type in self._event_handlers:
                for handler in self._event_handlers[event.event_type]:
                    try:
                        handler(event)
                    except Exception as e:
                        self.logger.error(f"Error in event handler for {event.event_type}: {e}")

            # Handle specific event types
            if event.event_type == EventType.MOUSE_MOVE:
                return self._handle_mouse_move(event)
            elif event.event_type == EventType.MOUSE_PRESS:
                return self._handle_mouse_press(event)
            elif event.event_type == EventType.MOUSE_RELEASE:
                return self._handle_mouse_release(event)
            elif event.event_type == EventType.WIDGET_RESIZE:
                return self._handle_widget_resize(event)
            elif event.event_type == EventType.WIDGET_MOVE:
                return self._handle_widget_move(event)
            elif event.event_type == EventType.LAYOUT_CHANGE:
                return self._handle_layout_change(event)

            return True  # Event was processed by handlers

        except Exception as e:
            self.logger.error(f"Error in immediate event processing: {e}")
            return False

    def _handle_mouse_move(self, event: SnapEvent) -> bool:
        """Handle mouse move events for snapping."""
        try:
            if not self.config.enabled:
                return False

            # Only process if we have a target widget
            if not event.target_widget:
                return False

            # Calculate snap position
            snap_result = self.snap_engine.calculate_snap(
                event.position,
                CoordinateSystem.UNIFIED,
                event.target_widget
            )

            # Apply snap if applicable
            if snap_result.snap_applied and snap_result.snap_candidate:
                self._apply_snap_to_widget(event.target_widget, snap_result)

            return True
        except Exception as e:
            self.logger.error(f"Error handling mouse move: {e}")
            return False

    def _handle_mouse_press(self, event: SnapEvent) -> bool:
        """Handle mouse press events."""
        try:
            # Reset debouncer for new interaction
            self.debouncer.reset()

            # Start tracking for potential drag operation
            if event.target_widget and isinstance(event.target_widget, QDockWidget):
                self._start_drag_tracking(event.target_widget)

            return True
        except Exception as e:
            self.logger.error(f"Error handling mouse press: {e}")
            return False

    def _handle_mouse_release(self, event: SnapEvent) -> bool:
        """Handle mouse release events."""
        try:
            # End drag tracking
            if event.target_widget:
                self._end_drag_tracking(event.target_widget)

            return True
        except Exception as e:
            self.logger.error(f"Error handling mouse release: {e}")
            return False

    def _handle_widget_resize(self, event: SnapEvent) -> bool:  # pylint: disable=unused-argument
        """Handle widget resize events."""
        try:
            # Update coordinate systems
            self.coordinate_manager.update_main_window_geometry()

            # Clear caches that might be affected by resize
            self.snap_engine.update_configuration()

            return True
        except Exception as e:
            self.logger.error(f"Error handling widget resize: {e}")
            return False

    def _handle_widget_move(self, event: SnapEvent) -> bool:  # pylint: disable=unused-argument
        """Handle widget move events."""
        try:
            # Update coordinate systems
            self.coordinate_manager.update_main_window_geometry()

            return True
        except Exception as e:
            self.logger.error(f"Error handling widget move: {e}")
            return False

    def _handle_layout_change(self, event: SnapEvent) -> bool:  # pylint: disable=unused-argument
        """Handle layout change events."""
        try:
            # Clear all caches when layout changes
            self.snap_engine.update_configuration()
            self.coordinate_manager.clear_cache()

            return True
        except Exception as e:
            self.logger.error(f"Error handling layout change: {e}")
            return False

    def _apply_snap_to_widget(self, widget: QWidget, snap_result: SnapResult) -> None:
        """
        Apply snap result to a widget.

        Args:
            widget: Widget to apply snap to
            snap_result: Snap calculation result
        """
        try:
            if not snap_result.snap_applied:
                return

            # Convert snapped position back to appropriate coordinate system
            if isinstance(widget, QDockWidget):
                # For dock widgets, we need to work with the main window's coordinate system
                snapped_global = self.coordinate_manager.transform_point(
                    snap_result.snapped_position,
                    CoordinateSystem.UNIFIED,
                    CoordinateSystem.SCREEN
                ).point

                # Apply the snap by moving the dock
                current_pos = widget.mapToGlobal(QPoint(0, 0))
                delta_x = snapped_global.x() - current_pos.x()
                delta_y = snapped_global.y() - current_pos.y()

                if abs(delta_x) > 1 or abs(delta_y) > 1:  # Only move if significant change
                    widget.move(widget.x() + int(delta_x), widget.y() + int(delta_y))

            self.logger.debug(f"Applied snap to widget {widget.objectName() or type(widget).__name__}")
        except Exception as e:
            self.logger.error(f"Failed to apply snap to widget: {e}")

    def _start_drag_tracking(self, widget: QWidget) -> None:
        """Start tracking a drag operation."""
        try:
            # Mark widget as being dragged
            self._active_widgets[id(widget)] = widget

            self.logger.debug(f"Started drag tracking for widget {widget.objectName() or type(widget).__name__}")
        except Exception as e:
            self.logger.error(f"Failed to start drag tracking: {e}")

    def _end_drag_tracking(self, widget: QWidget) -> None:
        """End tracking a drag operation."""
        try:
            # Remove drag tracking
            widget_id = id(widget)
            if widget_id in self._active_widgets:
                del self._active_widgets[widget_id]

            self.logger.debug(f"Ended drag tracking for widget {widget.objectName() or type(widget).__name__}")
        except Exception as e:
            self.logger.error(f"Failed to end drag tracking: {e}")

    def _update_performance_timing(self, processing_time_ms: float) -> None:
        """Update performance timing statistics."""
        self._performance_stats["max_processing_time_ms"] = max(
            self._performance_stats["max_processing_time_ms"],
            processing_time_ms
        )

        # Update average processing time
        total_events = self._performance_stats["processed_events"]
        if total_events > 0:
            total_time = self._performance_stats["avg_processing_time_ms"] * (total_events - 1)
            self._performance_stats["avg_processing_time_ms"] = (total_time + processing_time_ms) / total_events

    def register_event_handler(self, event_type: EventType, handler: Callable) -> None:
        """
        Register an event handler for a specific event type.

        Args:
            event_type: Type of event to handle
            handler: Handler function that takes a SnapEvent parameter
        """
        try:
            if event_type not in self._event_handlers:
                self._event_handlers[event_type] = []

            self._event_handlers[event_type].append(handler)
            self.logger.debug(f"Registered event handler for {event_type}")
        except Exception as e:
            self.logger.error(f"Failed to register event handler: {e}")

    def unregister_event_handler(self, event_type: EventType, handler: Callable) -> None:
        """
        Unregister an event handler for a specific event type.

        Args:
            event_type: Type of event
            handler: Handler function to remove
        """
        try:
            if event_type in self._event_handlers:
                if handler in self._event_handlers[event_type]:
                    self._event_handlers[event_type].remove(handler)
                    self.logger.debug(f"Unregistered event handler for {event_type}")
        except Exception as e:
            self.logger.error(f"Failed to unregister event handler: {e}")

    def set_processing_enabled(self, enabled: bool) -> None:
        """
        Enable or disable event processing.

        Args:
            enabled: Whether event processing should be enabled
        """
        try:
            self._processing_enabled = enabled
            self.logger.info(f"Event processing {'enabled' if enabled else 'disabled'}")
        except Exception as e:
            self.logger.error(f"Failed to set processing enabled: {e}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        try:
            return {
                "event_processor_stats": self._performance_stats.copy(),
                "debouncer_stats": {
                    "pending_events": len(self.debouncer.get_pending_events()),
                    "time_threshold_ms": self.debouncer.time_threshold_ms,
                    "movement_threshold": self.debouncer.movement_threshold
                },
                "active_widgets": len(self._active_widgets),
                "registered_handlers": {et.name: len(handlers) for et, handlers in self._event_handlers.items()},
                "processing_enabled": self._processing_enabled
            }
        except Exception as e:
            self.logger.error(f"Failed to get performance stats: {e}")
            return {"error": str(e)}

    def reset(self) -> None:
        """
        Reset the event processor to initial state.

        Clears all tracking data and resets performance statistics.
        """
        try:
            self.debouncer.reset()
            self._active_widgets.clear()
            self._event_handlers.clear()
            self._performance_stats = {
                "total_events": 0,
                "processed_events": 0,
                "debounced_events": 0,
                "avg_processing_time_ms": 0.0,
                "max_processing_time_ms": 0.0
            }

            self.logger.info("Event processor reset to initial state")
        except Exception as e:
            self.logger.error(f"Failed to reset event processor: {e}")
            raise

    def cleanup(self) -> None:
        """
        Cleanup resources and remove all event filters.

        This should be called when the snapping system is being shut down.
        """
        try:
            # Stop cleanup timer
            if hasattr(self, '_cleanup_timer'):
                self._cleanup_timer.stop()

            # Remove all event filters
            for widget in list(self._active_widgets.values()):
                self.remove_event_filter(widget)

            # Clear all data
            self.reset()

            self.logger.info("Event processor cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during event processor cleanup: {e}")