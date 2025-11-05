# Installer Modes Specification

**Date**: 2025-11-04  
**Status**: Ready to implement  
**Scope**: Per-module compilation with 4 installation modes

---

## 🎯 Overview

The installer supports **4 distinct modes** for different use cases:

1. **Full Install** - Fresh installation with all modules
2. **Patching** - Update existing installation
3. **Reinstall** - Fresh install, preserve user data
4. **Clean Install** - DESTRUCTIVE - Delete everything

---

## 📋 Mode 1: Full Install

### Purpose
Fresh installation on a new system or clean slate.

### What Happens
```
1. Check if application already exists
   ├─ If yes: Ask user (upgrade/cancel/clean)
   └─ If no: Proceed

2. Create application directory structure
   ├─ C:\Users\{user}\AppData\Local\DigitalWorkshop\
   ├─ C:\Users\{user}\AppData\Local\DigitalWorkshop\modules\
   ├─ C:\Users\{user}\AppData\Local\DigitalWorkshop\data\
   ├─ C:\Users\{user}\AppData\Local\DigitalWorkshop\config\
   └─ C:\Users\{user}\AppData\Local\DigitalWorkshop\logs\

3. Install all modules
   ├─ Core module (app executable)
   ├─ PySide6 module
   ├─ VTK module
   ├─ OpenCV module
   ├─ NumPy module
   └─ Other dependencies

4. Initialize database
   ├─ Create SQLite database
   ├─ Create default tables
   └─ Set initial schema version

5. Create default configuration
   ├─ Create config.json
   ├─ Set default preferences
   └─ Create version.txt

6. Create shortcuts
   ├─ Desktop shortcut
   ├─ Start menu shortcut
   └─ Quick launch shortcut

7. Register application
   ├─ Add to Windows registry
   ├─ Add to Programs & Features
   └─ Create uninstall entry
```

### User Experience
```
Welcome Screen
    ↓
Installation Path Selection
    ↓
Module Selection (all pre-selected)
    ↓
Installation Progress
    ├─ Installing Core...
    ├─ Installing PySide6...
    ├─ Installing VTK...
    ├─ Installing OpenCV...
    ├─ Installing NumPy...
    └─ Finalizing...
    ↓
Completion Screen
    ↓
Launch Application (optional)
```

### Success Criteria
- ✅ All modules installed
- ✅ Database initialized
- ✅ Configuration created
- ✅ Shortcuts created
- ✅ Application launches successfully

---

## 📋 Mode 2: Patching

### Purpose
Update existing installation with new versions of modules.

### What Happens
```
1. Detect existing installation
   ├─ Check for version.txt
   ├─ Check for manifest.json
   └─ Verify installation integrity

2. Compare versions
   ├─ Current version: v0.1.5
   ├─ New version: v0.1.6
   └─ Identify changed modules

3. Backup current installation
   ├─ Create backup directory
   ├─ Copy current modules
   ├─ Copy database
   └─ Copy configuration

4. Update changed modules only
   ├─ Download new module versions
   ├─ Verify checksums
   ├─ Replace old modules
   └─ Update manifest

5. Run migration scripts (if needed)
   ├─ Check for database migrations
   ├─ Apply pending migrations
   └─ Update schema version

6. Verify installation
   ├─ Check all modules present
   ├─ Verify checksums
   ├─ Test application launch
   └─ Verify database integrity

7. Clean up
   ├─ Remove backup (if successful)
   └─ Update version.txt
```

### User Experience
```
Patch Available Screen
    ↓
Show Changes
    ├─ Current: v0.1.5
    ├─ New: v0.1.6
    ├─ Changed modules: [list]
    └─ Release notes: [display]
    ↓
Confirm Patch
    ↓
Patching Progress
    ├─ Backing up...
    ├─ Updating Core...
    ├─ Updating PySide6...
    ├─ Running migrations...
    └─ Verifying...
    ↓
Completion Screen
    ├─ Patch successful
    ├─ New version: v0.1.6
    └─ Restart application (optional)
```

### Success Criteria
- ✅ Only changed modules updated
- ✅ User data preserved
- ✅ Configuration preserved
- ✅ Database migrated successfully
- ✅ Application launches with new version
- ✅ Backup available if rollback needed

---

## 📋 Mode 3: Reinstall

### Purpose
Fresh installation while preserving user data and projects.

### What Happens
```
1. Detect existing installation
   ├─ Check for version.txt
   ├─ Verify data directory exists
   └─ Backup user data

2. Backup user data
   ├─ Copy projects directory
   ├─ Copy database
   ├─ Copy user preferences
   └─ Create backup archive

3. Remove application files only
   ├─ Delete modules directory
   ├─ Delete application executable
   ├─ Delete temporary files
   └─ Keep data directory intact

4. Install fresh modules
   ├─ Install Core module
   ├─ Install PySide6 module
   ├─ Install VTK module
   ├─ Install OpenCV module
   ├─ Install NumPy module
   └─ Install other dependencies

5. Restore user data
   ├─ Restore projects
   ├─ Restore database
   ├─ Restore preferences
   └─ Verify data integrity

6. Verify installation
   ├─ Check all modules present
   ├─ Verify data restored
   ├─ Test application launch
   └─ Verify database integrity

7. Finalize
   ├─ Update version.txt
   ├─ Update manifest.json
   └─ Clean up backups
```

### User Experience
```
Reinstall Confirmation
    ├─ Warning: This will reinstall the application
    ├─ Your data will be preserved
    └─ Confirm?
    ↓
Reinstall Progress
    ├─ Backing up data...
    ├─ Removing application files...
    ├─ Installing Core...
    ├─ Installing PySide6...
    ├─ Installing VTK...
    ├─ Installing OpenCV...
    ├─ Installing NumPy...
    ├─ Restoring data...
    └─ Verifying...
    ↓
Completion Screen
    ├─ Reinstall successful
    ├─ All data preserved
    └─ Launch application (optional)
```

