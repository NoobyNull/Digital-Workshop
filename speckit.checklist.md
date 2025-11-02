# Digital Workshop - Naming Convention Implementation Checklist

## Overview
This checklist tracks all naming convention modifications required for the four Windows installer variants:
- **RAW**: Development build (python run.py)
- **PORTABLE**: Self-contained build (DigitalWorkshop-Portable.exe)
- **USER**: User installation (DigitalWorkshop.exe)
- **SYSTEM**: System-wide installation (DigitalWorkshop.exe)

## Progress Tracking Legend
- [x] **COMPLETED** - Item fully implemented
- [o] **IN PROGRESS** - Currently being worked on
- [ ] **PENDING** - Not started
- [~] **BLOCKED** - Cannot proceed due to dependencies
- [!] **ISSUE** - Problems encountered

---

## PHASE 1: CRITICAL FIXES (Must Fix Before Release)

### 1.1 Version Information Standardization
| Item | File | RAW | PORTABLE | USER | SYSTEM | Status | Notes |
|------|------|-----|----------|------|--------|---------|-------|
| V1.1.1 | `src/__init__.py` - Dynamic version | [ ] | [ ] | [ ] | [ ] | | Replace static "1.0.0" with installation-type aware |
| V1.1.2 | `src/main.py` - About dialog version | [ ] | [ ] | [ ] | [ ] | | Dynamic version display |
| V1.1.3 | `src/gui/main_window.py` - About dialog | [ ] | [ ] | [ ] | [ ] | | Version display in UI |
| V1.1.4 | `src/gui/main_window_components/event_handler.py` | [ ] | [ ] | [ ] | [ ] | | Duplicate about dialog fix |
| V1.1.5 | `src/core/settings_migration.py` | [ ] | [ ] | [ ] | [ ] | | Remove hardcoded version fallback |
| V1.1.6 | `src/gui/CLO/enhanced_cut_list_optimizer_widget.py` | [ ] | [ ] | [ ] | [ ] | | Dynamic version in logging |
| V1.1.7 | `src/gui/CLO/clo_logging_service.py` | [ ] | [ ] | [ ] | [ ] | | Dynamic version in logging |

### 1.2 QSettings Registry Path Fixes
| Item | File | RAW | PORTABLE | USER | SYSTEM | Status | Notes |
|------|------|-----|----------|------|--------|---------|-------|
| Q1.2.1 | `src/gui/theme/qt_material_service.py` | [ ] | [ ] | [ ] | [ ] | | Remove spaces from organization name |
| Q1.2.2 | `src/gui/theme/theme_persistence.py` | [ ] | [ ] | [ ] | [ ] | | Remove spaces from organization name |
| Q1.2.3 | All QSettings initialization | [ ] | [ ] | [ ] | [ ] | | Installation-type specific registry paths |

### 1.3 Logger Name Standardization
| Item | File | RAW | PORTABLE | USER | SYSTEM | Status | Notes |
|------|------|-----|----------|------|--------|---------|-------|
| L1.3.1 | `src/core/logging_config.py` | [ ] | [ ] | [ ] | [ ] | | Remove spaces from logger names |
| L1.3.2 | All logger initializations | [ ] | [ ] | [ ] | [ ] | | Standardize logger name format |
| L1.3.3 | Log message format | [ ] | [ ] | [ ] | [ ] | | Consistent log message format |

### 1.4 Executable Naming Standardization
| Item | File | RAW | PORTABLE | USER | SYSTEM | Status | Notes |
|------|------|-----|----------|------|--------|---------|-------|
| E1.4.1 | Entry point names | [ ] | [ ] | [ ] | [ ] | | `run.py` → `DigitalWorkshop-run.py` |
| E1.4.2 | Main script | [ ] | [ ] | [ ] | [ ] | | `main.py` → `DigitalWorkshop-main.py` |
| E1.4.3 | Executable names | [ ] | [ ] | [ ] | [ ] | | Installation-type specific names |

---

## PHASE 2: HIGH PRIORITY FIXES

### 2.1 Database and Cache Path Standardization
| Item | File | RAW | PORTABLE | USER | SYSTEM | Status | Notes |
|------|------|-----|----------|------|--------|---------|-------|
| D2.1.1 | `src/core/model_cache.py` | [ ] | [ ] | [ ] | [ ] | | Dynamic cache directory paths |
| D2.1.2 | `src/core/logging_config.py` | [ ] | [ ] | [ ] | [ ] | | Dynamic log directory paths |
| D2.1.3 | Database file naming | [ ] | [ ] | [ ] | [ ] | | Installation-type aware database names |

