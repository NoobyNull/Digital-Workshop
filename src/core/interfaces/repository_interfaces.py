"""Repository interfaces for data access patterns.

This module defines the abstract base classes for repository patterns
used throughout the Candy-Cadence application.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class IModelRepository(ABC):
    """Interface for model data repository operations."""
    
    @abstractmethod
    def create(self, model_data: Dict[str, Any]) -> str:
        """Create a new model record.
        
        Args:
            model_data: Dictionary containing model data
            
        Returns:
            Unique model ID if successful, None otherwise
        """
        pass
    
    @abstractmethod
    def read(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Read a model record by ID.
        
        Args:
            model_id: Unique identifier of the model
            
        Returns:
            Dictionary containing model data, None if not found
        """
        pass
    
    @abstractmethod
    def update(self, model_id: str, model_data: Dict[str, Any]) -> bool:
        """Update an existing model record.
        
        Args:
            model_id: Unique identifier of the model
            model_data: Dictionary containing updated model data
            
        Returns:
            True if update was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, model_id: str) -> bool:
        """Delete a model record.
        
        Args:
            model_id: Unique identifier of the model to delete
            
        Returns:
            True if deletion was successful, False otherwise
        """
        pass
    
    @abstractmethod
    def list_all(self) -> List[Dict[str, Any]]:
        """List all model records.
        
        Returns:
            List of dictionaries containing all model data
        """
        pass
    
    @abstractmethod
    def search(self, criteria: Dict[str, Any]) -> List[str]:
        """Search for models matching criteria.
        
        Args:
            criteria: Dictionary containing search criteria
            
        Returns:
            List of model IDs matching the criteria
        """
        pass
    
    @abstractmethod
    def exists(self, model_id: str) -> bool:
        """Check if a model exists.
        
        Args:
            model_id: Unique identifier of the model
            
        Returns:
            True if model exists, False otherwise
        """
        pass
    
    @abstractmethod
    def count(self) -> int:
        """Get total count of models.
        
        Returns:
            Total number of models in the repository
        """
        pass


class IMetadataRepository(ABC):
    """Interface for metadata repository operations."""
    
    @abstractmethod
    def add_metadata(self, model_id: str, metadata: Dict[str, Any]) -> bool:
        """Add metadata for a model.
        
        Args:
            model_id: Unique identifier of the model
            metadata: Dictionary containing metadata
            
        Returns:
            True if metadata was added successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_metadata(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a model.
        
        Args:
            model_id: Unique identifier of the model
            
        Returns:
            Dictionary containing metadata, None if not found
        """
        pass
    
    @abstractmethod
    def update_metadata(self, model_id: str, metadata: Dict[str, Any]) -> bool:
        """Update metadata for a model.
        
        Args:
            model_id: Unique identifier of the model
            metadata: Dictionary containing updated metadata
            
        Returns:
            True if metadata was updated successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def delete_metadata(self, model_id: str) -> bool:
        """Delete metadata for a model.
        
        Args:
            model_id: Unique identifier of the model
            
        Returns:
            True if metadata was deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def search_by_metadata(self, criteria: Dict[str, Any]) -> List[str]:
        """Search models by metadata criteria.
        
        Args:
            criteria: Dictionary containing metadata search criteria
            
        Returns:
            List of model IDs matching the criteria
        """
        pass
    
    @abstractmethod
    def get_metadata_keys(self, model_id: str) -> List[str]:
        """Get all metadata keys for a model.
        
        Args:
            model_id: Unique identifier of the model
            
        Returns:
            List of metadata key names
        """
        pass
    
    @abstractmethod
    def get_metadata_value(self, model_id: str, key: str) -> Optional[Any]:
        """Get a specific metadata value.
        
        Args:
            model_id: Unique identifier of the model
            key: Metadata key name
            
        Returns:
            Metadata value if found, None otherwise
        """
        pass
    
    @abstractmethod
    def set_metadata_value(self, model_id: str, key: str, value: Any) -> bool:
        """Set a specific metadata value.
        
        Args:
            model_id: Unique identifier of the model
            key: Metadata key name
            value: Metadata value
            
        Returns:
            True if value was set successfully, False otherwise
        """
        pass


class ISearchRepository(ABC):
    """Interface for search operations."""
    
    @abstractmethod
    def search_models(self, query: str, filters: Optional[Dict[str, Any]] = None) -> List[str]:
        """Search for models using text query and filters.
        
        Args:
            query: Text search query
            filters: Optional additional filters
            
        Returns:
            List of model IDs matching the search criteria
        """
        pass
    
    @abstractmethod
    def search_by_tags(self, tags: List[str]) -> List[str]:
        """Search models by tags.
        
        Args:
            tags: List of tag names to search for
            
        Returns:
            List of model IDs containing any of the specified tags
        """
        pass
    
    @abstractmethod
    def search_by_date_range(self, start_date: str, end_date: str) -> List[str]:
        """Search models by date range.
        
        Args:
            start_date: Start date in ISO format
            end_date: End date in ISO format
            
        Returns:
            List of model IDs created within the date range
        """
        pass
    
    @abstractmethod
    def search_by_file_type(self, file_types: List[str]) -> List[str]:
        """Search models by file type.
        
        Args:
            file_types: List of file extensions (e.g., ['.stl', '.obj'])
            
        Returns:
            List of model IDs with matching file types
        """
        pass
    
    @abstractmethod
    def get_search_suggestions(self, partial_query: str) -> List[str]:
        """Get search suggestions for partial query.
        
        Args:
            partial_query: Partial search query
            
        Returns:
            List of suggested search terms
        """
        pass
    
    @abstractmethod
    def save_search(self, name: str, query: str, filters: Dict[str, Any]) -> bool:
        """Save a search query for future use.
        
        Args:
            name: Name for the saved search
            query: Search query string
            filters: Search filters
            
        Returns:
            True if search was saved successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_saved_searches(self) -> List[Dict[str, Any]]:
        """Get all saved searches.
        
        Returns:
            List of dictionaries containing saved search information
        """
        pass
    
    @abstractmethod
    def delete_saved_search(self, search_id: str) -> bool:
        """Delete a saved search.
        
        Args:
            search_id: Unique identifier of the saved search
            
        Returns:
            True if search was deleted successfully, False otherwise
        """
        pass