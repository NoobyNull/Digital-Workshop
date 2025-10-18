# 🔍 3D-MM Research & Knowledge Base

## 📋 Document Purpose

This document serves as the **research memory** for the 3D-MM project. All research findings, technical decisions, and reference materials are documented here for:

- **Cross-mode reference** - Debug mode can recall previous research
- **Implementation guidance** - Ask mode can reference when more research needed
- **Decision tracking** - Why specific technical choices were made
- **Knowledge persistence** - Avoid re-researching solved problems

---

## 🏗️ Architecture Research

### **PySide5 vs PySide6 Decision**
**Context**: Initial framework selection for 3D visualization
**Research Date**: 2024-10-13
**Decision**: PySide5 (not PySide6)

**Findings**:
- PySide6 lacks built-in 3D engine (PyQt3D)
- PySide5 includes PyQt3D for reliable 3D visualization
- PySide5 has more mature ecosystem for 3D applications
- PySide6 would require external 3D dependencies

**References**:
- Qt documentation: PyQt3D module requirements
- PySide6 GitHub issues: 3D engine dependency discussions
- Stack Overflow: PySide6 3D visualization alternatives

**Related Components**:
- 3D viewer implementation
- VTK integration planning
- PyQt3D widget development

---

## 🔧 3D Visualization Research

### **PyQt3D Integration Patterns**
**Context**: 3D model display implementation
**Research Date**: 2024-10-13
**Status**: Ready for implementation

**Key Findings**:
```python
# PyQt3D Setup Pattern
from PySide5.Qt3DCore import QEntity, QTransform
from PySide5.Qt3DExtras import Qt3DWindow, QOrbitCameraController
from PySide5.Qt3DRender import QPointLight

class ModelViewer(Qt3DWindow):
    def __init__(self):
        super().__init__()
        self.root_entity = QEntity()
        self.setRootEntity(self.root_entity)
        self.setup_camera()
        self.setup_lighting()

    def load_stl_model(self, file_path):
        # STL loading implementation
        pass
```

**Performance Optimizations**:
- Use QOrbitCameraController for mouse interaction
- Implement LOD (Level of Detail) for large models
- Use QPointLight for proper lighting
- Consider QTechnique for performance optimization

**References**:
- Qt3D documentation: Scenegraph and entities
- PySide5 examples: 3D visualization patterns
- VTK integration: QVTKRenderWindowInteractor as backup

---

## 📁 File Format Parser Research

### **STL Parser Implementation**
**Context**: Primary 3D format for hobbyists
**Research Date**: 2024-10-13
**Priority**: Phase 1 implementation

**Implementation Approach**:
```python
import struct
import numpy as np

class STLParser:
    def __init__(self, file_path):
        self.file_path = file_path
        self.vertices = []
        self.triangles = []

    def parse(self):
        with open(self.file_path, 'rb') as f:
            # Read 80-byte header
            header = f.read(80)

            # Read triangle count
            triangle_count = struct.unpack('<I', f.read(4))[0]

            # Parse triangles
            for _ in range(triangle_count):
                triangle_data = f.read(50)  # 50 bytes per triangle
                # Parse normal vector, vertices, attribute count
                # Implementation details...
```

**Memory Optimization**:
- Stream processing for large files
- Lazy loading of geometry data
- Progressive mesh loading for UI responsiveness

**References**:
- STL file format specification
- NumPy array optimization for geometry
- Python struct module for binary parsing

---

## 🗄️ Database Schema Research

### **SQLite Metadata Design**
**Context**: Model organization and search functionality
**Research Date**: 2024-10-13
**Status**: Schema finalized

**Optimized Schema**:
```sql
-- Core model information
CREATE TABLE models (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    format TEXT NOT NULL CHECK(format IN ('stl', 'mf3', 'obj', 'step')),
    file_path TEXT NOT NULL,
    file_size INTEGER,
    date_added DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- User-friendly metadata
CREATE TABLE model_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    model_id INTEGER REFERENCES models(id),
    title TEXT,
    description TEXT,
    keywords TEXT,
    category TEXT,
    source TEXT,
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    view_count INTEGER DEFAULT 0,
    last_viewed DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(model_id)
);

-- Search optimization
CREATE INDEX idx_models_filename ON models(filename);
CREATE INDEX idx_metadata_title ON model_metadata(title);
CREATE INDEX idx_metadata_keywords ON model_metadata(keywords);
CREATE INDEX idx_metadata_category ON model_metadata(category);
```

**Performance Considerations**:
- FTS5 (Full-Text Search) for advanced search capabilities
- Composite indexes for common query patterns
- WAL mode for concurrent read/write operations

---

## 🔍 Search Functionality Research

### **Full-Text Search Implementation**
**Context**: Fast model discovery for hobbyists
**Research Date**: 2024-10-13
**Implementation**: SQLite FTS5

**Search Features**:
- **Multi-field search**: filename, title, description, keywords
- **Category filtering**: Quick filtering by model type
- **Recent files**: Sort by last viewed
- **Ranking**: Relevance-based result ordering

