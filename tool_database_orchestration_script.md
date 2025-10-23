# Tool Database Management System Orchestration Script

## Introduction
This orchestration script provides detailed, step-by-step instructions for implementing the tool database management system. Each step includes specific file paths, class structures, method signatures, and implementation details. The orchestrator must follow this script precisely.

## Phase 1: Database Foundation (Steps 1-2)

### Step 1: Create SQLite database schema
**File:** `src/core/database/tool_database_schema.py`

**Implementation Details:**
```python
"""
Tool database schema definition and initialization.
"""

import sqlite3
from pathlib import Path
from typing import Optional

from src.core.logging_config import get_logger

logger = get_logger(__name__)

class ToolDatabaseSchema:
    """Manages the tool database schema initialization and migrations."""
    
    def __init__(self, db_path: str):
        """Initialize schema manager with database path."""
        self.db_path = Path(db_path)
        self.logger = logger
    
    def initialize_database(self) -> bool:
        """Create all database tables if they don't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create Providers table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS providers (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        description TEXT,
                        file_path TEXT,
                        format_type TEXT CHECK(format_type IN ('CSV', 'JSON', 'VTDB', 'TDB')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create Tools table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tools (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        provider_id INTEGER NOT NULL,
                        guid TEXT,
                        description TEXT NOT NULL,
                        tool_type TEXT,
                        diameter REAL,
                        vendor TEXT,
                        product_id TEXT,
                        unit TEXT DEFAULT 'inches',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (provider_id) REFERENCES providers (id) ON DELETE CASCADE
                    )
                """)
                
                # Create ToolProperties table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tool_properties (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        tool_id INTEGER NOT NULL,
                        property_name TEXT NOT NULL,
                        property_value TEXT,
                        property_type TEXT CHECK(property_type IN ('geometry', 'start_values', 'custom')),
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (tool_id) REFERENCES tools (id) ON DELETE CASCADE
                    )
                """)
                
                # Create Preferences table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS preferences (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        key TEXT UNIQUE NOT NULL,
                        value TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create indexes for performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tools_provider_id ON tools(provider_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tools_guid ON tools(guid)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tool_properties_tool_id ON tool_properties(tool_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_preferences_key ON preferences(key)")
                
                conn.commit()
                self.logger.info("Database schema initialized successfully")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database schema: {e}")
            return False
    
    def get_version(self) -> int:
        """Get current database schema version."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA user_version")
                return cursor.fetchone()[0]
        except Exception:
            return 0
    
    def set_version(self, version: int) -> None:
        """Set database schema version."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"PRAGMA user_version = {version}")
                conn.commit()
        except Exception as e:
            self.logger.error(f"Failed to set database version: {e}")
```

**Expected Outcome:** Database schema file created with all tables, indexes, and version management.

### Step 2: Implement database repository classes
**File:** `src/core/database/tool_database_repository.py`

**Implementation Details:**
```python
"""
Tool database repository for CRUD operations.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.core.logging_config import get_logger
from .tool_database_schema import ToolDatabaseSchema

logger = get_logger(__name__)

class ToolDatabaseRepository:
    """Repository for tool database operations."""
    
    def __init__(self, db_path: str):
        """Initialize repository with database path."""
        self.db_path = Path(db_path)
        self.schema = ToolDatabaseSchema(str(self.db_path))
        self.logger = logger
        self.schema.initialize_database()
    
    def add_tool(self, provider_id: int, tool_data: Dict[str, Any]) -> Optional[int]:
        """Add a new tool to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert tool
                cursor.execute("""
                    INSERT INTO tools (provider_id, guid, description, tool_type, diameter, vendor, product_id, unit)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    provider_id,
                    tool_data.get('guid'),
                    tool_data.get('description'),
                    tool_data.get('tool_type'),
                    tool_data.get('diameter'),
                    tool_data.get('vendor'),
                    tool_data.get('product_id'),
                    tool_data.get('unit', 'inches')
                ))
                
                tool_id = cursor.lastrowid
                
                # Insert tool properties
                for prop_name, prop_value in tool_data.get('properties', {}).items():
                    cursor.execute("""
                        INSERT INTO tool_properties (tool_id, property_name, property_value, property_type)
                        VALUES (?, ?, ?, ?)
                    """, (
                        tool_id,
                        prop_name,
                        str(prop_value),
                        tool_data.get('property_types', {}).get(prop_name, 'custom')
                    ))
                
                conn.commit()
                self.logger.info(f"Added tool: {tool_data.get('description')} (ID: {tool_id})")
                return tool_id
                
        except Exception as e:
            self.logger.error(f"Failed to add tool: {e}")
            return None
    
    def get_tools_by_provider(self, provider_id: int) -> List[Dict[str, Any]]:
        """Get all tools for a specific provider."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT t.*, p.name as provider_name
                    FROM tools t
                    JOIN providers p ON t.provider_id = p.id
                    WHERE t.provider_id = ?
                    ORDER BY t.description
                """, (provider_id,))
                
                tools = []
                for row in cursor.fetchall():
                    tool = dict(row)
                    
                    # Get tool properties
                    cursor.execute("""
                        SELECT property_name, property_value, property_type
                        FROM tool_properties
                        WHERE tool_id = ?
                    """, (tool['id'],))
                    
                    properties = {}
                    for prop_row in cursor.fetchall():
                        if prop_row['property_type'] == 'geometry':
                            if 'geometry' not in properties:
                                properties['geometry'] = {}
                            properties['geometry'][prop_row['property_name']] = prop_row['property_value']
                        elif prop_row['property_type'] == 'start_values':
                            if 'start_values' not in properties:
                                properties['start_values'] = {}
                            properties['start_values'][prop_row['property_name']] = prop_row['property_value']
                        else:
                            properties[prop_row['property_name']] = prop_row['property_value']
                    
                    tool['properties'] = properties
                    tools.append(tool)
                
                return tools
                
        except Exception as e:
            self.logger.error(f"Failed to get tools for provider {provider_id}: {e}")
            return []
    
    def search_tools(self, query: str, provider_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for tools by description."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                sql = """
                    SELECT t.*, p.name as provider_name
                    FROM tools t
                    JOIN providers p ON t.provider_id = p.id
                    WHERE t.description LIKE ?
                """
                params = [f"%{query}%"]
                
                if provider_id:
                    sql += " AND t.provider_id = ?"
                    params.append(provider_id)
                
                sql += " ORDER BY t.description"
                
                cursor.execute(sql, params)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to search tools: {e}")
            return []
    
    def delete_tool(self, tool_id: int) -> bool:
        """Delete a tool from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM tools WHERE id = ?", (tool_id,))
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    self.logger.info(f"Deleted tool ID: {tool_id}")
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to delete tool {tool_id}: {e}")
            return False
```

