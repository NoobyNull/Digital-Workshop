# Interface Contracts

## Overview

This document defines the interface contracts between modules in the Candy-Cadence architecture. These contracts ensure loose coupling, clear responsibilities, and maintainable code.

## Core Service Interfaces

### IThemeService

```python
from abc import ABC, abstractmethod
from typing import Dict, Optional, Union
from pathlib import Path

class IThemeService(ABC):
    """Interface for theme management services."""
    
    @abstractmethod
    def apply_theme(self, theme_name: str) -> bool:
        """Apply a theme by name."""
        pass
    
    @abstractmethod
    def get_current_theme(self) -> str:
        """Get the name of the currently applied theme."""
        pass
    
    @abstractmethod
    def get_available_themes(self) -> list[str]:
        """Get list of available theme names."""
        pass
    
    @abstractmethod
    def get_color(self, color_name: str, default: Optional[str] = None) -> str:
        """Get a color value by name."""
        pass
    
    @abstractmethod
    def set_color(self, color_name: str, value: str) -> None:
        """Set a color value."""
        pass
    
    @abstractmethod
    def export_theme(self, file_path: Path) -> bool:
        """Export current theme to file."""
        pass
    
    @abstractmethod
    def import_theme(self, file_path: Path) -> bool:
        """Import theme from file."""
        pass
```

### IModelService

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pathlib import Path

class IModelService(ABC):
    """Interface for model management services."""
    
    @abstractmethod
    def load_model(self, file_path: Path, progress_callback: Optional[callable] = None) -> bool:
        """Load a 3D model from file."""
        pass
    
    @abstractmethod
    def unload_model(self, model_id: str) -> bool:
        """Unload a model from memory."""
        pass
    
    @abstractmethod
    def get_model(self, model_id: str) -> Optional[Any]:
        """Get a loaded model by ID."""
        pass
    
    @abstractmethod
    def get_loaded_models(self) -> List[str]:
        """Get list of loaded model IDs."""
        pass
    
    @abstractmethod
    def get_model_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a model."""
        pass
    
    @abstractmethod
    def update_model_metadata(self, model_id: str, metadata: Dict[str, Any]) -> bool:
        """Update model metadata."""
        pass
    
    @abstractmethod
    def search_models(self, query: str) -> List[str]:
        """Search for models by query."""
        pass
```

### IDatabaseService

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

class IDatabaseService(ABC):
    """Interface for database operations."""
    
    @abstractmethod
    def add_model(self, model_data: Dict[str, Any]) -> str:
        """Add a model to the database. Returns model ID."""
        pass
    
    @abstractmethod
    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get model data by ID."""
        pass
    
    @abstractmethod
    def update_model(self, model_id: str, model_data: Dict[str, Any]) -> bool:
        """Update model data."""
        pass
    
    @abstractmethod
    def delete_model(self, model_id: str) -> bool:
        """Delete model from database."""
        pass
    
    @abstractmethod
    def search_models(self, criteria: Dict[str, Any]) -> List[str]:
        """Search models by criteria."""
        pass
    
    @abstractmethod
    def get_all_models(self) -> List[Dict[str, Any]]:
        """Get all models from database."""
        pass
    
    @abstractmethod
    def add_metadata(self, model_id: str, metadata: Dict[str, Any]) -> bool:
        """Add metadata for a model."""
        pass
    
    @abstractmethod
    def get_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a model."""
        pass
    
    @abstractmethod
    def backup_database(self, backup_path: Path) -> bool:
        """Create database backup."""
        pass
    
    @abstractmethod
    def restore_database(self, backup_path: Path) -> bool:
        """Restore database from backup."""
        pass
```

### IViewerService

```python
from abc import ABC, abstractmethod
from typing import Optional, Any, Tuple
from enum import Enum

class RenderMode(Enum):
    SOLID = "solid"
    WIREFRAME = "wireframe"
    POINTS = "points"

class IViewerService(ABC):
    """Interface for 3D viewer operations."""
    
    @abstractmethod
    def set_model(self, model_id: str) -> bool:
        """Set the model to display in the viewer."""
        pass
    
    @abstractmethod
    def clear_model(self) -> None:
        """Clear the current model from viewer."""
        pass
    
    @abstractmethod
    def set_render_mode(self, mode: RenderMode) -> None:
        """Set the render mode."""
        pass
    
    @abstractmethod
    def get_render_mode(self) -> RenderMode:
        """Get current render mode."""
        pass
    
    @abstractmethod
    def reset_camera(self) -> None:
        """Reset camera to default position."""
        pass
    
    @abstractmethod
    def take_screenshot(self, file_path: Path, width: int = 1920, height: int = 1080) -> bool:
        """Take a screenshot of the viewer."""
        pass
    
    @abstractmethod
    def set_camera_position(self, x: float, y: float, z: float) -> None:
        """Set camera position."""
        pass
    
    @abstractmethod
    def get_camera_position(self) -> Tuple[float, float, float]:
        """Get current camera position."""
        pass
```

## Repository Interfaces

### IModelRepository

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class IModelRepository(ABC):
    """Interface for model data repository operations."""
    
    @abstractmethod
    def create(self, model_data: Dict[str, Any]) -> str:
        """Create a new model record. Returns the model ID."""
        pass
    
    @abstractmethod
    def read(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Read a model record by ID."""
        pass
    
    @abstractmethod
    def update(self, model_id: str, model_data: Dict[str, Any]) -> bool:
        """Update an existing model record."""
        pass
    
    @abstractmethod
    def delete(self, model_id: str) -> bool:
        """Delete a model record."""
        pass
    
    @abstractmethod
    def list_all(self) -> List[Dict[str, Any]]:
        """List all model records."""
        pass
    
    @abstractmethod
    def search(self, criteria: Dict[str, Any]) -> List[str]:
        """Search for models matching criteria."""
        pass