### Success Criteria
- ✅ Application files replaced
- ✅ User data preserved
- ✅ Projects intact
- ✅ Database intact
- ✅ Preferences preserved
- ✅ Application launches successfully

---

## 📋 Mode 4: Clean Install (DESTRUCTIVE)

### Purpose
Complete removal and fresh start. **WARNING: DESTRUCTIVE - DELETES ALL DATA**

### What Happens
```
1. Display DESTRUCTIVE warning
   ├─ "This will DELETE all data"
   ├─ "This action CANNOT be undone"
   ├─ "All projects will be lost"
   ├─ "All settings will be lost"
   └─ Require explicit confirmation

2. Create final backup (optional)
   ├─ Ask user if they want backup
   ├─ Create backup archive
   ├─ Save to user-selected location
   └─ Verify backup integrity

3. Remove everything
   ├─ Delete application directory
   ├─ Delete data directory
   ├─ Delete configuration directory
   ├─ Delete logs directory
   ├─ Delete cache directory
   ├─ Delete shortcuts
   ├─ Remove registry entries
   └─ Remove from Programs & Features

4. Verify complete removal
   ├─ Check no files remain
   ├─ Check registry cleaned
   ├─ Check shortcuts removed
   └─ Confirm clean state

5. Fresh installation
   ├─ Create new directory structure
   ├─ Install all modules
   ├─ Initialize new database
   ├─ Create default configuration
   ├─ Create shortcuts
   └─ Register application

6. Finalize
   ├─ Create version.txt (v0.1.5)
   ├─ Create manifest.json
   └─ Ready for first launch
```

### User Experience
```
⚠️  DESTRUCTIVE OPERATION WARNING
    ├─ This will DELETE everything
    ├─ All projects will be lost
    ├─ All settings will be lost
    ├─ This CANNOT be undone
    └─ Type "DELETE" to confirm
    ↓
Backup Confirmation
    ├─ Create backup before deletion? (Recommended)
    ├─ Yes / No
    └─ If Yes: Select backup location
    ↓
Deletion Progress
    ├─ Creating backup...
    ├─ Removing application...
    ├─ Removing data...
    ├─ Removing configuration...
    ├─ Cleaning registry...
    └─ Verifying removal...
    ↓
Fresh Installation
    ├─ Creating directories...
    ├─ Installing Core...
    ├─ Installing PySide6...
    ├─ Installing VTK...
    ├─ Installing OpenCV...
    ├─ Installing NumPy...
    ├─ Initializing database...
    └─ Finalizing...
    ↓
Completion Screen
    ├─ Clean install complete
    ├─ Application ready
    ├─ Backup saved to: [path]
    └─ Launch application (optional)
```

### Success Criteria
- ✅ All files deleted
- ✅ Registry cleaned
- ✅ Shortcuts removed
- ✅ Fresh installation complete
- ✅ Database initialized
- ✅ Configuration created
- ✅ Backup created (if requested)
- ✅ Application launches successfully

---

## 🔄 Mode Selection Logic

```
Installer Start
    ↓
Check existing installation
    ├─ No existing installation
    │   └─ Full Install
    │
    ├─ Existing installation found
    │   ├─ Check version
    │   │   ├─ Same version
    │   │   │   ├─ Repair / Reinstall / Clean
    │   │   │   └─ User selects
    │   │   │
    │   │   ├─ Newer version available
    │   │   │   ├─ Patch / Reinstall / Clean
    │   │   │   └─ User selects
    │   │   │
    │   │   └─ Older version
    │   │       ├─ Upgrade / Reinstall / Clean
    │   │       └─ User selects
    │   │
    │   └─ User selects mode
    │
    └─ Proceed with selected mode
```

---

## 📊 Mode Comparison

| Aspect | Full | Patch | Reinstall | Clean |
|--------|------|-------|-----------|-------|
| **Requires existing install** | No | Yes | Yes | No |
| **Preserves data** | N/A | Yes | Yes | No |
| **Preserves config** | N/A | Yes | Yes | No |
| **Updates modules** | All | Changed | All | All |
| **Time** | ~15 min | ~5 min | ~10 min | ~15 min |
| **Risk** | Low | Low | Low | HIGH |
| **Reversible** | Yes | Yes | Yes | No |
| **Backup created** | No | Yes | Yes | Optional |

---

## 🔧 Implementation Requirements

### Per-Module Compilation
- Each module compiled separately
- Each module has own PyInstaller spec
- Each module versioned independently
- Each module has checksum for verification

### Module Manager
- Track installed modules
- Verify module integrity
- Manage module versions
- Handle module dependencies

### Installation Registry
- Record installation mode
- Track installed modules
- Store checksums
- Store installation date/time

### Backup System
- Create backups before patching
- Create backups before reinstalling
- Optional backup for clean install
- Backup verification

### Migration System
- Detect schema changes
- Run migration scripts
- Update schema version
- Verify migration success

---

## ✅ Checklist

- [ ] Implement Full Install mode
- [ ] Implement Patch mode
- [ ] Implement Reinstall mode
- [ ] Implement Clean Install mode
- [ ] Create module manager
- [ ] Create installation registry
- [ ] Create backup system
- [ ] Create migration system
- [ ] Create UI for mode selection
- [ ] Create progress dialogs
- [ ] Create warning dialogs
- [ ] Test all modes
- [ ] Test mode transitions
- [ ] Test backup/restore
- [ ] Test rollback scenarios

---

**Status**: ✅ SPECIFICATION COMPLETE

**Next**: Per-module compilation guide

