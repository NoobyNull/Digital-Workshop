"""
Integration tests for tool database management system.

Tests complete workflows including:
- Database initialization and schema creation
- Parser integration with database storage
- Import/export functionality
- Query and search operations
- Multi-format import workflows
"""

import pytest
import sqlite3
import tempfile
import gc
from pathlib import Path

from src.core.database.tool_database_schema import ToolDatabaseSchema
from src.core.database.tool_database_repository import ToolDatabaseRepository
from src.core.database.provider_repository import ProviderRepository
from src.core.database.tool_preferences_repository import ToolPreferencesRepository
from src.parsers.tool_database_manager import ToolDatabaseManager


class TestToolDatabaseIntegration:
    """Integration tests for tool database system."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_tools.db"
            yield str(db_path)
            # Force garbage collection to release database connections
            gc.collect()

    @pytest.fixture
    def tool_manager(self, temp_db):
        """Create tool database manager with temporary database."""
        manager = ToolDatabaseManager(temp_db)
        yield manager

    def test_database_initialization(self, temp_db):
        """Test database schema initialization."""
        schema = ToolDatabaseSchema(temp_db)
        schema.initialize_schema()

        # Verify tables exist (SQLite table names are case-insensitive, stored as lowercase)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        tables = {row[0] for row in cursor.fetchall()}

        # Check for lowercase table names (SQL standard convention)
        assert "providers" in tables
        assert "tools" in tables
        assert "tool_properties" in tables
        assert "preferences" in tables
        conn.close()

    def test_provider_repository_operations(self, temp_db):
        """Test provider repository CRUD operations."""
        ToolDatabaseSchema(temp_db).initialize_schema()
        provider_repo = ProviderRepository(temp_db)

        # Create provider with valid format_type
        provider_id = provider_repo.add_provider(
            name="Test Provider Unique",
            description="Test provider for CRUD operations",
            format_type="CSV"
        )

        assert provider_id is not None

        # Read provider
        provider = provider_repo.get_provider(provider_id)
        assert provider is not None
        assert provider["name"] == "Test Provider Unique"

        # List providers
        providers = provider_repo.list_providers()
        assert len(providers) > 0

        # Update provider
        provider_repo.update_provider(
            provider_id,
            description="Updated description"
        )
        updated = provider_repo.get_provider(provider_id)
        assert updated["description"] == "Updated description"

        # Delete provider
        provider_repo.delete_provider(provider_id)
        deleted = provider_repo.get_provider(provider_id)
        assert deleted is None

    def test_tool_repository_operations(self, temp_db):
        """Test tool repository CRUD operations."""
        ToolDatabaseSchema(temp_db).initialize_schema()
        tool_repo = ToolDatabaseRepository(temp_db)
        provider_repo = ProviderRepository(temp_db)

        # Create provider first
        provider_id = provider_repo.add_provider(
            name="Test Provider",
            description="Test",
            format_type="CSV"
        )

        # Create tool
        tool_id = tool_repo.add_tool(
            provider_id=provider_id,
            guid="tool-123",
            description="Test Tool",
            tool_type="EndMill",
            diameter=3.175,
            vendor="Carbide",
            geometry_data={},
            start_values={}
        )

        assert tool_id is not None

        # Read tool
        tool = tool_repo.get_tool(tool_id)
        assert tool is not None
        assert tool["description"] == "Test Tool"
        assert tool["diameter"] == 3.175

        # List tools
        tools = tool_repo.list_tools()
        assert len(tools) > 0

        # Search tools
        results = tool_repo.search_tools(tool_type="EndMill")
        assert len(results) > 0

        # Filter by diameter
        results = tool_repo.filter_by_diameter(min_diameter=3.0, max_diameter=4.0)
        assert len(results) > 0

        # Update tool
        tool_repo.update_tool(tool_id, description="Updated Tool")
        updated = tool_repo.get_tool(tool_id)
        assert updated["description"] == "Updated Tool"

        # Delete tool
        tool_repo.delete_tool(tool_id)
        deleted = tool_repo.get_tool(tool_id)
        assert deleted is None

    def test_tool_properties_storage(self, temp_db):
        """Test tool properties storage and retrieval."""
        ToolDatabaseSchema(temp_db).initialize_schema()
        tool_repo = ToolDatabaseRepository(temp_db)
        provider_repo = ProviderRepository(temp_db)

        provider_id = provider_repo.add_provider(
            name="Test Provider",
            description="Test",
            format_type="CSV"
        )

        tool_id = tool_repo.add_tool(
            provider_id=provider_id,
            guid="tool-456",
            description="Tool with properties",
            tool_type="Drill",
            diameter=2.0,
            vendor="Test",
            geometry_data={},
            start_values={}
        )

        # Add custom properties
        properties = {
            "flute_count": 2,
            "material": "carbide",
            "max_rpm": 24000,
            "tags": ["HSS", "roughing"]
        }

        tool_repo.add_tool_properties(tool_id, properties)

        # Retrieve properties
        retrieved = tool_repo.get_tool_properties(tool_id)
        assert retrieved is not None
        assert retrieved["flute_count"] == 2
        assert retrieved["material"] == "carbide"

    def test_preferences_storage(self, temp_db):
        """Test preferences storage and retrieval."""
        ToolDatabaseSchema(temp_db).initialize_schema()
        prefs_repo = ToolPreferencesRepository(temp_db)

        # Store preference
        prefs_repo.set_preference(
            key="external_db_paths",
            value={"csv": "/path/to/csv", "json": "/path/to/json"}
        )

        # Retrieve preference
        value = prefs_repo.get_preference("external_db_paths")
        assert value is not None
        assert value["csv"] == "/path/to/csv"

        # Update preference
        updated_value = {"csv": "/new/path", "json": "/path/to/json"}
        prefs_repo.set_preference("external_db_paths", updated_value)

        retrieved = prefs_repo.get_preference("external_db_paths")
        assert retrieved["csv"] == "/new/path"

        # Delete preference
        prefs_repo.delete_preference("external_db_paths")
        deleted = prefs_repo.get_preference("external_db_paths")
        assert deleted is None

    def test_tool_manager_initialization(self, tool_manager):
        """Test tool manager initialization and parser registration."""
        assert tool_manager.db_path is not None
        assert tool_manager.tool_repo is not None
        assert tool_manager.provider_repo is not None
        assert tool_manager.preferences_repo is not None

        # Verify parsers are registered
        assert "CSV" in tool_manager.parsers
        assert "JSON" in tool_manager.parsers
        assert "VTDB" in tool_manager.parsers
        assert "TDB" in tool_manager.parsers

    def test_complete_import_workflow(self, temp_db):
        """Test complete workflow: schema init -> provider create -> tool import."""
        # Initialize schema
        schema = ToolDatabaseSchema(temp_db)
        schema.initialize_schema()

        # Create manager
        manager = ToolDatabaseManager(temp_db)

        # Create provider
        provider_id = manager.provider_repo.add_provider(
            name="Test Provider",
            description="Complete workflow test",
            format_type="CSV"
        )

        # Simulate tool data
        from src.parsers.tool_parsers import ToolData
        tool_data = ToolData(
            guid="tool-789",
            description="Test Tool",
            tool_type="EndMill",
            diameter=6.35,
            vendor="Test Vendor",
            geometry_data={},
            start_values={}
        )

        # Store tool
        tool_id = manager.tool_repo.add_tool(
            provider_id=provider_id,
            guid=tool_data.guid,
            description=tool_data.description,
            tool_type=tool_data.tool_type,
            diameter=tool_data.diameter,
            vendor=tool_data.vendor,
            geometry_data=tool_data.geometry_data,
            start_values=tool_data.start_values
        )

        # Verify tool was stored
        stored_tool = manager.tool_repo.get_tool(tool_id)
        assert stored_tool is not None
        assert stored_tool["guid"] == "tool-789"

        # Verify provider relationship
        provider_tools = manager.tool_repo.list_tools_for_provider(provider_id)
        assert len(provider_tools) > 0

    def test_search_and_filter_workflow(self, temp_db):
        """Test search and filter workflow."""
        schema = ToolDatabaseSchema(temp_db)
        schema.initialize_schema()

        manager = ToolDatabaseManager(temp_db)

        # Create provider
        provider_id = manager.provider_repo.add_provider(
            name="Search Test Provider",
            description="Testing search",
            format_type="CSV"
        )

        # Add multiple tools
        tools_data = [
            ("tool-1", "EndMill 3mm", "EndMill", 3.0),
            ("tool-2", "EndMill 6mm", "EndMill", 6.0),
            ("tool-3", "Drill 2mm", "Drill", 2.0),
        ]

        for guid, desc, tool_type, diameter in tools_data:
            manager.tool_repo.add_tool(
                provider_id=provider_id,
                guid=guid,
                description=desc,
                tool_type=tool_type,
                diameter=diameter,
                vendor="Test",
                geometry_data={},
                start_values={}
            )

        # Search by type
        endmills = manager.tool_repo.search_tools(tool_type="EndMill")
        assert len(endmills) == 2

        # Filter by diameter
        small_tools = manager.tool_repo.filter_by_diameter(min_diameter=0, max_diameter=3.5)
        assert len(small_tools) >= 2

        # Search by description
        search_results = manager.tool_repo.search_tools_by_description("EndMill 6mm")
        assert len(search_results) > 0

    def test_multi_provider_workflow(self, temp_db):
        """Test workflow with multiple providers."""
        schema = ToolDatabaseSchema(temp_db)
        schema.initialize_schema()

        manager = ToolDatabaseManager(temp_db)

        # Create multiple providers
        provider_ids = []
        for i in range(3):
            provider_id = manager.provider_repo.add_provider(
                name=f"Provider {i}",
                description=f"Provider {i} description",
                format_type="CSV" if i % 2 == 0 else "JSON"
            )
            provider_ids.append(provider_id)

        # Add tools to each provider
        for idx, provider_id in enumerate(provider_ids):
            for j in range(2):
                manager.tool_repo.add_tool(
                    provider_id=provider_id,
                    guid=f"tool-p{idx}-t{j}",
                    description=f"Tool {j} for provider {idx}",
                    tool_type="EndMill",
                    diameter=3.0 + j,
                    vendor="Test",
                    geometry_data={},
                    start_values={}
                )

        # Verify tools per provider
        for idx, provider_id in enumerate(provider_ids):
            provider_tools = manager.tool_repo.list_tools_for_provider(provider_id)
            assert len(provider_tools) == 2

        # Verify total tools
        all_tools = manager.tool_repo.list_tools()
        assert len(all_tools) == 6


class TestToolDatabaseMemoryManagement:
    """Tests for memory management during database operations."""

    @pytest.fixture
    def temp_db(self):
        """Create temporary database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "memory_test.db"
            yield str(db_path)
            # Force garbage collection to release database connections
            gc.collect()

    def test_repeated_operations_no_memory_leak(self, temp_db):
        """Test that repeated operations don't leak memory."""
        schema = ToolDatabaseSchema(temp_db)
        schema.initialize_schema()

        manager = ToolDatabaseManager(temp_db)

        # Create provider
        provider_id = manager.provider_repo.add_provider(
            name="Memory Test",
            description="Testing memory",
            format_type="CSV"
        )

        # Perform many operations
        for iteration in range(10):
            tool_id = manager.tool_repo.add_tool(
                provider_id=provider_id,
                guid=f"tool-mem-{iteration}",
                description=f"Memory test tool {iteration}",
                tool_type="EndMill",
                diameter=3.0,
                vendor="Test",
                geometry_data={},
                start_values={}
            )

            # Retrieve tool
            tool = manager.tool_repo.get_tool(tool_id)
            assert tool is not None

            # Search
            results = manager.tool_repo.search_tools(tool_type="EndMill")
            assert len(results) > 0

            # Delete tool
            manager.tool_repo.delete_tool(tool_id)

        # Verify cleanup
        remaining_tools = manager.tool_repo.list_tools()
        assert len(remaining_tools) == 0

    def test_large_batch_operations(self, temp_db):
        """Test performance with large batch operations."""
        schema = ToolDatabaseSchema(temp_db)
        schema.initialize_schema()

        manager = ToolDatabaseManager(temp_db)

        provider_id = manager.provider_repo.add_provider(
            name="Batch Test",
            description="Testing batch operations",
            format_type="CSV"
        )

        # Add many tools
        tool_count = 100
        for i in range(tool_count):
            manager.tool_repo.add_tool(
                provider_id=provider_id,
                guid=f"batch-tool-{i}",
                description=f"Batch tool {i}",
                tool_type="EndMill" if i % 2 == 0 else "Drill",
                diameter=2.0 + (i % 5),
                vendor="Test",
                geometry_data={},
                start_values={}
            )

        # Verify all tools were added
        all_tools = manager.tool_repo.list_tools()
        assert len(all_tools) == tool_count

        # Verify search works with large dataset
        endmills = manager.tool_repo.search_tools(tool_type="EndMill")
        assert len(endmills) == tool_count // 2
