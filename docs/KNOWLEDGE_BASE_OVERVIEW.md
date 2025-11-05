# Digital Workshop - Knowledge Base Overview

## 📚 Purpose

This knowledge base provides comprehensive documentation for Digital Workshop, combining technical specifications, user guides, implementation details, and best practices. It serves as the single source of truth for all aspects of the application.

---

## 🎯 Core Knowledge Areas

### 1. **Installation & Deployment**
- **Modular Installer System** - Per-module compilation with 4 installation modes
- **Installation Modes** - Full Install, Patch, Reinstall, Clean Install
- **Module Compilation** - Per-module PyInstaller specifications
- **Deployment Strategy** - Production deployment guidelines

### 2. **Project Management**
- **Project Structure** - Directory organization and file layout
- **Project Import/Export** - DWW format for project portability
- **Tab Data Integration** - Cut List, Feed & Speed, Cost Estimator data
- **Database Schema** - SQLite database structure and relationships

### 3. **File Formats & Data**
- **DWW Format** - Digital Wood Works project archive format
- **Supported File Types** - Models, G-code, documents, and more
- **File Security** - File type restrictions and validation
- **Data Integrity** - Checksum verification and backup systems

### 4. **Security & Compliance**
- **Security Policies** - Application security guidelines
- **File Type Security** - Blocked and allowed file types
- **Data Protection** - Backup and recovery procedures
- **Code Standards** - Linting and formatting requirements

### 5. **Features & Capabilities**
- **3D Visualization** - VTK-based model rendering
- **CNC Workflow** - G-code generation and optimization
- **Project Management** - Multi-project support with metadata
- **Thumbnail Generation** - Efficient multi-size thumbnail system

### 6. **Development & Architecture**
- **Application Architecture** - Core components and systems
- **Database Management** - SQLite operations and migrations
- **GUI Framework** - PySide6 user interface components
- **Code Quality** - Linting standards and best practices

---

## 📖 Document Organization

### Quick Start Documents
- **README.md** - Main project overview
- **MODULAR_INSTALLER_START_HERE.md** - 5-minute installer quick start
- **DOCUMENTATION_INDEX.md** - Master documentation index

### Technical Specifications
- **INSTALLER_IMPLEMENTATION.md** - Installer code structure
- **INSTALLER_MODES_SPECIFICATION.md** - Detailed mode specifications
- **PER_MODULE_COMPILATION_GUIDE.md** - Module compilation process
- **DWW_FORMAT_SPECIFICATION.md** - Complete DWW format spec

### User Guides
- **DWW_USER_GUIDE.md** - DWW export/import guide
- **README_TAB_DATA.md** - Tab data integration guide

### Reference Documents
- **MODULAR_INSTALLER_COMPLETE_PLAN.md** - Technical plan
- **MODULAR_INSTALLER_VISUAL_GUIDE.md** - Visual diagrams
- **MODULAR_INSTALLER_CHECKLIST.md** - Implementation checklist

### Policy & Standards
- **SECURITY.md** - Security policies
- **FILE_TYPE_SECURITY_POLICY.md** - File type restrictions
- **LINTING_STANDARDS.md** - Code standards

---

## 🔍 Finding Information

### By Role

**End Users**
- Start: DWW_USER_GUIDE.md
- Reference: README_TAB_DATA.md

**Developers**
- Start: README.md
- Then: INSTALLER_IMPLEMENTATION.md
- Reference: LINTING_STANDARDS.md

**DevOps/Build Engineers**
- Start: MODULAR_INSTALLER_START_HERE.md
- Then: PER_MODULE_COMPILATION_GUIDE.md
- Reference: INSTALLER_MODES_SPECIFICATION.md

**Security Officers**
- Start: SECURITY.md
- Then: FILE_TYPE_SECURITY_POLICY.md
- Reference: DWW_FORMAT_SPECIFICATION.md

**Project Managers**
- Start: README.md
- Then: MODULAR_INSTALLER_START_HERE.md
- Reference: MODULAR_INSTALLER_COMPLETE_PLAN.md

### By Topic

