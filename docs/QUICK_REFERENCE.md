# Digital Workshop - Quick Reference Guide

## 🚀 Quick Start (5 Minutes)

### Installation
```bash
# 1. Clone repository
git clone <repository-url>
cd digital-workshop

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run application
python run.py
```

### First Project
1. Click "New Project"
2. Enter project name
3. Click "Import Model"
4. Select 3D file (STL, OBJ, STEP, 3MF, PLY)
5. Model appears in viewport
6. Click "Export as DWW" to save

---

## 📋 Command Reference

### Running Application
```bash
python run.py                    # Quick start
python src/main.py              # Direct run
python -m pytest tests/ -v      # Run tests
```

### Development
```bash
pylint src/                      # Lint code
black src/                       # Format code
mypy src/                        # Type check
pytest tests/ --cov=src         # Coverage report
```

### Installation Modes
```bash
# Full Install (fresh installation)
python -m src.installer.installer --mode full

# Patch Mode (update only changed modules)
python -m src.installer.installer --mode patch

# Reinstall (fresh app, preserve data)
python -m src.installer.installer --mode reinstall

# Clean Install (DESTRUCTIVE - complete removal)
python -m src.installer.installer --mode clean
```

---

## 🎯 Common Tasks

### Import a Model
1. File → Import Model
2. Select file (STL, OBJ, STEP, 3MF, PLY)
3. Model loads and thumbnail generates
4. Model appears in project tree

### Export Project
1. Select project
2. File → Export as DWW
3. Choose save location
4. DWW file created

### Import Project
1. File → Import DWW
2. Select DWW file
3. Project extracted and verified
4. Project loaded

### Create Cut List
1. Open project
2. Click "Cut List" tab
3. Enter cutting information
4. Data saved automatically
5. Export to CSV/Excel

### Add Feed & Speed
1. Open project
2. Click "Feed & Speed" tab
3. Enter tool settings
4. Data saved automatically
5. Reference during CNC

### Create Invoice-Style Estimate
1. Open project
2. Click "Cost Estimator" tab
3. Import line items from resources/G-code/cut list or enter manually
4. Adjust quantities, tax, shipping, and terms
5. Save to project (XML + PDF) or export PDF for sharing

---

## 📁 File Structure Quick Reference

```
src/
├── core/                 # Core application
│   ├── application.py
│   ├── database/         # Database layer
│   ├── logging_config.py
│   └── ...
├── gui/                  # User interface
│   ├── main_window.py
│   ├── widgets/
│   └── ...
├── parsers/              # File parsers
│   ├── stl_parser.py
│   ├── obj_parser.py
│   └── ...
├── utils/                # Utilities
├── installer/            # Installation system
│   ├── modes/
│   ├── managers/
│   └── ...
└── main.py               # Entry point

tests/                     # Unit tests
config/                    # Configuration
docs/                      # Documentation
```

---

## 🔑 Keyboard Shortcuts

### Viewport Controls
- **Left Click + Drag**: Rotate model
- **Right Click + Drag**: Pan view
- **Scroll Wheel**: Zoom in/out
- **Home**: Reset view
- **F**: Fit to view

### Application
- **Ctrl+N**: New project
- **Ctrl+O**: Open project
- **Ctrl+S**: Save project
- **Ctrl+E**: Export as DWW
- **Ctrl+I**: Import model
- **Ctrl+Q**: Quit application

---

## 🗄️ Database Quick Reference

### Main Tables
```sql
-- Projects
CREATE TABLE projects (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP
);

-- Models
CREATE TABLE models (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    filename TEXT,
    format TEXT,
    file_path TEXT
);

-- Files
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    project_id INTEGER,
    filename TEXT,
    file_path TEXT,
    file_type TEXT
);
```

### Common Queries
```sql
-- Get all projects
SELECT * FROM projects;

-- Get models in project
SELECT * FROM models WHERE project_id = ?;

-- Get files in project
SELECT * FROM files WHERE project_id = ?;

-- Count models
SELECT COUNT(*) FROM models;
```

---

## 🔐 Security Quick Reference

### Blocked File Types
```
EXE, SYS, INI, INF, COM, BAT, PS1, DLL, MSI
```

### Allowed File Types
```
Models: STL, OBJ, STEP, STP, 3MF, PLY
G-Code: NC, GCODE
Documents: CSV, XLSX, XLS, PDF, TXT, MD
```

