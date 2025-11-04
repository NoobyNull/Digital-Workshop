"""
Snap Engine Module

This module provides the core snapping logic and calculations for the widget snapping system.
It uses the coordinate manager for unified coordinate transformations and the configuration
system for snap parameters, providing high-performance snap detection and magnetism.

Classes:
    SnapEngine: Core snapping logic and calculations
    SnapResult: Result of a snap calculation
    SnapCandidate: Potential snap target with scoring
    SpatialIndex: High-performance spatial indexing for snap zones
"""

import math
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Dict, Tuple, Any
from collections import defaultdict

from PySide6.QtCore import QPointF, QRectF
from PySide6.QtWidgets import QWidget

from src.core.logging_config import get_logger
from src.gui.layout.snapping.coordinate_manager import (
    CoordinateManager,
    CoordinateSystem,
)
from src.gui.layout.snapping.snap_configuration import SnapConfiguration, SnapZone


class SnapType(Enum):
    """
    Types of snapping operations.

    Defines different ways widgets can snap to targets.
    """

    EDGE = "edge"  # Snap to edge of target
    CENTER = "center"  # Snap to center of target
    CORNER = "corner"  # Snap to corner of target
    GRID = "grid"  # Snap to grid points
    CUSTOM = "custom"  # Custom snap behavior


@dataclass
class SnapCandidate:
    """
    A potential snap target with scoring information.

    Represents a possible snapping destination with associated metadata
    for determining the best snap target.

    Attributes:
        zone: Snap zone configuration
        snap_type: Type of snap operation
        position: Snap position in unified coordinates
        distance: Distance from current position to snap target
        score: Calculated score for this candidate (higher = better)
        widget: Optional widget associated with this snap target
        confidence: Confidence level of this snap candidate (0.0 to 1.0)
    """

    zone: SnapZone
    snap_type: SnapType
    position: QPointF
    distance: float
    score: float
    widget: Optional[QWidget] = None
    confidence: float = 1.0

    def __post_init__(self):
        """Validate snap candidate after initialization."""
        if self.distance < 0:
            raise ValueError(f"Distance must be non-negative, got {self.distance}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be between 0.0 and 1.0, got {self.confidence}")
        if self.score < 0:
            raise ValueError(f"Score must be non-negative, got {self.score}")


