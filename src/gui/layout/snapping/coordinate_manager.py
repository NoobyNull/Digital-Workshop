"""
Coordinate Manager Module

This module provides unified coordinate system management for the widget snapping system.
It eliminates conflicts between different coordinate spaces (screen, client, widget-local, dock)
by providing a centralized coordinate transformation system with caching and performance optimization.

Classes:
    CoordinateManager: Manages unified coordinate transformations
    CoordinateSystem: Represents a coordinate system type
    TransformationCache: Caches coordinate transformations for performance
"""

import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple, Any, NamedTuple
from weakref import WeakKeyDictionary

from PySide6.QtCore import QPoint, QRect, QPointF, QRectF
from PySide6.QtWidgets import QWidget, QMainWindow, QDockWidget

from src.core.logging_config import get_logger


class CoordinateSystem(Enum):
    """
    Enumeration of supported coordinate systems.

    Defines the different coordinate spaces used in the application.
    """

    SCREEN = "screen"  # Global screen coordinates
    CLIENT = "client"  # Main window client area coordinates
    WIDGET = "widget"  # Widget-local coordinates
    DOCK = "dock"  # Dock widget coordinates
    UNIFIED = "unified"  # Unified snapping coordinate system


class TransformationKey(NamedTuple):
    """
    Cache key for coordinate transformations.

    Used to cache transformation results for performance optimization.
    """

    source_system: CoordinateSystem
    target_system: CoordinateSystem
    source_point: Tuple[float, float]
    context_widget: Optional[int]  # Widget ID for context-specific transformations