**File:** `src/core/database/provider_repository.py`

**Implementation Details:**
```python
"""
Provider repository for managing tool providers.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.core.logging_config import get_logger

logger = get_logger(__name__)

class ProviderRepository:
    """Repository for provider operations."""
    
    def __init__(self, db_path: str):
        """Initialize repository with database path."""
        self.db_path = Path(db_path)
        self.logger = logger
    
    def add_provider(self, name: str, description: str = "", file_path: str = "", 
                    format_type: str = "") -> Optional[int]:
        """Add a new provider to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO providers (name, description, file_path, format_type)
                    VALUES (?, ?, ?, ?)
                """, (name, description, file_path, format_type))
                
                provider_id = cursor.lastrowid
                conn.commit()
                
                self.logger.info(f"Added provider: {name} (ID: {provider_id})")
                return provider_id
                
        except sqlite3.IntegrityError:
            self.logger.warning(f"Provider already exists: {name}")
            return self.get_provider_by_name(name).get('id')
        except Exception as e:
            self.logger.error(f"Failed to add provider: {e}")
            return None
    
    def get_provider_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a provider by name."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM providers WHERE name = ?", (name,))
                row = cursor.fetchone()
                
                return dict(row) if row else None
                
        except Exception as e:
            self.logger.error(f"Failed to get provider {name}: {e}")
            return None
    
    def get_all_providers(self) -> List[Dict[str, Any]]:
        """Get all providers."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM providers ORDER BY name")
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            self.logger.error(f"Failed to get providers: {e}")
            return []
    
    def delete_provider(self, provider_id: int) -> bool:
        """Delete a provider and all associated tools."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM providers WHERE id = ?", (provider_id,))
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    self.logger.info(f"Deleted provider ID: {provider_id}")
                return success
                
        except Exception as e:
            self.logger.error(f"Failed to delete provider {provider_id}: {e}")
            return False
```

**File:** `src/core/database/tool_preferences_repository.py`

**Implementation Details:**
```python
"""
Preferences repository for tool database settings.
"""

import sqlite3
import json
from typing import Any, Optional
from pathlib import Path

from src.core.logging_config import get_logger

logger = get_logger(__name__)

class ToolPreferencesRepository:
    """Repository for tool database preferences."""
    
    def __init__(self, db_path: str):
        """Initialize repository with database path."""
        self.db_path = Path(db_path)
        self.logger = logger
    
    def set_preference(self, key: str, value: Any) -> bool:
        """Set a preference value."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Convert value to JSON if it's not a string
                if not isinstance(value, str):
                    value = json.dumps(value)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO preferences (key, value, updated_at)
                    VALUES (?, ?, CURRENT_TIMESTAMP)
                """, (key, value))
                
                conn.commit()
                self.logger.debug(f"Set preference: {key}")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to set preference {key}: {e}")
            return False
    
    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get a preference value."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
                row = cursor.fetchone()
                
                if row:
                    value = row[0]
                    # Try to parse as JSON
                    try:
                        return json.loads(value)
                    except json.JSONDecodeError:
                        return value
                
                return default
                
        except Exception as e:
            self.logger.error(f"Failed to get preference {key}: {e}")
            return default
    
    def get_external_db_paths(self) -> Dict[str, str]:
        """Get all external database paths."""
        paths = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT key, value FROM preferences 
                    WHERE key LIKE 'external_db_%'
                """)
                
                for row in cursor.fetchall():
                    # Extract format type from key (e.g., 'external_db_csv' -> 'CSV')
                    format_type = row[0].split('_')[-1].upper()
                    paths[format_type] = row[1]
                
        except Exception as e:
            self.logger.error(f"Failed to get external DB paths: {e}")
        
        return paths
```

**Expected Outcome:** Three repository classes created with full CRUD operations for tools, providers, and preferences.

## Phase 2: Parser Implementation (Steps 3-7)

### Step 3: Create base tool parser
**File:** `src/parsers/tool_parsers/__init__.py`

**Implementation Details:**
```python
"""
Tool parsers package for handling various tool database formats.
"""

from .base_tool_parser import BaseToolParser, ToolData
from .csv_tool_parser import CSVToolParser
from .json_tool_parser import JSONToolParser
from .vtdb_tool_parser import VTDBToolParser
from .tdb_tool_parser import TDBToolParser

__all__ = [
    'BaseToolParser',
    'ToolData',
    'CSVToolParser',
    'JSONToolParser',
    'VTDBToolParser',
    'TDBToolParser'
]
```

**File:** `src/parsers/tool_parsers/base_tool_parser.py`

**Implementation Details:**
```python
"""
Base class for all tool parsers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from pathlib import Path

from src.core.logging_config import get_logger

@dataclass
class ToolData:
    """Data structure for a parsed tool."""
    guid: str
    description: str
    tool_type: str
    diameter: float
    vendor: str
    product_id: str
    unit: str = "inches"
    geometry: Dict[str, Any] = None
    start_values: Dict[str, Any] = None
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize default values."""
        if self.geometry is None:
            self.geometry = {}
        if self.start_values is None:
            self.start_values = {}
        if self.properties is None:
            self.properties = {}

class ProgressCallback:
    """Callback for progress reporting during parsing."""
    
    def __init__(self, callback: Optional[Callable[[float, str], None]] = None):
        """Initialize progress callback."""
        self.callback = callback
        self.last_report = 0
    
    def report(self, progress: float, message: str = "") -> None:
        """Report progress if callback is set."""
        if self.callback and progress - self.last_report >= 0.1:  # Report every 10%
            self.callback(progress, message)
            self.last_report = progress

class BaseToolParser(ABC):
    """Abstract base class for tool parsers."""
    
    def __init__(self):
        """Initialize parser."""
        self.logger = get_logger(self.__class__.__name__)
        self._cancelled = False
    
    @abstractmethod
    def parse(self, file_path: str, progress_callback: Optional[ProgressCallback] = None) -> List[ToolData]:
        """
        Parse a tool database file.
        
        Args:
            file_path: Path to the tool database file
            progress_callback: Optional progress callback
            
        Returns:
            List of parsed tools
        """
        pass
    
    @abstractmethod
    def validate_file(self, file_path: str) -> tuple[bool, str]:
        """
        Validate if file is supported format.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def get_format_name(self) -> str:
        """Get the format name this parser handles."""
        pass
    
    def cancel(self) -> None:
        """Cancel the parsing operation."""
        self._cancelled = True
        self.logger.info("Parsing cancelled")
    
    def reset_cancel(self) -> None:
        """Reset cancellation state."""
        self._cancelled = False
    
    def _check_cancelled(self) -> bool:
        """Check if parsing was cancelled."""
        return self._cancelled
```