@dataclass
class SnapResult:
    """
    Result of a snap calculation operation.

    Contains the best snap target found and associated metadata.

    Attributes:
        snapped_position: Final snapped position in unified coordinates
        original_position: Original position before snapping
        snap_candidate: Best snap candidate found (None if no snap occurred)
        snap_applied: Whether snapping was actually applied
        snap_strength: Strength of the snap effect (0.0 to 1.0)
        calculation_time_ms: Time taken for the calculation
        candidates_found: Number of snap candidates evaluated
        performance_metrics: Additional performance data
    """

    snapped_position: QPointF
    original_position: QPointF
    snap_candidate: Optional[SnapCandidate]
    snap_applied: bool
    snap_strength: float
    calculation_time_ms: float
    candidates_found: int
    performance_metrics: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate snap result after initialization."""
        if not 0.0 <= self.snap_strength <= 1.0:
            raise ValueError(f"Snap strength must be between 0.0 and 1.0, got {self.snap_strength}")
        if self.calculation_time_ms < 0:
            raise ValueError(
                f"Calculation time must be non-negative, got {self.calculation_time_ms}"
            )


class SpatialIndex:
    """
    High-performance spatial indexing for snap zones.

    Uses a simple grid-based spatial index for fast nearest-neighbor queries.
    Optimized for the snapping system's performance requirements.
    """

    def __init__(self, cell_size: int = 100):
        """
        Initialize the spatial index.

        Args:
            cell_size: Size of spatial grid cells in pixels
        """
        self.cell_size = cell_size
        self._grid: Dict[Tuple[int, int], List[SnapZone]] = defaultdict(list)
        self._bounds: Optional[QRectF] = None

    def add_zone(self, zone: SnapZone) -> None:
        """
        Add a snap zone to the spatial index.

        Args:
            zone: Snap zone to add
        """
        # Calculate grid cells that this zone occupies
        cells = self._get_zone_cells(zone)
        for cell in cells:
            self._grid[cell].append(zone)

        # Update bounds
        if self._bounds is None:
            self._bounds = QRectF(zone.area)
        else:
            self._bounds = self._bounds.united(QRectF(zone.area))

    def remove_zone(self, zone: SnapZone) -> None:
        """
        Remove a snap zone from the spatial index.

        Args:
            zone: Snap zone to remove
        """
        # Remove from all cells
        for cell_zones in self._grid.values():
            if zone in cell_zones:
                cell_zones.remove(zone)

        # Clean up empty cells
        empty_cells = [cell for cell, zones in self._grid.items() if not zones]
        for cell in empty_cells:
            del self._grid[cell]

        # Update bounds
        self._update_bounds()

    def find_nearby_zones(self, point: QPointF, radius: float) -> List[SnapZone]:
        """
        Find snap zones near a given point within a radius.

        Args:
            point: Center point for the search
            radius: Search radius in pixels

        Returns:
            List of nearby snap zones
        """
        if self._bounds is None or not self._bounds.contains(point):
            return []

        # Calculate search area in grid coordinates
        min_cell_x = int((point.x() - radius) // self.cell_size)
        max_cell_x = int((point.x() + radius) // self.cell_size)
        min_cell_y = int((point.y() - radius) // self.cell_size)
        max_cell_y = int((point.y() + radius) // self.cell_size)

        nearby_zones = []
        seen_zones = set()

        # Check all cells in the search area
        for cell_x in range(min_cell_x, max_cell_x + 1):
            for cell_y in range(min_cell_y, max_cell_y + 1):
                cell_key = (cell_x, cell_y)
                for zone in self._grid.get(cell_key, []):
                    if zone in seen_zones:
                        continue
                    seen_zones.add(zone)

                    # Check if zone is actually within radius
                    if self._zone_intersects_circle(zone, point, radius):
                        nearby_zones.append(zone)

        return nearby_zones

    def _get_zone_cells(self, zone: SnapZone) -> List[Tuple[int, int]]:
        """Get grid cells occupied by a snap zone."""
        cells = []
        min_x = zone.area.left()
        max_x = zone.area.right()
        min_y = zone.area.top()
        max_y = zone.area.bottom()

        start_cell_x = int(min_x // self.cell_size)
        end_cell_x = int(max_x // self.cell_size)
        start_cell_y = int(min_y // self.cell_size)
        end_cell_y = int(max_y // self.cell_size)

        for cell_x in range(start_cell_x, end_cell_x + 1):
            for cell_y in range(start_cell_y, end_cell_y + 1):
                cells.append((cell_x, cell_y))

        return cells

    def _zone_intersects_circle(self, zone: SnapZone, center: QPointF, radius: float) -> bool:
        """Check if a snap zone intersects with a circle."""
        # Simple distance check to zone bounds
        zone_center = QPointF(zone.area.center().x(), zone.area.center().y())
        distance = math.hypot(center.x() - zone_center.x(), center.y() - zone_center.y())
        return distance <= radius + max(zone.area.width(), zone.area.height()) / 2

    def _update_bounds(self) -> None:
        """Update the spatial index bounds based on current zones."""
        if not self._grid:
            self._bounds = None
            return

        # Recalculate bounds from all zones
        all_zones = []
        for zones in self._grid.values():
            all_zones.extend(zones)

        if all_zones:
            self._bounds = QRectF(all_zones[0].area)
            for zone in all_zones[1:]:
                self._bounds = self._bounds.united(QRectF(zone.area))
        else:
            self._bounds = None

    def clear(self) -> None:
        """Clear all zones from the spatial index."""
        self._grid.clear()
        self._bounds = None

    def get_stats(self) -> Dict[str, Any]:
        """Get spatial index statistics."""
        return {
            "total_zones": sum(len(zones) for zones in self._grid.values()),
            "occupied_cells": len(self._grid),
            "bounds": self._bounds.getCoords() if self._bounds else None,
            "cell_size": self.cell_size,
            "memory_usage_mb": len(self._grid) * 0.01,  # Rough estimate
        }


class SnapEngine:
    """
    Core snapping logic and calculations for the widget snapping system.

    This engine provides high-performance snap detection, magnetism calculations,
    and snap target evaluation. It uses spatial indexing for efficient zone queries
    and implements hysteresis to prevent flickering during interaction.

    The engine supports multiple snap types (edge, center, corner, grid) and
    provides real-time feedback for smooth 30+ FPS interaction.

    Attributes:
        config: Snap configuration settings
        coordinate_manager: Coordinate system manager
        spatial_index: Spatial index for efficient zone queries
        logger: Logger instance for debugging and monitoring
        _last_snap_position: Last snap position for hysteresis
        _snap_history: History of recent snap operations
    """

    def __init__(self, config: SnapConfiguration, coordinate_manager: CoordinateManager):
        """
        Initialize the snap engine.

        Args:
            config: Snap configuration settings
            coordinate_manager: Coordinate system manager for transformations
        """
        self.logger = get_logger(__name__)
        self.logger.info("Initializing snap engine")

        self.config = config
        self.coordinate_manager = coordinate_manager
        self.spatial_index = SpatialIndex()

        # Performance tracking
        self._last_snap_position: Optional[QPointF] = None
        self._snap_history: List[SnapResult] = []
        self._performance_stats = {
            "total_calculations": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_calculation_time_ms": 0.0,
        }

        # Build spatial index from configuration
        self._rebuild_spatial_index()

        # Connect to configuration changes
        self._connect_config_signals()

        self.logger.info("Snap engine initialized successfully")

    def _connect_config_signals(self) -> None:
        """Connect to configuration change signals."""
        # Note: In a real implementation, this would connect to config change signals
        # For now, we'll handle configuration updates manually
        # TODO: Implement signal connections when configuration change signals are available

    def _rebuild_spatial_index(self) -> None:
        """
        Rebuild the spatial index from current configuration.

        This should be called when snap zones are added, removed, or modified.
        """
        try:
            self.spatial_index.clear()
            active_zones = self.config.get_active_snap_zones()

            for zone in active_zones:
                self.spatial_index.add_zone(zone)

            self.logger.debug("Rebuilt spatial index with %s zones", len(active_zones))
        except Exception as e:
            self.logger.error("Failed to rebuild spatial index: %s", e)

    def calculate_snap(
        self,
        position: QPointF,
        source_system: CoordinateSystem = CoordinateSystem.CLIENT,
        context_widget: Optional[QWidget] = None,
        max_candidates: int = 10,
    ) -> SnapResult:
        """
        Calculate the best snap position for a given point.

        Args:
            position: Position to snap in source coordinate system
            source_system: Coordinate system of the input position
            context_widget: Optional widget for context-specific snapping
            max_candidates: Maximum number of candidates to evaluate

        Returns:
            Snap calculation result with best snap position and metadata
        """
        start_time = time.time()
        original_position = position

        try:
            # Transform position to unified coordinate system
            unified_pos = self.coordinate_manager.transform_point(
                position, source_system, CoordinateSystem.UNIFIED, context_widget
            ).point

            # Check hysteresis to avoid unnecessary calculations
            if self._should_skip_calculation(unified_pos):
                return SnapResult(
                    snapped_position=self._last_snap_position or unified_pos,
                    original_position=original_position,
                    snap_candidate=None,
                    snap_applied=False,
                    snap_strength=0.0,
                    calculation_time_ms=(time.time() - start_time) * 1000,
                    candidates_found=0,
                )

            # Find nearby snap zones
            search_radius = (
                max(zone.snap_threshold for zone in self.config.get_active_snap_zones()) * 2
            )
            nearby_zones = self.spatial_index.find_nearby_zones(unified_pos, search_radius)

            # Generate snap candidates
            candidates = self._generate_snap_candidates(unified_pos, nearby_zones, context_widget)

            # Filter and rank candidates
            best_candidate = self._select_best_candidate(candidates, max_candidates)

            # Calculate final snap position
            if best_candidate:
                snapped_pos = self._apply_snap_magnetism(unified_pos, best_candidate)
                snap_applied = True
                snap_strength = best_candidate.zone.magnetism
            else:
                snapped_pos = unified_pos
                snap_applied = False
                snap_strength = 0.0

            # Update tracking
            self._last_snap_position = snapped_pos
            self._update_performance_stats(time.time() - start_time)

            # Create result
            result = SnapResult(
                snapped_position=snapped_pos,
                original_position=original_position,
                snap_candidate=best_candidate,
                snap_applied=snap_applied,
                snap_strength=snap_strength,
                calculation_time_ms=(time.time() - start_time) * 1000,
                candidates_found=len(candidates),
                performance_metrics=self._get_calculation_metrics(),
            )

            # Add to history
            self._snap_history.append(result)
            if len(self._snap_history) > 100:  # Keep last 100 results
                self._snap_history.pop(0)

            return result

        except Exception as e:
            self.logger.error("Failed to calculate snap for position %s: {e}", position)
            return SnapResult(
                snapped_position=original_position,
                original_position=original_position,
                snap_candidate=None,
                snap_applied=False,
                snap_strength=0.0,
                calculation_time_ms=(time.time() - start_time) * 1000,
                candidates_found=0,
                performance_metrics={"error": str(e)},
            )

    def _should_skip_calculation(self, position: QPointF) -> bool:
        """
        Check if calculation should be skipped due to hysteresis.

        Args:
            position: Current position

        Returns:
            True if calculation should be skipped
        """
        if not self._last_snap_position:
            return False

        hysteresis_threshold = self.config.performance.hysteresis_threshold
        distance = math.hypot(
            position.x() - self._last_snap_position.x(),
            position.y() - self._last_snap_position.y(),
        )

        return distance < hysteresis_threshold

    def _generate_snap_candidates(
        self,
        position: QPointF,
        zones: List[SnapZone],
        context_widget: Optional[QWidget],
    ) -> List[SnapCandidate]:
        """
        Generate snap candidates from nearby zones.

        Args:
            position: Current position in unified coordinates
            zones: Nearby snap zones
            context_widget: Context widget for snapping

        Returns:
            List of snap candidates
        """
        candidates = []

        try:
            for zone in zones:
                if not zone.enabled:
                    continue

                # Generate candidates for different snap types
                for snap_type in [SnapType.EDGE, SnapType.CENTER, SnapType.CORNER]:
                    candidate = self._create_snap_candidate(
                        position, zone, snap_type, context_widget
                    )
                    if candidate:
                        candidates.append(candidate)

            # Sort by distance (closest first)
            candidates.sort(key=lambda c: c.distance)

        except Exception as e:
            self.logger.error("Failed to generate snap candidates: %s", e)

        return candidates

    def _create_snap_candidate(
        self,
        position: QPointF,
        zone: SnapZone,
        snap_type: SnapType,
        context_widget: Optional[QWidget],
    ) -> Optional[SnapCandidate]:
        """
        Create a snap candidate for a specific zone and snap type.

        Args:
            position: Current position
            zone: Snap zone configuration
            snap_type: Type of snap operation
            context_widget: Context widget

        Returns:
            Snap candidate or None if not applicable
        """
        try:
            # Calculate snap position based on type
            if snap_type == SnapType.EDGE:
                snap_pos = self._calculate_edge_snap(position, zone)
            elif snap_type == SnapType.CENTER:
                snap_pos = self._calculate_center_snap(position, zone)
            elif snap_type == SnapType.CORNER:
                snap_pos = self._calculate_corner_snap(position, zone)
            else:
                return None

            # Calculate distance and score
            distance = math.hypot(position.x() - snap_pos.x(), position.y() - snap_pos.y())

            # Check if within snap threshold
            if distance > zone.snap_threshold:
                return None

            # Calculate score based on distance, magnetism, and priority
            score = self._calculate_candidate_score(distance, zone, snap_type)

            return SnapCandidate(
                zone=zone,
                snap_type=snap_type,
                position=snap_pos,
                distance=distance,
                score=score,
                widget=context_widget,
                confidence=self._calculate_candidate_confidence(distance, zone),
            )

        except Exception as e:
            self.logger.error("Failed to create snap candidate for zone %s: {e}", zone.name)
            return None

    def _calculate_edge_snap(self, position: QPointF, zone: SnapZone) -> QPointF:
        """Calculate edge snap position."""
        # Snap to nearest edge of the zone
        zone_rect = QRectF(zone.area)
        snap_x = position.x()
        snap_y = position.y()

        # Snap to vertical edges
        if abs(position.x() - zone_rect.left()) < abs(position.x() - zone_rect.right()):
            snap_x = zone_rect.left()
        else:
            snap_x = zone_rect.right()

        # Snap to horizontal edges
        if abs(position.y() - zone_rect.top()) < abs(position.y() - zone_rect.bottom()):
            snap_y = zone_rect.top()
        else:
            snap_y = zone_rect.bottom()

        return QPointF(snap_x, snap_y)

    def _calculate_center_snap(
        self, position: QPointF, zone: SnapZone
    ) -> QPointF:  # pylint: disable=unused-argument
        """Calculate center snap position."""
        # Note: position is not used for center snap as we always snap to the zone center
        # This maintains API consistency with other snap calculation methods
        zone_rect = QRectF(zone.area)
        return zone_rect.center()

    def _calculate_corner_snap(self, position: QPointF, zone: SnapZone) -> QPointF:
        """Calculate corner snap position."""
        zone_rect = QRectF(zone.area)

        # Find nearest corner
        corners = [
            zone_rect.topLeft(),
            zone_rect.topRight(),
            zone_rect.bottomLeft(),
            zone_rect.bottomRight(),
        ]

        nearest_corner = min(
            corners,
            key=lambda corner: math.hypot(position.x() - corner.x(), position.y() - corner.y()),
        )

        return nearest_corner

    def _calculate_candidate_score(
        self, distance: float, zone: SnapZone, snap_type: SnapType
    ) -> float:
        """
        Calculate score for a snap candidate.

        Higher scores indicate better snap targets.

        Args:
            distance: Distance from current position
            zone: Snap zone configuration
            snap_type: Type of snap operation

        Returns:
            Calculated score
        """
        # Base score from distance (closer = higher score)
        distance_score = max(0, zone.snap_threshold - distance)

        # Apply magnetism multiplier
        magnetism_multiplier = zone.magnetism

        # Apply priority multiplier
        priority_multiplier = 1.0 + (zone.priority * 0.1)

        # Apply snap type preference (edges are generally preferred)
        type_multiplier = {
            SnapType.EDGE: 1.0,
            SnapType.CENTER: 0.8,
            SnapType.CORNER: 0.6,
            SnapType.GRID: 0.9,
            SnapType.CUSTOM: 0.7,
        }.get(snap_type, 0.5)

        return distance_score * magnetism_multiplier * priority_multiplier * type_multiplier

    def _calculate_candidate_confidence(self, distance: float, zone: SnapZone) -> float:
        """
        Calculate confidence level for a snap candidate.

        Args:
            distance: Distance from current position
            zone: Snap zone configuration

        Returns:
            Confidence level between 0.0 and 1.0
        """
        # Confidence decreases with distance
        if distance >= zone.snap_threshold:
            return 0.0

        # Higher magnetism = higher confidence
        base_confidence = zone.magnetism

        # Closer distance = higher confidence
        distance_factor = 1.0 - (distance / zone.snap_threshold)

        return min(1.0, base_confidence * (0.5 + 0.5 * distance_factor))

    def _select_best_candidate(
        self, candidates: List[SnapCandidate], max_candidates: int
    ) -> Optional[SnapCandidate]:
        """
        Select the best snap candidate from the list.

        Args:
            candidates: List of snap candidates
            max_candidates: Maximum number of candidates to consider

        Returns:
            Best snap candidate or None
        """
        if not candidates:
            return None

        # Limit candidates for performance
        limited_candidates = candidates[:max_candidates]

        # Select candidate with highest score
        return max(limited_candidates, key=lambda c: c.score)

    def _apply_snap_magnetism(self, position: QPointF, candidate: SnapCandidate) -> QPointF:
        """
        Apply magnetic attraction to the snap position.

        Args:
            position: Current position
            candidate: Snap candidate to apply magnetism for

        Returns:
            Position with magnetism applied
        """
        try:
            # Calculate magnetic pull based on distance and magnetism strength
            distance = candidate.distance
            magnetism = candidate.zone.magnetism

            if distance >= candidate.zone.snap_threshold:
                return position

            # Calculate pull strength (stronger when closer)
            pull_strength = magnetism * (1.0 - (distance / candidate.zone.snap_threshold))

            # Apply pull towards snap position
            snap_pos = candidate.position
            pull_x = (snap_pos.x() - position.x()) * pull_strength
            pull_y = (snap_pos.y() - position.y()) * pull_strength

            return QPointF(position.x() + pull_x, position.y() + pull_y)

        except Exception as e:
            self.logger.error("Failed to apply snap magnetism: %s", e)
            return position

    def _update_performance_stats(self, calculation_time: float) -> None:
        """Update performance statistics."""
        self._performance_stats["total_calculations"] += 1

        # Update average calculation time
        total_time = self._performance_stats["avg_calculation_time_ms"] * (
            self._performance_stats["total_calculations"] - 1
        )
        total_time += calculation_time * 1000  # Convert to ms
        self._performance_stats["avg_calculation_time_ms"] = (
            total_time / self._performance_stats["total_calculations"]
        )

    def _get_calculation_metrics(self) -> Dict[str, Any]:
        """Get current calculation metrics."""
        return {
            "spatial_index_stats": self.spatial_index.get_stats(),
            "performance_stats": self._performance_stats.copy(),
            "history_size": len(self._snap_history),
            "last_calculation_time_ms": self._performance_stats["avg_calculation_time_ms"],
        }

    def update_configuration(self) -> None:
        """
        Update the engine when configuration changes.

        This rebuilds the spatial index and clears caches.
        """
        try:
            self._rebuild_spatial_index()
            self.coordinate_manager.clear_cache()
            self._last_snap_position = None

            self.logger.info("Snap engine configuration updated")
        except Exception as e:
            self.logger.error("Failed to update configuration: %s", e)

    def get_snap_zones_near_position(self, position: QPointF, radius: float) -> List[SnapZone]:
        """
        Get snap zones near a given position.

        Args:
            position: Position in unified coordinates
            radius: Search radius

        Returns:
            List of nearby snap zones
        """
        return self.spatial_index.find_nearby_zones(position, radius)

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive performance statistics.

        Returns:
            Dictionary with performance metrics
        """
        return {
            "engine_stats": self._performance_stats.copy(),
            "spatial_index_stats": self.spatial_index.get_stats(),
            "coordinate_manager_stats": self.coordinate_manager.get_performance_stats(),
            "calculation_metrics": self._get_calculation_metrics(),
            "history_stats": {
                "total_snaps": len(self._snap_history),
                "avg_snap_strength": sum(r.snap_strength for r in self._snap_history)
                / max(len(self._snap_history), 1),
                "snap_applied_ratio": sum(1 for r in self._snap_history if r.snap_applied)
                / max(len(self._snap_history), 1),
            },
        }

    def reset(self) -> None:
        """
        Reset the snap engine to initial state.

        Clears all caches, history, and performance statistics.
        """
        try:
            self._last_snap_position = None
            self._snap_history.clear()
            self._performance_stats = {
                "total_calculations": 0,
                "cache_hits": 0,
                "cache_misses": 0,
                "avg_calculation_time_ms": 0.0,
            }
            self.spatial_index.clear()
            self.coordinate_manager.clear_cache()

            self.logger.info("Snap engine reset to initial state")
        except Exception as e:
            self.logger.error("Failed to reset snap engine: %s", e)
            raise