### 2.2 Resource Path Standardization
| Item | File | RAW | PORTABLE | USER | SYSTEM | Status | Notes |
|------|------|-----|----------|------|--------|---------|-------|
| R2.2.1 | Tool library files | [ ] | [ ] | [ ] | [ ] | | Rename to DigitalWorkshop-ToolLibrary.json |
| R2.2.2 | Resource directory structure | [ ] | [ ] | [ ] | [ ] | | Installation-type specific paths |
| R2.2.3 | Help system paths | [ ] | [ ] | [ ] | [ ] | | Dynamic help directory resolution |

### 2.3 Documentation Naming Standardization
| Item | File | RAW | PORTABLE | USER | SYSTEM | Status | Notes |
|------|------|-----|----------|------|--------|---------|-------|
| D2.3.1 | `MASTER_REFERENCE.md` | [ ] | [ ] | [ ] | [ ] | | Add DigitalWorkshop branding |
| D2.3.2 | Guide file naming | [ ] | [ ] | [ ] | [ ] | | Consistent DigitalWorkshop naming |
| D2.3.3 | Help documentation paths | [ ] | [ ] | [ ] | [ ] | | Dynamic documentation paths |

---

## PHASE 3: MEDIUM PRIORITY FIXES

### 3.1 Test Configuration Standardization
| Item | File | RAW | PORTABLE | USER | SYSTEM | Status | Notes |
|------|------|-----|----------|------|--------|---------|-------|
| T3.1.1 | Test file naming | [ ] | [ ] | [ ] | [ ] | | `test_*_digitalworkshop_*.py` pattern |
| T3.1.2 | Test configuration | [ ] | [ ] | [ ] | [ ] | | `DigitalWorkshop-test-config.json` |
| T3.1.3 | Test directory structure | [ ] | [ ] | [ ] | [ ] | | Installation-type specific test dirs |

### 3.2 Requirements File Standardization
| Item | File | RAW | PORTABLE | USER | SYSTEM | Status | Notes |
|------|------|-----|----------|------|--------|---------|-------|
| R3.2.1 | Development requirements | [ ] | [ ] | [ ] | [ ] | | `requirements-raw.txt` |
| R3.2.2 | Portable requirements | [ ] | [ ] | [ ] | [ ] | | `requirements-portable.txt` |
| R3.2.3 | User installation requirements | [ ] | [ ] | [ ] | [ ] | | `requirements-user.txt` |
| R3.2.4 | System installation requirements | [ ] | [ ] | [ ] | [ ] | | `requirements-system.txt` |

### 3.3 Tool Library Organization
| Item | File | RAW | PORTABLE | USER | SYSTEM | Status | Notes |
|------|------|-----|----------|------|--------|---------|-------|
| L3.3.1 | Tool database standardization | [ ] | [ ] | [ ] | [ ] | | Consistent naming convention |
| L3.3.2 | Resource file organization | [ ] | [ ] | [ ] | [ ] | | Installation-type specific structure |

---

## NEW FILES TO CREATE

### Core Infrastructure Files
| Item | File | Purpose | Status | Notes |
|------|------|---------|---------|-------|
| N4.1.1 | `src/core/path_manager.py` | Centralized path resolution | [ ] | PathManager class |
| N4.1.2 | `src/core/installation_detector.py` | Installation type detection | [ ] | InstallationDetector class |
| N4.1.3 | `src/core/version_manager.py` | Dynamic version management | [ ] | VersionManager class |

### Configuration Files
| Item | File | Purpose | Status | Notes |
|------|------|---------|---------|-------|
| N4.2.1 | `requirements-raw.txt` | Development dependencies | [ ] | Python development environment |
| N4.2.2 | `requirements-portable.txt` | Portable build dependencies | [ ] | Self-contained build |
| N4.2.3 | `requirements-user.txt` | User installation dependencies | [ ] | Standard user install |
| N4.2.4 | `requirements-system.txt` | System installation dependencies | [ ] | System-wide install |

---

## BACKWARD COMPATIBILITY CHECKLIST