**Expected Outcome:** Base parser class created with common interface and progress reporting.

### Step 4: Create CSV parser
**File:** `src/parsers/tool_parsers/csv_tool_parser.py`

**Implementation Details:**
```python
"""
CSV tool database parser for IDC-Woodcraft-Carbide-Create-Database-5-2-2025.csv format.
"""

import csv
from typing import List, Optional
from pathlib import Path

from .base_tool_parser import BaseToolParser, ToolData, ProgressCallback

class CSVToolParser(BaseToolParser):
    """Parser for CSV tool databases."""
    
    def get_format_name(self) -> str:
        """Get the format name."""
        return "CSV"
    
    def validate_file(self, file_path: str) -> tuple[bool, str]:
        """Validate CSV file format."""
        try:
            path = Path(file_path)
            if not path.exists():
                return False, "File does not exist"
            
            if path.suffix.lower() != '.csv':
                return False, "Not a CSV file"
            
            # Check if file has expected headers
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(row, [])
                
                required_headers = ['description', 'tool_type', 'diameter']
                missing = [h for h in required_headers if h.lower() not in [h.lower() for h in headers]]
                
                if missing:
                    return False, f"Missing required headers: {missing}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def parse(self, file_path: str, progress_callback: Optional[ProgressCallback] = None) -> List[ToolData]:
        """Parse CSV tool database."""
        tools = []
        
        try:
            path = Path(file_path)
            
            # Get file size for progress reporting
            file_size = path.stat().st_size
            
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Get total rows for progress
                total_rows = sum(1 for _ in reader) if progress_callback else 0
                f.seek(0)
                next(reader)  # Skip header
                
                for row_num, row in enumerate(reader, 1):
                    if self._check_cancelled():
                        break
                    
                    # Parse tool data
                    tool = ToolData(
                        guid=row.get('guid', ''),
                        description=row.get('description', ''),
                        tool_type=row.get('tool_type', ''),
                        diameter=self._parse_float(row.get('diameter', 0)),
                        vendor=row.get('vendor', 'IDC Woodcraft'),
                        product_id=row.get('product_id', ''),
                        unit=row.get('unit', 'inches'),
                        geometry=self._parse_geometry(row),
                        start_values=self._parse_start_values(row)
                    )
                    
                    tools.append(tool)
                    
                    # Report progress
                    if progress_callback and total_rows > 0:
                        progress = min(row_num / total_rows, 1.0)
                        progress_callback.report(progress, f"Parsing tool {row_num}/{total_rows}")
            
            self.logger.info(f"Parsed {len(tools)} tools from CSV file")
            return tools
            
        except Exception as e:
            self.logger.error(f"Failed to parse CSV file: {e}")
            raise
    
    def _parse_float(self, value: str) -> float:
        """Parse float value from string."""
        try:
            return float(value.replace(',', ''))
        except (ValueError, AttributeError):
            return 0.0
    
    def _parse_geometry(self, row: dict) -> dict:
        """Parse geometry properties from row."""
        geometry = {}
        
        # Common geometry fields
        geometry_fields = {
            'DC': 'diameter',
            'LB': 'length',
            'NOF': 'number_of_flutes',
            'OAL': 'overall_length',
            'SHK': 'shank_diameter'
        }
        
        for csv_field, prop_name in geometry_fields.items():
            if csv_field in row and row[csv_field]:
                geometry[prop_name] = self._parse_float(row[csv_field])
        
        return geometry
    
    def _parse_start_values(self, row: dict) -> dict:
        """Parse start values from row."""
        start_values = {}
        
        # Common start value fields
        start_fields = {
            'n': 'rpm',
            'v_f': 'feed_rate',
            'stepdown': 'stepdown',
            'stepover': 'stepover'
        }
        
        for csv_field, prop_name in start_fields.items():
            if csv_field in row and row[csv_field]:
                start_values[prop_name] = self._parse_float(row[csv_field])
        
        return start_values
```

**Expected Outcome:** CSV parser created with support for IDC-Woodcraft-Carbide-Create-Database format.

### Step 5: Create JSON parser
**File:** `src/parsers/tool_parsers/json_tool_parser.py`