**Query Patterns**:
```sql
-- Multi-field search
SELECT m.*, mm.*, rank
FROM models m
LEFT JOIN model_metadata mm ON m.id = mm.model_id
JOIN model_fts ON model_fts.rowid = m.id
WHERE model_fts MATCH 'search_term'
ORDER BY rank DESC;

-- Category filter
SELECT * FROM models m
LEFT JOIN model_metadata mm ON m.id = mm.model_id
WHERE mm.category = 'Characters'
ORDER BY mm.last_viewed DESC;
```

**UI Integration**:
- Real-time search as user types
- Search result highlighting
- Keyboard navigation (up/down arrows)
- Search history and suggestions

---

## 📦 Packaging Research

### **PyInstaller + Inno Setup Strategy**
**Context**: Installable Windows application
**Research Date**: 2024-10-13
**Status**: Architecture designed

**PyInstaller Configuration**:
```ini
# pyinstaller.spec
a = Analysis(
    ['src/main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('resources', 'resources'),
        ('src/core', 'core'),
        ('src/gui', 'gui'),
        ('src/parsers', 'parsers')
    ],
    hiddenimports=[
        'PySide5.Qt3DCore',
        'PySide5.Qt3DRender',
        'PySide5.Qt3DExtras'
    ],
    excludes=['tkinter', 'unittest']
)

pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(pyz, a.scripts, a.binaries, a.zipfiles, a.datas,
          name='3D-MM',
          icon='resources/icons/app.ico',
          console=False,
          upx=True,
          debug=False)
```

**Inno Setup Features**:
- Desktop shortcut creation
- Start menu integration
- File associations for .stl, .obj, .3mf, .step
- Uninstall capability
- Settings migration during updates

---

## 🚀 Performance Research

### **5-Second Load Time Optimization**
**Context**: Large file handling for 500MB+ models
**Research Date**: 2024-10-13
**Target**: < 5 seconds for file operations

**Optimization Strategies**:
1. **Lazy Loading**: Load metadata first, geometry on demand
2. **Progressive Rendering**: Show low-res preview immediately
3. **Background Processing**: Parse files while showing progress
4. **Memory Management**: Clear unused models from memory
5. **Caching**: Smart caching of frequently accessed models

**Implementation Pattern**:
```python
class LazyModelLoader:
    def __init__(self, file_path):
        self.file_path = file_path
        self.metadata = None
        self.geometry = None

    async def load_metadata(self):
        # Load basic file info quickly
        return metadata

    async def load_geometry(self):
        # Load full geometry in background
        return geometry
```

**Progress Feedback**:
- Loading progress bar for large files
- Cancel operation capability
- Time remaining estimates
- Memory usage monitoring

---

## 🛠️ Development Tool Research

### **MCP Server Configurations**
**Context**: Tool setup for development workflow
**Research Date**: 2024-10-13
**Status**: Configured and tested

**Working Configurations**:
- **Context7**: Library documentation and examples
- **Filesystem**: File system operations for project
- **GitHub**: Repository management (when authenticated)

**Configuration**:
```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "d:/Candy-Cadence"]
    }
  }
}
```

---

## 📝 Logging System Research

### **JSON Logging with Rotation**
**Context**: Application monitoring and debugging
**Research Date**: 2024-10-13
**Implementation**: Custom JSON formatter with rotation

**Design Decisions**:
- **Format**: Human-readable JSON for easy parsing
- **Rotation**: On application startup, not size-based
- **Naming**: "Log - MMDDYY-HH-MM-SS <Level>.txt"
- **Structure**: Include timestamp, level, logger, function, line number

**Sample Output**:
```json
{
  "timestamp": "2024-10-13 23:45:22",
  "level": "INFO",
  "logger": "3d_mm.gui",
  "function": "load_model",
  "line": 45,
  "message": "Loading model: example.stl"
}
```

---

## 🔮 Future Research Topics

### **Pending Research Areas**
- [ ] **VTK Integration**: Backup 3D visualization if PyQt3D insufficient
- [ ] **Advanced STL Parsing**: Optimization for very large files
- [ ] **Cross-Platform Compatibility**: Mac/Linux support if needed
- [ ] **Plugin Architecture**: Extensibility for future features

### **Research Request Protocol**
When Debug mode encounters issues:
1. **Reference this document** for existing research
2. **Switch to Ask mode** if more research needed
3. **Document new findings** in this knowledge base
4. **Update implementation plans** based on new information

---

## 📚 Reference Materials

### **Key Documentation**
- **PySide5 Documentation**: https://doc.qt.io/qtforpython/
- **PyQt3D Examples**: Qt Creator 3D examples
- **SQLite FTS5**: Full-text search documentation
- **STL Format Spec**: Binary and ASCII STL specifications

### **Code Examples**
- **PyQt3D Basic Scene**: Qt documentation examples
- **SQLite FTS Usage**: SQLite official documentation
- **File Parser Patterns**: Python struct module examples

---

*This knowledge base should be referenced before new research and updated with all findings. Debug mode should check here first, Ask mode should add here after research, and all modes should maintain this as the single source of truth for technical decisions.*