```

### IMetadataRepository

```python
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any

class IMetadataRepository(ABC):
    """Interface for metadata repository operations."""
    
    @abstractmethod
    def add_metadata(self, model_id: str, metadata: Dict[str, Any]) -> bool:
        """Add metadata for a model."""
        pass
    
    @abstractmethod
    def get_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a model."""
        pass
    
    @abstractmethod
    def update_metadata(self, model_id: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for a model."""
        pass
    
    @abstractmethod
    def delete_metadata(self, model_id: str) -> bool:
        """Delete metadata for a model."""
        pass
    
    @abstractmethod
    def search_by_metadata(self, criteria: Dict[str, Any]) -> List[str]:
        """Search models by metadata criteria."""
        pass
```

## Parser Interfaces

### IParser

```python
from abc import ABC, abstractmethod
from typing import Optional, Any, Callable
from pathlib import Path
from enum import Enum

class ModelFormat(Enum):
    STL = "stl"
    OBJ = "obj"
    3MF = "3mf"
    STEP = "step"

class IParser(ABC):
    """Interface for 3D model file parsers."""
    
    @property
    @abstractmethod
    def supported_formats(self) -> List[ModelFormat]:
        """Get list of supported file formats."""
        pass
    
    @abstractmethod
    def can_parse(self, file_path: Path) -> bool:
        """Check if parser can handle the given file."""
        pass
    
    @abstractmethod
    def parse(self, file_path: Path, progress_callback: Optional[Callable] = None) -> Any:
        """Parse a 3D model file."""
        pass
    
    @abstractmethod
    def get_model_info(self, file_path: Path) -> Dict[str, Any]:
        """Get basic information about the model file."""
        pass
```

## Event Interfaces

### IEventPublisher

```python
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict

class IEventPublisher(ABC):
    """Interface for event publishing."""
    
    @abstractmethod
    def subscribe(self, event_type: str, callback: Callable) -> str:
        """Subscribe to an event type. Returns subscription ID."""
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from an event."""
        pass
    
    @abstractmethod
    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event."""
        pass
```

### IEventSubscriber

```python
from abc import ABC, abstractmethod

class IEventSubscriber(ABC):
    """Interface for event subscribers."""
    
    @abstractmethod
    def handle_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Handle an event."""
        pass
```

## Configuration Interfaces

### IConfigurationService

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class IConfigurationService(ABC):
    """Interface for configuration management."""
    
    @abstractmethod
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value."""
        pass
    
    @abstractmethod
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get all configuration values for a section."""
        pass
    
    @abstractmethod
    def save(self) -> bool:
        """Save configuration to persistent storage."""
        pass
    
    @abstractmethod
    def load(self) -> bool:
        """Load configuration from persistent storage."""
        pass
```

## Error Handling Interfaces

### IErrorHandler

```python
from abc import ABC, abstractmethod
from typing import Any, Optional

class IErrorHandler(ABC):
    """Interface for error handling."""
    
    @abstractmethod
    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> bool:
        """Handle an error. Returns True if error was handled successfully."""
        pass
    
    @abstractmethod
    def log_error(self, error: Exception, level: str = "ERROR") -> None:
        """Log an error."""
        pass
    
    @abstractmethod
    def should_retry(self, error: Exception) -> bool:
        """Determine if operation should be retried."""
        pass
```

## Implementation Guidelines

### Interface Design Principles

1. **Single Responsibility**: Each interface should have one clear purpose
2. **Dependency Inversion**: High-level modules depend on abstractions, not concretions
3. **Interface Segregation**: Clients should not depend on interfaces they don't use
4. **Liskov Substitution**: Implementations should be substitutable for their interfaces

### Error Handling Contract

All interface methods should:
- Return `False` or `None` for failed operations when appropriate
- Raise specific exceptions for different error types
- Log errors through the error handling service
- Provide meaningful error messages

### Thread Safety

Interface implementations should:
- Be thread-safe for read operations
- Use proper locking for write operations
- Document thread safety guarantees
- Handle concurrent access gracefully

### Performance Contract

Interface implementations should:
- Meet specified performance requirements
- Provide progress callbacks for long operations
- Support cancellation where applicable
- Optimize for the use case (read-heavy vs write-heavy)

### Testing Contract

Interface implementations should:
- Be testable in isolation
- Support dependency injection for testing
- Provide mock implementations for testing
- Have comprehensive unit tests