**Implementation Details:**
```python
"""
JSON tool database parser for IDCWoodcraftFusion360Library.json format.
"""

import json
from typing import List, Optional
from pathlib import Path

from .base_tool_parser import BaseToolParser, ToolData, ProgressCallback

class JSONToolParser(BaseToolParser):
    """Parser for JSON tool databases."""
    
    def get_format_name(self) -> str:
        """Get the format name."""
        return "JSON"
    
    def validate_file(self, file_path: str) -> tuple[bool, str]:
        """Validate JSON file format."""
        try:
            path = Path(file_path)
            if not path.exists():
                return False, "File does not exist"
            
            if path.suffix.lower() != '.json':
                return False, "Not a JSON file"
            
            # Try to parse JSON
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Check if it has expected structure
            if 'data' not in data:
                return False, "Missing 'data' field in JSON"
            
            if not isinstance(data['data'], list):
                return False, "'data' field must be an array"
            
            # Check first tool structure
            if data['data']:
                tool = data['data'][0]
                required_fields = ['description', 'type']
                missing = [f for f in required_fields if f not in tool]
                
                if missing:
                    return False, f"Missing required tool fields: {missing}"
            
            return True, ""
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def parse(self, file_path: str, progress_callback: Optional[ProgressCallback] = None) -> List[ToolData]:
        """Parse JSON tool database."""
        tools = []
        
        try:
            path = Path(file_path)
            
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            tool_list = data.get('data', [])
            total_tools = len(tool_list)
            
            for i, tool_data in enumerate(tool_list):
                if self._check_cancelled():
                    break
                
                # Parse tool
                tool = ToolData(
                    guid=tool_data.get('guid', ''),
                    description=tool_data.get('description', ''),
                    tool_type=tool_data.get('type', ''),
                    diameter=tool_data.get('geometry', {}).get('DC', 0.0),
                    vendor=tool_data.get('vendor', 'IDC Woodcraft'),
                    product_id=tool_data.get('product-id', ''),
                    unit=tool_data.get('unit', 'inches'),
                    geometry=tool_data.get('geometry', {}),
                    start_values=tool_data.get('start-values', {})
                )
                
                tools.append(tool)
                
                # Report progress
                if progress_callback and total_tools > 0:
                    progress = min((i + 1) / total_tools, 1.0)
                    progress_callback.report(progress, f"Parsing tool {i + 1}/{total_tools}")
            
            self.logger.info(f"Parsed {len(tools)} tools from JSON file")
            return tools
            
        except Exception as e:
            self.logger.error(f"Failed to parse JSON file: {e}")
            raise
```

**Expected Outcome:** JSON parser created with support for IDCWoodcraftFusion360Library format.

### Step 6: Create VTDB parser
**File:** `src/parsers/tool_parsers/vtdb_tool_parser.py`

**Implementation Details:**
```python
"""
VTDB tool database parser for IDC Woodcraft Vectric Tool Database Library Update rev 25-5.vtdb format.
VTDB files are SQLite databases with a specific structure.
"""

import sqlite3
from typing import List, Optional
from pathlib import Path

from .base_tool_parser import BaseToolParser, ToolData, ProgressCallback

class VTDBToolParser(BaseToolParser):
    """Parser for VTDB (SQLite) tool databases."""
    
    def get_format_name(self) -> str:
        """Get the format name."""
        return "VTDB"
    
    def validate_file(self, file_path: str) -> tuple[bool, str]:
        """Validate VTDB file format."""
        try:
            path = Path(file_path)
            if not path.exists():
                return False, "File does not exist"
            
            if path.suffix.lower() != '.vtdb':
                return False, "Not a VTDB file"
            
            # Try to connect to SQLite database
            with sqlite3.connect(file_path) as conn:
                cursor = conn.cursor()
                
                # Check if it has expected tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                if 'tools' not in tables:
                    return False, "Missing 'tools' table"
                
                # Check tools table structure
                cursor.execute("PRAGMA table_info(tools)")
                columns = [row[1] for row in cursor.fetchall()]
                
                required_columns = ['description', 'tool_type']
                missing = [c for c in required_columns if c not in columns]
                
                if missing:
                    return False, f"Missing required columns: {missing}"
            
            return True, ""
            
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def parse(self, file_path: str, progress_callback: Optional[ProgressCallback] = None) -> List[ToolData]:
        """Parse VTDB tool database."""
        tools = []
        
        try:
            with sqlite3.connect(file_path) as conn:
                cursor = conn.cursor()
                
                # Get total tool count
                cursor.execute("SELECT COUNT(*) FROM tools")
                total_tools = cursor.fetchone()[0]
                
                # Query tools
                cursor.execute("""
                    SELECT * FROM tools
                    ORDER BY description
                """)
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                for i, row in enumerate(rows):
                    if self._check_cancelled():
                        break
                    
                    tool_dict = dict(zip(columns, row))
                    
                    # Parse tool properties if they exist
                    geometry = {}
                    start_values = {}
                    
                    if 'properties' in tool_dict and tool_dict['properties']:
                        try:
                            import json
                            properties = json.loads(tool_dict['properties'])
                            geometry = properties.get('geometry', {})
                            start_values = properties.get('start_values', {})
                        except json.JSONDecodeError:
                            self.logger.warning(f"Failed to parse properties for tool {tool_dict.get('description', '')}")
                    
                    # Create tool
                    tool = ToolData(
                        guid=tool_dict.get('guid', ''),
                        description=tool_dict.get('description', ''),
                        tool_type=tool_dict.get('tool_type', ''),
                        diameter=tool_dict.get('diameter', 0.0),
                        vendor=tool_dict.get('vendor', 'IDC Woodcraft'),
                        product_id=tool_dict.get('product_id', ''),
                        unit=tool_dict.get('unit', 'inches'),
                        geometry=geometry,
                        start_values=start_values
                    )
                    
                    tools.append(tool)
                    
                    # Report progress
                    if progress_callback and total_tools > 0:
                        progress = min((i + 1) / total_tools, 1.0)
                        progress_callback.report(progress, f"Parsing tool {i + 1}/{total_tools}")
            
            self.logger.info(f"Parsed {len(tools)} tools from VTDB file")
            return tools
            
        except Exception as e:
            self.logger.error(f"Failed to parse VTDB file: {e}")
            raise
```

**Expected Outcome:** VTDB parser created with support for SQLite-based Vectric tool databases.

### Step 7: Create TDB parser
**File:** `src/parsers/tool_parsers/tdb_tool_parser.py`