### Security Features
- ✅ File type validation
- ✅ SHA256 checksums
- ✅ Salted hash verification
- ✅ Automatic backups
- ✅ Data integrity checks

---

## 📊 Performance Quick Reference

### Module Sizes
```
Core:      150.48 MB
PySide6:   630.83 MB
VTK:       298.49 MB
OpenCV:    222.82 MB
NumPy:      84.33 MB
─────────────────────
Total:    1386.95 MB (~1.4 GB)
```

### Installation Times
```
Full Install:   ~15 minutes
Patch Mode:     ~5 minutes
Reinstall:      ~10 minutes
Clean Install:  ~15 minutes
```

### Performance Targets
```
Model Loading:      < 5 seconds (< 100MB)
Thumbnail Gen:      Non-blocking
UI Responsiveness:  Maintained
Frame Rate:         Minimum 30 FPS
```

---

## 🧪 Testing Quick Reference

### Run All Tests
```bash
python -m pytest tests/ -v
```

### Run Specific Test
```bash
python -m pytest tests/test_installer.py::TestInstaller::test_full_install -v
```

### Run with Coverage
```bash
python -m pytest tests/ --cov=src --cov-report=html
```

### Test Categories
```
Unit Tests:        62 tests
Integration Tests: 30 tests
Performance Tests: 5 tests
Security Tests:    7 tests
─────────────────────────
Total:            104 tests (100% passing)
```

---

## 📝 Code Standards Quick Reference

### Naming Conventions
```python
# Classes: PascalCase
class DatabaseManager:
    pass

# Functions: snake_case
def get_project_data():
    pass

# Constants: UPPER_SNAKE_CASE
MAX_FILE_SIZE = 1000000

# Private: Leading underscore
def _internal_method():
    pass
```

### Logging
```python
from src.core.logging_config import get_logger

logger = get_logger(__name__)

# Use lazy % formatting
logger.info("Processing: %s", filename)
logger.error("Error: %s", str(error))
logger.debug("Debug: %s", data)
```

### Type Hints
```python
def process_file(filename: str, size: int) -> bool:
    """Process a file and return success status."""
    return True
```

---

## 🔧 Configuration Quick Reference

### Config File Location
```
Windows: AppData\Local\DigitalWorkshop\config\config.json
Linux:   ~/.local/share/DigitalWorkshop/config/config.json
macOS:   ~/Library/Application Support/DigitalWorkshop/config/config.json
```

### Common Settings
```json
{
    "debug": false,
    "theme": "dark",
    "auto_backup": true,
    "backup_interval": 3600,
    "max_recent_projects": 10,
    "thumbnail_size": 128
}
```

---

## 📚 Documentation Quick Links

| Document | Purpose |
|----------|---------|
| README.md | Main overview |
| MODULAR_INSTALLER_START_HERE.md | Installation guide |
| FEATURES_GUIDE.md | Feature documentation |
| DEVELOPER_GUIDE.md | Development guide |
| SYSTEM_ARCHITECTURE.md | Architecture details |
| TROUBLESHOOTING_FAQ.md | Troubleshooting |
| SECURITY.md | Security policies |
| LINTING_STANDARDS.md | Code standards |

---

## 🆘 Quick Troubleshooting

### Application Won't Start
```bash
# Check Python version
python --version  # Should be 3.8-3.12

# Check dependencies
pip list | grep -E "PySide6|VTK|OpenCV|NumPy"

# Try clean install
python -m src.installer.installer --mode clean
python -m src.installer.installer --mode full
```

### Slow Performance
```bash
# Clear cache
rmdir /s AppData\Local\DigitalWorkshop\cache

# Close unused projects
# Reduce model complexity
# Update graphics drivers
```

### Database Error
```bash
# Restore from backup
# Or delete and reinitialize
rmdir /s AppData\Local\DigitalWorkshop\data
```

---

## 📞 Getting Help

- **Documentation**: See docs/ folder
- **Troubleshooting**: TROUBLESHOOTING_FAQ.md
- **Development**: DEVELOPER_GUIDE.md
- **Architecture**: SYSTEM_ARCHITECTURE.md

---

## ✅ Checklist

### Before First Use
- [ ] Python 3.8-3.12 installed
- [ ] Dependencies installed
- [ ] Application runs
- [ ] Can create project
- [ ] Can import model

### Before Development
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Tests passing
- [ ] Code linting clean

### Before Deployment
- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Backups created
- [ ] Security verified

---

**Last Updated**: November 4, 2025  
**Status**: ✅ Current