**Installation & Deployment**
- MODULAR_INSTALLER_START_HERE.md
- INSTALLER_MODES_SPECIFICATION.md
- PER_MODULE_COMPILATION_GUIDE.md

**File Formats & Data**
- DWW_FORMAT_SPECIFICATION.md
- DWW_USER_GUIDE.md
- README_TAB_DATA.md

**Security & Compliance**
- SECURITY.md
- FILE_TYPE_SECURITY_POLICY.md
- DWW_FORMAT_SPECIFICATION.md (Security Features section)

**Code Quality & Development**
- LINTING_STANDARDS.md
- INSTALLER_IMPLEMENTATION.md
- README.md (Development section)

---

## 🔄 Document Relationships

```
README.md (Main Overview)
├── MODULAR_INSTALLER_START_HERE.md (Quick Start)
│   ├── INSTALLER_MODES_SPECIFICATION.md (Detailed Modes)
│   ├── PER_MODULE_COMPILATION_GUIDE.md (Compilation)
│   └── INSTALLER_IMPLEMENTATION.md (Code Structure)
│
├── DWW_USER_GUIDE.md (User Guide)
│   └── DWW_FORMAT_SPECIFICATION.md (Technical Spec)
│
├── README_TAB_DATA.md (Tab Data)
│   └── MODULAR_INSTALLER_COMPLETE_PLAN.md (Technical Plan)
│
└── SECURITY.md (Security)
    └── FILE_TYPE_SECURITY_POLICY.md (File Types)
```

---

## 📊 System Components

### Modular Installer System
- **5 Modules**: Core, PySide6, VTK, OpenCV, NumPy
- **4 Modes**: Full Install, Patch, Reinstall, Clean Install
- **Total Size**: ~1.4 GB
- **Status**: ✅ Production Ready

### DWW Format
- **Type**: ZIP-based archive
- **Integrity**: SHA256 salted hash verification
- **Supported Files**: Models, G-code, documents, metadata
- **Status**: ✅ Fully Implemented

### Tab Data Integration
- **Components**: Cut List, Feed & Speed, Cost Estimator
- **Storage**: JSON files in project directory
- **Integration**: Linked to project in database
- **Status**: ✅ Fully Implemented

### Database System
- **Type**: SQLite3
- **Tables**: Projects, Models, Metadata, Files, Settings
- **Migrations**: Automatic schema updates
- **Status**: ✅ Fully Implemented

---

## 🚀 Getting Started

1. **New to Digital Workshop?**
   - Read: README.md
   - Then: MODULAR_INSTALLER_START_HERE.md

2. **Need to Install?**
   - Read: MODULAR_INSTALLER_START_HERE.md
   - Reference: INSTALLER_MODES_SPECIFICATION.md

3. **Working with Projects?**
   - Read: DWW_USER_GUIDE.md
   - Reference: README_TAB_DATA.md

4. **Developing?**
   - Read: README.md (Development section)
   - Reference: LINTING_STANDARDS.md
   - Then: INSTALLER_IMPLEMENTATION.md

5. **Security Review?**
   - Read: SECURITY.md
   - Then: FILE_TYPE_SECURITY_POLICY.md
   - Reference: DWW_FORMAT_SPECIFICATION.md

---

## 📞 Support & Resources

- **Documentation Index**: DOCUMENTATION_INDEX.md
- **Quick Reference**: MODULAR_INSTALLER_VISUAL_GUIDE.md
- **Implementation Checklist**: MODULAR_INSTALLER_CHECKLIST.md
- **Technical Plan**: MODULAR_INSTALLER_COMPLETE_PLAN.md

---

## ✅ Knowledge Base Status

- **Last Updated**: November 4, 2025
- **Coverage**: 100% of current systems
- **Completeness**: ✅ Complete
- **Accuracy**: ✅ Verified
- **Maintenance**: Active

---

## 🔄 Continuous Updates

This knowledge base is actively maintained. Updates are made when:
- New features are implemented
- Systems are modified
- Best practices are updated
- Issues are discovered and resolved

For the latest information, always refer to the most recent version of these documents.