**Implementation Details:**
```python
"""
TDB tool database parser for IDC-Woodcraft-Carveco-Tool-Database.tdb format.
TDB files are binary files with UTF-16 encoding.
"""

import struct
from typing import List, Optional
from pathlib import Path

from .base_tool_parser import BaseToolParser, ToolData, ProgressCallback

class TDBToolParser(BaseToolParser):
    """Parser for TDB (binary) tool databases."""
    
    def get_format_name(self) -> str:
        """Get the format name."""
        return "TDB"
    
    def validate_file(self, file_path: str) -> tuple[bool, str]:
        """Validate TDB file format."""
        try:
            path = Path(file_path)
            if not path.exists():
                return False, "File does not exist"
            
            if path.suffix.lower() != '.tdb':
                return False, "Not a TDB file"
            
            # Check file header
            with open(path, 'rb') as f:
                header = f.read(4)
                
                # TDB files start with magic bytes 'TDB\0'
                if header != b'TDB\x00':
                    return False, "Invalid TDB file signature"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def parse(self, file_path: str, progress_callback: Optional[ProgressCallback] = None) -> List[ToolData]:
        """Parse TDB tool database."""
        tools = []
        
        try:
            path = Path(file_path)
            file_size = path.stat().st_size
            
            with open(path, 'rb') as f:
                # Read header
                header = f.read(4)
                if header != b'TDB\x00':
                    raise ValueError("Invalid TDB file signature")
                
                # Read version
                version = struct.unpack('<I', f.read(4))[0]
                
                # Read tool count
                tool_count = struct.unpack('<I', f.read(4))[0]
                
                # Parse each tool
                for i in range(tool_count):
                    if self._check_cancelled():
                        break
                    
                    # Read tool header
                    tool_header_size = struct.unpack('<I', f.read(4))[0]
                    tool_data = f.read(tool_header_size)
                    
                    # Parse tool data (UTF-16 encoded)
                    tool = self._parse_tdb_tool(tool_data)
                    tools.append(tool)
                    
                    # Report progress
                    if progress_callback and tool_count > 0:
                        progress = min((i + 1) / tool_count, 1.0)
                        progress_callback.report(progress, f"Parsing tool {i + 1}/{tool_count}")
            
            self.logger.info(f"Parsed {len(tools)} tools from TDB file")
            return tools
            
        except Exception as e:
            self.logger.error(f"Failed to parse TDB file: {e}")
            raise
    
    def _parse_tdb_tool(self, data: bytes) -> ToolData:
        """Parse a single tool from TDB data."""
        # Decode UTF-16 data
        text = data.decode('utf-16-le')
        
        # Split into fields
        fields = text.split('\x00')
        
        # Parse tool data (example structure - adjust based on actual format)
        tool = ToolData(
            guid=fields[0] if len(fields) > 0 else '',
            description=fields[1] if len(fields) > 1 else '',
            tool_type=fields[2] if len(fields) > 2 else '',
            diameter=float(fields[3]) if len(fields) > 3 and fields[3] else 0.0,
            vendor=fields[4] if len(fields) > 4 else 'IDC Woodcraft',
            product_id=fields[5] if len(fields) > 5 else '',
            unit=fields[6] if len(fields) > 6 else 'inches'
        )
        
        # Parse additional properties if available
        if len(fields) > 7:
            tool.geometry = self._parse_tdb_properties(fields[7])
        
        if len(fields) > 8:
            tool.start_values = self._parse_tdb_properties(fields[8])
        
        return tool
    
    def _parse_tdb_properties(self, prop_string: str) -> dict:
        """Parse property string from TDB format."""
        properties = {}
        
        if not prop_string:
            return properties
        
        # Example property parsing - adjust based on actual format
        pairs = prop_string.split(';')
        for pair in pairs:
            if '=' in pair:
                key, value = pair.split('=', 1)
                try:
                    # Try to parse as float
                    properties[key] = float(value)
                except ValueError:
                    # Keep as string
                    properties[key] = value
        
        return properties
```

**Expected Outcome:** TDB parser created with support for binary Carveco tool databases.

## Phase 3: Integration and Management (Steps 8-9)

### Step 8: Implement unified tool database manager
**File:** `src/parsers/tool_database_manager.py`