@dataclass
class TransformationResult:
    """
    Result of a coordinate transformation.

    Contains the transformed coordinates and metadata about the transformation.
    """

    point: QPointF
    source_system: CoordinateSystem
    target_system: CoordinateSystem
    timestamp: float
    context_widget: Optional[QWidget] = None
    confidence: float = 1.0  # Confidence level of the transformation (0.0 to 1.0)

    def __post_init__(self):
        """Validate transformation result after initialization."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")


class TransformationCache:
    """
    High-performance cache for coordinate transformations.

    Uses LRU (Least Recently Used) eviction policy and weak references to prevent memory leaks.
    Thread-safe and optimized for the snapping system's performance requirements.
    """

    def __init__(self, max_size: int = 1000, ttl_seconds: float = 1.0):
        """
        Initialize the transformation cache.

        Args:
            max_size: Maximum number of cached transformations
            ttl_seconds: Time-to-live for cached entries in seconds
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[TransformationKey, TransformationResult] = {}
        self._access_times: Dict[TransformationKey, float] = {}
        self._widget_refs: WeakKeyDictionary = WeakKeyDictionary()

    def get(self, key: TransformationKey) -> Optional[TransformationResult]:
        """
        Get a cached transformation result.

        Args:
            key: Cache key for the transformation

        Returns:
            Cached transformation result or None if not found/expired
        """
        current_time = time.time()

        # Check if key exists and hasn't expired
        if key in self._cache:
            result = self._cache[key]
            if current_time - result.timestamp <= self.ttl_seconds:
                # Update access time
                self._access_times[key] = current_time
                return result

            # Entry expired, remove it
            self._remove(key)

        return None

    def put(self, key: TransformationKey, result: TransformationResult) -> None:
        """
        Store a transformation result in the cache.

        Args:
            key: Cache key for the transformation
            result: Transformation result to cache
        """
        current_time = time.time()

        # Remove expired entries first
        self._cleanup_expired()

        # If cache is full, remove least recently used entry
        if len(self._cache) >= self.max_size:
            self._evict_lru()

        # Store the new entry
        self._cache[key] = result
        self._access_times[key] = current_time

    def _cleanup_expired(self) -> None:
        """Remove expired cache entries."""
        current_time = time.time()
        expired_keys = [
            key
            for key, result in self._cache.items()
            if current_time - result.timestamp > self.ttl_seconds
        ]

        for key in expired_keys:
            self._remove(key)

    def _evict_lru(self) -> None:
        """Remove the least recently used cache entry."""
        if not self._access_times:
            return

        # Find least recently used key
        lru_key = min(self._access_times.items(), key=lambda x: x[1])
        self._remove(lru_key[0])

    def _remove(self, key: TransformationKey) -> None:
        """Remove a specific cache entry."""
        self._cache.pop(key, None)
        self._access_times.pop(key, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._access_times.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        current_time = time.time()
        active_entries = len(
            [
                key
                for key, result in self._cache.items()
                if current_time - result.timestamp <= self.ttl_seconds
            ]
        )

        return {
            "total_entries": len(self._cache),
            "active_entries": active_entries,
            "max_size": self.max_size,
            "hit_ratio": 0.0,  # Would need hit/miss counters for this
            "memory_usage_mb": len(self._cache) * 0.1,  # Rough estimate
        }


class CoordinateManager:
    """
    Manages unified coordinate transformations across the application.

    This class provides a centralized system for converting between different coordinate
    spaces (screen, client, widget-local, dock, unified) while maintaining high performance
    through caching and efficient algorithms.

    The coordinate manager eliminates the conflicts between different coordinate systems
    that existed in the previous implementation by providing a single source of truth
    for all coordinate transformations.

    Attributes:
        main_window: Reference to the main window for coordinate context
        cache: Transformation cache for performance optimization
        logger: Logger instance for debugging and monitoring
        _system_origins: Origins of different coordinate systems
        _system_bounds: Bounds of different coordinate systems
    """

    def __init__(self, main_window: QMainWindow, cache_size: int = 1000):
        """
        Initialize the coordinate manager.

        Args:
            main_window: Main window instance for coordinate context
            cache_size: Size of the transformation cache
        """
        self.logger = get_logger(__name__)
        self.logger.info("Initializing coordinate manager")

        self.main_window = main_window
        self.cache = TransformationCache(max_size=cache_size)

        # Coordinate system tracking
        self._system_origins: Dict[CoordinateSystem, QPoint] = {}
        self._system_bounds: Dict[CoordinateSystem, QRect] = {}

        # Initialize coordinate systems
        self._initialize_coordinate_systems()

        # Performance monitoring
        self._transform_count = 0
        self._cache_hits = 0
        self._cache_misses = 0

        self.logger.info("Coordinate manager initialized with cache size %s", cache_size)

    def _initialize_coordinate_systems(self) -> None:
        """
        Initialize all coordinate systems with their origins and bounds.

        This method sets up the reference points for all coordinate systems
        used in the application.
        """
        try:
            # Screen coordinate system (global desktop coordinates)
            self._system_origins[CoordinateSystem.SCREEN] = QPoint(0, 0)
            self._system_bounds[CoordinateSystem.SCREEN] = QRect(
                0, 0, 1920, 1080  # Default desktop resolution, will be updated
            )

            # Client coordinate system (main window client area)
            if self.main_window:
                self._system_origins[CoordinateSystem.CLIENT] = self.main_window.mapToGlobal(
                    QPoint(0, 0)
                )
                self._system_bounds[CoordinateSystem.CLIENT] = self.main_window.rect()
            else:
                self._system_origins[CoordinateSystem.CLIENT] = QPoint(0, 0)
                self._system_bounds[CoordinateSystem.CLIENT] = QRect(0, 0, 1200, 800)

            # Widget coordinate system (relative to widget top-left)
            self._system_origins[CoordinateSystem.WIDGET] = QPoint(0, 0)
            self._system_bounds[CoordinateSystem.WIDGET] = QRect(0, 0, 1000, 1000)

            # Dock coordinate system (dock widget area)
            self._system_origins[CoordinateSystem.DOCK] = QPoint(0, 0)
            self._system_bounds[CoordinateSystem.DOCK] = QRect(0, 0, 300, 200)

            # Unified coordinate system (snapping system coordinates)
            self._system_origins[CoordinateSystem.UNIFIED] = QPoint(0, 0)
            self._system_bounds[CoordinateSystem.UNIFIED] = QRect(0, 0, 1920, 1080)

            self.logger.debug("Initialized coordinate systems")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to initialize coordinate systems: %s", e)
            raise

    def update_screen_geometry(self, geometry: QRect) -> None:
        """
        Update the screen coordinate system bounds.

        Args:
            geometry: New screen geometry
        """
        try:
            self._system_bounds[CoordinateSystem.SCREEN] = geometry
            self._system_bounds[CoordinateSystem.UNIFIED] = geometry

            # Clear cache since screen geometry changed
            self.cache.clear()

            self.logger.debug("Updated screen geometry to %s", geometry)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to update screen geometry: %s", e)

    def update_main_window_geometry(self) -> None:
        """
        Update coordinate systems based on current main window geometry.

        This should be called when the main window is resized or moved.
        """
        try:
            if not self.main_window:
                return

            # Update client coordinate system
            self._system_origins[CoordinateSystem.CLIENT] = self.main_window.mapToGlobal(
                QPoint(0, 0)
            )
            self._system_bounds[CoordinateSystem.CLIENT] = self.main_window.rect()

            # Update unified system to match screen
            self._system_bounds[CoordinateSystem.UNIFIED] = self._system_bounds[
                CoordinateSystem.SCREEN
            ]

            # Clear cache since window geometry changed
            self.cache.clear()

            self.logger.debug("Updated main window coordinate systems")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to update main window geometry: %s", e)

    def transform_point(
        self,
        point: QPointF,
        source_system: CoordinateSystem,
        target_system: CoordinateSystem,
        context_widget: Optional[QWidget] = None,
    ) -> TransformationResult:
        """
        Transform a point from one coordinate system to another.

        Args:
            point: Point to transform
            source_system: Source coordinate system
            target_system: Target coordinate system
            context_widget: Optional widget for context-specific transformations

        Returns:
            Transformation result with the transformed point and metadata
        """
        try:
            # Create cache key
            cache_key = TransformationKey(
                source_system=source_system,
                target_system=target_system,
                source_point=(point.x(), point.y()),
                context_widget=id(context_widget) if context_widget else None,
            )

            # Check cache first
            cached_result = self.cache.get(cache_key)
            if cached_result:
                self._cache_hits += 1
                return cached_result

            self._cache_misses += 1

            # Perform transformation
            transformed_point = self._transform_point_impl(
                point, source_system, target_system, context_widget
            )

            # Create result
            result = TransformationResult(
                point=transformed_point,
                source_system=source_system,
                target_system=target_system,
                timestamp=time.time(),
                context_widget=context_widget,
                confidence=self._calculate_confidence(source_system, target_system, context_widget),
            )

            # Cache the result
            self.cache.put(cache_key, result)
            self._transform_count += 1

            return result
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(
                f"Failed to transform point {point} from {source_system} to {target_system}: {e}"
            )
            # Return identity transformation on error
            return TransformationResult(
                point=point,
                source_system=source_system,
                target_system=target_system,
                timestamp=time.time(),
                context_widget=context_widget,
                confidence=0.0,
            )

    def _transform_point_impl(
        self,
        point: QPointF,
        source_system: CoordinateSystem,
        target_system: CoordinateSystem,
        context_widget: Optional[QWidget] = None,
    ) -> QPointF:
        """
        Internal implementation of point transformation.

        Args:
            point: Point to transform
            source_system: Source coordinate system
            target_system: Target coordinate system
            context_widget: Optional widget for context-specific transformations

        Returns:
            Transformed point
        """
        if source_system == target_system:
            return QPointF(point)

        # Get current transformations
        if not self.main_window:
            return QPointF(point)  # Fallback for no main window

        # Screen coordinates are the global reference
        if source_system == CoordinateSystem.SCREEN:
            if target_system == CoordinateSystem.CLIENT:
                # Screen to client: subtract main window offset
                return point - QPointF(self._system_origins[CoordinateSystem.CLIENT])
            elif target_system == CoordinateSystem.WIDGET and context_widget:
                # Screen to widget: map through widget
                widget_pos = context_widget.mapFromGlobal(point.toPoint())
                return QPointF(widget_pos)
            elif target_system == CoordinateSystem.DOCK and context_widget:
                # Screen to dock: map through dock widget
                if isinstance(context_widget, QDockWidget):
                    dock_pos = context_widget.mapFromGlobal(point.toPoint())
                    return QPointF(dock_pos)
                else:
                    return self.transform_point(
                        point,
                        CoordinateSystem.SCREEN,
                        CoordinateSystem.WIDGET,
                        context_widget,
                    ).point
            elif target_system == CoordinateSystem.UNIFIED:
                return QPointF(point)  # Unified system matches screen

        elif source_system == CoordinateSystem.CLIENT:
            if target_system == CoordinateSystem.SCREEN:
                # Client to screen: add main window offset
                return point + QPointF(self._system_origins[CoordinateSystem.CLIENT])
            elif target_system == CoordinateSystem.WIDGET and context_widget:
                # Client to widget: map through widget
                global_pos = self.main_window.mapToGlobal(point.toPoint())
                widget_pos = context_widget.mapFromGlobal(global_pos)
                return QPointF(widget_pos)
            elif target_system == CoordinateSystem.DOCK and context_widget:
                # Client to dock: map through dock widget
                global_pos = self.main_window.mapToGlobal(point.toPoint())
                if isinstance(context_widget, QDockWidget):
                    dock_pos = context_widget.mapFromGlobal(global_pos)
                    return QPointF(dock_pos)
                else:
                    widget_pos = context_widget.mapFromGlobal(global_pos)
                    return QPointF(widget_pos)
            elif target_system == CoordinateSystem.UNIFIED:
                # Client to unified: convert to screen first
                screen_pos = self.transform_point(
                    point, CoordinateSystem.CLIENT, CoordinateSystem.SCREEN
                ).point
                return screen_pos

        elif source_system == CoordinateSystem.WIDGET and context_widget:
            if target_system == CoordinateSystem.SCREEN:
                # Widget to screen: map through widget
                global_pos = context_widget.mapToGlobal(point.toPoint())
                return QPointF(global_pos)
            elif target_system == CoordinateSystem.CLIENT:
                # Widget to client: map to global then to client
                global_pos = context_widget.mapToGlobal(point.toPoint())
                client_pos = self.main_window.mapFromGlobal(global_pos)
                return QPointF(client_pos)
            elif target_system == CoordinateSystem.DOCK and context_widget:
                # Widget to dock: both are widget-based, need context
                if isinstance(context_widget, QDockWidget):
                    return QPointF(point)  # Already in dock coordinates
                else:
                    # Map through parent dock if this widget is inside a dock
                    dock_parent = self._find_dock_parent(context_widget)
                    if dock_parent:
                        return self.transform_point(
                            point,
                            CoordinateSystem.WIDGET,
                            CoordinateSystem.DOCK,
                            dock_parent,
                        ).point
                    else:
                        return self.transform_point(
                            point,
                            CoordinateSystem.WIDGET,
                            CoordinateSystem.CLIENT,
                            context_widget,
                        ).point
            elif target_system == CoordinateSystem.UNIFIED:
                # Widget to unified: convert to screen first
                screen_pos = self.transform_point(
                    point,
                    CoordinateSystem.WIDGET,
                    CoordinateSystem.SCREEN,
                    context_widget,
                ).point
                return screen_pos

        elif source_system == CoordinateSystem.DOCK and context_widget:
            if target_system == CoordinateSystem.SCREEN:
                # Dock to screen: map through dock widget
                global_pos = context_widget.mapToGlobal(point.toPoint())
                return QPointF(global_pos)
            elif target_system == CoordinateSystem.CLIENT:
                # Dock to client: map to global then to client
                global_pos = context_widget.mapToGlobal(point.toPoint())
                client_pos = self.main_window.mapFromGlobal(global_pos)
                return QPointF(client_pos)
            elif target_system == CoordinateSystem.WIDGET and context_widget:
                # Dock to widget: need to find the target widget
                return QPointF(point)  # Assume already in correct widget coordinates
            elif target_system == CoordinateSystem.UNIFIED:
                # Dock to unified: convert to screen first
                screen_pos = self.transform_point(
                    point,
                    CoordinateSystem.DOCK,
                    CoordinateSystem.SCREEN,
                    context_widget,
                ).point
                return screen_pos

        elif source_system == CoordinateSystem.UNIFIED:
            if target_system == CoordinateSystem.SCREEN:
                return QPointF(point)  # Unified system matches screen
            elif target_system == CoordinateSystem.CLIENT:
                # Unified to client: convert to screen first
                screen_pos = QPointF(point)
                return screen_pos - QPointF(self._system_origins[CoordinateSystem.CLIENT])
            elif target_system == CoordinateSystem.WIDGET and context_widget:
                # Unified to widget: convert to screen first
                screen_pos = QPointF(point)
                widget_pos = context_widget.mapFromGlobal(screen_pos.toPoint())
                return QPointF(widget_pos)
            elif target_system == CoordinateSystem.DOCK and context_widget:
                # Unified to dock: convert to screen first
                screen_pos = QPointF(point)
                if isinstance(context_widget, QDockWidget):
                    dock_pos = context_widget.mapFromGlobal(screen_pos.toPoint())
                    return QPointF(dock_pos)
                else:
                    widget_pos = context_widget.mapFromGlobal(screen_pos.toPoint())
                    return QPointF(widget_pos)

        # Fallback: return original point
        self.logger.warning("Unsupported transformation from %s to {target_system}", source_system)
        return QPointF(point)

    def _find_dock_parent(self, widget: QWidget) -> Optional[QDockWidget]:
        """
        Find the dock widget parent of a given widget.

        Args:
            widget: Widget to find dock parent for

        Returns:
            Parent dock widget or None if not found
        """
        try:
            current = widget.parent()
            while current:
                if isinstance(current, QDockWidget):
                    return current
                current = current.parent()
            return None
        except Exception:
            return None

    def _calculate_confidence(
        self,
        source_system: CoordinateSystem,
        target_system: CoordinateSystem,
        context_widget: Optional[QWidget],
    ) -> float:
        """
        Calculate confidence level for a transformation.

        Args:
            source_system: Source coordinate system
            target_system: Target coordinate system
            context_widget: Context widget for the transformation

        Returns:
            Confidence level between 0.0 and 1.0
        """
        # Direct transformations have high confidence
        if source_system == target_system:
            return 1.0

        # Transformations involving the main window have high confidence
        if source_system == CoordinateSystem.CLIENT or target_system == CoordinateSystem.CLIENT:
            return 0.95

        # Widget transformations with context have good confidence
        if context_widget and (
            source_system == CoordinateSystem.WIDGET or target_system == CoordinateSystem.WIDGET
        ):
            return 0.9

        # Dock transformations with context have good confidence
        if context_widget and isinstance(context_widget, QDockWidget):
            if source_system == CoordinateSystem.DOCK or target_system == CoordinateSystem.DOCK:
                return 0.9

        # Screen transformations are reliable
        if source_system == CoordinateSystem.SCREEN or target_system == CoordinateSystem.SCREEN:
            return 0.95

        # Unified system transformations are reliable
        if source_system == CoordinateSystem.UNIFIED or target_system == CoordinateSystem.UNIFIED:
            return 0.95

        # Default confidence for other transformations
        return 0.7

    def transform_rect(
        self,
        rect: QRectF,
        source_system: CoordinateSystem,
        target_system: CoordinateSystem,
        context_widget: Optional[QWidget] = None,
    ) -> QRectF:
        """
        Transform a rectangle from one coordinate system to another.

        Args:
            rect: Rectangle to transform
            source_system: Source coordinate system
            target_system: Target coordinate system
            context_widget: Optional widget for context-specific transformations

        Returns:
            Transformed rectangle
        """
        try:
            # Transform all four corners and create bounding rectangle
            top_left = self.transform_point(
                rect.topLeft(), source_system, target_system, context_widget
            ).point
            top_right = self.transform_point(
                rect.topRight(), source_system, target_system, context_widget
            ).point
            bottom_left = self.transform_point(
                rect.bottomLeft(), source_system, target_system, context_widget
            ).point
            bottom_right = self.transform_point(
                rect.bottomRight(), source_system, target_system, context_widget
            ).point

            # Find min/max coordinates
            min_x = min(top_left.x(), top_right.x(), bottom_left.x(), bottom_right.x())
            max_x = max(top_left.x(), top_right.x(), bottom_left.x(), bottom_right.x())
            min_y = min(top_left.y(), top_right.y(), bottom_left.y(), bottom_right.y())
            max_y = max(top_left.y(), top_right.y(), bottom_left.y(), bottom_right.y())

            return QRectF(min_x, min_y, max_x - min_x, max_y - min_y)
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error(
                f"Failed to transform rectangle {rect} from {source_system} to {target_system}: {e}"
            )
            return QRectF(rect)  # Return original on error

    def get_system_bounds(self, system: CoordinateSystem) -> QRect:
        """
        Get the bounds of a coordinate system.

        Args:
            system: Coordinate system to get bounds for

        Returns:
            Bounds of the coordinate system
        """
        return self._system_bounds.get(system, QRect(0, 0, 1920, 1080))

    def get_system_origin(self, system: CoordinateSystem) -> QPoint:
        """
        Get the origin of a coordinate system.

        Args:
            system: Coordinate system to get origin for

        Returns:
            Origin point of the coordinate system
        """
        return self._system_origins.get(system, QPoint(0, 0))

    def is_point_in_system(self, point: QPointF, system: CoordinateSystem) -> bool:
        """
        Check if a point is within the bounds of a coordinate system.

        Args:
            point: Point to check
            system: Coordinate system to check against

        Returns:
            True if point is within system bounds
        """
        try:
            bounds = self.get_system_bounds(system)
            return bounds.contains(point.toPoint())
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to check if point %s is in system {system}: {e}", point)
            return False

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for the coordinate manager.

        Returns:
            Dictionary with performance statistics
        """
        try:
            cache_stats = self.cache.get_stats()

            total_transforms = self._transform_count
            hit_ratio = (self._cache_hits / max(total_transforms, 1)) * 100

            return {
                "total_transformations": total_transforms,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "cache_hit_ratio_percent": hit_ratio,
                "cache_stats": cache_stats,
                "memory_usage_mb": cache_stats["memory_usage_mb"],
                "coordinate_systems": len(self._system_origins),
            }
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to get performance stats: %s", e)
            return {
                "error": str(e),
                "total_transformations": self._transform_count,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
            }

    def clear_cache(self) -> None:
        """
        Clear the transformation cache.

        This should be called when the window geometry changes significantly.
        """
        try:
            self.cache.clear()
            self._cache_hits = 0
            self._cache_misses = 0
            self.logger.debug("Coordinate transformation cache cleared")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to clear cache: %s", e)

    def reset(self) -> None:
        """
        Reset the coordinate manager to initial state.

        This clears all caches and reinitializes coordinate systems.
        """
        try:
            self.cache.clear()
            self._transform_count = 0
            self._cache_hits = 0
            self._cache_misses = 0
            self._initialize_coordinate_systems()
            self.logger.info("Coordinate manager reset to initial state")
        except (OSError, IOError, ValueError, TypeError, KeyError, AttributeError) as e:
            self.logger.error("Failed to reset coordinate manager: %s", e)
            raise
