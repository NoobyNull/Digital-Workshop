# Digital Workshop - Naming Inconsistencies Analysis Report

## Executive Summary

This report identifies all naming inconsistencies, path variations, and directory structure mismatches found throughout the Digital Workshop codebase that require standardization for the four installation variants (RAW, PORTABLE, USER, SYSTEM).

## Application Name Variations

### Primary Identifiers
| Usage Context | Current Name | Issues | Standardized Name |
|---------------|--------------|---------|-------------------|
| **UI Display** | "Digital Workshop" (with spaces) | ✅ Good for user display | "Digital Workshop" |
| **File System** | "DigitalWorkshop" (no spaces) | ✅ Good for paths | "DigitalWorkshop" |
| **Registry** | "Digital Workshop" | ❌ Spaces cause registry issues | "DigitalWorkshop" |
| **Logger** | "Digital Workshop.ComponentName" | ❌ Spaces in logger names | "DigitalWorkshop.ComponentName" |

### Database Name Inconsistencies
| File | Current Name | Location | Standardized Name |
|------|--------------|----------|-------------------|
| **Legacy DB** | `3dmm.db` | `./data/3dmm.db` | ❌ Abbreviation confusing |
| **RAW DB** | Not specified | `./data/` | `DigitalWorkshop-Raw.db` |
| **PORTABLE DB** | Not specified | `%EXE_DIR%/DigitalWorkshop-Portable/` | `DigitalWorkshop-Portable.db` |
| **USER DB** | Not specified | `%LOCALAPPDATA%/DigitalWorkshop/` | `DigitalWorkshop.db` |
| **SYSTEM DB** | Not specified | `%PROGRAMDATA%/DigitalWorkshop/` | `DigitalWorkshop.db` |

## Directory Path Inconsistencies

### Current Directory Structures
```
# Inconsistent naming patterns found:
./data/
./cache/
./config/
./resources/
./resources/ToolLib/
./logs/ (referenced but not consistently created)
```

### Standardized Directory Structure
```
# RAW (Development)
./data/DigitalWorkshop-Raw/
./cache/DigitalWorkshop-Raw/
./logs/DigitalWorkshop-Raw/
./config/DigitalWorkshop-Raw/

# PORTABLE (Self-contained)
%EXE_DIR%/DigitalWorkshop-Portable/
%EXE_DIR%/DigitalWorkshop-Portable/data/
%EXE_DIR%/DigitalWorkshop-Portable/cache/
%EXE_DIR%/DigitalWorkshop-Portable/logs/

# USER (Per-user installation)
%LOCALAPPDATA%/DigitalWorkshop/
%LOCALAPPDATA%/DigitalWorkshop/data/
%LOCALAPPDATA%/DigitalWorkshop/cache/
%LOCALAPPDATA%/DigitalWorkshop/logs/

# SYSTEM (System-wide installation)
%PROGRAMDATA%/DigitalWorkshop/
%PROGRAMDATA%/DigitalWorkshop/data/
%PROGRAMDATA%/DigitalWorkshop/cache/
%PROGRAMDATA%/DigitalWorkshop/logs/
```

## File Name Inconsistencies

### Configuration Files
| Current Name | Usage | Issues | Standardized Name |
|--------------|-------|---------|-------------------|
| `config.json` | Application settings | ❌ Generic name conflicts | `DigitalWorkshop-settings.json` |
| `quality_config.yaml` | Quality settings | ❌ Generic name | `DigitalWorkshop-quality.yaml` |
| `test_framework_config.json` | Test settings | ❌ Generic name | `DigitalWorkshop-test-config.json` |

### Resource Files
| Current Name | Location | Issues | Standardized Name |
|--------------|----------|---------|-------------------|
| `app_icon.ico` | `./resources/icons/` | ❌ Generic name | `DigitalWorkshop-icon.ico` |
| Various theme files | `./src/gui/theme/` | ❌ Inconsistent naming | `DigitalWorkshop-themes.json` |

### Database Files
| Pattern | Current | Issues | Standardized |
|---------|---------|---------|--------------|
| Database names | `3dmm.db` | ❌ Unclear abbreviation | `DigitalWorkshop-{variant}.db` |
| Database paths | Hardcoded `./data/` | ❌ Not installation-aware | Dynamic based on installation type |

## Registry Inconsistencies

### Current Registry Usage
```python
# Found in multiple files:
QSettings("Digital Workshop", "Digital Workshop")  # ❌ Spaces in organization name
QCoreApplication.setOrganizationName("Digital Workshop")  # ❌ Spaces
QCoreApplication.setApplicationName("3D Model Manager")  # ❌ Different app name
```

### Standardized Registry Structure
```python
# RAW: No registry entries
# PORTABLE: No registry entries
# USER: HKEY_CURRENT_USER/Software/DigitalWorkshop/
# SYSTEM: HKEY_LOCAL_MACHINE/SOFTWARE/DigitalWorkshop/
```

## Logger Name Inconsistencies

### Current Logger Patterns
```python
# Found inconsistent patterns:
logger = logging.getLogger(f"Digital Workshop.{name}")  # ❌ Spaces
logger.info("Digital Workshop application starting")  # ❌ Spaces in messages
logger = logging.getLogger(f"DigitalWorkshop.{name}")  # ✅ Some already correct
```