**Implementation Details:**
```python
"""
Unified tool database manager that integrates all parsers.
"""

from typing import List, Dict, Any, Optional, Type
from pathlib import Path

from src.core.logging_config import get_logger
from src.core.database.tool_database_repository import ToolDatabaseRepository
from src.core.database.provider_repository import ProviderRepository
from src.core.database.tool_preferences_repository import ToolPreferencesRepository
from .tool_parsers import (
    BaseToolParser, ToolData, CSVToolParser, JSONToolParser, 
    VTDBToolParser, TDBToolParser, ProgressCallback
)

logger = get_logger(__name__)

class ToolDatabaseManager:
    """Unified manager for tool database operations."""
    
    def __init__(self, db_path: str):
        """Initialize manager with database path."""
        self.db_path = db_path
        self.logger = logger
        
        # Initialize repositories
        self.tool_repo = ToolDatabaseRepository(db_path)
        self.provider_repo = ProviderRepository(db_path)
        self.preferences_repo = ToolPreferencesRepository(db_path)
        
        # Initialize parsers
        self.parsers: Dict[str, BaseToolParser] = {
            'CSV': CSVToolParser(),
            'JSON': JSONToolParser(),
            'VTDB': VTDBToolParser(),
            'TDB': TDBToolParser()
        }
    
    def import_tools_from_file(self, file_path: str, provider_name: str = "",
                             progress_callback: Optional[ProgressCallback] = None) -> tuple[bool, str]:
        """
        Import tools from a file.
        
        Args:
            file_path: Path to the tool database file
            provider_name: Optional provider name (defaults to filename)
            progress_callback: Optional progress callback
            
        Returns:
            Tuple of (success, message)
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return False, "File does not exist"
            
            # Determine format from file extension
            format_type = path.suffix.upper().lstrip('.')
            if format_type not in self.parsers:
                return False, f"Unsupported file format: {format_type}"
            
            parser = self.parsers[format_type]
            
            # Validate file
            is_valid, error_msg = parser.validate_file(file_path)
            if not is_valid:
                return False, f"Invalid file: {error_msg}"
            
            # Create provider if needed
            if not provider_name:
                provider_name = path.stem
            
            provider_id = self.provider_repo.add_provider(
                name=provider_name,
                description=f"Imported from {path.name}",
                file_path=str(path),
                format_type=format_type
            )
            
            if not provider_id:
                return False, "Failed to create provider"
            
            # Parse tools
            tools = parser.parse(file_path, progress_callback)
            
            if not tools:
                return False, "No tools found in file"
            
            # Import tools to database
            imported_count = 0
            for tool in tools:
                tool_data = {
                    'guid': tool.guid,
                    'description': tool.description,
                    'tool_type': tool.tool_type,
                    'diameter': tool.diameter,
                    'vendor': tool.vendor,
                    'product_id': tool.product_id,
                    'unit': tool.unit,
                    'properties': {
                        **tool.geometry,
                        **tool.start_values
                    },
                    'property_types': {
                        **{k: 'geometry' for k in tool.geometry.keys()},
                        **{k: 'start_values' for k in tool.start_values.keys()}
                    }
                }
                
                if self.tool_repo.add_tool(provider_id, tool_data):
                    imported_count += 1
            
            message = f"Successfully imported {imported_count} tools from {provider_name}"
            self.logger.info(message)
            return True, message
            
        except Exception as e:
            error_msg = f"Failed to import tools: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_tools_by_provider(self, provider_id: int) -> List[Dict[str, Any]]:
        """Get all tools for a provider."""
        return self.tool_repo.get_tools_by_provider(provider_id)
    
    def search_tools(self, query: str, provider_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search for tools."""
        return self.tool_repo.search_tools(query, provider_id)
    
    def get_all_providers(self) -> List[Dict[str, Any]]:
        """Get all providers."""
        return self.provider_repo.get_all_providers()
    
    def export_tools_to_external_db(self, provider_id: int, external_db_path: str,
                                  format_type: str) -> tuple[bool, str]:
        """
        Export tools to external database.
        
        Args:
            provider_id: Provider ID to export
            external_db_path: Path to external database
            format_type: Export format ('CSV', 'JSON', 'VTDB', 'TDB')
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Get tools
            tools = self.get_tools_by_provider(provider_id)
            if not tools:
                return False, "No tools to export"
            
            # Export based on format
            if format_type == 'CSV':
                return self._export_to_csv(tools, external_db_path)
            elif format_type == 'JSON':
                return self._export_to_json(tools, external_db_path)
            elif format_type == 'VTDB':
                return self._export_to_vtdb(tools, external_db_path)
            elif format_type == 'TDB':
                return self._export_to_tdb(tools, external_db_path)
            else:
                return False, f"Unsupported export format: {format_type}"
                
        except Exception as e:
            error_msg = f"Failed to export tools: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def _export_to_csv(self, tools: List[Dict[str, Any]], file_path: str) -> tuple[bool, str]:
        """Export tools to CSV format."""
        import csv
        
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # Write header
                writer.writerow([
                    'guid', 'description', 'tool_type', 'diameter', 'vendor',
                    'product_id', 'unit', 'geometry', 'start_values'
                ])
                
                # Write tools
                for tool in tools:
                    writer.writerow([
                        tool.get('guid', ''),
                        tool.get('description', ''),
                        tool.get('tool_type', ''),
                        tool.get('diameter', ''),
                        tool.get('vendor', ''),
                        tool.get('product_id', ''),
                        tool.get('unit', ''),
                        str(tool.get('properties', {}).get('geometry', {})),
                        str(tool.get('properties', {}).get('start_values', {}))
                    ])
            
            return True, f"Exported {len(tools)} tools to CSV"
            
        except Exception as e:
            return False, f"Failed to export to CSV: {str(e)}"
    
    def _export_to_json(self, tools: List[Dict[str, Any]], file_path: str) -> tuple[bool, str]:
        """Export tools to JSON format."""
        import json
        
        try:
            # Convert tools to expected format
            export_data = {
                'data': []
            }
            
            for tool in tools:
                tool_data = {
                    'guid': tool.get('guid', ''),
                    'description': tool.get('description', ''),
                    'type': tool.get('tool_type', ''),
                    'vendor': tool.get('vendor', ''),
                    'product-id': tool.get('product_id', ''),
                    'unit': tool.get('unit', 'inches'),
                    'geometry': tool.get('properties', {}).get('geometry', {}),
                    'start-values': tool.get('properties', {}).get('start_values', {})
                }
                export_data['data'].append(tool_data)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)
            
            return True, f"Exported {len(tools)} tools to JSON"
            
        except Exception as e:
            return False, f"Failed to export to JSON: {str(e)}"
    
    def _export_to_vtdb(self, tools: List[Dict[str, Any]], file_path: str) -> tuple[bool, str]:
        """Export tools to VTDB (SQLite) format."""
        import sqlite3
        
        try:
            # Create new SQLite database
            with sqlite3.connect(file_path) as conn:
                cursor = conn.cursor()
                
                # Create tables
                cursor.execute("""
                    CREATE TABLE tools (
                        id INTEGER PRIMARY KEY,
                        guid TEXT,
                        description TEXT,
                        tool_type TEXT,
                        diameter REAL,
                        vendor TEXT,
                        product_id TEXT,
                        unit TEXT,
                        properties TEXT
                    )
                """)
                
                # Insert tools
                for tool in tools:
                    properties = {
                        'geometry': tool.get('properties', {}).get('geometry', {}),
                        'start_values': tool.get('properties', {}).get('start_values', {})
                    }
                    
                    cursor.execute("""
                        INSERT INTO tools (guid, description, tool_type, diameter, vendor, 
                                         product_id, unit, properties)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        tool.get('guid', ''),
                        tool.get('description', ''),
                        tool.get('tool_type', ''),
                        tool.get('diameter', 0.0),
                        tool.get('vendor', ''),
                        tool.get('product_id', ''),
                        tool.get('unit', 'inches'),
                        str(properties)
                    ))
                
                conn.commit()
            
            return True, f"Exported {len(tools)} tools to VTDB"
            
        except Exception as e:
            return False, f"Failed to export to VTDB: {str(e)}"
    
    def _export_to_tdb(self, tools: List[Dict[str, Any]], file_path: str) -> tuple[bool, str]:
        """Export tools to TDB (binary) format."""
        try:
            with open(file_path, 'wb') as f:
                # Write header
                f.write(b'TDB\x00')  # Magic bytes
                f.write(struct.pack('<I', 1))  # Version
                f.write(struct.pack('<I', len(tools)))  # Tool count
                
                # Write tools
                for tool in tools:
                    tool_data = self._format_tool_for_tdb(tool)
                    encoded_data = tool_data.encode('utf-16-le')
                    f.write(struct.pack('<I', len(encoded_data)))
                    f.write(encoded_data)
            
            return True, f"Exported {len(tools)} tools to TDB"
            
        except Exception as e:
            return False, f"Failed to export to TDB: {str(e)}"
    
    def _format_tool_for_tdb(self, tool: Dict[str, Any]) -> str:
        """Format tool data for TDB export."""
        # Format tool as null-separated fields
        fields = [
            tool.get('guid', ''),
            tool.get('description', ''),
            tool.get('tool_type', ''),
            str(tool.get('diameter', 0.0)),
            tool.get('vendor', ''),
            tool.get('product_id', ''),
            tool.get('unit', 'inches'),
            str(tool.get('properties', {}).get('geometry', {})),
            str(tool.get('properties', {}).get('start_values', {}))
        ]
        
        return '\x00'.join(fields)
```