### Migration Support
| Item | Description | RAW | PORTABLE | USER | SYSTEM | Status | Notes |
|------|-------------|-----|----------|------|--------|---------|-------|
| M5.1.1 | Old QSettings path support | [ ] | [ ] | [ ] | [ ] | | Migration utilities |
| M5.2.2 | Old file path support | [ ] | [ ] | [ ] | [ ] | | Path abstraction layer |
| M5.3.3 | Version format compatibility | [ ] | [ ] | [ ] | [ ] | | Support old and new formats |

---

## TESTING CHECKLIST

### Installation Type Detection Testing
| Item | Test Case | RAW | PORTABLE | USER | SYSTEM | Status | Notes |
|------|-----------|-----|----------|------|--------|---------|-------|
| T6.1.1 | Installation type detection | [ ] | [ ] | [ ] | [ ] | | Verify correct type identification |
| T6.1.2 | Path resolution | [ ] | [ ] | [ ] | [ ] | | Verify correct paths for each type |
| T6.1.3 | Registry path access | [ ] | [ ] | [ ] | [ ] | | Verify proper registry handling |

### Version Information Testing
| Item | Test Case | RAW | PORTABLE | USER | SYSTEM | Status | Notes |
|------|----------|-----|----------|------|--------|---------|-------|
| T7.1.1 | Version display accuracy | [ ] | [ ] | [ ] | [ ] | | Verify correct version shown |
| T7.1.2 | About dialog content | [ ] | [ ] | [ ] | [ ] | | Verify installation-specific info |
| T7.1.3 | Logging version consistency | [ ] | [ ] | [ ] | [ ] | | Verify version in logs |

---

## QUALITY ASSURANCE CHECKLIST

### Code Review Requirements
| Item | Requirement | Status | Reviewer | Date | Notes |
|------|------------|--------|----------|------|-------|
| Q8.1.1 | All critical fixes reviewed | [ ] | | | Phase 1 completion |
| Q8.1.2 | Installation detection tested | [ ] | | | Verify functionality |
| Q8.1.3 | Backward compatibility verified | [ ] | | | Migration works |
| Q8.1.4 | Performance impact assessed | [ ] | | | No degradation |

### Security Review
| Item | Requirement | Status | Reviewer | Date | Notes |
|------|------------|--------|----------|------|-------|
| S9.1.1 | No hardcoded secrets | [ ] | | | Security audit |
| S9.1.2 | Proper path validation | [ ] | | | Path traversal protection |
| S9.1.3 | Registry access permissions | [ ] | | | Proper access rights |

---

## DEPLOYMENT CHECKLIST

### Build Process Validation
| Item | Build Step | RAW | PORTABLE | USER | SYSTEM | Status | Notes |
|------|------------|-----|----------|------|--------|---------|-------|
| B10.1.1 | Development build | [ ] | [ ] | [ ] | [ ] | | `python run.py` works |
| B10.1.2 | Portable build | [ ] | [ ] | [ ] | [ ] | | Self-contained executable |
| B10.1.3 | User installer | [ ] | [ ] | [ ] | [ ] | | Standard Windows installer |
| B10.1.4 | System installer | [ ] | [ ] | [ ] | [ ] | | Administrative installer |

### Installation Testing
| Item | Installation Test | RAW | PORTABLE | USER | SYSTEM | Status | Notes |
|------|-------------------|-----|----------|------|--------|---------|-------|
| I11.1.1 | Clean installation | [ ] | [ ] | [ ] | [ ] | | Fresh install test |
| I11.1.2 | Upgrade from old version | [ ] | [ ] | [ ] | [ ] | | Migration test |
| I11.1.3 | Multiple installations | [ ] | [ ] | [ ] | [ ] | | Coexistence test |

---

## COMPLETION TRACKING

### Overall Progress
- **Phase 1 (Critical)**: 0/13 items completed
- **Phase 2 (High Priority)**: 0/9 items completed  
- **Phase 3 (Medium Priority)**: 0/7 items completed
- **New Files**: 0/7 files created
- **Testing**: 0/15 test cases passed
- **Overall Completion**: 0% complete

### Last Updated
- **Date**: 2025-11-01
- **Updated By**: Digital Workshop Development Team

---

## NOTES AND DEPENDENCIES

### Critical Dependencies
1. Installation type detection must be implemented before path standardization
2. Version manager must be created before version standardization
3. Path manager must be created before path-related fixes

### Known Issues
- None currently identified

### Future Considerations
- Plugin system integration
- Update mechanism compatibility
- Multi-language support

---

*End of Checklist*