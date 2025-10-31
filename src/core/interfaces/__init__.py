"""Core interfaces for Candy-Cadence application.

This module defines the abstract base classes and interfaces that establish
the contract between different components of the application architecture.
"""

from .service_interfaces import (
    IThemeService,
    IModelService,
    IDatabaseService,
    IViewerService,
    IConfigurationService,
    IErrorHandler,
    IEventPublisher,
    IEventSubscriber
)

from .repository_interfaces import (
    IModelRepository,
    IMetadataRepository,
    ISearchRepository
)

from .parser_interfaces import (
    IParser,
    ModelFormat
)

__all__ = [
    # Service interfaces
    'IThemeService',
    'IModelService', 
    'IDatabaseService',
    'IViewerService',
    'IConfigurationService',
    'IErrorHandler',
    'IEventPublisher',
    'IEventSubscriber',
    
    # Repository interfaces
    'IModelRepository',
    'IMetadataRepository',
    'ISearchRepository',
    
    # Parser interfaces
    'IParser',
    'ModelFormat'
]