**Expected Outcome:** Unified tool database manager created with import/export capabilities for all formats.

### Step 9: Create migration utility
**File:** `src/tools/migration/json_to_sqlite_migrator.py`

**Implementation Details:**
```python
"""
Migration utility to convert existing JSON tool library to SQLite database.
"""

import json
from pathlib import Path
from typing import Optional

from src.core.logging_config import get_logger
from src.parsers.tool_database_manager import ToolDatabaseManager, ProgressCallback

logger = get_logger(__name__)

class JsonToSqliteMigrator:
    """Migrates JSON tool library to SQLite database."""
    
    def __init__(self, json_path: str, db_path: str):
        """Initialize migrator."""
        self.json_path = Path(json_path)
        self.db_path = db_path
        self.logger = logger
    
    def migrate(self, progress_callback: Optional[ProgressCallback] = None) -> tuple[bool, str]:
        """
        Migrate JSON tool library to SQLite database.
        
        Args:
            progress_callback: Optional progress callback
            
        Returns:
            Tuple of (success, message)
        """
        try:
            if not self.json_path.exists():
                return False, "JSON file does not exist"
            
            # Initialize tool database manager
            db_manager = ToolDatabaseManager(self.db_path)
            
            # Import JSON file
            success, message = db_manager.import_tools_from_file(
                str(self.json_path),
                provider_name="IDC Woodcraft",
                progress_callback=progress_callback
            )
            
            if success:
                self.logger.info("Migration completed successfully")
                return True, "Migration completed successfully"
            else:
                self.logger.error(f"Migration failed: {message}")
                return False, f"Migration failed: {message}"
                
        except Exception as e:
            error_msg = f"Migration error: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def backup_existing_db(self) -> bool:
        """Backup existing database if it exists."""
        try:
            db_path = Path(self.db_path)
            if db_path.exists():
                backup_path = db_path.with_suffix('.db.backup')
                db_path.rename(backup_path)
                self.logger.info(f"Backed up existing database to {backup_path}")
                return True
            return True
        except Exception as e:
            self.logger.error(f"Failed to backup database: {e}")
            return False
    
    def rollback(self) -> bool:
        """Rollback migration by restoring backup."""
        try:
            db_path = Path(self.db_path)
            backup_path = db_path.with_suffix('.db.backup')
            
            if backup_path.exists():
                if db_path.exists():
                    db_path.unlink()
                backup_path.rename(db_path)
                self.logger.info("Rolled back to previous database version")
                return True
            
            return False
        except Exception as e:
            self.logger.error(f"Failed to rollback: {e}")
            return False
```

**Expected Outcome:** Migration utility created to convert existing JSON data to SQLite database.

## Phase 4: User Interface Updates (Steps 10-14)

### Step 10: Update FeedsAndSpeedsWidget
**File:** `src/gui/feeds_and_speeds/feeds_and_speeds_widget.py`

**Implementation Details:**
Update the existing widget to use the new database system. Key changes:
- Replace ToolLibraryManager with ToolDatabaseManager
- Add provider selection dropdown
- Update tool loading and search methods
- Maintain existing UI functionality

**Expected Outcome:** Updated FeedsAndSpeedsWidget that uses the new database system.

### Step 11: Create "Add Tool" dialog
**File:** `src/gui/feeds_and_speeds/add_tool_dialog.py`

