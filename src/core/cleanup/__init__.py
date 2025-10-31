"""
Unified Cleanup System

This module provides a consolidated cleanup architecture that replaces
4 overlapping cleanup systems with a single, well-architected coordinator
and specialized handlers.

Components:
- UnifiedCleanupCoordinator: Central orchestration
- VTKCleanupHandler: VTK-specific resource cleanup
- WidgetCleanupHandler: Qt widget cleanup
- ServiceCleanupHandler: Application service cleanup
- ResourceCleanupHandler: System resource cleanup
"""

from .unified_cleanup_coordinator import (
    UnifiedCleanupCoordinator,
    CleanupPhase,
    CleanupContext,
    CleanupError,
    CleanupStats,
    CleanupHandler,
    get_unified_cleanup_coordinator,
    coordinate_unified_cleanup
)

from .vtk_cleanup_handler import VTKCleanupHandler
from .widget_cleanup_handler import WidgetCleanupHandler
from .service_cleanup_handler import ServiceCleanupHandler
from .resource_cleanup_handler import ResourceCleanupHandler

__all__ = [
    'UnifiedCleanupCoordinator',
    'CleanupPhase',
    'CleanupContext',
    'CleanupError',
    'CleanupStats',
    'CleanupHandler',
    'VTKCleanupHandler',
    'WidgetCleanupHandler',
    'ServiceCleanupHandler',
    'ResourceCleanupHandler',
    'get_unified_cleanup_coordinator',
    'coordinate_unified_cleanup'
]

# Version information
__version__ = '1.0.0'
__author__ = 'Kilo Code'
__description__ = 'Unified Cleanup System for Application Resource Management'