### Standardized Logger Names
```python
# RAW: "DigitalWorkshop-Raw"
# PORTABLE: "DigitalWorkshop-Portable"  
# USER: "DigitalWorkshop"
# SYSTEM: "DigitalWorkshop"
```

## Configuration Key Inconsistencies

### Application Config Issues
| Current Field | Issues | Standardized Field |
|---------------|---------|-------------------|
| `organization_name` | "Digital Workshop" with spaces | "DigitalWorkshop" |
| `application_name` | "3D Model Manager" inconsistent | "Digital Workshop" |
| `version` | Hardcoded strings | Dynamic based on installation |
| `database_name` | Not installation-aware | Dynamic per installation type |

## QSettings Inconsistencies

### Current QSettings Usage
```python
# Multiple instances of inconsistent QSettings initialization:
self.settings = QSettings("Digital Workshop", "Digital Workshop")  # ❌ Spaces
QCoreApplication.setOrganizationName("Digital Workshop")  # ❌ Spaces
QCoreApplication.setApplicationName("3D Model Manager")  # ❌ Wrong app name
```

### Standardized QSettings Usage
```python
# RAW: QSettings("Digital Workshop Development Team", "Digital Workshop (Development)")
# PORTABLE: QSettings("Digital Workshop", "Digital Workshop")  
# USER: QSettings("Digital Workshop", "Digital Workshop")
# SYSTEM: QSettings("Digital Workshop", "Digital Workshop")
```

## File Path Hardcoding Issues

### Files with Hardcoded Paths
| File | Current Hardcoded Path | Issues |
|------|------------------------|--------|
| `src/core/logging_config.py` | `app_data / 'DigitalWorkshop' / 'logs'` | ❌ Not installation-aware |
| `src/core/model_cache.py` | `app_data / 'DigitalWorkshop' / 'cache'` | ❌ Not installation-aware |
| `src/core/settings_migration.py` | `self.app_data_path` | ❌ Uses old naming |
| `src/gui/theme/qt_material_service.py` | `QSettings("Digital Workshop", "Digital Workshop")` | ❌ Inconsistent |

### Standardized Path Resolution
```python
# All paths should use PathManager class:
class PathManager:
    def get_data_directory(self) -> Path:
        # Returns appropriate path based on installation type
    
    def get_database_path(self) -> Path:
        # Returns appropriate database path
    
    def get_log_directory(self) -> Path:
        # Returns appropriate log directory
    
    def get_cache_directory(self) -> Path:
        # Returns appropriate cache directory
```

## Tool Library Inconsistencies

### Current Tool Library Organization
```
./resources/ToolLib/
├── IDC Woodcraft Vectric Tool Database Library Update rev 25-5.vtdb
├── IDC-Woodcraft-Carbide-Create-Database-5-2-2025.csv
├── IDC-Woodcraft-Carveco-Tool-Database.tdb
└── IDCWoodcraftFusion360Library.json
```

### Issues Found
- **Inconsistent naming**: Mix of spaces, hyphens, and underscores
- **Version information scattered**: Some in filename, some in content
- **No DigitalWorkshop branding**: Generic tool library organization

## Test Configuration Inconsistencies

### Test File Naming
| Current Name | Issues | Standardized Name |
|--------------|---------|-------------------|
| `test_*.py` | Generic naming | `test_*_digitalworkshop_*.py` |
| Screenshot tests | Location inconsistent | Standardized test directories |

### Test Path Dependencies
- Tests expect specific hardcoded paths
- No environment-based test configuration
- Missing installation-type awareness in tests

## Critical Action Items

### Immediate Fixes Required
1. **QSettings Initialization**: Fix all hardcoded "Digital Workshop" with spaces
2. **Database Path Resolution**: Implement dynamic database naming
3. **Logger Name Standardization**: Remove spaces from all logger names
4. **Path Hardcoding**: Replace all hardcoded paths with PathManager calls

### High Priority Standardization
1. **Directory Structure**: Implement installation-type-aware directory creation
2. **Registry Usage**: Standardize registry keys (no spaces)
3. **Configuration Files**: Rename config files with DigitalWorkshop prefix
4. **Resource Files**: Standardize resource file naming

### Medium Priority Updates
1. **Tool Library Organization**: Improve tool library file naming
2. **Test Configuration**: Make tests installation-type aware
3. **Documentation**: Update all documentation with new naming standards

## Implementation Impact Assessment

### Files Requiring Modification
- **High Priority (Core)**: 8 files
- **Medium Priority (Services)**: 12 files  
- **Low Priority (UI/Docs)**: 6 files
- **New Files Required**: 3 files (PathManager, InstallationDetector, MigrationManager)

### Risk Assessment
- **HIGH RISK**: QSettings changes will affect all user preferences
- **MEDIUM RISK**: Database path changes require migration strategy
- **LOW RISK**: Logger name changes are cosmetic but affect log analysis tools

### Backward Compatibility Requirements
- **100% backward compatibility** during transition period
- **Dual-path support** for all file operations
- **Graceful fallback** for missing new paths
- **User notification** for any migration requirements

## Conclusion

This analysis reveals significant naming inconsistencies that must be addressed before implementing the four installation variants. The standardization approach will require careful implementation to maintain backward compatibility while establishing consistent naming conventions across all installation types.

The implementation should proceed with the compatibility-first approach outlined in the specification to ensure zero test failures and seamless user experience during the transition period.