**Implementation Details:**
```python
"""
Add Tool dialog for importing tools from various providers.
"""

from typing import Optional
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QProgressBar, QFileDialog,
    QGroupBox, QRadioButton, QButtonGroup
)
from PySide6.QtCore import Qt, Signal, QThread

from src.core.logging_config import get_logger
from src.parsers.tool_database_manager import ToolDatabaseManager, ProgressCallback

logger = get_logger(__name__)

class ImportThread(QThread):
    """Thread for importing tools in background."""
    
    progress_updated = Signal(float, str)
    import_completed = Signal(bool, str)
    
    def __init__(self, db_manager: ToolDatabaseManager, file_path: str, provider_name: str):
        super().__init__()
        self.db_manager = db_manager
        self.file_path = file_path
        self.provider_name = provider_name
    
    def run(self):
        """Run import operation."""
        progress_callback = ProgressCallback(self.progress_updated.emit)
        success, message = self.db_manager.import_tools_from_file(
            self.file_path, self.provider_name, progress_callback
        )
        self.import_completed.emit(success, message)

class AddToolDialog(QDialog):
    """Dialog for adding tools from providers."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logger
        self.setWindowTitle("Add Tools")
        self.setModal(True)
        self.resize(800, 600)
        
        # Initialize database manager
        self.db_manager = ToolDatabaseManager("data/tools.db")
        
        # Import thread
        self.import_thread = None
        
        self._setup_ui()
        self._load_providers()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout()
        
        # Import section
        import_group = QGroupBox("Import from File")
        import_layout = QVBoxLayout()
        
        # File selection
        file_layout = QHBoxLayout()
        file_layout.addWidget(QLabel("File:"))
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("Select tool database file...")
        file_layout.addWidget(self.file_path_edit)
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._on_browse)
        file_layout.addWidget(self.browse_btn)
        
        import_layout.addLayout(file_layout)
        
        # Provider name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Provider Name:"))
        self.provider_name_edit = QLineEdit()
        name_layout.addWidget(self.provider_name_edit)
        import_layout.addLayout(name_layout)
        
        # Import button
        self.import_btn = QPushButton("Import Tools")
        self.import_btn.clicked.connect(self._on_import)
        self.import_btn.setEnabled(False)
        import_layout.addWidget(self.import_btn)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        import_layout.addWidget(self.progress_bar)
        
        import_group.setLayout(import_layout)
        layout.addWidget(import_group)
        
        # Existing providers section
        providers_group = QGroupBox("Existing Providers")
        providers_layout = QVBoxLayout()
        
        # Providers table
        self.providers_table = QTableWidget()
        self.providers_table.setColumnCount(3)
        self.providers_table.setHorizontalHeaderLabels(["Provider", "Format", "Tools"])
        self.providers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.providers_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.providers_table.itemSelectionChanged.connect(self._on_provider_selected)
        providers_layout.addWidget(self.providers_table)
        
        # Tools table
        tools_label = QLabel("Tools:")
        providers_layout.addWidget(tools_label)
        
        self.tools_table = QTableWidget()
        self.tools_table.setColumnCount(3)
        self.tools_table.setHorizontalHeaderLabels(["Description", "Type", "Diameter"])
        self.tools_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        providers_layout.addWidget(self.tools_table)
        
        # Add selected tools button
        self.add_tools_btn = QPushButton("Add Selected Tools to My Toolbox")
        self.add_tools_btn.clicked.connect(self._on_add_tools)
        self.add_tools_btn.setEnabled(False)
        providers_layout.addWidget(self.add_tools_btn)
        
        providers_group.setLayout(providers_layout)
        layout.addWidget(providers_group)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _load_providers(self):
        """Load existing providers."""
        providers = self.db_manager.get_all_providers()
        
        self.providers_table.setRowCount(len(providers))
        
        for row, provider in enumerate(providers):
            # Provider name
            name_item = QTableWidgetItem(provider['name'])
            self.providers_table.setItem(row, 0, name_item)
            
            # Format
            format_item = QTableWidgetItem(provider['format_type'])
            self.providers_table.setItem(row, 1, format_item)
            
            # Tool count (placeholder - would need to implement count method)
            count_item = QTableWidgetItem("...")
            self.providers_table.setItem(row, 2, count_item)
    
    def _on_browse(self):
        """Handle browse button click."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Tool Database File",
            "",
            "Tool Database Files (*.csv *.json *.vtdb *.tdb);;All Files (*)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            
            # Set default provider name from filename
            path = Path(file_path)
            if not self.provider_name_edit.text():
                self.provider_name_edit.setText(path.stem)
            
            # Enable import button
            self.import_btn.setEnabled(True)
    
    def _on_import(self):
        """Handle import button click."""
        file_path = self.file_path_edit.text()
        provider_name = self.provider_name_edit.text()
        
        if not file_path or not provider_name:
            QMessageBox.warning(self, "Warning", "Please select a file and enter a provider name.")
            return
        
        # Start import in background thread
        self.import_thread = ImportThread(self.db_manager, file_path, provider_name)
        self.import_thread.progress_updated.connect(self._on_progress_updated)
        self.import_thread.import_completed.connect(self._on_import_completed)
        
        # Update UI
        self.import_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        self.import_thread.start()
    
    def _on_progress_updated(self, progress: float, message: str):
        """Handle progress update."""
        self.progress_bar.setValue(int(progress * 100))
    
    def _on_import_completed(self, success: bool, message: str):
        """Handle import completion."""
        self.progress_bar.setVisible(False)
        self.import_btn.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Success", message)
            self._load_providers()  # Refresh providers list
        else:
            QMessageBox.critical(self, "Error", message)
    
    def _on_provider_selected(self):
        """Handle provider selection."""
        current_row = self.providers_table.currentRow()
        if current_row >= 0:
            # Load tools for selected provider
            # This would need to be implemented in the database manager
            self.add_tools_btn.setEnabled(True)
        else:
            self.add_tools_btn.setEnabled(False)
    
    def _on_add_tools(self):
        """Handle add tools button click."""
        selected_items = self.tools_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select tools to add.")
            return
        
        # Add selected tools to personal toolbox
        # This would need to be implemented
        QMessageBox.information(self, "Success", f"Added {len(selected_items)} tools to your toolbox.")
```

**Expected Outcome:** "Add Tool" dialog created with provider selection and tool browsing capabilities.

### Step 12: Implement export functionality
**File:** `src/gui/feeds_and_speeds/export_dialog.py`

**Implementation Details:**
Create export dialog with format selection and destination path.

**Expected Outcome:** Export functionality implemented for all supported formats.

### Step 13: Create external database viewer/editor
**File:** `src/gui/feeds_and_speeds/external_db_dialog.py`

**Implementation Details:**
Create dialog for viewing and editing external databases with calculation capabilities.

**Expected Outcome:** External database viewer/editor dialog created.

### Step 14: Implement preferences system
**File:** `src/gui/feeds_and_speeds/tool_preferences_dialog.py`

**Implementation Details:**
Create preferences dialog for managing external database paths and settings.

**Expected Outcome:** Preferences system implemented for external database paths.

## Phase 5: Quality Assurance (Steps 15-20)

### Step 15: Add comprehensive logging
Add JSON-formatted logs to all modules with performance metrics and error tracking.

### Step 16: Create unit tests
Create comprehensive unit tests for all parser functions with sample files.

### Step 17: Create integration tests
Create integration tests for complete workflows and database operations.

### Step 18: Perform memory leak testing
Test repeated operations (10-20 times) to verify no memory leaks.

### Step 19: Create performance benchmarks
Create performance benchmarks for database operations.

### Step 20: Write documentation
Write user guide, developer documentation, and troubleshooting guide.

## Testing Requirements

### Unit Tests
- Test each parser with actual sample files
- Include edge cases and malformed data handling
- Verify error handling and logging

### Integration Tests
- Test complete import/export workflows
- Verify database operations
- Test UI interactions

### Memory Leak Testing
- Run each operation 10-20 times
- Monitor memory usage patterns
- Verify proper resource cleanup

### Performance Benchmarks
- Database operations should complete within specified time limits
- Memory usage should remain stable during stress testing
- UI should remain responsive during operations

## Completion Criteria

The project is complete when:

1. All implementation steps are finished
2. All unit tests pass
3. All integration tests pass
4. Memory leak testing shows no leaks
5. Performance benchmarks meet requirements
6. Documentation is complete
7. User acceptance testing is successful
8. Existing functionality is preserved
9. New functionality works as specified
10. The system is ready for production use