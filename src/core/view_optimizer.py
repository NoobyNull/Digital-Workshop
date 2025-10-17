"""
View Optimizer for Thumbnail Generation

This module provides algorithms for finding the optimal viewing angle for 3D model thumbnails.
Uses orthogonal views only (0°, 90°, 180°, 270°) with Z-up orientation for professional appearance.
"""

import math
from typing import Dict, Tuple
from dataclasses import dataclass

from core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CameraParameters:
    """Camera parameters for thumbnail generation."""
    position: Tuple[float, float, float]
    focal_point: Tuple[float, float, float]
    view_up: Tuple[float, float, float]
    distance: float
    view_name: str  # 'front', 'right', 'back', 'left', 'top'


class ViewOptimizer:
    """
    Optimize camera view for 3D model thumbnail generation.
    
    Tests orthogonal views (0°, 90°, 180°, 270°) with Z-up orientation
    and selects the best view based on visible surface area and balance.
    """
    
    def __init__(self):
        """Initialize the view optimizer."""
        self.logger = get_logger(__name__)
        
    def find_best_orthogonal_view(
        self,
        bounds: Tuple[float, float, float, float, float, float],
        prefer_front: bool = True
    ) -> CameraParameters:
        """
        Find the best orthogonal viewing angle for a 3D model.
        
        Args:
            bounds: Model bounds (xmin, xmax, ymin, ymax, zmin, zmax)
            prefer_front: If True, prefer front view when scores are equal
            
        Returns:
            CameraParameters with optimal view settings
        """
        try:
            xmin, xmax, ymin, ymax, zmin, zmax = bounds
            
            # Calculate model center and dimensions
            center_x = (xmin + xmax) * 0.5
            center_y = (ymin + ymax) * 0.5
            center_z = (zmin + zmax) * 0.5
            center = (center_x, center_y, center_z)
            
            dx = max(1e-6, xmax - xmin)
            dy = max(1e-6, ymax - ymin)
            dz = max(1e-6, zmax - zmin)
            
            # Calculate radius for camera distance
            radius = math.sqrt(dx*dx + dy*dy + dz*dz) * 0.5
            
            # Define orthogonal views (0°, 90°, 180°, 270°) with Z-up
            views = self._get_orthogonal_views(center, radius)
            
            # Score each view
            best_view = None
            best_score = -1
            
            for view_name, camera_params in views.items():
                score = self._score_view(view_name, dx, dy, dz)
                
                self.logger.debug(
                    f"View '{view_name}' score: {score:.3f} "
                    f"(dimensions: X={dx:.2f}, Y={dy:.2f}, Z={dz:.2f})"
                )
                
                if score > best_score or (score == best_score and prefer_front and view_name == 'front'):
                    best_score = score
                    best_view = camera_params
                    
            if best_view is None:
                # Fallback to front view
                self.logger.warning("No valid view found, using front view as fallback")
                best_view = views['front']
                
            self.logger.info(
                f"Selected '{best_view.view_name}' view with score {best_score:.3f} "
                f"for model with dimensions X={dx:.2f}, Y={dy:.2f}, Z={dz:.2f}"
            )
            
            return best_view
            
        except Exception as e:
            self.logger.error(f"Error finding optimal view: {e}", exc_info=True)
            # Return safe default view
            return self._get_default_view(bounds)
            
    def _get_orthogonal_views(
        self,
        center: Tuple[float, float, float],
        radius: float
    ) -> Dict[str, CameraParameters]:
        """
        Get all orthogonal viewing angles with Z-up orientation.
        
        Args:
            center: Model center point (x, y, z)
            radius: Model radius for camera distance calculation
            
        Returns:
            Dictionary of view names to CameraParameters
        """
        cx, cy, cz = center
        # Distance scaled for good framing
        distance = radius * 2.5
        
        # Z-up is always (0, 0, 1)
        view_up = (0.0, 0.0, 1.0)
        
        return {
            # Front view (0°) - looking along +Y axis
            'front': CameraParameters(
                position=(cx, cy - distance, cz),
                focal_point=center,
                view_up=view_up,
                distance=distance,
                view_name='front'
            ),
            # Right view (90°) - looking along +X axis
            'right': CameraParameters(
                position=(cx + distance, cy, cz),
                focal_point=center,
                view_up=view_up,
                distance=distance,
                view_name='right'
            ),
            # Back view (180°) - looking along -Y axis
            'back': CameraParameters(
                position=(cx, cy + distance, cz),
                focal_point=center,
                view_up=view_up,
                distance=distance,
                view_name='back'
            ),
            # Left view (270°) - looking along -X axis
            'left': CameraParameters(
                position=(cx - distance, cy, cz),
                focal_point=center,
                view_up=view_up,
                distance=distance,
                view_name='left'
            ),
            # Top view - looking down along -Z axis
            'top': CameraParameters(
                position=(cx, cy, cz + distance),
                focal_point=center,
                view_up=(0.0, 1.0, 0.0),  # Y-up for top view
                distance=distance,
                view_name='top'
            )
        }
        
    def _score_view(
        self,
        view_name: str,
        dx: float,
        dy: float,
        dz: float
    ) -> float:
        """
        Score a view based on model dimensions and view characteristics.
        
        Scoring criteria:
        - Prefer views that show the largest face
        - Prefer views with good aspect ratio balance
        - Slightly prefer front and right views for consistency
        
        Args:
            view_name: Name of the view ('front', 'right', 'back', 'left', 'top')
            dx: Model width (X dimension)
            dy: Model depth (Y dimension)
            dz: Model height (Z dimension)
            
        Returns:
            Score value (higher is better)
        """
        score = 0.0
        
        # Calculate visible area for each view
        if view_name == 'front' or view_name == 'back':
            # Shows XZ plane
            visible_area = dx * dz
            aspect_ratio = dx / dz if dz > 0 else 1.0
        elif view_name == 'right' or view_name == 'left':
            # Shows YZ plane
            visible_area = dy * dz
            aspect_ratio = dy / dz if dz > 0 else 1.0
        elif view_name == 'top':
            # Shows XY plane
            visible_area = dx * dy
            aspect_ratio = dx / dy if dy > 0 else 1.0
        else:
            visible_area = 0.0
            aspect_ratio = 1.0
            
        # Base score is visible area
        score = visible_area
        
        # Penalize extreme aspect ratios (prefer balanced views)
        if aspect_ratio > 1.0:
            aspect_penalty = 1.0 / (1.0 + abs(aspect_ratio - 1.0))
        else:
            aspect_penalty = 1.0 / (1.0 + abs(1.0/aspect_ratio - 1.0))
        score *= aspect_penalty
        
        # Slight preference bonus for front and right views (consistency)
        if view_name == 'front':
            score *= 1.05
        elif view_name == 'right':
            score *= 1.03
            
        return score
        
    def _get_default_view(
        self,
        bounds: Tuple[float, float, float, float, float, float]
    ) -> CameraParameters:
        """
        Get default fallback view (front view with Z-up).
        
        Args:
            bounds: Model bounds
            
        Returns:
            Default CameraParameters
        """
        xmin, xmax, ymin, ymax, zmin, zmax = bounds
        
        center_x = (xmin + xmax) * 0.5
        center_y = (ymin + ymax) * 0.5
        center_z = (zmin + zmax) * 0.5
        center = (center_x, center_y, center_z)
        
        dx = max(1e-6, xmax - xmin)
        dy = max(1e-6, ymax - ymin)
        dz = max(1e-6, zmax - zmin)
        radius = math.sqrt(dx*dx + dy*dy + dz*dz) * 0.5
        distance = radius * 2.5
        
        return CameraParameters(
            position=(center_x, center_y - distance, center_z),
            focal_point=center,
            view_up=(0.0, 0.0, 1.0),
            distance=distance,
            view_name='front'
        )